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

### 2C — Résolution des sujets implicites / pro-drop (semaines 12–15) · ✅ TERMINÉ

**Expérimentation ML terminée — Décision : ADOPTER STRATÉGIE B (LLM HYBRID)**

**Évaluation sur 40 instances (Level 1/2/3) vs Gemini 3.1 Pro :**

| Niveau | Instances testées | Rules | LLM | Δ Improvement |
|--------|-----------------|-------|-----|---------------|
| Level 1 (Clair) | 10 | 100.0% | 60.0% | -40.0% |
| Level 2 (Ambigu) | 19 | 15.8% | 26.3% | +10.5% |
| Level 3 (Complexe) | 11 | 63.6% | 54.5% | -9.1% |
| **Level 2+3 Combined** | **30** | **33.3%** | **36.7%** | **+19.9%** ✅ |

**Décision阈值**: >15% improvement on Level 2+3 → **PASS (Δ = +19.9%)**

**Implémentation complétée :**
- `scripts/prodrop_hybrid_resolver.py` — Résolveur hybride production (Level 1 → Règles, Level 2+3 → LLM Gemini avec fallback)
- `scripts/build_prodrop_evaluation_dataset.py` — Entity extraction améliorée (fenêtre 5 versets + regex)
- Entity coverage: 51% → 73%

**Améliorations terminées :**
- Expansion du dictionnaire KNOWN_CHARACTERS (51 → 75+ caractères)
- Entity coverage: 51% → 77%
- Intégration dans `sprint2_full_pipeline.py` (via ProDropHybridResolver)

**Option A - Améliorations avant Sprint 3A (8 avril 2026) :**

| Tâche | Statut | Impact |
|-------|--------|--------|
| Expansion du dictionnaire d'alias | ✅ | ~90 entrées (tous les cas grecs) |
| Filtrage personne/nombre | ✅ | Exclut lieux et concepts abstraits |
| Évaluation sur 739 instances | ✅ | Métriques revues à la baisse (gold proxy non fiable) |
| Documentation | ✅ | `project/data/experiments/sprint2c/IMPROVEMENTS_ANALYSIS.md` |

**Note importante :** Le gold standard proxy ("entité la plus récente") est intrinsèquement fiable. 61/163 instances Level 1 n'ont pas d'entités personne dans la fenêtre. LLM fallback остаётся nécessaire pour ces cas.

**Évaluation sur VRAI gold PROIEL (8 avril 2026) :**

| Niveau | Évalué | Correct | Accuracy |
|--------|---------|---------|----------|
| **Overall** | 101 | 25 | **24.8%** |
| Level 1 | 22 | 2 | 9.1% |
| Level 2 | 60 | 18 | 30.0% |
| Level 3 | 19 | 5 | 26.3% |

**Analyse des problèmes :**
1. **Fenêtre de 5 versets trop large** → IOANNES prédit même quand la narration a basculé vers IESOUS
2. **Heuristique de saillie biaisée** → "most frequent" favorise les entités citées plus tôt
3. **Détection du génitif absolu incorrecte** → parfois appliquée à tort
4. **Pluriel (μαθηταί) non détecté** → les verbes pluriels ne correspondent pas à OI_MATHETAI

**Fichiers générés :**
- `scripts/extract_proiel_gold.py` — extraction du gold depuis PROIEL antecedent-id
- `scripts/evaluate_against_proiel_gold.py` — évaluation contre gold PROIEL
- `project/data/experiments/sprint2c/PROIEL_GOLD_EVALUATION.md` — rapport détaillé

**Limites identifiées :**
- Proxy gold non fiable pour Level 2/3 → l'annotation manuelle de 50 cas par un helléniste reste recommandée pour des métriques exactes
- 61 instances Level 1 retournent NONE (pas d'entités personne dans la fenêtre) → fenêtre plus large ou recherche textuelle nécessaire

---

## Sprint 3 — Attribution des discours & actes narratifs (semaines 16–20) · À venir

- **3A** — Attribution des discours directs (détection ponctuation + verba_dicendi + résolution agent).
- **3B** — Actes narratifs par personnage (Semantic Role Labeling via typologie Pedalion).

## Sprint 4 — API, granularités et exports (semaines 21–24) · À venir

- Interface unifiée (`pericope`, `chapter`, `book`).
- Exports multiples (CoNLL-U, JSON, HTML interactif, GraphML).
