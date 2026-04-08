# Sprint 3A Plan — Two-Stage Pro-Drop Resolution

**Target:** 60% accuracy on PROIEL gold  
**Deadline:** 6 weeks  
**Status:** Implementation

---

## Background

**No Ancient Greek coreference SOTA exists.** Our 60% target would be pioneering work.

Current baseline:
- LLM accuracy: 29.7%
- Rules accuracy: 24.8%
- **Target gap:** +30 percentage points

---

## Architecture: Two-Stage Approach

Based on Celano (2023) "Neural Network Approach to Ellipsis Detection":

```
┌─────────────────────────────────────────────────────────────────┐
│                     STAGE 1: Rules (High Precision)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Input: Sentence with finite verb                                │
│      ↓                                                           │
│  Dependency Parse (PROIEL/trankit)                              │
│      ↓                                                           │
│  Candidate Detection:                                            │
│    - Finite verb without nsubj (pro-drop candidate)             │
│    - Person/number compatibility filter                         │
│      ↓                                                           │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │           STAGE 2: Ambiguity Resolution                  │      │
│  ├─────────────────────────────────────────────────────────┤      │
│  │                                                          │      │
│  │   Clear (1 entity) → Apply rules → 95% target          │      │
│  │                                                          │      │
│  │   Ambiguous (2+ entities) → Neural classifier → 60%    │      │
│  │                                                          │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Week-by-Week Implementation

### Week 1: Dependency Parsing Integration

**Goal:** Replace entity window with dependency-based candidate detection

| Task | Deliverable | Tools |
|------|-------------|-------|
| Integrate trankit | Parser initialized | trankit |
| Alternative: OdyCy | Check availability | OdyCy spaCy |
| Build candidate detector | `find_prodrop_candidates()` | PROIEL XML |

**Success criteria:** Parse Mark 1 sentences, identify finite verbs without nsubj

```python
# Week 1 deliverable
def find_prodrop_candidates(sentence_tokens):
    """Find finite verbs without subject (pro-drop candidates)."""
    # 1. Find finite verbs (V-* POS)
    # 2. Check for nsubj dependency
    # 3. Return candidates
```

---

### Week 2: Ambiguity Classifier

**Goal:** Binary classification — clear vs ambiguous

| Task | Deliverable |
|------|-------------|
| Feature engineering | Narrative markers, entity count, distance |
| Build classifier | `is_ambiguous()` function |
| Train on PROIEL | ~100 annotated examples |

**Features:**

```python
features = {
    'entity_count': 1,  # 1 = clear, 2+ = ambiguous
    'has_delta': False,  # δέ marker
    'has_genitive_absolute': False,
    'verb_number': 'singular',
    'entity_recency': 2,  # verses since mention
}
```

**Success criteria:** Classifier achieves 90% accuracy on held-out set

---

### Week 3: Neural Resolution Model

**Goal:** Train classifier for ambiguous cases

| Task | Deliverable | Model |
|------|-------------|-------|
| Prepare training data | PROIEL antecedent chains | ~500 examples |
| Model architecture | Character-level + context | LOGION or character CNN |
| Training loop | Trained model | PyTorch |

**Model architecture:**

```
Input: Greek text (current verse + 2 preceding)
    ↓
Character-level encoder (captures morphology)
    ↓
Context encoder (BiLSTM or Transformer)
    ↓
Output: Entity probability distribution
```

**Success criteria:** Model achieves 60% accuracy on Level 2+3

---

### Week 4: Character-Level Integration

**Goal:** Integrate LOGION or alternative for Greek morphology

| Task | Status | Notes |
|------|--------|-------|
| Research LOGION | ❓ | Find access |
| Alternative: Character CNN | ✅ Fallback | Simpler but effective |
| Integration | Pending | Week 4 dependent |

**Character CNN approach:**

```python
# Alternative to LOGION
char_vocab = greek_char_set()  # ~50 chars
char_embeddings = nn.Embedding(vocab_size=50, embedding_dim=32)
cnn = Conv1D(filters=128, kernel_size=3)
```

---

### Week 5: Full Pipeline Integration

**Goal:** End-to-end system

| Component | Integration |
|-----------|-------------|
| Candidate detector | → Ambiguity classifier |
| Clear path | → Rules resolver |
| Ambiguous path | → Neural resolver |
| Fallback | → Most recent entity |

**Pipeline:**

```python
def resolve_prodrop(sentence, context):
    candidates = find_prodrop_candidates(sentence)
    
    for candidate in candidates:
        if is_clear(candidate):
            return rules_resolve(candidate)
        else:
            return neural_resolve(candidate, context)
```

---

### Week 6: Evaluation & Documentation

**Goal:** Validate 60% target

| Evaluation | Metric |
|------------|--------|
| PROIEL gold | 60% accuracy on Level 2+3 |
| Ablation study | Rules only vs full pipeline |
| Error analysis | Top failure modes |

---

## Training Data Strategy

| Source | Count | Use |
|--------|-------|-----|
| PROIEL Mark | ~200 | Clear case training |
| PROIEL John | ~200 | Clear case validation |
| PROIEL antecedent chains | ~100 | Ambiguous training |
| Synthetic | TBD | Hard negative mining |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Insufficient training data | Medium | Augment with Luke, Acts when available |
| LOGION unavailable | High | Use character CNN fallback |
| 60% not achievable | Medium | Lower to 50%, document limits |
| Trankit servers down | High | Use PROIEL XML directly, or OdyCy |

---

## Dependencies

| Dependency | Status | Action |
|------------|--------|--------|
| Trankit | ⚠️ Servers unstable | Check, fallback to PROIEL XML |
| OdyCy | ❓ Check | Research centre-for-humanities-computing/odyCy |
| LOGION | ❓ Unknown | Research access |
| Manual annotation | ❌ Not available | Use PROIEL only for now |

---

## Deliverables

| Week | Deliverable |
|------|-------------|
| 1 | Candidate detector script |
| 2 | Ambiguity classifier |
| 3 | Neural resolution model |
| 4 | Character-level features |
| 5 | Full pipeline script |
| 6 | Evaluation report + 60% claim |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Level 2+3 accuracy | 60% | PROIEL gold evaluation |
| Clear case accuracy | 95% | Rules-only subset |
| Overall accuracy | 50% | Full evaluation |

---

## Next Steps

1. **Week 1:** Start with PROIEL XML parsing for candidate detection
2. **Parallel:** Research LOGION availability and OdyCy alternatives
3. **Week 2:** Build ambiguity classifier with narrative features
4. **Ongoing:** Document every decision in `project/docs/`

---

**Status:** Ready to begin Week 1 implementation
