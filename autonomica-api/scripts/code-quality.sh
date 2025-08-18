#!/bin/bash

# Autonomica API Code Quality Script
# This script runs all code quality checks and provides a comprehensive report

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install dependencies if needed
install_dependencies() {
    print_status "Checking and installing dependencies..."
    
    if ! command_exists ruff; then
        print_status "Installing ruff..."
        pip install ruff
    fi
    
    if ! command_exists mypy; then
        print_status "Installing mypy..."
        pip install mypy
    fi
    
    if ! command_exists black; then
        print_status "Installing black..."
        pip install black
    fi
    
    if ! command_exists isort; then
        print_status "Installing isort..."
        pip install isort
    fi
    
    if ! command_exists bandit; then
        print_status "Installing bandit..."
        pip install bandit
    fi
    
    if ! command_exists safety; then
        print_status "Installing safety..."
        pip install safety
    fi
    
    if ! command_exists codespell; then
        print_status "Installing codespell..."
        pip install codespell
    fi
    
    if ! command_exists coverage; then
        print_status "Installing coverage..."
        pip install coverage
    fi
}

# Function to run formatting checks
run_formatting() {
    print_status "Running code formatting checks..."
    
    # Check if code is properly formatted
    print_status "Checking Black formatting..."
    if black --check --diff .; then
        print_success "Black formatting check passed"
    else
        print_warning "Code is not properly formatted. Run 'black .' to fix"
        BLACK_FAILED=true
    fi
    
    print_status "Checking isort import sorting..."
    if isort --check-only --diff .; then
        print_success "isort import sorting check passed"
    else
        print_warning "Imports are not properly sorted. Run 'isort .' to fix"
        ISORT_FAILED=true
    fi
}

# Function to run linting checks
run_linting() {
    print_status "Running linting checks..."
    
    print_status "Running Ruff linter..."
    if ruff check .; then
        print_success "Ruff linting passed"
    else
        print_warning "Ruff found issues. Run 'ruff check --fix .' to fix auto-fixable issues"
        RUFF_FAILED=true
    fi
    
    print_status "Running type checking with mypy..."
    if mypy app/; then
        print_success "Type checking passed"
    else
        print_warning "Type checking found issues"
        MYPY_FAILED=true
    fi
}

# Function to run security checks
run_security() {
    print_status "Running security checks..."
    
    print_status "Running Bandit security linter..."
    if bandit -r app/ -f json -o bandit-report.json; then
        print_success "Bandit security check passed"
    else
        print_warning "Bandit found security issues. Check bandit-report.json for details"
        BANDIT_FAILED=true
    fi
    
    print_status "Running Safety dependency vulnerability check..."
    if safety check; then
        print_success "Safety dependency check passed"
    else
        print_warning "Safety found vulnerable dependencies"
        SAFETY_FAILED=true
    fi
    
    print_status "Running pip-audit..."
    if pip-audit; then
        print_success "pip-audit passed"
    else
        print_warning "pip-audit found issues"
        PIP_AUDIT_FAILED=true
    fi
}

# Function to run spell checking
run_spell_check() {
    print_status "Running spell checking..."
    
    if codespell --ignore-words-list="ans,creat,hist,nd,te,ue" --skip="*.pyc,*.pyo,*.pyd,.git,__pycache__,.venv,venv,node_modules,community_usecase,local,final_output,licenses,owl,Python,examples,environment"; then
        print_success "Spell checking passed"
    else
        print_warning "Spell checking found issues"
        CODESPELL_FAILED=true
    fi
}

# Function to run test coverage
run_coverage() {
    print_status "Running test coverage analysis..."
    
    if [ -d "tests" ]; then
        print_status "Running tests with coverage..."
        if python -m pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80; then
            print_success "Test coverage passed (minimum 80%)"
        else
            print_warning "Test coverage below threshold or tests failed"
            COVERAGE_FAILED=true
        fi
    else
        print_warning "No tests directory found. Skipping coverage check"
    fi
}

# Function to generate quality report
generate_report() {
    print_status "Generating code quality report..."
    
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}        CODE QUALITY REPORT           ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Formatting section
    echo -e "\n${YELLOW}FORMATTING:${NC}"
    if [ "$BLACK_FAILED" = true ]; then
        echo -e "  ${RED}✗ Black formatting${NC}"
    else
        echo -e "  ${GREEN}✓ Black formatting${NC}"
    fi
    
    if [ "$ISORT_FAILED" = true ]; then
        echo -e "  ${RED}✗ Import sorting${NC}"
    else
        echo -e "  ${GREEN}✓ Import sorting${NC}"
    fi
    
    # Linting section
    echo -e "\n${YELLOW}LINTING:${NC}"
    if [ "$RUFF_FAILED" = true ]; then
        echo -e "  ${RED}✗ Ruff linting${NC}"
    else
        echo -e "  ${GREEN}✓ Ruff linting${NC}"
    fi
    
    if [ "$MYPY_FAILED" = true ]; then
        echo -e "  ${RED}✗ Type checking${NC}"
    else
        echo -e "  ${GREEN}✓ Type checking${NC}"
    fi
    
    # Security section
    echo -e "\n${YELLOW}SECURITY:${NC}"
    if [ "$BANDIT_FAILED" = true ]; then
        echo -e "  ${RED}✗ Bandit security${NC}"
    else
        echo -e "  ${GREEN}✓ Bandit security${NC}"
    fi
    
    if [ "$SAFETY_FAILED" = true ]; then
        echo -e "  ${RED}✗ Safety check${NC}"
    else
        echo -e "  ${GREEN}✓ Safety check${NC}"
    fi
    
    if [ "$PIP_AUDIT_FAILED" = true ]; then
        echo -e "  ${RED}✗ pip-audit${NC}"
    else
        echo -e "  ${GREEN}✓ pip-audit${NC}"
    fi
    
    # Spell checking section
    echo -e "\n${YELLOW}SPELL CHECKING:${NC}"
    if [ "$CODESPELL_FAILED" = true ]; then
        echo -e "  ${RED}✗ Spell checking${NC}"
    else
        echo -e "  ${GREEN}✓ Spell checking${NC}"
    fi
    
    # Coverage section
    echo -e "\n${YELLOW}TEST COVERAGE:${NC}"
    if [ "$COVERAGE_FAILED" = true ]; then
        echo -e "  ${RED}✗ Test coverage${NC}"
    else
        echo -e "  ${GREEN}✓ Test coverage${NC}"
    fi
    
    # Summary
    echo -e "\n${BLUE}========================================${NC}"
    
    # Count failures
    FAILURES=0
    [ "$BLACK_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$ISORT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$RUFF_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$MYPY_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$BANDIT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$SAFETY_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$PIP_AUDIT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$CODESPELL_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$COVERAGE_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    
    if [ $FAILURES -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL CHECKS PASSED! 🎉${NC}"
        exit 0
    else
        echo -e "${RED}❌ $FAILURES CHECK(S) FAILED ❌${NC}"
        echo -e "\n${YELLOW}To fix issues:${NC}"
        echo -e "  • Run 'black .' to fix formatting"
        echo -e "  • Run 'isort .' to fix import sorting"
        echo -e "  • Run 'ruff check --fix .' to fix auto-fixable linting issues"
        echo -e "  • Check individual tool outputs above for specific issues"
        exit 1
    fi
}

# Function to auto-fix issues
auto_fix() {
    print_status "Attempting to auto-fix issues..."
    
    print_status "Running Black formatter..."
    black .
    
    print_status "Running isort..."
    isort .
    
    print_status "Running Ruff auto-fix..."
    ruff check --fix .
    
    print_success "Auto-fix completed. Re-run the script to verify all issues are resolved."
}

# Main execution
main() {
    print_status "Starting Autonomica API Code Quality Check..."
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "This script must be run from the autonomica-api directory"
        exit 1
    fi
    
    # Parse command line arguments
    AUTO_FIX=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto-fix)
                AUTO_FIX=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--auto-fix] [--help]"
                echo "  --auto-fix  Automatically fix auto-fixable issues"
                echo "  --help      Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Install dependencies
    install_dependencies
    
    # Run all checks
    run_formatting
    run_linting
    run_security
    run_spell_check
    run_coverage
    
    # Auto-fix if requested
    if [ "$AUTO_FIX" = true ]; then
        auto_fix
    fi
    
    # Generate report
    generate_report
}

# Run main function
main "$@"
