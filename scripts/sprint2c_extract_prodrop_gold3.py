import pandas as pd
import os

print("Chargement des données PROIEL...")
df = pd.read_csv("project/data/proiel_coref.csv")

df_mark = df[df['book'] == 'MARK'].copy()

# In PROIEL, the morphology code is 10 characters long.
# 1st char = Person (1, 2, 3 or -)
# 2nd char = Number (s, p, d or -)
# So if it starts with '1', '2' or '3', it is a FINITE VERB!
def is_finite(morph):
    if pd.isna(morph): return False
    return morph[0] in ['1', '2', '3']

finite_verbs = df_mark[df_mark['morphology'].apply(is_finite)]

sub_heads = set(df_mark[df_mark['relation'] == 'sub']['head_id'])
pro_drop_verbs = finite_verbs[~finite_verbs['token_id'].isin(sub_heads)]

print(f"Verbes conjugués dans MARK : {len(finite_verbs)}")
print(f"Verbes pro-drop dans MARK : {len(pro_drop_verbs)}")

# Check coreference links
has_ant = pro_drop_verbs[pro_drop_verbs['antecedent_id'].notna()]
is_ant = pro_drop_verbs[pro_drop_verbs['token_id'].isin(df_mark['antecedent_id'])]

print(f"Pro-drop avec antécédent (anaphorique) : {len(has_ant)}")
print(f"Pro-drop qui sont antécédents : {len(is_ant)}")

combined = pd.concat([has_ant, is_ant]).drop_duplicates()
print(f"Total des verbes pro-drop participant à une chaîne annotée : {len(combined)}")

# Extrayons 50 exemples (ou le maximum disponible)
sample = combined.sample(min(50, len(combined)), random_state=42)

out_lines = []
for _, row in sample.iterrows():
    vid = row['token_id']
    vform = row['form']
    ref = row['ref']
    sent_id = row['sentence_id']
    
    # Get previous sentence and current sentence for context
    prev_sent_id = sent_id - 1 if sent_id > 1 else sent_id
    
    prev_df = df_mark[df_mark['sentence_id'] == prev_sent_id]
    curr_df = df_mark[df_mark['sentence_id'] == sent_id]
    
    # Render with nice highlighting around the verb
    context_words = []
    for _, t in prev_df.iterrows():
        context_words.append(str(t['form']))
    context_words.append("|||") # separator
    for _, t in curr_df.iterrows():
        if t['token_id'] == vid:
            context_words.append(f"*{str(t['form'])}*")
        else:
            context_words.append(str(t['form']))
            
    context = " ".join(context_words)
    
    ant_id = row['antecedent_id']
    if pd.notna(ant_id):
        gold_df = df_mark[df_mark['token_id'] == ant_id]
        gold_answer = f"{gold_df['form'].values[0]} ({gold_df['lemma'].values[0]})" if len(gold_df)>0 else "UNKNOWN"
        role = "ANAPHORIQUE"
    else:
        ana_df = df_mark[df_mark['antecedent_id'] == vid]
        # In case there are multiple, get the first one
        if len(ana_df) > 0:
            gold_answer = f"Est l'antécédent de: {ana_df['form'].values[0]} ({ana_df['lemma'].values[0]})"
        else:
            gold_answer = "UNKNOWN"
        role = "ANTECEDENT"
        
    out_lines.append(f"REF: {ref} | Token: {vid}")
    out_lines.append(f"VERBE PRO-DROP: {vform} ({row['morphology']})")
    out_lines.append(f"ROLE PROIEL: {role}")
    out_lines.append(f"CONTEXTE: {context}")
    out_lines.append(f"GOLD: {gold_answer}")
    out_lines.append("-" * 60)

with open("project/data/experiments/prodrop_sample_50.txt", "w") as f:
    f.write("\n".join(out_lines))
    
print("Généré avec succès dans project/data/experiments/prodrop_sample_50.txt")
