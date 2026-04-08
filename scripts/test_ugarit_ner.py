from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline

# Testing UGARIT/grc-ner-xlmr for C1 module
model_id = "UGARIT/grc-ner-xlmr"
print(f"Loading {model_id}...")

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForTokenClassification.from_pretrained(model_id)

nlp_ner = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ"
print(f"\nAnalyzing: {text}")
ner_results = nlp_ner(text)

print("\n--- UGARIT NER RESULTS ---")
for entity in ner_results:
    print(f"Entity: {entity['word']:<12} | Label: {entity['entity_group']:<5} | Score: {entity['score']:.4f}")
