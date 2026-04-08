#!/usr/bin/env python3
"""
Build evaluation dataset for pro-drop resolution.
For each pro-drop verb, includes:
- Full context (5 verses)
- All entities in the window
- Sentence text
- Gold answer (to be determined by rules/LLM)
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd


def parse_proiel_morphology(morph):
    """Parse PROIEL morphology code."""
    if not morph or morph == "---------n":
        return None, None, None

    person = None
    number = None
    voice = None

    if len(morph) >= 4:
        person_char = morph[0]
        number_char = morph[2]
        voice_char = morph[3] if len(morph) > 3 else None

        if person_char in "123":
            person = int(person_char)
        if number_char in "sp":
            number = "singular" if number_char == "s" else "plural"
        if voice_char:
            voice = "mediopass" if voice_char in "mM" else "active"

    return person, number, voice


def is_participle(morph):
    """Check if verb form is a participle."""
    if not morph:
        return True
    return "p" in morph[3:5] if len(morph) > 4 else False


def is_genitive_absolute(sent_tokens, verb_idx):
    """Check if verb is in genitive absolute construction."""
    if verb_idx > 0:
        prev_token = sent_tokens[verb_idx - 1]
        if prev_token.get("relation") in ["adv", "atr"]:
            return True
    return False


def has_delta_adversative(sent_tokens):
    """Check if sentence contains δέ (but) which signals contrast."""
    for token in sent_tokens:
        if token["form"] == "δέ":
            return True
    return False


def has_tote_marker(sent_tokens):
    """Check if sentence contains τότε (then) which signals narrative shift."""
    for token in sent_tokens:
        if token["form"] == "τότε":
            return True
    return False


def extract_context_verses(df, ref, window=5):
    """Get N verses of context before current verse."""
    parts = ref.split()
    book = parts[0]
    chapter_verse = parts[1]
    chapter = chapter_verse.split(".")[0]
    verse_num = int(chapter_verse.split(".")[-1])

    verses = []
    for v in range(max(1, verse_num - window), verse_num + 1):
        verse_ref = f"{book} {chapter}.{v}"
        verse_df = df[df["ref"] == verse_ref]
        if not verse_df.empty:
            tokens = verse_df.sort_values("token_id")["form"].tolist()
            verses.append({"ref": verse_ref, "text": " ".join(tokens)})

    return verses


def extract_entities(df, verse_ref, window=5, sentence_text=None):
    """Extract all person entities in verse window."""
    entities = []

    # Parse ref - format is "MARK 1.9"
    parts = verse_ref.split()
    book = parts[0]  # "MARK"
    chapter_verse = parts[1]  # "1.9"
    chapter = chapter_verse.split(".")[0]  # "1"
    verse_num = int(chapter_verse.split(".")[-1])  # 9

    # Known character names for text-based extraction
    # Key: form to search, Value: canonical lemma
    KNOWN_CHARACTERS = {
        # Jesus - all cases
        "Ἰησοῦς": "Ἰησοῦς",
        "Ἰησοῦν": "Ἰησοῦς",
        "Ἰησοῦ": "Ἰησοῦς",
        "Ἰησοῖς": "Ἰησοῦς",
        "Ἰησοῦν": "Ἰησοῦς",
        # Peter - all cases
        "Πέτρος": "Πέτρος",
        "Πέτρον": "Πέτρος",
        "Πέτρῳ": "Πέτρος",
        "Πέτρου": "Πέτρος",
        "Σίμων": "Σίμων",
        "Σίμωνα": "Σίμων",
        "Σίμωνος": "Σίμων",
        # John - all cases (including variants with nu-dropping)
        "Ἰωάννης": "Ἰωάννης",
        "Ἰωάννην": "Ἰωάννης",
        "Ἰωάννου": "Ἰωάννης",
        "Ἰωάννῳ": "Ἰωάννης",
        "Ἰωάν(ν)ης": "Ἰωάννης",
        # James
        "Ἰάκωβος": "Ἰάκωβος",
        "Ἰακώβου": "Ἰάκωβος",
        "Ἰακώβῳ": "Ἰάκωβος",
        "Ἰάκωβον": "Ἰάκωβος",
        # Andrew
        "Ἀνδρέας": "Ἀνδρέας",
        "Ἀνδρέαν": "Ἀνδρέας",
        "Ἀνδρέου": "Ἀνδρέας",
        # Philip
        "Φίλιππος": "Φίλιππος",
        "Φιλίππου": "Φίλιππος",
        # Bartholomew
        "Βαρθολομαῖος": "Βαρθολομαῖος",
        # Matthew
        "Ματθαῖος": "Ματθαῖος",
        "Ματθίου": "Ματθαῖος",
        # Thomas
        "Θωμᾶς": "Θωμᾶς",
        "Θωμᾶ": "Θωμᾶς",
        # Paul
        "Παῦλος": "Παῦλος",
        "Παύλου": "Παῦλος",
        "Παῦλον": "Παῦλος",
        # Stephen
        "Στέφανος": "Στέφανος",
        # Herod
        "Ἡρῴδης": "Ἡρῴδης",
        "Ἡρῴδου": "Ἡρῴδης",
        # Pilate
        "Πιλᾶτος": "Πιλᾶτος",
        "Πιλάτου": "Πιλᾶτος",
        # Caiaphas
        "Καϊάφας": "Καϊάφας",
        # David
        "Δαυείδ": "Δαυείδ",
        # Moses
        "Μωϋσῆς": "Μωϋσῆς",
        # Satan
        "σατανᾶς": "σατανᾶς",
        "Σατανᾶς": "σατανᾶς",
        # Zebedee
        "Ζεβεδαῖος": "Ζεβεδαῖος",
        "Ζεβεδαίου": "Ζεβεδαῖος",
        # Jairus
        "Ἰάειρος": "Ἰάειρος",
        # Lazarus
        "Λάζαρος": "Λάζαρος",
        # Nicodemus
        "Νικόδημος": "Νικόδημος",
        # Samaritan Woman
        "Σαμαρείτις": "Σαμαρείτις",
        # Centurion
        "κεντυρίων": "κεντυρίων",
        "ἑκατοντάρχης": "ἑκατοντάρχης",
        # Priests
        "ἀρχιερεύς": "ἀρχιερεύς",
        "ἀρχιερέως": "ἀρχιερεύς",
        # Levite
        "Λευίτης": "Λευίτης",
        # Blind man (Jericho)
        "Βαρτίμαιος": "Βαρτίμαιος",
        # Bartimaeus
        "Τιμαῖος": "Τιμαῖος",
        # Demoniac (Gerasene)
        "Λεγεών": "Λεγεών",
        # Syrophoenician woman
        "Σύρος": "Σύρος",
        # mute/spirit
        "πνεῦμα": "πνεῦμα",
        "δαιμόνιον": "δαιμόνιον",
        "δαιμόνια": "δαιμόνιον",
    }

    # Track seen lemmas to avoid duplicates
    seen_lemmas = set()

    for v in range(max(1, verse_num - window), verse_num + 1):
        verse_r = f"{book} {chapter}.{v}"
        verse_df = df[df["ref"] == verse_r]

        for _, row in verse_df.iterrows():
            pos = row.get("pos", row.get("POS"))
            lemma = row.get("lemma", row.get("LEMMA"))
            form = row.get("form", row.get("FORM"))
            ref = row.get("ref", row.get("ref"))
            morph = row.get("morphology", row.get("MORPH"))

            if not pos:
                continue

            # Proper nouns (Ne) are character names
            if pos == "Ne" and lemma:
                if lemma not in seen_lemmas:
                    seen_lemmas.add(lemma)
                    person, number, _ = parse_proiel_morphology(morph)
                    entities.append(
                        {
                            "form": form,
                            "lemma": lemma,
                            "ref": ref,
                            "person": person,
                            "number": number,
                            "pos": pos,
                            "source": "pos_match",
                        }
                    )

            # Also check for known characters via form matching
            if form in KNOWN_CHARACTERS:
                lemma = KNOWN_CHARACTERS[form]
                if lemma not in seen_lemmas:
                    seen_lemmas.add(lemma)
                    entities.append(
                        {
                            "form": form,
                            "lemma": lemma,
                            "ref": ref,
                            "person": 3,
                            "number": "singular",
                            "pos": "known_char",
                            "source": "known_char",
                        }
                    )

    # Also try to extract from sentence text (if provided) or verse text
    if sentence_text:
        text_to_search = sentence_text
    else:
        verse_r = f"{book} {chapter}.{verse_num}"
        verse_df = df[df["ref"] == verse_r]
        text_to_search = " ".join(verse_df["form"].tolist())

    for char_form, char_lemma in KNOWN_CHARACTERS.items():
        if char_form in text_to_search and char_lemma not in seen_lemmas:
            seen_lemmas.add(char_lemma)
            entities.append(
                {
                    "form": char_form,
                    "lemma": char_lemma,
                    "ref": verse_ref,
                    "person": 3,
                    "number": "singular",
                    "pos": "known_char",
                    "source": "text_search",
                }
            )

    return entities


def classify_difficulty(sent_tokens, verb_idx, entities_in_window):
    """Classify pro-drop difficulty level."""

    # Check for narrative markers
    has_delta = has_delta_adversative(sent_tokens)
    has_tote = has_tote_marker(sent_tokens)
    is_gen_abs = is_genitive_absolute(sent_tokens, verb_idx)

    # Level 3: Complex cases
    if has_delta or has_tote or is_gen_abs:
        return 3

    # Count compatible entities
    # For now, simplified: if we have clear entities in sentence, it's Level 1
    person_entities = [e for e in entities_in_window if e["pos"] == "Ne"]

    if len(person_entities) == 1:
        return 1
    elif len(person_entities) > 1:
        # Check if all are same person/number
        lemmas = set(e["lemma"] for e in person_entities)
        if len(lemmas) == 1:
            return 1  # Same entity, easy
        else:
            return 2  # Multiple entities, ambiguous
    else:
        return 2  # No clear entities, need broader context


def build_evaluation_dataset(df, corpus_name, verse_filter=None):
    """Build evaluation dataset for a corpus."""
    instances = []

    if verse_filter:
        df = df[df["ref"].str.startswith(verse_filter, na=False)].copy()

    # Group by sentence
    sentences = df.groupby("sentence_id")

    for sent_id, sent_df in sentences:
        sent_df = sent_df.sort_values("token_id")
        tokens = sent_df.to_dict("records")

        # Find finite 3rd person verbs without subject
        for verb_idx, token in enumerate(tokens):
            if token["pos"] != "V-":
                continue

            person, number, _ = parse_proiel_morphology(token["morphology"])

            # Skip 1st/2nd person and participles
            if person != 3 or is_participle(token["morphology"]):
                continue

            # Check for explicit subject
            has_subject = False
            for other in tokens:
                if other["head_id"] == token["token_id"] and other["relation"] in [
                    "sub",
                    "nsubj",
                ]:
                    has_subject = True
                    break

            if has_subject:
                continue  # Not pro-drop

            # This is a pro-drop verb
            verse_ref = token["ref"]

            # Build sentence text first (needed for entity extraction)
            sentence_text = " ".join([t["form"] for t in tokens])

            # Get entities in window (expanded to 5 verses, with text fallback)
            entities = extract_entities(
                df, verse_ref, window=5, sentence_text=sentence_text
            )

            # Classify difficulty
            difficulty = classify_difficulty(tokens, verb_idx, entities)

            # Get context (5 verses before)
            context = extract_context_verses(df, verse_ref, window=5)
            context_text = " ".join([c["text"] for c in context])

            instance = {
                "id": len(instances),
                "corpus": corpus_name,
                "verse_ref": verse_ref,
                "sentence_id": str(sent_id),
                "sentence_text": sentence_text,
                "context_5verses": context_text,
                "verb_form": token["form"],
                "verb_lemma": token["lemma"],
                "person": person,
                "number": number,
                "morph": token["morphology"],
                "difficulty_level": difficulty,
                "entities_in_window": entities,
                "entity_lemmas": list(set(e["lemma"] for e in entities)),
                "narrative_markers": {
                    "delta_adversative": has_delta_adversative(tokens),
                    "tote_shift": has_tote_marker(tokens),
                    "genitive_absolute": is_genitive_absolute(tokens, verb_idx),
                },
            }
            instances.append(instance)

    return instances


def main():
    df = pd.read_csv("project/data/proiel_coref.csv", low_memory=False)

    all_instances = []

    # Process Mark 1:1-4:26 as primary dataset
    mark_df = df[df["book"] == "MARK"].copy()
    mark_instances = build_evaluation_dataset(mark_df, "Mark_1_1_4_26")
    all_instances.extend(mark_instances)

    print(f"Total pro-drop instances in Mark 1:1-4:26: {len(mark_instances)}")

    # Stats by difficulty
    level_counts = defaultdict(int)
    for inst in mark_instances:
        level_counts[inst["difficulty_level"]] += 1

    print("\nDifficulty distribution:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} instances")

    # Sample instances by level
    print("\n--- Sample by Difficulty Level ---")
    for level in [1, 2, 3]:
        level_insts = [i for i in mark_instances if i["difficulty_level"] == level]
        if level_insts:
            print(f"\nLevel {level} examples:")
            for inst in level_insts[:3]:
                print(
                    f"  {inst['verse_ref']}: {inst['verb_form']} ({inst['verb_lemma']})"
                )
                print(f"    Entities: {inst['entity_lemmas'][:5]}")
                print(f"    Markers: {inst['narrative_markers']}")

    # Save
    os.makedirs("project/data/experiments/sprint2c", exist_ok=True)
    output = {
        "total_instances": len(all_instances),
        "instances": all_instances,
        "level_counts": dict(level_counts),
    }

    with open(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"\nSaved to project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    )


if __name__ == "__main__":
    main()
