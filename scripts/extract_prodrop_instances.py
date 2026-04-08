#!/usr/bin/env python3
"""
Extract pro-drop instances with gold antecedents from PROIEL data.
Uses the antecedent links on pronouns to build entity chains, then infers
the implied subject of null-subject verbs.
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
    # PROIEL: participles have specific morphology codes
    # 'p' at position 3 or 4 = participle
    return "p" in morph[3:5] if len(morph) > 4 else False


def load_proiel_csv(csv_path):
    """Load PROIEL data from CSV."""
    import pandas as pd

    df = pd.read_csv(csv_path, low_memory=False)
    return df


def build_entity_chains(df, book):
    """Build entity chains from antecedent links within a book."""
    book_df = df[df["book"] == book].copy()

    # Create a map of token_id -> token info
    token_map = {}
    for _, row in book_df.iterrows():
        token_map[row["token_id"]] = {
            "form": row["form"],
            "lemma": row["lemma"],
            "pos": row["pos"],
            "ref": row["ref"],
            "antecedent_id": row["antecedent_id"],
        }

    # Build chains by following antecedent links
    chains = defaultdict(list)
    for tid, token in token_map.items():
        if pd.notna(token["antecedent_id"]):
            ant_id = int(token["antecedent_id"])
            if ant_id in token_map:
                chains[ant_id].append(tid)

    return token_map, chains


def resolve_antecedent(token_id, token_map, chains):
    """Resolve the head of an entity chain."""
    # Find the chain this token belongs to
    for head_id, members in chains.items():
        if token_id == head_id or token_id in members:
            return head_id
    return token_id


def extract_prodrop_instances(df, corpus_name, verses_filter=None):
    """Extract pro-drop instances from a corpus."""
    instances = []

    if verses_filter:
        df = df[df["ref"].str.startswith(verses_filter, na=False)]

    # Group by sentence for context
    sentences = df.groupby("sentence_id")

    for sent_id, sent_df in sentences:
        sent_df = sent_df.sort_values("token_id")

        # Get all tokens and their info
        tokens = sent_df.to_dict("records")

        # Find finite verbs (not participles)
        for token in tokens:
            if token["pos"] == "V-":
                person, number, _ = parse_proiel_morphology(token["morphology"])

                # Skip non-finite forms (participles)
                if is_participle(token["morphology"]):
                    continue

                # Check if this verb has a subject noun in the sentence
                has_subject = False
                subject_token = None

                # Look for noun with nsubj relation
                for other in tokens:
                    if other["head_id"] == token["token_id"] and other["relation"] in [
                        "sub",
                        "nsubj",
                    ]:
                        has_subject = True
                        subject_token = other
                        break

                # Pro-drop if no explicit subject
                if not has_subject and person == 3:  # 3rd person only
                    # Find entities in context (this sentence + previous)
                    verse_ref = token["ref"]
                    chapter = verse_ref.split()[0] if verse_ref else "UNKNOWN"
                    verse_num = (
                        verse_ref.split(".")[-1]
                        if verse_ref and "." in verse_ref
                        else "0"
                    )

                    # Get all entities (nouns, proper nouns) in this sentence
                    entities_in_sent = []
                    for t in tokens:
                        if t["pos"] in ["Ne", "Nb"] and t["lemma"]:
                            entities_in_sent.append(
                                {
                                    "form": t["form"],
                                    "lemma": t["lemma"],
                                    "deprel": t["relation"],
                                }
                            )

                    # Get narrative context - who is the main subject before?
                    # Use antecedent links to build entity chains
                    prev_entities = []

                    # Get context from PROIEL - look for most recent 3sg-compatible entity
                    # by checking antecedent links
                    for t in tokens:
                        if t["pos"] == "Pp" and pd.notna(t["antecedent_id"]):
                            ant_id = int(t["antecedent_id"])
                            if ant_id in df["token_id"].values:
                                ant_rows = df[df["token_id"] == ant_id]
                                if not ant_rows.empty:
                                    ant = ant_rows.iloc[0]
                                    if ant["lemma"]:
                                        prev_entities.append(
                                            {
                                                "form": ant["form"],
                                                "lemma": ant["lemma"],
                                                "source_ref": ant["ref"],
                                            }
                                        )

                    # Determine gold entity from context
                    # In PROIEL, the gold antecedent is encoded in the antecedent links
                    # For pro-drop, we infer from narrative flow
                    gold_entity = None

                    # Heuristic: the most recent 3rd person singular entity
                    recent_sg = [
                        e
                        for e in prev_entities
                        if e.get("source_ref", "").startswith(corpus_name.split("_")[0])
                    ]
                    if recent_sg:
                        gold_entity = (
                            recent_sg[-1]["lemma"].upper() if recent_sg else None
                        )

                    # Alternative: check if this is a continuation of a speech
                    # by looking at λέγω/εἶπεν patterns
                    is_speech_continuation = False
                    for t in tokens:
                        if t["lemma"] in ["λέγω", "εἶπεν", "ἀποκρίνω"]:
                            is_speech_continuation = True
                            break

                    instance = {
                        "corpus": corpus_name,
                        "verse_ref": verse_ref,
                        "sentence_id": str(sent_id),
                        "verb_form": token["form"],
                        "verb_lemma": token["lemma"],
                        "person": person,
                        "number": number,
                        "morph": token["morphology"],
                        "is_prodrop": True,
                        "entities_in_sentence": entities_in_sent,
                        "previous_entities": prev_entities[-5:],  # Last 5
                        "gold_entity": gold_entity,
                        "is_speech_continuation": is_speech_continuation,
                        "sentence_text": " ".join(
                            [
                                t["form"]
                                for t in sorted(tokens, key=lambda x: x["token_id"])
                            ]
                        ),
                    }
                    instances.append(instance)

    return instances


def main():
    # Load PROIEL data
    df = load_proiel_csv("project/data/proiel_coref.csv")

    # Process each gold corpus
    gold_files = list(Path("project/data/gold").glob("*.conllu"))

    all_instances = []

    for gold_file in gold_files:
        corpus_name = gold_file.stem
        print(f"\nProcessing {corpus_name}...")

        # Get book prefix from filename
        if "Mark" in corpus_name:
            book_filter = "MARK"
        elif "John" in corpus_name:
            book_filter = "JOHN"
        elif "Acts" in corpus_name:
            book_filter = "ACTS"
        else:
            book_filter = None

        if book_filter:
            corpus_df = df[df["book"] == book_filter].copy()
        else:
            corpus_df = df.copy()

        # Extract instances
        instances = extract_prodrop_instances(corpus_df, corpus_name)
        all_instances.extend(instances)

        print(f"  Found {len(instances)} pro-drop instances")

    # Filter to Marc 1:1-4:26 for our main experiment
    marc_1_1_4_26 = [i for i in all_instances if i["corpus"] == "Mark_1_1_4_26"]
    print(f"\nMarc 1:1-4:26 pro-drop instances: {len(marc_1_1_4_26)}")

    # Print sample
    print("\n--- Sample Marc 1:1-4:26 Instances ---")
    for inst in marc_1_1_4_26[:10]:
        print(f"  {inst['verse_ref']}: {inst['verb_form']} ({inst['verb_lemma']})")
        print(f"    Entities: {[e['lemma'] for e in inst['entities_in_sentence']]}")
        print(f"    Gold: {inst['gold_entity']}")

    # Save all instances
    os.makedirs("project/data/experiments/sprint2c", exist_ok=True)
    output = {"all_instances": all_instances, "marc_1_1_4_26": marc_1_1_4_26}

    with open(
        "project/data/experiments/sprint2c/prodrop_instances.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"\nSaved {len(all_instances)} total instances to project/data/experiments/sprint2c/prodrop_instances.json"
    )


if __name__ == "__main__":
    main()
