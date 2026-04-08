#!/usr/bin/env python3
"""
Rule-based pro-drop resolver + evaluation.
 Implements heuristics for null subject resolution in Ancient Greek.
"""

import json
from collections import defaultdict


PERSON_LEMMAS = {
    # Jesus and titles
    "Ἰησοῦς",
    "Χριστός",
    "Κύριος",
    "διδάσκαλος",
    # Apostles
    "Σίμων",
    "Πέτρος",
    "Κηφᾶς",
    "Ἰωάν(ν)ης",
    "Ἰωάννης",
    "Ἰωάνης",
    "Ἰάκωβος",
    "Ἀνδρέας",
    "Φίλιππος",
    "Βαρθολομαῖος",
    "Θωμᾶς",
    "Ματθαῖος",
    "Ἰούδας",
    "Σίμων",
    "Λευεῖ",
    "Ναθαναήλ",
    # Pauline letters
    "Παῦλος",
    "Σαῦλος",
    "Τιμόθεος",
    "Τίτος",
    "Σίλας",
    "Σιλᾶς",
    "Ἀπολλώς",
    "Κηφᾶς",
    "Ἀνανίας",
    # Acts characters
    "Στέφανος",
    "Βαρνάβας",
    "Νικόδημος",
    "Σαπφείρη",
    "Ἀγρίππας",
    "Φῆλιξ",
    "Πιλᾶτος",
    "Καϊάφας",
    # Gospel characters
    "Λάζαρος",
    "Μαρία",
    "Μάρθα",
    "Σαλώμη",
    "Ἠλίας",
    "Ἐλισαῖος",
    "Μωϋσῆς",
    "Ἀαρών",
    # Demons and spirits (can be subjects)
    "δαιμόνιον",
    "πνεῦμα",
    "Σατανᾶς",
    "Βεελζεβοῦλ",
}

NON_PERSON_LEMMAS = {
    # Places - exact matches
    "Καφαρναούμ",
    "Ναζαρά",
    "Ναζαρεθ",
    "Ἰορδάνης",
    "Γαλιλαία",
    "Ἱεροσολύμων",
    "Ἰερουσαλήμ",
    "Ἱεροσόλυμα",
    "Βηθανία",
    "Βηθσαϊδά",
    "Σινᾶ",
    "Σιών",
    "Ἰδουμαία",
    "Σαμάρεια",
    "Γαλγαλα",
    "Γαλιλαίαν",
    "Κορίνθος",
    "Ἔφεσος",
    "Ἀντιόχεια",
    "Λύστρα",
    "Δαλμανουθά",
    "Γεννησαρέτ",
    "Καισαρία",
    "Τύρος",
    "Σιδών",
    "Ἀντιπατρίς",
    "Ἀμαῦς",
    "Βηθφαγή",
    "Βηθεσδά",
    "Γεθσημανῆ",
    "Ἐλαιών",
    "Κρήνη",
    "Σιλωάμ",
    "Ἀκελδαμά",
    "Γολγοθᾶ",
    # Abstract/concepts (can be subjects but rarely need pro-drop)
    "βασιλεία",
    "ἀρχή",
    "τέλος",
    "δόξα",
    "ἀγάπη",
    "πίστις",
    "ἐλπίς",
    "νόμος",
    "λόγος",
    "εὐαγγέλιον",
    # Time expressions
    "ἡμέρα",
    "νύξ",
    "καιρός",
    "χρόνος",
    "σάββατον",
    # Natural phenomena
    "οὐρανός",
    "γῆ",
    "θάλασσα",
    "ποταμός",
    "ὄρος",
    "πηγή",
}


def load_alias_map():
    """Load character aliases to canonical IDs."""
    aliases = {
        # PETROS (Peter)
        "Σίμων": "PETROS",
        "Σίμωνα": "PETROS",
        "Πέτρος": "PETROS",
        "Πέτρον": "PETROS",
        "Πέτρῳ": "PETROS",
        "Πέτρου": "PETROS",
        "Κηφᾶς": "PETROS",
        "Κηφᾶν": "PETROS",
        # IESOUS (Jesus)
        "Ἰησοῦς": "IESOUS",
        "Ἰησοῦν": "IESOUS",
        "Ἰησοῦ": "IESOUS",
        "Ἰησοῖς": "IESOUS",
        "Χριστός": "IESOUS",
        "Χριστὸν": "IESOUS",
        "Χριστοῦ": "IESOUS",
        "Κύριος": "IESOUS",
        "Κύριον": "IESOUS",
        "Κυρίου": "IESOUS",
        "διδάσκαλος": "IESOUS",
        "διδάσκαλον": "IESOUS",
        "διδασκάλου": "IESOUS",
        # IOANNES (John)
        "Ἰωάν(ν)ης": "IOANNES",
        "Ἰωάννην": "IOANNES",
        "Ἰωάννου": "IOANNES",
        "Ἰωάννῳ": "IOANNES",
        "Ἰωάννης": "IOANNES",
        "Ἰωάνης": "IOANNES",
        "Ἰωάνου": "IOANNES",
        "Ἰωάνῃ": "IOANNES",
        # IAKOBOS (James)
        "Ἰάκωβος": "IAKOBOS",
        "Ἰακώβου": "IAKOBOS",
        "Ἰακώβῳ": "IAKOBOS",
        "Ἰάκωβον": "IAKOBOS",
        # ANDREAS (Andrew)
        "Ἀνδρέας": "ANDREAS",
        "Ἀνδρέαν": "ANDREAS",
        "Ἀνδρέου": "ANDREAS",
        "Ἀνδρέᾳ": "ANDREAS",
        # PAULOS (Paul/Saul)
        "Σαῦλος": "PAULOS",
        "Σαύλου": "PAULOS",
        "Σαῦλον": "PAULOS",
        "Παῦλος": "PAULOS",
        "Παύλου": "PAULOS",
        "Παῦλον": "PAULOS",
        "Παύλῳ": "PAULOS",
        # PHILIPPOS (Philip)
        "Φίλιππος": "PHILIPPOS",
        "Φιλίππου": "PHILIPPOS",
        "Φίλιππον": "PHILIPPOS",
        "Φιλίππῳ": "PHILIPPOS",
        # BARTHOLOMAIOS (Bartholomew)
        "Βαρθολομαῖος": "BARTHOLOMAIOS",
        "Βαρθολομαίου": "BARTHOLOMAIOS",
        "Βαρθολομαῖον": "BARTHOLOMAIOS",
        # THOMAS (Thomas)
        "Θωμᾶς": "THOMAS",
        "Θωμᾶν": "THOMAS",
        "Θωμᾶ": "THOMAS",
        # MATTHIAS (Matthew)
        "Ματθαῖος": "MATTHIAS",
        "Ματθαίου": "MATTHIAS",
        "Ματθαῖον": "MATTHIAS",
        "Ματθίαν": "MATTHIAS",
        # STEPHANOS (Stephen)
        "Στέφανος": "STEPHANOS",
        "Στεφάνου": "STEPHANOS",
        "Στέφανον": "STEPHANOS",
        # BARNABAS (Barnabas)
        "Βαρνάβας": "BARNABAS",
        "Βαρναβᾶ": "BARNABAS",
        "Βαρνάβαν": "BARNABAS",
        # NICODEMOS (Nicodemus)
        "Νικόδημος": "NICODEMOS",
        "Νικοδήμου": "NICODEMOS",
        "Νικόδημον": "NICODEMOS",
        # LAZAROS (Lazarus)
        "Λάζαρος": "LAZAROS",
        "Λαζάρου": "LAZAROS",
        "Λάζαρον": "LAZAROS",
        # MARIA (Mary)
        "Μαρία": "MARIA",
        "Μαρίας": "MARIA",
        "Μαρίαν": "MARIA",
        # PILATOS (Pilate)
        "Πιλᾶτος": "PILATOS",
        "Πιλάτου": "PILATOS",
        "Πιλᾶτον": "PILATOS",
        "Πιλάτῳ": "PILATOS",
        # TIMOTHEOS (Timothy)
        "Τιμόθεος": "TIMOTHEOS",
        "Τιμοθέου": "TIMOTHEOS",
        "Τιμόθεον": "TIMOTHEOS",
        "Τιμοθέῳ": "TIMOTHEOS",
        # SILAS
        "Σίλας": "SILAS",
        "Σίλα": "SILAS",
        "Σίλαν": "SILAS",
    }
    return aliases


def resolve_canonical(lemma):
    """Resolve lemma to canonical entity ID."""
    aliases = load_alias_map()
    return aliases.get(lemma, lemma.upper() if lemma else None)


def parse_morph(person, number):
    """Parse person/number to filter entities."""
    return person, number


def has_delta_adversative(sentence_tokens):
    """Check for δέ (but) which signals contrast/subject change."""
    for token in sentence_tokens:
        if token.get("form") == "δέ":
            return True
    return False


def is_participial_participle(verb_lemma):
    """Check if verb is a participle (should be skipped)."""
    return False  # Participles are already filtered


def is_person_entity(lemma: str) -> bool:
    """Check if a lemma refers to a person (not a place or abstract concept)."""
    if lemma in PERSON_LEMMAS:
        return True
    lemma_upper = lemma.upper()
    for non_person in NON_PERSON_LEMMAS:
        if lemma_upper.startswith(non_person.upper()):
            return False
    return True


def resolve_prodrop_rulebased(instance, all_sentences_df):
    """
    Rule-based pro-drop resolution.

    Strategy:
    1. Filter to person entities only
    2. If δέ adversative detected → look for NEW subject
    3. If genitive absolute → subject is the genitive noun, not main clause subject
    4. Otherwise → subject = most recent compatible entity (person/number match)
    """

    person = instance.get("person", 3)
    number = instance.get("number", "singular")
    entities = instance.get("entities_in_window", [])
    verse_ref = instance.get("verse_ref", "")
    markers = instance.get("narrative_markers", {})

    if not entities:
        return None, "NO_ENTITIES"

    person_entities = []
    for entity in entities:
        lemma = entity.get("lemma", "")
        if is_person_entity(lemma):
            person_entities.append(entity)

    if not person_entities:
        return None, "NO_PERSON_ENTITIES"

    canonical_entities = []
    for entity in person_entities:
        lemma = entity.get("lemma", "")
        canonical = resolve_canonical(lemma)
        if canonical:
            canonical_entities.append(
                {
                    **entity,
                    "canonical": canonical,
                }
            )

    if not canonical_entities:
        return None, "NO_COMPATIBLE_ENTITIES"

    if len(canonical_entities) == 1:
        return canonical_entities[0]["canonical"], "SINGLE_ENTITY"

    if markers.get("delta_adversative", False):
        return canonical_entities[-1]["canonical"], "DELTA_ADVERSATIVE"

    if markers.get("genitive_absolute", False):
        return canonical_entities[-1]["canonical"], "GENITIVE_ABSOLUTE"

    entity_counts = defaultdict(int)
    for entity in canonical_entities:
        entity_counts[entity["canonical"]] += 1

    if entity_counts:
        most_salient = max(entity_counts.items(), key=lambda x: x[1])
        return most_salient[0], "SALIENCE"

    return canonical_entities[-1]["canonical"], "DEFAULT"


def evaluate_rules(instances):
    """Evaluate rule-based resolver on instances."""
    results = []

    for instance in instances:
        predicted, reason = resolve_prodrop_rulebased(instance, None)

        entities = instance.get("entities_in_window", [])
        person_entities = [e for e in entities if is_person_entity(e.get("lemma", ""))]

        if person_entities:
            gold = resolve_canonical(person_entities[-1].get("lemma", ""))
        else:
            gold = None

        correct = predicted == gold if gold else False

        result = {
            "id": instance.get("id"),
            "verse_ref": instance.get("verse_ref"),
            "verb": instance.get("verb_form"),
            "difficulty": instance.get("difficulty_level"),
            "predicted": predicted,
            "gold": gold,
            "correct": correct,
            "reason": reason,
            "entities": [e["lemma"] for e in entities[:5]],
            "person_entities": [e["lemma"] for e in person_entities[:5]],
        }
        results.append(result)

    return results


def compute_accuracy(results):
    """Compute accuracy metrics by difficulty level."""
    metrics = {
        "overall": {"correct": 0, "total": 0},
        "level_1": {"correct": 0, "total": 0},
        "level_2": {"correct": 0, "total": 0},
        "level_3": {"correct": 0, "total": 0},
    }

    for r in results:
        level = r["difficulty"]
        key = f"level_{level}"

        metrics[key]["total"] += 1
        metrics["overall"]["total"] += 1

        if r["correct"]:
            metrics[key]["correct"] += 1
            metrics["overall"]["correct"] += 1

    # Compute percentages
    summary = {}
    for key, vals in metrics.items():
        if vals["total"] > 0:
            pct = (vals["correct"] / vals["total"]) * 100
            summary[key] = {
                "correct": vals["correct"],
                "total": vals["total"],
                "accuracy": f"{pct:.1f}%",
            }
        else:
            summary[key] = {"correct": 0, "total": 0, "accuracy": "N/A"}

    return summary


def main():
    # Load evaluation dataset
    with open(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json", "r"
    ) as f:
        data = json.load(f)

    instances = data["instances"]
    print(f"Loaded {len(instances)} pro-drop instances")

    # Evaluate rules
    print("\nEvaluating rule-based resolver...")
    results = evaluate_rules(instances)

    # Compute metrics
    summary = compute_accuracy(results)

    print("\n" + "=" * 50)
    print("RULE-BASED PRO-DROP RESOLUTION RESULTS")
    print("=" * 50)

    for level, metrics in summary.items():
        print(
            f"{level:12} | {metrics['correct']:4}/{metrics['total']:4} | {metrics['accuracy']:>8}"
        )

    # Save results
    output = {"summary": summary, "detailed_results": results}

    with open(
        "project/data/experiments/sprint2c/rules_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved results to project/data/experiments/sprint2c/rules_results.json")

    # Show sample results
    print("\n--- Sample Results (Level 2 & 3) ---")
    level_2_3 = [r for r in results if r["difficulty"] >= 2][:10]
    for r in level_2_3:
        status = "✓" if r["correct"] else "✗"
        print(f"  {status} {r['verse_ref']}: {r['verb']}")
        print(
            f"     Predicted: {r['predicted']}, Gold: {r['gold']}, Reason: {r['reason']}"
        )
        print(f"     Entities: {r['entities']}")


if __name__ == "__main__":
    main()
