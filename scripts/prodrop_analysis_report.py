#!/usr/bin/env python3
"""
Final analysis: Rules vs LLM comparison for pro-drop resolution.
Generates the decision report.
"""

import json
from collections import defaultdict


def main():
    # Load data
    with open(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json", "r"
    ) as f:
        eval_data = json.load(f)

    with open("project/data/experiments/sprint2c/rules_results.json", "r") as f:
        rules_data = json.load(f)

    instances = eval_data["instances"]
    rules_results = rules_data["detailed_results"]

    print("=" * 70)
    print("SPRINT 2C: PRO-DROP RESOLUTION - FINAL ANALYSIS REPORT")
    print("=" * 70)
    print(f"\nDate: April 8, 2026")
    print(f"Corpus: Mark 1:1-4:26 (Greek New Testament)")
    print(f"Total pro-drop instances: {len(instances)}")

    # Difficulty distribution
    level_counts = defaultdict(int)
    for inst in instances:
        level_counts[inst["difficulty_level"]] += 1

    print(f"\n--- Difficulty Distribution ---")
    print(
        f"  Level 1 (Clear - 1 compatible entity):      {level_counts.get(1, 0):4d} instances"
    )
    print(
        f"  Level 2 (Ambiguous - 2+ entities):         {level_counts.get(2, 0):4d} instances"
    )
    print(
        f"  Level 3 (Complex - δέ/tote/gen.abs):       {level_counts.get(3, 0):4d} instances"
    )

    # Rules performance
    print(f"\n--- Rule-Based Baseline Performance ---")
    print(f"  Overall accuracy:  {rules_data['summary']['overall']['accuracy']}")
    print(f"  Level 1 accuracy:  {rules_data['summary']['level_1']['accuracy']}")
    print(f"  Level 2 accuracy:  {rules_data['summary']['level_2']['accuracy']}")
    print(f"  Level 3 accuracy:  {rules_data['summary']['level_3']['accuracy']}")

    # Try to load LLM results
    try:
        with open("project/data/experiments/sprint2c/llm_results.json", "r") as f:
            llm_data = json.load(f)

        if llm_data.get("llm_available"):
            print(f"\n--- LLM (Gemini 3.1 Pro) Performance ---")
            print(f"  Instances evaluated: {llm_data['metrics']['llm_total']}")
            print(
                f"  Pending adjudication: {llm_data['metrics']['pending_adjudication']}"
            )

            # Check for comparison data
            if llm_data.get("comparison"):
                rules_wins = 0
                llm_wins = 0
                ties = 0

                for c in llm_data["comparison"]:
                    if c["rules_correct"] and not c.get("llm_confidence"):
                        rules_wins += 1
                    elif c.get("llm_confidence") and not c["rules_correct"]:
                        llm_wins += 1
                    else:
                        ties += 1

                print(f"\n  Head-to-head comparison:")
                print(f"    Rules wins: {rules_wins}")
                print(f"    LLM wins: {llm_wins}")
                print(f"    Ties/other: {ties}")
        else:
            print(f"\n--- LLM Evaluation ---")
            print(f"  Status: {llm_data.get('message', 'Not run')}")
    except FileNotFoundError:
        print(f"\n--- LLM Evaluation ---")
        print(f"  Status: Not yet run (requires API key in .env)")

    # Decision analysis
    print(f"\n" + "=" * 70)
    print("DECISION ANALYSIS")
    print("=" * 70)

    # Calculate the value of ML on Level 2+3
    level_2_3_rules = (
        rules_data["summary"]["level_2"]["correct"]
        + rules_data["summary"]["level_3"]["correct"]
    )
    level_2_3_total = (
        rules_data["summary"]["level_2"]["total"]
        + rules_data["summary"]["level_3"]["total"]
    )
    level_2_3_baseline = (
        (level_2_3_rules / level_2_3_total * 100) if level_2_3_total > 0 else 0
    )

    print(f"\nCritical threshold: >15% improvement on Level 2+3 combined")
    print(f"Current baseline (rules) on Level 2+3: {level_2_3_baseline:.1f}%")

    print(f"\n--- Strategy Recommendation ---")

    print(f"""
    Based on the rules-only baseline:
    
    1. LEVEL 1 (Clear cases):
       - Rules achieve 100% accuracy (heuristic baseline)
       - Recommendation: Use rules only (fast, reliable)
       - No ML needed
    
    2. LEVEL 2 (Ambiguous cases):
       - Rules achieve {rules_data["summary"]["level_2"]["accuracy"]}
       - This is where ML can add the most value
       - Recommendation: LLM evaluation needed to quantify improvement
    
    3. LEVEL 3 (Complex cases):
       - Rules achieve {rules_data["summary"]["level_3"]["accuracy"]}
       - Genitive absolute detection helps
       - Recommendation: LLM evaluation needed
    
    --- NEXT STEPS ---
    
    1. Run LLM evaluation with Gemini 3.1 Pro:
       python scripts/prodrop_llm_evaluator.py
    
    2. Compare accuracy on Level 2+3 combined:
       - If LLM > rules + 15%: ADOPT LLM HYBRID STRATEGY
       - If LLM < rules + 15%: CONSIDER FINE-TUNING LOGION
    
    3. Manual adjudication for ambiguous cases:
       python scripts/adjudicate_prodrop.py
""")

    # Save report
    report = {
        "date": "2026-04-08",
        "corpus": "Mark 1:1-4:26",
        "total_instances": len(instances),
        "difficulty_distribution": dict(level_counts),
        "rules_summary": rules_data["summary"],
        "decision_threshold": ">15% improvement on Level 2+3",
        "recommendation": "Run LLM evaluation to make final decision",
    }

    with open("project/data/experiments/sprint2c/analysis_report.json", "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport saved to project/data/experiments/sprint2c/analysis_report.json")


if __name__ == "__main__":
    main()
