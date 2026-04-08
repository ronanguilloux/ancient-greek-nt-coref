import pandas as pd

class CharacterRegistry:
    def __init__(self, aliases_path):
        self.aliases_df = pd.read_csv(aliases_path, sep="\t")
        self.registry = {}
        
        # Pre-build lookup map for fast resolution: lemma -> canonical_id
        self.alias_map = dict(zip(self.aliases_df["lemma"], self.aliases_df["canonical_id"]))
        
    def resolve_lemma(self, lemma):
        """
        Rule 1: If in aliases, return canonical_id.
        Rule 2: Else, uppercase the lemma to create a provisional canonical_id.
        """
        if lemma in self.alias_map:
            return self.alias_map[lemma]
        return lemma.upper()
        
    def register_mention(self, mention_id, lemma, attributes=None):
        canonical_id = self.resolve_lemma(lemma)
        
        if canonical_id not in self.registry:
            self.registry[canonical_id] = {
                "mentions": [],
                "attributes": attributes or {}
            }
        
        self.registry[canonical_id]["mentions"].append(mention_id)
        return canonical_id

if __name__ == "__main__":
    registry = CharacterRegistry("project/lexicons/character_aliases.tsv")
    
    mentions_to_process = [
        {"id": 1, "lemma": "Ἰησοῦς", "form": "Ἰησοῦς", "pos": "NOUN"},
        {"id": 5, "lemma": "Ἰησοῦς", "form": "Ἰησοῦν", "pos": "NOUN"}, # Accusative
        {"id": 12, "lemma": "Σίμων", "form": "Σίμωνα", "pos": "NOUN"},
        {"id": 15, "lemma": "Πέτρος", "form": "Πέτρῳ", "pos": "NOUN"},
        {"id": 18, "lemma": "Μαριάμ", "form": "Μαριάμ", "pos": "NOUN"},
        {"id": 20, "lemma": "Φίλιππος", "form": "Φιλίππῳ", "pos": "NOUN"} # Not in alias
    ]
    
    print("\n--- SPRINT 2A: Character Clustering ---")
    for m in mentions_to_process:
        canon_id = registry.register_mention(m["id"], m["lemma"])
        print(f"Mention {m['id']} (form: {m['form']:<8}, lemma: {m['lemma']:<8}) -> RESOLVED CLUSTER: {canon_id}")
        
    print("\n--- Final Character Registry ---")
    for canon_id, data in registry.registry.items():
        print(f"Cluster: {canon_id:<10} | Mention IDs: {data['mentions']}")
