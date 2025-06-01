import os
import json
import joblib
import numpy as np

# Arbeitsverzeichnis im Container ist /home/app
# function/ liegt also unter /home/app/function
BASE_DIR = os.getcwd()                  # "/home/app"
FUNC_DIR = os.path.join(BASE_DIR, "function")

# Lade Modell und Scaler global
MODEL_PATH  = os.path.join(FUNC_DIR, "logistic_diabetes_model.joblib")
SCALER_PATH = os.path.join(FUNC_DIR, "scaler.joblib")

MODEL  = joblib.load(MODEL_PATH)
SCALER = joblib.load(SCALER_PATH)

def handle(event, context):
    try:
        # Debug-Ausgabe (optional, um Body zu sehen)
        print("BODY:", event.body)

        data = json.loads(event.body)
        features = np.array([data["features"]])

        # Sicherheits-Check (eigentlich redundant, MODEL ist geladen)
        if MODEL is None or SCALER is None:
            raise RuntimeError("Modell oder Scaler fehlt")

        # Inferenz
        X_scaled = SCALER.transform(features)
        pred     = MODEL.predict(X_scaled)[0]
        proba    = MODEL.predict_proba(X_scaled)[0][1]

        return json.dumps({
            "prediction": int(pred),
            "probability_of_class_1": float(proba)
        })
    except Exception as e:
        # Logs ausgeben und Fehler zurückgeben
        print("EXCEPTION:", str(e))
        return json.dumps({"error": str(e)})
