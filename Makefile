.PHONY: help install install-backend install-ops build ops-build test test-py test-js clean

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
NPM ?= npm

help:
	@echo "Seo Trum / Auto_social developer commands"
	@echo ""
	@echo "  make install       Install backend and Ops frontend dependencies"
	@echo "  make build         Build the Ops frontend"
	@echo "  make test          Run Python and JavaScript test suites"
	@echo "  make test-py       Run Python tests"
	@echo "  make test-js       Run JavaScript tests"
	@echo "  make clean         Remove local build/cache output"

install: install-backend install-ops

install-backend:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-ops:
	$(NPM) --prefix ops install

build: ops-build

ops-build:
	$(NPM) --prefix ops run build

test: test-py test-js

test-py:
	$(PYTHON) -m pytest tests/python

test-js:
	$(PYTHON) tests/run.py --js

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in map(pathlib.Path, ['ops/dist', '.pytest_cache'])]"
