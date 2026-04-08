import stanza
nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse', verbose=False)
doc = nlp("ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ.")
print("\n--- STANZA RESULTS ---")
for word in doc.sentences[0].words:
    print(f"Form: {word.text:<12} | Lemma: {word.lemma:<10} | "
          f"UPOS: {word.upos:<5} | "
          f"Head: {word.head} | "
          f"DepRel: {word.deprel}")
