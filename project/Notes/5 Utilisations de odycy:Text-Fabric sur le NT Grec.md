#5 Utilisations de odycy/Text-Fabric sur le NT Grec

Cinq usages documentés, avec les ressources associées, allant au-delà du simple tokenisation/POS-tagging.

---

## 1. **BookNLP — Coreference & cartographie des personnages**
**Outil :** BookNLP (Bamman et al., Berkeley NLP)
**Usage :** Résolution de coréférence à l'échelle du roman entier, identification des chaînes d'entités, attribution des actes narratifs (qui dit quoi, qui fait quoi).
**Pourquoi c'est profond :** Permet de reconstruire les réseaux sociaux implicites dans un roman (ex. : qui interagit avec qui, centralité des personnages).
**Documentation :** [github.com/booknlp/booknlp](https://github.com/booknlp/booknlp) + article Bamman, Underwood & Smith (ACL 2014).

---

## 2. **odyCy — Analyse morphosyntaxique de textes grecs anciens**
**Outil :** odyCy (pipeline spaCy pour le grec ancien, développé par Jacobo Myerston)
**Usage :** Lemmatisation, POS-tagging et parsing de dépendances sur des textes homériques ou attiques, avec modèles entraînés sur l'Universal Dependencies Greek.
**Pourquoi c'est profond :** Ouvre la stylométrie computationnelle à des corpus sans ressources NLP robustes préexistantes ; permet par exemple de comparer les registres épique vs tragique.
**Documentation :** [github.com/explosion/spacy-models](https://spacy.io/models/el) + travaux du projet **KELP** (Koine & Epic Language Processing).

---

## 3. **LitBank — Annotation multi-couches pour la compréhension narrative**
**Outil :** LitBank (Bamman, Popat & Yao, 2019) — corpus de 100 romans anglais annotés, compatible spaCy
**Usage :** Entités, événements, coréférence, cadres sémantiques — toutes les couches nécessaires à une compréhension *narrative* fine.
**Pourquoi c'est profond :** Sert de benchmark pour entraîner ou évaluer des modèles sur la *spécificité* du texte littéraire (temps narratif, focalisateur, ellipse).
**Documentation :** [github.com/dbamman/litbank](https://github.com/dbamman/litbank) + LREC 2019.

---

## 4. **Analyse de la complexité syntaxique comme marqueur stylistique**
**Outil :** spaCy (dep parser) + scripts maison
**Usage :** Extraire des métriques de complexité (longueur moyenne des arcs de dépendance, profondeur des arbres, proportion de subordonnées) pour comparer des styles (Proust vs Camus, ou évolution d'un auteur).
**Pourquoi c'est profond :** La *Dependency Distance* (DD) est un corrélat de la charge cognitive et a été appliquée à des corpus littéraires en français, chinois et anglais.
**Documentation :** Liu (2008) *Dependency distance as a metric of language comprehension difficulty* ; pour le français littéraire, voir les travaux du projet **OBVIL** (Sorbonne) utilisant spaCy fr.

---

## 5. **Détection des arcs émotionnels (Emotional Arc)**
**Outil :** spaCy (preprocessing) + lexiques NRC/EmoLex ou modèles transformer fine-tunés
**Usage :** Segmenter un texte en fenêtres, projeter chaque segment dans un espace émotionnel, visualiser la courbe affective sur l'ensemble du récit.
**Pourquoi c'est profond :** Reagan et al. (2016, *EPJ Data Science*) ont identifié 6 archétypes narratifs universels via cette méthode sur Project Gutenberg. spaCy y joue le rôle de pipeline de nettoyage/lemmatisation.
**Documentation :** Reagan et al. (2016) ; implémentation spaCy documentée dans le projet [**syuzhet**](https://github.com/mjockers/syuzhet) (R) et ses portages Python.

---

**Point de tension à explorer pour ton projet :**
Ces approches supposent toutes que les unités linguistiques standard (token, lemme, entité) correspondent à des unités *narratives* pertinentes — ce qui n'est pas toujours le cas (ironie, narrateur non fiable, polyphonie). C'est là que la couche d'interprétation humaine reste irremplaçable.

