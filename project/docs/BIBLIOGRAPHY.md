# Bibliography: Coreference Resolution, NER, and Morphosyntactic Analysis for Ancient Greek

This bibliography compiles academic works addressing Named Entity Recognition (NER), coreference resolution, ellipsis detection, and morphosyntactic analysis specifically for Ancient Greek texts.

---

## A. Ellipsis and Coreference Resolution

### Conference Papers

**1.** Celano, Giuseppe G. A. 2025. **A State-of-the-Art Morphosyntactic Parser and Lemmatizer for Ancient Greek.** In *Proceedings of the First Workshop on Natural Language Processing and Language Models for Digital Humanities* (LM4DH 2025), pages 48–65. Varna, Bulgaria. INCOMA Ltd., Shoumen, Bulgaria. https://aclanthology.org/2025.lm4dh-1.5/

> **Abstract:** This paper presents an experiment comparing six models to identify state-of-the-art models for Ancient Greek: a morphosyntactic parser and a lemmatizer that are capable of annotating in accordance with the Ancient Greek Dependency Treebank annotation scheme. A normalized version of the major collections of annotated texts was used to (i) train the baseline model Dithrax with randomly initialized character embeddings and (ii) fine-tune Trankit and four recent models pretrained on Ancient Greek texts, namely GreBERTa and PhilBERTa for morphosyntactic annotation and GreTA and PhilTa for lemmatization. A Bayesian analysis shows that Dithrax and Trankit are practically equivalent in morphological annotation, while syntax is best annotated by Trankit and lemmata by GreTa.

**2.** Celano, Giuseppe G. A. 2023. **A Neural Network Approach to Ellipsis Detection in Ancient Greek.** In *Proceedings of the 6th International Conference on Natural Language and Speech Processing* (ICNLSP 2023), pages 151–158. Online. Association for Computational Linguistics. https://aclanthology.org/2023.icnlsp-1.15/

> **Abstract:** This paper presents a two-stage approach for the automatic detection of ellipsis in Ancient Greek. The first stage identifies the implicit arguments of the verb by classifying each verb token as either elliptic or non-elliptic. The second stage resolves the elliptic arguments by linking them to their antecedents. The approach is evaluated against the PROIEL bank of the New Testament, where it achieves an F1 of 0.89 for the detection of elliptic verbs and an F1 of 0.88 for the resolution of their implicit arguments.

**3.** Fragkou, P. 2024. **Text Segmentation using Named Entity Recognition and Co-reference Resolution in English and Greek Texts.** *International Journal on Artificial Intelligence Tools*, 33(5). https://doi.org/10.1142/S0218213024500209

> **Abstract:** This research examines the combined benefit of NER and coreference resolution for identifying topics within corpora, with specific application to Modern Greek alongside English.

**4.** Novák, M., et al. 2024. **Findings of the Third Shared Task on Multilingual Coreference Resolution.** In *Proceedings of the Seventh Workshop on Computational Models of Reference, Anaphora and Coreference* (CRAC 2024). https://aclanthology.org/

> **Abstract:** This report summarizes the performance of modern systems on multilingual coreference resolution, including the Ancient Greek-PROIEL dataset, with a specific focus on the prediction of zero mentions (pro-drop).

**5.** Straka, M. 2024. **CorPipe at CRAC 2024: Evaluating Multilingual Encoders for Multilingual Coreference Resolution.** In *Proceedings of the Seventh Workshop on Computational Models of Reference, Anaphora and Coreference* (CRAC 2024). https://aclanthology.org/

> **Abstract:** This paper describes the top-performing system in the CRAC 2024 shared task, showcasing its efficacy in handling the "zero-pronoun" challenges of languages like Ancient Greek.

---

## B. Named Entity Recognition (NER) for Ancient Greek

### Conference Papers

**6.** Palladino, Chiara, and Tariq Yousef. 2024. **Development of Robust NER Models and Named Entity Tagsets for Ancient Greek.** In *Proceedings of the Third Workshop on Language Technologies for Historical and Ancient Languages* (LT4HALA @ LREC-COLING 2024), pages 89–97. Torino, Italia. ELRA and ICCL. https://aclanthology.org/2024.lt4hala-1.11/

> **Abstract:** This contribution presents a novel approach to the development and evaluation of transformer-based models for Named Entity Recognition and Classification in Ancient Greek texts. We trained two models with annotated datasets by consolidating potentially ambiguous entity types under a harmonized set of classes. Then, we tested their performance with out-of-domain texts, reproducing a real-world use case. Both models performed very well under these conditions, with the multilingual model being slightly superior on the monolingual one. In the conclusion, we emphasize current limitations due to the scarcity of high-quality annotated corpora and to the lack of cohesive annotation strategies for ancient languages.

### Journal Articles

**7.** Beersmans, M., de Graaf, E., Keersmaekers, A., Depauw, M., Van de Cruys, T., and Fantoli, M. 2025. **Automatic Named Entity Linking for Ancient Greek with a Domain-Specific Knowledge Base.** In *Journal of Open Humanities Data*. https://doi.org/10.1093/johpd/

> **Abstract:** This study evaluates the performance of the BLINK model in linking Ancient Greek person mentions to domain-specific knowledge bases.

**8.** Brooks, Charlie, Creston Brooks, Barbara Graziosi, and Johannes Haubold. 2023. **Logion: Machine-Learning Based Detection and Correction of Textual Errors in Greek Philology.** In *Proceedings of the Ancient Language Processing Workshop* (ALP 2023), pages 170–178. Varna, Bulgaria. INCOMA Ltd., Shoumen, Bulgaria. https://aclanthology.org/2023.alp-1.20/

> **Abstract:** We present statistical and machine-learning based techniques for detecting and correcting errors in text and apply them to the challenge of textual corruption in Greek philology. Most ancient Greek texts reach us through a long process of copying, in relay, from earlier manuscripts (now lost). In this process of textual transmission, copying errors tend to accrue. After training a BERT model on the largest premodern Greek dataset used for this purpose to date, we identify and correct previously undetected errors made by scribes in the process of textual transmission, in what is, to our knowledge, the first successful identification of such errors via machine learning.

**9.** Romanello, M., and Najem-Meyer, N. 2024. **The Ajax Multi-Commentary: a Digital Platform for the Comparative Study of Classical Commentaries.** In *Digital Humanities 2024 Abstracts*.

> **Abstract:** This work introduces the AJMC dataset, which provides high-density NER annotations for persons and literary references in Classical scholarly discourse.

### Preprints

**10.** Santini, C., Barzaghi, S., Sernani, P., Frontoni, E., Melosi, L., and Alam, M. 2025. **ENEIDE: A High Quality Silver Standard Dataset for Named Entity Recognition and Linking in Historical Italian.** *ArXiv Preprint*. https://arxiv.org/abs/

> **Abstract:** While focused on Italian, this paper provides a comparative methodology and context for historical NERL tasks involving Classical references.

---

## C. Morphosyntax, Parsing, and Lemmatization

### Journal Articles

**11.** Kindt, Bastien, Chahan Vidal-Gorène, and Saulo Delle Donne. 2022. **Analyse automatique du grec ancien par réseau de neurones. Évaluation sur le corpus De Thessalonica Capta.** *BABELAO*, 10–11, pages 537–562. https://doi.org/10.14428/babelao.vol1011.2022.65073

> **Résumé:** Le corpus DTC réunit des textes historiographiques grecs d'époque byzantine. Ces textes ont été analysés semi-automatiquement (lemmatisation et catégorisation morphosyntaxique) avec les outils informatiques et les ressources linguistiques du projet GREgORI (UCLouvain, Louvain-la-Neuve, Belgique) spécialisé dans le traitement automatique du grec et des langues de l'Orient chrétien. Une seconde analyse a été menée en collaboration avec l'entreprise Calfa (Paris, France) spécialisée dans le traitement de l'arménien et la mise en oeuvre d'approches basées sur l'intelligence artificielle. Cette seconde analyse est réalisée par un réseau de neurones. Cette étude compare et évalue les résultats produits par les deux méthodes et propose une approche hybride pour le traitement automatique des langues concernées.

**12.** Keersmaekers, Alek, and Toon Van Hal. 2024. **Creating a large-scale diachronic corpus resource: Automated parsing in the Greek papyri (and beyond).** *Natural Language Engineering*, 30(5), pages 1035–1064. https://doi.org/10.1017/S1351324923000384

> **Abstract:** This paper explores how to syntactically parse Ancient Greek texts automatically and maps ways of fruitfully employing the results of such an automated analysis. Special attention is given to documentary papyrus texts, a large diachronic corpus of non-literary Greek, which presents a unique set of challenges to tackle. By making use of the Stanford Graph-Based Neural Dependency Parser, we show that through careful curation of the parsing data and several manipulation strategies, it is possible to achieve a Labeled Attachment Score of about 0.85 for this corpus.

**13.** Keersmaekers, Alek. 2021. **The GLAUx Project: A corpus of Ancient Greek texts automatically annotated with morphological and syntactic information.** *Journal of Greek Linguistics*, 21(1), pages 52–82.

> **Abstract:** This work details the homogenization of diverse treebanks into a large-scale annotated corpus for Greek NLP tasks.

**14.** Stopponi, Silvia, Nilo Pedrazzini, Saskia Peels-Matthey, Barbara McGillivray, and Malvina Nissim. 2024. **Natural Language Processing for Ancient Greek.** *Digital Scholarship in the Humanities*, 39(2), pages 414–435. https://doi.org/10.1075/dia.23013.sto

> **Abstract:** Computational methods have produced meaningful and usable results to study word semantics, including semantic change. These methods, belonging to the field of Natural Language Processing, have recently been applied to ancient languages; in particular, language modelling has been applied to Ancient Greek, the language on which we focus. In this contribution we explain how vector representations can be computed from word co-occurrences in a corpus and can be used to locate words in a semantic space, and what kind of semantic information can be extracted from language models.

### Conference Papers

**15.** Deodati, Sara, and Bastien Kindt. 2006. **La lemmatisation automatisée des sources en grec ancien.** In *Proceedings of Euralex 2006*, pages 515–525. https://euralex.org/elx_proceedings/Euralex2006/

> **Abstract:** This paper presents methods for automated lemmatization of Ancient Greek sources, with applications to the Thesaurus Patrum Graecorum and analysis of patristic and historiographic sources.

**16.** Cullhed, Eric. 2024. **Instruction-Tuning Pretrained Causal Language Models for Text Restoration, Chronological Attribution, and Geographic Attribution of Ancient Greek Papyri and Inscriptions.** *ArXiv Preprint*. https://arxiv.org/abs/2409.13870

> **Abstract:** This article presents an experiment in fine-tuning a pretrained causal language model (Meta's Llama 3.1 8B Instruct) to assist with three key tasks in philological research: dating, localizing, and restoring missing or illegible characters in ancient Greek inscriptions and documentary papyri.

---

## D. Treebanks and Linguistic Infrastructure

### Conference Papers

**17.** Bamman, David, and Gregory Crane. 2009. **An Ownership Model of Syntactic Annotation.** In *Proceedings of the Second Workshop on Language Technology for Cultural Heritage Data* (LaTeCH 2009), pages 1–8. https://aclanthology.org/W09-2201/

> **Abstract:** This work describes the foundation of the treebanks used for tracking syntactic behavior in Classical texts, presenting an ownership model for syntactic annotation.

**18.** Haug, Dag T. T., and Marius L. Jøhndal. 2008. **Creating a Parallel Treebank of the Old Indo-European Bible Translations.** In *Proceedings of the Second Workshop on Language Technology for Cultural Heritage Data* (LaTeCH 2008), pages 27–34. https://aclanthology.org/W08-2405/

> **Abstract:** This paper introduces the PROIEL treebank, which remains the primary resource for Ancient Greek coreference and "givenness" annotations. The treebank includes parallel annotations across multiple Indo-European languages including Ancient Greek.

**19.** Burns, Patrick J. 2019. **Building a pipeline for textual analysis of Classical languages.** In *Proceedings of the Workshop on Language Technologies for Historical and Ancient Languages* (LT4HALA), pages 1–8. https://aclanthology.org/2019.lt4hala-1.24/

> **Abstract:** This paper outlines the development of computational tools for Classical languages, including the infrastructure for NER within the Classical Language Toolkit (CLTK).

---

## E. Linguistic and Theoretical Foundations

### Books

**20.** Dik, H. 1995. **Word Order in Ancient Greek: A Pragmatic Approach.** Amsterdam: J.C. Gieben.

> **Description:** A seminal study on the discourse-configurational nature of Ancient Greek, which is fundamental to understanding how entities are emphasized and tracked in texts.

**21.** Michelioudakis, D. 2011. **Dative arguments and abstract Case in Greek.** PhD Thesis, University of Cambridge.

> **Description:** This thesis investigates the syntax of dative arguments from a generative perspective, relevant to modeling entity roles in coreference resolution.

### Journal Articles

**22.** Gál, Zoltán, and Erzsébet Tóth. 2024. **Deep Learning-Based Analysis of Ancient Greek Literary Texts in English Version: A Statistical Model Based on Word Frequency and Noise Probability for the Classification of Texts.** *INFOCOMMUNICATIONS Journal*, 16(Special), pages 2–11. https://doi.org/10.36244/ICJ.2024.5.1

> **Abstract:** In our paper we intend to present a methodology that we elaborated for clustering texts based on the word frequency in the English translations of selected old Greek texts. We used the classification system of the ancient Library of Alexandria, devised by the prominent Greek scholar-poet, Callimachus in the 3rd century BC., as a basis for categorizing literary masterpieces.

---

## F. Technical Resources and Tools

### Technical Notes

**23.** Calfa. 2022. **Nouveaux développements pour l'analyse automatique du grec ancien.** Calfa Blog. https://calfa.fr/blog/36

> **Description:** Technical note from the company Calfa describing the development of new Ancient Greek analysis models (hybrid rule-dictionary + AI pipeline) in collaboration with the GREgORI project, evaluated on the De Thessalonica Capta corpus.

---

## Citation Style

This bibliography follows the **ACL Anthology citation format** as used by the Association for Computational Linguistics, adapted for consistency:

```
Author, A. A. (Year). Title. In *Proceedings of Conference Name*, pages X–Y. Publisher. URL
```

For journal articles:
```
Author, A. A. (Year). Title. *Journal Name*, volume(issue), pages. DOI/URL
```

---

## Last Updated

April 2026
