SHELL := /bin/bash
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python3

.PHONY: install run debug clean lint lint-strict

install:
	@python3 -m venv $(VENV_DIR)
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install flake8 mypy
	@VENV_DIR="$(abspath $(VENV_DIR))" $(SHELL) --noprofile --rcfile <(printf '%s\n' \
		'source "$$VENV_DIR/bin/activate"' \
		'finish() { deactivate; rm -rf "$$VENV_DIR"; exit; }') -i

run:
	@if [ ! -d "$(VENV_DIR)" ]; then python3 -m venv "$(VENV_DIR)"; fi
	@. "$(VENV_DIR)/bin/activate"; \
		python3 main.py

debug:
	@if [ ! -d "$(VENV_DIR)" ]; then python3 -m venv "$(VENV_DIR)"; fi
	@. "$(VENV_DIR)/bin/activate"; \
		trap 'deactivate' EXIT; \
		python3 -m pdb main.py

clean:
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@rm -rf .mypy_cache .pytest_cache $(VENV_DIR)

lint:
	@if [ ! -d "$(VENV_DIR)" ]; then python3 -m venv "$(VENV_DIR)"; fi
	@. "$(VENV_DIR)/bin/activate"; \
		trap 'deactivate' EXIT; \
		flake8 . --exclude='venv'; \
		python3 -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@if [ ! -d "$(VENV_DIR)" ]; then python3 -m venv "$(VENV_DIR)"; fi
	@. "$(VENV_DIR)/bin/activate"; \
		trap 'deactivate' EXIT; \
		flake8 . --exclude='venv'; \
		python3 -m mypy . --strict
