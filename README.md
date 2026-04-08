# Grec ancien NT — Résolution de coréférence

Un projet de recherche qui applique le traitement automatique du langage naturel (TALN) au Nouveau Testament grec, avec un objectif unique : **identifier automatiquement qui est qui dans un passage.**

Quand on lit un texte comme l'Évangile de Marc en grec, on tombe souvent sur des phrases comme :

> *ἀπεκρίθη καὶ εἶπεν αὐτοῖς· — "Et répondant, il leur dit..."*

Pour un lecteur humain, le contexte permet de savoir qui parle. Pour une machine, c'est un défi à trois niveaux :

1. **Le sujet est absent** — en grec, il est absorbé dans la terminaison verbale (*pro-drop*)
2. **Les pronoms sont ambigus** — à qui renvoie ce `αὐτός` ("il/lui") ?
3. **Un même personnage a plusieurs noms** — Σίμων, Πέτρος et Κηφᾶς désignent la même personne

Ce projet construit les outils pour résoudre ces énigmes automatiquement.

---

## État du projet (Avril 2026)

### Précision actuelle
- **Précision initiale (LLM) :** 29.7% sur gold PROIEL
- **Précision règles :** 24.8%
- **Benchmark SOTA anglais (CoNLL) :** ~80-85%
- **Benchmark grec ancien :** ❌ N'EXISTE PAS

### Objectif
**55-60% de précision** — Ce serait pioneering work, car aucun benchmark public n'existe pour la résolution de coréférence sur le grec ancien.

> Justification détaillée : [`project/docs/TARGET_JUSTIFICATION.md`](./project/docs/TARGET_JUSTIFICATION.md)

### Approche
Architecture two-stage inspirée de Celano (2023) :
1. Règles de haute précision pour les cas clairs (~87%)
2. Réseau neuronal pour les cas ambigus (~13%)

---

## De quoi parle-t-on ? Les notions clés

### Traitement automatique du langage naturel (TALN / NLP)

Le **traitement automatique du langage naturel** (en anglais *Natural Language Processing*, NLP) désigne l'ensemble des techniques informatiques qui permettent à une machine d'analyser, de comprendre et de manipuler du texte humain.

Concrètement, cela recouvre des tâches comme :
- **tokenisation** — découper un texte en unités (mots, ponctuations)
- **analyse morphologique** — reconnaître le genre, le nombre, le cas, la personne d'un mot
- **analyse syntaxique** — identifier la fonction de chaque mot dans la phrase (sujet, objet, etc.)
- **reconnaissance d'entités nommées** (NER — voir ci-dessous)
- **résolution de coréférence** — le cœur de ce projet

### Reconnaissance d'entités nommées (NER)

La **NER** (*Named Entity Recognition*) consiste à repérer automatiquement dans un texte les noms propres et à les classer par catégorie : personnes (`PER`), lieux (`LOC`), organisations (`ORG`), etc.

Exemple en grec du NT :

```
ἦλθεν  Ἰησοῦς  εἰς  τὴν  Γαλιλαίαν
          PER             LOC
```

La NER est un prérequis ici : avant de résoudre *qui fait quoi*, il faut d'abord savoir *qui est mentionné*.

### Coréférence

La **coréférence** désigne le fait que plusieurs expressions différentes dans un texte renvoient au même référent dans le monde réel.

Exemple en français :
> *Pierre entra dans la salle. **Il** s'assit. **Le disciple** prit la parole.*

`Pierre` / `Il` / `Le disciple` → trois expressions, un seul personnage.

La **résolution de coréférence** est la tâche qui consiste à regrouper automatiquement ces expressions en **chaînes de coréférence** — une chaîne par entité.

### Désambiguïsation des entités nommées

La difficulté vient du fait que plusieurs personnages peuvent porter le même nom, ou qu'un même personnage peut être désigné de plusieurs façons différentes. C'est le problème de la **désambiguïsation**.

Dans le NT grec, cela prend des formes concrètes :

| Problème | Exemple |
|---|---|
| Un personnage, plusieurs noms | Σίμων / Πέτρος / Κηφᾶς → toujours Pierre |
| Plusieurs personnages, même nom | Marie (mère de Jésus), Marie de Magdala, Marie de Béthanie |
| Jacques × 2 | Jacques fils de Zébédée, Jacques fils d'Alphée |
| Épithètes indirectes | `ὁ κύριος` (le Seigneur), `ὁ διδάσκαλος` (le Maître) → Jésus selon le contexte |

Pour lever ces ambiguïtés, le système doit combiner : correspondance de lemmes, dictionnaire d'alias, contexte narratif, et parfois position dans le livre.

### Le problème spécifique du grec ancien : le *pro-drop*

Le grec koinè (langue du NT) est une langue dite **pro-drop** (*pronoun dropping*) : le sujet d'un verbe n'est pas toujours exprimé explicitement — il est encodé dans la terminaison verbale.

Exemple :

```
ἀπεκρίθη καὶ εἶπεν αὐτοῖς·
```
*"Il répondit et leur dit :"*

Le sujet (`ἐκεῖνος` / `αὐτός` / un nom propre) est absent. La terminaison verbale (`-θη`, 3e personne singulier aoriste passif) indique qu'il s'agit d'un singulier masculin, mais ne dit pas *qui*. Pour résoudre ce sujet implicite, il faut :

1. Regarder la morphologie verbale (personne + nombre)
2. Identifier le sujet de la clause précédente
3. Détecter les marqueurs de rupture narrative (`δέ`, `τότε`, participes circonstanciels) qui signalent un changement de personnage

C'est le problème le plus difficile du projet, et celui qui le distingue le plus des outils NLP construits pour les langues modernes.

---

## Ce que le système produira (à terme)

Pour un passage du NT grec — quelques versets, un chapitre, ou un livre entier — le système vise à produire :

- **Chaînes d'entités** — toutes les mentions d'un même personnage regroupées
  ex. `Ἰησοῦς` / `αὐτός` / `ὁ διδάσκαλος` / sujet implicite → `IESOUS`
- **Attribution des discours** — qui dit quoi dans les dialogues directs
- **Actes narratifs** — qui fait quoi à qui, prédicat par prédicat

---

## Ce qui existe aujourd'hui

L'architecture principale de coréférence est opérationnelle jusqu'au traitement des pronoms et groupes nominaux définis (Sprints 0, 1, 2A, 2B achevés).

Dans le dossier `scripts/`, vous trouverez notamment :
- `parse_proiel.py` — Extraction complète du NT annoté depuis PROIEL vers un CSV structuré.
- `build_lexicons.py` — Création des dictionnaires linguistiques du projet (alias, pronoms, verba_dicendi).
- `sprint1_mention_detector_final.py` — Pipeline d'extraction des mentions (combinant `Trankit`, `UGARIT` pour le NER, et `LOGION` pour la détection d'erreurs OCR/scribales).
- `sprint2_full_pipeline.py` — Algorithme de clustering des personnages et de résolution des pronoms par calcul de score (morphologie + distance + saillance syntaxique).

### Scripts de résolution Pro-Drop (Sprint 2C)

Ces scripts implémentent la résolution des sujets implicites (pro-drop) en grec ancien. L'expérience a démontré que l'approche hybride (règles + LLM) surpasse les règles seules de +19.9% sur les cas difficiles.

#### Pipeline de génération des données

| Script | Description |
|--------|-------------|
| `generate_gold_samples.py` | Extrait un corpus gold depuis PROIEL (Mark 1:1-4:26 par défaut) |
| `extract_prodrop_instances.py` | Identifie les verbes pro-drop (3e personne, sans sujet explicite) |
| `build_prodrop_evaluation_dataset.py` | Classe les instances par niveau de difficulté (1/2/3) et ajoute le contexte narratif |

**Commandes :**
```bash
source .venv/bin/activate

# 1. Générer le corpus gold
python scripts/generate_gold_samples.py

# 2. Extraire les instances pro-drop
python scripts/extract_prodrop_instances.py

# 3. Construire le dataset d'évaluation avec niveaux de difficulté
python scripts/build_prodrop_evaluation_dataset.py
```

**Entrée :** Fichiers PROIEL (`.conll` ou `.conllu`)
**Sortie :** `project/data/experiments/sprint2c/prodrop_evaluation_dataset.json`

#### Évaluation et analyse

| Script | Description |
|--------|-------------|
| `prodrop_rules_evaluator.py` | Baseline : résolution par règles seules (heuristiques morphologiques) |
| `prodrop_llm_evaluator.py` | Évaluation avec Gemini 3.1 Pro (nécessite clé API dans `.env`) |
| `prodrop_analysis_report.py` | Génère le rapport d'analyse comparatif et les métriques |

**Commandes :**
```bash
# Option A : Règles seules (rapide, sans API key)
python scripts/prodrop_rules_evaluator.py

# Option B : LLM Gemini (requiert clé API dans .env)
python scripts/prodrop_llm_evaluator.py

# Option C : Rapport d'analyse (après avoir exécuté les deux ci-dessus)
python scripts/prodrop_analysis_report.py
```

**Sortie :**
- `rules_results.json` — Prédictions du système par règles
- `llm_results.json` — Prédictions du système LLM
- `analysis_report.json` — Métriques par niveau de difficulté
- `FINAL_REPORT.md` — Rapport complet avec décision d'architecture

#### Résolveur hybride (production)

| Script | Description |
|--------|-------------|
| `prodrop_hybrid_resolver.py` | Résolveur hybride combinant règles (Level 1) + LLM (Level 2+3) |

**Commande :**
```bash
python scripts/prodrop_hybrid_resolver.py
```

**Architecture :**
```
Instance pro-drop
    │
    ├── Level 1 (1 entité compatible) → RÈGLES (100% accuracy)
    │
    └── Level 2+3 (2+ entités) → LLM Gemini
                                      │
                                      ├── LLM réussit → Utiliser prédiction LLM
                                      └── LLM échoue → Fallback vers règles
```

#### Interprétation des niveaux de difficulté

| Niveau | Critère | Stratégie | Performance |
|--------|---------|-----------|-------------|
| **Level 1** (Clair) | 1 seule entité compatible dans la fenêtre | Règles | 100% |
| **Level 2** (Ambigu) | 2+ entités compatibles | LLM recommandé | +10.5% vs règles |
| **Level 3** (Complexe) | δέ adversatif / τότε / génitif absolu | LLM + fallback | Variable |

#### Format de sortie JSON

```json
{
  "verse_ref": "MARK 1.7",
  "sentence_text": "οὗτος ἦν ὁ βαπτίζων...",
  "verb_form": "ἐκήρυσσεν",
  "verb_lemma": "κηρύσσω",
  "entities_in_window": [
    {"form": "Ἰωάννης", "lemma": "Ἰωάννης"}
  ],
  "narrative_markers": {
    "delta_adversative": false,
    "tote_shift": false,
    "genitive_absolute": false
  },
  "difficulty_level": 1,
  "predicted_entity": "IOANNES",
  "confidence": "high",
  "method": "RULES"
}
```

#### Décision d'architecture (Sprint 2C)

| Métrique | Règles | LLM Gemini |
|----------|--------|------------|
| Overall (PROIEL gold) | 24.8% | 29.7% |

**Note:** Évaluation sur 101 instances avec gold PROIEL (avril 2026).  
**Découverte:** AUCUN benchmark SOTA n'existe pour le grec ancien.  
**Nouvelle cible:** 55-60% — voir [`project/docs/TARGET_JUSTIFICATION.md`](./project/docs/TARGET_JUSTIFICATION.md)

> ⚠️ **Mise à jour avril 2026:** Cette architecture a été dépassée.  
> Voir [`project/docs/SPRINT2C_POSTMORTEM.md`](./project/docs/SPRINT2C_POSTMORTEM.md) et la nouvelle architecture two-stage dans [`project/docs/SPRINT3A_PLAN.md`](./project/docs/SPRINT3A_PLAN.md).

---

## Pipeline technique SOTA (State of the Art)

L'architecture ML du projet repose sur les publications les plus récentes (2024-2025) en NLP pour le grec ancien :

```
Texte grec NT (péricope / chapitre / livre)
    → Détection des corruptions textuelles   (modèle LOGION character-level, Princeton)
    → Extraction des arbres de dépendances   (modèle Trankit Biaffine, SOTA Koinè)
    → Lemmatisation experte                  (modèle GreTa, Leipzig)
    → NER : Extraction entités (PER/LOC)     (modèle UGARIT/grc-ner-xlmr, LT4HALA 2024)
    → Regroupement des personnages           (Simon/Pierre/Céphas → même entité canonique)
    → Résolution pronominale                 (règles d'accord morphologique)
    → Résolution des sujets implicites       (LLM Instruct-tuning / Feedforward sur LOGION)
    → Attribution des discours               (verbes de parole + agent résolu)
    → Sortie : JSON structuré + HTML annoté
```

---

## Installation

### Prérequis

- Python 3.12+ (recommandé ; Python 3.9+ fonctionne aussi)
- macOS/Linux avec `python3` ou `python3.12`
- Clé API Gemini dans le fichier `.env` (optionnel, requis uniquement pour `prodrop_llm_evaluator.py` et `prodrop_hybrid_resolver.py`)

Les données d'entraînement/audit peuvent être téléchargées via le dépôt [PROIEL treebank](https://github.com/proiel/proiel-treebank).

### Créer l'environnement virtuel

```bash
# 1. Se placer à la racine du projet
cd ancient-greek-nt-coref

# 2. Créer l'environnement virtuel avec Python 3.12
python3.12 -m venv .venv

# 3. L'activer (à faire à chaque nouvelle session)
source .venv/bin/activate

# 4. Installer les dépendances (inclut NLP + LLM)
pip install -r requirements.txt

# 5. (Optionnel) Définir la clé API Gemini dans .env pour les scripts LLM
cp .env.example .env  # puis éditer .env avec votre clé
```

### Vérifier l'installation

```bash
source .venv/bin/activate
python scripts/sprint2_full_pipeline.py
```

### Désactiver l'environnement

```bash
deactivate
```

---

## Sources de données

| Source | Description | Usage |
|---|---|---|
| [PROIEL treebank](https://github.com/proiel/proiel-treebank) | NT grec avec annotation syntaxique et coréférence partielle | Données d'entraînement, baseline d'évaluation |
| [N1904-TF](https://github.com/ETCBC/nestle1904) | Nestle 1904 en format Text-Fabric | Traits morphologiques (genre, nombre, cas, lemme) |
| [odyCy](https://github.com/explosion/spaCy) | Modèle NLP pour le grec ancien (`grc_odycy_joint_trf`) | Tokenisation, POS, analyse syntaxique |

---

## Références bibliographiques

La bibliographie complète du projet, avec les citations au format ACL Anthology et les résumés des publications clés, est disponible dans :

➡️ [`project/docs/BIBLIOGRAPHY.md`](./project/docs/BIBLIOGRAPHY.md)

---

## Avancement

| Sprint | Objectif | État |
|---|---|---|
| Sprint 0 | Audit des données, lexiques, annotations gold | ✅ Terminé |
| Sprint 1 | Pipeline de base + NER minimal (Trankit, LOGION, UGARIT) | ✅ Terminé |
| Sprint 2A | Clustering de personnages (Dictionnaire d'alias) | ✅ Terminé |
| Sprint 2B | Règles de coréférence pronominale (Morphologie) | ✅ Terminé |
| Sprint 2C | Résolution des sujets implicites (pro-drop) | 🔄 Pivot (avril 2026) |
| Sprint 3 | Attribution des discours + actes narratifs | Planifié |
| Sprint 4 | API, Granularités, Exports | Planifié |

---

## Pour qui, pourquoi ?

Ce projet peut intéresser :

- les **chercheurs en humanités numériques** — pour analyser les réseaux de personnages ou comparer la façon dont différents évangélistes présentent un même protagoniste
- les **hellénistes et exégètes** — pour naviguer dans le texte grec de façon augmentée, personnage par personnage
- les **développeurs NLP** — comme cas d'étude sur une langue morphologiquement riche et peu dotée en ressources annotées

Il ne présuppose aucune position théologique.

Le plan d'action détaillé (architecture, sprints, protocoles d'évaluation) est disponible dans [`project/Plan_Actions.md`](./project/Plan_Actions.md).

---

## Contexte technique

L'approche privilégie une **architecture hybride** : la syntaxe et la morphologie du grec koinè fournissent des indices déterministes puissants (règles et dictionnaires pour 80% des tâches). Le **Machine Learning (Transformers, Character-Level Embeddings, et Instruct-Tuning)** n'intervient que là où les règles échouent de par la complexité sémantique (détection d'erreurs OCR, extraction NER, verbes pro-drop ambigus).

Ce projet s'inscrit dans une démarche d'humanités numériques appliquée aux textes antiques.
