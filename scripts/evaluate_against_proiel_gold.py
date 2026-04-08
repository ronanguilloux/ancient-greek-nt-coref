#!/usr/bin/env python3
"""
Evaluate rule-based pro-drop resolution against TRUE PROIEL gold standard.
"""

import json
import sys
from collections import defaultdict

sys.path.insert(0, "scripts")
from prodrop_hybrid_resolver import RuleBasedResolver, load_evaluation_dataset


def normalize_for_comparison(entity: str) -> str:
    """Normalize entity for comparison."""
    if not entity:
        return "NONE"
    entity = entity.upper()
    if entity in ["IOANNES", "IWANNHS", "IWANNES"]:
        return "IOANNES"
    return entity


def main():
    print("=" * 60)
    print("PROIEL Gold Evaluation")
    print("=" * 60)

    instances = load_evaluation_dataset(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    )
    print(f"Loaded {len(instances)} instances")

    with open("project/data/experiments/sprint2c/proiel_gold_standard.json", "r") as f:
        gold_data = json.load(f)

    gold_results = {r["verse_ref"]: r for r in gold_data["gold_results"]}
    print(f"Loaded {len(gold_results)} gold results")

    rules_resolver = RuleBasedResolver()

    stats = {
        "total": 0,
        "correct": 0,
        "level_1": {"total": 0, "correct": 0},
        "level_2": {"total": 0, "correct": 0},
        "level_3": {"total": 0, "correct": 0},
    }

    detailed = []

    for inst in instances:
        gold = gold_results.get(inst.verse_ref, {})
        gold_entity = gold.get("antecedent_entity")

        if not gold_entity:
            continue

        gold_entity = normalize_for_comparison(gold_entity)

        rules_result = rules_resolver.resolve(inst)
        pred_entity = normalize_for_comparison(rules_result.entity)

        correct = pred_entity == gold_entity

        level_key = f"level_{inst.difficulty_level.value}"
        stats["total"] += 1
        stats["correct"] += 1 if correct else 0
        stats[level_key]["total"] += 1
        stats[level_key]["correct"] += 1 if correct else 0

        detailed.append(
            {
                "verse_ref": inst.verse_ref,
                "verb": inst.verb_form,
                "level": inst.difficulty_level.value,
                "gold": gold_entity,
                "pred": pred_entity,
                "correct": correct,
                "reasoning": rules_result.reasoning[:80],
            }
        )

    print()
    print("=" * 60)
    print("RULES ACCURACY vs PROIEL GOLD")
    print("=" * 60)
    print()

    overall_acc = 100 * stats["correct"] / stats["total"] if stats["total"] > 0 else 0
    print(f"Overall:   {stats['correct']}/{stats['total']} ({overall_acc:.1f}%)")
    print()

    for level in [1, 2, 3]:
        s = stats[f"level_{level}"]
        if s["total"] > 0:
            acc = 100 * s["correct"] / s["total"]
            print(f"Level {level}: {s['correct']}/{s['total']} ({acc:.1f}%)")

    print()
    print("Sample Level 2+3 results:")
    l23 = [d for d in detailed if d["level"] >= 2 and d["gold"]]
    for d in l23[:15]:
        status = "✓" if d["correct"] else "✗"
        print(
            f"  {status} {d['verse_ref']}: {d['verb']} → Gold: {d['gold']}, Pred: {d['pred']}"
        )

    with open(
        "project/data/experiments/sprint2c/proiel_evaluation_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            {
                "metadata": {"source": "PROIEL", "date": "2026-04-08"},
                "stats": stats,
                "detailed": detailed,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Saved to: project/data/experiments/sprint2c/proiel_evaluation_results.json")


if __name__ == "__main__":
    main()
