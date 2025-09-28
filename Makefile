.PHONY: help install dev test lint format type-check clean docker-up docker-down docker-logs docker-build docker-restart docker-clean docker-test

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e ".[dev]"

dev: ## Set up development environment
	pip install -e ".[dev]"
	pre-commit install

test: ## Run tests
	python backend/tests/test_basic.py
	@if command -v pytest >/dev/null 2>&1; then \
		pytest backend/tests/ -v; \
	else \
		echo "pytest not available, basic tests passed"; \
	fi

lint: ## Run linter
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check backend/; \
	else \
		echo "ruff not available, skipping linting"; \
	fi

format: ## Format code
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format backend/; \
	else \
		echo "ruff not available, skipping formatting"; \
	fi

type-check: ## Run type checker
	@if command -v mypy >/dev/null 2>&1; then \
		mypy backend/app/; \
	else \
		echo "mypy not available, skipping type checking"; \
	fi

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-up: ## Start development environment with Docker Compose
	docker compose up -d

docker-down: ## Stop development environment
	docker compose down

docker-logs: ## Show Docker Compose logs
	docker compose logs -f

docker-build: ## Build Docker images
	docker compose build --no-cache

docker-restart: ## Restart all services
	docker compose restart

docker-clean: ## Stop and remove all containers, networks, and volumes  
	docker compose down -v --remove-orphans

docker-test: ## Test Docker Compose configuration
	./test-docker-compose.sh