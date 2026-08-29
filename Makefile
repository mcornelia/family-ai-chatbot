PYTHON ?= $(shell command -v python3.11 2>/dev/null || command -v python3)
PYCACHE ?= /tmp/family-ai-chatbot-pycache

.PHONY: test compile shellcheck check

test:
	PYTHONPYCACHEPREFIX="$(PYCACHE)" "$(PYTHON)" -m unittest discover -s tests -v

compile:
	PYTHONPYCACHEPREFIX="$(PYCACHE)" "$(PYTHON)" -m py_compile courier.py

shellcheck:
	bash -n install.sh

check: compile shellcheck test
