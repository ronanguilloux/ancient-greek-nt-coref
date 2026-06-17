import pandas as pd
import random

df = pd.read_csv("project/data/proiel_coref.csv")
df_mark = df[df['book'] == 'MARK'].copy()

def is_finite(morph):
    if pd.isna(morph): return False
    return len(morph) >= 2 and morph[0] == 'v' and morph[1] in ['1', '2', '3']

finite_verbs = df_mark[df_mark['morphology'].apply(is_finite)]
sub_heads = set(df_mark[df_mark['relation'] == 'sub']['head_id'])
pro_drop_verbs = finite_verbs[~finite_verbs['token_id'].isin(sub_heads)]

print(f"Total des verbes pro-drop dans Marc : {len(pro_drop_verbs)}")

# We just take 50 random pro-drop verbs to annotate ourselves
sample = pro_drop_verbs.sample(50, random_state=42)

out_lines = []
out_lines.append("# EXPERIMENT 1 : LLM vs HEURISTICS for PRO-DROP")
out_lines.append("# Remplissez le champ GOLD: avec l'entité attendue (ex: IESOUS, PETROS, FOULS, etc.)\n")

for i, (_, row) in enumerate(sample.iterrows()):
    vid = row['token_id']
    vform = row['form']
    ref = row['ref']
    sent_id = row['sentence_id']
    
    prev_sent_id = sent_id - 1 if sent_id > 1 else sent_id
    prev_df = df_mark[df_mark['sentence_id'] == prev_sent_id]
    curr_df = df_mark[df_mark['sentence_id'] == sent_id]
    
    context_words = []
    if prev_sent_id != sent_id:
        context_words.extend([str(t) for t in prev_df['form'].fillna('')])
        context_words.append("|||")
        
    for _, t in curr_df.iterrows():
        if t['token_id'] == vid:
            context_words.append(f"**{str(t['form']).upper()}**")
        else:
            context_words.append(str(t['form']))
            
    context = " ".join(context_words)
    
    out_lines.append(f"[{i+1}/50] REF: {ref} | Morph: {row['morphology']}")
    out_lines.append(f"CONTEXTE: {context}")
    out_lines.append(f"VERBE : {vform} ({row['lemma']})")
    out_lines.append(f"GOLD  : ")
    out_lines.append("-" * 60)

with open("project/data/experiments/prodrop_experiment_blank.txt", "w") as f:
    f.write("\n".join(out_lines))
print("Généré dans project/data/experiments/prodrop_experiment_blank.txt")
