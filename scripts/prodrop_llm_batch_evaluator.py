#!/usr/bin/env python3
"""
Batch LLM Evaluation of Pro-Drop Resolver on Level 2+3 instances.
Uses concurrent API calls for faster execution.
"""

import json
import os
import asyncio
import aiohttp
import time
import re
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
    ResolutionResult,
    AliasResolver,
    DifficultyLevel,
    load_evaluation_dataset,
)


class BatchLLMEvaluator:
    """Concurrent LLM evaluator for pro-drop instances."""

    def __init__(self, max_concurrent: int = 5, rate_limit_delay: float = 0.2):
        self.max_concurrent = max_concurrent
        self.rate_limit_delay = rate_limit_delay
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

        entity_match = re.search(r"Entity:\s*(.+)", response_text)
        if entity_match:
            entity = entity_match.group(1).strip()
            if entity.upper() == "UNKNOWN":
                entity = None

        conf_match = re.search(
            r"Confidence:\s*(high|medium|low)", response_text, re.IGNORECASE
        )
        if conf_match:
            confidence = conf_match.group(1).lower()

        reason_match = re.search(r"Reasoning:\s*(.+)", response_text, re.DOTALL)
        if reason_match:
            reasoning = reason_match.group(1).strip()[:300]

        return entity, confidence, reasoning

    async def _call_llm(
        self, session: aiohttp.ClientSession, instance_id: int, prompt: str
    ) -> Dict[str, Any]:
        """Make a single LLM API call."""
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 300},
        }

        try:
            async with session.post(
                GEMINI_API_URL, headers=headers, params=params, json=data
            ) as response:
                if response.status == 429:
                    await asyncio.sleep(2)
                    async with session.post(
                        GEMINI_API_URL, headers=headers, params=params, json=data
                    ) as retry:
                        if retry.status != 200:
                            return {
                                "error": f"Rate limited twice, status: {retry.status}",
                                "instance_id": instance_id,
                            }
                        result = await retry.json()
                elif response.status != 200:
                    return {
                        "error": f"API error, status: {response.status}",
                        "instance_id": instance_id,
                    }
                else:
                    result = await response.json()

                response_text = ""
                if "candidates" in result:
                    for candidate in result["candidates"]:
                        if "content" in candidate and "parts" in candidate["content"]:
                            for part in candidate["content"]["parts"]:
                                if "text" in part:
                                    response_text += part["text"]

                entity, confidence, reasoning = self._parse_response(response_text)
                if entity:
                    entity = AliasResolver.resolve(entity)

                return {
                    "instance_id": instance_id,
                    "entity": entity,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "raw_response": response_text[:500],
                }

        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    async def evaluate_batch(
        self, instances: List[ProDropInstance]
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple instances concurrently."""
        print(f"Starting batch evaluation of {len(instances)} instances...")
        print(f"Max concurrent: {self.max_concurrent}")

        # Create semaphore inside the async context
        semaphore = asyncio.Semaphore(self.max_concurrent)

        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            tasks = []
            for i, inst in enumerate(instances):
                prompt = self._build_prompt(inst)

                async def call_with_semaphore(idx, p):
                    async with semaphore:
                        return await self._call_llm(session, idx, p)

                tasks.append(call_with_semaphore(i, prompt))

                # Progress update every 50 instances
                if (i + 1) % 50 == 0:
                    print(f"  Queued {i + 1}/{len(instances)} instances...")

            print("  All tasks queued, waiting for results...")
            results = await asyncio.gather(*tasks)

        return results


def main():
    print("=" * 70)
    print("Pro-Drop Batch LLM Evaluation - Level 2+3 Instances")
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

    # Show distribution
    level_counts = defaultdict(int)
    for inst in level_2_3:
        level_counts[inst.difficulty_level] += 1
    print(f"  - AMBIGUOUS (Level 2): {level_counts[DifficultyLevel.AMBIGUOUS]}")
    print(f"  - COMPLEX (Level 3): {level_counts[DifficultyLevel.COMPLEX]}")

    # Initialize evaluator
    evaluator = BatchLLMEvaluator(max_concurrent=5, rate_limit_delay=0.2)

    # Run evaluation
    print("\n" + "-" * 70)
    print("Running batch LLM evaluation...")
    start_time = time.time()

    results = asyncio.run(evaluator.evaluate_batch(level_2_3))

    elapsed = time.time() - start_time
    print(f"\nEvaluation completed in {elapsed:.1f} seconds")

    # Analyze results
    print("\n" + "=" * 70)
    print("LLM EVALUATION RESULTS")
    print("=" * 70)

    # Count success vs errors
    successful = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    print(f"\nTotal Level 2+3: {len(level_2_3)}")
    print(f"Successful LLM calls: {len(successful)}")
    print(f"Errors: {len(errors)}")

    # Entity distribution
    entity_counts = defaultdict(int)
    for r in successful:
        entity_counts[r.get("entity", "NONE") or "NONE"] += 1

    print("\nTop entities predicted by LLM:")
    for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:10]:
        pct = 100 * count / len(successful) if successful else 0
        print(f"  {entity}: {count} ({pct:.1f}%)")

    # Confidence distribution
    conf_counts = defaultdict(int)
    for r in successful:
        conf_counts[r.get("confidence", "unknown")] += 1

    print("\nConfidence distribution:")
    for conf, count in sorted(conf_counts.items()):
        pct = 100 * count / len(successful) if successful else 0
        print(f"  {conf}: {count} ({pct:.1f}%)")

    # Save results
    output_path = "project/data/experiments/sprint2c/llm_batch_evaluation_results.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_level_2_3": len(level_2_3),
        "successful_calls": len(successful),
        "errors": len(errors),
        "elapsed_seconds": elapsed,
        "level_counts": dict(level_counts),
        "entity_distribution": dict(entity_counts),
        "confidence_distribution": dict(conf_counts),
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Generate report
    report_path = "project/data/experiments/sprint2c/LLM_BATCH_EVALUATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Pro-Drop LLM Batch Evaluation Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Level 2+3 instances evaluated:** {len(level_2_3)}\n\n")
        f.write(f"**Successful LLM calls:** {len(successful)}\n\n")
        f.write(f"**Errors:** {len(errors)}\n\n")
        f.write(f"**Execution time:** {elapsed:.1f} seconds\n\n")
        f.write(f"**Rate:** {len(level_2_3) / elapsed:.1f} instances/second\n\n")

        f.write("## Level Distribution\n\n")
        f.write("| Level | Count |\n")
        f.write("|-------|-------|\n")
        for level, count in level_counts.items():
            f.write(f"| {level.name} | {count} |\n")

        f.write("\n## Entity Distribution\n\n")
        f.write("| Entity | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        for entity, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:15]:
            pct = 100 * count / len(successful) if successful else 0
            f.write(f"| {entity} | {count} | {pct:.1f}% |\n")

        f.write("\n## Confidence Distribution\n\n")
        f.write("| Confidence | Count | Percentage |\n")
        f.write("|------------|-------|------------|\n")
        for conf, count in sorted(conf_counts.items()):
            pct = 100 * count / len(successful) if successful else 0
            f.write(f"| {conf} | {count} | {pct:.1f}% |\n")

        if errors:
            f.write("\n## Errors\n\n")
            for err in errors[:10]:
                f.write(
                    f"- Instance {err.get('instance_id')}: {err.get('error', 'Unknown error')}\n"
                )

    print(f"Report saved to: {report_path}")
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
