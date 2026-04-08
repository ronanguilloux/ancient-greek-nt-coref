import pandas as pd
import os

df = pd.read_csv("project/data/proiel_coref.csv")


# We want to extract specific verses. The citation format is like "JOHN 4.7"
def get_verse_range(book_prefix, chapter, start_v, end_v):
    verses = [f"{book_prefix} {chapter}.{v}" for v in range(start_v, end_v + 1)]
    return df[df["ref"].isin(verses)].copy()


samples = {
    "John_4_7_26": get_verse_range("JOHN", 4, 7, 26),
    "Mark_1_12_20": get_verse_range("MARK", 1, 12, 20),
    "Mark_1_1_4_26": get_verse_range("MARK", 1, 1, 26),
    "Acts_2_14_41": get_verse_range("ACTS", 2, 14, 41),
    "Acts_9_1_31": get_verse_range("ACTS", 9, 1, 31),
    "Acts_15_1_35": get_verse_range("ACTS", 15, 1, 35),
}

os.makedirs("project/data/gold", exist_ok=True)

for name, sample_df in samples.items():
    if sample_df.empty:
        print(f"Warning: No data found for {name}")
        continue

    # Generate CoNLL-U style format
    # Columns: ID, FORM, LEMMA, UPOS, XPOS, FEATS, HEAD, DEPREL, DEPS, MISC
    # In MISC, we'll put the PROIEL antecedent_id and coref_id if available

    conllu_lines = []
    current_sent_id = None
    token_counter = 1

    # We also need to map global token_id to sentence-level token counter
    global_to_local_id = {}

    for _, row in sample_df.iterrows():
        sent_id = row["sentence_id"]
        if sent_id != current_sent_id:
            conllu_lines.append(f"")
            conllu_lines.append(f"# sent_id = {sent_id}")
            conllu_lines.append(
                f"# text = {' '.join(sample_df[sample_df['sentence_id'] == sent_id]['form'].fillna(''))}"
            )
            current_sent_id = sent_id
            token_counter = 1

        tid = row["token_id"]
        form = row["form"]
        lemma = row["lemma"]
        pos = row["pos"]
        morph = row["morphology"]
        head = row["head_id"]
        deprel = row["relation"]
        ant_id = row["antecedent_id"]

        global_to_local_id[tid] = token_counter

        misc = f"Ref={row['ref']}"
        if pd.notna(ant_id):
            misc += f"|AntId={int(ant_id)}"

        conllu_lines.append(
            f"{token_counter}\t{form}\t{lemma}\t{pos}\t_\t{morph}\t{head}\t{deprel}\t_\t{misc}"
        )
        token_counter += 1

    out_path = f"project/data/gold/{name}.conllu"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(conllu_lines))
        f.write("\n")
    print(f"Saved {len(sample_df)} tokens to {out_path}")
