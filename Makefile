.PHONY: setup audit clean eval-rules eval-llm extract-gold

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

$(VENV)/bin/activate: requirements.txt
	# Requires Python 3.12+
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

setup: $(VENV)/bin/activate

audit: setup
	$(PYTHON) scripts/proiel_audit.py proiel-treebank/data/greek-nt.xml --out ./proiel_audit/

# Sprint 2C - Pro-drop evaluation
extract-gold: setup
	$(PYTHON) scripts/extract_proiel_gold.py

eval-rules: setup
	$(PYTHON) scripts/evaluate_against_proiel_gold.py

eval-llm: setup
	$(PYTHON) scripts/evaluate_llm_against_proiel_gold.py

clean:
	rm -rf $(VENV)
