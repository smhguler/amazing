PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
CONFIG ?= config.txt
MLX_WHEEL := vendor/mlx/ubuntu/mlx-2.2-py3-none-any.whl
PIP := "$(PYTHON)" -m pip --python "$(VENV_PY)"
DEV_READY := $(VENV)/.dev-ready
MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs

.PHONY: install install-dev run debug clean lint lint-strict package

$(VENV_PY):
	"$(PYTHON)" -m venv --without-pip "$(VENV)"

install: $(VENV_PY)
	$(PIP) install --no-deps "$(MLX_WHEEL)"
	"$(VENV_PY)" tools/check_mlx.py

install-dev: $(DEV_READY)

$(DEV_READY): $(VENV_PY) Makefile
	$(PIP) install --only-binary=:all: flake8 mypy build 'setuptools>=77'
	touch "$(DEV_READY)"

run: $(VENV_PY)
	"$(VENV_PY)" a_maze_ing.py "$(CONFIG)"

debug: $(VENV_PY)
	"$(VENV_PY)" -m pdb a_maze_ing.py "$(CONFIG)"

clean:
	find . -name .git -prune -o -name .venv -prune -o \
		-type d -name __pycache__ -prune -exec rm -rf -- {} +
	rm -rf -- .mypy_cache .pytest_cache build dist mazegen.egg-info

lint: $(DEV_READY)
	"$(VENV_PY)" -m flake8 .
	"$(VENV_PY)" -m mypy . $(MYPY_FLAGS)

lint-strict: $(DEV_READY)
	"$(VENV_PY)" -m flake8 .
	"$(VENV_PY)" -m mypy . --strict

package: $(DEV_READY)
	"$(VENV_PY)" -m build --no-isolation --wheel --outdir .
