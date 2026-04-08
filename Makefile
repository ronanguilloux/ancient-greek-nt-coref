.PHONY: setup audit clean

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

clean:
	rm -rf $(VENV)
