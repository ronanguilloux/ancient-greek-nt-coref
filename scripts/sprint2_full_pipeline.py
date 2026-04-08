import stanza
import pandas as pd
import sys
from collections import defaultdict
from transformers import pipeline, AutoTokenizer, AutoModelForMaskedLM

print("Loading Lexicons & Models...")
pronouns_df = pd.read_csv("project/lexicons/pronouns.tsv", sep="\t")
PRONOUN_LEMMAS = set(pronouns_df["lemma"].dropna())
aliases_df = pd.read_csv("project/lexicons/character_aliases.tsv", sep="\t")
ALIAS_MAP = dict(zip(aliases_df["lemma"], aliases_df["canonical_id"]))
# Stanza lemma quirk
ALIAS_MAP["Ἰησός"] = "IESOUS"

nlp = stanza.Pipeline("grc", processors="tokenize,pos,lemma,depparse", verbose=False)
ner_pipeline = pipeline(
    "ner", model="UGARIT/grc-ner-xlmr", aggregation_strategy="first"
)

# --- Load Pro-Drop Hybrid Resolver ---
sys.path.insert(0, "scripts")
from prodrop_hybrid_resolver import ProDropHybridResolver

print("Loading Pro-Drop Hybrid Resolver...")
try:
    prodrop_resolver = ProDropHybridResolver(use_llm=False)  # Start with rules-only
    print(f"  Pro-Drop resolver loaded (LLM: {prodrop_resolver.use_llm})")
except Exception as e:
    print(f"  Warning: Could not load pro-drop resolver: {e}")
    prodrop_resolver = None


def resolve_character(lemma):
    if lemma in ALIAS_MAP:
        return ALIAS_MAP[lemma]
    return lemma.upper()


def parse_feats(feat_str):
    if not feat_str or feat_str == "None":
        return {}
    return {f.split("=")[0]: f.split("=")[1] for f in feat_str.split("|")}


def run_pipeline(text):
    print(f"\n{'=' * 50}\nTEXT: {text}\n{'=' * 50}")

    doc = nlp(text)
    ner_results = ner_pipeline(text)
    named_entities = [
        ent["word"].strip().replace(" ", "")
        for ent in ner_results
        if ent["entity_group"] == "PER"
    ]

    mentions = []
    global_id = 0

    for sentence in doc.sentences:
        for word in sentence.words:
            global_id += 1
            feats = parse_feats(word.feats)

            # Temporary Stanza mock fix
            if word.text == "Ἰησοῦς":
                feats.update({"Gender": "Masc", "Case": "Nom"})
                word.deprel = "nsubj"

            m_type = None
            if word.text in named_entities or word.upos == "PROPN":
                m_type = "NAMED"
            elif word.lemma in PRONOUN_LEMMAS:
                m_type = "PRONOUN"
            elif word.upos == "NOUN":
                # Check if it has a definite article (DEF_NP)
                has_det = any(
                    w.head == word.id and w.lemma in ["ὁ", "ἡ", "τό"]
                    for w in sentence.words
                )
                if has_det:
                    m_type = "DEF_NP"
            elif word.upos == "VERB":
                has_nsubj = any(
                    w.head == word.id and w.deprel == "nsubj" for w in sentence.words
                )
                if not has_nsubj:
                    m_type = "PRO_DROP"

            if m_type:
                mentions.append(
                    {
                        "id": global_id,
                        "type": m_type,
                        "text": word.text,
                        "lemma": word.lemma,
                        "gender": feats.get("Gender"),
                        "number": feats.get("Number"),
                        "case": feats.get("Case"),
                        "deprel": word.deprel,
                        "sentence_id": sentence.index,
                        "cluster": None,
                    }
                )

    # --- C2: Clustering (NAMED & DEF_NP Entities) ---
    registry = defaultdict(list)
    for m in mentions:
        if m["type"] in ["NAMED", "DEF_NP"]:
            m["cluster"] = resolve_character(m["lemma"])
            registry[m["cluster"]].append(m["id"])

    # --- C3a: Pronoun Resolution ---
    for i, mention in enumerate(mentions):
        if mention["type"] == "PRONOUN":
            candidates = []
            for j in range(i - 1, -1, -1):
                cand = mentions[j]
                if cand["type"] in ["NAMED", "DEF_NP"]:
                    # Morphology match
                    if (
                        cand["gender"] == mention["gender"]
                        and cand["number"] == mention["number"]
                    ):
                        score = 0.0
                        if (
                            cand["sentence_id"] == mention["sentence_id"] - 1
                            and cand["deprel"] == "nsubj"
                        ):
                            score += 3.0
                        if (
                            cand["sentence_id"] == mention["sentence_id"]
                            and cand["deprel"] == "nsubj"
                        ):
                            score += 2.0
                        score += 1.0 / (mention["id"] - cand["id"])
                        candidates.append((score, cand))

            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_cand = candidates[0][1]
                mention["cluster"] = best_cand["cluster"]
                registry[mention["cluster"]].append(mention["id"])

    # --- C3b: Pro-Drop Resolution (Hybrid) ---
    if prodrop_resolver:
        named_entities_in_window = [
            {"form": m["text"], "lemma": m["lemma"]}
            for m in mentions
            if m["type"] in ["NAMED", "DEF_NP"]
        ]

        for mention in mentions:
            if mention["type"] == "PRO_DROP" and not mention["cluster"]:
                from prodrop_hybrid_resolver import ProDropInstance

                inst = ProDropInstance(
                    verse_ref="INLINE",
                    sentence_text=text,
                    context_5verses=text,
                    verb_form=mention["text"],
                    verb_lemma=mention["lemma"],
                    person=3,
                    number=mention.get("number", "singular") or "singular",
                    entities=named_entities_in_window,
                    narrative_markers={
                        "delta_adversative": False,
                        "tote_shift": False,
                        "genitive_absolute": False,
                    },
                )

                result = prodrop_resolver.resolve(inst)
                if result.entity:
                    mention["cluster"] = result.entity
                    registry[result.entity].append(mention["id"])

    # --- Final Output ---
    print(f"\n{'=' * 50}")
    print("ENTITY CHAINS:")
    for cluster_id, member_ids in registry.items():
        print(f"  {cluster_id}: {len(member_ids)} mentions")

    print(f"\n{'=' * 50}")
    print("MENTION RESOLUTION:")
    for m in mentions:
        cluster_str = f" -> {m['cluster']}" if m["cluster"] else " -> UNRESOLVED"
        print(
            f"  {m['type']:<10} | {m['text']:<10} (lemma: {m['lemma']:<10}){cluster_str}"
        )


if __name__ == "__main__":
    run_pipeline("ἀπεκρίθη Ἰησοῦς καὶ εἶπεν τῇ γυναικί. αὐτὴ δὲ λέγει αὐτῷ.")
