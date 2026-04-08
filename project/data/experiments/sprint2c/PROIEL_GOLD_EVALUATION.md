# Sprint 2C — PROIEL Gold Evaluation Report

**Date:** April 8, 2026  
**Corpus:** Mark 1:1-16:20 (739 instances, 101 with PROIEL gold)  
**Gold Source:** PROIEL NT Treebank `antecedent-id` links

---

## Executive Summary

**Key Finding: Rules-based accuracy is 24.8% against TRUE gold standard.**

This is significantly lower than expected. The evaluation reveals fundamental limitations in the current approach that require rethinking before proceeding to Sprint 3A.

---

## Results vs PROIEL Gold

| Level | Evaluated | Correct | Accuracy | Notes |
|-------|-----------|---------|---------|-------|
| **Overall** | 101 | 25 | **24.8%** | Well below 70% target |
| Level 1 | 22 | 2 | 9.1% | Entity window too small |
| Level 2 | 60 | 18 | 30.0% | Best performance |
| Level 3 | 19 | 5 | 26.3% | Genitive absolute misfire |

---

## Root Cause Analysis

### 1. Salience Heuristic Favors IOANNES

**Problem:** IOANNES (John) appears frequently in early verses, and the salience heuristic ("most frequently mentioned") picks it even when the narrative has shifted to IESOUS.

**Example:**
```
MARK 1.10: εἶδεν (he saw)
  Gold: IESOUS
  Pred: IOANNES
  Reasoning: "Salience heuristic: 7 entities, most frequent = IOANNES"
```

The 5-verse window includes John from earlier context, even though the narrative has shifted to Jesus.

### 2. Entity Window Issues

**Problem:** The 5-verse window extracts entities too broadly, mixing narrative contexts.

- 22 Level 1 instances have "No entities in window" → entity extraction fails
- Window includes entities from previous scenes that are no longer relevant

### 3. Genitive Absolute Misdetection

**Problem:** The genitive absolute detection rule fires incorrectly, picking the wrong entity.

**Example:**
```
MARK 2.26: εἰσῆλθεν (he entered)
  Gold: ΔΑΥΊΔ (David)
  Pred: ἈΡΧΙΕΡΕΎΣ (high priest)
  Reasoning: "Genitive absolute construction detected"
```

### 4. Number Agreement Gaps

**Problem:** Plural verbs (ἦσαν, εἶχον) should match OI_MATHETAI but often don't.

**Example:**
```
MARK 4.41: ἔλεγον (they said)
  Gold: OI_MATHETAI
  Pred: NONE
  Reasoning: "No entities in window"
```

---

## Key Metrics from PROIEL Gold Extraction

| Metric | Value |
|--------|-------|
| Total instances | 739 |
| Null subject found in PROIEL | 668 (90.4%) |
| Person antecedent found | 97 (13.1%) |
| Non-person antecedent | 343 (46.4%) |
| No null subject | 71 (9.6%) |

**Note:** Only 13.1% of instances have a clear person antecedent in PROIEL. This suggests:
1. PROIEL's annotation is selective (not all pro-drop annotated)
2. Many pro-drop antecedents are non-person (places, abstract concepts)
3. True person resolution is difficult

---

## Person Entity Distribution in PROIEL Gold

| Entity | Count |
|--------|-------|
| OI_MATHETAI (disciples) | 21 |
| IESOUS | 17 |
| PETROS | 13 |
| SALOME | 9 |
| PILATOS | 7 |
| OI_APOSTOLOI | 6 |
| IOANNES | 5 |
| ΔΑΥΊΔ (David) | 4 |
| ἸΩΣΉΦ (Joseph) | 4 |
| ΣΑΤΑΝΑ͂Σ (Satan) | 3 |

---

## Comparison: Proxy Gold vs TRUE Gold

| Metric | Proxy Gold | TRUE Gold (PROIEL) |
|--------|-----------|-------------------|
| Overall accuracy | 31.9% | 24.8% |
| Level 1 | 47.9% | 9.1% |
| Level 2 | 19.4% | 30.0% |
| Level 3 | 60.7% | 26.3% |

**Interpretation:** The proxy gold ("most recent entity") was misleading. Level 1 appeared good because the proxy was lenient. TRUE gold reveals the rules perform worse than expected.

---

## Recommendations

### Immediate (Before Sprint 3A)

1. **Reduce entity window** - Use 2 verses instead of 5 to avoid stale entities
2. **Add distance decay** - Weight recent mentions more heavily than distant ones
3. **Fix genitive absolute detection** - Only apply when construction is clear
4. **Handle plural subjects** - Ensure OI_MATHETAI is matched for plural verbs
5. **Expand entity extraction** - Cover Level 1 instances with "No entities"

### Medium-term (Revisit Sprint 2C)

1. **LLM evaluation with TRUE gold** - Run LLM hybrid and compare against PROIEL gold
2. **Consider Celano (2023) approach** - Two-stage: rules first, then neural confirmation
3. **Character-level models** - LOGION for Greek morphology
4. **Fine-tune on PROIEL data** - Use antecedent-id links for training

### Decision Framework

| LLM Accuracy on TRUE Gold | Recommended Action |
|-------------------------|-------------------|
| ≥70% on Level 2+3 | Adopt LLM hybrid as primary |
| 50-70% on Level 2+3 | Hybrid with rules for clear cases |
| <50% on Level 2+3 | Reconsider approach, focus on entity extraction |

---

## Files Generated

| File | Description |
|------|-------------|
| `scripts/extract_proiel_gold.py` | Extracts true gold from PROIEL antecedent-id |
| `scripts/evaluate_against_proiel_gold.py` | Evaluates rules against PROIEL gold |
| `project/data/experiments/sprint2c/proiel_gold_standard.json` | True gold standard |
| `project/data/experiments/sprint2c/proiel_evaluation_results.json` | Evaluation results |

---

## Next Steps

1. **Run LLM evaluation** against PROIEL gold (requires new API key)
2. **Compare LLM vs rules** on same gold standard
3. **Decide architecture** based on true metrics
4. **Consider reverting to Sprint 1** for entity extraction improvements
