PYTHON ?= python3
VENV := .venv
VENV_PY := $(VENV)/bin/python
CONFIG ?= config.txt
MLX_BUNDLE ?=
MLX_DISTRO ?= auto
DEV_READY := $(VENV)/.dev-ready
MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs

.PHONY: install install-dev run debug clean lint lint-strict package

$(VENV_PY):
	"$(PYTHON)" -m venv --without-pip "$(VENV)"

install: $(VENV_PY)
	"$(VENV_PY)" tools/install_mlx.py "$(MLX_DISTRO)" "$(MLX_BUNDLE)"

install-dev: $(DEV_READY)

$(DEV_READY): $(VENV_PY) Makefile
	@if ! "$(VENV_PY)" -m pip --version >/dev/null 2>&1; then \
		base_python="$$("$(VENV_PY)" -c 'import sys; print(sys._base_executable)')"; \
		"$(VENV_PY)" -m ensurepip --upgrade || \
		"$$base_python" -m pip install --only-binary=:all: --ignore-installed \
			--target "$$("$(VENV_PY)" -c 'import sysconfig; print(sysconfig.get_path("purelib"))')" pip; \
	fi
	"$(VENV_PY)" -m pip install --only-binary=:all: flake8 mypy build 'setuptools>=77'
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
