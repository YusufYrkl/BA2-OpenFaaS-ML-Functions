import os
import joblib
import numpy as np
import json

# Modell laden – hier wird der Pfad so gesetzt, dass die Datei im Funktion-Verzeichnis liegt
MODEL_PATH = os.path.join(os.getcwd(), "function", "logistic_regression_model.joblib")
model = joblib.load(MODEL_PATH)

def handle(event, context):
    """
    Diese Funktion erwartet einen HTTP-Request als JSON, z.B.:
    {
      "features": [0.1, 1.2, 3.4, ...]
    }
    Hinweis: Das event-Objekt enthält unter `event.body` den Request-Body als String.
    """
    try:
        # Extrahiere den Request-Body als String
        req_str = event.body
        data = json.loads(req_str)
        features = data["features"]  # Erwartet wird eine Liste von Floats
        # Forme die Input-Daten in das erwartete Format um:
        X = np.array([features])
        
        prediction = model.predict(X)  # z.B. Ergebnis [0] oder [1]
        probability = model.predict_proba(X)  # Wahrscheinlichkeiten

        result = {
            "prediction": int(prediction[0]),
            "probability_of_class_1": float(probability[0][1])
        }
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})
