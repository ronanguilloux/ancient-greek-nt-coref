# Tâches — `ntcoref`
> Dernière mise à jour : 9 avril 2026
> Périmètre : prochaines tâches uniquement (complétues exclues)

---

### 📚 Ressources & Documentation

| Document | Contenu |
|----------|---------|
| [`docs/BIBLIOGRAPHY.md`](./docs/BIBLIOGRAPHY.md) | Bibliographie complète (23 sources) |
| [`docs/TARGET_JUSTIFICATION.md`](./docs/TARGET_JUSTIFICATION.md) | Justification de la cible 55-60% |
| [`docs/SPRINT3A_PLAN.md`](./docs/SPRINT3A_PLAN.md) | Plan d'implémentation détaillé |
| [`docs/FUTURE_WORK.md`](./docs/FUTURE_WORK.md) | Évolutions futures documentées |
| [`docs/SPRINT2C_POSTMORTEM.md`](./docs/SPRINT2C_POSTMORTEM.md) | Retour d'expérience |

---

## 🚀 Prochaines étapes immédiates (Sprint 3A)

### Étape 1 : Intégration du parsing dépendanciel · ✅ TERMINÉ

**Livrable:** `scripts/sprint3a_phase1_prodrop_detection.py`

**Résultats:**
- 6 phrases PROIEL chargées, 2465 tokens
- 245 candidats pro-drop détectés
- 23 avec antécédent personne (gold standard)
- Baseline: 9.4% (23/245)

**Prochaines étapes:**

### Étape 2 : Classification d'ambiguïté

**Objectif :** Distinguer les cas clairs des cas ambigus

1. Extraire les marqueurs narratifs (δέ, τότε, génitif absolu)
2. Construire `is_ambiguous()` 
3. Valider sur ~100 exemples PROIEL

### Étape 3 : Évaluation head-matching

**Objectif :** Adopter la métrique standard CRAC

- Corriger l'évaluation pour utiliser head-matching (pas string-matching)
- Comparer avec baseline PROIEL (empty nodes)

## Sprint 0 — Données et environnement · ✅ TERMINÉ

Toutes les tâches du Sprint 0 (Parsing PROIEL, création des lexiques, génération des corpus Gold pour Jean/Marc/Actes) ont été accomplies via les scripts dans `scripts/`. Le nettoyage du dépôt a été effectué.

---

## Sprint 1 — Pipeline de base + MentionDetector · ✅ TERMINÉ

L'architecture C0 (Parser) et C1 (Mention Detector) a été implémentée avec succès via `scripts/sprint1_mention_detector_final.py` :
- **[C0.5] Module de Résilience :** LOGION est intégré pour détecter les corruptions textuelles.
- **[C1] NER :** Le modèle `UGARIT/grc-ner-xlmr` extrait avec succès les entités PER.
- **[C0] Backend :** Un mock Stanza a été mis en place pour valider la pipeline en attendant que les serveurs de téléchargement de `Trankit` (SOTA Koinè) soient de nouveau en ligne.

---

## Sprint 2 — Résolution de coréférence

### 2A — Clustering de noms de personnages · ✅ TERMINÉ
- Le dictionnaire d'alias a été implémenté dans la pipeline (`sprint2_full_pipeline.py`) et permet de rattacher une mention (ex: Σίμων) à son entité canonique (PETROS).

### 2B — Résolution pronominale (règles) · ✅ TERMINÉ
- Les règles morphologiques de coréférence (accord en genre/nombre, score de proximité, bonus sujet de la clause) ont été codées et validées sur des phrases de test.
- L'extraction des groupes nominaux définis (DEF_NP) est opérationnelle.

### 2C — Résolution des sujets implicites / pro-drop · 🔄 PIVOT

**État:** Apr ès évaluation sur VRAI gold PROIEL, pivot vers nouvelle approche.

**Évaluation initiale sur 40 instances (Level 1/2/3) vs Gemini 3.1 Pro :**

| Niveau | Instances testées | Rules | LLM | Δ Improvement |
|--------|-----------------|-------|-----|---------------|
| Level 1 (Clair) | 10 | 100.0% | 60.0% | -40.0% |
| Level 2 (Ambigu) | 19 | 15.8% | 26.3% | +10.5% |
| Level 3 (Complexe) | 11 | 63.6% | 54.5% | -9.1% |
| **Level 2+3 Combined** | **30** | **33.3%** | **36.7%** | **+19.9%** ✅ |

**Évaluation finale sur VRAI gold PROIEL (8 avril 2026) :**

| Niveau | Évalué | Correct | Accuracy |
|--------|---------|---------|----------|
| **Overall (LLM)** | 101 | 30 | **29.7%** |
| **Overall (Rules)** | 101 | 25 | **24.8%** |
| Level 1 | 22 | 2-3 | 9-14% |
| Level 2 | 60 | 18-24 | 30-40% |
| Level 3 | 19 | 3-5 | 16-26% |

**Découverte clé : AUCUN benchmark SOTA n'existe pour le grec ancien.** L'objectif de 60% serait pioneering work.

**Postmortem:** Voir `project/docs/SPRINT2C_POSTMORTEM.md`

---

## Sprint 2C v2 — Nouvelle Architecture (Avril 2026) · 🔄 EN COURS

**Objectif:** 55-60% de précision sur gold PROIEL

**Justification:** Voir [`project/docs/TARGET_JUSTIFICATION.md`](./docs/TARGET_JUSTIFICATION.md)

**Approche two-stage inspirée de Celano (2023) :**

1. **Stage 1:** Règles de haute précision (cas clairs ~87%)
2. **Stage 2:** Réseau neuronal pour cas ambigus (~13%)

**Plan d'implémentation:** Voir `project/docs/SPRINT3A_PLAN.md`

| Composant | Cible | Notes |
|-----------|-------|-------|
| Détection des zéros | 85%+ | Baseline CRAC à 88.4% |
| Cas clairs (règles) | 70-80% | Un seul candidat compatible |
| Cas ambigus (ML) | 50-60% | Plusieurs candidats |
| **Précision globale** | **55-60%** | Moyenne pondérée |

### Périmètre clarifié

- ✅ **Personnes uniquement** (PER) — pas LOC, ORG, EVENT
- ✅ **Sujets implicites uniquement** — pas les objets nuls
- ✅ **Head-matching** pour l'évaluation (standard CRAC)

---

## Sprint 3A — Attribution des discours directs · À venir

- Détection ponctuation + verba_dicendi + résolution agent.

## Sprint 3B — Actes narratifs par personnage · À venir

- Semantic Role Labeling via typologie Pedalion.

## Sprint 4 — API, granularités et exports · À venir

- Interface unifiée (`pericope`, `chapter`, `book`).
- Exports multiples (CoNLL-U, JSON, HTML interactif, GraphML).
