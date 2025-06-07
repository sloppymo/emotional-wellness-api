# Emotional Wellness API - Development Makefile
# Makes common tasks stupidly easy to run

.PHONY: help install test lint clean dev docker-up docker-down reset-db

help: ## Show this help message - because nobody remembers all the commands
	@echo "Emotional Wellness API Development Commands"
	@echo "==========================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies - everything you need to get started
	@echo "🔧 Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r requirements-test.txt
	@echo "✅ Dependencies installed"

install-symbolic: ## Install symbolic processing dependencies - the AI stuff
	@echo "🧠 Installing symbolic AI dependencies..."
	pip install -r requirements-symbolic.txt
	@echo "✅ Symbolic dependencies installed"

test: ## Run all tests - the full test suite
	@echo "🧪 Running tests..."
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "✅ Tests complete. Check htmlcov/index.html for coverage report"

test-fast: ## Run tests without coverage - when you just want to know if it works
	@echo "⚡ Running fast tests..."
	pytest -x --tb=short
	@echo "✅ Fast tests complete"

test-crisis: ## Run crisis compliance tests - the important ones
	@echo "🚨 Running crisis compliance tests..."
	pytest tests/test_crisis_compliance.py -v
	@echo "✅ Crisis tests complete"

lint: ## Run linting and formatting - make the code pretty
	@echo "🎨 Running linters..."
	black src tests
	isort src tests
	flake8 src tests
	@echo "✅ Code formatted and linted"

clean: ## Clean up build artifacts - remove the crud
	@echo "🧹 Cleaning up..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

dev: ## Start development server - the main thing you'll use
	@echo "🚀 Starting development server..."
	@echo "Dashboard: http://localhost:8000/dashboard"
	@echo "API Docs: http://localhost:8000/docs"
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-full: ## Start full development stack - api + workers + redis
	@echo "🚀 Starting full development stack..."
	docker-compose up -d redis postgres
	@echo "⏳ Waiting for services to start..."
	sleep 5
	@echo "🔄 Starting background workers..."
	celery -A src.tasks.celery_app worker --loglevel=info --detach
	celery -A src.tasks.celery_app beat --loglevel=info --detach
	@echo "🌐 Starting API server..."
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-up: ## Start all services with Docker - the lazy way
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started. API at http://localhost:8000"

docker-down: ## Stop all Docker services - turn it off
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped"

docker-logs: ## Show Docker logs - when things break
	@echo "📜 Showing Docker logs..."
	docker-compose logs -f

reset-db: ## Reset database with fresh migrations - nuclear option
	@echo "💥 Resetting database..."
	@echo "⚠️  This will destroy all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "✅ Database reset complete"; \
	else \
		echo ""; \
		echo "❌ Reset cancelled"; \
	fi

migrate: ## Run database migrations - when schema changes
	@echo "🗄️  Running database migrations..."
	alembic upgrade head
	@echo "✅ Migrations complete"

shell: ## Start Python shell with app context - for debugging
	@echo "🐍 Starting Python shell..."
	python -c "from src.main import app; import asyncio; print('App loaded. Use app variable.')"

logs: ## Show application logs - when you need to debug
	@echo "📋 Showing recent logs..."
	tail -f logs/app.log

check-env: ## Verify environment setup - make sure everything's configured
	@echo "🔍 Checking environment..."
	@python -c "from src.config.settings import get_settings; s=get_settings(); print('✅ Database URL:', s.DATABASE_URL[:20]+'...'); print('✅ Redis URL:', s.REDIS_URL); print('✅ JWT Secret:', 'SET' if s.JWT_SECRET_KEY else 'MISSING')"

debug-crisis: ## Debug crisis detection with sample data - test the AI
	@echo "🧠 Testing crisis detection..."
	@python -c "
import asyncio
from src.symbolic.crisis.vectorized_detector import VectorizedCrisisDetector
async def test():
    detector = VectorizedCrisisDetector()
    result = await detector.detect_crisis_patterns('I want to hurt myself')
    print('Crisis detected:', result.detected)
    print('Severity:', result.severity)
    print('Confidence:', result.confidence)
asyncio.run(test())
"

performance: ## Run performance tests - check if it's fast enough
	@echo "⚡ Running performance tests..."
	pytest tests/performance/ -v
	@echo "✅ Performance tests complete"

security: ## Run security scans - make sure we're not leaking data
	@echo "🔒 Running security checks..."
	bandit -r src/
	safety check
	@echo "✅ Security scan complete"

docs: ## Generate documentation - make it readable
	@echo "📚 Generating documentation..."
	@echo "API docs available at http://localhost:8000/docs when server is running"
	@echo "✅ Documentation ready"

quick-start: install migrate dev ## Complete setup for new developers - everything in one command
	@echo "🎉 Quick start complete! Happy coding!" 