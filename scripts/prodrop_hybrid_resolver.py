#!/usr/bin/env python3
"""
Pro-Drop Hybrid Resolver
Combines rule-based and LLM-based approaches for null subject resolution in Ancient Greek.

Architecture:
- Level 1 (Clear): Rules only (fast, 100% accuracy on pilot)
- Level 2+3 (Ambiguous + Complex): LLM with rules fallback
"""

import json
import os
import time
import re
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Check for Gemini SDK
try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class DifficultyLevel(Enum):
    CLEAR = 1  # Level 1: 1 compatible entity
    AMBIGUOUS = 2  # Level 2: 2+ compatible entities
    COMPLEX = 3  # Level 3: δέ/tote/genitive absolute


@dataclass
class ProDropInstance:
    """A pro-drop verb instance to resolve."""

    verse_ref: str
    sentence_text: str
    context_5verses: str
    verb_form: str
    verb_lemma: str
    person: int
    number: str
    entities: List[Dict[str, str]]  # [{'form': 'Ἰησοῦς', 'lemma': 'Ἰησοῦς', ...}]
    narrative_markers: Dict[str, bool]
    difficulty_level: DifficultyLevel = None

    def __post_init__(self):
        if self.difficulty_level is None:
            self.difficulty_level = self._classify_difficulty()

    def _classify_difficulty(self) -> DifficultyLevel:
        """Classify difficulty based on entities and markers."""
        # Check for complex markers
        if self.narrative_markers.get("delta_adversative", False):
            return DifficultyLevel.COMPLEX
        if self.narrative_markers.get("tote_shift", False):
            return DifficultyLevel.COMPLEX
        if self.narrative_markers.get("genitive_absolute", False):
            return DifficultyLevel.COMPLEX

        # Count unique entities
        unique_entities = set(e.get("lemma", "") for e in self.entities)

        if len(unique_entities) <= 1:
            return DifficultyLevel.CLEAR
        else:
            return DifficultyLevel.AMBIGUOUS


@dataclass
class ResolutionResult:
    """Result of pro-drop resolution."""

    entity: Optional[str]
    confidence: str  # 'high', 'medium', 'low'
    method: str  # 'RULES', 'LLM', 'HYBRID', 'UNKNOWN'
    reasoning: str
    level: DifficultyLevel


class AliasResolver:
    """Resolves character lemmas to canonical IDs."""

    ALIASES = {
        # PETROS (Peter)
        "Σίμων": "PETROS",
        "Σίμωνα": "PETROS",
        "Πέτρος": "PETROS",
        "Πέτρον": "PETROS",
        "Πέτρῳ": "PETROS",
        "Πέτρου": "PETROS",
        "Πέτρῳ": "PETROS",
        "Κηφᾶς": "PETROS",
        "Κηφᾶν": "PETROS",
        # IESOUS (Jesus)
        "Ἰησοῦς": "IESOUS",
        "Ἰησοῦν": "IESOUS",
        "Ἰησοῦ": "IESOUS",
        "Ἰησοῖς": "IESOUS",
        "Ἰησοῦν": "IESOUS",
        "Ἰησοῦς": "IESOUS",
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
        # IAKOBOS (James)
        "Ἰάκωβος": "IAKOBOS",
        "Ἰακώβου": "IAKOBOS",
        "Ἰακώβῳ": "IAKOBOS",
        "Ἰάκωβον": "IAKOBOS",
        "Ἰάκωβος": "IAKOBOS",
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
        # IACON (John - alternate spelling)
        "Ἰωάνης": "IOANNES",
        "Ἰωάνου": "IOANNES",
        "Ἰωάνῃ": "IOANNES",
        # STEPHANOS (Stephen)
        "Στέφανος": "STEPHANOS",
        "Στεφάνου": "STEPHANOS",
        "Στέφανον": "STEPHANOS",
        # BARNABAS (Barnabas)
        "Βαρνάβας": "BARNABAS",
        "Βαρναβᾶ": "BARNABAS",
        "Βαρνάβαν": "BARNABAS",
        # DEMETRIOS (Demetrius)
        "Δημήτριος": "DEMETRIOS",
        "Δημητρίου": "DEMETRIOS",
        "Δημήτριον": "DEMETRIOS",
        # GEORGIOS (George)
        "Γεώργιος": "GEORGIOS",
        "Γεωργίου": "GEORGIOS",
        "Γεώργιον": "GEORGIOS",
        # NICODEMOS (Nicodemus)
        "Νικόδημος": "NICODEMOS",
        "Νικοδήμου": "NICODEMOS",
        "Νικόδημον": "NICODEMOS",
        # LAZAROS (Lazarus)
        "Λάζαρος": "LAZAROS",
        "Λαζάρου": "LAZAROS",
        "Λάζαρον": "LAZAROS",
        # MARIA (Mary - Magdalene)
        "Μαρία": "MARIA",
        "Μαρίας": "MARIA",
        "Μαρίαν": "MARIA",
        "Μαρίας": "MARIA",
        # MARTHA
        "Μάρθα": "MARTHA",
        "Μάρθης": "MARTHA",
        "Μάρθαν": "MARTHA",
        # SALOME
        "Σαλώμη": "SALOME",
        "Σαλώμης": "SALOME",
        "Σαλώμην": "SALOME",
        # PILATOS (Pilate)
        "Πιλᾶτος": "PILATOS",
        "Πιλάτου": "PILATOS",
        "Πιλᾶτον": "PILATOS",
        "Πιλάτῳ": "PILATOS",
        # CAIAPHAS
        "Καϊάφας": "CAIAPHAS",
        "Καϊάφα": "CAIAPHAS",
        "Καϊάφαν": "CAIAPHAS",
        # ANANIAS
        "Ἀνανίας": "ANANIAS",
        "Ἀνανίου": "ANANIAS",
        "Ἀνανίαν": "ANANIAS",
        # SAPPHIRA
        "Σαπφείρη": "SAPPHIRA",
        "Σαπφείρης": "SAPPHIRA",
        "Σαπφείρην": "SAPPHIRA",
        # TIMOTHEOS (Timothy)
        "Τιμόθεος": "TIMOTHEOS",
        "Τιμοθέου": "TIMOTHEOS",
        "Τιμόθεον": "TIMOTHEOS",
        "Τιμοθέῳ": "TIMOTHEOS",
        # SILAS
        "Σίλας": "SILAS",
        "Σίλα": "SILAS",
        "Σίλαν": "SILAS",
        # Titus
        "Τίτος": "TITUS",
        "Τίτου": "TITUS",
        "Τίτον": "TITUS",
    }

    @classmethod
    def resolve(cls, lemma: str) -> str:
        """Resolve lemma to canonical ID."""
        return cls.ALIASES.get(lemma, lemma.upper() if lemma else None)


class RuleBasedResolver:
    """Rule-based pro-drop resolver."""

    PLURAL_CANONICAL_IDS = {
        "OI_MATHETAI",  # The disciples
        "OI_FARISAIOI",  # The Pharisees
        "OI_GRAMMATEIS",  # The scribes
        "OI_IOUDAIOI",  # The Jews
        "OI_APOSTOLOI",  # The apostles
        "OI_PRESBUTEROI",  # The elders
        "OI_HIEREIS",  # The priests
        "OI_GALILAIOI",  # The Galileans
        "OI_SAMARITAI",  # The Samaritans
        "OI_ETHNIKOI",  # The Gentiles
    }

    def _is_plural_entity(self, entity_id: str) -> bool:
        """Check if an entity is plural (group)."""
        if entity_id is None:
            return False
        entity_id_upper = entity_id.upper()
        return entity_id_upper in self.PLURAL_CANONICAL_IDS

    def _filter_by_number(self, entities: list, target_number: str) -> list:
        """
        Filter entities by number compatibility.
        For 3rd singular verbs: only singular entities
        For 3rd plural verbs: only plural entities or groups
        """
        if target_number == "plural":
            return [
                e
                for e in entities
                if self._is_plural_entity(AliasResolver.resolve(e.get("lemma", "")))
            ]
        else:
            return [
                e
                for e in entities
                if not self._is_plural_entity(AliasResolver.resolve(e.get("lemma", "")))
            ]

    def resolve(self, instance: ProDropInstance) -> ResolutionResult:
        """Apply rules to resolve pro-drop."""
        entities = instance.entities

        if not entities:
            return ResolutionResult(
                entity=None,
                confidence="low",
                method="RULES",
                reasoning="No entities in window",
                level=instance.difficulty_level,
            )

        target_number = instance.number

        filtered_entities = self._filter_by_number(entities, target_number)

        if not filtered_entities:
            filtered_entities = entities

        if len(filtered_entities) == 1:
            entity = filtered_entities[0]
            canonical = AliasResolver.resolve(entity.get("lemma", ""))
            return ResolutionResult(
                entity=canonical,
                confidence="high",
                method="RULES",
                reasoning=f"Single compatible entity in window (number={target_number})",
                level=instance.difficulty_level,
            )

        if len(filtered_entities) == 0:
            return ResolutionResult(
                entity=None,
                confidence="low",
                method="RULES",
                reasoning=f"No entities matching number={target_number}",
                level=instance.difficulty_level,
            )

        # Level 1: Single entity after filtering - use it directly
        if instance.difficulty_level == DifficultyLevel.CLEAR:
            entity = filtered_entities[0]
            canonical = AliasResolver.resolve(entity.get("lemma", ""))
            return ResolutionResult(
                entity=canonical,
                confidence="high",
                method="RULES",
                reasoning=f"Single compatible entity after number filter ({target_number})",
                level=instance.difficulty_level,
            )

        # Level 2+3: Multiple entities - use heuristics

        # Strategy 1: Most recently mentioned (salience)
        most_recent = filtered_entities[-1] if filtered_entities else None
        most_recent_canonical = AliasResolver.resolve(
            most_recent.get("lemma", "") if most_recent else ""
        )

        # Strategy 2: Check for genitive absolute
        if instance.narrative_markers.get("genitive_absolute", False):
            return ResolutionResult(
                entity=most_recent_canonical,
                confidence="medium",
                method="RULES",
                reasoning="Genitive absolute construction detected",
                level=instance.difficulty_level,
            )

        # Strategy 3: δέ adversative - look for new subject
        if instance.narrative_markers.get("delta_adversative", False):
            if len(filtered_entities) > 1:
                new_entity = (
                    filtered_entities[-2]
                    if len(filtered_entities) > 1
                    else filtered_entities[-1]
                )
                return ResolutionResult(
                    entity=AliasResolver.resolve(new_entity.get("lemma", "")),
                    confidence="medium",
                    method="RULES",
                    reasoning="δέ adversative detected - looking for new subject",
                    level=instance.difficulty_level,
                )

        # Strategy 4: τότε shift
        if instance.narrative_markers.get("tote_shift", False):
            if len(filtered_entities) > 1:
                new_entity = (
                    filtered_entities[-2]
                    if len(filtered_entities) > 1
                    else filtered_entities[-1]
                )
                return ResolutionResult(
                    entity=AliasResolver.resolve(new_entity.get("lemma", "")),
                    confidence="medium",
                    method="RULES",
                    reasoning="τότε detected - narrative time shift",
                    level=instance.difficulty_level,
                )

        # Default: salience heuristic (most frequently mentioned entity)
        from collections import Counter

        canonical_counts = Counter()
        for e in filtered_entities:
            canon = AliasResolver.resolve(e.get("lemma", ""))
            if canon:
                canonical_counts[canon] += 1

        if canonical_counts:
            most_salient = canonical_counts.most_common(1)[0][0]
            return ResolutionResult(
                entity=most_salient,
                confidence="low",
                method="RULES",
                reasoning=f"Salience heuristic: {len(filtered_entities)} entities, most frequent = {most_salient}",
                level=instance.difficulty_level,
            )

        # Fallback to most recent
        return ResolutionResult(
            entity=most_recent_canonical,
            confidence="low",
            method="RULES",
            reasoning=f"Multiple entities ({len(filtered_entities)}) - fallback to most recent",
            level=instance.difficulty_level,
        )


class LLMResolver:
    """LLM-based pro-drop resolver using Gemini."""

    def __init__(self, model: str = "gemini-3.1-pro-preview"):
        self.model = model
        self.client = None
        if GEMINI_AVAILABLE:
            api_key = os.environ.get("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)

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

        # Extract entity
        entity_match = re.search(r"Entity:\s*(.+)", response_text)
        if entity_match:
            entity = entity_match.group(1).strip()
            if entity.upper() == "UNKNOWN":
                entity = None

        # Extract confidence
        conf_match = re.search(
            r"Confidence:\s*(high|medium|low)", response_text, re.IGNORECASE
        )
        if conf_match:
            confidence = conf_match.group(1).lower()

        # Extract reasoning
        reason_match = re.search(r"Reasoning:\s*(.+)", response_text, re.DOTALL)
        if reason_match:
            reasoning = reason_match.group(1).strip()[:300]

        return entity, confidence, reasoning

    def resolve(self, instance: ProDropInstance) -> ResolutionResult:
        """Resolve using LLM."""
        if not self.client:
            return ResolutionResult(
                entity=None,
                confidence="low",
                method="LLM",
                reasoning="LLM not available (no API key)",
                level=instance.difficulty_level,
            )

        prompt = self._build_prompt(instance)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": 0.1, "max_output_tokens": 300},
            )

            # Extract text from response
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

            entity, confidence, reasoning = self._parse_response(response_text)

            # Resolve to canonical ID
            if entity:
                entity = AliasResolver.resolve(entity)

            return ResolutionResult(
                entity=entity,
                confidence=confidence,
                method="LLM",
                reasoning=reasoning,
                level=instance.difficulty_level,
            )

        except Exception as e:
            return ResolutionResult(
                entity=None,
                confidence="low",
                method="LLM",
                reasoning=f"LLM error: {str(e)[:100]}",
                level=instance.difficulty_level,
            )


class ProDropHybridResolver:
    """
    Hybrid pro-drop resolver combining rules and LLM.

    Architecture:
    - Level 1 (Clear): Rules only
    - Level 2+3 (Ambiguous + Complex): LLM with rules fallback
    """

    def __init__(self, use_llm: bool = True):
        self.rules_resolver = RuleBasedResolver()
        self.llm_resolver = LLMResolver() if use_llm else None
        self.use_llm = use_llm and GEMINI_AVAILABLE

    def resolve(self, instance: ProDropInstance) -> ResolutionResult:
        """Resolve pro-drop using hybrid approach."""
        # Level 1: Use rules if entities exist, otherwise try LLM
        if instance.difficulty_level == DifficultyLevel.CLEAR:
            rules_result = self.rules_resolver.resolve(instance)

            # If rules found an entity, use it
            if rules_result.entity:
                return rules_result

            # No entities found - try LLM for Level 1
            if self.use_llm and self.llm_resolver:
                llm_result = self.llm_resolver.resolve(instance)
                if llm_result.entity:
                    return ResolutionResult(
                        entity=llm_result.entity,
                        confidence="medium",
                        method="LLM_FALLBACK",
                        reasoning=f"Level 1 with no entities - LLM resolved: {llm_result.reasoning[:100]}",
                        level=instance.difficulty_level,
                    )

            # Fallback to rules result (which has NONE)
            return rules_result

        # Level 2+3: Use LLM if available, fallback to rules
        if self.use_llm and self.llm_resolver:
            llm_result = self.llm_resolver.resolve(instance)

            # If LLM succeeded, return it
            if llm_result.entity:
                return llm_result

            # LLM failed, fallback to rules
            rules_result = self.rules_resolver.resolve(instance)
            return ResolutionResult(
                entity=rules_result.entity,
                confidence=rules_result.confidence,
                method="HYBRID",
                reasoning=f"LLM failed: {llm_result.reasoning[:50]}. "
                + rules_result.reasoning,
                level=instance.difficulty_level,
            )

        # LLM not available, use rules only
        return self.rules_resolver.resolve(instance)

    def resolve_batch(self, instances: List[ProDropInstance]) -> List[ResolutionResult]:
        """Resolve multiple instances."""
        results = []
        for instance in instances:
            result = self.resolve(instance)
            results.append(result)
            # Rate limiting for LLM
            if self.use_llm:
                time.sleep(0.3)
        return results


def load_evaluation_dataset(path: str) -> List[ProDropInstance]:
    """Load evaluation dataset from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    instances = []
    for item in data.get("instances", []):
        # Convert narrative markers
        markers = item.get("narrative_markers", {})
        if isinstance(markers, dict):
            markers = {
                "delta_adversative": markers.get("delta_adversative", False),
                "tote_shift": markers.get("tote_shift", False),
                "genitive_absolute": markers.get("genitive_absolute", False),
            }

        # Convert entities
        entities = [
            {"form": e.get("form", ""), "lemma": e.get("lemma", "")}
            for e in item.get("entities_in_window", [])
        ]

        instance = ProDropInstance(
            verse_ref=item.get("verse_ref", ""),
            sentence_text=item.get("sentence_text", ""),
            context_5verses=item.get("context_5verses", ""),
            verb_form=item.get("verb_form", ""),
            verb_lemma=item.get("verb_lemma", ""),
            person=item.get("person", 3),
            number=item.get("number", "singular"),
            entities=entities,
            narrative_markers=markers,
        )
        instances.append(instance)

    return instances


def main():
    """Test the hybrid resolver."""
    print("=" * 60)
    print("Pro-Drop Hybrid Resolver Test")
    print("=" * 60)

    # Load test data
    dataset_path = "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found: {dataset_path}")
        return

    instances = load_evaluation_dataset(dataset_path)
    print(f"Loaded {len(instances)} instances")

    # Initialize resolver
    resolver = ProDropHybridResolver(use_llm=True)
    print(f"LLM available: {resolver.use_llm}")

    # Test on sample instances
    print("\n--- Testing on sample instances ---")

    # Test Level 1
    level1_samples = [
        i for i in instances if i.difficulty_level == DifficultyLevel.CLEAR
    ][:3]
    print(f"\nLevel 1 (Clear) - {len(level1_samples)} samples:")
    for inst in level1_samples:
        result = resolver.resolve(inst)
        print(f"  {inst.verse_ref}: {inst.verb_form}")
        print(f"    Method: {result.method}, Entity: {result.entity}")

    # Test Level 2
    level2_samples = [
        i for i in instances if i.difficulty_level == DifficultyLevel.AMBIGUOUS
    ][:3]
    print(f"\nLevel 2 (Ambiguous) - {len(level2_samples)} samples:")
    for inst in level2_samples:
        result = resolver.resolve(inst)
        print(f"  {inst.verse_ref}: {inst.verb_form}")
        print(f"    Method: {result.method}, Entity: {result.entity}")
        print(f"    Reasoning: {result.reasoning[:80]}")

    # Test Level 3
    level3_samples = [
        i for i in instances if i.difficulty_level == DifficultyLevel.COMPLEX
    ][:3]
    print(f"\nLevel 3 (Complex) - {len(level3_samples)} samples:")
    for inst in level3_samples:
        result = resolver.resolve(inst)
        print(f"  {inst.verse_ref}: {inst.verb_form}")
        print(f"    Method: {result.method}, Entity: {result.entity}")
        print(f"    Reasoning: {result.reasoning[:80]}")


if __name__ == "__main__":
    main()
