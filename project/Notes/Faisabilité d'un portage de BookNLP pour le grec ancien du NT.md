# GrcNLP — Faisabilité d'un portage de BookNLP pour le grec ancien du NT
## Étude de faisabilité & feuille de route

---

## 0. Rappel du besoin

L'objectif est de construire une bibliothèque Python (provisoirement appelée **`grcnlp`** ou **`ntcoref`**) capable d'effectuer sur le texte grec du Nouveau Testament :

| Tâche | Exemple attendu |
|---|---|
| **Résolution de coréférence** | `αὐτός` / `αὐτῷ` / `ὁ` → `Ἰησοῦς` |
| **Chaînes d'entités** | Toutes les mentions de Pierre regroupées en une chaîne |
| **Attribution des actes narratifs** | "Pierre dit", "Jésus guérit", agent/patient par personnage |
| **Identification des locuteurs** | Attribution des discours directs à un personnage |
| **Regroupement de noms** | Σίμων / Πέτρος / Κηφᾶς → entité unique |

---

## PHASE 1 — Analyse de faisabilité (ce document)

### 1.1 Ce que BookNLP fait (architecture interne)

BookNLP s'appuie sur une pipeline modulaire combinant :

```
Texte brut
    │
    ▼
[spaCy] POS + dépendances syntaxiques
    │
    ▼
[BERT fine-tuné] → Reconnaissance d'entités nommées (NER)
    │
    ▼
[Clustering de noms] → "Tom" / "Tom Sawyer" / "Mr. Sawyer" → TOM_SAWYER
    │
    ▼
[Modèle de coréférence] → pronoms + noms communs → entités nommées
    │
    ▼
[Attribution des locuteurs] → discours direct → personnage
    │
    ▼
[Actes narratifs] → agent/patient par personnage (verbes)
```

Chaque module est entraîné sur des corpus annotés anglais (LitBank, PreCo).
→ **Aucun module n'est directement réutilisable** pour le grec ancien.

---

### 1.2 Spécificités du grec koinè / NT qui rendent le problème DIFFÉRENT

| Caractéristique | Impact sur le NLP |
|---|---|
| **Langue pro-drop** | Le sujet est souvent absent (`εἶπεν` = "il/elle dit") — la coréférence est encodée dans la flexion verbale, pas dans un pronom explicite |
| **Accord en genre/nombre/cas** | Potentiellement très utile : `αὐτῷ` (dat. masc. sg.) restreint fortement les antécédents possibles |
| **Richesse morphologique** | La résolution peut s'appuyer sur la morphologie plutôt que sur la position |
| **Participe absolu (génitif absolu)** | Construction narrative propre au grec, souvent sans lien syntaxique explicite avec le sujet principal |
| **Changements de sujet implicites** | Dans les Évangiles, le narrateur change souvent de personnage focalisé sans pronom |
| **Corpus de taille modeste** | Le NT fait ~137 000 mots — c'est petit pour entraîner un modèle from scratch |
| **Ressources annotées existantes** | PROIEL (annotations UD + coréférence partielle), N1904-TF (Text-Fabric), LOWFAT syntax trees |

---

### 1.3 Ressources disponibles (inventaire)

#### Corpus textuels annotés
- **PROIEL Treebank** — annotations UD (POS, dépendances) + **coréférence partielle** sur le NT grec → très précieux
- **N1904-TF** (Text-Fabric / ETCBC + Andrews University) — NT Nestle 1904 avec annotations linguistiques complètes
- **LOWFAT XML trees** (biblicalhumanities/greek-new-testament) — arbres syntaxiques du NT
- **Perseus Digital Library** — corpus grec large, base d'entraînement d'odyCy

#### Outils NLP grec ancien
- **odyCy** (`grc_odycy_joint_trf`) — pipeline spaCy état de l'art : POS, morphologie, dépendances, lemmatisation
- **greCy** — alternative, entraîné sur le TLG (corpus plus large), bonne lemmatisation hors-corpus
- **Ancient Greek BERT** — modèle transformeur pré-entraîné sur Perseus + First Thousand Years of Greek, base d'odyCy
- **Stanza** (StanfordNLP) — modèles grecs alternatifs
- **CLTK** — Classical Language Toolkit, utilitaires variés

#### Frameworks de gestion de corpus
- **Text-Fabric** — accès structuré au corpus NT avec features linguistiques riches
- **spaCy** (via odyCy) — traitement NLP en temps réel, extensible

---

### 1.4 Verdict de faisabilité

**✅ FAISABLE — mais par étapes, avec des compromis clairs**

La faisabilité repose sur trois piliers :

1. **La morphologie grecque compense le manque de pronoms explicites** — le genre, le nombre et le cas des formes pronominales et des participes permettent de filtrer fortement les antécédents candidats. Un système à base de règles morphologiques peut atteindre une bonne baseline.

2. **PROIEL contient déjà des annotations de coréférence partielles** sur le NT — c'est un point de départ pour un entraînement supervisé.

3. **odyCy + Ancient Greek BERT** fournissent une base morpho-syntaxique fiable sur laquelle greffer les modules manquants (coréférence, NER narratif, attribution).

**⚠️ Difficulté principale :** la résolution des sujets implicites (pro-drop) — il faudra un module spécifique, inexistant dans BookNLP.

---

## PHASE 2 — Architecture cible de la bibliothèque `grcnlp`

### 2.1 Schéma d'architecture

```
┌─────────────────────────────────────────────────────────┐
│                     grcnlp Pipeline                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Texte grec NT                                           │
│       │                                                  │
│       ▼                                                  │
│  [Module 0] Tokenisation + POS + Morphologie             │
│  ← odyCy (grc_odycy_joint_trf)                          │
│       │                                                  │
│       ▼                                                  │
│  [Module 1] NER Narratif                                 │
│  ← fine-tuning Ancient Greek BERT sur PROIEL/NT         │
│  → PER (Ἰησοῦς, Πέτρος…), LOC (Ἱερουσαλήμ…), ORG      │
│       │                                                  │
│       ▼                                                  │
│  [Module 2] Clustering de noms de personnages            │
│  ← règles + lemmatisation + graphe de cooccurrence      │
│  → Σίμων / Πέτρος / Κηφᾶς → PETROS                     │
│       │                                                  │
│       ▼                                                  │
│  [Module 3] Résolution de coréférence                    │
│  3a. Pronoms explicites (αὐτός, αὐτῷ…) → accord morpho │
│  3b. Sujets implicites (pro-drop) → contexte verbal     │
│  3c. Groupes nominaux définis (ὁ ἄνθρωπος) → entités   │
│       │                                                  │
│       ▼                                                  │
│  [Module 4] Attribution des discours directs             │
│  ← verbes dicendi (λέγω, ἀποκρίνομαι, εἶπεν…)         │
│  → "εἶπεν αὐτοῖς ὁ Ἰησοῦς" → locuteur = IESOUS        │
│       │                                                  │
│       ▼                                                  │
│  [Module 5] Actes narratifs par personnage               │
│  ← extraction agent/patient des prédicats verbaux       │
│  → IESOUS : agent de [ἐθεράπευσεν, εἶπεν, ἦλθεν…]     │
│       │                                                  │
│       ▼                                                  │
│  [Sortie] Chaînes d'entités + JSON + HTML annoté         │
└─────────────────────────────────────────────────────────┘
```

---

### 2.2 odyCy vs Text-Fabric : quel backend choisir ?

#### odyCy (surcouche spaCy)

| ✅ Avantages | ⚠️ Inconvénients |
|---|---|
| Architecture NLP standard (Doc/Token/Span) | Pas d'accès structuré aux nœuds du corpus NT |
| Extensible : custom components via `@Language.component` | Gestion du pro-drop à coder entièrement |
| Interopérable avec les extensions spaCy existantes (coref, NER) | Modèle chargé à chaque exécution |
| Fine-tuning natif via spaCy train | Morphologie moins accessible que via TF |
| Meilleure pour du **traitement en temps réel** d'un texte quelconque | — |

#### Text-Fabric

| ✅ Avantages | ⚠️ Inconvénients |
|---|---|
| Accès direct aux features linguistiques du NT (N1904-TF) | API différente de l'écosystème spaCy |
| Graphe de features : genre, nombre, cas, lemme, parse syntaxique | Moins adapté au traitement de nouveaux textes |
| Requêtes cross-références natives (chaînes, clauses, phrases) | Moins de modèles NLP disponibles en natif |
| Idéal pour **l'analyse du corpus NT fixe** | Courbe d'apprentissage spécifique |
| Résultats exportables, persistants, versionnés | |

#### Recommandation

> **Architecture hybride recommandée** :
>
> - **odyCy** comme moteur NLP de base (tokenisation, POS, morphologie, dépendances)
> - **Text-Fabric** comme source de données et backend de stockage des annotations du NT
> - **Interface unifiée** : la bibliothèque exporte ses résultats en format TF (features) ET en format spaCy (Doc)

Concrètement :

```python
# Usage via odyCy (texte libre)
from grcnlp import GrcNLP
nlp = GrcNLP(backend="odycy")
doc = nlp.process("εἶπεν δὲ αὐτοῖς ὁ Ἰησοῦς·")

# Usage via Text-Fabric (corpus NT structuré)
from grcnlp import GrcNLP
nlp = GrcNLP(backend="textfabric", corpus="N1904")
chains = nlp.entity_chains(book="Matthew")
```

---

## PHASE 3 — Feuille de route de développement (6 étapes)

---

### Étape 1 — Audit et collecte des données annotées (semaines 1–3)

**Objectif :** constituer le gold standard d'entraînement et d'évaluation.

**Actions :**
- Télécharger et parser le **PROIEL treebank NT** (format CoNLL-U) → extraction des annotations de coréférence existantes
- Importer le corpus **N1904-TF** (Text-Fabric / Nestle 1904) → features morphologiques, syntaxiques
- Aligner PROIEL ↔ N1904-TF au niveau token (normalisation orthographique)
- Recenser les **verbes dicendi** du NT (λέγω, εἶπεν, ἀποκρίνομαι, ἐρωτάω…) → dictionnaire
- Identifier les **pronoms anaphoriques** typiques (αὐτός et ses formes, ὁ/ἡ/τό anaphorique, ἐκεῖνος…)
- Recenser les **variantes nominales** des personnages principaux (Σίμων/Πέτρος/Κηφᾶς, Σαῦλος/Παῦλος…)

**Livrable :** dataset unifié NT grec en CoNLL-U étendu avec features morpho + coréférence partielle.

---

### Étape 2 — Module 0+1 : NLP de base + NER narratif (semaines 4–7)

**Objectif :** obtenir un pipeline fiable de POS/morphologie/NER sur le NT.

**Actions :**
- Charger odyCy (`grc_odycy_joint_trf`) comme base
- Fine-tuner sur le NT spécifiquement (koinè vs grec classique) à partir du corpus PROIEL NT
- Développer un composant spaCy custom **`GrcNER`** :
  - Entités personnages (PER) : noms propres + épithètes narratives ("le fils de l'homme", "le Seigneur")
  - Lieux (LOC/GPE), groupes (ORG : "les Pharisiens", "les disciples")
- Construire le **lexique NT** des noms propres (Strong's numbers + lemmes)

**Métriques cibles :** F1 NER > 85% sur NT test set.

---

### Étape 3 — Module 2 : Clustering de noms de personnages (semaines 8–10)

**Objectif :** regrouper toutes les variantes nominales d'un même personnage en une entité canonique.

**Actions :**
- Règles linguistiques : même lemme → même entité
- Graphe de cooccurrence : si "Σίμων" et "Πέτρος" apparaissent dans la même clause avec identification explicite (Jean 1:42), les relier
- Dictionnaire manuel des équivalences pour les personnages NT (liste des ~50 personnages principaux)
- Gestion des homonymes (deux "Jacques", deux "Marie"…) : désambiguïsation par contexte narratif (livre, chapitre)

**Livrable :** `CharacterCluster` — dictionnaire personnage canonique ↔ toutes ses mentions.

---

### Étape 4 — Module 3 : Résolution de coréférence (semaines 11–18)

C'est le module central et le plus complexe. Il se décompose en trois sous-modules.

#### 4a. Coréférence pronominale explicite (règles morphologiques)

Pour un pronom anaphorique (αὐτόν, αὐτῷ, αὐτοῖς…) :
1. Extraire ses traits morphologiques : genre, nombre, cas (depuis odyCy)
2. Chercher en arrière dans une fenêtre de N tokens/phrases les entités PER compatibles en genre+nombre
3. Scorer les candidats (distance, saillance narrative, sujet grammatical)
4. Assigner l'antécédent le plus probable

→ Approche basée sur des règles + heuristiques = bonne baseline (~70% F1 estimé)

#### 4b. Résolution des sujets implicites (pro-drop)

C'est la vraie innovation par rapport à BookNLP :
- Détecter les verbes sans sujet syntaxique explicite (via dépendances odyCy)
- Inférer le sujet à partir de :
  - La morphologie verbale (personne, nombre)
  - Le sujet de la clause précédente (continuité narrative)
  - Les marqueurs de changement de sujet (δέ, τότε, participes circonstanciels)
  - Le contexte discursif (qui parlait en dernier ?)
- Fine-tuner Ancient Greek BERT sur des exemples annotés manuellement (~500 phrases du NT)

#### 4c. Groupes nominaux définis

- "ὁ διδάσκαλος" → Jésus si contexte l'indique
- Règles + modèle de classification

**Livrable :** composant `GrcCoref` ajoutant `._.coref_cluster` à chaque token/span spaCy.

---

### Étape 5 — Modules 4+5 : Discours + Actes narratifs (semaines 19–23)

#### Module 4 — Attribution des discours directs

- Détecter les guillemets / deux-points narratifs (ponctuation du texte édité)
- Identifier le verbe dicendi le plus proche
- Résoudre l'agent du verbe dicendi via le module 3
- Cas particulier : discours indirect, discours en chaîne

**Output :**
```json
{
  "quote": "Ποῦ ἐστιν ὁ τεχθεὶς βασιλεὺς τῶν Ἰουδαίων;",
  "speaker_id": "MAGOI",
  "speaker_mention": "λέγοντες",
  "ref": "Matt 2:2"
}
```

#### Module 5 — Actes narratifs par personnage

- Pour chaque verbe fini, extraire : agent (sujet résolu), patient (objet résolu), verbe (lemme)
- Agréger par personnage canonique
- Classifier les verbes : parole / mouvement / action physique / cognition

**Output JSON par personnage :**
```json
{
  "character": "IESOUS",
  "canonical_name": "Ἰησοῦς",
  "mentions": 942,
  "as_agent": ["εἶπεν×312", "ἦλθεν×45", "ἐθεράπευσεν×28", ...],
  "as_patient": ["ἐβάπτισεν×1", "ἐπηρώτησαν×23", ...]
}
```

---

### Étape 6 — Packaging, interface et exports (semaines 24–26)

**API de la bibliothèque :**

```python
from grcnlp import GrcNLP

nlp = GrcNLP(backend="odycy")  # ou "textfabric"

# Traitement d'un texte
result = nlp.process(greek_text, book_id="john")

# Accès aux résultats
result.entity_chains()       # toutes les chaînes d'entités
result.character_profile("IESOUS")  # actes, discours, mentions
result.coreference_html()   # visualisation HTML annotée
result.to_conllu()          # export CoNLL-U étendu
result.to_textfabric()      # export en features TF
```

**Exports :**
- `.entities` — tableau des entités (id, type, mentions, chaîne)
- `.tokens` — tableau token-level (POS, morpho, entité, coref_id)
- `.quotes` — discours directs + locuteur
- `.narrativeacts` — actes narratifs par personnage
- `.html` — visualisation annotée interactive

---

## PHASE 4 — Évaluation et validation

### Métriques à utiliser

| Module | Métrique |
|---|---|
| NER | F1 (entités complètes) |
| Coréférence | MUC, B³, CEAFₑ (Avg. F1) |
| Attribution discours | B-Cubed precision/recall |
| Pro-drop | Accuracy sur set annoté manuellement |

### Corpus d'évaluation

- Utiliser 10% du NT comme test set (Épître aux Romains + Évangile de Jean ch. 1–5)
- Annoter manuellement ~200 phrases pour le pro-drop (annotation manuelle par un helléniste)

---

## PHASE 5 — Risques et mitigations

| Risque | Probabilité | Mitigation |
|---|---|---|
| Pro-drop irrésoluble sans annotation manuelle massive | Haute | Commencer par une baseline à règles, améliorer itérativement |
| Corpus d'entraînement trop petit pour fine-tuning | Moyenne | Augmentation via LXX (Septante) + littérature grecque proche NT |
| Homonymes de personnages non résolus | Moyenne | Dictionnaire manuel des 50 personnages NT, désambiguïsation par livre |
| Performance odyCy faible sur koinè vs grec classique | Basse | PROIEL est koinè — fine-tuning spécifique NT réaliste |
| Dépendance à Ancient Greek BERT (maintenance) | Basse | Fallback sur modèle tok2vec odyCy |

---

## Résumé exécutif

| | Détail |
|---|---|
| **Nom proposé** | `grcnlp` / `ntcoref` |
| **Faisabilité globale** | ✅ Oui, en 6 étapes sur ~6 mois |
| **Backend recommandé** | Hybride : odyCy (traitement) + Text-Fabric (données NT) |
| **Innovation clé** | Module pro-drop (résolution sujets implicites) — absent de BookNLP |
| **Point de départ** | PROIEL NT (coréférence partielle) + N1904-TF (morphologie) |
| **Dépendance critique** | Ancient Greek BERT + odyCy `grc_odycy_joint_trf` |
| **Livrable final** | Bibliothèque Python open-source, compatible spaCy et Text-Fabric |
