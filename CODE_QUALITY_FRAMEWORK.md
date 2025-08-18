# Code Quality Framework

## Overview
This document provides comprehensive information about the code quality framework implemented for the Autonomica project, covering both backend (Python) and frontend (React/Next.js) code quality tools, configurations, and processes.

## What is Code Quality?

Code quality encompasses various aspects of software development that ensure code is:
- **Readable**: Easy to understand and maintain
- **Consistent**: Follows established patterns and standards
- **Secure**: Free from vulnerabilities and security issues
- **Efficient**: Optimized for performance
- **Testable**: Well-structured for testing
- **Maintainable**: Easy to modify and extend

## Backend Code Quality (Python)

### Tools and Configuration

#### 1. Ruff - Fast Python Linter
**Configuration**: `autonomica-api/pyproject.toml`

**Features**:
- **Speed**: 10-100x faster than traditional linters
- **Comprehensive**: Replaces flake8, isort, pyupgrade, and more
- **Auto-fix**: Automatically fixes many common issues
- **Configurable**: Extensive rule customization

**Key Rules Enabled**:
```toml
select = [
    "E",      # pycodestyle errors
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "N",      # pep8-naming
    "W",      # pycodestyle warnings
    "S",      # bandit (security)
    "A",      # flake8-builtins
    "COM",    # flake8-commas
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "T20",    # flake8-print
    "EM",     # flake8-errmsg
    "EXE",    # flake8-executable
    "FA",     # flake8-future-annotations
    "ICN",    # flake8-import-conventions
    "INP",    # flake8-no-pep420
    "ISC",    # flake8-implicit-str-concat
    "NPY",    # flake8-numpy
    "PD",     # pandas-vet
    "PGH",    # pygrep-hooks
    "PIE",    # flake8-pie
    "PLR",    # pylint refactor
    "PLW",    # pylint warnings
    "PT",     # flake8-pytest-style
    "PTH",    # use-pathlib
    "PYI",    # flake8-pyi
    "RET",    # flake8-return
    "RSE",    # flake8-raise
    "SIM",    # flake8-simplify
    "SLF",    # flake8-self
    "SLOT",   # flake8-slots
    "TCH",    # flake8-type-checking
    "TID",    # flake8-tidy-imports
    "ARG",    # flake8-unused-arguments
    "BLE",    # flake8-blind-except
    "FBT",    # flake8-boolean-trap
    "LOG",    # flake8-logging-format
    "PIE",    # flake8-pie
    "TRY",    # tryceratops
    "NPY",    # flake8-numpy
    "AIR",    # flake8-airbnb
    "PERF",   # perflint
    "RUF",    # ruff-specific rules
]
```

**Usage**:
```bash
# Check code
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

#### 2. MyPy - Static Type Checker
**Configuration**: `autonomica-api/pyproject.toml`

**Features**:
- **Type Safety**: Catches type-related errors before runtime
- **Gradual Typing**: Supports both typed and untyped code
- **Strict Mode**: Configurable strictness levels
- **IDE Integration**: Excellent editor support

**Configuration**:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

**Usage**:
```bash
# Type check entire project
mypy app/

# Type check specific file
mypy app/main.py

# Generate type stubs
mypy --stubgen app/
```

#### 3. Black - Code Formatter
**Configuration**: Integrated with Ruff

**Features**:
- **Uncompromising**: Minimal configuration, consistent output
- **Fast**: High-performance formatting
- **PEP 8 Compliant**: Follows Python style guidelines
- **Integration**: Works seamlessly with other tools

**Usage**:
```bash
# Format code
black .

# Check formatting
black --check --diff .

# Format specific file
black app/main.py
```

#### 4. isort - Import Sorter
**Configuration**: Integrated with Ruff

**Features**:
- **Smart Grouping**: Groups imports logically
- **Profile Support**: Multiple import style profiles
- **Auto-fix**: Automatically fixes import order
- **Black Compatible**: Works with Black formatting

**Usage**:
```bash
# Sort imports
isort .

# Check import order
isort --check-only --diff .

# Sort specific file
isort app/main.py
```

#### 5. Bandit - Security Linter
**Configuration**: `autonomica-api/pyproject.toml`

**Features**:
- **Security Focus**: Identifies security vulnerabilities
- **Comprehensive**: Covers common security anti-patterns
- **Configurable**: Customizable rule sets
- **CI/CD Ready**: Perfect for automated security checks

**Configuration**:
```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv", "community_usecase", "local", "final_output", "licenses", "owl", "Python", "examples", "environment"]
skips = ["B101", "B601"]
```

**Usage**:
```bash
# Security scan
bandit -r app/

# Generate JSON report
bandit -r app/ -f json -o bandit-report.json

# Skip specific tests
bandit -r app/ -s B101,B601
```

#### 6. Safety - Dependency Vulnerability Checker
**Features**:
- **Vulnerability Database**: Checks against known security issues
- **Real-time Updates**: Always current vulnerability data
- **CI/CD Integration**: Perfect for automated security checks
- **Multiple Formats**: Supports various output formats

**Usage**:
```bash
# Check dependencies
safety check

# Generate requirements file
safety check -r requirements.txt

# JSON output
safety check --json
```

#### 7. pip-audit - Package Vulnerability Scanner
**Features**:
- **Comprehensive**: Scans all installed packages
- **Multiple Sources**: Checks multiple vulnerability databases
- **Fix Suggestions**: Provides remediation advice
- **CI/CD Ready**: Perfect for automated security workflows

**Usage**:
```bash
# Audit all packages
pip-audit

# Audit specific requirements
pip-audit -r requirements.txt

# Generate JSON report
pip-audit --format json
```

#### 8. codespell - Spell Checker
**Configuration**: `autonomica-api/pyproject.toml`

**Features**:
- **Code-Aware**: Understands code context
- **Customizable**: Configurable word lists
- **Fast**: Efficient spell checking
- **Integration**: Works with CI/CD pipelines

**Configuration**:
```toml
[tool.codespell]
ignore-words-list = "ans,creat,hist,nd,te,ue"
skip = "*.pyc,*.pyo,*.pyd,.git,__pycache__,.venv,venv,node_modules,community_usecase,local,final_output,licenses,owl,Python,examples,environment"
```

**Usage**:
```bash
# Spell check
codespell .

# Skip specific patterns
codespell --skip="*.pyc,*.pyo,*.pyd"

# Custom word list
codespell --ignore-words-list="ans,creat,hist,nd,te,ue"
```

#### 9. Coverage.py - Test Coverage
**Configuration**: `autonomica-api/pyproject.toml`

**Features**:
- **Comprehensive**: Measures code coverage accurately
- **Multiple Formats**: HTML, XML, terminal output
- **Thresholds**: Configurable minimum coverage requirements
- **Branch Coverage**: Tracks conditional execution paths

**Configuration**:
```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/migrations/*",
    "*/venv/*",
    "*/.venv/*",
    "*/node_modules/*",
    "*/__pycache__/*",
    "*/scripts/*",
    "*/monitoring/*",
    "*/docs/*",
    "*/examples/*",
    "*/community_usecase/*",
    "*/local/*",
    "*/final_output/*",
    "*/licenses/*",
    "*/owl/*",
    "*/Python/*",
    "*/quick_test_chat.sh",
    "*/start_autonomica.sh",
    "*/stop_autonomica.sh",
    "*/test_autonomica.sh",
    "*/uv.lock",
    "*/pyproject.toml",
    "*/requirements*.txt",
    "*/.env*",
    "*/env.*",
    "*/server.*",
    "*/security-report.md",
    "*/setup_for_testing.py",
    "*/test_*.py",
    "*/ollama-performance-dashboard.html",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

**Usage**:
```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Generate coverage report
coverage run -m pytest
coverage report
coverage html
```

### Backend Code Quality Script

**Location**: `autonomica-api/scripts/code-quality.sh`

**Features**:
- **Comprehensive**: Runs all quality checks in sequence
- **Auto-fix**: Automatically fixes auto-fixable issues
- **Colored Output**: Clear, readable status reporting
- **Dependency Management**: Installs required tools automatically
- **Detailed Reporting**: Comprehensive quality status report

**Usage**:
```bash
# Run all quality checks
./scripts/code-quality.sh

# Auto-fix issues
./scripts/code-quality.sh --auto-fix

# Show help
./scripts/code-quality.sh --help
```

**Output Example**:
```
========================================
        CODE QUALITY REPORT           
========================================

FORMATTING:
  ✓ Black formatting
  ✓ Import sorting

LINTING:
  ✓ Ruff linting
  ✓ Type checking

SECURITY:
  ✓ Bandit security
  ✓ Safety check
  ✓ pip-audit

SPELL CHECKING:
  ✓ Spell checking

TEST COVERAGE:
  ✓ Test coverage

========================================
🎉 ALL CHECKS PASSED! 🎉
```

## Frontend Code Quality (React/Next.js)

### Tools and Configuration

#### 1. ESLint - JavaScript/TypeScript Linter
**Configuration**: `autonomica-frontend/.eslintrc.js`

**Features**:
- **Comprehensive**: Extensive rule set for JavaScript/TypeScript
- **Framework Aware**: React, Next.js, and TypeScript support
- **Auto-fix**: Automatically fixes many issues
- **Plugin Ecosystem**: Rich plugin ecosystem

**Key Rules**:
```javascript
rules: {
  // Prettier integration
  'prettier/prettier': 'error',

  // React rules
  'react/react-in-jsx-scope': 'off',
  'react/prop-types': 'off',
  'react/display-name': 'off',

  // React Hooks rules
  'react-hooks/rules-of-hooks': 'error',
  'react-hooks/exhaustive-deps': 'warn',

  // TypeScript rules
  '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  '@typescript-eslint/no-explicit-any': 'warn',
  '@typescript-eslint/prefer-const': 'error',

  // Import rules
  'import/order': ['error', {
    groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
    'newlines-between': 'always',
    alphabetize: { order: 'asc', caseInsensitive: true }
  }],

  // General rules
  'no-console': 'warn',
  'no-debugger': 'error',
  'no-alert': 'warn',
  'prefer-const': 'error',

  // Accessibility rules
  'jsx-a11y/alt-text': 'error',
  'jsx-a11y/anchor-has-content': 'error',
  'jsx-a11y/anchor-is-valid': 'error',
  'jsx-a11y/aria-props': 'error',
  'jsx-a11y/aria-proptypes': 'error',
  'jsx-a11y/aria-unsupported-elements': 'error',
  'jsx-a11y/click-events-have-key-events': 'error',
  'jsx-a11y/heading-has-content': 'error',
  'jsx-a11y/html-has-lang': 'error',
  'jsx-a11y/img-redundant-alt': 'error',
  'jsx-a11y/no-access-key': 'error',
  'jsx-a11y/no-redundant-roles': 'error',
  'jsx-a11y/role-has-required-aria-props': 'error',
  'jsx-a11y/role-supports-aria-props': 'error',
  'jsx-a11y/tabindex-no-positive': 'error',
}
```

**Usage**:
```bash
# Lint code
npx eslint src/ --ext .js,.jsx,.ts,.tsx

# Auto-fix issues
npx eslint src/ --ext .js,.jsx,.ts,.tsx --fix

# Lint specific file
npx eslint src/components/Button.tsx
```

#### 2. Prettier - Code Formatter
**Configuration**: `autonomica-frontend/.prettierrc`

**Features**:
- **Opinionated**: Minimal configuration, consistent output
- **Framework Support**: Works with all JavaScript/TypeScript frameworks
- **Integration**: Seamless ESLint integration
- **Fast**: High-performance formatting

**Configuration**:
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "bracketSameLine": false,
  "arrowParens": "avoid",
  "endOfLine": "lf",
  "quoteProps": "as-needed",
  "jsxSingleQuote": true,
  "proseWrap": "preserve",
  "htmlWhitespaceSensitivity": "css",
  "embeddedLanguageFormatting": "auto",
  "singleAttributePerLine": false
}
```

**Usage**:
```bash
# Format code
npx prettier --write src/

# Check formatting
npx prettier --check src/

# Format specific file
npx prettier --write src/components/Button.tsx
```

#### 3. TypeScript - Type Checker
**Configuration**: `autonomica-frontend/tsconfig.json`

**Features**:
- **Static Typing**: Catches type errors at compile time
- **IntelliSense**: Enhanced IDE support
- **Refactoring**: Safe code refactoring
- **Documentation**: Types serve as documentation

**Usage**:
```bash
# Type check
npx tsc --noEmit

# Build with types
npx tsc

# Generate declaration files
npx tsc --declaration
```

#### 4. Jest - Testing Framework
**Configuration**: `autonomica-frontend/jest.config.js`

**Features**:
- **Fast**: Parallel test execution
- **Comprehensive**: Full testing framework
- **Mocking**: Built-in mocking capabilities
- **Coverage**: Integrated coverage reporting

**Usage**:
```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- Button.test.tsx
```

#### 5. React Testing Library - Component Testing
**Features**:
- **User-Centric**: Tests from user perspective
- **Accessibility**: Built-in accessibility testing
- **Best Practices**: Encourages good testing practices
- **Integration**: Works seamlessly with Jest

**Usage**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import Button from './Button'

test('renders button with text', () => {
  render(<Button>Click me</Button>)
  expect(screen.getByText('Click me')).toBeInTheDocument()
})

test('calls onClick when clicked', () => {
  const handleClick = jest.fn()
  render(<Button onClick={handleClick}>Click me</Button>)
  fireEvent.click(screen.getByText('Click me'))
  expect(handleClick).toHaveBeenCalledTimes(1)
})
```

### Frontend Code Quality Script

**Location**: `autonomica-frontend/scripts/code-quality.sh`

**Features**:
- **Comprehensive**: Runs all frontend quality checks
- **Auto-fix**: Automatically fixes auto-fixable issues
- **Performance**: Skips optional checks for faster execution
- **Dependency Management**: Installs required packages automatically
- **Detailed Reporting**: Comprehensive quality status report

**Usage**:
```bash
# Run all quality checks
./scripts/code-quality.sh

# Auto-fix issues
./scripts/code-quality.sh --auto-fix

# Skip tests
./scripts/code-quality.sh --skip-tests

# Skip build check
./scripts/code-quality.sh --skip-build

# Show help
./scripts/code-quality.sh --help
```

## Pre-commit Hooks

### Configuration
**File**: `.pre-commit-config.yaml`

**Features**:
- **Automated**: Runs quality checks before each commit
- **Comprehensive**: Covers all code quality aspects
- **Fast**: Optimized for minimal delay
- **Configurable**: Easy to customize and extend

**Hooks**:
```yaml
repos:
  # Python code formatting and linting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
        args: [--line-length=88]
        
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black, --line-length=88]
        
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]
        
  # JavaScript/TypeScript formatting and linting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types: [javascript, jsx, ts, tsx, json, css, scss, md]
        args: [--write]
        
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        args: [--fix]
        
  # Security checks
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, ., -f, json, -o, bandit-report.json]
        
  - repo: https://github.com/PyCQA/safety
    rev: 2.3.5
    hooks:
      - id: safety
        args: [check]
        
  # Spell checking
  - repo: https://github.com/codespell-project/codespell
    rev: v2.2.6
    hooks:
      - id: codespell
        args: [--ignore-words-list=ans,creat,hist,nd,te,ue]
```

**Usage**:
```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks on staged files
pre-commit run

# Run specific hook
pre-commit run black

# Run on all files
pre-commit run --all-files
```

## CI/CD Integration

### GitHub Actions Integration

**Backend Quality Checks**:
```yaml
- name: Code Quality - Backend
  run: |
    cd autonomica-api
    ./scripts/code-quality.sh

- name: Security Scan - Backend
  run: |
    cd autonomica-api
    bandit -r app/ -f json -o bandit-report.json
    safety check

- name: Type Check - Backend
  run: |
    cd autonomica-api
    mypy app/
```

**Frontend Quality Checks**:
```yaml
- name: Code Quality - Frontend
  run: |
    cd autonomica-frontend
    ./scripts/code-quality.sh --skip-tests --skip-build

- name: Lint - Frontend
  run: |
    cd autonomica-frontend
    npx eslint src/ --ext .js,.jsx,.ts,.tsx

- name: Type Check - Frontend
  run: |
    cd autonomica-frontend
    npx tsc --noEmit

- name: Test - Frontend
  run: |
    cd autonomica-frontend
    npm test -- --coverage --watchAll=false
```

### Quality Gates

**Backend Quality Gates**:
- **Coverage**: Minimum 80% test coverage
- **Security**: No high/critical vulnerabilities
- **Linting**: All linting rules pass
- **Type Checking**: No type errors
- **Formatting**: Code properly formatted

**Frontend Quality Gates**:
- **Linting**: All ESLint rules pass
- **Type Checking**: No TypeScript errors
- **Formatting**: Prettier formatting check passes
- **Tests**: All tests pass
- **Build**: Next.js build succeeds

## Best Practices

### 1. Consistent Code Style
- Use automated formatters (Black, Prettier)
- Enforce consistent naming conventions
- Maintain consistent import ordering
- Follow established code patterns

### 2. Regular Quality Checks
- Run quality checks before committing
- Integrate quality checks in CI/CD
- Regular dependency vulnerability scans
- Continuous monitoring of code quality metrics

### 3. Incremental Improvement
- Start with basic quality checks
- Gradually increase strictness
- Address technical debt systematically
- Regular quality reviews and improvements

### 4. Team Collaboration
- Establish quality standards as a team
- Use pre-commit hooks for consistency
- Regular code quality discussions
- Share quality improvement insights

### 5. Documentation
- Document quality standards
- Maintain quality check procedures
- Update quality configurations
- Share quality best practices

## Troubleshooting

### Common Issues

#### 1. Pre-commit Hook Failures
```bash
# Skip pre-commit hooks for this commit
git commit --no-verify

# Update pre-commit hooks
pre-commit autoupdate

# Clear pre-commit cache
pre-commit clean
```

#### 2. ESLint Configuration Issues
```bash
# Check ESLint configuration
npx eslint --print-config src/components/Button.tsx

# Debug ESLint issues
npx eslint --debug src/

# Reset ESLint cache
npx eslint --cache-location .eslintcache --cache src/
```

#### 3. TypeScript Configuration Issues
```bash
# Check TypeScript configuration
npx tsc --showConfig

# Generate TypeScript project references
npx tsc --build --verbose

# Clear TypeScript cache
rm -rf .tsbuildinfo
```

#### 4. Python Quality Tool Issues
```bash
# Check tool versions
ruff --version
mypy --version
black --version

# Update tools
pip install --upgrade ruff mypy black isort bandit safety codespell

# Clear tool caches
ruff clean
mypy --clear-cache
```

### Performance Optimization

#### 1. Parallel Execution
```bash
# Run tests in parallel
pytest -n auto

# Parallel linting
ruff check . --jobs 4

# Parallel type checking
mypy app/ --junit-xml=typecheck-results.xml
```

#### 2. Caching
```bash
# Enable ESLint caching
npx eslint --cache src/

# Enable TypeScript incremental compilation
npx tsc --incremental

# Use pytest cache
pytest --cache-clear
```

#### 3. Selective Checks
```bash
# Check only changed files
git diff --name-only | xargs ruff check

# Run only specific quality checks
./scripts/code-quality.sh --skip-tests

# Check specific directories
ruff check app/core/ app/api/
```

## Future Enhancements

### Planned Improvements

1. **SonarQube Integration**: Advanced code quality analysis
2. **Code Climate**: Maintainability metrics
3. **Semgrep**: Advanced security scanning
4. **Trivy**: Container vulnerability scanning
5. **Dependabot**: Automated dependency updates

### Quality Metrics Dashboard

1. **Coverage Trends**: Track test coverage over time
2. **Quality Scores**: Maintainability and complexity metrics
3. **Security Reports**: Vulnerability tracking and remediation
4. **Performance Metrics**: Bundle size and build time tracking
5. **Team Metrics**: Quality improvement tracking

### Advanced Quality Tools

1. **Mutation Testing**: Code quality validation
2. **Static Analysis**: Advanced code analysis
3. **Dynamic Analysis**: Runtime quality monitoring
4. **Architecture Validation**: Code structure verification
5. **API Contract Testing**: Interface validation

## Resources and References

### Documentation
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [ESLint Documentation](https://eslint.org/docs/)
- [Prettier Documentation](https://prettier.io/docs/)
- [Pre-commit Documentation](https://pre-commit.com/)

### Community
- [Python Quality Tools](https://github.com/topics/python-quality)
- [JavaScript Quality Tools](https://github.com/topics/javascript-quality)
- [Code Quality Discussions](https://github.com/topics/code-quality)

### Tools
- [Quality Tools Comparison](https://github.com/topics/code-quality)
- [Security Tools](https://github.com/topics/security-tools)
- [Testing Tools](https://github.com/topics/testing-tools)
