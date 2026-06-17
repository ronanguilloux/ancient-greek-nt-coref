import pandas as pd
df = pd.read_csv("project/data/proiel_coref.csv")
print("Unique POS tags starting with V:")
print(df[df['pos'].str.startswith('V', na=False)]['pos'].unique())

print("\nSample Morphology tags for POS = 'V-' (Verb):")
print(df[df['pos'] == 'V-']['morphology'].value_counts().head(20))

print("\nLooking at sentence: καὶ ἀπεκρίθη Ἰησοῦς")
sent = df[df['form'] == 'ἀπεκρίθη'].head(5)
for _, row in sent.iterrows():
    print(f"{row['form']} | POS: {row['pos']} | Morph: {row['morphology']} | Rel: {row['relation']}")
