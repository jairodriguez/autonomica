# Code Quality Framework

## Overview

This document describes the comprehensive code quality framework implemented for the Autonomica project. The framework ensures consistent code style, maintains high code quality standards, and provides automated tools for code analysis, formatting, and validation.

## Architecture

### Backend Code Quality Tools
- **Location**: `autonomica-api/`
- **Languages**: Python
- **Tools**: Black, isort, Flake8, MyPy, Bandit, Safety, Radon, Xenon
- **Configuration**: `pyproject.toml`, `.pre-commit-config.yaml`

### Frontend Code Quality Tools
- **Location**: `autonomica-frontend/`
- **Languages**: TypeScript, JavaScript, CSS/SCSS
- **Tools**: ESLint, Prettier, Stylelint, TypeScript Compiler
- **Configuration**: `.eslintrc.js`, `.prettierrc`, `.stylelintrc`

## Backend Code Quality Tools

### 1. Code Formatting

#### Black
- **Purpose**: Uncompromising Python code formatter
- **Configuration**: `pyproject.toml`
- **Line Length**: 88 characters
- **Target Version**: Python 3.11+

```bash
# Format code
black .

# Check formatting without changes
black --check --diff .
```

#### isort
- **Purpose**: Import sorting and organization
- **Configuration**: `pyproject.toml`
- **Profile**: Black-compatible
- **Sections**: FUTURE, STDLIB, THIRDPARTY, FIRSTPARTY, LOCALFOLDER

```bash
# Sort imports
isort .

# Check import sorting
isort --check-only --diff .
```

### 2. Code Linting

#### Flake8
- **Purpose**: Style guide enforcement
- **Configuration**: `pyproject.toml`
- **Max Line Length**: 88 (compatible with Black)
- **Extensions**: bugbear, comprehensions, docstrings, import-order

```bash
# Run Flake8
flake8 .

# Run with specific configuration
flake8 --max-line-length=88 --extend-ignore=E203,W503 .
```

#### MyPy
- **Purpose**: Static type checking
- **Configuration**: `pyproject.toml`
- **Strict Mode**: Enabled
- **Python Version**: 3.11+

```bash
# Run type checking
mypy app/

# Run with specific configuration
mypy --ignore-missing-imports --show-error-codes app/
```

### 3. Security Analysis

#### Bandit
- **Purpose**: Security vulnerability detection
- **Configuration**: `pyproject.toml`
- **Output**: JSON format
- **Exclusions**: Tests, virtual environments

```bash
# Run security scan
bandit -r . -f json -o bandit-report.json

# Run with exclusions
bandit -r . --exclude tests/,venv/,.venv/,env/,.env/
```

#### Safety
- **Purpose**: Dependency vulnerability checking
- **Configuration**: `pyproject.toml`
- **Output**: JSON format
- **Database**: PyUp safety database

```bash
# Check dependencies
safety check --output json --save safety-report.json

# Check specific requirements file
safety check -r requirements.txt
```

### 4. Code Complexity Analysis

#### Radon
- **Purpose**: Code complexity metrics
- **Configuration**: `pyproject.toml`
- **Metrics**: Cyclomatic complexity, maintainability index
- **Thresholds**: Configurable minimum values

```bash
# Analyze complexity
radon cc app --min A --json

# Generate report
radon cc app --min A --xml
```

#### Xenon
- **Purpose**: Complexity threshold enforcement
- **Configuration**: `pyproject.toml`
- **Thresholds**: Absolute (10), Average (5)
- **Integration**: CI/CD pipeline

```bash
# Check complexity thresholds
xenon --max-absolute-complexity=10 --max-average-complexity=5 app
```

### 5. Testing and Coverage

#### Pytest
- **Purpose**: Testing framework
- **Configuration**: `pyproject.toml`
- **Coverage**: pytest-cov integration
- **Markers**: Unit, integration, e2e, slow, fast

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=xml

# Run specific test types
pytest -m "unit"
pytest -m "integration"
```

#### Coverage
- **Purpose**: Code coverage measurement
- **Configuration**: `pyproject.toml`
- **Thresholds**: 70% minimum
- **Reports**: HTML, XML, terminal

```bash
# Run coverage
coverage run --source=app -m pytest

# Generate reports
coverage report
coverage html
```

## Frontend Code Quality Tools

### 1. Code Linting

#### ESLint
- **Purpose**: JavaScript/TypeScript linting
- **Configuration**: `.eslintrc.js`
- **Extends**: Next.js, TypeScript, React, Accessibility
- **Plugins**: SonarJS, Unicorn, Import, Unused Imports

```bash
# Run ESLint
npm run lint:eslint

# Fix issues automatically
npm run lint:eslint:fix

# Run on specific files
npx eslint src/components/ --ext .tsx
```

#### TypeScript Compiler
- **Purpose**: Type checking
- **Configuration**: `tsconfig.json`
- **Strict Mode**: Enabled
- **No Emit**: Type checking only

```bash
# Run type checking
npm run lint:typescript

# Check specific files
npx tsc --noEmit src/components/
```

### 2. Code Formatting

#### Prettier
- **Purpose**: Code formatting
- **Configuration**: `.prettierrc`
- **Plugins**: Tailwind CSS
- **Line Length**: 80 characters

```bash
# Format code
npm run format:prettier

# Check formatting
npm run format:prettier:check

# Format specific files
npx prettier --write src/components/
```

#### Stylelint
- **Purpose**: CSS/SCSS linting
- **Configuration**: `.stylelintrc`
- **Rules**: Standard + custom
- **Plugins**: Order, Prettier compatibility

```bash
# Run Stylelint
npm run lint:stylelint

# Fix issues automatically
npm run lint:stylelint:fix

# Check specific files
npx stylelint src/styles/ --formatter=compact
```

### 3. Testing

#### Jest
- **Purpose**: Testing framework
- **Configuration**: `jest.config.js`
- **Environment**: jsdom
- **Coverage**: Built-in coverage reporting

```bash
# Run tests
npm run test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run integration tests
npm run test:integration
```

## Pre-commit Hooks

### Configuration
- **File**: `.pre-commit-config.yaml`
- **Tools**: Multiple language support
- **Stages**: pre-commit, commit-msg, push

### Hooks
1. **General**: trailing-whitespace, end-of-file-fixer, check-yaml
2. **Python**: Black, isort, Flake8, MyPy, Bandit, Safety
3. **Frontend**: ESLint, Prettier, Stylelint
4. **Documentation**: Markdown, YAML, TOML linting
5. **Security**: Docker, Terraform validation

### Installation
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Install commit-msg hook
pre-commit install --hook-type commit-msg

# Run on all files
pre-commit run --all-files
```

## Automated Quality Checks

### Backend Runner
- **Script**: `run_code_quality.py`
- **Features**: Comprehensive checking, auto-fixing, reporting
- **Integration**: CI/CD pipeline

```bash
# Run all checks
python run_code_quality.py

# Auto-fix issues
python run_code_quality.py --auto-fix

# Run specific check
python run_code_quality.py --check formatting
```

### Frontend Runner
- **Script**: `run_code_quality.js`
- **Features**: Multi-tool checking, scoring, recommendations
- **Integration**: npm scripts, CI/CD

```bash
# Run all checks
node run_code_quality.js

# Auto-fix issues
node run_code_quality.js --auto-fix

# Run specific check
node run_code_quality.js --check eslint
```

## Makefile Commands (Backend)

### Quality Commands
```bash
# Run all quality checks
make quality

# Run specific checks
make lint
make format
make type-check
make security
make complexity
make coverage

# Auto-fix issues
make auto-fix

# Quick quality check
make quick-check
```

### Development Commands
```bash
# Setup development environment
make dev-setup

# Run tests
make test
make test-cov
make test-integration

# Clean up
make clean

# Update dependencies
make update-deps
```

## NPM Scripts (Frontend)

### Quality Scripts
```bash
# Run all quality checks
npm run quality

# Run specific checks
npm run lint:all
npm run lint:eslint
npm run lint:typescript
npm run lint:stylelint

# Format code
npm run format:prettier
npm run format:prettier:check

# Auto-fix issues
npm run quality:fix
```

### Testing Scripts
```bash
# Run tests
npm run test
npm run test:watch
npm run test:coverage
npm run test:ci

# Integration tests
npm run test:integration
npm run test:integration:coverage
```

## CI/CD Integration

### GitHub Actions
- **Workflow**: `.github/workflows/ci-cd-pipeline.yml`
- **Quality Gates**: Linting, formatting, type checking
- **Security**: Automated vulnerability scanning
- **Coverage**: Minimum threshold enforcement

### Quality Gates
1. **Code Formatting**: Black, isort, Prettier
2. **Linting**: Flake8, ESLint, Stylelint
3. **Type Checking**: MyPy, TypeScript
4. **Security**: Bandit, Safety
5. **Testing**: Pytest, Jest with coverage
6. **Complexity**: Radon, Xenon thresholds

## Configuration Files

### Backend Configuration
- **`pyproject.toml`**: Centralized configuration for all tools
- **`.pre-commit-config.yaml`**: Git hook configuration
- **`.coveragerc`**: Coverage configuration
- **`pytest.ini`**: Pytest configuration

### Frontend Configuration
- **`.eslintrc.js`**: ESLint rules and plugins
- **`.prettierrc`**: Prettier formatting rules
- **`.stylelintrc`**: Stylelint CSS rules
- **`.husky/`**: Git hooks configuration
- **`.lintstagedrc.js`**: Staged file processing

## Quality Standards

### Code Style
- **Python**: PEP 8 with Black formatting
- **JavaScript/TypeScript**: ESLint + Prettier
- **CSS/SCSS**: Stylelint with BEM methodology
- **Line Length**: 80-88 characters
- **Indentation**: 2-4 spaces (language dependent)

### Code Quality
- **Coverage**: Minimum 70% (backend), 60% (frontend)
- **Complexity**: Maximum 10 (absolute), 5 (average)
- **Security**: Zero high/critical vulnerabilities
- **Type Safety**: Strict TypeScript, MyPy enabled

### Documentation
- **Docstrings**: Google style (Python)
- **Comments**: Clear, concise, meaningful
- **README**: Comprehensive project documentation
- **API Docs**: OpenAPI/Swagger specification

## Best Practices

### 1. Code Organization
- **Imports**: Organized by type and alphabetized
- **Functions**: Single responsibility, clear naming
- **Classes**: Logical grouping, inheritance hierarchy
- **Files**: One class/function per file when possible

### 2. Error Handling
- **Exceptions**: Specific exception types
- **Logging**: Structured logging with appropriate levels
- **Validation**: Input validation and sanitization
- **Graceful Degradation**: Handle failures gracefully

### 3. Performance
- **Algorithms**: Efficient algorithms and data structures
- **Database**: Optimized queries and indexing
- **Caching**: Strategic caching strategies
- **Monitoring**: Performance metrics and alerting

### 4. Security
- **Authentication**: Secure authentication mechanisms
- **Authorization**: Role-based access control
- **Input Validation**: Sanitize all user inputs
- **Dependencies**: Regular security updates

## Troubleshooting

### Common Issues

#### Backend Issues
1. **Import Errors**: Check `PYTHONPATH` and virtual environment
2. **Type Errors**: Verify MyPy configuration and type hints
3. **Formatting Conflicts**: Ensure Black and isort compatibility
4. **Coverage Issues**: Check `.coveragerc` configuration

#### Frontend Issues
1. **ESLint Errors**: Verify `.eslintrc.js` configuration
2. **TypeScript Errors**: Check `tsconfig.json` settings
3. **Prettier Conflicts**: Ensure ESLint and Prettier compatibility
4. **Stylelint Issues**: Verify `.stylelintrc` configuration

### Debug Commands
```bash
# Backend debugging
python run_code_quality.py --check formatting
make lint-help
make format-help

# Frontend debugging
node run_code_quality.js --check eslint
npm run lint:eslint -- --debug
npm run lint:typescript -- --listFiles
```

## Future Enhancements

### Planned Improvements
1. **Visual Reports**: HTML-based quality dashboards
2. **Trend Analysis**: Quality metrics over time
3. **Custom Rules**: Project-specific linting rules
4. **Performance Profiling**: Automated performance analysis
5. **Security Scanning**: Advanced security analysis tools

### Integration Opportunities
1. **IDE Integration**: VS Code, PyCharm, WebStorm
2. **Editor Config**: `.editorconfig` for consistent formatting
3. **Git Hooks**: Advanced commit message validation
4. **Code Review**: Automated quality gate enforcement

## Conclusion

The code quality framework provides comprehensive tools and processes to maintain high code standards across the Autonomica project. By following the established patterns and using the automated tools, developers can ensure consistent, secure, and maintainable code.

For questions or issues with the code quality framework, please refer to the troubleshooting section or contact the development team.