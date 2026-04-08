# Sprint 2C Postmortem — Pro-Drop Resolution

**Date:** April 8, 2026  
**Status:** Pivoting to new approach

---

## Executive Summary

| Metric | Target | Actual | Assessment |
|--------|--------|--------|------------|
| Pro-drop accuracy | 70% (initial) | 30% (LLM) | ❌ Significantly below target |
| SOTA benchmark | Unknown | N/A | ⚠️ No Greek coreference SOTA exists |
| Hybrid improvement | >15% over rules | +4.9% | ⚠️ Marginal benefit |

**Key Finding:** There is **no published SOTA benchmark** for coreference resolution on Ancient Greek. Our 30% accuracy, while low, is pioneering work in an unexplored domain.

---

## What We Tried

### Approach 1: Pure Rules
- **Method:** Heuristic-based resolution (salience, genitive absolute, δέ markers)
- **Accuracy:** 24.8% on PROIEL gold
- **Issues:** 
  - Salience heuristic favors frequently-mentioned entities (IOANNES)
  - Entity window too broad (5 verses)
  - Genitive absolute misdetection

### Approach 2: LLM (Gemini 3.1 Pro)
- **Method:** Zero-shot LLM evaluation
- **Accuracy:** 29.7% on PROIEL gold
- **Improvement over rules:** +4.9%
- **Issues:**
  - LLM struggles with Greek morphology
  - Context window may not capture narrative shifts
  - No domain-specific fine-tuning

### Approach 3: Hybrid (Rules + LLM)
- **Method:** Rules for clear cases, LLM for ambiguous
- **Accuracy:** Not fully evaluated
- **Issues:** LLM only marginally better than rules

---

## Why Accuracy Is Low

### Technical Factors

| Factor | Impact | Mitigation |
|--------|--------|------------|
| Entity extraction | High | Need dependency parsing, not regex |
| Gold standard | Medium | Only 101/739 (14%) have person antecedents |
| Window size | High | 5 verses includes stale entities |
| Greek morphology | Medium | Need character-level models |

### Fundamental Factors

1. **No SOTA benchmark exists** — We're in unexplored territory
2. **Task difficulty** — Pro-drop in narrative Greek requires deep textual understanding
3. **Gold standard quality** — PROIEL antecedent-id is selective, not comprehensive

---

## What Worked

| Technique | Benefit |
|-----------|---------|
| Salience heuristic | Works when one entity dominates |
| Genitive absolute detection | Helps Level 3 cases |
| PERSON_LEMMAS filtering | Reduces false positives |
| PROIEL antecedent extraction | Enabled true gold evaluation |

---

## Lessons Learned

### Do Differently

1. **Start with dependency parsing** — PROIEL/trankit for candidate detection
2. **Build ambiguity classifier** — Binary: clear vs ambiguous before resolution
3. **Character-level models** — LOGION for Greek morphology
4. **Smaller context windows** — 2 verses max, not 5

### Continue

1. **PROIEL gold extraction** — Valuable for evaluation
2. **Hybrid approach principle** — Rules for clear, ML for ambiguous
3. **Entity person filtering** — Essential for reducing noise

---

## Literature Review Findings

### Celano (2023) - "Neural Network Approach to Ellipsis Detection"
- **Two-stage approach:** Syntax-based detection → Neural confirmation
- **Key insight:** "Symbolic rules are extremely precise for 87% of cases; neural networks essential for 13% remaining"
- **Gap:** No published F1 metrics available

### OdyCy (2023) - Ancient Greek NLP Pipeline
- **SOTA for:** POS tagging, morphological analysis, dependency parsing
- **Pipeline:** spaCy-based transformers
- **Relevance:** Can provide dependency parsing for candidate detection

### English Coreference SOTA (Maverick 2024)
- **CoNLL-2012:** ~80-85% F1
- **Key insight:** Efficient models can match large models with better architecture

---

## New Direction: 60% SOTA Target

**Since no Ancient Greek coreference SOTA exists, our 60% target would be pioneering work.**

### Proposed Architecture

```
STAGE 1: Dependency Parse (OdyCy/trankit)
    ↓
STAGE 2: Candidate Detection (finite verb, no nsubj)
    ↓
STAGE 3: Ambiguity Classifier
    ├── Clear (1 entity) → Rules → 95% target
    └── Ambiguous (2+ entities) → Neural → 60% target
```

### Week-by-Week Plan

| Week | Task | Target |
|------|------|--------|
| 1 | Integrate trankit/PROIEL parsing | Candidate detection |
| 2 | Build ambiguity classifier | Binary classification |
| 3 | Train on PROIEL data | Classifier model |
| 4 | LOGION character embeddings | Greek morphology |
| 5 | Neural resolver for ambiguous | Resolution model |
| 6 | Full pipeline + eval | 60% accuracy |

---

## Resources Needed

| Resource | Status | Action |
|----------|--------|--------|
| PROIEL treebank | ✅ Available | Use for training |
| Trankit parser | ⚠️ Servers down | Check OdyCy alternative |
| LOGION | ❓ Unknown | Research access |
| Manual annotation | ❌ Not available | Defer to "for now" |

---

## Decision: Proceed with New Approach

**Status:** Pivoting from hybrid LLM comparison to two-stage rules + neural

**Next:** See `project/docs/SPRINT3A_PLAN.md` for implementation plan

---

## Appendix: Original Metrics

| Metric | Value |
|--------|-------|
| Total instances evaluated | 101 (with PROIEL gold) |
| Rules accuracy | 24.8% |
| LLM accuracy | 29.7% |
| Improvement over baseline | +4.9% |
| Level 1 accuracy (LLM) | 13.6% |
| Level 2 accuracy (LLM) | 40.0% |
| Level 3 accuracy (LLM) | 15.8% |
