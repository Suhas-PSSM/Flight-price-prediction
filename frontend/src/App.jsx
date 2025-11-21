import { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import "./App.css"; 

function FlightPricePredictor() {
  const [formData, setFormData] = useState({
    airline: "",
    source_city: "",
    departure_time: "",
    stops: "",
    arrival_time: "",
    destination_city: "",
    class: "",
    departure_date: "",
  });

  const [prediction, setPrediction] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("http://127.0.0.1:5000/predict", formData);
      setPrediction(response.data.prediction);
    } catch (error) {
      console.error("Error fetching prediction:", error);
    }
  };

  return (
    <div className="page-container">

      {/* Animated Title */}
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="title"
      >
        ✈️ Flight Price Predictor
      </motion.h1>

      {/* Animated Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="card"
      >
        <form onSubmit={handleSubmit} className="form">

          {/* Dynamic Select Inputs */}
          {[
            { label: "Airline", name: "airline", options: ["SpiceJet", "AirAsia", "Vistara", "GO_FIRST", "Indigo", "Air_India"] },
            { label: "Source City", name: "source_city", options: ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"] },
            { label: "Departure Time", name: "departure_time", options: ["Evening", "Early_Morning", "Morning", "Afternoon", "Night", "Late_Night"] },
            { label: "Stops", name: "stops", options: ["zero", "one", "two_or_more"] },
            { label: "Arrival Time", name: "arrival_time", options: ["Night", "Morning", "Early_Morning", "Afternoon", "Evening", "Late_Night"] },
            { label: "Destination City", name: "destination_city", options: ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai"] },
            { label: "Class", name: "class", options: ["Economy", "Business"] },
          ].map((field, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -15 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className="input-container"
            >
              <label>{field.label}</label>
              <select name={field.name} value={formData[field.name]} onChange={handleChange}>
                <option value="">Select {field.label}</option>
                {field.options.map((opt, j) => (
                  <option key={j} value={opt}>{opt}</option>
                ))}
              </select>
            </motion.div>
          ))}

          {/* Date Picker */}
          <motion.div
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="input-container"
          >
            <label>Departure Date</label>
            <input
              type="date"
              name="departure_date"
              min={new Date().toISOString().split("T")[0]}
              value={formData.departure_date}
              onChange={handleChange}
            />
          </motion.div>

          {/* Animated Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="predict-btn"
          >
             Predict 
          </motion.button>

        </form>
      </motion.div>

      {/* Prediction Box */}
      {prediction !== null && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="prediction-box"
        >
          Estimated Price: <strong>₹{prediction}</strong>
        </motion.div>
      )}

    </div>
  );
}

export default FlightPricePredictor;
