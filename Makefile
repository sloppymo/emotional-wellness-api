# Emotional Wellness API - Development Makefile
# Makes common tasks stupidly easy to run

.PHONY: help install test dev docker-up

help: ## Show help - because nobody remembers commands
	@echo "Development Commands:"
	@echo "  make install     - Install all dependencies"
	@echo "  make test        - Run tests with coverage"
	@echo "  make test-fast   - Run tests quickly"
	@echo "  make test-crisis - Run crisis compliance tests"
	@echo "  make dev         - Start development server"
	@echo "  make docker-up   - Start with Docker"
	@echo "  make clean       - Clean build files"

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-test.txt

test: ## Run all tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term

test-fast: ## Quick test run
	pytest -x --tb=short

test-crisis: ## Run crisis tests
	pytest tests/test_crisis_compliance.py -v

dev: ## Start development server
	@echo "🚀 Starting server at http://localhost:8000"
	@echo "📊 Dashboard: http://localhost:8000/dashboard"
	@echo "📖 API Docs: http://localhost:8000/docs"
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-up: ## Start with Docker
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

clean: ## Clean build artifacts
	rm -rf __pycache__ .pytest_cache htmlcov .coverage
	find . -name "*.pyc" -delete

quick-start: install ## Complete setup
	@echo "🎉 Ready! Run 'make dev' to start" 