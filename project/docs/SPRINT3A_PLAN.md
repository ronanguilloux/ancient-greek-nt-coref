# Sprint 3A Plan — Two-Stage Pro-Drop Resolution

**Target:** 55-60% accuracy on PROIEL gold  
**Status:** Implementation

> See [`TARGET_JUSTIFICATION.md`](./TARGET_JUSTIFICATION.md) for detailed benchmarking analysis.

---

## Background

**No Ancient Greek coreference SOTA exists.** Our 55-60% target would be pioneering work.

Current baseline:
- LLM accuracy: 29.7%
- Rules accuracy: 24.8%
- **Target gap:** +25-30 percentage points

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

## Scope Constraints

### PERSONS Only (Not LOC, ORG, etc.)

This project focuses exclusively on **person entities** (PER):
- ✅ Ἰησοῦς, Παῦλος, Πέτρος
- ✅ αὐτός (anaphoric pronouns referring to persons)
- ✅ ὁ διδάσκαλος (epithets referring to persons)

Out of scope:
- ❌ LOC (place names) - separate NER task
- ❌ ORG (organizations, institutions)
- ❌ EVENT, WORK, etc.

### Subject Pro-Drop Only (Not Objects)

Current focus: **Subject** zero mentions (implied subjects).

**Future extension potential:** Object zero mentions (e.g., "gave" → "gave [it]") — requires additional grammatical role analysis. Documented in [`FUTURE_WORK.md`](./FUTURE_WORK.md).

---

## Evaluation: Head-Matching

**Critical for Ancient Greek:** Because mentions are often subtrees in dependency trees, string matching fails on case-inflected forms.

| Method | Example | Result |
|--------|---------|--------|
| String matching | "τῷ ΠΕΤΡῳ" vs "ΠΕΤΡΟΣ" | ❌ Wrong |
| Head-matching | Both → "Peter" | ✅ Correct |

**Head-matching aligns with CRAC shared task standards (Novák et al., 2024).**

The CRAC 2024 evaluation uses **head-match CoNLL F1** as the primary metric:
- Gold and predicted mentions match if their **syntactic heads** are identical
- Full spans are ignored except for disambiguation
- This accounts for Ancient Greek's rich morphology (case inflection)

---

## Milestones

### Milestone 1: Dependency Parsing Integration · ✅ TERMINÉ

**Script:** `scripts/sprint3a_phase1_prodrop_detection.py`

**Results:**
- 6 CONLLU files parsed, 2,465 tokens
- 245 pro-drop candidates detected
- 23 with person antecedent (gold standard)
- **Baseline accuracy: 9.4%**

---

### Milestone 2: Ambiguity Classifier · ⏳ PROCHAIN

**Goal:** Binary classification — clear vs ambiguous

| Task | Deliverable |
|------|-------------|
| Feature engineering | Narrative markers, entity count, distance |
| Build classifier | `is_ambiguous()` function |
| Validate on PROIEL | ~100 annotated examples |

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

### Milestone 3: Neural Resolution Model · ⏳ À VENIR

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

### Milestone 4: Character-Level Integration · ⏳ À VENIR

**Goal:** Integrate LOGION or alternative for Greek morphology

| Task | Status | Notes |
|------|--------|-------|
| Research LOGION | ❓ | Find access |
| Alternative: Character CNN | ✅ Fallback | Simpler but effective |
| Integration | Pending | Dependent on Milestone 3 |

**Character CNN approach:**

```python
# Alternative to LOGION
char_vocab = greek_char_set()  # ~50 chars
char_embeddings = nn.Embedding(vocab_size=50, embedding_dim=32)
cnn = Conv1D(filters=128, kernel_size=3)
```

---

### Milestone 5: Full Pipeline Integration · ⏳ À VENIR

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

### Milestone 6: Evaluation & Documentation · ⏳ À VENIR

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
| 60% not achievable | Medium | Lower to 55%, document limits (see TARGET_JUSTIFICATION.md) |
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

| Milestone | Deliverable |
|----------|-------------|
| 1 ✅ | Candidate detector script |
| 2 ⏳ | Ambiguity classifier |
| 3 ⏳ | Neural resolution model |
| 4 ⏳ | Character-level features |
| 5 ⏳ | Full pipeline script |
| 6 ⏳ | Evaluation report + 55-60% accuracy claim |

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Zero detection | 85%+ | Compare against PROIEL empty nodes |
| Clear case accuracy | 70-80% | Rules-only subset |
| Ambiguous case accuracy | 50-60% | ML classifier |
| **Overall accuracy** | **55-60%** | PROIEL gold evaluation |

> Full justification in [`TARGET_JUSTIFICATION.md`](./TARGET_JUSTIFICATION.md)

---

## Phase 1 Completion (9 avril 2026)

**Deliverable:** `scripts/sprint3a_phase1_prodrop_detection.py`

### Results

| Metric | Value |
|--------|-------|
| Sentences parsed | 6 |
| Tokens | 2,465 |
| Pro-drop candidates | 245 |
| With person antecedent | 23 |
| **Baseline accuracy** | **9.4%** |

### Entity Distribution (Gold Standard Matches)

| Entity | Count |
|--------|-------|
| IESOUS | 15 |
| ANDREAS | 4 |
| IOANNES | 4 |

### Key Findings

1. **CONLLU format works:** Successfully parsed PROIEL CONLLU files directly
2. **Token IDs restart per sentence:** Required composite key `(sentence_id, token_id)`
3. **Verse refs in token MISC:** Extracted from `Ref=` annotation
4. **Low baseline:** 9.4% because most verbs don't have person antecedents (they have non-person or no antecedents)

### Next: Milestone 2

- **Ambiguity classifier** (`is_ambiguous()`)
- Narrative markers: δέ, τότε, genitive absolute
- Entity count in context window
- Target: Distinguish clear cases (1 candidate) from ambiguous (2+ candidates)

---

**Status:** Milestone 1 Complete ✅ — Ready for Milestone 2
