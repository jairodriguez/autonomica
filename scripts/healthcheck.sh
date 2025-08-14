#!/bin/bash

# Staging Environment Health Check Script
# This script checks the health of all services in the staging environment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
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

# Health check results
declare -A health_results
declare -A response_times

# Check service health
check_service_health() {
    local service_name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    log_info "Checking $service_name health at $url"
    
    local start_time=$(date +%s%N)
    local response_code=0
    local response_body=""
    
    # Try to get response
    if response_body=$(curl -s -w "%{http_code}" -o /dev/null "$url" 2>/dev/null); then
        response_code="$response_body"
        local end_time=$(date +%s%N)
        local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        
        if [ "$response_code" -eq "$expected_status" ]; then
            health_results["$service_name"]="healthy"
            response_times["$service_name"]="$duration"
            log_success "$service_name is healthy (${duration}ms)"
        else
            health_results["$service_name"]="unhealthy"
            response_times["$service_name"]="$duration"
            log_error "$service_name returned status $response_code (expected $expected_status)"
        fi
    else
        health_results["$service_name"]="unreachable"
        response_times["$service_name"]="timeout"
        log_error "$service_name is unreachable"
    fi
}

# Check database health
check_database_health() {
    log_info "Checking database health..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-db pg_isready -U staging_user -d autonomica_staging &> /dev/null; then
        health_results["database"]="healthy"
        response_times["database"]="0"
        log_success "Database is healthy"
    else
        health_results["database"]="unhealthy"
        response_times["database"]="timeout"
        log_error "Database is unhealthy"
    fi
}

# Check Redis health
check_redis_health() {
    log_info "Checking Redis health..."
    
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T staging-redis redis-cli ping &> /dev/null; then
        health_results["redis"]="healthy"
        response_times["redis"]="0"
        log_success "Redis is healthy"
    else
        health_results["redis"]="unhealthy"
        response_times["redis"]="timeout"
        log_error "Redis is unhealthy"
    fi
}

# Check container status
check_container_status() {
    log_info "Checking container status..."
    
    local containers=(
        "frontend-staging"
        "api-staging"
        "worker-staging"
        "staging-db"
        "staging-redis"
        "nginx-staging"
        "traefik-staging"
        "prometheus-staging"
        "grafana-staging"
        "elasticsearch-staging"
        "kibana-staging"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container"; then
            local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container" | awk '{print $2}')
            health_results["container_$container"]="running"
            log_success "Container $container is $status"
        else
            health_results["container_$container"]="stopped"
            log_error "Container $container is not running"
        fi
    done
}

# Check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Check CPU and memory usage
    local cpu_usage=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" | tail -n +2 | head -5)
    local disk_usage=$(df -h / | tail -n 1 | awk '{print $5}')
    
    log_info "Top 5 containers by resource usage:"
    echo "$cpu_usage" | while IFS=$'\t' read -r cpu mem; do
        echo "  CPU: $cpu, Memory: $mem"
    done
    
    log_info "Disk usage: $disk_usage"
    
    # Check if disk usage is high
    local disk_percent=$(echo "$disk_usage" | sed 's/%//')
    if [ "$disk_percent" -gt 80 ]; then
        log_warning "Disk usage is high: $disk_usage"
    fi
}

# Check network connectivity
check_network_connectivity() {
    log_info "Checking network connectivity..."
    
    local endpoints=(
        "https://api.openai.com"
        "https://api.clerk.dev"
        "https://www.google.com"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -s --connect-timeout 5 "$endpoint" &> /dev/null; then
            log_success "Network connectivity to $endpoint: OK"
        else
            log_warning "Network connectivity to $endpoint: FAILED"
        fi
    done
}

# Check log health
check_log_health() {
    log_info "Checking log health..."
    
    # Check for recent errors in logs
    local error_count=$(docker-compose -f "$DOCKER_COMPOSE_FILE" logs --since=1h 2>&1 | grep -i "error\|exception\|traceback" | wc -l)
    
    if [ "$error_count" -eq 0 ]; then
        log_success "No recent errors found in logs"
    else
        log_warning "Found $error_count recent errors in logs"
    fi
    
    # Check log file sizes
    if [ -d "$PROJECT_ROOT/logs" ]; then
        log_info "Log file sizes:"
        find "$PROJECT_ROOT/logs" -name "*.log" -exec ls -lh {} \; 2>/dev/null | head -5
    fi
}

# Generate health report
generate_health_report() {
    echo ""
    echo "📊 STAGING ENVIRONMENT HEALTH REPORT"
    echo "===================================="
    echo "Generated: $(date)"
    echo ""
    
    # Service health summary
    echo "🏥 SERVICE HEALTH SUMMARY"
    echo "-------------------------"
    
    local healthy_count=0
    local unhealthy_count=0
    local total_count=0
    
    for service in "${!health_results[@]}"; do
        local status="${health_results[$service]}"
        local response_time="${response_times[$service]}"
        
        case "$status" in
            "healthy"|"running")
                echo "  ✅ $service: $status"
                if [ "$response_time" != "0" ] && [ "$response_time" != "timeout" ]; then
                    echo "      Response time: ${response_time}ms"
                fi
                ((healthy_count++))
                ;;
            "unhealthy"|"stopped")
                echo "  ❌ $service: $status"
                ((unhealthy_count++))
                ;;
            *)
                echo "  ⚠️  $service: $status"
                ;;
        esac
        ((total_count++))
    done
    
    echo ""
    echo "📈 HEALTH SCORE: $(( (healthy_count * 100) / total_count ))%"
    echo "  ✅ Healthy: $healthy_count"
    echo "  ❌ Unhealthy: $unhealthy_count"
    echo "  📊 Total: $total_count"
    echo ""
    
    # Recommendations
    echo "💡 RECOMMENDATIONS"
    echo "------------------"
    
    if [ $unhealthy_count -eq 0 ]; then
        echo "🎉 All services are healthy! No action needed."
    else
        echo "🔧 Actions needed:"
        
        for service in "${!health_results[@]}"; do
            local status="${health_results[$service]}"
            if [ "$status" = "unhealthy" ] || [ "$status" = "stopped" ]; then
                case "$service" in
                    "frontend")
                        echo "  • Restart frontend service: docker-compose -f docker-compose.staging.yml restart frontend-staging"
                        ;;
                    "api")
                        echo "  • Restart API service: docker-compose -f docker-compose.staging.yml restart api-staging"
                        ;;
                    "worker")
                        echo "  • Restart worker service: docker-compose -f docker-compose.staging.yml restart worker-staging"
                        ;;
                    "database")
                        echo "  • Check database logs: docker-compose -f docker-compose.staging.yml logs staging-db"
                        ;;
                    "redis")
                        echo "  • Check Redis logs: docker-compose -f docker-compose.staging.yml logs staging-redis"
                        ;;
                    container_*)
                        local container_name=$(echo "$service" | sed 's/container_//')
                        echo "  • Restart container $container_name: docker restart $container_name"
                        ;;
                esac
            fi
        done
    fi
    
    echo ""
    echo "🔍 TROUBLESHOOTING COMMANDS"
    echo "----------------------------"
    echo "  View all logs: docker-compose -f docker-compose.staging.yml logs -f"
    echo "  View specific service logs: docker-compose -f docker-compose.staging.yml logs -f [service-name]"
    echo "  Check container status: docker ps"
    echo "  Check resource usage: docker stats"
    echo "  Access service directly: curl -v [service-url]"
    echo ""
}

# Main health check function
main() {
    echo "🏥 Autonomica Staging Environment Health Check"
    echo "=============================================="
    echo ""
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if Docker Compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Staging Docker Compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    # Run health checks
    check_service_health "Frontend" "http://localhost:3000/health"
    check_service_health "API" "http://localhost:8000/health"
    check_service_health "Worker" "http://localhost:8001/health"
    check_service_health "Monitoring" "http://localhost:9090/-/healthy"
    check_service_health "Grafana" "http://localhost:3001/api/health"
    check_service_health "Logs" "http://localhost:5601/api/status"
    
    check_database_health
    check_redis_health
    check_container_status
    check_resource_usage
    check_network_connectivity
    check_log_health
    
    # Generate report
    generate_health_report
    
    # Exit with appropriate code
    local unhealthy_count=0
    for status in "${health_results[@]}"; do
        if [ "$status" = "unhealthy" ] || [ "$status" = "stopped" ]; then
            ((unhealthy_count++))
        fi
    done
    
    if [ $unhealthy_count -eq 0 ]; then
        log_success "Health check completed successfully"
        exit 0
    else
        log_error "Health check found $unhealthy_count unhealthy services"
        exit 1
    fi
}

# Run main function
main "$@"