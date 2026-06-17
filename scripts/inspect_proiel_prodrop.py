import pandas as pd
df = pd.read_csv("project/data/proiel_coref.csv")
df_mark = df[df['book'] == 'MARK'].copy()

# Print POS tags that HAVE an antecedent_id
print(df_mark[df_mark['antecedent_id'].notna()]['pos'].value_counts())

