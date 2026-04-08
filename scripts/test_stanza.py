# Let's verify stanza instead, just in case trankit is permanently broken for download
import stanza
stanza.download('grc')
nlp = stanza.Pipeline('grc')
doc = nlp("ἀπεκρίθη Ἰησοῦς καὶ εἶπεν αὐτῇ.")
print(doc)
