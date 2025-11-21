from flask import Flask, request, jsonify
import pickle
import requests
import os
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# -------------------------------
# Fetch model.pkl from Google Drive
# -------------------------------

GOOGLE_DRIVE_FILE_ID = "1NHI4k7_Nmy5b1b2S9TwaouV6p5w7eMBc"    # <-- Replace
MODEL_PATH = "model.pkl"

def download_model_from_drive():
    if os.path.exists(MODEL_PATH):
        print("Model already exists locally. Skipping download...")
        return

    print("Downloading model.pkl from Google Drive...")

    # Direct download link format
    url = f"https://drive.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"

    response = requests.get(url, allow_redirects=True)

    if response.status_code == 200:
        with open(MODEL_PATH, "wb") as f:
            f.write(response.content)
        print("Download completed!")
    else:
        raise Exception("Failed to download model from Google Drive.")

# Download model when server starts
download_model_from_drive()

# Load the model
model = pickle.load(open(MODEL_PATH, 'rb'))

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
    data = request.json
    try:
        airline = airline_dict[data['airline']]
        source_city = source_dict[data['source_city']]
        departure_time = departure_dict[data['departure_time']]
        stops = stops_dict[data['stops']]
        arrival_time = arrival_dict[data['arrival_time']]
        destination_city = destination_dict[data['destination_city']]
        travel_class = class_dict[data['class']]

        # Calculate date difference
        departure_date = datetime.strptime(data['departure_date'], '%Y-%m-%d')
        date_diff = (departure_date - datetime.today()).days + 1

        # Features
        features = [
            airline, source_city, departure_time, stops,
            arrival_time, destination_city, travel_class, date_diff
        ]

        prediction = model.predict([features])[0]

        return jsonify({'prediction': round(prediction, 2)})

    except KeyError as e:
        return jsonify({'error': f'Missing data for: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
