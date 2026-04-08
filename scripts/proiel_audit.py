#!/usr/bin/env python3
"""
proiel_audit.py
Audit de couverture coréférentielle du treebank PROIEL NT grec.

Usage:
    python proiel_audit.py <path/to/greek-nt.xml> [--out <output_dir>]

Sorties:
    proiel_coverage_report.csv    — métriques M1–M5 par livre NT
    proiel_character_coverage.csv — métrique M6 par personnage (livres prioritaires)
    proiel_audit_decision.md      — rapport de décision (train / eval / exclus)
"""

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date

from lxml import etree
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Seuils de sélection (cf. §"Critères de sélection" du plan)
THRESHOLDS = {
    "M1_min": 0.05,  # taux d'annotation brut minimal
    "M1_ideal": 0.10,
    "M2_min": 100,  # nombre de chaînes minimal
    "M2_ideal": 300,
    "M3_min": 3.0,  # longueur moyenne de chaîne minimale
    "M3_ideal": 5.0,
    "M4_min": 0.40,  # couverture des pronoms minimale
    "M4_ideal": 0.60,
    "M6_min": 0.50,  # couverture du personnage principal minimal
    "M6_ideal": 0.70,
}

# Personnages cibles par livre (lemmes tels qu'ils apparaissent dans PROIEL)
# Note : PROIEL peut normaliser différemment certains lemmes — à vérifier à l'étape A
TARGETS = {
    "John": ["Ἰησοῦς", "Πέτρος", "Ἰωάν(ν)ης", "Μαρία", "Θωμᾶς", "Πιλᾶτος"],
    "Mark": ["Ἰησοῦς", "Πέτρος", "Ἰάκωβος", "Ἰωάν(ν)ης"],
    "Acts": ["Πέτρος", "Παῦλος", "Βαρναβᾶς", "Ἰάκωβος", "Στέφανος"],
}

# POS codes PROIEL pour les catégories qui nous intéressent
POS_PRONOUNS = {"Pp", "Pd", "Pr", "Pi"}  # personnel, démonstratif, relatif, indéfini
POS_VERBS = {"V-"}  # tous les verbes (préfixe)
REL_SUBJECT = "sub"  # relation syntaxique sujet


# ─────────────────────────────────────────────────────────────────────────────
# 2. ÉTAPE A — PARSING DU XML PROIEL
# ─────────────────────────────────────────────────────────────────────────────


def parse_proiel_xml(xml_path: str) -> pd.DataFrame:
    """
    Parse greek-nt.xml et retourne un DataFrame avec une ligne par token.

    Colonnes produites :
        book, sentence_id, token_id, head_id, form, lemma,
        pos, relation, antecedent_id, info_status, morphology
    """
    print(f"[A] Parsing {xml_path} …", flush=True)
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # PROIEL XML : <proiel> > <source title="…"> > <div> > <sentence> > <token>
    rows = []
    for source in root.iter("source"):
        for div in source.iter("div"):
            title_elem = div.find("title")
            if title_elem is not None and title_elem.text:
                text = title_elem.text.strip()
                parts = text.split()
                if len(parts) > 1 and parts[-1].isdigit():
                    book = " ".join(parts[:-1])
                else:
                    book = text
            else:
                book = "unknown"

            for sentence in div.iter("sentence"):
                sid = sentence.get("id")
                for token in sentence.iter("token"):
                    # Les tokens "vides" (pro-drop explicites) ont un form="*"
                    rows.append(
                        {
                            "book": book,
                            "sentence_id": sid,
                            "token_id": token.get("id"),
                            "head_id": token.get("head-id"),  # antécédent syntaxique
                            "form": token.get("form", ""),
                            "lemma": token.get("lemma", ""),
                            "pos": token.get("part-of-speech", ""),
                            "relation": token.get("relation", ""),
                            "antecedent_id": token.get(
                                "antecedent-id"
                            ),  # None si absent
                            "info_status": token.get("information-status", ""),
                            "morphology": token.get("morphology", ""),
                        }
                    )

    df = pd.DataFrame(rows)

    # Vérification de base
    n_books = df["book"].nunique()
    print(f"    → {len(df):,} tokens, {n_books} livres détectés")
    if n_books < 27:
        print(f"    ⚠️  Seulement {n_books} livres — vérifier le fichier XML source")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. ÉTAPE B — RECONSTRUCTION DES CHAÎNES (UNION-FIND) ET MÉTRIQUES M1–M5
# ─────────────────────────────────────────────────────────────────────────────


class UnionFind:
    """Structure union-find pour reconstruire les chaînes de coréférence."""

    def __init__(self):
        self._parent: dict = {}

    def find(self, x):
        self._parent.setdefault(x, x)
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])  # compression de chemin
        return self._parent[x]

    def union(self, a, b):
        self._parent[self.find(a)] = self.find(b)

    def clusters(self, members: list) -> dict:
        """Retourne {root_id: [token_ids]} pour les membres donnés."""
        result = defaultdict(list)
        for m in members:
            result[self.find(m)].append(m)
        return dict(result)


def build_chains(df_book: pd.DataFrame) -> dict:
    """
    Reconstruit les chaînes de coréférence pour un livre donné.
    Retourne {root_id: [token_ids]} — seules les chaînes de longueur ≥ 2.
    """
    uf = UnionFind()
    # Un lien antécédent→anaphorique unit deux tokens dans la même chaîne
    linked = df_book[df_book["antecedent_id"].notna()]
    for _, row in linked.iterrows():
        uf.union(row["token_id"], row["antecedent_id"])

    # Collecter tous les tokens impliqués dans au moins un lien
    involved = set(linked["token_id"]) | set(linked["antecedent_id"].dropna())
    raw_clusters = uf.clusters(list(involved))

    # Ne garder que les chaînes de longueur ≥ 2
    return {k: v for k, v in raw_clusters.items() if len(v) >= 2}


def is_verb(pos: str) -> bool:
    return pos.startswith("V")


def is_pronoun(pos: str) -> bool:
    return pos[:2] in POS_PRONOUNS


def detect_prodrop_sentences(df_book: pd.DataFrame) -> int:
    """
    Approximation du nombre de phrases avec sujet implicite (pro-drop) :
    phrases où le verbe principal (relation != 'sub') n'a aucun token
    avec relation='sub' qui lui soit syntaxiquement rattaché.

    Retourne le nombre de phrases pro-drop détectées.
    """
    prodrop_count = 0
    for sid, sent in df_book.groupby("sentence_id"):
        # Tokens qui sont sujets syntaxiques dans cette phrase
        subjects = set(sent[sent["relation"] == REL_SUBJECT]["head_id"].dropna())
        # Verbes finis dans cette phrase (heuristique : pos commence par V,
        # morphologie position 4 = tense ≠ infinitif/participe)
        # On approche : verbe non-participe = morphologie[1] != 'p' (participe) et != 'n' (infinitif)
        finite_verbs = sent[
            sent["pos"].apply(is_verb)
            & sent["morphology"].apply(lambda m: len(m) > 1 and m[1] not in ("p", "n"))
        ]
        for _, vrow in finite_verbs.iterrows():
            if vrow["token_id"] not in subjects:
                prodrop_count += 1
                break  # compter une fois par phrase
    return prodrop_count


def compute_metrics_per_book(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les métriques M1–M5 pour chaque livre du NT.
    Retourne un DataFrame trié par M1 décroissant.
    """
    print("[B] Calcul des métriques M1–M5 par livre …", flush=True)
    records = []

    for book, df_book in df.groupby("book"):
        total = len(df_book)
        annotated = df_book["antecedent_id"].notna().sum()  # tokens avec antécédent
        chains = build_chains(df_book)
        chain_lens = [len(v) for v in chains.values()]

        # Pronoms (mentions explicites anaphoriques)
        pronouns = df_book[df_book["pos"].apply(is_pronoun)]
        pron_total = len(pronouns)
        pron_annot = pronouns["antecedent_id"].notna().sum()

        # Pro-drop (approximation)
        prodrop_sent = detect_prodrop_sentences(df_book)
        total_sent = df_book["sentence_id"].nunique()

        records.append(
            {
                "book": book,
                "total_tokens": total,
                "total_sentences": total_sent,
                "M1_coref_rate": round(annotated / total, 4) if total else 0,
                "M2_chain_count": len(chains),
                "M3_avg_chain_len": round(sum(chain_lens) / len(chain_lens), 2)
                if chain_lens
                else 0,
                "M3_max_chain_len": max(chain_lens) if chain_lens else 0,
                "M4_pronoun_total": pron_total,
                "M4_pronoun_annotated": int(pron_annot),
                "M4_pronoun_coverage": round(pron_annot / pron_total, 4)
                if pron_total
                else 0,
                "M5_prodrop_sentences": prodrop_sent,
                "M5_prodrop_rate": round(prodrop_sent / total_sent, 4)
                if total_sent
                else 0,
            }
        )
        print(
            f"    {book:20s}  tokens={total:5d}  M1={records[-1]['M1_coref_rate']:.3f}"
            f"  chains={len(chains):3d}  M3={records[-1]['M3_avg_chain_len']:.1f}"
            f"  M4={records[-1]['M4_pronoun_coverage']:.2f}"
        )

    result = pd.DataFrame(records).sort_values("M1_coref_rate", ascending=False)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. ÉTAPE C — MÉTRIQUE M6 : COUVERTURE DES PERSONNAGES CIBLES
# ─────────────────────────────────────────────────────────────────────────────


def compute_character_coverage(df: pd.DataFrame, targets: dict) -> pd.DataFrame:
    """
    Pour chaque personnage cible dans les livres prioritaires,
    calcule la couverture M6 :
        - mentions_total     : occurrences du lemme dans le livre
        - as_anaphor         : fois où le token a un antecedent_id
        - as_antecedent      : fois où ce token est référencé par un autre
        - in_chain           : as_anaphor + as_antecedent (union, sans doublon)
        - M6_coverage        : in_chain / mentions_total
    """
    print("[C] Calcul de la couverture personnages (M6) …", flush=True)
    records = []

    for book, chars in targets.items():
        df_book = df[df["book"] == book]
        if df_book.empty:
            print(
                f"    ⚠️  Livre '{book}' introuvable dans le DataFrame — vérifier le titre exact"
            )
            continue

        # Ensemble des tokens qui sont des antécédents (référencés par d'autres)
        antecedent_ids = set(df_book["antecedent_id"].dropna())

        for lemma in chars:
            mentions = df_book[df_book["lemma"] == lemma]
            total = len(mentions)
            if total == 0:
                print(
                    f"    ⚠️  Lemme '{lemma}' absent dans {book} — vérifier la normalisation"
                )
                records.append(
                    {
                        "book": book,
                        "lemma": lemma,
                        "mentions_total": 0,
                        "as_anaphor": 0,
                        "as_antecedent": 0,
                        "in_chain": 0,
                        "M6_coverage": 0.0,
                        "status": "ABSENT",
                    }
                )
                continue

            as_anaphor = int(mentions["antecedent_id"].notna().sum())
            as_antecedent = int(mentions["token_id"].isin(antecedent_ids).sum())
            in_chain_ids = set(
                mentions[mentions["antecedent_id"].notna()]["token_id"]
            ) | set(mentions[mentions["token_id"].isin(antecedent_ids)]["token_id"])
            in_chain = len(in_chain_ids)
            m6_coverage = round(in_chain / total, 4)

            records.append(
                {
                    "book": book,
                    "lemma": lemma,
                    "mentions_total": total,
                    "as_anaphor": as_anaphor,
                    "as_antecedent": as_antecedent,
                    "in_chain": in_chain,
                    "M6_coverage": m6_coverage,
                    "status": _m6_status(m6_coverage),
                }
            )
            print(
                f"    {book:6s}  {lemma:15s}  total={total:4d}  "
                f"anaphor={as_anaphor:3d}  antec={as_antecedent:3d}  "
                f"M6={m6_coverage:.2f}  {records[-1]['status']}"
            )

    return pd.DataFrame(records)


def _m6_status(m6: float) -> str:
    if m6 >= THRESHOLDS["M6_ideal"]:
        return "✅ IDEAL"
    if m6 >= THRESHOLDS["M6_min"]:
        return "⚠️  MINIMAL"
    return "❌ INSUFFISANT"


# ─────────────────────────────────────────────────────────────────────────────
# 5. APPLICATION DES SEUILS ET DÉCISION PAR LIVRE
# ─────────────────────────────────────────────────────────────────────────────


def apply_thresholds(metrics_df: pd.DataFrame, char_df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les colonnes 'meets_min', 'meets_ideal', 'role' à metrics_df.
    'role' ∈ {"TRAIN_IDEAL", "TRAIN_MIN", "EXCLUDED", "PRIORITY_EVAL"}
    """
    # Personnage principal par livre prioritaire (premier de la liste TARGETS)
    main_char = {book: chars[0] for book, chars in TARGETS.items()}

    def classify(row):
        m1 = row["M1_coref_rate"]
        m2 = row["M2_chain_count"]
        m3 = row["M3_avg_chain_len"]
        m4 = row["M4_pronoun_coverage"]
        book = row["book"]

        meets_min = (
            m1 >= THRESHOLDS["M1_min"]
            and m2 >= THRESHOLDS["M2_min"]
            and m3 >= THRESHOLDS["M3_min"]
            and m4 >= THRESHOLDS["M4_min"]
        )
        meets_ideal = (
            m1 >= THRESHOLDS["M1_ideal"]
            and m2 >= THRESHOLDS["M2_ideal"]
            and m3 >= THRESHOLDS["M3_ideal"]
            and m4 >= THRESHOLDS["M4_ideal"]
        )

        # Vérifier M6 si livre prioritaire
        m6_ok = True
        if book in main_char and not char_df.empty:
            row_m6 = char_df[
                (char_df["book"] == book) & (char_df["lemma"] == main_char[book])
            ]
            if not row_m6.empty:
                m6_ok = float(row_m6.iloc[0]["M6_coverage"]) >= THRESHOLDS["M6_min"]

        if not meets_min or not m6_ok:
            role = "EXCLUDED"
        elif meets_ideal:
            role = "TRAIN_IDEAL" if book not in TARGETS else "PRIORITY_EVAL"
        else:
            role = "TRAIN_MIN"

        return pd.Series(
            {"meets_min": meets_min, "meets_ideal": meets_ideal, "role": role}
        )

    thresholds_applied = metrics_df.apply(classify, axis=1)
    return pd.concat([metrics_df, thresholds_applied], axis=1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. EXPORT CSV
# ─────────────────────────────────────────────────────────────────────────────


def export_csvs(metrics_df: pd.DataFrame, char_df: pd.DataFrame, out_dir: str):
    """Exporte les deux CSV en UTF-8."""
    os.makedirs(out_dir, exist_ok=True)

    cov_path = os.path.join(out_dir, "proiel_coverage_report.csv")
    char_path = os.path.join(out_dir, "proiel_character_coverage.csv")

    metrics_df.to_csv(cov_path, index=False, encoding="utf-8-sig")
    char_df.to_csv(char_path, index=False, encoding="utf-8-sig")

    print(f"\n[D] Exports CSV :")
    print(f"    → {cov_path}")
    print(f"    → {char_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 7. GÉNÉRATION DU RAPPORT DE DÉCISION MARKDOWN
# ─────────────────────────────────────────────────────────────────────────────


def generate_decision_report(
    metrics_df: pd.DataFrame, char_df: pd.DataFrame, out_dir: str
):
    """
    Génère proiel_audit_decision.md avec :
      - Tableau récapitulatif de toutes les métriques
      - Section par rôle (PRIORITY_EVAL / TRAIN_IDEAL / TRAIN_MIN / EXCLUDED)
      - Recommandation finale
      - Alerte si augmentation manuelle nécessaire
    """
    lines = []
    lines += [
        "# Rapport d'audit PROIEL NT — Couverture coréférentielle",
        f"_Généré le {date.today().isoformat()}_",
        "",
        "---",
        "",
        "## Résumé des métriques par livre",
        "",
    ]

    # Tableau métriques
    display_cols = [
        "book",
        "total_tokens",
        "M1_coref_rate",
        "M2_chain_count",
        "M3_avg_chain_len",
        "M4_pronoun_coverage",
        "M5_prodrop_rate",
        "role",
    ]
    lines.append(metrics_df[display_cols].to_markdown(index=False))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections par rôle
    roles_labels = {
        "PRIORITY_EVAL": (
            "📗 Livres prioritaires — Corpus d'évaluation (gold)",
            "Ces livres atteignent les seuils idéaux ET font partie des livres "
            "prioritaires (Jean, Marc, Actes). Ils serviront de **test set** "
            "pour l'évaluation de la pipeline de coréférence.",
        ),
        "TRAIN_IDEAL": (
            "📘 Livres entraînement — Couverture idéale",
            "Ces livres atteignent tous les seuils idéaux. "
            "Ils constitueront le **corpus d'entraînement principal**.",
        ),
        "TRAIN_MIN": (
            "📙 Livres entraînement — Couverture minimale",
            "Ces livres atteignent les seuils minimaux mais pas idéaux. "
            "Ils peuvent compléter le corpus d'entraînement "
            "mais ne doivent **pas** servir d'évaluation.",
        ),
        "EXCLUDED": (
            "📕 Livres exclus — Couverture insuffisante",
            "Ces livres n'atteignent pas les seuils minimaux. "
            "Ils sont **exclus** du corpus pour l'instant. "
            "Si un livre prioritaire est exclu, voir la section "
            "'Stratégie d'augmentation manuelle' ci-dessous.",
        ),
    }

    for role, (title, explanation) in roles_labels.items():
        subset = metrics_df[metrics_df["role"] == role]
        lines.append(f"## {title}")
        lines.append("")
        lines.append(explanation)
        lines.append("")
        if subset.empty:
            lines.append("_Aucun livre dans cette catégorie._")
        else:
            for _, row in subset.iterrows():
                lines.append(
                    f"- **{row['book']}** "
                    f"({row['total_tokens']:,} tokens, "
                    f"M1={row['M1_coref_rate']:.3f}, "
                    f"M2={int(row['M2_chain_count'])} chaînes, "
                    f"M3={row['M3_avg_chain_len']:.1f}, "
                    f"M4={row['M4_pronoun_coverage']:.2f})"
                )
        lines.append("")
        lines.append("---")
        lines.append("")

    # Section M6 — personnages cibles
    lines += [
        "## Couverture des personnages principaux (M6)",
        "",
        char_df.to_markdown(index=False),
        "",
        "---",
        "",
    ]

    # Alerte augmentation manuelle si livre prioritaire exclu
    priority_books = set(TARGETS.keys())
    excluded_books = set(metrics_df[metrics_df["role"] == "EXCLUDED"]["book"])
    priority_exclu = priority_books & excluded_books

    lines.append("## Recommandation finale")
    lines.append("")

    if priority_exclu:
        lines.append(
            f"⚠️ **Attention** : les livres prioritaires suivants "
            f"n'atteignent pas les seuils minimaux : "
            f"{', '.join(sorted(priority_exclu))}."
        )
        lines.append("")
        lines.append("**Stratégie d'augmentation manuelle recommandée :**")
        lines.append("")
        for book in sorted(priority_exclu):
            lines.append(
                f"- **{book}** : annoter manuellement les chaînes de coréférence "
                f"sur les 5 premières péricopes (environ 100 versets) "
                f"en format CoNLL-U, en priorité les pronoms anaphoriques "
                f"et les sujets nuls des verbes finis."
            )
        lines.append("")
    else:
        lines.append(
            "✅ Tous les livres prioritaires (Jean, Marc, Actes) atteignent "
            "au moins les seuils minimaux."
        )
        lines.append("")

    # Récapitulatif final
    train_books = metrics_df[
        metrics_df["role"].isin(["TRAIN_IDEAL", "TRAIN_MIN", "PRIORITY_EVAL"])
    ]["book"].tolist()
    eval_books = metrics_df[metrics_df["role"] == "PRIORITY_EVAL"]["book"].tolist()

    lines += [
        "### Décision :",
        "",
        f"- **Corpus d'entraînement** ({len(train_books)} livres) : "
        + ", ".join(train_books),
        f"- **Corpus d'évaluation / gold** ({len(eval_books)} livres) : "
        + ", ".join(eval_books)
        if eval_books
        else "- **Corpus d'évaluation** : à compléter par annotation manuelle",
        f"- **Livres exclus** ({len(excluded_books)} livres) : "
        + ", ".join(sorted(excluded_books))
        if excluded_books
        else "- **Livres exclus** : aucun",
        "",
        "_Ce rapport a été généré automatiquement par `proiel_audit.py`. "
        "Toute décision finale doit être validée par inspection manuelle "
        "d'un échantillon de chaînes dans les livres retenus._",
    ]

    # Écriture du fichier
    report_path = os.path.join(out_dir, "proiel_audit_decision.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"    → {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. MAIN
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Audit coréférence PROIEL NT grec")
    parser.add_argument("xml_path", help="Chemin vers greek-nt.xml")
    parser.add_argument(
        "--out",
        default="./proiel_audit",
        help="Dossier de sortie (défaut : ./proiel_audit)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.xml_path):
        print(f"Erreur : fichier introuvable : {args.xml_path}", file=sys.stderr)
        sys.exit(1)

    # Étape A — Parsing
    df = parse_proiel_xml(args.xml_path)

    # Étape B — Métriques M1–M5
    metrics_df = compute_metrics_per_book(df)

    # Étape C — Métrique M6
    char_df = compute_character_coverage(df, TARGETS)

    # Application des seuils
    metrics_df = apply_thresholds(metrics_df, char_df)

    # Étape D — Export
    export_csvs(metrics_df, char_df, args.out)
    generate_decision_report(metrics_df, char_df, args.out)

    # Aperçu console du classement final
    print("\n=== CLASSEMENT FINAL ===")
    print(
        metrics_df[
            [
                "book",
                "M1_coref_rate",
                "M2_chain_count",
                "M3_avg_chain_len",
                "M4_pronoun_coverage",
                "role",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
