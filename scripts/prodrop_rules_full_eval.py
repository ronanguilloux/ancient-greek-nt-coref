#!/usr/bin/env python3
"""
Full Rules-Only Evaluation of Pro-Drop Resolver on all 739 instances.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

import sys

sys.path.insert(0, "scripts")
from prodrop_hybrid_resolver import (
    ProDropHybridResolver,
    load_evaluation_dataset,
    DifficultyLevel,
    RuleBasedResolver,
)


def run_rules_full_evaluation():
    print("=" * 70)
    print("Pro-Drop Rules-Only Resolver - Full Evaluation (739 instances)")
    print("=" * 70)

    # Load dataset
    dataset_path = "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found: {dataset_path}")
        return

    instances = load_evaluation_dataset(dataset_path)
    print(f"\nLoaded {len(instances)} instances")

    # Initialize rules-only resolver
    rules_resolver = RuleBasedResolver()

    # Count by level
    level_counts = defaultdict(int)
    for inst in instances:
        level_counts[inst.difficulty_level] += 1

    print(f"\nInstances by level:")
    for level in [
        DifficultyLevel.CLEAR,
        DifficultyLevel.AMBIGUOUS,
        DifficultyLevel.COMPLEX,
    ]:
        print(f"  {level.name} (Level {level.value}): {level_counts[level]}")

    # Run evaluation
    print("\n" + "-" * 70)
    print("Running rules-only evaluation...")
    print("-" * 70)

    results = []
    level_results = defaultdict(list)

    for i, inst in enumerate(instances):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(instances)} instances...")

        result = rules_resolver.resolve(inst)
        results.append(
            {
                "verse_ref": inst.verse_ref,
                "verb_form": inst.verb_form,
                "level": inst.difficulty_level.name,
                "level_value": inst.difficulty_level.value,
                "entities_count": len(inst.entities),
                "method": result.method,
                "entity_predicted": result.entity,
                "confidence": result.confidence,
                "reasoning": result.reasoning[:200] if result.reasoning else "",
            }
        )

        level_results[inst.difficulty_level].append(result)

    # Summary statistics
    print("\n" + "=" * 70)
    print("RULES-ONLY EVALUATION RESULTS")
    print("=" * 70)

    print(f"\nTotal instances: {len(instances)}")

    print(f"\nBreakdown by level:")
    for level in [
        DifficultyLevel.CLEAR,
        DifficultyLevel.AMBIGUOUS,
        DifficultyLevel.COMPLEX,
    ]:
        level_insts = level_results[level]
        level_total = len(level_insts)
        if level_total > 0:
            print(f"\n  {level.name} (Level {level.value}) - {level_total} instances:")
            confidence_counts = defaultdict(int)
            entity_counts = defaultdict(int)
            for r in level_insts:
                confidence_counts[r.confidence] += 1
                entity_counts[r.entity if r.entity else "NONE"] += 1
            print(f"    Confidence distribution:")
            for conf, count in sorted(confidence_counts.items()):
                pct = 100 * count / level_total
                print(f"      {conf}: {count} ({pct:.1f}%)")
            print(f"    Entities predicted:")
            for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:5]:
                pct = 100 * count / level_total
                print(f"      {entity}: {count} ({pct:.1f}%)")

    # Save results
    output_path = "project/data/experiments/sprint2c/rules_full_evaluation_results.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_instances": len(instances),
        "level_counts": {k.name: v for k, v in level_counts.items()},
        "results": results,
        "level_summary": {
            level.name: {
                "count": len(level_results[level]),
                "confidence_distribution": dict(
                    defaultdict(int, {r.confidence: 0 for r in level_results[level]})
                ),
            }
            for level in level_results.keys()
        },
    }

    # Calculate confidence distribution per level
    for level in level_results.keys():
        conf_dist = defaultdict(int)
        for r in level_results[level]:
            conf_dist[r.confidence] += 1
        output_data["level_summary"][level.name]["confidence_distribution"] = dict(
            conf_dist
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Generate markdown report
    report_path = "project/data/experiments/sprint2c/RULES_FULL_EVALUATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Pro-Drop Rules-Only Resolver - Full Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total instances evaluated:** {len(instances)}\n\n")
        f.write("## Distribution by Level\n\n")
        f.write("| Level | Count | Percentage |\n")
        f.write("|-------|-------|------------|\n")
        for level in [
            DifficultyLevel.CLEAR,
            DifficultyLevel.AMBIGUOUS,
            DifficultyLevel.COMPLEX,
        ]:
            count = level_counts[level]
            pct = 100 * count / len(instances)
            f.write(f"| {level.name} (Level {level.value}) | {count} | {pct:.1f}% |\n")

        f.write("\n## Confidence Distribution by Level\n\n")
        for level in [
            DifficultyLevel.CLEAR,
            DifficultyLevel.AMBIGUOUS,
            DifficultyLevel.COMPLEX,
        ]:
            level_total = len(level_results[level])
            if level_total > 0:
                conf_dist = defaultdict(int)
                for r in level_results[level]:
                    conf_dist[r.confidence] += 1
                f.write(f"\n### {level.name} (Level {level.value})\n\n")
                f.write("| Confidence | Count | Percentage |\n")
                f.write("|------------|-------|------------|\n")
                for conf in ["high", "medium", "low"]:
                    count = conf_dist[conf]
                    pct = 100 * count / level_total if level_total > 0 else 0
                    f.write(f"| {conf} | {count} | {pct:.1f}% |\n")

        f.write("\n## Entity Distribution by Level\n\n")
        for level in [
            DifficultyLevel.CLEAR,
            DifficultyLevel.AMBIGUOUS,
            DifficultyLevel.COMPLEX,
        ]:
            level_total = len(level_results[level])
            if level_total > 0:
                entity_counts = defaultdict(int)
                for r in level_results[level]:
                    entity_counts[r.entity if r.entity else "NONE"] += 1
                f.write(f"\n### {level.name} (Level {level.value})\n\n")
                f.write("| Entity | Count | Percentage |\n")
                f.write("|--------|-------|------------|\n")
                for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[
                    :10
                ]:
                    pct = 100 * count / level_total
                    f.write(f"| {entity} | {count} | {pct:.1f}% |\n")

    print(f"Report saved to: {report_path}")
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_rules_full_evaluation()
