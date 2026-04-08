# Future Work: Extensions and Evolutions

This document outlines potential extensions to the ntcoref project that are out of scope for the current implementation phase but represent natural next steps.

---

## 1. Named Entity Linking (NEL)

### Description

Named Entity Linking connects recognized entities to unique identifiers in Knowledge Bases, enabling disambiguation and enriched context.

### Knowledge Bases for Ancient Greek

| Knowledge Base | Scope | Unique Identifiers | Priority |
|---------------|-------|-------------------|----------|
| **LGPN** (Lexicon of Greek Personal Names) | Ancient Greek personal names | Oxford-based IDs | High |
| **Trismegistos** | Papyri and epigraphy | TM Nam IDs | Medium |
| **Pleiades** | Ancient geography | URI-based place names | Low |
| **Paulys Realencyclopädie** | Encyclopedic classical knowledge | Entry IDs (~100,000) | Medium |
| **Wikidata** | General semantic web | Q-IDs | Low |

### Use Cases

1. **Homonym Disambiguation**
   - Distinguish "James" in Mark vs. "James" in Acts
   - Link to LGPN entry for context

2. **Augmented Reading**
   - Display biographical information on hover
   - Link to related mentions across corpus

3. **Social Network Analysis**
   - Build person relationship graphs
   - Analyze narrative structures

### Implementation Notes

- BLINK model evaluated by Beersmans et al. (2025) - suboptimal for Greek due to Wikipedia-centric training
- Requires cross-lingual linking (Greek → English/German/French KB entries)
- MHEL-LLaMo approach uses LLMs for complex disambiguation

### References

- Beersmans et al. (2025). Automatic Named Entity Linking for Ancient Greek with a Domain-Specific Knowledge Base. JOHM.
- Beersmans et al. (2024). "Gotta catch 'em all!" ML4AL 2024.

---

## 2. Object Zero Mentions

### Description

Currently, the project focuses on **subject pro-drop** (implied subjects). Object zero mentions represent another category where the direct object is omitted.

### Example

```
ἔδωκεν [αὐτὸν] τῷ πατρί
"he gave [it] to the father"
```

The direct object may be implied from context, requiring different resolution strategies.

### Differences from Subject Pro-Drop

| Aspect | Subject Pro-Drop | Object Pro-Drop |
|--------|------------------|------------------|
| Detection | Verb morphology (person/number) | Semantic role labeling |
| Resolution | Narrative continuity | Object animacy/definiteness |
| Frequency | ~1 per 10 words | Less frequent |
| Complexity | Moderate | High |

### Implementation Considerations

- Requires Semantic Role Labeling (SRL)
- Object animacy constraints help disambiguation
- Often requires world knowledge

### Priority

**Low for NT** - Subject pro-drop is the dominant phenomenon; object dropping is rare.

---

## 3. Geographic and Organizational Entities

### Description

The current scope is limited to **person entities** (PER). Future work could extend to other named entity types.

### Entity Types

| Type | Examples | Complexity | Priority |
|------|----------|------------|----------|
| **LOC** (Locations) | Ἰερουσαλήμ, Γαλιλαία | Medium | Medium |
| **ORG** (Organizations) | συναγωγή, ναός | High | Low |
| **EVENT** | ἑορτή, σάββατον | High | Low |
| **WORK** | Τὸ εὐαγγέλιον | High | Low |

### Use Cases

1. **Geographical mapping** - Link place names to Pleiades coordinates
2. **Narrative analysis** - Track movement of characters
3. **Historical reconstruction** - Social network visualization

### Priority

**Low** - Person coreference is the primary scholarly interest for NT analysis.

---

## 4. Additional Ancient Greek Corpora

### Description

The current implementation focuses on the New Testament (PROIEL). Future extensions could include:

| Corpus | Coverage | Use Case |
|--------|----------|----------|
| **Septuagint (LXX)** | Greek Old Testament | Intertextual analysis |
| **Josephus** | Jewish historian | Historical narrative |
| **Plutarch** | Parallel biographies | Character analysis |
| **Papyri** | Documentary Greek | Diachronic study |

### Challenges

- Variable annotation quality
- Different morphological conventions
- Less standardized formatting

---

## 5. Enhanced Discourse Attribution

### Description

Beyond speech attribution, future work could address:

1. **Indirect Discourse**
   - "Jesus said that the Kingdom was near"
   - Requires understanding of reporting verbs

2. **Free Indirect Discourse**
   - Narrative voice blending with character thought
   - Difficult even for human interpreters

3. **Narrative Time Markers**
   - Temporal adverbs and particles
   - Scene change detection

### Priority

**Medium** - Important for full narrative analysis but complex.

---

## 6. Integration with Other NLP Tools

### Potential Integrations

| Tool | Purpose | Priority |
|------|---------|----------|
| **odyCy** | spaCy pipeline for Ancient Greek | High |
| **Trankit** | Biaffine dependency parser | High |
| **GreTa** | Lemmatizer (Celano, 2025) | Medium |
| **LOGION** | Error detection (Brooks et al.) | Medium |
| **Pythia** | Ancient Greek BERT variants | Low |

### Priority

**High** - Integration with existing tools is essential for production use.

---

## 7. Collaborative Annotation Platform

### Description

Manual annotation of coreference chains requires a web-based platform for:

1. **Multi-user annotation** - Classical scholars working together
2. **Quality control** - Inter-annotator agreement metrics
3. **Active learning** - System suggests uncertain cases for human review
4. **Export capabilities** - CoNLL-U, JSON, proprietary formats

### Tools to Consider

- INCEpTION (annotation platform)
- brat (rapid annotation)
- Prodigy (active learning)

### Priority

**Medium** - Important for scaling annotation beyond single researcher.

---

## 8. Real-Time API Service

### Description

Wrap the coreference resolution in a REST API for external use:

```
POST /api/v1/resolve
{
  "text": "Ἰησοῦς εἶπεν αὐτοῖς· ἀμὴν ἀμὴν λέγω ὑμῖν",
  "scope": "verse",
  "options": {...}
}
```

### Features

- Batch processing
- Caching of parsed results
- Rate limiting
- Multiple output formats

### Priority

**Low** - Not critical for initial research use.

---

## Priority Summary

| Extension | Priority | Complexity | Timeline |
|-----------|----------|-----------|----------|
| Tool Integration (odyCy/Trankit) | High | Medium | Short |
| Named Entity Linking | Medium | High | Long |
| Additional Corpora | Medium | Medium | Medium |
| Discourse Attribution | Medium | High | Long |
| Geographic Entities | Low | Medium | Medium |
| Object Zero Mentions | Low | High | Long |
| Annotation Platform | Low | High | Long |
| API Service | Low | Low | Short |

---

## References

- Beersmans et al. (2025). Automatic Named Entity Linking for Ancient Greek. JOHM.
- Celano (2025). A State-of-the-Art Morphosyntactic Parser and Lemmatizer. LM4DH 2025.
- Brooks et al. (2023). LOGION: Machine-Learning Based Detection and Correction of Textual Errors. ALP 2023.
- Novák et al. (2024). Findings of the Third Shared Task on Multilingual Coreference Resolution. CRAC 2024.

---

**Last Updated:** April 2026
