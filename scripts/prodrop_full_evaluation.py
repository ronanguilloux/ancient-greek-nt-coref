#!/usr/bin/env python3
"""
Full evaluation of the Pro-Drop Hybrid Resolver on all 739 instances.
"""
import json
import os
import time
from datetime import datetime
from collections import defaultdict

# Import the hybrid resolver
import sys
sys.path.insert(0, 'scripts')
from prodrop_hybrid_resolver import ProDropHybridResolver, load_evaluation_dataset, DifficultyLevel

def run_full_evaluation():
    print("=" * 70)
    print("Pro-Drop Hybrid Resolver - Full Evaluation")
    print("=" * 70)
    
    # Load dataset
    dataset_path = "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found: {dataset_path}")
        return
    
    instances = load_evaluation_dataset(dataset_path)
    print(f"\nLoaded {len(instances)} instances")
    
    # Initialize resolver
    resolver = ProDropHybridResolver(use_llm=True)
    print(f"LLM available: {resolver.use_llm}")
    
    # Count by level
    level_counts = defaultdict(int)
    for inst in instances:
        level_counts[inst.difficulty_level] += 1
    
    print(f"\nInstances by level:")
    for level in [DifficultyLevel.CLEAR, DifficultyLevel.AMBIGUOUS, DifficultyLevel.COMPLEX]:
        print(f"  {level.name} (Level {level.value}): {level_counts[level]}")
    
    # Run evaluation
    print("\n" + "-" * 70)
    print("Running evaluation...")
    print("-" * 70)
    
    results = []
    method_counts = defaultdict(int)
    level_results = defaultdict(list)
    
    for i, inst in enumerate(instances):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(instances)} instances...")
        
        result = resolver.resolve(inst)
        results.append({
            "verse_ref": inst.verse_ref,
            "verb_form": inst.verb_form,
            "level": inst.difficulty_level.name,
            "level_value": inst.difficulty_level.value,
            "entities_count": len(inst.entities),
            "method": result.method,
            "entity_predicted": result.entity,
            "confidence": result.confidence,
            "reasoning": result.reasoning[:200] if result.reasoning else "",
        })
        
        method_counts[result.method] += 1
        level_results[inst.difficulty_level].append(result.method)
        
        # Rate limiting for LLM
        if resolver.use_llm and inst.difficulty_level != DifficultyLevel.CLEAR:
            time.sleep(0.3)
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)
    
    print(f"\nTotal instances: {len(instances)}")
    print(f"\nMethods used:")
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(instances)
        print(f"  {method}: {count} ({pct:.1f}%)")
    
    print(f"\nBreakdown by level:")
    for level in [DifficultyLevel.CLEAR, DifficultyLevel.AMBIGUOUS, DifficultyLevel.COMPLEX]:
        level_insts = level_results[level]
        level_total = len(level_insts)
        if level_total > 0:
            print(f"\n  {level.name} (Level {level.value}) - {level_total} instances:")
            method_counts_lvl = defaultdict(int)
            for m in level_insts:
                method_counts_lvl[m] += 1
            for method, count in sorted(method_counts_lvl.items(), key=lambda x: -x[1]):
                pct = 100 * count / level_total
                print(f"    {method}: {count} ({pct:.1f}%)")
    
    # Save results
    output_path = "project/data/experiments/sprint2c/hybrid_evaluation_results.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_instances": len(instances),
        "level_counts": {k.name: v for k, v in level_counts.items()},
        "method_counts": dict(method_counts),
        "results": results,
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # Generate markdown report
    report_path = "project/data/experiments/sprint2c/HYBRID_EVALUATION_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Pro-Drop Hybrid Resolver - Full Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total instances:** {len(instances)}\n\n")
        f.write("## Distribution by Level\n\n")
        f.write("| Level | Count | Percentage |\n")
        f.write("|-------|-------|------------|\n")
        for level in [DifficultyLevel.CLEAR, DifficultyLevel.AMBIGUOUS, DifficultyLevel.COMPLEX]:
            count = level_counts[level]
            pct = 100 * count / len(instances)
            f.write(f"| {level.name} (Level {level.value}) | {count} | {pct:.1f}% |\n")
        
        f.write("\n## Methods Used\n\n")
        f.write("| Method | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
            pct = 100 * count / len(instances)
            f.write(f"| {method} | {count} | {pct:.1f}% |\n")
        
        f.write("\n## Breakdown by Level\n\n")
        for level in [DifficultyLevel.CLEAR, DifficultyLevel.AMBIGUOUS, DifficultyLevel.COMPLEX]:
            level_insts = level_results[level]
            level_total = len(level_insts)
            if level_total > 0:
                f.write(f"\n### {level.name} (Level {level.value}) - {level_total} instances\n\n")
                f.write("| Method | Count | Percentage |\n")
                f.write("|--------|-------|------------|\n")
                method_counts_lvl = defaultdict(int)
                for m in level_insts:
                    method_counts_lvl[m] += 1
                for method, count in sorted(method_counts_lvl.items(), key=lambda x: -x[1]):
                    pct = 100 * count / level_total
                    f.write(f"| {method} | {count} | {pct:.1f}% |\n")
    
    print(f"Report saved to: {report_path}")

if __name__ == "__main__":
    run_full_evaluation()
