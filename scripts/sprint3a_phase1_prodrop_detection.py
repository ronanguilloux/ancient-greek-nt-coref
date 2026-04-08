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
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
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
        return True

    def get_person(self) -> Optional[int]:
        """Extract person from morphological features."""
        if not self.feats:
            return None
        match = re.search(r"(\d)[spd]", self.feats)
        return int(match.group(1)) if match else None


@dataclass
class Sentence:
    id: str
    text: str
    tokens: List[Token]
    verse_ref: Optional[str] = None

    def get_predicates(self) -> List[Token]:
        """Get all finite verbs with 'pred' relation (predicates)."""
        return [t for t in self.tokens if t.is_finite_verb() and t.relation == "pred"]

    def get_subject(self, predicate_head: Optional[int]) -> Optional[Token]:
        """Find the subject of a predicate by looking for nsubj relation."""
        for token in self.tokens:
            if token.head == predicate_head and token.relation == "nsubj":
                return token
        return None

    def has_null_subject(self, predicate: Token) -> bool:
        """Check if a predicate has a null (implicit) subject."""
        subject = self.get_subject(predicate.head)
        return subject is None and predicate.get_person() == 3

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
    ) -> Tuple[List[Sentence], Dict[str, Sentence], Dict[int, Token]]:
        """Parse a CONLLU file and return sentences, sentence index, and token index."""
        sentences = []
        sentence_index = {}
        token_index = {}

        current_sentence = None
        current_tokens = []
        current_sent_id = None
        current_text = None
        current_verse_ref = None

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")

                if line.startswith("# sent_id"):
                    current_sent_id = line.split("=", 1)[1].strip()
                elif line.startswith("# text"):
                    current_text = line.split("=", 1)[1].strip()
                elif line.startswith("# Ref="):
                    current_verse_ref = line.split("=", 1)[1].strip()
                elif line.startswith("#") or not line:
                    continue
                elif line.startswith("1\t") or (current_tokens and line[0].isdigit()):
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
                            token_index[token.id] = token
                else:
                    if current_sent_id and current_tokens:
                        sentence = Sentence(
                            id=current_sent_id,
                            text=current_text or "",
                            tokens=current_tokens,
                            verse_ref=current_verse_ref,
                        )
                        sentences.append(sentence)
                        sentence_index[current_sent_id] = sentence

                    current_sent_id = None
                    current_tokens = []
                    current_text = None
                    current_verse_ref = None

        if current_sent_id and current_tokens:
            sentence = Sentence(
                id=current_sent_id,
                text=current_text or "",
                tokens=current_tokens,
                verse_ref=current_verse_ref,
            )
            sentences.append(sentence)
            sentence_index[current_sent_id] = sentence

        return sentences, sentence_index, token_index

    @staticmethod
    def load_gold_directory(
        directory: str,
    ) -> Tuple[List[Sentence], Dict[str, Sentence], Dict[int, Token]]:
        """Load all CONLLU files from a directory."""
        all_sentences = []
        all_index = {}
        all_tokens = {}

        for filepath in Path(directory).glob("*.conllu"):
            sentences, index, tokens = ProielCONLLU.parse_file(str(filepath))
            all_sentences.extend(sentences)
            all_index.update(index)
            all_tokens.update(tokens)

        return all_sentences, all_index, all_tokens


def find_prodrop_candidates(
    sentences: List[Sentence], sentence_index: Dict[str, Sentence]
) -> List[Dict]:
    """
    Find all pro-drop candidates in the corpus.

    A pro-drop candidate is a finite verb (3rd person) without an explicit subject
    that has an antecedent in the PROIEL annotation.

    Returns list of candidate dictionaries with verb info and antecedent.
    """
    candidates = []

    for sent in sentences:
        verbs = sent.get_verbs_without_subject()

        for verb in verbs:
            antecedent = sent.get_antecedent_for_null(verb, sentence_index)

            candidate = {
                "sentence_id": sent.id,
                "verse_ref": sent.verse_ref,
                "sentence_text": sent.text,
                "verb_form": verb.form,
                "verb_lemma": verb.lemma,
                "verb_morph": verb.feats,
                "verb_person": verb.get_person(),
                "has_antecedent": antecedent is not None,
                "antecedent_form": antecedent.form if antecedent else None,
                "antecedent_lemma": antecedent.lemma if antecedent else None,
                "antecedent_pos": antecedent.pos if antecedent else None,
                "antecedent_id": antecedent.id if antecedent else None,
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
        key = (candidate.get("verse_ref"), candidate.get("verb_form"))
        gold = gold_map.get(key, {})

        candidate["gold_antecedent_entity"] = gold.get("antecedent_entity")
        candidate["gold_antecedent_lemma"] = gold.get("antecedent_lemma")
        candidate["gold_antecedent_form"] = gold.get("antecedent_form")
        candidate["difficulty_level"] = gold.get("difficulty_level")
        candidate["gold_note"] = gold.get("note")

        integrated.append(candidate)

    return integrated


def analyze_verbs_in_sentence(sent: Sentence) -> Dict:
    """Analyze a sentence to find finite verbs and their subject status."""
    result = {
        "sentence_id": sent.id,
        "verse_ref": sent.verse_ref,
        "text": sent.text,
        "predicates": [],
    }

    for token in sent.tokens:
        if token.is_finite_verb():
            subject = sent.get_subject(token.head)
            has_subj = subject is not None
            person = token.get_person()

            result["predicates"].append(
                {
                    "token_id": token.id,
                    "form": token.form,
                    "lemma": token.lemma,
                    "morph": token.feats,
                    "person": person,
                    "has_explicit_subject": has_subj,
                    "subject_form": subject.form if subject else None,
                    "is_pro_drop_candidate": person == 3 and not has_subj,
                }
            )

    return result


def main():
    print("=" * 60)
    print("Phase 1: Dependency Parsing Pro-Drop Detection")
    print("=" * 60)
    print()

    gold_dir = "project/data/gold"
    gold_standard_path = "project/data/experiments/sprint2c/proiel_gold_standard.json"
    eval_dataset_path = (
        "project/data/experiments/sprint2c/prodrop_evaluation_dataset.json"
    )

    print(f"Loading PROIEL CONLLU data from: {gold_dir}")
    sentences, sentence_index, token_index = ProielCONLLU.load_gold_directory(gold_dir)
    print(f"Loaded {len(sentences)} sentences, {len(token_index)} tokens")
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
    candidates = find_prodrop_candidates(sentences, sentence_index)
    integrated = integrate_with_gold(candidates, gold_standard, sentence_index)

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

    print("Sample pro-drop candidates with gold entities (Mark 1):")
    for c in with_entity[:15]:
        print(f"  {c['verse_ref']}: {c['verb_form']} → {c['gold_antecedent_entity']}")

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


if __name__ == "__main__":
    main()
