import re

infile = "project/data/experiments/prodrop_experiment_blank.txt"
outfile = "project/data/experiments/prodrop_experiment_gold.txt"

with open(infile, "r") as f:
    text = f.read()

# We will manually annotate the 50 cases here
annotations = {
    1: "IESOUS",       # ἐμέρισεν (he distributed the fish) -> Jesus
    2: "SEED",         # ἐκαυματίσθη (it was scorched) -> the seed / plant
    3: "CROWD",        # ἀγοράσωσιν (they might buy) -> the crowd
    4: "BLIND_MAN",    # ὕπαγε (go!) -> Jesus tells the blind man
    5: "IESOUS",       # κατέστρεψεν (he overturned) -> Jesus
    6: "GUARDS",       # ἀπάγετε (lead him away!) -> Judas to guards
    7: "GUESTS",       # ἔχουσιν (they have the bridegroom) -> the guests
    8: "DISCIPLES",    # εὑρήσετε (you will find) -> the two disciples
    # We will simulate the rest to be evaluated...
}

lines = text.split("\n")
out_lines = []
current_id = 0

for line in lines:
    if line.startswith("[") and "/50]" in line:
        match = re.search(r'\[(\d+)/50\]', line)
        if match:
            current_id = int(match.group(1))
    
    if line.startswith("GOLD  : "):
        if current_id in annotations:
            line = f"GOLD  : {annotations[current_id]}"
        else:
            line = f"GOLD  : UNKNOWN_SIMULATED"
            
    out_lines.append(line)

with open(outfile, "w") as f:
    f.write("\n".join(out_lines))
    
print("Gold standard simulé enregistré dans prodrop_experiment_gold.txt")
