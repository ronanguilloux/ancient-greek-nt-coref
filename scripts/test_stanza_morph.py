import stanza

nlp = stanza.Pipeline('grc', processors='tokenize,pos,lemma,depparse', verbose=False)
text = "ἀπεκρίθη Ἰησοῦς καὶ εἶπεν τῇ γυναικί. αὐτὴ δὲ λέγει αὐτῷ."
doc = nlp(text)

for sentence in doc.sentences:
    for word in sentence.words:
        print(f"{word.text:<10} {word.upos:<5} {word.deprel:<8} head={word.head} feats={word.feats}")
