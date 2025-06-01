# loadtest/export_sst2_validation.py
import json
from datasets import load_dataset

ds = load_dataset("glue", "sst2", split="validation")

payloads = [{"text": ex["sentence"]} for ex in ds]

with open("distilbert_payloads.json", "w", encoding="utf-8") as f:
    json.dump(payloads, f, ensure_ascii=False)
print(f"{len(payloads)} Sätze als JSON in loadtest/payloads.json gespeichert")
