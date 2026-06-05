# Ghostrace Backend — Developer Makefile
#
# Usage:
#   make dev        — start the backend in hot-reload mode
#   make test       — run the test suite
#   make lint       — run ruff linter
#   make fmt        — auto-format with ruff
#   make clean      — remove __pycache__ and .pytest_cache

.PHONY: dev test lint fmt clean install

VENV_PYTHON ?= .venv/Scripts/python.exe
ifeq ($(shell uname -s 2>/dev/null),Linux)
    VENV_PYTHON = .venv/bin/python
endif
ifeq ($(shell uname -s 2>/dev/null),Darwin)
    VENV_PYTHON = .venv/bin/python
endif

install:
	pip install -r backend/requirements.txt

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest backend/tests -v --tb=short

test-cov:
	pytest backend/tests -v --cov=backend/app --cov-report=term-missing

lint:
	ruff check backend/

fmt:
	ruff format backend/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
