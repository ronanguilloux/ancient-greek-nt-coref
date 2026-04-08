import pandas as pd
import os

df = pd.read_csv("project/data/proiel_coref.csv")

os.makedirs("project/lexicons", exist_ok=True)

# 1. Pronouns
pronoun_lemmas = ["αὐτός", "ἐκεῖνος", "οὗτος", "ὅδε", "ἐγώ", "σύ", "ἡμεῖς", "ὑμεῖς"]
pronoun_forms = df[df["lemma"].isin(pronoun_lemmas) & df["form"].notna()]
# Drop duplicates based on form, lemma and morphology
pronouns_unique = pronoun_forms[["form", "lemma", "pos", "morphology"]].drop_duplicates(subset=["form", "lemma"])

# Wait, we might want to normalize accents and lower case for matching?
# Let's save it as is.
pronouns_unique.to_csv("project/lexicons/pronouns.tsv", sep="\t", index=False)
print(f"Saved {len(pronouns_unique)} pronoun forms to project/lexicons/pronouns.tsv")

# 2. Verba dicendi
dicendi_lemmas = [
    "λέγω", "εἶπον", "ἀποκρίνομαι", "ἐρωτάω", "φημί", "κράζω", "φωνέω", 
    "λαλέω", "ἐπερωτάω", "παρακαλέω", "διδάσκω", "μαρτυρέω", "ὁμολογέω",
    "εὔχομαι", "αἰτέω", "ἀπαγγέλλω", "ἀναγγέλλω", "κηρύσσω", "διαμαρτύρομαι",
    "γράφω"
]
dicendi_forms = df[df["lemma"].isin(dicendi_lemmas) & df["form"].notna()]
dicendi_unique = dicendi_forms[["form", "lemma", "pos", "morphology"]].drop_duplicates(subset=["form", "lemma"])
dicendi_unique.to_csv("project/lexicons/verba_dicendi.tsv", sep="\t", index=False)
print(f"Saved {len(dicendi_unique)} verba dicendi forms to project/lexicons/verba_dicendi.tsv")

# 3. Character Aliases
aliases_data = [
    {"lemma": "Σίμων", "canonical_id": "PETROS"},
    {"lemma": "Πέτρος", "canonical_id": "PETROS"},
    {"lemma": "Κηφᾶς", "canonical_id": "PETROS"},
    {"lemma": "Σαῦλος", "canonical_id": "PAULOS"},
    {"lemma": "Παῦλος", "canonical_id": "PAULOS"},
    {"lemma": "Ἰησοῦς", "canonical_id": "IESOUS"},
    {"lemma": "Ἰωάνης", "canonical_id": "IOANNES"},  # PROIEL spelling
    {"lemma": "Ἰωάννης", "canonical_id": "IOANNES"},
    {"lemma": "Μαριάμ", "canonical_id": "MARIA"},
    {"lemma": "Μαρία", "canonical_id": "MARIA"},
    {"lemma": "Ἰάκωβος", "canonical_id": "IAKOBOS"},
    {"lemma": "Θωμᾶς", "canonical_id": "THOMAS"},
    {"lemma": "Πιλᾶτος", "canonical_id": "PILATOS"},
    {"lemma": "Βαρναβᾶς", "canonical_id": "BARNABAS"},
    {"lemma": "Στέφανος", "canonical_id": "STEPHANOS"}
]
aliases_df = pd.DataFrame(aliases_data)
aliases_df.to_csv("project/lexicons/character_aliases.tsv", sep="\t", index=False)
print(f"Saved {len(aliases_df)} character aliases to project/lexicons/character_aliases.tsv")

# 4. Narrative Epithets
epithets_data = [
    {"epithet": "ὁ κύριος", "canonical_id": "IESOUS"},
    {"epithet": "ὁ διδάσκαλος", "canonical_id": "IESOUS"},
    {"epithet": "ὁ υἱὸς τοῦ θεοῦ", "canonical_id": "IESOUS"},
    {"epithet": "ὁ υἱὸς τοῦ ἀνθρώπου", "canonical_id": "IESOUS"},
    {"epithet": "ὁ ἄγγελος", "canonical_id": "ANGELOS"},
    {"epithet": "ὁ βαπτιστὴς", "canonical_id": "IOANNES_BAPTISTES"},
]
epithets_df = pd.DataFrame(epithets_data)
epithets_df.to_csv("project/lexicons/narrative_epithets.tsv", sep="\t", index=False)
print(f"Saved {len(epithets_df)} narrative epithets to project/lexicons/narrative_epithets.tsv")

