import torch
import json
import base64
from io import BytesIO
from PIL import Image
import os
import time
import traceback
import sys
from torchvision import transforms

# Importiere NMS und andere Utilities direkt aus dem lokalen YOLOv5-Repo
# Dies setzt voraus, dass LOCAL_YOLO_REPO_PATH korrekt zu sys.path hinzugefügt wurde
# und die utils/general.py etc. im Repo vorhanden sind.
# Der Import muss nach der sys.path-Modifikation in load_model_pipeline erfolgen,
# daher verschieben wir ihn dorthin oder machen ihn dynamisch.
non_max_suppression = None # Wird in load_model_pipeline initialisiert

MODEL = None
MODEL_VARIANT_NAME = 'yolov5s'
EXPECTED_IMG_SIZE = 640

_HANDLER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_YOLO_REPO_SUBDIR_NAME = 'yolov5_local_repo'
LOCAL_YOLO_REPO_PATH = os.path.join(_HANDLER_SCRIPT_DIR, _YOLO_REPO_SUBDIR_NAME)
MODEL_WEIGHTS_NAME = f'{MODEL_VARIANT_NAME}.pt'
MODEL_WEIGHTS_PATH = os.path.join(LOCAL_YOLO_REPO_PATH, MODEL_WEIGHTS_NAME)

preprocess_transform = transforms.Compose([
    transforms.Resize((EXPECTED_IMG_SIZE, EXPECTED_IMG_SIZE)),
    transforms.ToTensor(),
])

def load_model_pipeline():
    global MODEL, non_max_suppression
    start_time = time.time()
    print(f"--- DEBUG: Aktuelles Arbeitsverzeichnis (CWD) des Python-Prozesses: {os.getcwd()}", flush=True)
    print(f"--- DEBUG: Erwarteter Pfad zum YOLO-Repo (LOCAL_YOLO_REPO_PATH): {LOCAL_YOLO_REPO_PATH}", flush=True)
    print(f"--- DEBUG: Erwarteter Pfad zu den Gewichten (MODEL_WEIGHTS_PATH): {MODEL_WEIGHTS_PATH}", flush=True)

    if not os.path.exists(LOCAL_YOLO_REPO_PATH) or not os.path.isdir(LOCAL_YOLO_REPO_PATH):
        print(f"FEHLER: Lokales YOLOv5 Repository-Verzeichnis '{LOCAL_YOLO_REPO_PATH}' nicht gefunden oder kein Verzeichnis!", flush=True)
        MODEL = None
        return

    if LOCAL_YOLO_REPO_PATH not in sys.path:
        sys.path.insert(0, LOCAL_YOLO_REPO_PATH)
        print(f"--- DEBUG: '{LOCAL_YOLO_REPO_PATH}' zum sys.path hinzugefügt.", flush=True)

    try:
        # Importiere NMS erst, nachdem der Pfad hinzugefügt wurde
        from utils.general import non_max_suppression as nms_func
        non_max_suppression = nms_func # Weise der globalen Variable zu
        print(f"--- DEBUG: Inhalt von '{LOCAL_YOLO_REPO_PATH}': {os.listdir(LOCAL_YOLO_REPO_PATH)}", flush=True)
        print(f"--- DEBUG: non_max_suppression Funktion erfolgreich importiert.", flush=True)
    except ImportError as ie:
        print(f"--- DEBUG: Fehler beim Importieren von utils.general: {ie}", flush=True)
        print(f"--- DEBUG: sys.path: {sys.path}", flush=True)
        MODEL = None
        return
    except FileNotFoundError:
        print(f"--- DEBUG: Konnte Inhalt von '{LOCAL_YOLO_REPO_PATH}' nicht auflisten, da es nicht existiert.", flush=True)
        MODEL = None
        return

    if not os.path.exists(MODEL_WEIGHTS_PATH):
        print(f"FEHLER: Modelldatei '{MODEL_WEIGHTS_PATH}' nicht im lokalen YOLOv5 Repository-Verzeichnis gefunden!", flush=True)
        MODEL = None
        return

    print(f"Versuche, YOLOv5 Modell '{MODEL_VARIANT_NAME}' aus lokalem Repo '{LOCAL_YOLO_REPO_PATH}' mit Gewichten '{MODEL_WEIGHTS_PATH}' zu laden (via torch.hub.load)...", flush=True)

    try:
        MODEL = torch.hub.load(
            repo_or_dir=LOCAL_YOLO_REPO_PATH,
            model='custom',
            path=MODEL_WEIGHTS_PATH,
            source='local',
            force_reload=False, # Bei Problemen auf True setzen
            trust_repo=True
        )
        MODEL.eval()
        print(f"--- DEBUG: Type of loaded MODEL object: {type(MODEL)}", flush=True)
        # MODEL.names enthält die Klassennamen, MODEL.nc die Anzahl der Klassen
        print(f"--- DEBUG: Modell Klassennamen: {MODEL.names}", flush=True)
        print(f"--- DEBUG: Modell Anzahl Klassen (nc): {MODEL.nc}", flush=True)


        end_time = time.time()
        print(f"YOLOv5 Modell '{MODEL_VARIANT_NAME}' erfolgreich aus lokalen Dateien geladen. Dauer: {end_time - start_time:.2f} Sekunden.", flush=True)

    except Exception as e:
        print(f"FEHLER beim Laden des lokalen YOLOv5 Modells '{MODEL_VARIANT_NAME}': {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        MODEL = None

load_model_pipeline()

def handle(event, context):
    global MODEL, non_max_suppression
    if MODEL is None or non_max_suppression is None:
        print("handle() aufgerufen, aber YOLOv5 MODELL oder NMS-Funktion ist None.", flush=True)
        return json.dumps({"error": "YOLOv5 Modell oder NMS ist nicht verfügbar."}), 500
    try:
        request_body_data = None
        if hasattr(event, 'body'):
            request_body_data = event.body
            if isinstance(event.body, bytes):
                request_body_data = event.body.decode('utf-8')
            elif not isinstance(event.body, str):
                request_body_data = str(event.body)
        elif isinstance(event, str):
            request_body_data = event
        elif isinstance(event, bytes):
            request_body_data = event.decode('utf-8')
        else:
            return json.dumps({"error": "Interner Fehler: Unerwartetes Event-Format."}), 500

        if request_body_data is None:
             return json.dumps({"error": "Interner Fehler: Request Body konnte nicht extrahiert werden."}), 500

        input_data = json.loads(request_body_data)

        if 'image' not in input_data or not isinstance(input_data['image'], str):
            return json.dumps({"error": "JSON muss Schlüssel 'image' mit einem Base64-kodierten String enthalten."}), 400

        base64_image_string = input_data['image']
        if not base64_image_string:
             return json.dumps({"error": "Base64-kodierter Bildstring darf nicht leer sein."}), 400

        image_bytes = base64.b64decode(base64_image_string)
        img_pil = Image.open(BytesIO(image_bytes)).convert('RGB')

        img_tensor = preprocess_transform(img_pil).unsqueeze(0)
        # Optional: Auf CPU/GPU verschieben, falls MODEL.device bekannt ist
        # if hasattr(MODEL, 'device'):
        #    img_tensor = img_tensor.to(MODEL.device)

        print(f"Führe Inferenz mit YOLOv5 Modell '{MODEL_VARIANT_NAME}' und Tensor-Input aus...", flush=True)
        
        with torch.no_grad(): # Wichtig für Inferenz
            raw_predictions = MODEL(img_tensor)[0] # MODEL(img_tensor) gibt bei DetectionModel oft (prediction, None) oder (prediction, augment_output) zurück
                                                # oder direkt die rohen Head-Outputs, je nach interner Logik.
                                                # Wir nehmen an, das erste Element ist das relevante.
                                                # Wenn MODEL ein AutoShape-Objekt wäre, wäre results = MODEL(img_tensor) direkt ein Detections-Objekt.
                                                # Da type(MODEL) als DetectionModel geloggt wurde, gehen wir von roheren Outputs aus.

        print(f"Roh-Vorhersagen erhalten, Typ: {type(raw_predictions)}. Führe Non-Max Suppression durch...", flush=True)

        # Wende Non-Max Suppression an
        # Parameter für NMS (können angepasst werden, dies sind gängige Defaults)
        conf_thres = 0.25  # Konfidenz-Schwellenwert
        iou_thres = 0.45   # IoU-Schwellenwert für NMS
        classes = None     # Filtere nach bestimmten Klassen (None für alle)
        agnostic_nms = False # Klassen-agnostisches NMS
        max_det = 1000     # Maximale Anzahl Detektionen pro Bild

        # non_max_suppression erwartet eine Liste von Tensoren oder einen einzelnen Tensor
        # Der Output von MODEL(img_tensor) ist hier etwas unklar, basierend auf dem Fehler.
        # Wenn raw_predictions bereits die NMS-Liste ist, ist das gut.
        # Wenn raw_predictions die rohen Head-Outputs sind, muss NMS darauf angewendet werden.
        # Die `DetectionModel.forward` gibt die rohen Head-Outputs zurück.
        # Wir müssen NMS darauf anwenden.
        
        # pred ist eine Liste von Tensoren, für jedes Bild im Batch einen Tensor
        # Da wir nur ein Bild haben, nehmen wir pred[0]
        pred = non_max_suppression(raw_predictions, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        
        output_detections = []
        if pred[0] is not None and len(pred[0]):
            # pred[0] ist ein Tensor der Form (num_detections, 6)
            # Spalten: x1, y1, x2, y2, conf, cls
            # Klassennamen holen wir aus MODEL.names (oder MODEL.module.names, falls vorhanden)
            class_names_map = MODEL.module.names if hasattr(MODEL, 'module') and hasattr(MODEL.module, 'names') else MODEL.names

            for detection in pred[0]: # Iteriere über jede Detektion
                coords = detection[:4].tolist()
                confidence = detection[4].item()
                class_id = int(detection[5].item())
                
                output_detections.append({
                    "xmin": round(coords[0], 2),
                    "ymin": round(coords[1], 2),
                    "xmax": round(coords[2], 2),
                    "ymax": round(coords[3], 2),
                    "confidence": round(confidence, 4),
                    "class_id": class_id,
                    "name": class_names_map[class_id] if class_id < len(class_names_map) else "unknown"
                })
        
        print(f"Objekterkennung erfolgreich, {len(output_detections)} Objekte gefunden.", flush=True)
        return json.dumps({"detections": output_detections}), 200

    except json.JSONDecodeError:
        print(f"Fehler beim Parsen des JSON-Inputs. Verwendeter Body (Anfang): {str(request_body_data)[:200]}...", flush=True)
        print(traceback.format_exc(), flush=True)
        return json.dumps({"error": "Ungültiger JSON Input."}), 400
    except AttributeError as ae:
        print(f"AttributeError in handle(): {ae}", flush=True)
        print(traceback.format_exc(), flush=True)
        return json.dumps({"error": "Interner Fehler bei der Verarbeitung des Request-Events."}), 500
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist in handle() aufgetreten: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return json.dumps({"error": "Interner Serverfehler bei der Verarbeitung."}), 500