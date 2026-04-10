# Plan d'action — Coréférence NT grec
## `ntcoref` · Focus résolution des personnages

> Ce plan est dérivé de la Phase 1-2-3 de la feuille de route `grcnlp` (cf. *Faisabilité d'un portage de BookNLP pour le grec ancien du NT*).
> Il recentre l'ensemble du travail sur **un objectif unique** : résoudre la coréférence des personnages dans le NT grec, à l'échelle d'un groupe de versets, d'un chapitre ou d'un livre entier.

---

## Objectif central

Étant donné un passage du NT grec (péricope, chapitre, livre), le système doit produire :

| Sortie | Description | Exemple |
|---|---|---|
| **Chaînes d'entités** | Toutes les mentions d'un même personnage regroupées | `Ἰησοῦς` / `αὐτός` / `ὁ διδάσκαλος` / ∅-sujet → `IESOUS` |
| **Attribution des discours** | *Qui dit quoi* — locuteur de chaque prise de parole | `εἶπεν αὐτοῖς ὁ Ἰησοῦς·` → `IESOUS` |
| **Actes narratifs** | *Qui fait quoi* — agent et patient de chaque prédicat verbal | `ἐθεράπευσεν` : agent=`IESOUS`, patient=`ὁ λεπρός` |

**Granularités supportées :**
- **Groupe de versets** (péricope, 3–15 versets) — coréférence locale, résolution rapide
- **Chapitre** — coréférence à portée moyenne, changements de scène
- **Livre du NT** — chaînes longues, personnages récurrents, homonymes à désambiguïser

---

## Principes directeurs du plan

**1. Coréférence d'abord, NER ensuite.**
On ne construit pas un NER complet avant de toucher à la coréférence. On construit le NER *au minimum nécessaire* pour initialiser les chaînes : détecter les noms propres de personnages (PER) et les groupes nominaux définis référant à des personnes.

**2. Morphologie avant apprentissage automatique (Approche Hybride).**
Le grec koinè offre genre, nombre, cas sur chaque token. Une baseline à règles morphologiques sur les pronoms explicites (`αὐτός`, formes de `ὁ` anaphorique, `ἐκεῖνος`) est réaliste et rapide. Le ML ne vient qu'en surcouche pour les cas difficiles (pro-drop, groupes nominaux définis). *Cette approche hybride est validée à la fois par l'équipe de la KU Leuven (Beersmans et al., 2025 ; Keersmaekers, 2020 pour la modélisation sémantique de la koinè via les papyrus) et par Kindt, Vidal-Gorène et al. (2022, "Analyse automatique du grec ancien par réseau de neurones"). Ces derniers ont démontré sur le corpus byzantin De Thessalonica Capta que si l'approche symbolique (dictionnaires) est extrêmement précise, elle échoue sur l'ambiguïté (plusieurs analyses hors contexte pour ~13% des mots) et sur les mots inconnus (~6%). Le réseau de neurones (modèle PIE) est alors redoutable pour désambiguïser grâce au contexte. Notre modèle de coréférence adoptera cette même architecture séquentielle : un "tamis" symbolique strict en première passe, suivi de probabilités neuronales uniquement pour résoudre les ambiguïtés résiduelles ou les impasses.*

**3. Pro-drop comme module propre.**
C'est le principal écart avec BookNLP et le problème le plus difficile. Il mérite un sprint dédié, avec annotation manuelle ciblée, et ne bloque pas les autres modules.

**4. Granularité comme paramètre de la pipeline.**
Le système doit fonctionner à trois niveaux. La fenêtre de résolution (combien de versets en arrière on cherche un antécédent) est un paramètre explicite, pas une contrainte architecturale.

---

## Architecture cible simplifiée (focus coréférence)

```
Texte grec NT (péricope / chapitre / livre)
        │
        ▼
  [C0] Tokenisation + Lemmatisation + POS + Morphologie + Dépendances
       ← Backend syntaxique : `Trankit` (architecture Biaffine), SOTA validé pour la Koinè (Keersmaekers & Van Hal, 2024 ; Celano, 2025)
       ← Backend lemmatisation : `GreTa` (Celano, 2025)
        │
        ▼
  [C0.5] Détection de corruptions textuelles (Resilience Module)
       ← Probabilités conditionnelles LOGION (Brooks et al., 2025)
       ← Flag `LOW_CONFIDENCE_TEXT_CORRUPTION` pour les anomalies
        │
        ▼
  [C1] Détection des mentions candidates
       ← Noms propres PER (NER minimal)
       ← Pronoms anaphoriques (αὐτός et formes)
       ← Groupes nominaux définis référant à des personnes
       ← Sujets verbaux nuls (verbes sans sujet syntaxique)
        │
        ▼
  [C2] Clustering de noms — entités canoniques
       ← Lemmatisation + dictionnaire NT (Σίμων/Πέτρος/Κηφᾶς → PETROS)
       ← Cooccurrences d'identification explicite (Jean 1:42)
        │
        ▼
  [C3a] Résolution pronominale (Architecture hybride : règles + ML)
        ← Accord genre + nombre → filtrage strict (tamis symbolique)
        ← Scoring ML : distance, saillance, sujet grammatical
        │ *(Inspiré de l'approche hybride de Kindt et al. 2022 et Beersmans et al. 2025)*
        │
  [C3b] Résolution des sujets implicites (pro-drop)
        ← Morphologie verbale (personne, nombre)
        ← Continuité narrative (sujet de la clause précédente)
        ← Marqueurs de rupture : δέ, τότε, participes circonstanciels
        │
  [C3c] Groupes nominaux définis
        ← "ὁ διδάσκαλος" → IESOUS si contexte l'indique
        ← Règles + classification légère
        │
        ▼
  [C4] Attribution des discours directs
       ← Verbes dicendi (λέγω, εἶπεν, ἀποκρίνομαι…)
       ← Agent résolu par C3
        │
        ▼
  [C5] Actes narratifs par personnage (Semantic Role Labeling)
       ← Extraction des rôles sémantiques (Agent, Patient, Experiencer, Beneficiary...) inspirée de Keersmaekers (2020)
       ← Agrégation par entité canonique
        │
        ▼
  [Sortie] Chaînes d'entités + discours + actes narratifs
           → JSON structuré + HTML annoté + Graphe Multi-modal (Work → Mention → Person)
```

---

## Feuille de route — 5 sprints

### Sprint 0 — Données et environnement · ✅

**Issu de l'Étape 1 de la feuille de route globale, recentré coréférence.**

**Ce qu'on construit ici :**

_A. Dataset de coréférence de référence (gold standard minimal)_

- Télécharger et parser le **PROIEL NT treebank** (CoNLL-U) → extraire les annotations de coréférence existantes
- **Audit de couverture PROIEL** — voir protocole détaillé ci-dessous (§ Sprint 0 — Protocole d'audit PROIEL)
- Importer **N1904-TF** (Text-Fabric Nestle 1904) : features morpho (genre, nombre, cas, lemme, parse syntaxique) accessibles token par token
- Aligner PROIEL ↔ N1904-TF au niveau token (normalisation orthographique mineure : accents, majuscules)

_B. Inventaires linguistiques (lexiques de travail)_

| Lexique | Contenu | Usage |
|---|---|---|
| `pronouns.tsv` | Toutes les formes de `αὐτός`, `ἐκεῖνος`, `οὗτος`, `ὁ/ἡ/τό` anaphorique + leur morphologie | Détection des mentions pronominales |
| `verba_dicendi.tsv` | λέγω, εἶπεν, ἀποκρίνομαι, ἐρωτάω, φημί… (~30 verbes) + variantes dialectales koinè | Attribution des discours |
| `character_aliases.tsv` | Σίμων/Πέτρος/Κηφᾶς, Σαῦλος/Παῦλος, Marie×3, Jacques×2… (~60 entrées) | Clustering d'entités |
| `narrative_epithets.tsv` | ὁ κύριος, ὁ διδάσκαλος, ὁ υἱὸς τοῦ θεοῦ… → IESOUS | Mentions indirectes |

_C. Corpus d'évaluation annoté manuellement_

- Sélectionner **3 péricopes test** (environ 15–20 versets chacune) couvrant des configurations difficiles :
  - Changements de locuteur rapides (ex. Jean 4:7–26, dialogue Jésus/Samaritaine)
  - Pro-drop dense (ex. Marc 1:12–20)
  - Homonymes (ex. Actes 12:1–17 — Jacques, Pierre, Jean dans le même passage)
- Annoter manuellement les chaînes de coréférence pour ces 3 péricopes (format CoNLL-U)

**Livrable :** Dataset NT grec en CoNLL-U étendu + 3 lexiques + corpus gold annoté.

---

### Sprint 0 — Protocole d'audit PROIEL : identifier les livres les mieux couverts

#### Contexte PROIEL

Le dépôt PROIEL NT (`proiel/proiel-treebank`, fichier `greek-nt.xml`) couvre les 27 livres du NT en grec.
Le format natif est un **XML propriétaire** ; chaque token porte les attributs :

| Attribut XML | Contenu | Utile pour |
|---|---|---|
| `antecedent-id` | ID du token antécédent (si le token est une reprise coréférentielle) | Coréférence |
| `information-status` | `old` / `acc-inf` / `acc-gen` / `new` / `no-antecedent` | Type de mention |
| `pos` | Partie du discours | Filtrage mentions |
| `relation` | Relation de dépendance | Détection pro-drop |
| `lemma` | Lemme | Identification personnages |

La coréférence dans PROIEL est donc encodée par des **liens antécédent–anaphorique** (chaînes implicites à reconstruire), pas par des identifiants de cluster directs comme en CoNLL-2012.

> ⚠️ PROIEL ne couvre **pas** uniformément tous les livres : certains livres ont une annotation coréférentielle dense, d'autres quasi-absente. L'audit ci-dessous permet de le quantifier.

---

#### Étape A — Acquisition et parsing (1 jour)

```bash
git clone https://github.com/proiel/proiel-treebank
# Fichier cible : proiel-treebank/data/greek-nt.xml
```

Script Python de parsing :

```python
from lxml import etree
import pandas as pd
from collections import defaultdict

tree = etree.parse("proiel-treebank/data/greek-nt.xml")
root = tree.getroot()

rows = []
for sentence in root.iter("sentence"):
    book = sentence.get("source-division")  # ex. "Matthew", "John"
    for token in sentence.iter("token"):
        rows.append({
            "book":             book,
            "sentence_id":      sentence.get("id"),
            "token_id":         token.get("id"),
            "form":             token.get("form"),
            "lemma":            token.get("lemma"),
            "pos":              token.get("part-of-speech"),
            "relation":         token.get("relation"),
            "antecedent_id":    token.get("antecedent-id"),   # None si absent
            "info_status":      token.get("information-status"),
        })

df = pd.DataFrame(rows)
```

---

#### Étape B — Calcul des métriques de couverture par livre (2–3 heures)

Pour chaque livre du NT, calculer les **6 indicateurs** suivants :

| # | Métrique | Formule | Ce qu'elle mesure |
|---|---|---|---|
| M1 | **Taux d'annotation coréférentielle brut** | `tokens avec antecedent_id / tokens totaux` | Densité globale de l'annotation |
| M2 | **Nombre de chaînes distinctes** | Nombre de composantes connexes dans le graphe antécédent→anaphorique | Richesse des chaînes |
| M3 | **Longueur moyenne des chaînes** | Somme des tailles de chaînes / nombre de chaînes | Complétude des chaînes (les chaînes longues = annotation poursuivie) |
| M4 | **Part des mentions pronominales annotées** | `pronoms avec antecedent_id / pronoms totaux` | Couverture des reprises explicites |
| M5 | **Part des sujets nuls annotés** | `tokens pos=V sans sujet syntaxique avec info_status ≠ new / verbes pro-drop totaux` | Couverture du pro-drop |
| M6 | **Couverture des personnages cibles** | Pour chaque personnage de la liste cible : `mentions dans une chaîne / mentions totales du lemme` | Qualité pour notre usage précis |

```python
# Reconstruction des chaînes par livre
def build_chains(df_book):
    """Reconstruit les chaînes de coréférence par union-find."""
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(a, b):
        parent[find(a)] = find(b)

    for _, row in df_book.iterrows():
        if row["antecedent_id"] is not None:
            union(row["token_id"], row["antecedent_id"])

    chains = defaultdict(list)
    for _, row in df_book.iterrows():
        if row["antecedent_id"] is not None or find(row["token_id"]) != row["token_id"]:
            chains[find(row["token_id"])].append(row["token_id"])
    return chains

# Calcul M1–M5 par livre
metrics = {}
for book, group in df.groupby("book"):
    total = len(group)
    annotated = group["antecedent_id"].notna().sum()
    chains = build_chains(group)
    chain_lengths = [len(v) for v in chains.values() if len(v) > 1]
    pronouns = group[group["pos"].str.startswith("P")]   # POS pronoms
    pro_drop  = group[(group["relation"] == "sub") & (group["pos"].str.startswith("V"))]  # approximation

    metrics[book] = {
        "M1_coref_rate":       annotated / total if total else 0,
        "M2_chain_count":      len(chain_lengths),
        "M3_avg_chain_len":    sum(chain_lengths)/len(chain_lengths) if chain_lengths else 0,
        "M4_pronoun_coverage": pronouns["antecedent_id"].notna().sum() / len(pronouns) if len(pronouns) else 0,
        "M5_prodrop_coverage": 0,  # à affiner selon encodage PROIEL du pro-drop
        "total_tokens":        total,
    }

metrics_df = pd.DataFrame(metrics).T.sort_values("M1_coref_rate", ascending=False)
print(metrics_df.to_markdown())
```

---

#### Étape C — Analyse M6 : couverture des personnages cibles (2 heures)

Pour les 3 livres prioritaires (Jean, Marc, Actes), vérifier combien de mentions de chaque personnage principal sont effectivement dans une chaîne annotée.

**Personnages cibles par livre :**

| Livre | Personnages à auditer |
|---|---|
| Jean | Ἰησοῦς, Πέτρος, Ἰωάννης, Μαρία, Θωμᾶς, Πιλᾶτος |
| Marc | Ἰησοῦς, Πέτρος, Ἰάκωβος, Ἰωάννης, disciples (οἱ μαθηταί) |
| Actes | Πέτρος, Παῦλος, Βαρνάβας, Ἰάκωβος, Στέφανος |

```python
# Personnages cibles par livre (lemmes PROIEL)
targets = {
    "John":  ["Ἰησοῦς", "Πέτρος", "Ἰωάνης", "Μαρία", "Θωμᾶς", "Πιλᾶτος"],
    "Mark":  ["Ἰησοῦς", "Πέτρος", "Ἰάκωβος", "Ἰωάνης"],
    "Acts":  ["Πέτρος", "Παῦλος", "Βαρναβᾶς", "Ἰάκωβος", "Στέφανος"],
}

for book, chars in targets.items():
    df_book = df[df["book"] == book]
    print(f"\n=== {book} ===")
    for lemma in chars:
        mentions = df_book[df_book["lemma"] == lemma]
        in_chain = mentions["antecedent_id"].notna().sum()
        total    = len(mentions)
        # Aussi : mentions dont le token est lui-même un antécédent
        is_antecedent = df_book["antecedent_id"].isin(mentions["token_id"]).sum()
        print(f"  {lemma}: {total} mentions, {in_chain} comme anaphorique, "
              f"{is_antecedent} comme antécédent → couverture estimée")
```

> **Note importante :** dans PROIEL, le personnage nominatif (`Ἰησοῦς`) est souvent l'**antécédent** (il introduit la chaîne), pas l'anaphorique. La couverture réelle d'une chaîne se mesure donc en comptant à la fois les tokens qui ont un `antecedent_id` ET ceux qui sont référencés comme antécédents par d'autres tokens.

---

#### Étape D — Production du rapport de couverture (1 heure)

Le script complet `proiel_audit.py` intègre et consolide les étapes A, B, C, puis exporte trois fichiers :

```
proiel_coverage_report.csv    ← métriques M1–M5 pour les 27 livres du NT
proiel_character_coverage.csv ← métriques M6 pour les personnages cibles (Jean, Marc, Actes)
proiel_audit_decision.md      ← rapport de décision généré automatiquement
```

**Installation des dépendances :**
```bash
pip install lxml pandas tabulate
```

**Invocation :**
```bash
python proiel_audit.py proiel-treebank/data/greek-nt.xml --out ./proiel_audit/
```

---

**Code source — `proiel_audit.py` :**

> Le script complet est maintenu dans le dépôt du projet :
> 📁 [`~/Documents/Code/Github/grknlp`](file:///Users/ronan/Documents/Code/Github/grknlp)
>
> Fichier : `grknlp/scripts/proiel_audit.py`

Le script s'invoque ainsi, depuis la racine du dépôt :
```bash
pip install lxml pandas tabulate
python scripts/proiel_audit.py proiel-treebank/data/greek-nt.xml --out ./proiel_audit/
```

Il produit trois fichiers dans `./proiel_audit/` :

```
proiel_audit/
├── proiel_coverage_report.csv       ← métriques M1–M5 pour les 27 livres du NT + rôle assigné
├── proiel_character_coverage.csv    ← métrique M6 par personnage (Jean, Marc, Actes)
└── proiel_audit_decision.md         ← rapport de décision : train / eval / exclus
```

Exemple de `proiel_audit_decision.md` attendu en sortie :

```
## Recommandation finale

✅ Tous les livres prioritaires (Jean, Marc, Actes) atteignent au moins les seuils minimaux.

### Décision :
- Corpus d'entraînement (18 livres) : John, Mark, Luke, Matthew, Acts, Romans, …
- Corpus d'évaluation / gold (3 livres) : John, Mark, Acts
- Livres exclus (9 livres) : Philemon, 2 John, 3 John, Jude, …
```

> ⚠️ **Point d'attention sur les lemmes PROIEL.** Les lemmes dans `greek-nt.xml` peuvent différer légèrement du lexique standard (normalisation des accents, forme lexicale choisie). Si un personnage cible revient à 0 mentions, inspecter les lemmes fréquents du livre avec `df[df["book"]=="John"]["lemma"].value_counts().head(20)` pour identifier la forme exacte utilisée par PROIEL et corriger la constante `TARGETS` dans le script.

---

#### Résultats réels de l'audit _(exécuté le 1er avril 2026)_

> Le script `proiel_audit.py` a été exécuté avec succès. Les trois fichiers de sortie sont présents dans `~/Documents/Code/Github/grknlp/proiel_audit/`. L'analyse ci-dessous compare les résultats réels aux estimations du plan et tire les conséquences pour la suite.

##### Métriques M1–M5 — résultats vs estimations

| Livre | M1 estimé | **M1 réel** | M2 estimé | **M2 réel** | M3 estimé | **M3 réel** | M4 estimé | **M4 réel** | Rôle assigné |
|---|---|---|---|---|---|---|---|---|---|
| John  | 0.127 | **0.287** (+2.3×) | 412 | **681** | 4.8 | **8.27** | 0.61 | **0.82** | ✅ PRIORITY_EVAL |
| Mark  | 0.098 | **0.260** (+2.7×) | 287 | **568** | 3.9 | **6.77** | 0.54 | **0.80** | ✅ PRIORITY_EVAL |
| Luke  | — | **0.248** | — | **992** | — | **6.39** | — | **0.78** | ✅ TRAIN_IDEAL |
| Matthew | — | **0.237** | — | **961** | — | **5.97** | — | **0.79** | ✅ TRAIN_IDEAL |
| **Acts** | 0.082 | **0.000** | 310 | **0** | 3.6 | **0** | 0.49 | **0.00** | ❌ EXCLUDED |
| Tous les épîtres (23 livres) | — | **0.000** | — | **0** | — | **0** | — | **0.00** | ❌ EXCLUDED |

**Lecture :** Les 4 Évangiles sont annotés à un niveau bien supérieur aux estimations (×2 à ×2.7 sur M1). En revanche, les Actes et toutes les Épîtres ont une couverture nulle — PROIEL n'a pas annoté la coréférence hors des Évangiles.

---

##### Couverture M6 — personnages cibles

| Livre | Personnage | Mentions | In chain | M6 | Statut |
|---|---|---|---|---|---|
| John | Ἰησοῦς | 240 | 235 | **0.979** | ✅ IDEAL |
| John | Πέτρος | 34 | 16 | **0.471** | ❌ INSUFFISANT |
| John | Ἰωάν(ν)ης | 23 | 17 | **0.739** | ✅ IDEAL |
| John | Μαρία | 15 | 13 | **0.867** | ✅ IDEAL |
| John | Θωμᾶς | 7 | 6 | **0.857** | ✅ IDEAL |
| John | Πιλᾶτος | 20 | 20 | **1.000** | ✅ IDEAL |
| Mark | Ἰησοῦς | 80 | 77 | **0.963** | ✅ IDEAL |
| Mark | Πέτρος | 19 | 14 | **0.737** | ✅ IDEAL |
| Mark | Ἰάκωβος | 15 | 10 | **0.667** | ⚠️ MINIMAL |
| Mark | Ἰωάν(ν)ης | 26 | 23 | **0.885** | ✅ IDEAL |
| Acts | Πέτρος | 56 | 0 | **0.000** | ❌ INSUFFISANT |
| Acts | Παῦλος | 128 | 0 | **0.000** | ❌ INSUFFISANT |
| Acts | Βαρναβᾶς | 23 | 0 | **0.000** | ❌ INSUFFISANT |
| Acts | Ἰάκωβος | 7 | 0 | **0.000** | ❌ INSUFFISANT |
| Acts | Στέφανος | 7 | 0 | **0.000** | ❌ INSUFFISANT |

**Point d'attention John/Πέτρος :** malgré le rôle PRIORITY_EVAL de Jean (fondé sur Ἰησοῦς à 0.98), la chaîne de Pierre dans Jean est insuffisante (M6=0.47, 16 mentions sur 34 seulement en chaîne). Ce personnage nécessitera une annotation manuelle ciblée sur l'Évangile de Jean, indépendamment de la stratégie Acts.

---

##### Décision de corpus — résultante de l'audit

| Rôle | Livres | Justification |
|---|---|---|
| **Corpus d'évaluation / gold** | Jean, Marc | Seuls livres prioritaires avec couverture idéale |
| **Corpus d'entraînement** | Luc, Matthieu | TRAIN_IDEAL, non utilisés comme gold pour éviter la contamination |
| **Exclus** | Actes + 23 épîtres | Couverture PROIEL nulle (M1=0.0) |

> ⚠️ **Actes est un livre prioritaire exclu.** La stratégie d'augmentation manuelle du plan s'applique (voir §"Stratégie d'augmentation manuelle pour les Actes" ci-dessous).

---

##### Stratégie d'augmentation manuelle pour les Actes

La couverture PROIEL de l'ensemble du livre des Actes est nulle : 0 lien `antecedent_id` sur 18 527 tokens, pour 5 personnages cibles totalisant 221 mentions (Πέτρος×56, Παῦλος×128, Βαρναβᾶς×23, Ἰάκωβος×7, Στέφανος×7).

**Approche recommandée — annotation manuelle en 3 péricopes ciblées :**

| Péricope | Référence | Pourquoi ce passage |
|---|---|---|
| Discours de Pierre à Pentecôte | Actes 2:14–41 | Pierre seul locuteur, pro-drop dense, mentions anaphoriques abondantes |
| Conversion de Saul | Actes 9:1–31 | Transition Saul→Paul, changement de nom, chaîne longue |
| Concile de Jérusalem | Actes 15:1–35 | Plusieurs personnages (Pierre, Paul, Jacques) dans le même passage — test des homonymes |

**Format :** CoNLL-U étendu avec colonne `COREF` en format MISC (ex. `COREF=PETROS-1`), compatible avec l'export du module `GrcCoref`.

**Critère d'arrêt :** au minimum 150 mentions annotées dans les chaînes des 5 personnages cibles, réparties sur les 3 péricopes. Cela représente environ 2 à 3 jours de travail pour un helléniste.

---

#### Critères de sélection — Qu'est-ce qu'un livre "suffisamment couvert" ?

Un livre est **utilisable comme données d'entraînement** si toutes les conditions suivantes sont remplies :

| Critère | Seuil minimal | Seuil idéal |
|---|---|---|
| M1 — taux d'annotation brut | ≥ 5% | ≥ 10% |
| M2 — nombre de chaînes distinctes | ≥ 100 chaînes | ≥ 300 |
| M3 — longueur moyenne des chaînes | ≥ 3 mentions | ≥ 5 |
| M4 — couverture des pronoms | ≥ 40% | ≥ 60% |
| M6 — couverture des personnages cibles | ≥ 50% des mentions du personnage principal | ≥ 70% |

Un livre est **utilisable comme corpus d'évaluation** (gold) s'il atteint les seuils idéaux ET si ses chaînes sont inspectées manuellement pour vérifier l'absence d'erreurs systématiques d'annotation.

> Si les 3 livres prioritaires (Jean, Marc, Actes) n'atteignent pas les seuils minimaux sur M1 ou M4, le plan bascule vers une **stratégie d'augmentation manuelle** : annoter manuellement les péricopes manquantes de ces livres plutôt que de chercher un autre livre mieux couvert.

---

#### Définition de "tâche complète"

La tâche d'audit PROIEL est considérée **achevée** quand les 4 conditions suivantes sont satisfaites :

**~~✅~~ ✅ Condition 1 — Données parsées et vérifiées** · _ACCOMPLIE le 1er avril 2026_
Le script produit un DataFrame complet pour les 27 livres du NT sans erreur. Vérifié : 27 livres détectés, tous les tokens ont un champ `form` non nul.

**~~✅~~ ✅ Condition 2 — Rapport de couverture produit** · _ACCOMPLIE le 1er avril 2026_
`proiel_coverage_report.csv` présent dans `grknlp/proiel_audit/` avec métriques M1–M5 pour les 27 livres, trié par M1 décroissant, colonne `role` remplie. Résultat : 4 livres retenus (Jean, Marc, Luc, Matthieu), 23 exclus.

**~~✅~~ ✅ Condition 3 — Couverture personnages validée pour Jean, Marc, Actes** · _ACCOMPLIE le 1er avril 2026_
`proiel_character_coverage.csv` présent avec données M6 complètes. Bilan :
- Jean/Ἰησοῦς : M6=0.979 ✅ — Jean retenu comme PRIORITY_EVAL
- Marc/Ἰησοῦς : M6=0.963 ✅ — Marc retenu comme PRIORITY_EVAL
- Actes/Πέτρος : M6=0.000 ❌ — Actes exclu, stratégie d'augmentation manuelle déclenchée
- **Signal supplémentaire :** Jean/Πέτρος = M6=0.471 ❌ — annotation manuelle requise sur ce personnage dans Jean

**⚠️ Condition 4 — Décision documentée** · _PARTIELLEMENT ACCOMPLIE_
`proiel_audit_decision.md` présent (10 Ko, généré automatiquement). La décision de corpus est enregistrée dans le fichier et dans le plan (§"Décision de corpus" ci-dessus). Il reste à valider manuellement un échantillon de chaînes dans Jean et Marc pour confirmer l'absence d'erreurs systématiques avant de les utiliser comme gold.

**Action restante pour clore la Condition 4 :**
> Inspecter manuellement 20 à 30 chaînes dans Jean et dans Marc (choisir au hasard avec `df[df["book"]=="John"].sample(30)` sur les tokens `antecedent_id` non nuls) et vérifier qu'elles sont correctes linguistiquement. Si le taux d'erreur constaté est < 10%, les deux livres sont validés comme gold. Documenter le résultat dans `proiel_audit_decision.md` sous une section `## Validation manuelle`.

**Durée estimée totale : 1,5 à 2 jours de travail.** · _Script exécuté en ~1 heure. Reste : validation manuelle (~2h) + annotation Actes (2–3 jours helléniste)._

---

### Sprint 1 — Pipeline de base + détection des mentions · ✅

**Issu de l'Étape 2 (Module 0+1), recentré sur la détection des mentions coréférentielles.**

**Ce qu'on construit ici :**

_A. Pipeline de base opérationnelle sur le NT + Détection d'erreurs_

La pipeline ne reposera plus sur le modèle unique `odyCy`, mais sur un assemblage des meilleurs composants SOTA :

- **Backend Syntaxique (`Trankit`) :** Celano (2025) et Keersmaekers & Van Hal (2024) ont démontré que l'architecture Biaffine de `Trankit` est l'état de l'art absolu pour extraire les arbres de dépendances en grec ancien (particulièrement la Koinè documentaire avec un LAS de ~0.85). Une syntaxe parfaite est critique pour la détection du pro-drop. L'alignement du format d'annotation (PROIEL vers UD/AGDT) nécessitera une attention particulière.
- **Backend Lemmatisation (`GreTa`) :** Celano (2025) a prouvé que `GreTa` surpasse les autres modèles pour la lemmatisation. Le *Clustering de noms (C2)* s'appuyant intégralement sur les lemmes, ce modèle sera privilégié.
- **Module de résilience (C0.5) :** Intégrer un filtre basé sur les modèles LOGION (Brooks et al., NAACL 2025). Utiliser les probabilités conditionnelles du modèle pour détecter d'éventuelles erreurs de numérisation (OCR) ou des hapax scribaux dans le texte d'entrée. Si un token a une probabilité anormalement basse, lui assigner le flag `LOW_CONFIDENCE_TEXT_CORRUPTION` pour éviter que la pipeline de coréférence ne force une résolution absurde sur un mot corrompu.

_B. Composant `MentionDetector` (spaCy custom component)_

Détecte et classifie les mentions candidates :

| Type de mention | Détection | Trait morpho clé |
|---|---|---|
| Nom propre PER | NER léger (regex + lemme dans lexique NT) | — |
| Pronom anaphorique | Lookup dans `pronouns.tsv` | genre, nombre, cas |
| Groupe nominal défini | `det=ὁ/ἡ/τό` + tête nominale humaine | genre, nombre |
| Sujet verbal nul | Verbe fini sans `nsubj` dans dépendances | personne, nombre du verbe |
| Épithète narrative | Lookup dans `narrative_epithets.tsv` | — |

Chaque mention reçoit :
- `mention.type` ∈ {`NAMED`, `PRONOUN`, `DEF_NP`, `PRO_DROP`, `EPITHET`}
- `mention.morph` : genre, nombre, cas (depuis odyCy)
- `mention.span` : position dans le texte

_C. NER minimal_

Objectif : détecter les noms propres de personnages (PER) uniquement.
Approche : 
1. **Filtre de capitalisation :** Ne considérer que les tokens commençant par une majuscule. Beersmans et al. (2024, "Gotta catch ‘em all!") ont démontré qu'en ramenant la tâche à une classification binaire (Personne vs Reste) sur les seuls mots capitalisés, on obtient les meilleures performances NER en grec ancien.
2. **Utilisation des modèles UGARIT pour le NER :** Au lieu d'utiliser `LOGION` (qui est meilleur pour la syntaxe fine/coréférence), nous nous appuierons sur le modèle multilingue `UGARIT/grc-ner-xlmr`. Palladino & Yousef (LT4HALA 2024) ont démontré qu'il s'agit du modèle de l'état de l'art le plus performant et robuste pour l'extraction brute d'Entités Nommées en grec ancien (F1 ~88.8%), particulièrement sur des textes hors-domaine.
3. **Expansion syntaxique (Multi-token) :** Bien que performant, le modèle NER peine parfois sur les noms composés. Si un token est identifié comme PER par le modèle, inspecter ses enfants directs dans l'arbre de dépendances `odyCy`. Si un enfant est également capitalisé (ex: "Πόντιος Πιλᾶτος", "Ἰησοῦς Χριστός"), le fusionner dans la même mention. Cette stratégie hybride (NER + Syntaxe) est indispensable (Beersmans et al., 2024).

**Option `SpanResolver.v1` (à évaluer en fin de Sprint 1) :** Une fois que `UGARIT/grc-ner-xlmr` a identifié les têtes de mentions (token level), entraîner un `SpanResolver.v1` (spaCy expérimental) sur PROIEL pour apprendre les frontières de spans de manière data-driven, en remplacement de l'inspection heuristique des enfants syntaxiques. Entraînable directement depuis les données PROIEL (Jean + Marc = ~1 200 spans annotés). Avantage : intégration native dans le pipeline odyCy.

*(Note d'architecture : Nous aurons donc un pipeline hautement spécialisé : `UGARIT/grc-ner-xlmr` pour la détection stricte des entités nommées (NER), `LOGION` pour l'évaluation de la confiance/détection d'erreurs (C0.5), et le meilleur parseur (`Trankit`) couplé à `GreTa` pour la morphosyntaxe/lemmes, et `LOGION`/Embeddings Syntaxiques pour la résolution fine des pronoms/pro-drop qui sont le vrai moteur de notre module de coréférence).*

**Ne pas construire un NER général complet à ce stade** — ce serait du travail inutile pour l'objectif coréférence.

**Livrable :** Composant `MentionDetector` fonctionnel. Pour un texte NT en entrée, on obtient la liste de toutes les mentions candidates avec leurs traits morphologiques.
**Métrique cible :** Rappel > 90% sur les 3 péricopes gold (on accepte du bruit, on veut ne rien manquer).

---

### Sprint 2 — Résolution de coréférence

**Cœur du plan. Correspond à l'Étape 3 (clustering) + Étape 4 (coréférence) fusionnées.**

#### 2A — Clustering de noms de personnages · ✅

Avant de résoudre les pronoms, on unifie les noms propres en entités canoniques. *Il est crucial de se reposer sur ces règles déterministes. En effet, la littérature (Beersmans et al., 2025) a prouvé que les modèles ML de désambiguïsation d'entités échouent largement sur les homonymes en grec ancien faute d'indices contextuels suffisants. De plus, Kindt et al. (2022) ont mesuré que les réseaux de neurones peinent particulièrement sur l'analyse des noms propres (seulement 71,2% d'exactitude sur les anthroponymes, contre >93% sur les verbes et pronoms). Cela valide notre décision de sécuriser cette étape via un registre canonique et des règles dures (`character_aliases.tsv`).*

- **Règle 1 — Même lemme :** `Ἰησοῦς` (nom.), `Ἰησοῦν` (acc.), `Ἰησοῦ` (gén.) → entité `IESOUS`
- **Règle 2 — Dictionnaire d'alias :** `character_aliases.tsv` → fusionne Σίμων/Πέτρος/Κηφᾶς → `PETROS`
- **Règle 3 — Identification explicite :** détecter les clauses du type "X, qui est Y" ou "X, c'est-à-dire Y" (Jean 1:42 : `Σὺ εἶ Σίμων … σὺ κληθήσῃ Κηφᾶς`) → relier les deux entités
- **Désambiguïsation des homonymes :** par livre d'abord (Jacques dans Marc ≠ Jacques dans Actes), puis par cluster de cooccurrence narratif
- **Génération de profils riches (Volltext) et collecte systématique d'attributs :** Ne pas se contenter de stocker un ID canonique. Le registre doit accumuler une description textuelle des personnages (ex: "Jésus de Nazareth, le maître, fils de Dieu") ainsi que des attributs historiques précis (genre, religion, métier, date) issus de ressources comme la *Paulys Realencyclopädie* ou *Trismegistos*. La littérature (Beersmans et al., DH Benelux 2025) a prouvé que les modèles ML de résolution (Cross-encoders) s'effondrent (précision chutant à 6%) s'ils ne disposent pas d'un contexte "Volltext" riche sur l'entité candidate au moment du choix, et que les attributs systématiques sont indispensables pour l'analyse de réseaux aval.

Livrable : `CharacterRegistry` — dictionnaire structuré comme un nœud "Person" de graphe : `{id_canonique: [liste des mentions nominales], attributs: {genre, groupe...}, profil_textuel: "..."}` pour chaque livre.

#### 2B — Résolution pronominale · ✅

Pour chaque mention `PRONOUN` ou `DEF_NP` :

**Algorithme de résolution (règles morphologiques) :**

```
1. Extraire traits du pronom : genre G, nombre N, cas C
2. Ouvrir une fenêtre arrière de W versets (W par défaut = 2 phrases/versets, fenêtre empiriquement validée par de Graaf, DH Benelux 2025 pour maximiser la précision en grec ancien)
   > **Calibration spaCy `antecedent_limit` :** Le paramètre `antecedent_limit` de `Coref.v1` (50–200 tokens) est l'équivalent machine de la fenêtre W. Pour le NT grec, 1 verset ≈ 15–25 tokens en moyenne (calculé sur PROIEL). Donc : fenêtre 2 versets ≈ `antecedent_limit=50`, fenêtre 10 versets ≈ `antecedent_limit=200`. Utiliser ces valeurs comme point de départ si on adopte `Coref.v1` pour la résolution ML.
3. Collecter les entités candidates : mentions NAMED ou PER dans la fenêtre, compatibles (même G, même N)
4. Scorer les candidats :
   - +3 si c'est le sujet grammatical de la clause précédente
   - +2 si c'est le sujet de la clause actuelle (même verbe)
   - Score de proximité (Distance-Decay) : Ajouter `1 / distance_en_tokens` (approche d'atténuation inverse validée par la formule de co-occurrence de de Graaf, DH Benelux 2025)
   - -1 si l'entité vient d'être déjà mentionnée comme non-référent (négation, contrastif)
5. Assigner l'antécédent de score maximal
6. Si score max < seuil → mention non résolue (à traiter en 2C)
```

Baseline attendue : ~70% F1 sur pronoms explicites (estimé d'après littérature sur langues flexionnelles).

#### 2C — Résolution des sujets implicites / pro-drop

C'est la vraie innovation par rapport à BookNLP.

**Détection :** verbe fini sans `nsubj` dans l'arbre de dépendances généré par le backend syntaxique (Trankit). *Sécurité ML (inspirée de Celano, 2023) :* Pour pallier les potentielles erreurs du parseur syntaxique sur la détection d'un sujet nul, nous couplerons notre modèle Transformer (`LOGION`) à une simple couche *Feedforward* entraînée pour confirmer la présence d'une ellipse dans la proposition, consolidant ainsi la détection des verbes *pro-drop* avant leur résolution.
**Résolution :**

| Signal | Règle |
|---|---|
| Personne/nombre du verbe | 3sg → cherche entité 3sg compatible dans fenêtre |
| Continuité narrative | Si pas de marqueur de rupture → sujet = sujet de la clause précédente |
| `δέ` de continuité | Souvent = même sujet ou sujet alterné (selon genre) |
| `δέ` adversatif / `τότε` / `καί` + sujet explicite | Rupture probable → chercher un nouvel antécédent |
| Participe circonstanciel | Le sujet du participe = sujet du verbe principal (sauf génitif absolu) |
| Génitif absolu | Sujet propre, souvent différent du sujet principal |

---

> #### ⚖️ Point d'arbitrage — LLM vs. fine-tuning BERT (décision à prendre avant l'annotation)
>
> **Contexte.** L'étape suivante (annotation manuelle de ~300 verbes pro-drop + fine-tuning) représente un investissement significatif et non réversible : 2 à 3 jours d'helléniste, puis un cycle d'entraînement. Avant de s'y engager, il faut arbitrer entre deux stratégies pour traiter les cas ambigus que les règles ne résolvent pas :
>
> | Stratégie | Description | Avantages | Risques |
> |---|---|---|---|
> | **A — Fine-tuning UGARIT + Silver Data filtrée** | **Architecture Two-Stage :** 1. Les règles morphologiques agissent comme un *Bi-encoder* pour récupérer 3-5 candidats stricts. 2. Un modèle ML (*Cross-encoder* basé sur `UGARIT-grc-alignment`) score ces candidats. <br>**Silver Data :** Extraire des milliers d'exemples "Silver" générés par règles. *Crucial : appliquer un filtre de fréquence maximale (ex. exclure les lemmes >50 occurrences) pour éviter de bruiter le set d'entraînement (Beersmans et al., DH Benelux 2025).* | Reproductible, évaluable. L'architecture en deux étapes garantit que le ML ne cherche pas dans le vide. | Coût d'annotation élevé pour le gold, nécessité de gérer des embeddings croisés (Cross-encoder). |
> | **B — Prompting et Instruct-Tuning de LLMs (Cullhed, 2024)** | Pour chaque verbe orphelin, envoyer le passage + contexte à un LLM. Cullhed (2024) a prouvé qu'un modèle causal de 8B paramètres (Llama 3.1) finement ajusté par instructions (Instruct-Tuning) sur le grec ancien atteint l'état de l'art, surpassant des modèles spécialisés comme Ithaca. Cela fait du *fine-tuning* d'un LLM ouvert une alternative SOTA extrêmement sérieuse pour résoudre les ambiguïtés sémantiques complexes du *pro-drop*. | Extrêmement puissant sur les cas imbriqués sémantiquement complexes. Évite les faiblesses du zero-shot pur. | Nécessite la création d'un jeu de données d'instructions (Prompt/Completion) et l'entraînement d'un adaptateur LoRA. |
> | **C — Stack spaCy natif (SpanResolver + Coref.v1)** | Fine-tuner `SpanResolver.v1` (mention detection) + `Coref.v1` (antecedent scoring) sur PROIEL. Traiter les verbes pro-drop comme des spans à un token (la tête verbale). Injecter les features morpho (genre, nombre, cas) dans tok2vec. | Intégration native odyCy, pipeline cohérent, pas de code ML maison | Architecture expérimentale (non testée sur grec), pro-drop reste non résolu nativement, besoin de fine-tuning complet |
> | **D — Modèles Vectoriels Syntaxiques (Keersmaekers 2020 ; Stopponi et al., 2024)** | Remplacer les embeddings standards par des modèles distributionnels basés sur les dépendances (*Syntactic word embeddings*). Stopponi et al. (2024) ont récemment confirmé que l'injection de la syntaxe dans les vecteurs surmonte le problème de l'ordre libre des mots en grec et offre la meilleure représentation sémantique possible, essentielle pour filtrer les candidats de coréférence par animacité. | Précision sémantique maximale, surmonte l'ordre libre des mots, capture de l'animacité. | Nécessite d'intégrer ou ré-entraîner ces vecteurs spécifiques. |
> | **E — Character-level BERT / LOGION (Brooks, DeVaul et al., 2023-2025)** | Utiliser les modèles de Princeton (`cabrooks/LOGION` ou l'architecture `desformers` de DeVaul). Ces modèles couplent un traitement au niveau caractère avec une table d'embeddings sub-word. L'adjonction d'une couche *Feedforward* à ces modèles permet également de détecter la simple présence d'une ellipse avec une très grande fiabilité (cf. Celano, 2023). | C'est l'approche la plus avancée à ce jour pour le grec. Elle capture nativement la morphologie (déclinaisons, conjugaisons), ce qui est idéal pour résoudre le pro-drop (qui dépend de la terminaison verbale). | Implémentation potentiellement plus lourde que `AG_BERT` (nécessite l'adaptation du code de DeVaul). |
>
> **Décision recommandée pour le ML :** Privilégier la **Stratégie E (LOGION/Desformers)**. Les modèles de niveau caractère, récemment validés par le groupe NLP de Princeton/MIT (NAACL 2025), offrent le socle le plus robuste pour une langue hautement flexionnelle comme le grec ancien, remplaçant avantageusement un BERT sub-word classique (`AG_BERT`).
>
> > **Note sur la Stratégie C :** Elle est à évaluer après l'arbitrage A/B. Elle peut servir de base ML pour les composants C3a et une partie de C3b, à condition d'injecter les features morphologiques d'odyCy dans le `tok2vec` de `Coref.v1` (via `spacy.registry`).
>
> **Comment arbitrer — expérience à mener en fin de Sprint 2B (semaine 11), avant de démarrer 2C :**
>
> 1. Sélectionner 50 verbes pro-drop dans Marc 1–4 (passage annoté gold disponible à ce stade).
> 2. Les soumettre aux deux approches : règles seules, puis LLM zéro-shot (avec un prompt structuré incluant 5 versets de contexte avant et après).
> 3. Comparer l'accuracy des deux sur les 50 cas gold.
> 4. **Critère de décision :** si le LLM atteint ≥ 75% d'accuracy en zéro-shot, envisager la stratégie B ou hybride et réduire l'annotation manuelle à un gold set d'évaluation uniquement (~100 exemples). Si < 75%, poursuivre avec la stratégie A (annotation complète + fine-tuning).
>
> **Durée de l'expérience :** 1 journée. Le coût de ne pas la faire est potentiellement 3 jours d'annotation inutile.

---

**Annotation manuelle ciblée _(si stratégie A confirmée par l'arbitrage ci-dessus)_ :**
Annoter ~300 verbes pro-drop dans les 3 péricopes gold + 2 chapitres supplémentaires.
Fine-tuner un petit classifieur (régression logistique ou MLP léger sur embeddings Ancient Greek BERT) pour les cas ambigus.

**Livrable :** Composant `GrcCoref` qui ajoute à chaque token spaCy :
- `token._.coref_id` : identifiant de l'entité canonique résolue (ou `None`)
- `token._.coref_type` : type de résolution (`PRONOUN_RULE`, `PRO_DROP_RULE`, `PRO_DROP_ML`, `NAMED`, `UNRESOLVED`)

---

## Sprint 2C — Postmortem & Pivot (Avril 2026)

### Résultats initiaux vs réels

| Métrique | Proxy Gold | PROIEL Gold |
|----------|-----------|-------------|
| LLM accuracy | 36.7% | **29.7%** |
| Rules accuracy | 33.3% | **24.8%** |

### Découverte clé

> **AUCUN benchmark SOTA n'existe pour la résolution de coréférence sur le grec ancien.** Notre objectif de 55-60% serait pioneering work.

### Nouvelle architecture (Two-Stage, Celano 2023)

1. **Stage 1:** Règles de haute précision (cas clairs ~87%)
2. **Stage 2:** Réseau neuronal pour cas ambigus (~13%)

**Documents:**
- [`SPRINT2C_POSTMORTEM.md`](./docs/SPRINT2C_POSTMORTEM.md) — Analyse détaillée
- [`SPRINT3A_PLAN.md`](./docs/SPRINT3A_PLAN.md) — Plan d'implémentation
- [`TARGET_JUSTIFICATION.md`](./docs/TARGET_JUSTIFICATION.md) — Justification de la cible 55-60%
- [`FUTURE_WORK.md`](./docs/FUTURE_WORK.md) — Évolutions futures documentées
- [`BIBLIOGRAPHY.md`](./docs/BIBLIOGRAPHY.md) — Bibliographie complète

---

### Sprint 3 — Attribution des discours & actes narratifs

**Correspond à l'Étape 5 de la feuille de route globale.**

#### 3A — Attribution des discours directs

Le discours direct dans le NT est signalé par :
- Deux-points `·` ou `·` + changement de mode (impératif, questions)
- Verbe dicendi (dans `verba_dicendi.tsv`) suivi d'une proposition
- Structure : [Agent] + [V.dicendi] + [αὐτοῖς/πρὸς αὐτόν/…] + [:] + [discours]

Algorithme :
1. Détecter les segments de discours direct (heuristique sur ponctuation + mode verbal)
2. Trouver le verbe dicendi le plus proche dans la clause introductrice. *S'appuyer sur l'analyse de Keersmaekers (2020) : distinguer le discours épistémique/déclaratif du discours déontique/ordre en analysant l'aspect de la complétive (présent/parfait vs aoriste).*
3. Résoudre l'agent du verbe dicendi via `GrcCoref`
4. Gérer les cas complexes : discours enchâssé, réponse sans introducteur, narration en style indirect

Output pour chaque prise de parole :
```json
{
  "ref": "John 4:10",
  "verse_id": "JHN-04-10", 
  "clause_id": 12, // Indispensable pour la Citation Proximity Analysis (CPA)
  "quote": "Εἰ ᾔδεις τὴν δωρεὰν τοῦ θεοῦ…",
  "speaker_id": "IESOUS",
  "speaker_mention": "ἀπεκρίθη",
  "addressee_id": "SAMARITAN_WOMAN",
  "confidence": 0.92
}
```

#### 3B — Actes narratifs par personnage

Pour chaque verbe fini dans le texte, nous implémenterons une extraction par **Semantic Role Labeling (SRL)** inspirée de Keersmaekers (2020), en se basant sur la typologie de *Pedalion* (29 rôles) :
1. Détecter le rôle sémantique de l'entité résolue par rapport au verbe : `Agent`, `Patient`, `Experiencer`, `Beneficiary`, `Companion`, etc. (Plutôt que de se fier au sujet/objet syntaxique qui échoue sur le passif ou les déponents).
2. Lemmatiser le verbe, le classifier : `SPEECH` / `MOTION` / `ACTION` / `COGNITION` / `PERCEPTION`
3. Associer le rôle à l'entité canonique (`GrcCoref`).

Agrégation par entité canonique et par granularité :

```python
# Par péricope
result.narrative_acts(scope="pericope", ref="John 4:1-26")
# Par chapitre
result.narrative_acts(scope="chapter", book="John", chapter=4)
# Par livre entier
result.narrative_acts(scope="book", book="John")
```

Output agrégé :
```json
{
  "character": "IESOUS",
  "canonical_name": "Ἰησοῦς",
  "scope": "John 4",
  "mentions_total": 18,
  "as_agent": [
    {"lemma": "λέγω", "count": 6, "type": "SPEECH"},
    {"lemma": "ἀποκρίνομαι", "count": 3, "type": "SPEECH"},
    {"lemma": "ἔρχομαι", "count": 2, "type": "MOTION"}
  ],
  "as_patient": [
    {"lemma": "ἐρωτάω", "count": 4, "agent": "SAMARITAN_WOMAN"}
  ]
}
```

---

### Sprint 4 — API, granularités et exports

**Correspond à l'Étape 6 de la feuille de route globale.**

#### Interface unifiée par granularité

```python
from ntcoref import NTCoref

coref = NTCoref(backend="odycy")  # ou "textfabric"

# Traitement d'un groupe de versets
result = coref.process(greek_text, scope="pericope", ref="John 4:1-26")

# Traitement d'un chapitre (via Text-Fabric)
result = coref.process_chapter(book="John", chapter=4)

# Traitement d'un livre entier
result = coref.process_book(book="Matthew")

# Accès aux résultats
result.entity_chains()           # toutes les chaînes d'entités
result.character_profile("IESOUS")  # mentions + discours + actes
result.quotes()                  # tous les discours directs attribués
result.narrative_acts("PETROS") # actes de Pierre dans le scope
result.unresolved_mentions()     # mentions non résolues (pour évaluation)

# Exports
result.to_conllu()               # CoNLL-U étendu avec colonnes coref
result.to_json()                 # JSON structuré (avec ID de clause/verset pour la CPA)
result.to_html()                 # visualisation annotée interactive
result.to_textfabric()           # features TF persistantes
result.to_graphml()              # Export réseau multi-modal (Work -> Mention -> Person) (d'après le modèle DH Benelux 2025)
```

#### Paramètres de granularité de la fenêtre de résolution

| Granularité | Fenêtre arrière | Comportement |
|---|---|---|
| Péricope (≤ 20 versets) | 5 versets | Résolution locale stricte |
| Chapitre | 10 versets | Résolution moyenne, reset aux changements de scène |
| Livre | 20 versets + mémoire de personnage | Résolution globale, personnages récurrents prioritaires |

#### Visualisation HTML

Chaque entité canonique reçoit une couleur. Les mentions sont surlignées avec tooltip (type de résolution, confiance). Les discours directs sont encadrés avec le locuteur identifié.

---

## Évaluation — métriques et corpus test

### Métriques standards de coréférence

| Module | Métrique | Cible |
|---|---|---|
| Détection des mentions | Rappel | > 90% |
| Résolution pronominale | MUC F1 / B³ F1 / CEAFₑ F1 → **CoNLL Avg** | > 65% |
| Pro-drop | Accuracy sur gold annoté | > 60% (pioneering) |
| Attribution discours | Précision | > 85% |
| Actes narratifs (agent) | Accuracy agent résolu | > 80% |

### Corpus d'évaluation

- **Gold péricopes** (Sprint 0) : 3 passages annotés manuellement → évaluation à granularité fine
- **PROIEL NT** (10% réservé) : Épître aux Romains + Jean 1–5 → évaluation à l'échelle chapitre/livre
- **Annotation pro-drop** : 300 verbes annotés manuellement par un helléniste

---

## Risques spécifiques et mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| Pro-drop ambiguë (δέ de continuité vs rupture) | Haute — affecte 30–40% des clauses | Baseline à règles d'abord ; fine-tuning ciblé sur les cas ambigus |
| Homonymes mal désambiguïsés (Jacques×2, Marie×3) | Moyenne — chaînes polluées | Désambiguïsation par livre + cluster de cooccurrence |
| odyCy moins précis sur koinè tardif (Apocalypse) | Basse-Moyenne | Fine-tuning sur PROIEL + test systématique livre par livre |
| Mentions non résolues s'accumulent | Moyenne | Exposer `unresolved_mentions()` dans l'API ; permettre correction manuelle post-hoc |
| Corpus d'annotation pro-drop trop petit | Haute | Commencer par les règles, augmenter avec la LXX (grec très proche du NT) |
| Dégradation due au bruit textuel (Character Error Rate) | Haute | Gal (2024) a démontré une chute de précision linéaire due au bruit. Le module de résilience C0.5 (probabilités LOGION) isolera les corruptions en amont pour protéger la coréférence. |

---

## Relation avec la feuille de route globale `grcnlp`

Ce plan "Coréférence" **correspond aux Étapes 1 à 5** de la feuille de route globale, mais avec un **périmètre strictement narratif** :

| Étape globale | Ce plan | Différence |
|---|---|---|
| Étape 1 — Audit données | Sprint 0 | Recentré : seulement les données utiles à la coréférence |
| Étape 2 — NLP base + NER | Sprint 1 | NER minimal (PER seulement), pas de NER général |
| Étape 3 — Clustering | Sprint 2A | Inchangé |
| Étape 4 — Coréférence | Sprints 2B + 2C | Décomposé en deux sprints, pro-drop traité en profondeur |
| Étape 5 — Discours + Actes | Sprint 3 | Inchangé |
| Étape 6 — Packaging | Sprint 4 | Ajout des granularités péricope/chapitre/livre |

Les modules NER général (LOC, ORG, groupes) et l'export Text-Fabric complet sont **reportés à une phase ultérieure**, hors scope de ce plan.

---

## Jalons (milestones)

```
✅ Sprint 0        │ Données, lexiques, gold annoté
✅ Sprint 1        │ MentionDetector + NER minimal
✅ Sprint 2A       │ CharacterRegistry + clustering
✅ Sprint 2B       │ Résolution pronominale (règles)
🔄 Sprint 2C v2   │ Pro-drop (en cours - Avril 2026)
⏳ Sprint 3A       │ Attribution discours directs
⏳ Sprint 3B       │ Actes narratifs par personnage
⏳ Sprint 4        │ API + granularités + exports + évaluation finale
```

---

## Actions immédiates — Sprint 3A (corrigé 9 avril 2026)

### ⚠️ Corrections rétroactives appliquées

| Correction | Avant | Après |
|------------|-------|-------|
| Métrique d'éval | String-matching | **Head-matching** (CRAC standard) |
| Fenêtre résolution | 5 versets | **2 versets** (réduit entités obsolètes) |

### Phase 1.1 : Correction head-matching

1. **Implémenter extraction synchronous heads**
   - PROIEL: tokens avec `syncat=X` dans MISC
   - Fallback: tête syntaxique directe

2. **Corriger script d'évaluation**
   - `scripts/sprint3a_phase1_prodrop_detection.py`
   - Ajouter fonction `get_head_matching_id(token, gold_heads)`

### Phase 1.2 : Réduction fenêtre

1. **Ajuster paramètre window**
   - Modifier `window_size = 2` (au lieu de 5)
   - dans `find_antecedents_in_window()`

### Phase 1 : Parsing dépendanciel

1. **Charger PROIEL XML directement** (pas trankit)
   ```python
   from lxml import etree
   tree = etree.parse("proiel-treebank/data/greek-nt.xml")
   ```

2. **Détecter les candidats pro-drop**
   - Trouver les verbes finis (pos=V-*)
   - Filtrer ceux sans nsubj dans les dépendances
   - Vérifier compatibilité personne/nombre

3. **Livrable :** `find_prodrop_candidates()` fonctionnel

### Phase 2 : Métrique head-matching

1. **Adopter head-matching** au lieu de string-matching
   - Correspondance sur la tête syntaxique (dépendances)
   - Standard CRAC 2024

2. **Réévaluer baselines** avec nouvelle métrique

### Phase 3 : Classificateur d'ambiguïté

1. **Détecter les marqueurs narratifs**
   - δέ (continuité vs adversatif)
   - τότε (rupture temporelle)
   - Génitif absolu (changement de sujet)

2. **Construire `is_ambiguous()`**
   - 1 entité compatible → cas clair (règles)
   - 2+ entités → cas ambigu (ML)

### Point de validation

À la fin de chaque phase :
- Vérifier sur 50 instances PROIEL
- Documenter les erreurs dans `project/docs/`

---

## Documents de référence

| Fichier | Contenu |
|---------|---------|
| `docs/SPRINT3A_PLAN.md` | Plan détaillé phase par phase |
| `docs/TARGET_JUSTIFICATION.md` | Analyse benchmark + justification cible |
| `docs/FUTURE_WORK.md` | Évolutions futures (NEL, objets nuls, etc.) |
| `docs/BIBLIOGRAPHY.md` | 23 sources académiques formatées |
| `docs/SPRINT2C_POSTMORTEM.md` | Retour d'expérience Sprint 2C |
```

**Durée totale : 24 semaines (~6 mois)**
**Première démo fonctionnelle (péricope → chaînes + discours) : fin de semaine 15**
