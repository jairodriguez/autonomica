#!/bin/bash

# Production Monitoring Setup Script
# This script sets up comprehensive monitoring and alerting for the production environment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

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

# Create monitoring directory structure
create_monitoring_structure() {
    log_info "Creating monitoring directory structure..."
    
    mkdir -p "$MONITORING_DIR"/{prometheus,alertmanager,grafana/{provisioning/{dashboards,datasources},dashboards}}
    
    log_success "Monitoring directory structure created"
}

# Make scripts executable
make_scripts_executable() {
    log_info "Making scripts executable..."
    
    chmod +x "$MONITORING_DIR"/start-monitoring.sh
    chmod +x "$MONITORING_DIR"/health-check.sh
    chmod +x "$MONITORING_DIR"/setup-monitoring.sh
    
    log_success "Scripts made executable"
}

# Main setup function
main() {
    echo "🔍 Setting up Production Monitoring and Alerting"
    echo "================================================"
    echo ""
    
    # Change to monitoring directory
    cd "$MONITORING_DIR"
    
    # Create monitoring structure
    create_monitoring_structure
    
    # Make scripts executable
    make_scripts_executable
    
    log_success "🎉 Production monitoring and alerting setup completed!"
    echo ""
    echo "📁 Monitoring files created in: $MONITORING_DIR"
    echo ""
    echo "🚀 To start monitoring:"
    echo "  cd $MONITORING_DIR"
    echo "  ./start-monitoring.sh"
    echo ""
    echo "🔍 To check monitoring health:"
    echo "  ./health-check.sh"
    echo ""
    echo "📊 Access monitoring interfaces:"
    echo "  Prometheus: http://localhost:9090"
    echo "  Alertmanager: http://localhost:9093"
    echo "  Grafana: http://localhost:3001"
    echo ""
    echo "⚠️  Don't forget to set environment variables:"
    echo "  export SMTP_PASSWORD='your_smtp_password'"
    echo "  export WEBHOOK_SLACK_URL='your_slack_webhook_url'"
    echo "  export GRAFANA_ADMIN_PASSWORD='your_grafana_password'"
    echo "  export DATABASE_PASSWORD='your_database_password'"
    echo "  export REDIS_PASSWORD='your_redis_password'"
}

# Run main function
main "$@"