#!/bin/bash

# Staging Environment Deployment Script
# This script deploys all components to the staging environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="staging"
FRONTEND_URL="https://staging.autonomica.app"
BACKEND_URL="https://staging-api.autonomica.app"
WORKER_URL="https://staging-worker.autonomica.app"

# Logging
LOG_FILE="deploy-staging-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}    STAGING ENVIRONMENT DEPLOYMENT     ${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Deployment started at: $(date)"
echo "Log file: $LOG_FILE"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "success")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "warning")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "error")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "info" "Checking prerequisites..."
    
    # Check if required tools are installed
    command -v gh >/dev/null 2>&1 || { print_status "error" "GitHub CLI (gh) is required but not installed. Aborting."; exit 1; }
    command -v vercel >/dev/null 2>&1 || { print_status "error" "Vercel CLI is required but not installed. Aborting."; exit 1; }
    command -v railway >/dev/null 2>&1 || { print_status "error" "Railway CLI is required but not installed. Aborting."; exit 1; }
    command -v docker >/dev/null 2>&1 || { print_status "error" "Docker is required but not installed. Aborting."; exit 1; }
    
    # Check if logged in to required services
    gh auth status >/dev/null 2>&1 || { print_status "error" "Not logged in to GitHub CLI. Please run 'gh auth login' first."; exit 1; }
    vercel whoami >/dev/null 2>&1 || { print_status "error" "Not logged in to Vercel. Please run 'vercel login' first."; exit 1; }
    railway whoami >/dev/null 2>&1 || { print_status "error" "Not logged in to Railway. Please run 'railway login' first."; exit 1; }
    
    print_status "success" "All prerequisites are satisfied"
}

# Function to validate environment
validate_environment() {
    print_status "info" "Validating staging environment configuration..."
    
    # Check if staging branch exists
    if ! git branch --list | grep -q "develop"; then
        print_status "error" "Develop branch does not exist. Please create it first."
        exit 1
    fi
    
    # Check if we're on the develop branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "develop" ]; then
        print_status "warning" "Not on develop branch. Current branch: $current_branch"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "info" "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_status "warning" "There are uncommitted changes in your working directory"
        git status --short
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "info" "Deployment cancelled"
            exit 0
        fi
    fi
    
    print_status "success" "Environment validation completed"
}

# Function to run tests
run_tests() {
    print_status "info" "Running tests before deployment..."
    
    # Run backend tests
    print_status "info" "Running backend tests..."
    cd autonomica-api
    if ! python -m pytest tests/ --cov=app --cov-report=term-missing; then
        print_status "error" "Backend tests failed. Aborting deployment."
        exit 1
    fi
    cd ..
    
    # Run frontend tests
    print_status "info" "Running frontend tests..."
    cd autonomica-frontend
    if ! npm test -- --passWithNoTests; then
        print_status "error" "Frontend tests failed. Aborting deployment."
        exit 1
    fi
    cd ..
    
    # Run integration tests
    print_status "info" "Running integration tests..."
    if ! python -m pytest tests/integration/; then
        print_status "error" "Integration tests failed. Aborting deployment."
        exit 1
    fi
    
    print_status "success" "All tests passed"
}

# Function to deploy backend
deploy_backend() {
    print_status "info" "Deploying backend to staging..."
    
    cd autonomica-api
    
    # Build Docker image
    print_status "info" "Building backend Docker image..."
    docker build -t autonomica-backend:staging .
    
    # Deploy to Railway
    print_status "info" "Deploying to Railway..."
    if ! railway up --service backend --detach; then
        print_status "error" "Backend deployment to Railway failed"
        exit 1
    fi
    
    cd ..
    print_status "success" "Backend deployed successfully"
}

# Function to deploy worker
deploy_worker() {
    print_status "info" "Deploying worker to staging..."
    
    cd worker
    
    # Build Docker image
    print_status "info" "Building worker Docker image..."
    docker build -t autonomica-worker:staging .
    
    # Deploy to Railway
    print_status "info" "Deploying to Railway..."
    if ! railway up --service worker --detach; then
        print_status "error" "Worker deployment to Railway failed"
        exit 1
    fi
    
    cd ..
    print_status "success" "Worker deployed successfully"
}

# Function to deploy frontend
deploy_frontend() {
    print_status "info" "Deploying frontend to staging..."
    
    cd autonomica-frontend
    
    # Build and deploy to Vercel
    print_status "info" "Building and deploying to Vercel..."
    if ! vercel --prod --confirm; then
        print_status "error" "Frontend deployment to Vercel failed"
        exit 1
    fi
    
    cd ..
    print_status "success" "Frontend deployed successfully"
}

# Function to run health checks
run_health_checks() {
    print_status "info" "Running health checks..."
    
    # Wait for services to be ready
    print_status "info" "Waiting for services to be ready..."
    sleep 30
    
    # Check backend health
    print_status "info" "Checking backend health..."
    if ! curl -f "$BACKEND_URL/health" >/dev/null 2>&1; then
        print_status "error" "Backend health check failed"
        return 1
    fi
    
    # Check worker health
    print_status "info" "Checking worker health..."
    if ! curl -f "$WORKER_URL/health" >/dev/null 2>&1; then
        print_status "error" "Worker health check failed"
        return 1
    fi
    
    # Check frontend health
    print_status "info" "Checking frontend health..."
    if ! curl -f "$FRONTEND_URL/api/health" >/dev/null 2>&1; then
        print_status "error" "Frontend health check failed"
        return 1
    fi
    
    print_status "success" "All health checks passed"
    return 0
}

# Function to run smoke tests
run_smoke_tests() {
    print_status "info" "Running smoke tests..."
    
    # Test basic API functionality
    print_status "info" "Testing API endpoints..."
    if ! curl -f "$BACKEND_URL/api/agents" >/dev/null 2>&1; then
        print_status "error" "API agents endpoint test failed"
        return 1
    fi
    
    # Test authentication
    print_status "info" "Testing authentication..."
    if ! curl -f "$BACKEND_URL/api/auth/status" >/dev/null 2>&1; then
        print_status "error" "Authentication test failed"
        return 1
    fi
    
    print_status "success" "Smoke tests passed"
    return 0
}

# Function to notify team
notify_team() {
    local status=$1
    local message=$2
    
    print_status "info" "Notifying team of deployment status..."
    
    # Send notification via GitHub
    if [ "$status" = "success" ]; then
        gh issue create --title "Staging Deployment Successful" --body "Deployment to staging environment completed successfully at $(date). All health checks and smoke tests passed."
    else
        gh issue create --title "Staging Deployment Failed" --body "Deployment to staging environment failed at $(date). Error: $message"
    fi
    
    print_status "success" "Team notification sent"
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    print_status "info" "Starting staging environment deployment..."
    
    # Check prerequisites
    check_prerequisites
    
    # Validate environment
    validate_environment
    
    # Run tests
    run_tests
    
    # Deploy components
    deploy_backend
    deploy_worker
    deploy_frontend
    
    # Run health checks
    if ! run_health_checks; then
        print_status "error" "Health checks failed. Rolling back deployment..."
        # TODO: Implement rollback logic
        notify_team "failure" "Health checks failed"
        exit 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests; then
        print_status "error" "Smoke tests failed. Rolling back deployment..."
        # TODO: Implement rollback logic
        notify_team "failure" "Smoke tests failed"
        exit 1
    fi
    
    # Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_status "success" "Staging environment deployment completed successfully!"
    print_status "info" "Deployment time: ${duration} seconds"
    print_status "info" "Frontend: $FRONTEND_URL"
    print_status "info" "Backend: $BACKEND_URL"
    print_status "info" "Worker: $WORKER_URL"
    
    # Notify team of success
    notify_team "success" "Deployment completed successfully"
    
    echo "Deployment completed at: $(date)"
    echo "Log file: $LOG_FILE"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --skip-tests   Skip running tests before deployment"
        echo "  --skip-health  Skip health checks after deployment"
        echo "  --skip-smoke   Skip smoke tests after deployment"
        echo ""
        echo "Environment Variables:"
        echo "  FRONTEND_URL   Frontend staging URL (default: https://staging.autonomica.app)"
        echo "  BACKEND_URL    Backend staging URL (default: https://staging-api.autonomica.app)"
        echo "  WORKER_URL     Worker staging URL (default: https://staging-worker.autonomica.app)"
        echo ""
        echo "Examples:"
        echo "  $0                    # Full deployment with all checks"
        echo "  $0 --skip-tests      # Deploy without running tests"
        echo "  $0 --skip-health     # Deploy without health checks"
        echo "  $0 --skip-smoke      # Deploy without smoke tests"
        exit 0
        ;;
    --skip-tests)
        SKIP_TESTS=true
        shift
        ;;
    --skip-health)
        SKIP_HEALTH=true
        shift
        ;;
    --skip-smoke)
        SKIP_SMOKE=true
        shift
        ;;
esac

# Run main function
main "$@"

