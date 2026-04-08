#!/usr/bin/env python3
"""
Evaluate LLM pro-drop resolution against TRUE PROIEL gold standard.
Quick version: evaluate only instances with person antecedents.
"""

import json
import sys
import os
import time

sys.path.insert(0, "scripts")

from dotenv import load_dotenv

load_dotenv()

from prodrop_hybrid_resolver import ProDropHybridResolver, load_evaluation_dataset


def normalize_for_comparison(entity: str) -> str:
    if not entity:
        return "NONE"
    entity = entity.upper()
    if entity in ["IOANNES", "IWANNHS", "IWANNES"]:
        return "IOANNES"
    return entity


def main():
    print("=" * 60)
    print("LLM Evaluation vs PROIEL Gold (Quick Test)")
    print("=" * 60)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "XXX":
        print("\nERROR: No valid API key in .env")
        return

    print(f"\nAPI Key: {api_key[:15]}...")

    instances = load_evaluation_dataset(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    )
    print(f"Loaded {len(instances)} instances")

    with open("project/data/experiments/sprint2c/proiel_gold_standard.json", "r") as f:
        gold_data = json.load(f)

    gold_results = {r["verse_ref"]: r for r in gold_data["gold_results"]}

    # Filter to only person antecedents for quick test
    person_gold = {
        k: v
        for k, v in gold_results.items()
        if v.get("antecedent_entity")
        and v["antecedent_entity"].upper() not in ["NONE", "NO_ANTECEDENT"]
    }
    print(f"Instances with person antecedent: {len(person_gold)}")

    hybrid_resolver = ProDropHybridResolver(use_llm=True)
    print(f"LLM available: {hybrid_resolver.use_llm}")

    if not hybrid_resolver.use_llm:
        print("ERROR: LLM not available")
        return

    stats = {
        "total": 0,
        "correct": 0,
        "level_1": {"total": 0, "correct": 0},
        "level_2": {"total": 0, "correct": 0},
        "level_3": {"total": 0, "correct": 0},
    }

    detailed = []

    print("\nEvaluating (person antecedent instances only)...")

    for inst in instances:
        gold = gold_results.get(inst.verse_ref, {})
        gold_entity = gold.get("antecedent_entity")

        if not gold_entity:
            continue

        gold_entity = normalize_for_comparison(gold_entity)

        result = hybrid_resolver.resolve(inst)
        pred_entity = normalize_for_comparison(result.entity)

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
                "method": result.method,
                "reasoning": result.reasoning[:80] if result.reasoning else "",
            }
        )

        time.sleep(0.5)

        if stats["total"] % 20 == 0:
            acc = 100 * stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  Progress: {stats['total']} evaluated, {acc:.1f}% accuracy")

    print()
    print("=" * 60)
    print("LLM ACCURACY vs PROIEL GOLD")
    print("=" * 60)

    overall_acc = 100 * stats["correct"] / stats["total"] if stats["total"] > 0 else 0
    print(f"\nOverall:   {stats['correct']}/{stats['total']} ({overall_acc:.1f}%)")

    for level in [1, 2, 3]:
        s = stats[f"level_{level}"]
        if s["total"] > 0:
            acc = 100 * s["correct"] / s["total"]
            print(f"Level {level}: {s['correct']}/{s['total']} ({acc:.1f}%)")

    print("\nSample results:")
    for d in detailed[:15]:
        status = "✓" if d["correct"] else "✗"
        print(
            f"  {status} {d['verse_ref']}: {d['verb']} → Gold: {d['gold']}, Pred: {d['pred']} ({d['method']})"
        )

    output = {
        "metadata": {"source": "PROIEL", "date": "2026-04-08", "method": "LLM"},
        "stats": stats,
        "detailed": detailed,
    }

    with open(
        "project/data/experiments/sprint2c/llm_proiel_evaluation_results.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"\nSaved to: project/data/experiments/sprint2c/llm_proiel_evaluation_results.json"
    )


if __name__ == "__main__":
    main()
