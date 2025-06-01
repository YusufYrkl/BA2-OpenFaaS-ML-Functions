# train_diabetes.py
import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# 1. Daten laden und binär vorbereiten
X, y_cont = load_diabetes(return_X_y=True)
# Binarisierung: hoher vs. niedriger Wert (Median)
y = (y_cont > np.median(y_cont)).astype(int)

# 2. Split & Skalierung
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler().fit(X_train)
X_train_scaled = scaler.transform(X_train)

# 3. Modell trainieren
clf = LogisticRegression(max_iter=1000).fit(X_train_scaled, y_train)

# 4. Speichern
joblib.dump(clf, "logistic_diabetes_model.joblib")
joblib.dump(scaler, "scaler.joblib")
