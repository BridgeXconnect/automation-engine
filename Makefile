# Makefile for automation package testing and development

.PHONY: help install test test-unit test-integration test-e2e test-all test-cov test-fast test-slow lint format check clean docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install        Install all dependencies"
	@echo "  test           Run all tests"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-e2e       Run end-to-end tests only"
	@echo "  test-models    Run model validation tests"
	@echo "  test-modules   Run business module tests"
	@echo "  test-cov       Run tests with coverage report"
	@echo "  test-fast      Run fast tests only"
	@echo "  test-slow      Run slow tests only"
	@echo "  test-parallel  Run tests in parallel"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code"
	@echo "  check          Run all checks (lint, format, test)"
	@echo "  clean          Clean up build artifacts"
	@echo "  docs           Generate documentation"
	@echo "  validate       Validate a specific package"

# Installation
install:
	pip install -r requirements.txt
	pip install -r tests/requirements-test.txt

install-dev:
	pip install -r requirements.txt
	pip install -r tests/requirements-test.txt
	pip install -e .

# Testing targets
test:
	pytest

test-unit:
	pytest -m "unit or models or modules" -v

test-integration:
	pytest -m "integration or notion or n8n" -v

test-e2e:
	pytest -m "e2e" -v

test-models:
	pytest tests/test_models.py -v

test-modules:
	pytest tests/test_modules.py -v

test-integrations:
	pytest tests/test_integrations.py -v

test-end-to-end:
	pytest tests/test_end_to_end.py -v

test-all:
	pytest --cov=src --cov-report=html --cov-report=term-missing -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing --cov-branch --cov-fail-under=80

test-fast:
	pytest -m "not slow" -v

test-slow:
	pytest -m "slow" -v

test-parallel:
	pytest -n auto

test-performance:
	pytest -m "performance" -v --benchmark-only

test-regression:
	pytest -m "regression" -v

# Specific test categories
test-validation:
	pytest -m "validation" -v

test-fixtures:
	pytest -m "fixtures" -v

# Test with different levels of verbosity
test-quiet:
	pytest -q

test-verbose:
	pytest -vv

test-debug:
	pytest -vv --tb=long --capture=no

# Linting and formatting
lint:
	flake8 src/ tests/
	pylint src/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Combined checks
check: format-check lint test

check-all: format-check lint test-all

# Package validation
validate:
	@if [ -z "$(PACKAGE)" ]; then \
		echo "Usage: make validate PACKAGE=<package-slug>"; \
		exit 1; \
	fi
	@echo "Validating package: $(PACKAGE)"
	python -c "from src.modules.validation import WorkflowValidator; from pathlib import Path; validator = WorkflowValidator(); print('Package validation complete')"

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

clean-test:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Documentation
docs:
	sphinx-build -b html docs/ docs/_build/html

docs-clean:
	rm -rf docs/_build/

# Development helpers
dev-setup: install-dev
	pre-commit install
	@echo "Development environment setup complete"

# Watch mode (requires pytest-watch)
test-watch:
	ptw -- --testmon

# Generate test report
test-report:
	pytest --html=reports/report.html --self-contained-html --cov=src --cov-report=html:reports/coverage

# Benchmark tests
benchmark:
	pytest --benchmark-only --benchmark-sort=mean

# Security testing
test-security:
	bandit -r src/
	safety check

# Type checking
type-check:
	mypy src/ --strict

# Coverage targets
coverage:
	pytest --cov=src --cov-report=term-missing --cov-branch

coverage-html:
	pytest --cov=src --cov-report=html --cov-branch
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml:
	pytest --cov=src --cov-report=xml --cov-branch

# CI/CD targets
ci-test:
	pytest --cov=src --cov-report=xml --junitxml=reports/junit.xml -v

ci-check: format-check lint type-check test-all

# Package building and distribution
build:
	python -m build

upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*

# Environment info
env-info:
	@echo "Python version:"
	@python --version
	@echo "Pip version:"
	@pip --version
	@echo "Pytest version:"
	@pytest --version
	@echo "Installed packages:"
	@pip list | grep -E "(pytest|pydantic|fastapi|notion)"

# Database and service setup (if needed)
setup-services:
	docker-compose up -d

teardown-services:
	docker-compose down

# Test data generation
generate-test-data:
	python scripts/generate_test_data.py

# Profile tests
profile-tests:
	pytest --profile --profile-svg

# Memory profiling
memory-profile:
	pytest --memprof

# Example usage targets
example-test:
	@echo "Running example test workflow..."
	python -c "from tests.conftest import *; print('Test fixtures loaded successfully')"

# Help with specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=tests/test_models.py"; \
		exit 1; \
	fi
	pytest $(FILE) -v

# Run specific test method
test-method:
	@if [ -z "$(METHOD)" ]; then \
		echo "Usage: make test-method METHOD=test_package_creation"; \
		exit 1; \
	fi
	pytest -k $(METHOD) -v