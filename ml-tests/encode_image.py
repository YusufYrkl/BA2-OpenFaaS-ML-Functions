import base64
import sys

def image_to_base64(image_path):
            """Liest ein Bild und gibt es als Base64-kodierten String zurück."""
            try:
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    return encoded_string
            except FileNotFoundError:
                print(f"FEHLER: Datei nicht gefunden unter '{image_path}'")
                return None
            except Exception as e:
                print(f"Ein Fehler ist aufgetreten: {e}")
                return None

if __name__ == "__main__":
            if len(sys.argv) < 2:
                print("Verwendung: python encode_image.py <PFAD_ZUM_BILD>")
                sys.exit(1)

            image_path_arg = sys.argv[1]
            base64_string = image_to_base64(image_path_arg)

            if base64_string:
                print("\n--- Base64-kodierter String (kopiere alles ab der nächsten Zeile bis zum Ende) ---")
                print(base64_string)
                print("\n--- Ende des Base64-Strings ---")
            else:
                print("Konnte das Bild nicht kodieren.")