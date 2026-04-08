from transformers import pipeline

print("Loading UGARIT/grc-ner-xlmr pipeline...")
# The aggregation strategy usually handles subwords, let's try another one.
nlp_ner = pipeline("ner", model="UGARIT/grc-ner-xlmr", aggregation_strategy="first")

text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ"
print(f"\nAnalyzing: {text}")
results = nlp_ner(text)

print("\n--- UGARIT NER RESULTS ---")
for entity in results:
    print(f"Entity: {entity['word']:<12} | Label: {entity['entity_group']:<5} | Score: {entity['score']:.4f}")
