#!/bin/bash

# Staging Environment Deployment Script
# This script deploys the Autonomica application to the staging environment

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STAGING_ENV_FILE="$PROJECT_ROOT/staging.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.staging.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are available
check_dependencies() {
    log_info "Checking deployment dependencies..."
    
    local missing_tools=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

# Validate environment configuration
validate_environment() {
    log_info "Validating staging environment configuration..."
    
    if [ ! -f "$STAGING_ENV_FILE" ]; then
        log_error "Staging environment file not found: $STAGING_ENV_FILE"
        exit 1
    fi
    
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Staging Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "OPENAI_API_KEY"
        "CLERK_SECRET_KEY"
        "CLERK_PUBLISHABLE_KEY"
        "DATABASE_PASSWORD"
        "SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$STAGING_ENV_FILE"; then
            log_warning "Required environment variable not set: $var"
        fi
    done
    
    log_success "Environment configuration validated"
}

# Run pre-deployment tests
run_tests() {
    log_info "Running pre-deployment tests..."
    
    cd "$PROJECT_ROOT"
    
    # Backend tests
    if [ -d "autonomica-api" ]; then
        log_info "Running backend tests..."
        cd autonomica-api
        
        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt
        fi
        
        if [ -f "run_code_quality.py" ]; then
            python run_code_quality.py --check security
            python run_code_quality.py --check linting
        fi
        
        if [ -f "run_integration_tests.py" ]; then
            python run_integration_tests.py
        fi
        
        cd ..
    fi
    
    # Frontend tests
    if [ -d "autonomica-frontend" ]; then
        log_info "Running frontend tests..."
        cd autonomica-frontend
        
        if [ -f "package.json" ]; then
            npm ci
            npm run test:ci
            npm run lint:all
            npm run format:prettier:check
        fi
        
        cd ..
    fi
    
    log_success "All tests passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images for staging..."
    
    cd "$PROJECT_ROOT"
    
    # Build frontend image
    if [ -d "autonomica-frontend" ]; then
        log_info "Building frontend image..."
        docker build -t autonomica-frontend:staging \
            --target staging \
            --build-arg NODE_ENV=staging \
            ./autonomica-frontend
    fi
    
    # Build backend API image
    if [ -d "autonomica-api" ]; then
        log_info "Building backend API image..."
        docker build -t autonomica-api:staging \
            --target staging \
            --build-arg ENVIRONMENT=staging \
            ./autonomica-api
    fi
    
    # Build worker image
    if [ -d "autonomica-worker" ]; then
        log_info "Building worker image..."
        docker build -t autonomica-worker:staging \
            --target staging \
            --build-arg ENVIRONMENT=staging \
            ./autonomica-worker
    fi
    
    log_success "All Docker images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying staging services..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    log_info "Stopping existing staging services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
    
    # Start services
    log_info "Starting staging services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    wait_for_services
    
    log_success "All services deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Checking service health (attempt $attempt/$max_attempts)..."
        
        local all_healthy=true
        
        # Check database
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-db pg_isready -U staging_user -d autonomica_staging &> /dev/null; then
            all_healthy=false
        fi
        
        # Check Redis
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-redis redis-cli ping &> /dev/null; then
            all_healthy=false
        fi
        
        # Check API health
        if ! curl -f http://localhost:8000/health &> /dev/null; then
            all_healthy=false
        fi
        
        # Check frontend health
        if ! curl -f http://localhost:3000/health &> /dev/null; then
            all_healthy=false
        fi
        
        if [ "$all_healthy" = true ]; then
            log_success "All services are healthy"
            return 0
        fi
        
        log_info "Some services are not ready yet, waiting 10 seconds..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services did not become healthy within expected time"
    return 1
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "autonomica-api" ]; then
        cd autonomica-api
        
        # Wait for database to be ready
        local max_attempts=10
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-db pg_isready -U staging_user -d autonomica_staging &> /dev/null; then
                break
            fi
            
            log_info "Database not ready, waiting 5 seconds... (attempt $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        done
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Database did not become ready"
            return 1
        fi
        
        # Run migrations if Alembic is available
        if [ -f "alembic.ini" ] && command -v alembic &> /dev/null; then
            log_info "Running Alembic migrations..."
            alembic upgrade head
        fi
        
        cd ..
    fi
    
    log_success "Database migrations completed"
}

# Initialize database with sample data
initialize_database() {
    log_info "Initializing database with sample data..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "database/init" ]; then
        log_info "Running database initialization scripts..."
        
        # Wait for database to be ready
        sleep 10
        
        # Run initialization scripts
        for script in database/init/*.sql; do
            if [ -f "$script" ]; then
                log_info "Running initialization script: $script"
                docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-db psql -U staging_user -d autonomica_staging -f "/docker-entrypoint-initdb.d/$(basename "$script")"
            fi
        done
    fi
    
    log_success "Database initialization completed"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    local test_results=()
    
    # Test frontend
    if curl -f http://localhost:3000/health &> /dev/null; then
        test_results+=("✅ Frontend health check passed")
    else
        test_results+=("❌ Frontend health check failed")
    fi
    
    # Test API
    if curl -f http://localhost:8000/health &> /dev/null; then
        test_results+=("✅ API health check passed")
    else
        test_results+=("❌ API health check failed")
    fi
    
    # Test worker
    if curl -f http://localhost:8001/health &> /dev/null; then
        test_results+=("✅ Worker health check passed")
    else
        test_results+=("❌ Worker health check failed")
    fi
    
    # Test database connection
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-db pg_isready -U staging_user -d autonomica_staging &> /dev/null; then
        test_results+=("✅ Database connection test passed")
    else
        test_results+=("❌ Database connection test failed")
    fi
    
    # Test Redis connection
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-redis redis-cli ping &> /dev/null; then
        test_results+=("✅ Redis connection test passed")
    else
        test_results+=("❌ Redis connection test failed")
    fi
    
    # Display results
    echo ""
    log_info "Smoke test results:"
    for result in "${test_results[@]}"; do
        echo "  $result"
    done
    
    # Check if all tests passed
    local failed_tests=$(echo "${test_results[@]}" | grep -c "❌" || true)
    
    if [ "$failed_tests" -eq 0 ]; then
        log_success "All smoke tests passed"
    else
        log_error "$failed_tests smoke test(s) failed"
        return 1
    fi
}

# Display deployment information
show_deployment_info() {
    log_info "Staging deployment completed successfully!"
    echo ""
    echo "🌐 Service URLs:"
    echo "  Frontend:     http://localhost:3000"
    echo "  API:          http://localhost:8000"
    echo "  Worker:       http://localhost:8001"
    echo "  Monitoring:   http://localhost:9090 (Prometheus)"
    echo "  Grafana:      http://localhost:3001"
    echo "  Logs:         http://localhost:5601 (Kibana)"
    echo ""
    echo "📊 Health Checks:"
    echo "  Frontend:     http://localhost:3000/health"
    echo "  API:          http://localhost:8000/health"
    echo "  Worker:       http://localhost:8001/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:    docker-compose -f docker-compose.staging.yml logs -f"
    echo "  Stop:         docker-compose -f docker-compose.staging.yml down"
    echo "  Restart:      docker-compose -f docker-compose.staging.yml restart"
    echo "  Scale:        docker-compose -f docker-compose.staging.yml up -d --scale api-staging=3"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Verify all services are running correctly"
    echo "  2. Test the application functionality"
    echo "  3. Monitor logs and metrics"
    echo "  4. Run integration tests if needed"
}

# Main deployment function
main() {
    echo "🚀 Autonomica Staging Environment Deployment"
    echo "============================================="
    echo ""
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root is not recommended"
    fi
    
    # Parse command line arguments
    local skip_tests=false
    local skip_migrations=false
    local force_rebuild=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-migrations)
                skip_migrations=true
                shift
                ;;
            --force-rebuild)
                force_rebuild=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-tests        Skip running tests before deployment"
                echo "  --skip-migrations   Skip running database migrations"
                echo "  --force-rebuild     Force rebuild of all Docker images"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Run deployment steps
    check_dependencies
    validate_environment
    
    if [ "$skip_tests" = false ]; then
        run_tests
    else
        log_warning "Skipping tests as requested"
    fi
    
    if [ "$force_rebuild" = true ]; then
        log_info "Force rebuilding all images..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down --rmi all
    fi
    
    build_images
    deploy_services
    
    if [ "$skip_migrations" = false ]; then
        run_migrations
        initialize_database
    else
        log_warning "Skipping migrations as requested"
    fi
    
    run_smoke_tests
    show_deployment_info
    
    log_success "Staging deployment completed successfully!"
}

# Run main function with all arguments
main "$@"