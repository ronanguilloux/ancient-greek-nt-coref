#!/usr/bin/env python3
"""
Sequential LLM Evaluation with progress saving.
Processes instances one at a time with intermediate saves.
"""

import json
import os
import time
import re
import requests
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"

# Import from hybrid resolver
import sys

sys.path.insert(0, "scripts")
from prodrop_hybrid_resolver import (
    ProDropInstance,
    AliasResolver,
    DifficultyLevel,
    load_evaluation_dataset,
)


class SequentialLLMEvaluator:
    """Sequential LLM evaluator with intermediate saves."""

    def __init__(self, save_interval: int = 20):
        self.save_interval = save_interval
        self.results = {}
        self.errors = []

    def _build_prompt(self, instance: ProDropInstance) -> str:
        """Build prompt for LLM."""
        unique_entities = list(set(e.get("lemma", "") for e in instance.entities))[:10]

        prompt = f"""You are analyzing Ancient Greek New Testament text for a coreference resolution task.

GREEK TEXT (current verse):
{instance.sentence_text}

CONTEXT (5 verses before):
{instance.context_5verses}

TARGET VERB:
{instance.verb_form} (lemma: {instance.verb_lemma})

KNOWN ENTITIES IN PASSAGE:
{", ".join(unique_entities) if unique_entities else "No named entities in immediate context"}

VERSE REFERENCE:
{instance.verse_ref}

TASK:
Identify the implied subject (antecedent) of the TARGET VERB.
In Ancient Greek, verbs often have no explicit subject pronoun because the person and number are encoded in the verb ending (pro-drop).

ANALYSIS REQUIRED:
1. What is the person and number of the verb? (3rd singular = he/she/it, 3rd plural = they)
2. Who is the most recently mentioned entity that matches this person/number?
3. Are there any narrative markers (δέ = but, τότε = then) that suggest a subject change?

OUTPUT FORMAT:
Entity: [The Greek form of the implied subject, e.g., Ἰησοῦς or UNKNOWN if truly ambiguous]
Confidence: [high/medium/low]
Reasoning: [2-3 sentence explanation in English]

Important: If there are multiple possible entities, choose the one that makes the most narrative sense given the context."""

        return prompt

    def _parse_response(self, response_text: str) -> Tuple[Optional[str], str, str]:
        """Parse LLM response."""
        entity = None
        confidence = "medium"
        reasoning = ""

        entity_match = re.search(r"Entity:\s*(.+)", response_text, re.IGNORECASE)
        if entity_match:
            entity = entity_match.group(1).strip()
            if entity.upper() == "UNKNOWN":
                entity = None

        conf_match = re.search(
            r"Confidence:\s*(high|medium|low)", response_text, re.IGNORECASE
        )
        if conf_match:
            confidence = conf_match.group(1).lower()

        reason_match = re.search(
            r"Reasoning:\s*(.+)", response_text, re.IGNORECASE | re.DOTALL
        )
        if reason_match:
            reasoning = reason_match.group(1).strip()[:300]

        return entity, confidence, reasoning

    def _call_llm(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Make a single LLM API call."""
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }

        try:
            response = requests.post(
                GEMINI_API_URL, headers=headers, params=params, json=data, timeout=60
            )

            if response.status_code != 200:
                return {
                    "error": f"API error: {response.status_code}",
                    "response": response.text[:200],
                }

            result = response.json()

            # Extract text from response
            response_text = ""
            if "candidates" in result and result["candidates"]:
                for candidate in result["candidates"]:
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                response_text += part["text"]

            if not response_text:
                return {"error": "Empty response from API", "raw": str(result)[:200]}

            entity, confidence, reasoning = self._parse_response(response_text)

            return {
                "entity": entity,
                "confidence": confidence,
                "reasoning": reasoning,
                "raw_response": response_text[:500],
            }

        except Exception as e:
            return {"error": str(e)}

    def evaluate_sequential(
        self, instances: List[ProDropInstance], output_path: str
    ) -> List[Dict[str, Any]]:
        """Evaluate instances sequentially with intermediate saves."""
        print(f"Starting sequential evaluation of {len(instances)} instances...")
        print(f"Save interval: every {self.save_interval} instances")

        start_time = time.time()
        results = []

        for i, inst in enumerate(instances):
            # Progress update
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(instances) - i - 1) / rate if rate > 0 else 0
                print(
                    f"  [{i + 1}/{len(instances)}] {rate:.2f} inst/s, ETA: {eta / 60:.1f} min"
                )

            # Build prompt and call LLM
            prompt = self._build_prompt(inst)
            llm_result = self._call_llm(prompt)

            # Combine instance info with LLM result
            result = {
                "instance_id": i,
                "verse_ref": inst.verse_ref,
                "sentence_text": inst.sentence_text[:100],
                "verb_form": inst.verb_form,
                "level": inst.difficulty_level.name,
                "entities_count": len(inst.entities),
            }

            if llm_result and "error" not in llm_result:
                entity = llm_result.get("entity")
                if entity:
                    entity = AliasResolver.resolve(entity)
                result.update(
                    {
                        "entity_predicted": entity,
                        "confidence": llm_result.get("confidence", "unknown"),
                        "reasoning": llm_result.get("reasoning", ""),
                        "raw_response": llm_result.get("raw_response", ""),
                        "success": True,
                    }
                )
            else:
                result.update(
                    {
                        "entity_predicted": None,
                        "confidence": "unknown",
                        "reasoning": llm_result.get("error", "Unknown error")
                        if llm_result
                        else "No response",
                        "success": False,
                    }
                )

            results.append(result)

            # Intermediate save
            if (i + 1) % self.save_interval == 0:
                self._save_results(results, output_path)

        # Final save
        self._save_results(results, output_path)

        return results

    def _save_results(self, results: List[Dict], output_path: str):
        """Save results to file."""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "total_processed": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 70)
    print("Pro-Drop Sequential LLM Evaluation - Level 2+3 Instances")
    print("=" * 70)

    # Load dataset
    dataset_path = "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found: {dataset_path}")
        return

    instances = load_evaluation_dataset(dataset_path)
    print(f"\nLoaded {len(instances)} total instances")

    # Filter to Level 2+3
    level_2_3 = [
        inst
        for inst in instances
        if inst.difficulty_level in [DifficultyLevel.AMBIGUOUS, DifficultyLevel.COMPLEX]
    ]
    print(f"Level 2+3 instances: {len(level_2_3)}")

    # Initialize evaluator
    evaluator = SequentialLLMEvaluator(save_interval=20)

    # Output path
    output_path = "project/data/experiments/sprint2c/llm_batch_evaluation_results.json"

    # Run evaluation
    print("\n" + "-" * 70)
    print("Running sequential LLM evaluation...")
    start_time = time.time()

    results = evaluator.evaluate_sequential(level_2_3, output_path)

    elapsed = time.time() - start_time
    print(
        f"\nEvaluation completed in {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)"
    )

    # Analyze results
    print("\n" + "=" * 70)
    print("LLM EVALUATION RESULTS")
    print("=" * 70)

    successful = [r for r in results if r.get("success")]
    print(f"\nTotal Level 2+3: {len(level_2_3)}")
    print(f"Successful LLM calls: {len(successful)}")
    print(f"Errors: {len(results) - len(successful)}")

    # Entity distribution
    entity_counts = defaultdict(int)
    for r in successful:
        entity_counts[r.get("entity_predicted") or "NONE"] += 1

    print("\nTop entities predicted by LLM:")
    for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:10]:
        pct = 100 * count / len(successful) if successful else 0
        print(f"  {entity}: {count} ({pct:.1f}%)")

    # Generate summary report
    report_path = "project/data/experiments/sprint2c/LLM_BATCH_EVALUATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Pro-Drop LLM Batch Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Level 2+3 instances evaluated:** {len(level_2_3)}\n\n")
        f.write(f"**Successful LLM calls:** {len(successful)}\n\n")
        f.write(f"**Errors:** {len(results) - len(successful)}\n\n")
        f.write(
            f"**Execution time:** {elapsed:.1f} seconds ({elapsed / 60:.1f} minutes)\n\n"
        )

        f.write("## Entity Distribution\n\n")
        f.write("| Entity | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:15]:
            pct = 100 * count / len(successful) if successful else 0
            f.write(f"| {entity} | {count} | {pct:.1f}% |\n")

    print(f"\nReport saved to: {report_path}")
    print(f"Results saved to: {output_path}")
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
