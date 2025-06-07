# Emotional Wellness API - Development Makefile
# Makes common tasks stupidly easy to run

.PHONY: help install test dev docker-up

help: ## Show help - because nobody remembers commands
	@echo "🔧 Development Commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make dev            - Start development server"
	@echo "  make docker-up      - Start with Docker"
	@echo "  make clean          - Clean build files"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-fast      - Run tests quickly"
	@echo "  make test-crisis    - Run crisis compliance tests"
	@echo "  make test-moss      - Run MOSS system tests"
	@echo "  make test-veluria   - Run VELURIA protocol tests"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make test-performance - Run performance benchmarks"
	@echo ""
	@echo "🐛 Debugging Commands:"
	@echo "  make debug          - Launch interactive debug CLI"
	@echo "  make debug-health   - System health check"
	@echo "  make debug-crisis   - Debug crisis intervention workflow"
	@echo "  make debug-moss     - Debug MOSS system components"
	@echo "  make debug-monitor  - Real-time system monitoring"
	@echo "  make debug-logs     - View recent application logs"
	@echo ""
	@echo "📊 Quality Commands:"
	@echo "  make lint           - Run code formatting and linting"
	@echo "  make security       - Run security checks"
	@echo "  make coverage       - Generate detailed coverage report"

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

# Enhanced Testing Commands
test-moss: ## Run MOSS system tests
	pytest tests/symbolic/moss/ -v --tb=short

test-veluria: ## Run VELURIA protocol tests
	pytest tests/symbolic/veluria/ tests/test_veluria/ -v --tb=short

test-integration: ## Run integration tests
	pytest tests/integration/ -v --tb=short

test-watch: ## Run tests in watch mode (requires pytest-watch)
	ptw --runner "pytest --tb=short" tests/

test-performance: ## Run performance benchmarks
	pytest tests/ -m performance -v --benchmark-only

# Debugging Commands
debug: ## Launch interactive debug CLI
	@echo "🐛 Launching debug CLI..."
	python scripts/debug_cli.py

debug-health: ## System health check
	@echo "🔍 Running system health check..."
	python scripts/debug_cli.py health

debug-crisis: ## Debug crisis intervention workflow
	@echo "🚨 Testing crisis intervention workflow..."
	python scripts/debug_cli.py test crisis

debug-moss: ## Debug MOSS system components
	@echo "🧠 Diagnosing MOSS system..."
	python scripts/debug_cli.py diagnose moss

debug-veluria: ## Debug VELURIA protocol system
	@echo "⚡ Diagnosing VELURIA system..."
	python scripts/debug_cli.py diagnose veluria

debug-monitor: ## Real-time system monitoring (30s)
	@echo "📊 Starting real-time monitoring..."
	python scripts/debug_cli.py monitor 30

debug-logs: ## View recent application logs
	@echo "📋 Recent application logs:"
	tail -n 50 logs/app.log 2>/dev/null || echo "No log file found. Start the application first."

# Quality Assurance Commands
lint: ## Run code formatting and linting
	@echo "🔍 Running code formatting and linting..."
	black src/ tests/ --check --diff
	flake8 src/ tests/
	mypy src/ --ignore-missing-imports

lint-fix: ## Fix code formatting issues
	@echo "🔧 Fixing code formatting..."
	black src/ tests/
	isort src/ tests/

security: ## Run security checks
	@echo "🔒 Running security checks..."
	bandit -r src/ -f json -o reports/security.json || true
	safety check --json --output reports/safety.json || true

coverage: ## Generate detailed coverage report
	@echo "📊 Generating coverage report..."
	pytest --cov=src --cov-report=html --cov-report=term --cov-report=xml
	@echo "Coverage report generated in htmlcov/index.html"

# Database Commands  
db-reset: ## Reset database (drop and recreate)
	@echo "🗄️ Resetting database..."
	python scripts/reset_db.py

db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	alembic upgrade head

db-seed: ## Seed database with test data
	@echo "🌱 Seeding database with test data..."
	python scripts/seed_db.py

# Development Helpers
logs-tail: ## Tail application logs in real-time
	tail -f logs/app.log

logs-error: ## Show recent error logs
	grep -i error logs/app.log | tail -n 20

check-deps: ## Check for outdated dependencies
	pip list --outdated

update-deps: ## Update dependencies (careful!)
	pip-review --auto

# Environment Setup
setup-dev: ## Complete development environment setup
	@echo "🚀 Setting up development environment..."
	python -m venv .venv
	@echo "Activate with: source .venv/bin/activate"
	make install
	make db-migrate
	@echo "✅ Development environment ready!"

# Performance Profiling
profile-api: ## Profile API performance
	@echo "📈 Profiling API performance..."
	python scripts/profile_api.py

profile-memory: ## Profile memory usage
	@echo "🧠 Profiling memory usage..."
	python -m memory_profiler scripts/memory_test.py

# Stress Testing  
stress-test: ## Run stress tests
	@echo "💪 Running stress tests..."
	python scripts/stress_test.py

load-test: ## Run load tests with locust
	@echo "🏋️ Running load tests..."
	locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 30s --host http://localhost:8000 
# Enhanced Debugging Commands
debug: ## Launch interactive debug CLI
	python scripts/debug_cli.py
