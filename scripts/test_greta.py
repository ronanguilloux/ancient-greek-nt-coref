from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

print("Loading bowphs/GreTa for Lemmatization...")
tokenizer = AutoTokenizer.from_pretrained("bowphs/GreTa")
model = AutoModelForSeq2SeqLM.from_pretrained("bowphs/GreTa")

# T5 expects a prompt, what is it for lemmatization? Let's check the readme
text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ"
inputs = tokenizer(text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=50)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

