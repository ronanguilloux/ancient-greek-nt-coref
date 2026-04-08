#!/usr/bin/env python3
"""
LLM-based pro-drop resolver using Gemini 3.1 Pro.
Evaluates the LLM on pro-drop resolution tasks.
"""

import json
import os
import time
import re
from collections import defaultdict

# Check if we have the Gemini SDK at module level
GEMINI_SDK_INSTALLED = False
try:
    from google import genai  # noqa: F401

    GEMINI_SDK_INSTALLED = True
except ImportError:
    print("Warning: google-genai not installed. Install with: pip install google-genai")


def build_prompt(instance):
    """Build prompt for pro-drop resolution."""
    context = instance.get("context_5verses", "")
    sentence = instance.get("sentence_text", "")
    verb_form = instance.get("verb_form", "")
    verb_lemma = instance.get("verb_lemma", "")
    entities = instance.get("entity_lemmas", [])
    verse_ref = instance.get("verse_ref", "")

    # Unique entities
    unique_entities = list(set(entities))[:10]

    prompt = f"""You are analyzing Ancient Greek New Testament text for a coreference resolution task.

GREEK TEXT (current verse):
{sentence}

CONTEXT (5 verses before):
{context}

TARGET VERB:
{verb_form} (lemma: {verb_lemma})

KNOWN ENTITIES IN PASSAGE:
{", ".join(unique_entities) if unique_entities else "No named entities in immediate context"}

VERSE REFERENCE:
{verse_ref}

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


def parse_llm_response(response_text):
    """Parse LLM response to extract entity and reasoning."""
    result = {
        "entity": None,
        "confidence": None,
        "reasoning": None,
        "needs_adjudication": False,
    }

    # Extract entity
    entity_match = re.search(r"Entity:\s*(.+)", response_text)
    if entity_match:
        result["entity"] = entity_match.group(1).strip()

    # Extract confidence
    conf_match = re.search(
        r"Confidence:\s*(high|medium|low)", response_text, re.IGNORECASE
    )
    if conf_match:
        result["confidence"] = conf_match.group(1).lower()

    # Extract reasoning
    reason_match = re.search(r"Reasoning:\s*(.+)", response_text, re.DOTALL)
    if reason_match:
        result["reasoning"] = reason_match.group(1).strip()[:200]

    # Check if needs adjudication
    if "unknown" in response_text.lower() or not result["entity"]:
        result["needs_adjudication"] = True

    return result


def evaluate_with_llm(instances, model="gemini-3.1-pro-preview", max_instances=50):
    """Evaluate LLM on pro-drop instances."""
    try:
        from google import genai as genai_module
    except ImportError:
        print("Gemini SDK not available. Skipping LLM evaluation.")
        return [], []

    # Initialize client with API key
    client = genai_module.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    results = []
    pending_adjudication = []

    # Sample instances - focus on Level 2 and 3
    level_2_3 = [i for i in instances if i.get("difficulty_level", 0) >= 2]
    level_1_sample = [i for i in instances if i.get("difficulty_level", 0) == 1][:10]

    # Limit total instances
    selected = level_2_3[:max_instances] + level_1_sample
    print(f"Evaluating {len(selected)} instances with Gemini 3.1 Pro...")

    for i, instance in enumerate(selected):
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(selected)}")

        prompt = build_prompt(instance)

        try:
            # Use models.generate_content with proper config
            # Note: gemini-3.1-pro-preview requires thinking mode
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"temperature": 0.1, "max_output_tokens": 300},
            )

            # Handle response - extract text from candidates
            response_text = ""
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    parts = candidate.content.parts or []
                    for part in parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text

            if not response_text:
                response_text = (
                    str(response.text) if hasattr(response, "text") else str(response)
                )

            parsed = parse_llm_response(response_text)

            result = {
                "id": instance.get("id"),
                "verse_ref": instance.get("verse_ref"),
                "verb": instance.get("verb_form"),
                "difficulty": instance.get("difficulty_level"),
                "entities": instance.get("entity_lemmas", []),
                "llm_entity": parsed["entity"],
                "llm_confidence": parsed["confidence"],
                "llm_reasoning": parsed["reasoning"],
                "needs_adjudication": parsed["needs_adjudication"],
                "raw_response": response_text[:500],
            }
            results.append(result)

            if parsed["needs_adjudication"]:
                pending_adjudication.append(result)

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  Error on instance {instance.get('id')}: {e}")
            results.append(
                {
                    "id": instance.get("id"),
                    "error": str(e),
                    "difficulty": instance.get("difficulty_level"),
                }
            )

    return results, pending_adjudication


def compute_comparison(rules_results, llm_results):
    """Compare rules vs LLM performance."""
    comparison = []

    rules_by_id = {r["id"]: r for r in rules_results}

    for llm_r in llm_results:
        if "error" in llm_r:
            continue

        rid = llm_r["id"]
        if rid in rules_by_id:
            rules_r = rules_by_id[rid]
            comparison.append(
                {
                    "id": rid,
                    "verse_ref": llm_r.get("verse_ref"),
                    "verb": llm_r.get("verb"),
                    "difficulty": llm_r.get("difficulty"),
                    "rules_correct": rules_r.get("correct", False),
                    "llm_entity": llm_r.get("llm_entity"),
                    "llm_confidence": llm_r.get("llm_confidence"),
                    "needs_adjudication": llm_r.get("needs_adjudication", False),
                }
            )

    return comparison


def main():
    # Load evaluation dataset
    with open(
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json", "r"
    ) as f:
        data = json.load(f)

    instances = data["instances"]
    print(f"Loaded {len(instances)} pro-drop instances")

    # Load rules results
    with open("project/data/experiments/sprint2c/rules_results.json", "r") as f:
        rules_data = json.load(f)

    rules_results = rules_data["detailed_results"]

    # Evaluate with LLM
    print("\n" + "=" * 60)
    print("LLM EVALUATION WITH GEMINI 3.1 PRO")
    print("=" * 60)

    # Check for API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\nWarning: GEMINI_API_KEY not set in environment.")
        print("Please set it in .env file")
        print("\nSkipping LLM evaluation.")

        # Create mock results for analysis
        print("\nCreating analysis report with rules-only results...")

        output = {
            "llm_available": False,
            "message": "LLM evaluation skipped - API key not configured",
            "rules_summary": rules_data["summary"],
        }

        with open("project/data/experiments/sprint2c/llm_results.json", "w") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return

    llm_results, pending = evaluate_with_llm(instances, max_instances=30)

    # Compute comparison
    comparison = compute_comparison(rules_results, llm_results)

    # Analyze results
    metrics = {
        "llm_total": len(llm_results),
        "llm_correct_by_level": defaultdict(int),
        "llm_total_by_level": defaultdict(int),
        "rules_correct_by_level": defaultdict(int),
        "rules_total_by_level": defaultdict(int),
        "pending_adjudication": len(pending),
    }

    for c in comparison:
        level = c.get("difficulty", 0)
        metrics["llm_total_by_level"][level] += 1
        metrics["rules_total_by_level"][level] += 1

        # LLM is correct if it predicted something (we don't have true gold)
        # For now, just count predictions
        if c.get("llm_entity"):
            metrics["llm_correct_by_level"][level] += 1

        if c.get("rules_correct"):
            metrics["rules_correct_by_level"][level] += 1

    # Print results
    print("\n" + "=" * 60)
    print("COMPARISON: RULES vs LLM")
    print("=" * 60)

    print(f"\nLLM Evaluation Summary:")
    print(f"  Total evaluated: {metrics['llm_total']}")
    print(f"  Pending adjudication: {metrics['pending_adjudication']}")

    print(f"\nBy Difficulty Level:")
    for level in sorted(metrics["llm_total_by_level"].keys()):
        llm_corr = metrics["llm_correct_by_level"][level]
        llm_tot = metrics["llm_total_by_level"][level]
        rules_corr = metrics["rules_correct_by_level"][level]
        rules_tot = metrics["rules_total_by_level"][level]

        llm_pct = (llm_corr / llm_tot * 100) if llm_tot > 0 else 0
        rules_pct = (rules_corr / rules_tot * 100) if rules_tot > 0 else 0

        print(f"\n  Level {level}:")
        print(f"    LLM predictions: {llm_corr}/{llm_tot} ({llm_pct:.1f}%)")
        print(f"    Rules accuracy:  {rules_corr}/{rules_tot} ({rules_pct:.1f}%)")

    # Save results
    output = {
        "llm_available": True,
        "llm_results": llm_results,
        "pending_adjudication": pending,
        "comparison": comparison,
        "metrics": dict(metrics),
    }

    with open(
        "project/data/experiments/sprint2c/llm_results.json", "w", encoding="utf-8"
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved LLM results to project/data/experiments/sprint2c/llm_results.json")

    # Show sample LLM responses
    print("\n--- Sample LLM Responses ---")
    for r in llm_results[:5]:
        if r.get("llm_entity"):
            reasoning = r.get("llm_reasoning") or "N/A"
            print(f"\n  {r['verse_ref']}: {r['verb']}")
            print(f"    LLM says: {r['llm_entity']} ({r['llm_confidence']})")
            print(f"    Reasoning: {reasoning[:100] if reasoning else 'N/A'}")


if __name__ == "__main__":
    main()
