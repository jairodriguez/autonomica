# Autonomica API Makefile
# Provides convenient commands for development and code quality

.PHONY: help install install-dev test test-cov lint format type-check security complexity coverage quality clean auto-fix pre-commit install-hooks

# Default target
help:
	@echo "🚀 Autonomica API Development Commands"
	@echo "======================================"
	@echo ""
	@echo "📦 Installation:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  install-hooks  Install pre-commit hooks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage"
	@echo "  test-integration Run integration tests"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint           Run all linting tools"
	@echo "  format         Format code with Black and isort"
	@echo "  type-check     Run MyPy type checking"
	@echo "  security       Run security scanning"
	@echo "  complexity     Run complexity analysis"
	@echo "  coverage       Run coverage analysis"
	@echo "  quality        Run all code quality checks"
	@echo "  auto-fix       Auto-fix formatting issues"
	@echo ""
	@echo "🔄 Pre-commit:"
	@echo "  pre-commit     Run pre-commit on all files"
	@echo ""
	@echo "🧹 Maintenance:"
	@echo "  clean          Clean up generated files"
	@echo "  update-deps    Update dependencies"
	@echo ""
	@echo "📊 Reports:"
	@echo "  report         Generate comprehensive quality report"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

install-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Testing
test:
	pytest -v --tb=short

test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml

test-integration:
	python run_integration_tests.py

# Code Quality
lint:
	@echo "🔍 Running linting checks..."
	flake8 --max-line-length=88 --extend-ignore=E203,W503 .
	mypy --ignore-missing-imports app/

format:
	@echo "🎨 Formatting code..."
	black --line-length=88 .
	isort --profile=black --line-length=88 .

type-check:
	@echo "🔍 Running type checking..."
	mypy --ignore-missing-imports --show-error-codes app/

security:
	@echo "🔒 Running security scanning..."
	bandit -r . -f json -o bandit-report.json --exclude tests/,venv/,.venv/,env/,.env/
	safety check --output json --save safety-report.json

complexity:
	@echo "🧮 Running complexity analysis..."
	radon cc app --min A --json
	xenon --max-absolute-complexity=10 --max-average-complexity=5 app

coverage:
	@echo "📊 Running coverage analysis..."
	coverage run --source=app --omit=*/tests/*,*/venv/*,*/env/* -m pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=70

quality:
	@echo "🚀 Running comprehensive code quality checks..."
	python run_code_quality.py

auto-fix:
	@echo "🔧 Auto-fixing code quality issues..."
	python run_code_quality.py --auto-fix

# Pre-commit
pre-commit:
	@echo "🔄 Running pre-commit on all files..."
	pre-commit run --all-files

# Maintenance
clean:
	@echo "🧹 Cleaning up generated files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "bandit-report.json" -delete
	find . -type f -name "safety-report.json" -delete
	find . -type f -name ".mypy_cache" -exec rm -rf {} +
	@echo "✅ Cleanup completed"

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

# Reports
report:
	@echo "📊 Generating comprehensive quality report..."
	python run_code_quality.py

# Development workflow
dev-setup: install-dev install-hooks
	@echo "✅ Development environment setup completed"

quick-check: format lint type-check
	@echo "✅ Quick quality check completed"

full-check: quality test-cov
	@echo "✅ Full quality check completed"

# CI/CD helpers
ci-test:
	@echo "🚀 Running CI test suite..."
	pytest --cov=app --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

ci-quality:
	@echo "🚀 Running CI quality checks..."
	python run_code_quality.py --check formatting
	python run_code_quality.py --check linting
	python run_code_quality.py --check type
	python run_code_quality.py --check security

# Docker helpers
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t autonomica-api .

docker-test:
	@echo "🐳 Running tests in Docker..."
	docker run --rm autonomica-api make test

docker-quality:
	@echo "🐳 Running quality checks in Docker..."
	docker run --rm autonomica-api make quality

# Performance testing
perf-test:
	@echo "⚡ Running performance tests..."
	pytest --benchmark-only --benchmark-skip

# Documentation
docs:
	@echo "📚 Building documentation..."
	sphinx-build -b html docs/ docs/_build/html

docs-serve:
	@echo "📚 Serving documentation..."
	cd docs/_build/html && python -m http.server 8001

# Database
db-migrate:
	@echo "🗄️  Running database migrations..."
	alembic upgrade head

db-rollback:
	@echo "🗄️  Rolling back database..."
	alembic downgrade -1

# Environment
env-check:
	@echo "🔍 Checking environment variables..."
	python -c "import os; print('Environment check:'); [print(f'  {k}={v}') for k, v in os.environ.items() if k.startswith(('AUTONOMICA', 'REDIS', 'DATABASE', 'OPENAI', 'CLERK'))]"

# Monitoring
monitor:
	@echo "📊 Starting monitoring..."
	python -m app.monitoring

# Health check
health:
	@echo "🏥 Running health checks..."
	curl -f http://localhost:8000/health || echo "API not responding"
	redis-cli ping || echo "Redis not responding"

# Backup
backup:
	@echo "💾 Creating backup..."
	tar -czf "backup-$(date +%Y%m%d-%H%M%S).tar.gz" app/ tests/ requirements*.txt pyproject.toml

# Restore
restore:
	@echo "📥 Restoring from backup..."
	@read -p "Enter backup filename: " backup_file; \
	tar -xzf "$$backup_file"

# Help for specific targets
lint-help:
	@echo "🔍 Linting Configuration:"
	@echo "  - Flake8: .flake8 or pyproject.toml"
	@echo "  - MyPy: pyproject.toml"
	@echo "  - Black: pyproject.toml"
	@echo "  - isort: pyproject.toml"

format-help:
	@echo "🎨 Formatting Configuration:"
	@echo "  - Black: 88 character line length"
	@echo "  - isort: Black-compatible profile"
	@echo "  - Pre-commit hooks configured"

security-help:
	@echo "🔒 Security Tools:"
	@echo "  - Bandit: Python security linter"
	@echo "  - Safety: Dependency vulnerability checker"
	@echo "  - Reports saved to JSON files"

# Shortcuts
f: format
l: lint
t: test
q: quality
c: clean
h: help