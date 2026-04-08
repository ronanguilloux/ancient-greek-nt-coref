# Target Accuracy Justification: 55-60%

**Date:** April 2026  
**Project:** ntcoref - Ancient Greek New Testament Coreference Resolution

---

## Summary

After extensive literature review and benchmark analysis, we establish a **realistic target accuracy range of 55-60%** for subject pro-drop resolution on the PROIEL gold standard. This range balances ambition with empirical constraints specific to Ancient Greek NLP.

---

## Benchmark Analysis

### Published Results in the Literature

| Source | Task | Performance | Notes |
|--------|------|-------------|-------|
| CRAC 2024 (CorPipe-2stage) | Multilingual Coreference | **73.9% CoNLL F1** | Best system, averaged across 15 languages |
| CRAC 2024 (Baseline) | Multilingual Coreference | **53.2% CoNLL F1** | Simple mBERT baseline |
| Celano (2023) | Pro-Drop Detection | **89% F1** | Ellipsis detection only, gold dependencies |
| Celano (2023) | Pro-Drop Resolution | **88% F1** | With gold parses, NT-specific data |
| Empty Node Prediction (CRAC Baseline) | Ancient Greek Zeros | **88.4% F1** | Detection only, not resolution |
| Our Sprint 2C | LLM baseline | **29.7%** | True PROIEL gold evaluation |
| Our Sprint 2C | Rules baseline | **24.8%** | True PROIEL gold evaluation |

### Key Observations

1. **CRAC SOTA at 73.9%** is averaged across ALL languages (including easy languages like English with no pro-drop)
2. **Ancient Greek is among the hardest** - 1 zero mention per 10 words (highest density)
3. **Celano's 88%** requires gold dependency parses - this is an upper bound, not achievable without perfect parsing
4. **Our current baselines** (25-30%) leave significant room for improvement

---

## Justification for 55-60% Range

### Conservative End (55%)

| Factor | Impact | Justification |
|--------|--------|-------------|
| Task complexity | -15% | Ancient Greek pro-drop is hardest pro-drop task in CorefUD |
| No gold parsing | -10% | We use automated parses, not gold |
| NT-specific scope | +5% | Smaller domain = easier than full PROIEL |
| Two-stage approach | +10% | Rules handle ~87% clear cases |

**Calculation:** Baseline 53% (CRAC) + NT domain bonus - parsing noise ≈ **55%**

### Ambitious End (60%)

| Factor | Impact | Justification |
|--------|--------|-------------|
| Person-only focus | +5% | We ignore LOC, ORG, EVENT |
| Two-stage optimization | +5% | Celano's approach validated |
| Targeted architecture | +5% | NT-specific training data |
| Head-matching evaluation | +5% | More forgiving metric |

**Calculation:** Conservative 55% + targeted improvements ≈ **60%**

---

## Why Not Higher?

### Arguments Against 70%+

1. **CRAC SOTA is 74%** but includes all mention types and all 15 languages
2. **Ancient Greek is outlier** - highest zero-mention density in CorefUD
3. **CRAC 2024 change** - participants must now predict both zero position AND coreference links simultaneously
4. **Celano's 88%** requires:
   - Gold dependency parses
   - NT-specific training
   - Binary classification (detection separate from resolution)

### Arguments Against Lower (40-50%)

1. **Two-stage approach** is proven effective (Celano 2023)
2. **Clear cases** (~87%) should resolve at 70-80% with rules
3. **CRAC baseline** already achieves 53% with minimal tuning
4. **Domain specificity** of NT provides advantage

---

## Target Breakdown by Component

| Component | Target | Notes |
|-----------|--------|-------|
| Zero mention detection | 85%+ | CRAC baseline already at 88% |
| Clear case resolution (rules) | 70-80% | Single compatible antecedent |
| Ambiguous case resolution (ML) | 50-60% | Multiple candidates |
| **Overall accuracy** | **55-60%** | Weighted average |

---

## Milestones and Checkpoints

| Milestone | Target | Verification |
|-----------|--------|-------------|
| Zero detection baseline | 85% | Compare against PROIEL empty nodes |
| Rules-only on clear cases | 70% | Single-candidate subset |
| Two-stage pipeline | 55% | Full PROIEL evaluation |
| Optimization pass | 60% | Error analysis iteration |

---

## Related Works

- **CorPipe-2stage** (Straka, 2024): 73.9% on multilingual coreference
- **Celano (2023)**: 88% on pro-drop, but with gold parses
- **CRAC 2024 Empty Node Baseline**: 88.4% on Ancient Greek zero detection
- **Beersmans et al. (2024)**: Binary person classification at 88.8% F1

---

## Conclusion

A **55-60% accuracy target** is:
- ✅ **Ambitious enough** to advance the field
- ✅ **Realistic** given CRAC benchmarks
- ✅ **Achievable** with two-stage approach and NT-specific tuning
- ✅ **Pioneering** - no existing work targets pro-drop on NT subset specifically

This target represents meaningful progress beyond the simple baseline (53%) while remaining grounded in empirical evidence from the literature.

---

## References

- Novák et al. (2024). Findings of the Third Shared Task on Multilingual Coreference Resolution. CRAC 2024.
- Straka (2024). CorPipe at CRAC 2024. CRAC 2024.
- Celano, G. G. A. (2023). A Neural Network Approach to Ellipsis Detection in Ancient Greek. ICNLSP 2023.
- Beersmans et al. (2024). "Gotta catch 'em all!" ML4AL 2024.

---

**Last Updated:** April 2026
