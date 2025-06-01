from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import json
import os
import time
import traceback # Importiere das traceback Modul

    # Korrigierter relativer Pfad zum Modellverzeichnis
    # Das Skript (index.py) wird von /home/app ausgeführt,
    # und die Funktionsdateien liegen in /home/app/function/
LOCAL_MODEL_DIR = "./function/mein_finetuned_modell"
CLASSIFIER_PIPELINE = None

def load_model_pipeline():
        """Lädt die Sentiment-Analyse-Pipeline aus dem lokalen Verzeichnis."""
        global CLASSIFIER_PIPELINE
        start_time = time.time()
        # Diese Debug-Ausgaben sind sehr nützlich, um das CWD zu bestätigen
        print(f"--- DEBUG: Aktuelles Arbeitsverzeichnis (CWD): {os.getcwd()}", flush=True)
        # Liste den Inhalt des "function"-Verzeichnisses, um zu sehen, ob "mein_finetuned_modell" dort ist
        function_dir_content = []
        if os.path.exists("./function"):
            function_dir_content = os.listdir('./function')
        print(f"--- DEBUG: Inhalt von ./function: {function_dir_content}", flush=True)

        print(f"Versuche, Pipeline aus lokalem Verzeichnis '{LOCAL_MODEL_DIR}' zu laden...", flush=True)

        # Überprüfe, ob das Verzeichnis und wichtige Dateien existieren
        model_path_exists = os.path.exists(LOCAL_MODEL_DIR) and os.path.isdir(LOCAL_MODEL_DIR)
        print(f"--- DEBUG: Prüfung '{LOCAL_MODEL_DIR}' (existiert & ist Verzeichnis): {model_path_exists}", flush=True)

        config_path = os.path.join(LOCAL_MODEL_DIR, "config.json")
        config_exists = os.path.exists(config_path)
        print(f"--- DEBUG: Prüfung '{config_path}' (existiert): {config_exists}", flush=True)

        weights_path_safetensors = os.path.join(LOCAL_MODEL_DIR, "model.safetensors")
        weights_path_pytorch_bin = os.path.join(LOCAL_MODEL_DIR, "pytorch_model.bin")
        weights_exist = os.path.exists(weights_path_safetensors) or os.path.exists(weights_path_pytorch_bin)
        print(f"--- DEBUG: Prüfung '{weights_path_safetensors}' (existiert): {os.path.exists(weights_path_safetensors)}", flush=True)
        print(f"--- DEBUG: Prüfung '{weights_path_pytorch_bin}' (existiert): {os.path.exists(weights_path_pytorch_bin)}", flush=True)
        print(f"--- DEBUG: Prüfung 'weights_exist' (mindestens eine Gewichtsdatei existiert): {weights_exist}", flush=True)

        if model_path_exists and config_exists and weights_exist:
            try:
                print(f"--- DEBUG: Versuche Modell und Tokenizer aus '{LOCAL_MODEL_DIR}' zu laden.", flush=True)
                # Lade Modell und Tokenizer explizit, dann erstelle die Pipeline
                model = AutoModelForSequenceClassification.from_pretrained(LOCAL_MODEL_DIR)
                tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_DIR)

                CLASSIFIER_PIPELINE = pipeline(
                    "sentiment-analysis", # Oder "text-classification"
                    model=model,
                    tokenizer=tokenizer,
                    device=-1  # Zwingt zur CPU-Nutzung
                )
                end_time = time.time()
                print(f"Pipeline erfolgreich aus '{LOCAL_MODEL_DIR}' geladen. Dauer: {end_time - start_time:.2f} Sekunden.", flush=True)
            except Exception as e:
                print(f"FEHLER beim Laden der Pipeline aus '{LOCAL_MODEL_DIR}': {e}", flush=True)
                print(traceback.format_exc(), flush=True) # Traceback beim Laden ausgeben
                CLASSIFIER_PIPELINE = None
        else:
            print(f"FEHLER: Modellverzeichnis '{LOCAL_MODEL_DIR}' oder notwendige Dateien (config.json, model weights) darin nicht gefunden!", flush=True)
            CLASSIFIER_PIPELINE = None

load_model_pipeline()

def handle(event, context):
        """Verarbeitet eine Anfrage zur Sentiment-Analyse."""
        global CLASSIFIER_PIPELINE

        if CLASSIFIER_PIPELINE is None:
            print("handle() aufgerufen, aber CLASSIFIER_PIPELINE ist None.", flush=True)
            return json.dumps({"error": "Sentiment-Analyse-Pipeline ist nicht verfügbar."}), 500

        try:
            # Annahme: Der eigentliche Request Body ist in event.body
            # Der Typ von event.body ist wahrscheinlich bytes, muss ggf. dekodiert werden
            # oder json.loads kann es direkt verarbeiten.
            request_body = None
            if hasattr(event, 'body'):
                request_body = event.body
                print(f"handle() aufgerufen. Event-Typ: {type(event)}, Body-Typ: {type(request_body)}", flush=True)
                # Logge nur, wenn der Body bytes oder str ist und gesliced werden kann
                if isinstance(request_body, (bytes, str)):
                    print(f"Event body (Anfang): {request_body[:200]}...", flush=True)
                else:
                    print(f"Event body (als str): {str(request_body)[:200]}...", flush=True)
            else:
                # Fallback, falls event direkt der Body ist (wie ursprünglich erwartet)
                request_body = event
                print(f"handle() aufgerufen. Event-Typ (direkt): {type(request_body)}", flush=True)
                if isinstance(request_body, (bytes, str)):
                     print(f"Event (direkt, Anfang): {request_body[:200]}...", flush=True)
                else:
                    print(f"Event (direkt, als str): {str(request_body)[:200]}...", flush=True)


            # Verwende request_body für json.loads
            input_data = json.loads(request_body)

            if 'text' not in input_data or not isinstance(input_data['text'], str):
                print("Fehler: 'text' nicht im JSON oder kein String.", flush=True)
                return json.dumps({"error": "JSON muss Schlüssel 'text' mit einem String enthalten."}), 400

            input_text = input_data['text']
            if not input_text.strip():
                 print("Fehler: 'text' ist leer.", flush=True)
                 return json.dumps({"error": "Schlüssel 'text' darf nicht leer sein."}), 400

            print(f"Führe Pipeline mit Text aus: '{input_text[:100]}...'", flush=True)
            results = CLASSIFIER_PIPELINE(input_text)
            print(f"Pipeline Ergebnis: {results}", flush=True)

            prediction = results[0] if results else {"label": "ERROR", "score": 0.0}
            return json.dumps(prediction), 200

        except json.JSONDecodeError:
            print(f"Fehler beim Parsen des JSON-Inputs. Verwendeter Body: {str(request_body)[:200]}...", flush=True)
            print(traceback.format_exc(), flush=True) # Traceback ausgeben
            return json.dumps({"error": "Ungültiger JSON Input."}), 400
        except AttributeError as ae: # Fängt Fehler ab, falls event.body nicht existiert und event kein str/bytes ist
            print(f"AttributeError in handle() - wahrscheinlich Problem mit 'event' oder 'event.body': {ae}", flush=True)
            print(traceback.format_exc(), flush=True)
            return json.dumps({"error": "Interner Fehler bei der Verarbeitung des Request-Events."}), 500
        except Exception as e:
            print(f"Ein unerwarteter Fehler ist in handle() aufgetreten: {e}", flush=True)
            print(traceback.format_exc(), flush=True) # Traceback ausgeben
            return json.dumps({"error": "Interner Serverfehler bei der Verarbeitung."}), 500