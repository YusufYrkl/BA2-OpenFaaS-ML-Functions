# Import der notwendigen Bibliotheken
import numpy as np  # Für numerische Operationen und Arrays
from sklearn.linear_model import LogisticRegression  # Für das logistische Regressionsmodell
from sklearn.datasets import make_classification  # Zum Erzeugen synthetischer Daten
from sklearn.model_selection import train_test_split  # Zum Aufteilen der Daten
import joblib  # Zum Speichern des trainierten Modells
import os  # Für Betriebssystem-Operationen

# Erzeugung synthetischer Daten für die binäre Klassifikation
# n_samples: Anzahl der Datenpunkte
# n_features: Anzahl der Merkmale pro Datenpunkt
# n_informative: Anzahl der informativen Features (tragen zur Klassifikation bei)
# n_redundant: Anzahl der redundanten Features (korrelieren mit informativen Features)
# random_state: Für Reproduzierbarkeit der Ergebnisse
X, y = make_classification(n_samples=1000, n_features=10, n_informative=5, n_redundant=5, random_state=42)

# Aufteilung der Daten in Trainings- und Testdatensätze
# test_size=0.2 bedeutet 20% der Daten werden für Tests verwendet
# random_state=42 stellt sicher, dass die Aufteilung bei jedem Durchlauf gleich ist
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialisierung und Training des logistischen Regressionsmodells
# random_state=42 für reproduzierbare Ergebnisse
model = LogisticRegression(random_state=42)
model.fit(X_train, y_train)  # Training des Modells mit den Trainingsdaten

# Bewertung des Modells auf den Testdaten
# score() berechnet die Genauigkeit (Accuracy) des Modells
accuracy = model.score(X_test, y_test)
print(f"Modell-Genauigkeit auf Testdaten: {accuracy:.4f}")  # Ausgabe der Genauigkeit mit 4 Dezimalstellen

# Speicherung des trainierten Modells
# Das Modell wird im aktuellen Verzeichnis gespeichert
model_filename = 'logistic_regression_model.joblib'
joblib.dump(model, model_filename)  # Speichert das Modell in einer Datei

# Ausgabe von Informationen über das gespeicherte Modell
print(f"Modell gespeichert als: {model_filename}")
# Wichtige Information über die erwartete Eingabe für das Modell
print(f"Das Modell erwartet Input mit {X.shape[1]} Features.")