# Tâches — `ntcoref`
> Dernière mise à jour : 8 avril 2026
> Périmètre : prochaines tâches uniquement (complétées exclues)

---

### 📚 Ressources prioritaires à explorer (Veille technique)

Voir la [Bibliographie](project/Recherches/Bibliographie.md)

## Sprint 0 — Données et environnement · ✅ TERMINÉ

Toutes les tâches du Sprint 0 (Parsing PROIEL, création des lexiques, génération des corpus Gold pour Jean/Marc/Actes) ont été accomplies via les scripts dans `scripts/`. Le nettoyage du dépôt a été effectué.

---

## Sprint 1 — Pipeline de base + MentionDetector (semaines 4–7) · ✅ TERMINÉ

L'architecture C0 (Parser) et C1 (Mention Detector) a été implémentée avec succès via `scripts/sprint1_mention_detector_final.py` :
- **[C0.5] Module de Résilience :** LOGION est intégré pour détecter les corruptions textuelles.
- **[C1] NER :** Le modèle `UGARIT/grc-ner-xlmr` extrait avec succès les entités PER.
- **[C0] Backend :** Un mock Stanza a été mis en place pour valider la pipeline en attendant que les serveurs de téléchargement de `Trankit` (SOTA Koinè) soient de nouveau en ligne.

---

## Sprint 2 — Résolution de coréférence (semaines 8–15)

### 2A — Clustering de noms de personnages · ✅ TERMINÉ
- Le dictionnaire d'alias a été implémenté dans la pipeline (`sprint2_full_pipeline.py`) et permet de rattacher une mention (ex: Σίμων) à son entité canonique (PETROS).

### 2B — Résolution pronominale (règles) · ✅ TERMINÉ
- Les règles morphologiques de coréférence (accord en genre/nombre, score de proximité, bonus sujet de la clause) ont été codées et validées sur des phrases de test.
- L'extraction des groupes nominaux définis (DEF_NP) est opérationnelle.

### 2C — Résolution des sujets implicites / pro-drop (semaines 12–15) · 🔄 PIVOT

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

**Objectif:** 60% de précision sur gold PROIEL

**Approche two-stage inspirée de Celano (2023) :**

1. **Stage 1:** Règles de haute précision (cas clairs ~87%)
2. **Stage 2:** Réseau neuronal pour cas ambigus (~13%)

**Plan d'implémentation:** Voir `project/docs/SPRINT3A_PLAN.md`

| Semaine | Tâche | Livrable |
|---------|-------|----------|
| 1 | Intégration parsing dépendanciel | Candidate detector |
| 2 | Classificateur d'ambiguïté | `is_ambiguous()` |
| 3 | Modèle neuronal | Training loop |
| 4 | Caractère-level (LOGION/CNN) | Embeddings |
| 5 | Pipeline complet | Script intégré |
| 6 | Évaluation | Rapport 60% |

---

## Sprint 3A — Attribution des discours directs (semaines 16–20) · À venir

- Détection ponctuation + verba_dicendi + résolution agent.

## Sprint 3B — Actes narratifs par personnage (semaines 18–20) · À venir

- Semantic Role Labeling via typologie Pedalion.

## Sprint 4 — API, granularités et exports (semaines 21–24) · À venir

- Interface unifiée (`pericope`, `chapter`, `book`).
- Exports multiples (CoNLL-U, JSON, HTML interactif, GraphML).
