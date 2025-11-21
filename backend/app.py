from flask import Flask, request, jsonify
import pickle
import requests
import os
from datetime import datetime, date
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)

# -------------------------------
# Config
# -------------------------------
GOOGLE_DRIVE_FILE_ID = os.environ.get("GOOGLE_DRIVE_FILE_ID", "1NHI4k7_Nmy5b1b2S9TwaouV6p5w7eMBc")
MODEL_PATH = Path(os.environ.get("MODEL_PATH", "model.pkl"))
ALLOW_RELOAD = os.environ.get("ALLOW_RELOAD", "0") == "1"  # set to "1" to enable /reload-model

# -------------------------------
# Download helper (handles Drive confirm token)
# -------------------------------
def download_model_from_drive(force=False):
    if MODEL_PATH.exists() and not force:
        app.logger.info("Model already exists locally. Skipping download...")
        return

    app.logger.info("Downloading model.pkl from Google Drive...")

    session = requests.Session()
    URL = "https://docs.google.com/uc?export=download"
    params = {"id": GOOGLE_DRIVE_FILE_ID}
    resp = session.get(URL, params=params, stream=True)

    # Look for confirm token in cookies (download_warning...)
    token = None
    for k, v in resp.cookies.items():
        if k.startswith("download_warning") or k.startswith("download"):
            token = v
            break

    if token:
        app.logger.info("Found download confirm token in cookies; requesting confirmed download...")
        params["confirm"] = token
        resp = session.get(URL, params=params, stream=True)

    # If Google returns an HTML page (preview, permission error), detect it
    first_bytes = resp.raw.read(1024)
    # reset stream by building bytes iterator combining first_bytes + rest
    rest = resp.raw.read()
    full_content = first_bytes + rest

    # detect common HTML signatures
    if first_bytes.lstrip().startswith(b"<") or b"DOCTYPE html" in first_bytes or b"<html" in first_bytes.lower():
        # write the HTML to a debug file for diagnosis
        debug_path = MODEL_PATH.with_suffix(".download_error.html")
        with open(debug_path, "wb") as df:
            df.write(full_content)
        raise RuntimeError(
            f"Download returned HTML (likely Google Drive permission/preview page). "
            f"Saved response to {debug_path}. Ensure the file sharing is 'Anyone with the link' and use the correct FILE_ID."
        )

    # otherwise write the binary content to disk
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        f.write(full_content)

    app.logger.info("Download completed and saved to %s", MODEL_PATH)

# -------------------------------
# Load model (with checks)
# -------------------------------
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}.")
    # quick sanity: check start byte for common pickle protocol header (b'\x80' for protocol 2+)
    with open(MODEL_PATH, "rb") as f:
        head = f.read(4)
        f.seek(0)
        if head.startswith(b"<") or b"html" in head.lower():
            raise RuntimeError("model.pkl appears to be HTML (download failed).")
        try:
            model_obj = pickle.load(f)
            app.logger.info("Model loaded successfully from %s", MODEL_PATH)
            return model_obj
        except Exception as e:
            raise RuntimeError(f"Failed to unpickle model.pkl: {e}")

# Attempt download + load on startup, but raise readable errors
try:
    download_model_from_drive()
    model = load_model()
except Exception as e:
    # log the error and re-raise so Render shows the failure (or for local dev you can change behavior)
    app.logger.error("Startup error while fetching/loading model: %s", e)
    raise

# ------------------------------------------------------
# Dictionaries for categorical variables (as before)
# ------------------------------------------------------
airline_dict = {'AirAsia': 0, "Indigo": 1, "GO_FIRST": 2, "SpiceJet": 3, "Air_India": 4, "Vistara": 5}
source_dict = {'Delhi': 0, "Hyderabad": 1, "Bangalore": 2, "Mumbai": 3, "Kolkata": 4, "Chennai": 5}
departure_dict = {'Early_Morning': 0, "Morning": 1, "Afternoon": 2, "Evening": 3, "Night": 4, "Late_Night": 5}
stops_dict = {'zero': 0, "one": 1, "two_or_more": 2}
arrival_dict = {'Early_Morning': 0, "Morning": 1, "Afternoon": 2, "Evening": 3, "Night": 4, "Late_Night": 5}
destination_dict = {'Delhi': 0, "Hyderabad": 1, "Mumbai": 2, "Bangalore": 3, "Chennai": 4, "Kolkata": 5}
class_dict = {'Economy': 0, 'Business': 1}

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json or {}
    try:
        # required fields validation (will raise KeyError if missing)
        airline = airline_dict[data['airline']]
        source_city = source_dict[data['source_city']]
        departure_time = departure_dict[data['departure_time']]
        stops = stops_dict[data['stops']]
        arrival_time = arrival_dict[data['arrival_time']]
        destination_city = destination_dict[data['destination_city']]
        travel_class = class_dict[data['class']]

        # Calculate date difference: use date() to avoid time-of-day issues
        departure_date = datetime.strptime(data['departure_date'], '%Y-%m-%d').date()
        today = date.today()
        date_diff = (departure_date - today).days
        # guard: if departure is today or past, keep at least 0 or handle as needed
        if date_diff < 0:
            app.logger.warning("Departure date is in the past (%s). Setting date_diff to 0.", departure_date)
            date_diff = 0

        # Features
        features = [
            airline, source_city, departure_time, stops,
            arrival_time, destination_city, travel_class, date_diff
        ]

        prediction = model.predict([features])[0]

        return jsonify({'prediction': round(float(prediction), 2)})

    except KeyError as e:
        missing = e.args[0] if e.args else str(e)
        return jsonify({'error': f'Missing or invalid data for: {missing}'}), 400
    except Exception as e:
        app.logger.exception("Prediction error")
        return jsonify({'error': str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_path": str(MODEL_PATH), "model_exists": MODEL_PATH.exists()})

@app.route("/reload-model", methods=["POST"])
def reload_model():
    if not ALLOW_RELOAD:
        return jsonify({"error": "Model reload endpoint disabled. Set ALLOW_RELOAD=1 to enable."}), 403
    try:
        download_model_from_drive(force=True)
        global model
        model = load_model()
        return jsonify({"status": "reloaded", "model_path": str(MODEL_PATH)})
    except Exception as e:
        app.logger.exception("Reload failed")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # For Render, the port is provided via env var PORT
    port = int(os.environ.get("PORT", 5000))
    app.logger.info("Starting Flask on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port, debug=True)
