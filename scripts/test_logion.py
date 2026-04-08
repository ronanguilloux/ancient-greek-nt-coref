# Prevent multiprocessing timeout
import multiprocessing
multiprocessing.set_start_method('fork', force=True)

import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

print("Loading LOGION model (cabrooks/LOGION-50k_wordpiece)...")
tokenizer = AutoTokenizer.from_pretrained("cabrooks/LOGION-50k_wordpiece")
model = AutoModelForMaskedLM.from_pretrained("cabrooks/LOGION-50k_wordpiece")

text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ"
print("Encoding...")
inputs = tokenizer(text, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)

logits = outputs.logits
print("Done. Model output shape:", logits.shape)
