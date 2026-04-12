#!/usr/bin/env python3
"""
Phase 1: Dependency Parsing Integration for Pro-Drop Detection

Load PROIEL CONLLU data directly and detect finite verbs without nsubj (pro-drop candidates).
This replaces the fragile entity window approach with proper dependency-based detection.
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Token:
    id: int
    form: str
    lemma: str
    pos: str
    feats: Optional[str]
    head: Optional[int]
    relation: str
    deps: Optional[str]
    misc: Optional[str]

    def get_antecedent_id(self) -> Optional[int]:
        """Extract antecedent ID from MISC column (AntId=XXXXX format)."""
        if not self.misc:
            return None
        match = re.search(r"AntId=(\d+)", self.misc)
        return int(match.group(1)) if match else None

    def is_finite_verb(self) -> bool:
        """Check if token is a finite verb based on POS and morphology."""
        if not self.pos.startswith("V"):
            return False
        if not self.feats:
            return False
        if self.feats == "_":
            return False
        return True

    def get_person(self) -> Optional[int]:
        """Extract person from morphological features."""
        if not self.feats or self.feats == "_":
            return None
        # Handle original PROIEL format: "3saim----i"
        match = re.search(r"(\d)[spd]", self.feats)
        if match:
            return int(match.group(1))
        # Handle new CONLLU format: "Number=Sing|Gender=Masc|Case=_"
        match = re.search(r"Person=(\d)", self.feats)
        if match:
            return int(match.group(1))
        return None


NARRATIVE_MARKERS = {
    "δέ": "continuity",  # δέ can mean same subject (continuity) or alternated (contrast)
    "τότε": "temporal",  # τότε = "then" - marks narrative shift
    "καί": "addition",  # καί = "and" - typically same subject
    "γάρ": "cause",  # γάρ = "for" - same subject continues
    "οὖν": "inference",  # οὖν = "therefore" - same subject
    "ἵνα": "purpose",  # ἵνα = "so that" - same subject
}

GENITIVE_ABSOLUTE_MARKERS = {"γενόμενος", "γενομένης", "ὄντος", "οὔσης", "θανάτου"}


def extract_narrative_features(sentence) -> Dict:
    """Extract narrative markers from sentence for disambiguation.

    Returns:
        features: dict with has_delta, has_tote, first_word, etc.
    """
    features = {
        "has_delta": False,
        "has_tote": False,
        "has_kai": False,
        "has_gar": False,
        "has_genitive_absolute": False,
        "starts_with_delta": False,
        "starts_with_tote": False,
        "delta_at_position_2": False,  # e.g., "καὶ δέ" pattern
    }

    # Get all token forms
    token_forms = [t.form for t in sentence.tokens]
    sentence_text = " ".join(token_forms)

    features["has_delta"] = "δέ" in sentence_text
    features["has_tote"] = "τότε" in sentence_text
    features["has_kai"] = "καί" in sentence_text or "καὶ" in sentence_text
    features["has_gar"] = "γάρ" in sentence_text or "γαρ" in sentence_text

    # Check first token(s) for narrative markers
    if token_forms:
        first_token = token_forms[0].lower()
        features["starts_with_delta"] = first_token == "δέ"
        features["starts_with_tote"] = first_token == "τότε" or first_token == "τότε"

        # Check second token for "καὶ δέ" pattern (very common for subject continuation)
        if len(token_forms) > 1:
            second_token = token_forms[1].lower()
            if second_token == "δέ":
                features["delta_at_position_2"] = True

        # Also check "οἱ δέ", "ὁ δέ", "αἱ δέ" patterns (article + δέ = subject continuity)
        features["article_delta_pattern"] = any(
            token_forms[i] in ("ὁ", "οἱ", "ἡ", "αἱ")
            and i + 1 < len(token_forms)
            and token_forms[i + 1].lower() == "δέ"
            for i in range(len(token_forms) - 1)
        )

    return features


def apply_narrative_rules(
    sentence, predicate_analysis: Dict, prev_subject: Optional[str] = None
) -> Dict:
    """
    Apply δέ/τότε narrative marker rules to disambiguate pro-drop candidates.

    Rules:
    - τότε at sentence start: narrative shift → DIFFERENT subject → likely pro-drop
    - δέ at sentence start: could be same or different subject → check context
    - δέ after article (οἱ δέ, ὁ δέ): subject continuity → likely NOT pro-drop
    - No narrative marker: default to original rule

    Args:
        sentence: Sentence object
        predicate_analysis: dict with predicate info including is_pro_drop_candidate
        prev_subject: subject from previous sentence (if known)

    Returns:
        Updated analysis dict with narrative_disambiguation reason
    """
    narrative = extract_narrative_features(sentence)
    form = predicate_analysis["form"]
    is_candidate = predicate_analysis.get("is_pro_drop_candidate", False)

    result = predicate_analysis.copy()
    result["narrative_marker"] = None
    result["narrative_disambiguation"] = "default"  # default: keep as-is

    if not is_candidate:
        return result

    # τότε = "then" - typically marks narrative shift to DIFFERENT subject
    # This STRENGTHENS the pro-drop detection (likely different subject)
    if narrative.get("starts_with_tote") or narrative.get("has_tote"):
        result["narrative_marker"] = "τότε"
        result["narrative_disambiguation"] = (
            "keep"  # τότε confirms different subject → pro-drop likely
        )
        return result

    # δέ anywhere in sentence - just mark it, don't filter
    # The "καὶ δέ" pattern does NOT mean "not pro-drop" - the subject can still be implicit
    # We keep these as pro-drop candidates but add the marker for analysis
    if narrative.get("has_delta"):
        result["narrative_marker"] = "δέ"
        result["narrative_disambiguation"] = (
            "keep"  # Don't filter - δέ doesn't guarantee explicit subject
        )
        return result

    # No specific narrative marker - use default
    return result

    # δέ anywhere in sentence - check for patterns
    if narrative.get("has_delta"):
        result["narrative_marker"] = "δέ"

        # Pattern 1: "καὶ δέ" at start (very common) → subject likely continues
        # Pattern 2: "οἱ δέ" / "ὁ δέ" → subject likely continues
        if narrative.get("delta_at_position_2") or narrative.get(
            "article_delta_pattern"
        ):
            result["narrative_disambiguation"] = (
                "filter_suggestion"  # likely same subject → NOT pro-drop
            )
        else:
            result["narrative_disambiguation"] = "keep"  # could be different subject
        return result

    # No specific narrative marker - use default
    return result

    # δέ at sentence start - context dependent
    if narrative.get("starts_with_delta"):
        result["narrative_marker"] = "δέ"

        # Rule: "οἱ δέ" or "ὁ δέ" pattern often means SAME subject continues
        # In this case, FILTER OUT (not pro-drop)
        if narrative.get("delta_after_article"):
            result["narrative_disambiguation"] = (
                "filter_suggestion"  # likely same subject
            )
        else:
            result["narrative_disambiguation"] = "keep"  # could be different subject
        return result

    # No specific narrative marker - use default
    return result


def is_genitive_absolute(sentence, verb_token_id: int) -> bool:
    """Check if verb is in a genitive absolute construction."""
    for token in sentence.tokens:
        if token.id == verb_token_id:
            if token.relation in ("advcl", "abl"):
                return True
    return False


def is_ambiguous(
    candidates: List[Dict], current_idx: int, sentence_index: Dict, window: int = 2
) -> Dict:
    """
    Classify a pro-drop candidate as clear or ambiguous.

    Returns:
        Dict with:
        - is_clear: bool
        - candidate_count: int
        - entity_count: int
        - narrative_shift: bool
        - reason: str
    """
    if current_idx >= len(candidates):
        return {"is_clear": True, "candidate_count": 0, "entity_count": 0}

    c = candidates[current_idx]
    sent_id = c.get("sentence_id", "")
    sent = sentence_index.get(sent_id)

    if not sent:
        return {
            "is_clear": True,
            "candidate_count": 0,
            "entity_count": 0,
            "reason": "no sentence",
        }

    sentence_text = c.get("sentence_text", "")
    narrative = extract_narrative_features(sentence_text)

    persons = find_persons_in_preceding_sentences(
        [sent], sent_id, sentence_index, window
    )

    unique_entities = list(dict.fromkeys(persons))
    entity_count = len(unique_entities)
    candidate_count = len(persons)

    is_clear = entity_count == 1 and candidate_count == 1
    has_shift = narrative.get("has_tote", False) or is_genitive_absolute(
        sent, c.get("verb_token_id", 0)
    )

    if has_shift:
        reason = "narrative shift marker"
    elif entity_count == 0:
        reason = "no antecedent found"
    elif entity_count == 1:
        reason = "single clear candidate"
    else:
        reason = f"{entity_count} entities in window"

    return {
        "is_clear": is_clear,
        "candidate_count": candidate_count,
        "entity_count": entity_count,
        "narrative_shift": has_shift,
        "has_delta": narrative.get("has_delta", False),
        "reason": reason,
    }


PERSON_LEMMAS = {
    "Ἰησοῦς",
    "πέτρος",
    "ἰωάννης",
    "ἰωάν(ν)ης",
    "ἰάκωβος",
    "ἀνδρέας",
    "φίλιππος",
    "βαρθολομαῖος",
    "ματθαῖος",
    "θωμᾶς",
    "σίμων",
    "παῦλος",
    "βαρνάβας",
    "στέφανος",
    "τηλᾶς",
    "νικόλαος",
    "ἀκύλας",
    "τιμόθεος",
    "τίτος",
    "φύρεικος",
    "ἑρμῆς",
    "μαρία",
    "μαρία ἡ μαγδαληνή",
    "σαμαρῖτις",
    "σαμαρίτις",
    "πιλᾶτος",
    "ἡρῴδης",
    "ἡρῴδια",
    "καΐφας",
    "νικόδημος",
    "λαζάρος",
    "μάρθα",
    "νικόδημος",
    "ἰούδας",
    "ληστής",
    "ἀρχιερεύς",
    "φαρισαῖος",
    "γραμματεύς",
}

CANONICAL_ALIASES = {
    "σίμων": "ΠΕΤΡΟΣ",
    "κηφᾶς": "ΠΕΤΡΟΣ",
    "πέτρος": "ΠΕΤΡΟΣ",
    "σαῦλος": "ΠΑΥΛΟΣ",
    "παῦλος": "ΠΑΥΛΟΣ",
    "ἰωάν(ν)ης": "ΙΩΑΝΝΗΣ",
    "ἰωάννης": "ΙΩΑΝΝΗΣ",
    "ἰάκωβος": "ΙΑΚΩΒΟΣ",
    "ἀνδρέας": "ΑΝΔΡΕΑΣ",
    "φίλιππος": "ΦΙΛΙΠΠΟΣ",
    "βαρθολομαῖος": "ΒΑΡΘΟΛΟΜΑΙΟΣ",
    "ματθαῖος": "ΜΑΤΘΑΙΟΣ",
    "θωμᾶς": "ΘΩΜΑΣ",
    "ἰησοῦς": "IESOUS",
    "βαρνάβας": "ΒΑΡΝΑΒΑΣ",
    "στέφανος": "ΣΤΕΦΑΝΟΣ",
    "μαρία": "ΜΑΡΙΑ",
    "πιλᾶτος": "ΠΙΛΑΤΟΣ",
    "ἡρῴδης": "ΗΡΩΔΗΣ",
    "σαμαρῖτις": "ΣΑΜΑΡΙΤΙΣ",
    "σαμαρίτις": "ΣΑΜΑΡΙΤΙΣ",
    "νικόδημος": "ΝΙΚΟΔΗΜΟΣ",
    "λαζάρος": "ΛΑΖΑΡΟΣ",
    "μάρθα": "ΜΑΡΘΑ",
    "ἰούδας": "ΙΟΥΔΑΣ",
    "καϊφας": "ΚΑΪΦΑΣ",
    "καΐφας": "ΚΑΪΦΑΣ",
    "ἀρχιερεύς": "ΑΡΧΙΕΡΕΥΣ",
    "φαρισαῖος": "ΦΑΡΙΣΑΙΟΣ",
    "γραμματεύς": "ΓΡΑΜΜΑΤΕΥΣ",
    "ληστής": "ΛΗΣΤΗΣ",
    "ἑρμῆς": "ΕΡΜΗΣ",
    "τιμόθεος": "ΤΙΜΟΘΕΟΣ",
    "τίτος": "ΤΙΤΟΣ",
    "ἀκύλας": "ΑΚΥΛΑΣ",
    "νικόλαος": "ΝΙΚΟΛΑΟΣ",
}


KNOWN_CANONICAL_ENTITIES = {
    "IESOUS",
    "ΠΕΤΡΟΣ",
    "ΙΩΑΝΝΗΣ",
    "ΙΑΚΩΒΟΣ",
    "ΑΝΔΡΕΑΣ",
    "ΦΙΛΙΠΠΟΣ",
    "ΒΑΡΘΟΛΟΜΑΙΟΣ",
    "ΜΑΤΘΑΙΟΣ",
    "ΘΩΜΑΣ",
    "ΣΙΜΩΝ",
    "ΠΑΥΛΟΣ",
    "ΒΑΡΝΑΒΑΣ",
    "ΣΤΕΦΑΝΟΣ",
    "ΜΑΡΙΑ",
    "ΠΙΛΑΤΟΣ",
    "ΗΡΩΔΗΣ",
    "ΣΑΜΑΡΙΤΙΣ",
    "ΝΙΚΟΔΗΜΟΣ",
    "ΛΑΖΑΡΟΣ",
    "ΜΑΡΘΑ",
    "ΙΟΥΔΑΣ",
    "ΚΑΪΦΑΣ",
    "ΑΡΧΙΕΡΕΥΣ",
    "ΦΑΡΙΣΑΙΟΣ",
    "ΓΡΑΜΜΑΤΕΥΣ",
    "ΛΗΣΤΗΣ",
    "ΕΡΜΗΣ",
    "ΤΙΜΟΘΕΟΣ",
    "ΤΙΤΟΣ",
    "ΑΚΥΛΑΣ",
    "ΝΙΚΟΛΑΟΣ",
}


def get_canonical_entity(lemma: str) -> Optional[str]:
    """Map a lemma to its canonical entity ID using alias dictionary."""
    if not lemma:
        return None
    lemma_normalized = lemma.lower().strip("()")
    canonical = CANONICAL_ALIASES.get(lemma_normalized, lemma.upper())
    if canonical in KNOWN_CANONICAL_ENTITIES:
        return canonical
    if canonical.upper() in KNOWN_CANONICAL_ENTITIES:
        return canonical.upper()
    return None


def compare_head_matching(predicted_lemma: str, gold_lemma: str) -> bool:
    """
    Compare two entities using HEAD-MATCHING (CRAC standard).

    Instead of exact string matching, compare canonical entity IDs.
    This handles Greek case inflection (Ἰησοῦς vs Ἰησοῦν vs τῷ Ἰησοῦ).
    """
    pred_canonical = get_canonical_entity(predicted_lemma)
    gold_canonical = get_canonical_entity(gold_lemma)

    if pred_canonical and gold_canonical:
        return pred_canonical == gold_canonical

    return predicted_lemma.upper() == gold_lemma.upper()


def find_persons_in_context(sent, verb_token_id: int, window: int = 2) -> List[str]:
    """
    Find person entity lemmas in the context before a verb.
    Scan the preceding tokens to find nouns (N*, Ne) that could be subjects.
    """
    persons = []

    for token in sent.tokens:
        if token.id < verb_token_id and token.pos in ("Ne", "Nb", "Nn"):
            lemma = token.lemma.lower()
            if lemma in PERSON_LEMMAS or lemma in CANONICAL_ALIASES:
                canonical = get_canonical_entity(lemma)
                if canonical:
                    persons.append(canonical)

    return persons[-window:] if persons else []


def find_persons_in_preceding_sentences(
    sentences: List, current_sent_id: str, sentence_index: Dict, window: int = 2
) -> List[str]:
    """
    Find person entities in preceding sentences, ordered by verse reference.
    Only considers sentences from the same book (e.g., MARK, ACTS).
    """
    current_sent = sentence_index.get(current_sent_id)
    if not current_sent or not current_sent.verse_refs:
        return []

    current_book = (
        current_sent.verse_refs[0].split()[0] if current_sent.verse_refs else ""
    )

    all_sentences = sorted(
        sentences, key=lambda s: s.verse_refs[0] if s.verse_refs else ""
    )

    all_sent_ids = [s.id for s in all_sentences]
    current_idx = -1
    for i, sid in enumerate(all_sent_ids):
        if sid == current_sent_id:
            current_idx = i
            break

    if current_idx < 0:
        return []

    persons = []
    look_back = min(window, current_idx)

    for idx in range(current_idx - look_back, current_idx):
        sent = all_sentences[idx]
        if sent:
            sent_book = sent.verse_refs[0].split()[0] if sent.verse_refs else ""
            if sent_book != current_book:
                continue

            for token in sent.tokens:
                if token.pos in ("Ne", "Nb", "Nn"):
                    lemma = token.lemma.lower()
                    if lemma in PERSON_LEMMAS or lemma in CANONICAL_ALIASES:
                        canonical = get_canonical_entity(lemma)
                        if canonical:
                            persons.append(canonical)

    return persons


def find_persons_in_sentence_before_verb(
    sentence: "Sentence", verb_token_id: int
) -> List[str]:
    """Find person entities in the same sentence before the verb."""
    persons = []
    for token in sentence.tokens:
        if token.id >= verb_token_id:
            continue
        if token.pos in ("Ne", "Nb", "Nn"):
            lemma = token.lemma.lower()
            if lemma in PERSON_LEMMAS or lemma in CANONICAL_ALIASES:
                canonical = get_canonical_entity(lemma)
                if canonical:
                    persons.append(canonical)
    return persons


def get_verb_person_number(verb_morph: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract person and number from verb morphology."""
    if not verb_morph:
        return None, None
    person_match = re.search(r"(\d)", verb_morph)
    number_match = re.search(r"(sg|pl)", verb_morph)
    person = int(person_match.group(1)) if person_match else None
    number = number_match.group(1) if number_match else None
    return person, number


def get_entity_person_number(entity_canonical: str) -> Optional[str]:
    """Get the grammatical number for an entity (sg for persons usually)."""
    return "sg"


def score_candidate(
    candidate_entity: str,
    verb_morph: str,
    is_subject: bool,
    has_delta: bool,
    position_score: float,
) -> float:
    """Score a candidate entity based on multiple signals."""
    score = position_score

    person, number = get_verb_person_number(verb_morph)
    entity_number = get_entity_person_number(candidate_entity)

    if person == 3 and number == "sg" and entity_number == "sg":
        score += 1.0

    if is_subject:
        score += 3.0

    if has_delta:
        score += 0.5

    return score


def find_clause_subject(sentence: "Sentence", verb_head: int) -> Optional[Token]:
    """Find the grammatical subject of a verb in a sentence."""
    for token in sentence.tokens:
        if token.head == verb_head and token.relation in ("nsubj", "sub"):
            return token
    return None


def detect_delta_type(sentence_text: str) -> str:
    """Detect if δέ is adversative (at sentence start) or continuity (mid-sentence)."""
    text = sentence_text.strip()
    if text.startswith("δέ") or text.startswith("δὲ"):
        return "adversative"
    elif " δέ " in text or " δὲ " in text:
        return "continuity"
    return "none"


def is_genitive_absolute_in_sentence(sentence: "Sentence", verb_head: int) -> bool:
    """Check if verb has genitive absolute (dependency-based)."""
    for token in sentence.tokens:
        if token.head == verb_head and token.relation in ("advcl", "abl"):
            return True
    return False


def resolve_prodrop_with_clear_rules(
    sentences, candidates: List[Dict], sentence_index: Dict, window: int = 2
) -> List[Dict]:
    """
    Two-stage pro-drop resolution:
    - Stage 1 (Clear cases): Rule-based resolution with same-sentence priority
    - Stage 2 (Ambiguous): Would go to neural classifier (not yet implemented)

    Clear case = single entity in same sentence OR immediate previous sentence
    """
    results = []

    for c in candidates:
        sent_id = c.get("sentence_id", "")
        verb_token_id = c.get("verb_token_id")
        verb_morph = c.get("verb_morph", "")
        verse_refs = c.get("verse_refs", [])
        sentence_text = c.get("sentence_text", "")

        if not sent_id:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "no_sentence"
            results.append(c)
            continue

        sent = sentence_index.get(sent_id)
        if not sent:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "no_sentence_index"
            results.append(c)
            continue

        current_verse = verse_refs[0] if verse_refs else ""
        current_book = current_verse.split()[0] if current_verse else ""

        if not current_book:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "no_book"
            results.append(c)
            continue

        book_sentences = []
        for s in sentences:
            if s.verse_refs:
                book = s.verse_refs[0].split()[0]
                if book == current_book:
                    book_sentences.append(s)

        if not book_sentences:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "no_book_sentences"
            results.append(c)
            continue

        book_sentences = sorted(
            book_sentences, key=lambda s: s.verse_refs[0] if s.verse_refs else ""
        )

        current_sent_idx = -1
        for i, s in enumerate(book_sentences):
            if s.id == sent_id:
                current_sent_idx = i
                break

        if current_sent_idx < 0:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "not_in_book"
            results.append(c)
            continue

        has_delta = c.get("has_delta", False)
        has_tote = c.get("has_tote", False)
        has_genitive_abs = (
            is_genitive_absolute_in_sentence(sent, verb_token_id)
            if verb_token_id
            else False
        )

        delta_type = detect_delta_type(sentence_text) if has_delta else "none"

        person_candidates = []
        look_back = min(window, current_sent_idx)

        for idx in range(current_sent_idx - look_back, current_sent_idx + 1):
            if idx < 0:
                continue
            idx_sent = book_sentences[idx]
            if not idx_sent:
                continue

            for token in idx_sent.tokens:
                if idx == current_sent_idx and token.id >= verb_token_id:
                    continue

                if token.pos in ("Ne", "Nb", "Nn"):
                    lemma = token.lemma.lower()
                    canonical = get_canonical_entity(lemma)
                    if not canonical:
                        continue

                    is_subject = token.relation in ("nsubj", "sub")
                    is_same_sentence = idx == current_sent_idx

                    person_candidates.append(
                        {
                            "canonical": canonical,
                            "lemma": token.lemma,
                            "is_subject": is_subject,
                            "sentence_idx": idx,
                            "is_same_sentence": is_same_sentence,
                        }
                    )

        if not person_candidates:
            c["predicted_entity"] = None
            c["is_clear"] = False
            c["resolution_stage"] = "no_candidates"
            results.append(c)
            continue

        same_sentence_candidates = [
            pc for pc in person_candidates if pc["is_same_sentence"]
        ]
        previous_sentence_candidates = [
            pc for pc in person_candidates if not pc["is_same_sentence"]
        ]

        unique_entities_same = list(
            dict.fromkeys(pc["canonical"] for pc in same_sentence_candidates)
        )
        unique_entities_prev = list(
            dict.fromkeys(pc["canonical"] for pc in previous_sentence_candidates)
        )

        is_clear = False
        if has_tote or has_genitive_abs:
            is_clear = False
        elif has_delta and delta_type == "adversative":
            is_clear = False
        elif len(unique_entities_same) == 1 and len(same_sentence_candidates) >= 1:
            is_clear = True
        elif len(unique_entities_same) == 0 and len(unique_entities_prev) == 1:
            is_clear = True

        c["is_clear"] = is_clear
        c["entity_count_same"] = len(unique_entities_same)
        c["entity_count_prev"] = len(unique_entities_prev)
        c["delta_type"] = delta_type
        c["has_genitive_absolute"] = has_genitive_abs

        if c.get("gold_antecedent_entity"):
            print(
                f"  DEBUG: is_clear={is_clear}, same={len(unique_entities_same)}, prev={len(unique_entities_prev)}, τότε={has_tote}, gen_abs={has_genitive_abs}"
            )

        scoring_candidates = None

        if has_tote:
            if same_sentence_candidates:
                scoring_candidates = same_sentence_candidates
            else:
                scoring_candidates = previous_sentence_candidates
        elif has_genitive_abs:
            scoring_candidates = previous_sentence_candidates
        elif has_delta and delta_type == "adversative":
            if previous_sentence_candidates:
                scoring_candidates = previous_sentence_candidates
            elif same_sentence_candidates:
                scoring_candidates = same_sentence_candidates
        else:
            if same_sentence_candidates:
                scoring_candidates = same_sentence_candidates
            elif previous_sentence_candidates:
                scoring_candidates = previous_sentence_candidates

        if not scoring_candidates:
            c["predicted_entity"] = None
            c["resolution_stage"] = "no_scoring"
            results.append(c)
            continue

        unique_entities = []
        seen = set()
        for pc in reversed(scoring_candidates):
            if pc["canonical"] not in seen:
                unique_entities.append(pc)
                seen.add(pc["canonical"])

        person, number = get_verb_person_number(verb_morph)

        scored = []
        for pc in unique_entities:
            score = 1.0

            if pc["is_same_sentence"]:
                score += 8.0

            if pc["is_subject"]:
                score += 1.0

            if person == 3 and number == "sg":
                score += 1.0

            if has_delta:
                score += 0.5

            dist_from_current = current_sent_idx - pc["sentence_idx"]
            score += 0.5 / (dist_from_current + 1)

            scored.append(
                (pc["canonical"], score, pc["is_subject"], pc["is_same_sentence"])
            )

        scored.sort(key=lambda x: -x[1])

        if scored:
            c["predicted_entity"] = scored[0][0]
            c["is_predicted_subject"] = scored[0][2]
            c["prediction_score"] = scored[0][1]
            c["resolution_stage"] = "rules_clear" if is_clear else "rules_ambiguous"
        else:
            c["predicted_entity"] = None
            c["resolution_stage"] = "no_scored"

        results.append(c)

    return results


@dataclass
class Sentence:
    id: str
    text: str
    tokens: List[Token]
    verse_refs: List[str] = field(default_factory=list)

    def get_predicates(self) -> List[Token]:
        """Get all finite verbs - includes predicates AND other verbal relations (comp, adv, etc.)

        PROIEL marks various verbal functions with different relations:
        - pred: main predicate
        - comp: complement (e.g., ἵνα clauses)
        - adv: adverbial clause
        - atr: attributive
        - apos: appositive
        All can have pro-drop subjects.
        """
        return [t for t in self.tokens if t.is_finite_verb() and t.get_person() == 3]

    def get_subject(self, predicate_head: Optional[int]) -> Optional[Token]:
        """Find the subject of a predicate by looking for nsubj relation.

        Note: For the predicate's head (external head), we use the predicate's id
        (internal token ID within the sentence) to find subjects, as this works
        for both old PROIEL format (where predicate.head=None) and new format
        (where predicate.head contains an external ID).
        """
        for token in self.tokens:
            if token.head == predicate_head and token.relation in ("nsubj", "sub"):
                return token
        return None

    def get_subject_by_id(self, predicate_id: int) -> Optional[Token]:
        """Find the subject of a predicate using the predicate's internal ID."""
        for token in self.tokens:
            if token.head == predicate_id and token.relation in ("nsubj", "sub"):
                return token
        return None

    def has_null_subject(self, predicate: Token) -> bool:
        """Check if a predicate has a null (implicit) subject."""
        # Use predicate.id (internal ID) to find subject - this works for both formats
        subject = self.get_subject_by_id(predicate.id)
        person = predicate.get_person()
        return subject is None and person == 3

    def get_antecedent_for_null(
        self, predicate: Token, all_sentences: Dict[str, "Sentence"]
    ) -> Optional[Token]:
        """Find the antecedent for a null subject by following AntId chain."""
        antecedent_id = predicate.get_antecedent_id()
        if not antecedent_id:
            return None

        for sid, sent in all_sentences.items():
            for token in sent.tokens:
                if token.id == antecedent_id:
                    return token
        return None

    def get_all_person_mentions(self) -> List[Token]:
        """Get all person entities (Ne = named entity) in the sentence."""
        return [t for t in self.tokens if t.pos == "Ne"]

    def get_verbs_without_subject(self) -> List[Token]:
        """Get all finite verbs that lack an explicit subject (pro-drop candidates)."""
        candidates = []
        for token in self.tokens:
            if token.is_finite_verb() and self.has_null_subject(token):
                candidates.append(token)
        return candidates


class ProielCONLLU:
    """Parser for PROIEL CONLLU format."""

    @staticmethod
    def parse_file(
        filepath: str,
    ) -> Tuple[List[Sentence], Dict[str, Sentence], Dict[Tuple[str, int], Token]]:
        """Parse a CONLLU file and return sentences, sentence index, and token index."""
        sentences = []
        sentence_index = {}
        token_index = {}

        current_sentence = None
        current_tokens = []
        current_sent_id = None
        current_text = None
        current_verse_refs = []

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                # Handle sentence start - save previous sentence first
                if line.startswith("# sent_id"):
                    if current_sent_id and current_tokens:
                        sentence = Sentence(
                            id=current_sent_id,
                            text=current_text or "",
                            tokens=current_tokens,
                            verse_refs=current_verse_refs,
                        )
                        sentences.append(sentence)
                        sentence_index[current_sent_id] = sentence
                    current_sent_id = line.split("=", 1)[1].strip()
                    current_tokens = []
                    current_text = None
                    current_verse_refs = []
                elif line.startswith("# text"):
                    current_text = line.split("=", 1)[1].strip()
                elif line.startswith("# Ref="):
                    # Old format: Ref in token misc
                    current_verse_refs.append(line.split("=", 1)[1].strip())
                elif line.startswith("# citation ="):
                    # New format: citation in comment (note: space before =)
                    current_verse_refs.append(line.split("=", 1)[1].strip())
                elif line.startswith("#") or not line:
                    continue
                elif "\t" in line and line.split("\t")[0].isdigit():
                    if current_sent_id:
                        parts = line.split("\t")
                        if len(parts) >= 8:
                            head_str = parts[6]
                            head = None
                            if (
                                head_str
                                and head_str != "_"
                                and head_str.lower() != "nan"
                            ):
                                try:
                                    head = int(float(head_str))
                                except ValueError:
                                    head = None

                            token = Token(
                                id=int(parts[0]),
                                form=parts[1],
                                lemma=parts[2],
                                pos=parts[3],
                                feats=parts[5] if len(parts) > 5 else None,
                                head=head,
                                relation=parts[7] if len(parts) > 7 else "_",
                                deps=parts[8] if len(parts) > 8 else None,
                                misc=parts[9] if len(parts) > 9 else None,
                            )
                            current_tokens.append(token)
                            token_index[(current_sent_id, token.id)] = token

                            if token.misc and "Ref=" in token.misc:
                                import re

                                match = re.search(
                                    r"Ref=([A-Za-z]+\s*[\d.]+)", token.misc
                                )
                                if match:
                                    ref = match.group(1).strip()
                                    if ref not in current_verse_refs:
                                        current_verse_refs.append(ref)
                else:
                    if current_sent_id and current_tokens:
                        sentence = Sentence(
                            id=current_sent_id,
                            text=current_text or "",
                            tokens=current_tokens,
                            verse_refs=current_verse_refs,
                        )
                        sentences.append(sentence)
                        sentence_index[current_sent_id] = sentence

                    current_sent_id = None
                    current_tokens = []
                    current_text = None
                    current_verse_refs = []

        if current_sent_id and current_tokens:
            sentence = Sentence(
                id=current_sent_id,
                text=current_text or "",
                tokens=current_tokens,
                verse_refs=current_verse_refs,
            )
            sentences.append(sentence)
            sentence_index[current_sent_id] = sentence

        return sentences, sentence_index, token_index

    @staticmethod
    def load_gold_directory(
        directory: str,
    ) -> Tuple[List[Sentence], Dict[str, Sentence], Dict[Tuple[str, int], Token]]:
        """Load all CONLLU files from a directory, excluding the combined new chapters file."""
        all_sentences = []
        all_index = {}
        all_tokens = {}

        for filepath in Path(directory).glob("*.conllu"):
            # Skip the combined new chapters file - it gets loaded separately
            if "MATT_24_27_MARK_13_LUKE_14_21_ACTS_9" in filepath.name:
                continue
            sentences, index, tokens = ProielCONLLU.parse_file(str(filepath))
            all_sentences.extend(sentences)
            all_index.update(index)
            all_tokens.update(tokens)

        return all_sentences, all_index, all_tokens


def find_prodrop_candidates(
    sentences: List[Sentence], sentence_index: Dict[str, Sentence], window_size: int = 2
) -> List[Dict]:
    """
    Find all pro-drop candidates in the corpus.

    A pro-drop candidate is a finite verb (3rd person) without an explicit subject
    that has an antecedent in the PROIEL annotation.

    Args:
        sentences: List of Sentence objects
        sentence_index: Dictionary mapping sentence IDs to Sentences
        window_size: Number of verses to look backward for antecedent (default: 2)

    Returns list of candidate dictionaries with verb info and antecedent.
    """
    candidates = []

    for sent in sentences:
        verbs = sent.get_verbs_without_subject()

        for verb in verbs:
            antecedent = sent.get_antecedent_for_null(verb, sentence_index)

            narrative = extract_narrative_features(sent.text)

            candidate = {
                "sentence_id": sent.id,
                "verse_refs": sent.verse_refs,
                "sentence_text": sent.text,
                "verb_form": verb.form,
                "verb_lemma": verb.lemma,
                "verb_morph": verb.feats,
                "verb_person": verb.get_person(),
                "verb_token_id": verb.id,
                "has_antecedent": antecedent is not None,
                "antecedent_form": antecedent.form if antecedent else None,
                "antecedent_lemma": antecedent.lemma if antecedent else None,
                "antecedent_id": antecedent.id if antecedent else None,
                "antecedent_pos": antecedent.pos if antecedent else None,
                "window_size": window_size,
                "has_delta": narrative.get("has_delta", False),
                "has_tote": narrative.get("has_tote", False),
                "has_genitive_absolute": narrative.get("has_genitive_absolute", False),
            }
            candidates.append(candidate)

    return candidates


def load_gold_standard(gold_path: str) -> Dict:
    """Load the existing gold standard for pro-drop evaluation."""
    with open(gold_path, "r", encoding="utf-8") as f:
        return json.load(f)


def integrate_with_gold(
    candidates: List[Dict], gold_standard: Dict, sentence_index: Dict[str, Sentence]
) -> List[Dict]:
    """
    Integrate pro-drop candidates with gold standard annotations.
    Uses gold standard to validate detection and add antecedent info.
    """
    integrated = []

    gold_map = {}
    for result in gold_standard.get("gold_results", []):
        verse_ref = result.get("verse_ref")
        verb_form = result.get("verb_form")
        key = (verse_ref, verb_form)
        gold_map[key] = result

    for candidate in candidates:
        verse_refs = candidate.get("verse_refs", [])
        verb_form = candidate.get("verb_form")
        matched_gold = None

        for vr in verse_refs:
            key = (vr, verb_form)
            if key in gold_map:
                matched_gold = gold_map[key]
                candidate["matched_verse_ref"] = vr
                break

        if matched_gold:
            candidate["gold_antecedent_entity"] = matched_gold.get("antecedent_entity")
            candidate["gold_antecedent_lemma"] = matched_gold.get("antecedent_lemma")
            candidate["gold_antecedent_form"] = matched_gold.get("antecedent_form")
            candidate["difficulty_level"] = matched_gold.get("difficulty_level")
            candidate["gold_note"] = matched_gold.get("note")
        else:
            candidate["gold_antecedent_entity"] = None
            candidate["gold_antecedent_lemma"] = None
            candidate["gold_antecedent_form"] = None
            candidate["difficulty_level"] = None
            candidate["gold_note"] = None

        integrated.append(candidate)

    return integrated


def analyze_verbs_in_sentence(sent: Sentence) -> Dict:
    """Analyze a sentence to find finite verbs and their subject status.

    Applies δέ/τότε narrative marker rules to disambiguate pro-drop candidates.
    """
    result = {
        "sentence_id": sent.id,
        "verse_refs": sent.verse_refs,
        "text": sent.text,
        "predicates": [],
        "narrative_features": extract_narrative_features(sent),
    }

    for token in sent.tokens:
        if token.is_finite_verb():
            # Use internal ID to find subject (works for both old and new PROIEL format)
            subject = sent.get_subject_by_id(token.id)
            has_subj = subject is not None
            person = token.get_person()

            # Base pro-drop detection
            is_candidate = person == 3 and not has_subj

            predicate_analysis = {
                "token_id": token.id,
                "form": token.form,
                "lemma": token.lemma,
                "morph": token.feats,
                "person": person,
                "relation": token.relation,
                "has_explicit_subject": has_subj,
                "subject_form": subject.form if subject else None,
                "is_pro_drop_candidate": is_candidate,
            }

            # Apply narrative marker rules if this is a candidate
            if is_candidate:
                predicate_analysis = apply_narrative_rules(sent, predicate_analysis)

            result["predicates"].append(predicate_analysis)

    return result


def main():
    print("=" * 60)
    print("Phase 1: Dependency Parsing Pro-Drop Detection")
    print("=" * 60)
    print()

    gold_dir = "project/data/gold"
    gold_standard_path = (
        "project/data/experiments/sprint2c/proiel_gold_standard_new_chapters.json"
    )
    eval_dataset_path = (
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    )

    # Load BOTH original gold data (MARK 1-16, etc.) and new chapters (MATT 24-27, MARK 13, LUKE 14/21, ACTS 9)
    # This gives us 190 new pro-drop instances with δέ/τότε markers to test narrative rules
    print("Loading PROIEL CONLLU data from: project/data/gold")
    print("  - Loading original files (MARK 1-16, etc.)...")
    sentences_orig, index_orig, tokens_orig = ProielCONLLU.load_gold_directory(gold_dir)
    print(f"    Loaded {len(sentences_orig)} sentences, {len(tokens_orig)} tokens")

    # Also load the new chapter file
    new_chapters_file = os.path.join(
        gold_dir, "MATT_24_27_MARK_13_LUKE_14_21_ACTS_9.conllu"
    )
    if os.path.exists(new_chapters_file):
        print("  - Loading new chapters (MATT 24-27, MARK 13, LUKE 14/21, ACTS 9)...")
        sentences_new, index_new, tokens_new = ProielCONLLU.parse_file(
            new_chapters_file
        )
        # Merge - add new sentences and tokens with offset IDs to avoid collisions
        sentences = sentences_orig + sentences_new
        sentence_index = {**index_orig, **index_new}
        token_index = {**tokens_orig, **tokens_new}
        print(f"    Loaded {len(sentences_new)} sentences, {len(tokens_new)} tokens")
    else:
        sentences, sentence_index, token_index = sentences_orig, index_orig, tokens_orig

    print(f"Total: {len(sentences)} sentences, {len(token_index)} tokens")
    print()

    print("Loading gold standard...")
    with open(gold_standard_path, "r", encoding="utf-8") as f:
        gold_standard = json.load(f)
    print(f"Loaded {len(gold_standard.get('gold_results', []))} gold annotations")
    print()

    print("Detecting finite verbs and pro-drop candidates...")
    verb_analysis = []
    pro_drop_count = 0

    for sent in sentences:
        analysis = analyze_verbs_in_sentence(sent)
        verb_analysis.append(analysis)
        pro_drop_count += sum(
            1 for p in analysis["predicates"] if p["is_pro_drop_candidate"]
        )

    print(f"Found {pro_drop_count} pro-drop candidates across all sentences")
    print()

    print("Detecting pro-drop candidates (matching gold standard)...")
    candidates = find_prodrop_candidates(sentences, sentence_index, window_size=2)
    integrated = integrate_with_gold(candidates, gold_standard, sentence_index)

    print("Running resolution (rules with subject + position scoring)...")
    with_resolution = resolve_prodrop_with_clear_rules(
        sentences, integrated, sentence_index, window=2
    )

    debug_with_gold = [c for c in with_resolution if c.get("gold_antecedent_entity")][
        :10
    ]
    print("\nDebug predictions:")
    for c in debug_with_gold:
        print(f"  {c.get('matched_verse_ref')}: verb={c.get('verb_form')}")
        print(
            f"    predicted={c.get('predicted_entity')}, gold={c.get('gold_antecedent_entity')}"
        )

    evaluated = evaluate_with_head_matching(with_resolution)

    debug_examples = [c for c in with_resolution[:5] if c.get("gold_antecedent_entity")]
    if debug_examples:
        print("\nDebug - prediction samples:")
        for c in debug_examples:
            print(
                f"  {c.get('matched_verse_ref')}: verb_id={c.get('verb_token_id')}, "
                f"predicted={c.get('predicted_entity')}, gold={c.get('gold_antecedent_entity')}"
            )

    print(f"\nBaseline Results:")
    print(f"  String-matching accuracy: {evaluated['string_accuracy']:.1%}")
    print(f"  Head-matching accuracy: {evaluated['head_accuracy']:.1%}")

    print("\n" + "=" * 60)
    print("STEP 2: Ambiguity Classification")
    print("=" * 60)

    clear_count = 0
    ambiguous_count = 0
    no_antecedent = 0

    for i, c in enumerate(with_resolution):
        if c.get("gold_antecedent_entity"):
            is_clear = c.get("is_clear", False)
            if is_clear:
                clear_count += 1
            else:
                ambiguous_count += 1
        else:
            no_antecedent += 1

    total_with_gold = clear_count + ambiguous_count
    print(f"\nAmbiguity Classification:")
    print(
        f"  Clear cases: {clear_count} ({clear_count / total_with_gold * 100:.1f}% if total_with_gold else 0)"
    )
    print(
        f"  Ambiguous cases: {ambiguous_count} ({ambiguous_count / total_with_gold * 100:.1f}% if total_with_gold else 0)"
    )
    print(f"  No gold antecedent: {no_antecedent}")
    print()

    if total_with_gold > 0:
        print(f"Stage breakdown:")
        stages = {}
        for c in with_resolution:
            stage = c.get("resolution_stage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
        for stage, count in stages.items():
            print(f"  {stage}: {count}")
    print()

    with_entity = [c for c in integrated if c.get("gold_antecedent_entity")]
    without_entity = [c for c in integrated if not c.get("gold_antecedent_entity")]

    print(f"  - With person antecedent: {len(with_entity)}")
    print(f"  - Without person antecedent: {len(without_entity)}")
    print()

    entity_stats = defaultdict(int)
    for c in with_entity:
        entity = c.get("gold_antecedent_entity")
        if entity:
            entity_stats[entity] += 1

    print("Person entity distribution:")
    for entity, count in sorted(entity_stats.items(), key=lambda x: -x[1]):
        print(f"  {entity}: {count}")
    print()

    print("Sample pro-drop candidates with gold entities:")
    for c in with_entity[:15]:
        ref = c.get("matched_verse_ref", "Unknown")
        print(f"  {ref}: {c['verb_form']} → {c['gold_antecedent_entity']}")

    output_path = "project/data/experiments/sprint3a/prodrop_candidates.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "source": "PROIEL CONLLU + Gold Standard",
                    "total_sentences": len(sentences),
                    "total_tokens": len(token_index),
                    "total_pro_drop_candidates": len(integrated),
                    "with_person_antecedent": len(with_entity),
                    "without_person_antecedent": len(without_entity),
                },
                "verb_analysis": verb_analysis,
                "candidates": integrated,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Saved to: {output_path}")
    print()

    summary = {
        "phase": "1_dependency_parsing",
        "total_sentences": len(sentences),
        "total_pro_drop": len(integrated),
        "with_antecedent": len(with_entity),
        "accuracy_baseline": len(with_entity) / len(integrated) if integrated else 0,
    }

    with open("project/data/experiments/sprint3a/phase1_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("=" * 60)
    print("Phase 1 Complete")
    print(
        f"Baseline: {summary['accuracy_baseline']:.1%} if we use simple last-person rule"
    )
    print("=" * 60)


def evaluate_with_head_matching(candidates: List[Dict]) -> Dict:
    """
    Evaluate candidates using HEAD-MATCHING (CRAC standard).

    This replaces string-matching with canonical entity comparison,
    handling Greek case inflection (Ἰησοῦς vs Ἰησοῦν vs τῷ Ἰησοῦ).
    """
    results = {
        "total": len(candidates),
        "with_gold": 0,
        "correct_string_matching": 0,
        "correct_head_matching": 0,
        "details": [],
    }

    for c in candidates:
        gold_entity = c.get("gold_antecedent_entity")
        predicted_entity = c.get("predicted_entity")

        if gold_entity:
            results["with_gold"] += 1

            is_string_match = predicted_entity and gold_entity == predicted_entity
            is_head_match = compare_head_matching(predicted_entity or "", gold_entity)

            if is_string_match:
                results["correct_string_matching"] += 1
            if is_head_match:
                results["correct_head_matching"] += 1

            results["details"].append(
                {
                    "verse": c.get("matched_verse_ref"),
                    "verb": c.get("verb_form"),
                    "gold": gold_entity,
                    "predicted": predicted_entity,
                    "string_match": is_string_match,
                    "head_match": is_head_match,
                }
            )

    results["string_accuracy"] = (
        results["correct_string_matching"] / results["with_gold"]
        if results["with_gold"] > 0
        else 0
    )
    results["head_accuracy"] = (
        results["correct_head_matching"] / results["with_gold"]
        if results["with_gold"] > 0
        else 0
    )

    return results


if __name__ == "__main__":
    main()
