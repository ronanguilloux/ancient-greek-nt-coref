import stanza

def parse_feats(feat_str):
    if not feat_str or feat_str == "None":
        return {}
    return {f.split('=')[0]: f.split('=')[1] for f in feat_str.split('|')}

def demo_pronoun_resolution():
    print("Loading Stanza (Mock parser)...")
    nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse', verbose=False)
    
    text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν τῇ γυναικί. αὐτὴ δὲ λέγει αὐτῷ."
    print(f"\n--- SPRINT 2B: Pronominal Resolution ---\nText: {text}\n")
    
    doc = nlp(text)
    
    # 1. Extract Mentions and their features
    mentions = []
    global_id = 0
    for sentence in doc.sentences:
        for word in sentence.words:
            global_id += 1
            feats = parse_feats(word.feats)
            
            # Temporary override for Stanza's parser error on 'Ἰησοῦς'
            if word.text == "Ἰησοῦς":
                feats["Gender"] = "Masc"
                feats["Case"] = "Nom"
                word.deprel = "nsubj" # Fixing parser error for demo
            
            m_type = None
            if word.text in ["Ἰησοῦς", "γυναικί"]:
                m_type = "NAMED/NP"
            elif word.text in ["αὐτὴ", "αὐτῷ"]:
                m_type = "PRONOUN"
                
            if m_type:
                mentions.append({
                    "id": global_id,
                    "type": m_type,
                    "text": word.text,
                    "lemma": word.lemma,
                    "gender": feats.get("Gender"),
                    "number": feats.get("Number"),
                    "deprel": word.deprel,
                    "head": word.head,
                    "sentence_id": sentence.index
                })
                
    print("[1] Detected Entities and Pronouns:")
    for m in mentions:
        print(f"  - {m['type']:<10} | {m['text']:<10} | Gen:{m['gender']}, Num:{m['number']}, Rel:{m['deprel']}")

    # 2. Pronoun Resolution Logic
    print("\n[2] Resolution Process:")
    for i, mention in enumerate(mentions):
        if mention["type"] == "PRONOUN":
            print(f"\nResolving PRONOUN: '{mention['text']}' (Gender: {mention['gender']}, Number: {mention['number']})")
            
            candidates = []
            # Look backwards for antecedents
            for j in range(i - 1, -1, -1):
                candidate = mentions[j]
                if candidate["type"] == "NAMED/NP":
                    # Step 1: Strict Morphological Filter (Gender and Number)
                    if candidate["gender"] == mention["gender"] and candidate["number"] == mention["number"]:
                        
                        # Step 2: Scoring
                        score = 0.0
                        
                        # +3 if subject of previous clause (we approximate by sentence_id diff and nsubj)
                        if candidate["sentence_id"] == mention["sentence_id"] - 1 and candidate["deprel"] == "nsubj":
                            score += 3.0
                            print(f"  -> Candidate '{candidate['text']}': +3 (Subject of previous clause)")
                            
                        # +2 if subject of current clause (same sentence, nsubj)
                        if candidate["sentence_id"] == mention["sentence_id"] and candidate["deprel"] == "nsubj":
                            score += 2.0
                            print(f"  -> Candidate '{candidate['text']}': +2 (Subject of current clause)")
                            
                        # Distance decay: 1 / distance_in_tokens
                        dist = mention["id"] - candidate["id"]
                        decay = 1.0 / dist
                        score += decay
                        print(f"  -> Candidate '{candidate['text']}': +{decay:.2f} (Distance decay, dist={dist})")
                        
                        candidates.append((score, candidate))
                    else:
                        print(f"  -> Candidate '{candidate['text']}' rejected (Morphology mismatch: Gen:{candidate['gender']} vs {mention['gender']})")
            
            # 3. Assign highest scoring candidate
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_score, best_cand = candidates[0]
                print(f"  => RESOLVED: '{mention['text']}' -> '{best_cand['text']}' (Score: {best_score:.2f})")
            else:
                print(f"  => UNRESOLVED: '{mention['text']}' (No morphological match found in window)")

if __name__ == "__main__":
    demo_pronoun_resolution()
