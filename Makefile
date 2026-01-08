.PHONY: help install dev test lint typecheck check format clean

PYTHON ?= python
PIP ?= $(PYTHON) -m pip

SRC = src/thaiphon
TESTS = tests

## Show this help
help:
	@echo ""
	@echo "Available commands:"
	@echo "  make install     Install package (editable)"
	@echo "  make dev         Install package with dev dependencies"
	@echo "  make test        Run tests (pytest)"
	@echo "  make lint        Run ruff"
	@echo "  make typecheck   Run mypy"
	@echo "  make check       Run all checks (test + lint + typecheck)"
	@echo "  make format      Auto-fix with ruff (if configured)"
	@echo "  make clean       Remove build artifacts"
	@echo ""

## Install package (editable)
install:
	$(PIP) install -e .

## Install package with dev dependencies
dev:
	$(PIP) install -e ".[dev]"

## Run tests
test:
	pytest -q

## Lint code
lint:
	ruff check .

## Type checking
typecheck:
	mypy $(SRC)

## Run all checks
check: test lint typecheck

## Auto-fix formatting (optional)
format:
	black .
	isort .

format-check:
	black --check .
	isort --check-only .


## Clean build artifacts
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist *.egg-info
