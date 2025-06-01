# download_distilbert.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

MODEL_NAME = "distilbert-base-uncased-finetuned-sst2-english"
# Verzeichnis, in dem Modell und Tokenizer gespeichert werden sollen
# Wir erstellen es im aktuellen Verzeichnis (oder passe den Pfad an)
SAVE_DIRECTORY = "./models/distilbert_sst2"

print(f"Lade Modell und Tokenizer für '{MODEL_NAME}' herunter...")

# Stelle sicher, dass das Zielverzeichnis existiert
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

# Lade Tokenizer und Modell von Hugging Face Hub herunter
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Speichere Tokenizer und Modell lokal im angegebenen Verzeichnis
tokenizer.save_pretrained(SAVE_DIRECTORY)
model.save_pretrained(SAVE_DIRECTORY)

print(f"Modell und Tokenizer erfolgreich in '{SAVE_DIRECTORY}' gespeichert.")