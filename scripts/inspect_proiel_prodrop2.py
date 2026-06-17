import pandas as pd
df = pd.read_csv("project/data/proiel_coref.csv")
df_mark = df[df['book'] == 'MARK'].copy()

# Look at those 59 verbs that have an antecedent!
verbs = df_mark[(df_mark['antecedent_id'].notna()) & (df_mark['pos'] == 'V-')]
for _, row in verbs.head(10).iterrows():
    print(f"{row['form']} | Morph: {row['morphology']} | Rel: {row['relation']}")

# Wait, the way PROIEL encodes pro-drop is often by creating an EMPTY node, or the verb is NOT the anaphor...
# If there are only 59 verbs, how is pro-drop annotated in PROIEL?
