import xml.etree.ElementTree as ET
import pandas as pd
from collections import defaultdict
import os

def parse_proiel_xml(xml_path):
    print(f"Parsing {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    rows = []
    
    # <source> contains <divs> which contain <sentences>
    for sentence in root.iter("sentence"):
        sent_id = sentence.get("id")
        
        for token in sentence.iter("token"):
            form = token.get("form")
            if not form:
                continue
                
            citation = token.get("citation-part", "")
            book = citation.split(" ")[0] if citation else "UNKNOWN"
            ref = citation
            
            rows.append({
                "book": book,
                "ref": ref,
                "sentence_id": sent_id,
                "token_id": token.get("id"),
                "form": form,
                "lemma": token.get("lemma"),
                "pos": token.get("part-of-speech"),
                "morphology": token.get("morphology"),
                "relation": token.get("relation"),
                "head_id": token.get("head-id"),
                "antecedent_id": token.get("antecedent-id"),
                "info_status": token.get("information-status"),
            })
            
    df = pd.DataFrame(rows)
    print(f"Parsed {len(df)} tokens.")
    return df

if __name__ == "__main__":
    df = parse_proiel_xml("proiel-treebank/data/greek-nt.xml")
    out_path = "project/data/proiel_coref.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    
    # Quick sanity check on JOHN and MARK
    print("\nSanity Check: Mentions with antecedents in JOHN:")
    print(df[(df["book"] == "JOHN") & df["antecedent_id"].notna()]["lemma"].value_counts().head(5))
