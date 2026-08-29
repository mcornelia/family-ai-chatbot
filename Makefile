PYTHON ?= $(shell command -v python3.11 2>/dev/null || command -v python3)
PYCACHE ?= /tmp/family-ai-chatbot-pycache

.PHONY: test compile check

test:
	PYTHONPYCACHEPREFIX="$(PYCACHE)" "$(PYTHON)" -m unittest discover -s tests -v

compile:
	PYTHONPYCACHEPREFIX="$(PYCACHE)" "$(PYTHON)" -m py_compile courier.py

check: compile test
