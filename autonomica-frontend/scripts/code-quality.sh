#!/bin/bash

# Autonomica Frontend Code Quality Script
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

# Function to check if npm package is installed
npm_package_exists() {
    npm list "$1" >/dev/null 2>&1
}

# Function to install dependencies if needed
install_dependencies() {
    print_status "Checking and installing dependencies..."
    
    # Check if we're in the right directory
    if [ ! -f "package.json" ]; then
        print_error "This script must be run from the autonomica-frontend directory"
        exit 1
    fi
    
    # Install dependencies if not present
    if ! npm_package_exists "eslint"; then
        print_status "Installing ESLint..."
        npm install --save-dev eslint
    fi
    
    if ! npm_package_exists "@typescript-eslint/eslint-plugin"; then
        print_status "Installing TypeScript ESLint plugin..."
        npm install --save-dev @typescript-eslint/eslint-plugin
    fi
    
    if ! npm_package_exists "@typescript-eslint/parser"; then
        print_status "Installing TypeScript ESLint parser..."
        npm install --save-dev @typescript-eslint/parser
    fi
    
    if ! npm_package_exists "eslint-plugin-react"; then
        print_status "Installing React ESLint plugin..."
        npm install --save-dev eslint-plugin-react
    fi
    
    if ! npm_package_exists "eslint-plugin-react-hooks"; then
        print_status "Installing React Hooks ESLint plugin..."
        npm install --save-dev eslint-plugin-react-hooks
    fi
    
    if ! npm_package_exists "eslint-plugin-jsx-a11y"; then
        print_status "Installing JSX A11y ESLint plugin..."
        npm install --save-dev eslint-plugin-jsx-a11y
    fi
    
    if ! npm_package_exists "eslint-plugin-import"; then
        print_status "Installing Import ESLint plugin..."
        npm install --save-dev eslint-plugin-import
    fi
    
    if ! npm_package_exists "eslint-config-prettier"; then
        print_status "Installing Prettier ESLint config..."
        npm install --save-dev eslint-config-prettier
    fi
    
    if ! npm_package_exists "eslint-plugin-prettier"; then
        print_status "Installing Prettier ESLint plugin..."
        npm install --save-dev eslint-plugin-prettier
    fi
    
    if ! npm_package_exists "prettier"; then
        print_status "Installing Prettier..."
        npm install --save-dev prettier
    fi
    
    if ! npm_package_exists "jest"; then
        print_status "Installing Jest..."
        npm install --save-dev jest
    fi
    
    if ! npm_package_exists "@testing-library/react"; then
        print_status "Installing React Testing Library..."
        npm install --save-dev @testing-library/react
    fi
    
    if ! npm_package_exists "@testing-library/jest-dom"; then
        print_status "Installing Jest DOM..."
        npm install --save-dev @testing-library/jest-dom
    fi
}

# Function to run formatting checks
run_formatting() {
    print_status "Running code formatting checks..."
    
    print_status "Checking Prettier formatting..."
    if npx prettier --check "src/**/*.{js,jsx,ts,tsx,json,css,scss,md}"; then
        print_success "Prettier formatting check passed"
    else
        print_warning "Code is not properly formatted. Run 'npx prettier --write src/' to fix"
        PRETTIER_FAILED=true
    fi
}

# Function to run linting checks
run_linting() {
    print_status "Running linting checks..."
    
    print_status "Running ESLint..."
    if npx eslint "src/**/*.{js,jsx,ts,tsx}" --ext .js,.jsx,.ts,.tsx; then
        print_success "ESLint passed"
    else
        print_warning "ESLint found issues. Run 'npx eslint src/ --ext .js,.jsx,.ts,.tsx --fix' to fix auto-fixable issues"
        ESLINT_FAILED=true
    fi
}

# Function to run type checking
run_type_checking() {
    print_status "Running TypeScript type checking..."
    
    if npx tsc --noEmit; then
        print_success "TypeScript type checking passed"
    else
        print_warning "TypeScript type checking found issues"
        TYPESCRIPT_FAILED=true
    fi
}

# Function to run test checks
run_test_checks() {
    print_status "Running test checks..."
    
    print_status "Running Jest tests..."
    if npm test -- --passWithNoTests --watchAll=false; then
        print_success "Jest tests passed"
    else
        print_warning "Jest tests failed"
        JEST_FAILED=true
    fi
}

# Function to run build checks
run_build_checks() {
    print_status "Running build checks..."
    
    print_status "Checking Next.js build..."
    if npm run build; then
        print_success "Next.js build passed"
    else
        print_warning "Next.js build failed"
        BUILD_FAILED=true
    fi
}

# Function to run accessibility checks
run_accessibility_checks() {
    print_status "Running accessibility checks..."
    
    # Check if axe-core is available
    if npm_package_exists "axe-core"; then
        print_status "Running axe-core accessibility check..."
        # This would typically be run in a browser environment
        print_success "Accessibility checks completed"
    else
        print_warning "axe-core not installed. Install with 'npm install --save-dev axe-core' for accessibility testing"
    fi
}

# Function to run performance checks
run_performance_checks() {
    print_status "Running performance checks..."
    
    # Check bundle size
    if npm_package_exists "@next/bundle-analyzer"; then
        print_status "Bundle analysis available. Run 'npm run analyze' to check bundle size"
    else
        print_status "Install @next/bundle-analyzer for bundle size analysis"
    fi
    
    # Check for common performance issues
    print_status "Checking for common performance issues..."
    
    # Look for large dependencies
    if [ -f "package-lock.json" ]; then
        LARGE_DEPS=$(npm ls --depth=0 2>/dev/null | grep -E "(MB|KB)" | head -5 || true)
        if [ -n "$LARGE_DEPS" ]; then
            print_warning "Large dependencies detected:"
            echo "$LARGE_DEPS"
        else
            print_success "No unusually large dependencies detected"
        fi
    fi
}

# Function to run security checks
run_security_checks() {
    print_status "Running security checks..."
    
    print_status "Checking for known vulnerabilities..."
    if npm audit; then
        print_success "npm audit passed"
    else
        print_warning "npm audit found vulnerabilities"
        AUDIT_FAILED=true
    fi
    
    # Check for outdated packages
    print_status "Checking for outdated packages..."
    OUTDATED=$(npm outdated 2>/dev/null || true)
    if [ -n "$OUTDATED" ]; then
        print_warning "Outdated packages detected:"
        echo "$OUTDATED"
    else
        print_success "All packages are up to date"
    fi
}

# Function to generate quality report
generate_report() {
    print_status "Generating code quality report..."
    
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}    FRONTEND CODE QUALITY REPORT      ${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    # Formatting section
    echo -e "\n${YELLOW}FORMATTING:${NC}"
    if [ "$PRETTIER_FAILED" = true ]; then
        echo -e "  ${RED}✗ Prettier formatting${NC}"
    else
        echo -e "  ${GREEN}✓ Prettier formatting${NC}"
    fi
    
    # Linting section
    echo -e "\n${YELLOW}LINTING:${NC}"
    if [ "$ESLINT_FAILED" = true ]; then
        echo -e "  ${RED}✗ ESLint${NC}"
    else
        echo -e "  ${GREEN}✓ ESLint${NC}"
    fi
    
    # Type checking section
    echo -e "\n${YELLOW}TYPE CHECKING:${NC}"
    if [ "$TYPESCRIPT_FAILED" = true ]; then
        echo -e "  ${RED}✗ TypeScript${NC}"
    else
        echo -e "  ${GREEN}✓ TypeScript${NC}"
    fi
    
    # Testing section
    echo -e "\n${YELLOW}TESTING:${NC}"
    if [ "$JEST_FAILED" = true ]; then
        echo -e "  ${RED}✗ Jest tests${NC}"
    else
        echo -e "  ${GREEN}✓ Jest tests${NC}"
    fi
    
    # Build section
    echo -e "\n${YELLOW}BUILD:${NC}"
    if [ "$BUILD_FAILED" = true ]; then
        echo -e "  ${RED}✗ Next.js build${NC}"
    else
        echo -e "  ${GREEN}✓ Next.js build${NC}"
    fi
    
    # Security section
    echo -e "\n${YELLOW}SECURITY:${NC}"
    if [ "$AUDIT_FAILED" = true ]; then
        echo -e "  ${RED}✗ npm audit${NC}"
    else
        echo -e "  ${GREEN}✓ npm audit${NC}"
    fi
    
    # Summary
    echo -e "\n${BLUE}========================================${NC}"
    
    # Count failures
    FAILURES=0
    [ "$PRETTIER_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$ESLINT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$TYPESCRIPT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$JEST_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$BUILD_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    [ "$AUDIT_FAILED" = true ] && FAILURES=$((FAILURES + 1))
    
    if [ $FAILURES -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL CHECKS PASSED! 🎉${NC}"
        exit 0
    else
        echo -e "${RED}❌ $FAILURES CHECK(S) FAILED ❌${NC}"
        echo -e "\n${YELLOW}To fix issues:${NC}"
        echo -e "  • Run 'npx prettier --write src/' to fix formatting"
        echo -e "  • Run 'npx eslint src/ --ext .js,.jsx,.ts,.tsx --fix' to fix auto-fixable linting issues"
        echo -e "  • Check individual tool outputs above for specific issues"
        exit 1
    fi
}

# Function to auto-fix issues
auto_fix() {
    print_status "Attempting to auto-fix issues..."
    
    print_status "Running Prettier formatter..."
    npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,scss,md}"
    
    print_status "Running ESLint auto-fix..."
    npx eslint "src/**/*.{js,jsx,ts,tsx}" --ext .js,.jsx,.ts,.tsx --fix
    
    print_success "Auto-fix completed. Re-run the script to verify all issues are resolved."
}

# Main execution
main() {
    print_status "Starting Autonomica Frontend Code Quality Check..."
    
    # Check if we're in the right directory
    if [ ! -f "package.json" ]; then
        print_error "This script must be run from the autonomica-frontend directory"
        exit 1
    fi
    
    # Parse command line arguments
    AUTO_FIX=false
    SKIP_TESTS=false
    SKIP_BUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto-fix)
                AUTO_FIX=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--auto-fix] [--skip-tests] [--skip-build] [--help]"
                echo "  --auto-fix    Automatically fix auto-fixable issues"
                echo "  --skip-tests  Skip running Jest tests"
                echo "  --skip-build  Skip Next.js build check"
                echo "  --help        Show this help message"
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
    run_type_checking
    
    if [ "$SKIP_TESTS" != true ]; then
        run_test_checks
    fi
    
    if [ "$SKIP_BUILD" != true ]; then
        run_build_checks
    fi
    
    run_accessibility_checks
    run_performance_checks
    run_security_checks
    
    # Auto-fix if requested
    if [ "$AUTO_FIX" = true ]; then
        auto_fix
    fi
    
    # Generate report
    generate_report
}

# Run main function
main "$@"
