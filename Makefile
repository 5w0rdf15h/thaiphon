.PHONY: help dev test lint typecheck check format clean

SRC = src/thaiphon

## Show this help
help:
	@echo ""
	@echo "Available commands:"
	@echo "  make dev         Sync dev environment via uv"
	@echo "  make test        Run the pytest suite (tests/)"
	@echo "  make lint        Run ruff on $(SRC)"
	@echo "  make typecheck   Run mypy on $(SRC)"
	@echo "  make check       lint + typecheck"
	@echo "  make format      Auto-format with ruff"
	@echo "  make clean       Remove build artifacts"
	@echo ""

dev:
	uv sync

test:
	uv run pytest -q

lint:
	uv run ruff check $(SRC)

typecheck:
	uv run mypy $(SRC)

format:
	uv run ruff format $(SRC)

check: lint typecheck

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist *.egg-info
