import csv
import json

# Eingabe- und Ausgabedateipfade
CSV_FILE_PATH = 'diabetes.csv'
JSON_PAYLOAD_FILE_PATH = 'logreg-payloads.json'

payloads = []

try:
    # CSV-Datei mit Diabetes-Datensatz einlesen
    with open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Überspringe die Kopfzeile

        # Verarbeitet jede Zeile im Datensatz
        # Das Modell erwartet 8 Merkmale: Schwangerschaften, Glukose, Blutdruck, Hautdicke, Insulin, BMI, Diabetes-Stammbaum-Funktion, Alter
        num_features = 8

        for row_number, row in enumerate(reader):
            if not row:  # Überspringe leere Zeilen
                continue
            try:
                # Konvertiere die ersten 8 Spalten zu Fließkommazahlen für die Modelleingabe
                features = [float(value) for value in row[:num_features]]
                payloads.append({"features": features})
            except ValueError as e:
                print(f"Warnung: Konnte Zeile {row_number + 2} nicht konvertieren: {row}. Fehler: {e}. Überspringe Zeile.")
            except IndexError:
                print(f"Warnung: Zeile {row_number + 2} hat nicht genügend Spalten: {row}. Überspringe Zeile.")

    # Schreibe die verarbeiteten Daten in eine JSON-Datei für k6-Tests
    with open(JSON_PAYLOAD_FILE_PATH, 'w', encoding='utf-8') as jsonfile:
        json.dump(payloads, jsonfile, indent=2)

    print(f"Erfolgreich {len(payloads)} Datenpunkte von '{CSV_FILE_PATH}' nach '{JSON_PAYLOAD_FILE_PATH}' konvertiert.")
    if not payloads:
        print("Warnung: Keine Payloads wurden generiert. Bitte überprüfen Sie die CSV-Datei und das Skript.")

except FileNotFoundError:
    print(f"Fehler: Datei '{CSV_FILE_PATH}' nicht gefunden.")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")