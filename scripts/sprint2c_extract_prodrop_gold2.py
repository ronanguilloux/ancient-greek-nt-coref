import pandas as pd
import os

df = pd.read_csv("project/data/proiel_coref.csv")

# Wait, PROIEL relation annotations for subject are "sub", not "nsubj"
# We need to refine the extraction of pro-drop verbs.
# A pro-drop verb is a verb that is finite AND has NO child with relation "sub".
# Let's count them properly across Mark 1 to 4.

df_mark = df[df['book'] == 'MARK'].copy()

# Finite verbs: V- (indicative, subjunctive, optative, imperative) 
# Wait, PROIEL morph format is complex, let's just take POS 'V-' and look for personal endings.
# Or simpler: any token with POS starting with 'V' and NO child with relation "sub"
# Note that in PROIEL, children point to their head via 'head_id'.
sub_heads = set(df_mark[df_mark['relation'] == 'sub']['head_id'])

# Finite verbs: The 5th char in 'morphology' is the mood: i(ndicative), s(ubjunctive), o(ptative), m(imperative)
# Actually, the 3rd char in PROIEL POS is mood in some parsers?
# Let's just look at 'pos' which is usually 'V-' for verb
# and 'morphology' which looks like 'v3spia---' (3rd person singular present indicative active)
def is_finite(morph):
    if pd.isna(morph): return False
    # If the first character is 'v' and the second character is 1, 2, or 3, it's a finite verb
    return morph.startswith('v1') or morph.startswith('v2') or morph.startswith('v3')

finite_verbs = df_mark[df_mark['morphology'].apply(is_finite)]

pro_drop_verbs = finite_verbs[~finite_verbs['token_id'].isin(sub_heads)]
print(f"Total finite verbs in MARK: {len(finite_verbs)}")
print(f"Total pro-drop verbs in MARK: {len(pro_drop_verbs)}")

# Now, we only care about those that are PART OF A COREF CHAIN
# In PROIEL, 'antecedent_id' points to the previous mention.
# If a pro-drop verb has an antecedent_id, it means PROIEL annotators resolved it!
# Wait, PROIEL coreference is usually annotated on PRONOUNS and NOUNS. 
# Do they annotate the verb itself when the subject is dropped?
has_ant = pro_drop_verbs[pro_drop_verbs['antecedent_id'].notna()]
print(f"Pro-drop verbs with an antecedent_id: {len(has_ant)}")

# Also, a pro-drop verb might BE the antecedent for a subsequent mention.
is_ant = pro_drop_verbs[pro_drop_verbs['token_id'].isin(df_mark['antecedent_id'])]
print(f"Pro-drop verbs acting as antecedent: {len(is_ant)}")

combined = pd.concat([has_ant, is_ant]).drop_duplicates()
print(f"Total annotated pro-drop verbs in MARK: {len(combined)}")

# Generate sample of 20 
sample = combined.sample(min(20, len(combined)), random_state=42)

out_lines = []
for _, row in sample.iterrows():
    vid = row['token_id']
    vform = row['form']
    ref = row['ref']
    sent_id = row['sentence_id']
    
    current_sent_df = df_mark[df_mark['sentence_id'] == sent_id]
    context = " ".join(current_sent_df['form'].fillna(''))
    
    ant_id = row['antecedent_id']
    if pd.notna(ant_id):
        gold_df = df_mark[df_mark['token_id'] == ant_id]
        gold_answer = f"{gold_df['form'].values[0]} ({gold_df['lemma'].values[0]})" if len(gold_df)>0 else "UNKNOWN"
        role = "Anaphoric"
    else:
        # It's an antecedent itself
        ana_df = df_mark[df_mark['antecedent_id'] == vid]
        gold_answer = f"Is antecedent for: {ana_df['form'].values[0]} ({ana_df['lemma'].values[0]})" if len(ana_df)>0 else "UNKNOWN"
        role = "Antecedent"
        
    out_lines.append(f"REF: {ref}")
    out_lines.append(f"VERBE PRO-DROP: {vform} ({row['morphology']})")
    out_lines.append(f"ROLE PROIEL: {role}")
    out_lines.append(f"CONTEXTE: {context}")
    out_lines.append(f"GOLD: {gold_answer}")
    out_lines.append("-" * 60)

with open("project/data/experiments/prodrop_sample_20.txt", "w") as f:
    f.write("\n".join(out_lines))

