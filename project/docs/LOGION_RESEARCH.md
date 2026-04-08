# LOGION Research — Character-Level Models for Ancient Greek

**Status:** Need to investigate availability

---

## What is LOGION?

LOGION is a character-level model specifically designed for Ancient Greek NLP, developed by Bastien Kindt and colleagues.

**Key features:**
- Character-level embeddings capture Greek morphology natively
- Handles the highly inflected nature of Greek (5 cases, 3 genders, multiple tenses)
- State-of-the-art for lemmatization and morphological analysis

**Reference:** Kindt et al. (2022) - "Analyse automatique du grec ancien par réseau de neurones"

---

## How to Find LOGION

### Option 1: GitHub
Search for "LOGION" or "Kindt grecor" on GitHub

### Option 2: Contact
- Bastien Kindt (Université catholique de Louvain)
- Chahan Vidal-Gorène (project GREgORI)

### Option 3: Alternative Character-Level Models

If LOGION is unavailable, use:

1. **Character CNN** (fallback)
   - Simple convolutional neural network on character sequences
   - Can be trained from scratch on Greek text
   - ~50 char vocabulary (Greek alphabet + diacritics)

2. **Byzantine tokenizers** 
   - Hugging Face: `keras-team/transformers` has Greek models
   - Check for pre-trained character-level embeddings

3. **OdyCy** (2023)
   - Centre for Humanities Computing
   - GitHub: `centre-for-humanities-computing/odyCy`
   - spaCy pipeline for Ancient Greek
   - SOTA for POS tagging, morphological analysis

---

## Action Items

- [ ] Search GitHub for "LOGION" and "Kindt"
- [ ] Check OdyCy GitHub repository
- [ ] Contact Kindt/GREgORI if LOGION unavailable
- [ ] Prepare character CNN as fallback

---

## Budget Estimate

If LOGION requires licensing:
- Character CNN implementation: ~2 days
- Training on PROIEL: ~1 day
- Integration: ~1 day
- **Total: ~1 week without LOGION**
