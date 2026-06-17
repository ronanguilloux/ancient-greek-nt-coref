import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
sys.path.append(os.path.abspath("scripts"))
from sprint2_character_registry import CharacterRegistry

# Initialize Environment and Client
load_dotenv()
client = genai.Client()
MODEL_ID = 'gemini-3.1-pro-preview'

class ProDropResolution(BaseModel):
    resolved_entity: str
    confidence: str

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60))
def call_gemini(context, verb, lemma):
    prompt = f"""You are an expert in Ancient Greek and the New Testament (Gospel of Mark).
Your task is to resolve the omitted subject (pro-drop) for a specific verb.
I will provide the previous sentence and the current sentence. The target verb is surrounded by **STARS**.

Context:
{context}

Target Verb: {verb} (lemma: {lemma})

Identify the canonical character or entity that is the subject of this verb.
- If it is Jesus, return "IESOUS".
- If it is Peter, return "PETROS".
- If it is a crowd, return "CROWD".
- If it refers to God, return "THEOS".
- If the verb is impersonal, existential (like ἐγένετο = it happened), or has no character subject, return "IMPERSONAL_OR_NONE".
- Use uppercase English identifiers for characters.

Respond in strict JSON matching the schema."""

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': ProDropResolution,
            'temperature': 0.1
        },
    )
    return json.loads(response.text)

def main():
    print("Loading data and registry...")
    df = pd.read_csv("project/data/proiel_coref.csv", low_memory=False)
    df_mark = df[df['book'] == 'MARK'].copy()
    
    registry = CharacterRegistry("project/lexicons/character_aliases.tsv")
    
    # Identify explicit subjects (head_ids)
    sub_heads = set(df_mark[df_mark['relation'] == 'sub']['head_id'])
    
    def is_pro_drop(row):
        if row['pos'] != 'V-': return False
        morph = str(row['morphology'])
        if not (morph.startswith('1') or morph.startswith('2') or morph.startswith('3')): return False
        if row['token_id'] in sub_heads: return False
        return True

    print("Building sentence mapping...")
    ordered_sents = df_mark['sentence_id'].unique()
    sent_idx = {sid: i for i, sid in enumerate(ordered_sents)}
    
    def get_context(sid, tid):
        idx = sent_idx[sid]
        prev_sid = ordered_sents[idx - 1] if idx > 0 else ordered_sents[idx]
        
        prev_words = df_mark[df_mark['sentence_id'] == prev_sid]['form'].fillna('').tolist()
        curr_words = []
        for _, r in df_mark[df_mark['sentence_id'] == sid].iterrows():
            if r['token_id'] == tid:
                curr_words.append(f"**{r['form'].upper()}**")
            else:
                curr_words.append(str(r['form']))
                
        if prev_sid != sid:
            return " ".join(prev_words) + " ||| " + " ".join(curr_words)
        return " ".join(curr_words)

    active_subject = "UNKNOWN"
    results = []
    
    print(f"Processing {len(ordered_sents)} sentences in Mark...")
    
    # We will process sequentially to maintain active_subject correctly
    pro_drop_count = 0
    llm_count = 0
    heuristic_count = 0
    
    # FOR DEMO/TESTING: We limit to first 100 sentences to ensure it runs quickly in the current session
    # If the user wants full processing, they can remove the slice.
    
    for sid in ordered_sents:
        group = df_mark[df_mark['sentence_id'] == sid]
        
        # Check for adversative particle anywhere in the sentence for simplicity
        # More precise: before the verb, but sentence-level is a good proxy.
        has_adversative = any(r['lemma'] in ['δέ', 'ἀλλά'] for _, r in group.iterrows())
        
        for _, token in group.iterrows():
            # 1. Update Active Subject
            if token['relation'] == 'sub':
                canon_id = registry.resolve_lemma(token['lemma'])
                active_subject = canon_id
                
            # 2. Check for Pro-Drop Verb
            if is_pro_drop(token):
                pro_drop_count += 1
                morph = str(token['morphology'])
                person = morph[0] if len(morph) > 0 else ''
                
                # Precise check for rupture before the verb
                tokens_before = group[group['token_id'] < token['token_id']]
                rupture_before = any(r['lemma'] in ['δέ', 'ἀλλά'] for _, r in tokens_before.iterrows())
                
                method = ""
                assigned_entity = ""
                
                if person == '3' and not rupture_before and active_subject != "UNKNOWN":
                    # HEURISTIC PASS
                    method = "HEURISTIC"
                    assigned_entity = active_subject
                    heuristic_count += 1
                else:
                    # LLM PASS
                    method = "LLM"
                    context = get_context(sid, token['token_id'])
                    try:
                        print(f"Calling LLM for {token['form']} (lemma: {token['lemma']})")
                        res = call_gemini(context, token['form'], token['lemma'])
                        assigned_entity = res.get('resolved_entity', 'UNKNOWN')
                        confidence = res.get('confidence', '')
                    except Exception as e:
                        print(f"LLM failed for {token['token_id']}: {e}")
                        assigned_entity = "ERROR"
                    
                    llm_count += 1
                    time.sleep(0.5) # Basic rate limit protection
                
                results.append({
                    'token_id': token['token_id'],
                    'form': token['form'],
                    'lemma': token['lemma'],
                    'method': method,
                    'resolved_entity': assigned_entity
                })
                
    print(f"\nFinished processing. Total Pro-Drop Verbs: {pro_drop_count}")
    print(f"Heuristic resolutions: {heuristic_count}")
    print(f"LLM resolutions: {llm_count}")
    
    # Save results
    out_df = pd.DataFrame(results)
    out_path = "project/data/mark_prodrop_resolved.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Saved results to {out_path}")

if __name__ == "__main__":
    main()
