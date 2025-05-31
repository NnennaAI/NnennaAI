# Makefile for NnennaAI development

.PHONY: help install install-dev test lint format clean build docs serve-docs

# Default target
help:
	@echo "🧠 NnennaAI Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install package in production mode"
	@echo "  make install-dev  Install package in development mode with all extras"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests with coverage"
	@echo "  make lint         Run linting checks"
	@echo "  make format       Format code with black and isort"
	@echo "  make type-check   Run mypy type checking"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs         Build documentation"
	@echo "  make serve-docs   Serve documentation locally"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        Remove build artifacts and caches"
	@echo "  make build        Build distribution packages"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[all]"
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=modules --cov=cli --cov-report=html --cov-report=term

test-fast:
	pytest tests/ -v -m "not slow"

# Code quality
lint:
	ruff check modules/ cli/ tests/
	black --check modules/ cli/ tests/
	isort --check-only modules/ cli/ tests/

format:
	black modules/ cli/ tests/
	isort modules/ cli/ tests/
	ruff check --fix modules/ cli/ tests/

type-check:
	mypy modules/ cli/

# Documentation
docs:
	mkdocs build

serve-docs:
	mkdocs serve

# Build and distribution
build:
	python -m build

publish-test:
	python -m twine upload --repository testpypi dist/*

publish:
	python -m twine upload dist/*

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf venv/
	rm -rf .nai/

# Development workflow
dev-setup: install-dev
	@echo "✅ Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code quality"

# Quick checks before committing
pre-commit: format lint type-check test
	@echo "✅ All checks passed! Ready to commit."

# Show current version
version:
	@python -c "from cli import __version__; print(__version__)"

# Create a new release
release:
	@echo "Current version: $$(make version)"
	@read -p "New version: " VERSION && \
		sed -i '' "s/version = \".*\"/version = \"$$VERSION\"/" pyproject.toml && \
		sed -i '' "s/__version__ = \".*\"/__version__ = \"$$VERSION\"/" cli/__init__.py && \
		sed -i '' "s/__version__ = \".*\"/__version__ = \"$$VERSION\"/" modules/__init__.py && \
		git add pyproject.toml cli/__init__.py modules/__init__.py && \
		git commit -m "Bump version to $$VERSION" && \
		git tag -a "v$$VERSION" -m "Release version $$VERSION" && \
		echo "✅ Version bumped to $$VERSION"
		echo "Run 'git push --tags' to push the release"