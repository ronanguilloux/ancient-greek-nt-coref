import pandas as pd
import os

print("Chargement des données PROIEL (project/data/proiel_coref.csv)...")
df = pd.read_csv("project/data/proiel_coref.csv")

# Filtrer les versets de Marc 1 à 4
df_mark = df[df['ref'].str.startswith('MARK 1.') | 
             df['ref'].str.startswith('MARK 2.') | 
             df['ref'].str.startswith('MARK 3.') | 
             df['ref'].str.startswith('MARK 4.')].copy()

print(f"Tokens dans Marc 1-4 : {len(df_mark)}")

# Identifier les verbes pro-drop avec un antécédent (coréférence existante)
# 1. On cherche les verbes (V)
verbs = df_mark[df_mark['pos'].str.startswith('V', na=False)]

# 2. On cherche ceux qui sont le prédicat principal/subordonné mais N'ONT PAS d'enfant 'nsubj'
# Pour ce faire, trouvons tous les tokens qui sont 'nsubj'
nsubj_heads = set(df_mark[df_mark['relation'] == 'sub']['head_id'])

# 3. Les verbes sans sujet
pro_drop_verbs = verbs[~verbs['token_id'].isin(nsubj_heads)]

# 4. On garde ceux qui ont un antecedent_id (ils participent à une chaîne)
pro_drop_annotated = pro_drop_verbs[pro_drop_verbs['antecedent_id'].notna()]

print(f"Verbes pro-drop trouvés et annotés dans Marc 1-4 : {len(pro_drop_annotated)}")

# Sélectionner 50 exemples au hasard pour l'expérience
sample_50 = pro_drop_annotated.sample(min(50, len(pro_drop_annotated)), random_state=42)

# Préparer le fichier de test avec le contexte
out_lines = []
for _, row in sample_50.iterrows():
    vid = row['token_id']
    vform = row['form']
    ref = row['ref']
    sent_id = row['sentence_id']
    
    # Récupérer la phrase courante + la précédente pour le contexte
    current_sent_df = df_mark[df_mark['sentence_id'] == sent_id]
    prev_sent_id = sent_id - 1 if sent_id > 1 else sent_id # Approximation simple
    prev_sent_df = df_mark[df_mark['sentence_id'] == prev_sent_id]
    
    context = " ".join(prev_sent_df['form'].fillna('')) + " " + " ".join(current_sent_df['form'].fillna(''))
    
    # Résoudre l'antécédent réel (Gold)
    ant_id = row['antecedent_id']
    gold_form = df_mark[df_mark['token_id'] == ant_id]['form'].values
    gold_lemma = df_mark[df_mark['token_id'] == ant_id]['lemma'].values
    
    gold_answer = f"{gold_form[0]} ({gold_lemma[0]})" if len(gold_form) > 0 else "UNKNOWN"
    
    out_lines.append(f"REF: {ref} | Token: {vid}")
    out_lines.append(f"VERBE PRO-DROP: {vform} ({row['lemma']})")
    out_lines.append(f"CONTEXTE: {context}")
    out_lines.append(f"GOLD (Antécédent attendu): {gold_answer}")
    out_lines.append("-" * 60)

os.makedirs("project/data/experiments", exist_ok=True)
with open("project/data/experiments/prodrop_sample_50.txt", "w") as f:
    f.write("\n".join(out_lines))

print("Échantillon généré dans project/data/experiments/prodrop_sample_50.txt")
