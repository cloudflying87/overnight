# OvernightApp Development Makefile

.PHONY: help install lint format type-check security test coverage clean

help:  ## Show this help message
	@echo "OvernightApp Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies (production + development)
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-hooks:  ## Install pre-commit git hooks
	pre-commit install
	@echo "✅ Pre-commit hooks installed!"

format:  ## Format code with black and isort
	@echo "🎨 Formatting code with black..."
	black apps config
	@echo "📦 Sorting imports with isort..."
	isort apps config
	@echo "✅ Code formatted!"

lint:  ## Run all linters
	@echo "🔍 Running flake8..."
	flake8 apps config
	@echo "🔍 Running pylint..."
	pylint apps config
	@echo "✅ Linting complete!"

type-check:  ## Run mypy type checker
	@echo "🔍 Running mypy type checker..."
	mypy apps config
	@echo "✅ Type checking complete!"

security:  ## Run security checks
	@echo "🔒 Running bandit security scanner..."
	bandit -r apps config -c pyproject.toml
	@echo "🔒 Checking for known security vulnerabilities..."
	safety check --json
	@echo "✅ Security checks complete!"

test:  ## Run tests with pytest
	@echo "🧪 Running tests..."
	pytest
	@echo "✅ Tests complete!"

coverage:  ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	pytest --cov --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated in htmlcov/index.html"

check-all:  ## Run all checks (format, lint, type-check, security, test)
	@echo "🚀 Running all checks..."
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) security
	@$(MAKE) test
	@echo "✅ All checks passed!"

migrate:  ## Run database migrations
	python manage.py migrate

makemigrations:  ## Create new migrations
	python manage.py makemigrations

runserver:  ## Start development server
	python manage.py runserver

shell:  ## Open Django shell
	python manage.py shell

superuser:  ## Create superuser
	python manage.py createsuperuser

collectstatic:  ## Collect static files
	python manage.py collectstatic --noinput

clean:  ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	@echo "✅ Cleanup complete!"

docker-build:  ## Build Docker images
	docker-compose build

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## Show Docker logs
	docker-compose logs -f web

docker-shell:  ## Access Docker container shell
	docker-compose exec web bash

# Development workflow
dev:  ## Quick development setup (install, migrate, runserver)
	@$(MAKE) install
	@$(MAKE) migrate
	@$(MAKE) collectstatic
	python manage.py runserver
