import re
import pandas as pd
import stanza
from transformers import pipeline, AutoTokenizer, AutoModelForMaskedLM
import torch
import math

# --- SPRINT 1 : PIPELINE C0.5 + C1 ---

print("Loading Lexicons...")
pronouns_df = pd.read_csv("project/lexicons/pronouns.tsv", sep="\t")
PRONOUN_LEMMAS = set(pronouns_df["lemma"].dropna())

print("Loading C0 Backend (Stanza mock)...")
nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse', verbose=False)

print("Loading C1 NER (UGARIT/grc-ner-xlmr)...")
ner_pipeline = pipeline("ner", model="UGARIT/grc-ner-xlmr", aggregation_strategy="first")

print("Loading C0.5 Resilience Module (cabrooks/LOGION)...")
logion_tokenizer = AutoTokenizer.from_pretrained("cabrooks/LOGION-50k_wordpiece")
logion_model = AutoModelForMaskedLM.from_pretrained("cabrooks/LOGION-50k_wordpiece")

def detect_corruptions(text, threshold=-3.5):
    """
    Evaluates token confidence via LOGION.
    If log_prob(token|context) < threshold, flags it as LOW_CONFIDENCE_TEXT_CORRUPTION
    """
    inputs = logion_tokenizer(text, return_tensors="pt")
    input_ids = inputs["input_ids"][0]
    
    corrupted_spans = []
    
    with torch.no_grad():
        for i in range(1, len(input_ids) - 1): # Skip CLS and SEP
            original_id = input_ids[i].item()
            
            # Mask the current token
            masked_ids = input_ids.clone()
            masked_ids[i] = logion_tokenizer.mask_token_id
            
            outputs = logion_model(masked_ids.unsqueeze(0))
            logits = outputs.logits[0, i, :]
            
            # Get probability of the original token
            probs = torch.nn.functional.log_softmax(logits, dim=0)
            token_log_prob = probs[original_id].item()
            
            if token_log_prob < threshold:
                token_str = logion_tokenizer.decode([original_id])
                corrupted_spans.append((token_str, token_log_prob))
                
    return corrupted_spans

def process_text(text):
    print(f"\n--- ANALYZING ---\n{text}")
    
    # C0.5: Check for corruptions
    corruptions = detect_corruptions(text)
    if corruptions:
        print("\n[C0.5] ⚠️  LOW_CONFIDENCE_TEXT_CORRUPTION detected:")
        for span, score in corruptions:
            print(f"  - '{span}' (log prob: {score:.2f})")
    else:
        print("\n[C0.5] Text confidence is HIGH. No corruptions detected.")
        
    # C0: Parse Dependencies
    doc = nlp(text)
    
    # C1: Extract Entities
    ner_results = ner_pipeline(text)
    named_entities = [ent['word'].strip().replace(" ", "") for ent in ner_results if ent['entity_group'] == 'PER']
    print(f"[C1] UGARIT Detected Entities: {named_entities}")
            
    mentions = []
    for sentence in doc.sentences:
        for word in sentence.words:
            mention = None
            
            # 1. PER Entity
            if word.text in named_entities:
                mention = {"type": "NAMED", "form": word.text, "lemma": word.lemma, "id": word.id}
            
            # 2. Pronoun
            elif word.lemma in PRONOUN_LEMMAS:
                mention = {"type": "PRONOUN", "form": word.text, "lemma": word.lemma, "id": word.id}
            
            # 3. Pro-drop (Subjectless verb)
            elif word.upos == "VERB":
                has_nsubj = any(w.head == word.id and w.deprel == "nsubj" for w in sentence.words)
                if not has_nsubj:
                    mention = {"type": "PRO_DROP", "form": word.text, "lemma": word.lemma, "id": word.id}
            
            if mention:
                mentions.append(mention)
                
    return mentions

if __name__ == "__main__":
    # Test 1: Normal sentence
    text1 = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ."
    mentions1 = process_text(text1)
    
    print("\n[Extracted Mentions]")
    for m in mentions1:
        print(f"  {m['type']:<10} | {m['form']} (lemma: {m['lemma']})")

    # Test 2: Sentence with an injected spelling error "αὐχῇ" instead of "αὐτῇ"
    text2 = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐχῇ."
    mentions2 = process_text(text2)

