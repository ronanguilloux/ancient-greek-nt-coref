#!/usr/bin/env python3
"""
Extract TRUE gold standard from PROIEL treebank for pro-drop evaluation.

PROIEL contains antecedent-id links that point to antecedent tokens.
This script properly follows chains to find the true antecedent person.
"""

import json
import os
from lxml import etree
from typing import Optional, Dict, List


def parse_proiel(proiel_path: str) -> Dict:
    """Parse PROIEL XML and build token index."""
    tree = etree.parse(proiel_path)
    root = tree.getroot()

    sentences = {}
    tokens = {}

    for sentence in root.iter("sentence"):
        sid = sentence.get("id")
        sentence_data = {"id": sid, "tokens": []}

        for token in sentence.iter("token"):
            tid = token.get("id")
            tok_data = {
                "id": tid,
                "form": token.get("form", ""),
                "lemma": token.get("lemma", ""),
                "pos": token.get("part-of-speech", ""),
                "relation": token.get("relation", ""),
                "antecedent_id": token.get("antecedent-id"),
                "head_id": token.get("head-id"),
            }
            sentence_data["tokens"].append(tok_data)
            tokens[tid] = tok_data

        sentences[sid] = sentence_data

    return sentences, tokens


def follow_antecedent_chain(
    token_id: str, tokens: Dict, max_depth: int = 20
) -> Optional[Dict]:
    """Follow antecedent chain to the original referent."""
    visited = set()
    current_id = token_id

    while current_id and max_depth > 0:
        if current_id in visited:
            break
        visited.add(current_id)

        token = tokens.get(current_id)
        if not token:
            break

        antec_id = token.get("antecedent_id")
        if antec_id and antec_id != current_id:
            current_id = antec_id
            max_depth -= 1
        else:
            return token

    return None


# Canonical entity mapping
PERSON_LEMMAS = {
    "Ἰησοῦς",
    "Ἰησοῦν",
    "Ἰησοῦ",
    "Ἰησοῖς",
    "Χριστός",
    "Χριστὸν",
    "Χριστοῦ",
    "Κύριος",
    "Κύριον",
    "Κυρίου",
    "διδάσκαλος",
    "διδάσκαλον",
    "διδασκάλου",
    "Πέτρος",
    "Πέτρον",
    "Πέτρου",
    "Πέτρῳ",
    "Σίμων",
    "Σίμωνα",
    "Κηφᾶς",
    "Κηφᾶν",
    "Ἰωάννης",
    "Ἰωάννην",
    "Ἰωάννου",
    "Ἰωάννῳ",
    "Ἰωάν(ν)ης",
    "Ἰωάνης",
    "Ἰωάνου",
    "Ἰωάνῃ",
    "Ἰάκωβος",
    "Ἰακώβου",
    "Ἰακώβῳ",
    "Ἰάκωβον",
    "Ἀνδρέας",
    "Ἀνδρέαν",
    "Ἀνδρέου",
    "Ἀνδρέᾳ",
    "Παῦλος",
    "Παύλου",
    "Παῦλον",
    "Παύλῳ",
    "Σαῦλος",
    "Σαύλου",
    "Σαῦλον",
    "Φίλιππος",
    "Φιλίππου",
    "Φίλιππον",
    "Φιλίππῳ",
    "Βαρθολομαῖος",
    "Βαρθολομαίου",
    "Βαρθολομαῖον",
    "Θωμᾶς",
    "Θωμᾶν",
    "Θωμᾶ",
    "Ματθαῖος",
    "Ματθαίου",
    "Ματθαῖον",
    "Ματθίαν",
    "Στέφανος",
    "Στεφάνου",
    "Στέφανον",
    "Βαρνάβας",
    "Βαρναβᾶ",
    "Βαρνάβαν",
    "Λάζαρος",
    "Λαζάρου",
    "Λάζαρον",
    "Νικόδημος",
    "Νικοδήμου",
    "Νικόδημον",
    "Μαρία",
    "Μαρίας",
    "Μαρίαν",
    "Πιλᾶτος",
    "Πιλάτου",
    "Πιλᾶτον",
    "Πιλάτῳ",
    "Ἀνανίας",
    "Ἀνανίου",
    "Ἀνανίαν",
    "Τιμόθεος",
    "Τιμοθέου",
    "Τιμόθεον",
    "Τιμοθέῳ",
    "Σίλας",
    "Σίλα",
    "Σίλαν",
    "Τίτος",
    "Ἀπολλώς",
    "Ἀγρίππας",
    "Φῆλιξ",
    "Καϊάφας",
    "Ἠλίας",
    "Ἐλισαῖος",
    "Μωϋσῆς",
    "Ἀαρών",
    # Groups
    "μαθητής",
    "μαθηταί",
    "μαθητὰς",
    "μαθητῇ",
    "ἀπόστολος",
    "ἀπόστολοι",
    "ἀποστόλων",
}

PERSON_CANONICAL = {
    "Ἰησοῦς": "IESOUS",
    "Ἰησοῦν": "IESOUS",
    "Ἰησοῦ": "IESOUS",
    "Χριστός": "IESOUS",
    "Κύριος": "IESOUS",
    "διδάσκαλος": "IESOUS",
    "Πέτρος": "PETROS",
    "Σίμων": "PETROS",
    "Κηφᾶς": "PETROS",
    "Ἰωάννης": "IOANNES",
    "Ἰωάν(ν)ης": "IOANNES",
    "Ἰάκωβος": "IAKOBOS",
    "Ἀνδρέας": "ANDREAS",
    "Παῦλος": "PAULOS",
    "Σαῦλος": "PAULOS",
    "Φίλιππος": "PHILIPPOS",
    "Βαρθολομαῖος": "BARTHOLOMAIOS",
    "Θωμᾶς": "THOMAS",
    "Ματθαῖος": "MATTHIAS",
    "Στέφανος": "STEPHANOS",
    "Βαρνάβας": "BARNABAS",
    "Λάζαρος": "LAZAROS",
    "Νικόδημος": "NICODEMOS",
    "Μαρία": "MARIA",
    "Πιλᾶτος": "PILATOS",
    "Ἀνανίας": "ANANIAS",
    "Τιμόθεος": "TIMOTHEOS",
    "Σίλας": "SILAS",
    "Τίτος": "TITUS",
    "Ἀπολλώς": "APOLLOS",
    "Ἀγρίππας": "AGRIPPAS",
    "Ἠλίας": "ELIAS",
    "Ἐλισαῖος": "ELISAEUS",
    "Μωϋσῆς": "MOYSES",
    "Ἀαρών": "AARON",
    # Groups
    "μαθητής": "OI_MATHETAI",
    "μαθηταί": "OI_MATHETAI",
    "μαθητὰς": "OI_MATHETAI",
    "μαθητῇ": "OI_MATHETAI",
    "ἀπόστολος": "OI_APOSTOLOI",
    "ἀπόστολοι": "OI_APOSTOLOI",
}

# Place/entity names that shouldn't be subjects
NON_SUBJECT_LEMMAS = {
    "Καφαρναούμ",
    "Ναζαρά",
    "Ναζαρεθ",
    "Ἰορδάνης",
    "Γαλιλαία",
    "Γαλιλαίαν",
    "Ἱεροσόλυμα",
    "Ἰερουσαλήμ",
    "Βηθανία",
    "Βηθσαϊδά",
    "Κορίνθος",
    "Ἔφεσος",
    "Γεννησαρὲτ",
    "Τύρος",
    "Σιδών",
}


def resolve_to_entity(antecedent: Dict) -> Optional[str]:
    """Resolve antecedent to canonical entity."""
    if not antecedent:
        return None

    lemma = antecedent.get("lemma", "").strip()
    pos = antecedent.get("pos", "")
    form = antecedent.get("form", "").strip()

    # Skip places and non-person entities
    if lemma in NON_SUBJECT_LEMMAS or form in NON_SUBJECT_LEMMAS:
        return None

    # Map known person lemmas
    if lemma in PERSON_CANONICAL:
        return PERSON_CANONICAL[lemma]

    # Check if it's a noun referring to people
    if pos.startswith("Ne"):
        return lemma.upper() if lemma else None

    return None


def find_null_subject_in_sentence(
    sentence_tokens: List[Dict], verb_form: str, verb_lemma: str
) -> Optional[Dict]:
    """Find the null subject token for a given verb."""
    verb_idx = -1
    for i, token in enumerate(sentence_tokens):
        if token.get("form") == verb_form or verb_lemma.replace("#1", "") in token.get(
            "lemma", ""
        ):
            if token.get("pos", "").startswith("V"):
                verb_idx = i
                break

    if verb_idx == -1:
        return None

    # Look backwards for null subject
    for i in range(verb_idx - 1, -1, -1):
        token = sentence_tokens[i]
        if not token.get("form") and token.get("antecedent_id"):
            return token
        if token.get("form") and token.get("pos", "").startswith(
            ("V", "N", "Ne", "Ri", "Rd")
        ):
            break

    return None


def main():
    print("=" * 60)
    print("PROIEL TRUE Gold Standard Extractor v2")
    print("=" * 60)

    sentences, tokens = parse_proiel("proiel-treebank/data/greek-nt.xml")
    print(f"Loaded {len(sentences)} sentences, {len(tokens)} tokens")

    with open(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json", "r"
    ) as f:
        eval_data = json.load(f)

    instances = eval_data["instances"]
    print(f"Evaluating {len(instances)} instances")

    gold_results = []
    stats = {
        "total": len(instances),
        "null_found": 0,
        "no_null": 0,
        "person_antecedent": 0,
        "non_person_antecedent": 0,
        "no_antecedent": 0,
    }

    person_entities = {}

    for inst in instances:
        sid = inst.get("sentence_id")
        result = {
            "instance_id": inst.get("id"),
            "verse_ref": inst.get("verse_ref"),
            "verb_form": inst.get("verb_form"),
            "difficulty_level": inst.get("difficulty_level"),
        }

        sentence = sentences.get(sid)
        if not sentence:
            result["error"] = "SENTENCE_NOT_FOUND"
            gold_results.append(result)
            continue

        null_subject = find_null_subject_in_sentence(
            sentence["tokens"], inst.get("verb_form"), inst.get("verb_lemma")
        )

        if null_subject:
            stats["null_found"] += 1
            antecedent = follow_antecedent_chain(null_subject["id"], tokens)

            if antecedent:
                entity = resolve_to_entity(antecedent)
                result["antecedent_token_id"] = antecedent["id"]
                result["antecedent_form"] = antecedent.get("form", "")
                result["antecedent_lemma"] = antecedent.get("lemma", "")
                result["antecedent_pos"] = antecedent.get("pos", "")
                result["antecedent_entity"] = entity

                if entity:
                    stats["person_antecedent"] += 1
                    person_entities[entity] = person_entities.get(entity, 0) + 1
                else:
                    stats["non_person_antecedent"] += 1
            else:
                stats["no_antecedent"] += 1
                result["note"] = "CHAIN_BROKEN"
        else:
            stats["no_null"] += 1
            result["note"] = "NO_NULL_SUBJECT"

        gold_results.append(result)

    print()
    print("=" * 60)
    print("PROIEL GOLD EXTRACTION RESULTS")
    print("=" * 60)
    print()
    print(f"Total: {stats['total']}")
    print(
        f"Null subject found: {stats['null_found']} ({100 * stats['null_found'] / stats['total']:.1f}%)"
    )
    print(
        f"Person antecedent: {stats['person_antecedent']} ({100 * stats['person_antecedent'] / stats['total']:.1f}%)"
    )
    print(
        f"Non-person antecedent: {stats['non_person_antecedent']} ({100 * stats['non_person_antecedent'] / stats['total']:.1f}%)"
    )
    print(f"No null subject: {stats['no_null']}")
    print()
    print("Person entity distribution:")
    for e, c in sorted(person_entities.items(), key=lambda x: -x[1]):
        print(f"  {e}: {c}")

    print()
    print("Sample Level 2+3 with person antecedents:")
    for r in gold_results:
        if r.get("difficulty_level", 0) >= 2 and r.get("antecedent_entity"):
            print(f"  {r['verse_ref']}: {r['verb_form']} → {r['antecedent_entity']}")
            if len([x for x in gold_results if x.get("antecedent_entity")]) > 20:
                break

    # Save
    with open(
        "project/data/experiments/sprint2c/proiel_gold_standard.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "metadata": {"source": "PROIEL", "date": "2026-04-08", "stats": stats},
                "gold_results": gold_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Saved to: project/data/experiments/sprint2c/proiel_gold_standard.json")


if __name__ == "__main__":
    main()
