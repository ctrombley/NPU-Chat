# Makefile for NPU Chat project

.PHONY: help test lint lint-fix build-frontend lint-frontend test-frontend run all install install-test clean

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt
	cd frontend && npm install

install-test: ## Install dependencies including test tools
	pip install -r requirements-test.txt
	cd frontend && npm install

test: ## Run Python unit and integration tests
	python3 -m pytest tests

lint: ## Run Python linting with ruff
	ruff check .

lint-fix: ## Run Python linting with ruff and auto-fix
	ruff check . --fix

build-frontend: ## Build the React frontend
	cd frontend && npm run build

lint-frontend: ## Run frontend linting
	cd frontend && npm run lint

test-frontend: ## Run frontend unit tests
	cd frontend && npm run test

run: ## Run the Flask application
	python3 npuchat.py

all: lint lint-frontend test test-frontend ## Run all linting and tests

clean: ## Clean build artifacts
	rm -rf static/dist
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

