#!/bin/bash

# Rollback Management Script
# This script provides management functions for the automated rollback system

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ROLLBACK_DIR="$PROJECT_ROOT/rollback"

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

# Check if rollback service is running
check_service_status() {
    if pgrep -f "rollback-service.py" > /dev/null; then
        echo "running"
    else
        echo "stopped"
    fi
}

# Start rollback service
start_service() {
    log_info "Starting rollback service..."
    
    if [ "$(check_service_status)" = "running" ]; then
        log_warning "Rollback service is already running"
        return 0
    fi
    
    cd "$ROLLBACK_DIR"
    
    # Create log directory if it doesn't exist
    sudo mkdir -p /var/log/rollback
    sudo chown $USER:$USER /var/log/rollback
    
    # Start service in background
    nohup python3 rollback-service.py > /var/log/rollback/service.log 2>&1 &
    
    # Wait for service to start
    sleep 5
    
    if [ "$(check_service_status)" = "running" ]; then
        log_success "Rollback service started successfully"
        return 0
    else
        log_error "Failed to start rollback service"
        return 1
    fi
}

# Stop rollback service
stop_service() {
    log_info "Stopping rollback service..."
    
    if [ "$(check_service_status)" = "stopped" ]; then
        log_warning "Rollback service is already stopped"
        return 0
    fi
    
    # Find and kill rollback service processes
    pkill -f "rollback-service.py" || true
    
    # Wait for service to stop
    sleep 3
    
    if [ "$(check_service_status)" = "stopped" ]; then
        log_success "Rollback service stopped successfully"
        return 0
    else
        log_error "Failed to stop rollback service"
        return 1
    fi
}

# Restart rollback service
restart_service() {
    log_info "Restarting rollback service..."
    
    stop_service
    sleep 2
    start_service
}

# Check rollback service health
check_health() {
    log_info "Checking rollback service health..."
    
    # Check if service is running
    if [ "$(check_service_status)" = "stopped" ]; then
        log_error "Rollback service is not running"
        return 1
    fi
    
    # Check log files
    if [ -f "/var/log/rollback/service.log" ]; then
        log_info "Service log file exists"
        
        # Check for recent activity
        if tail -n 10 "/var/log/rollback/service.log" | grep -q "$(date '+%Y-%m-%d')"; then
            log_success "Service log shows recent activity"
        else
            log_warning "Service log shows no recent activity"
        fi
    else
        log_warning "Service log file not found"
    fi
    
    # Check rollback log
    if [ -f "/var/log/rollback/rollback-service.log" ]; then
        log_info "Rollback log file exists"
        
        # Check for errors
        error_count=$(tail -n 100 "/var/log/rollback/rollback-service.log" | grep -c "ERROR" || echo "0")
        if [ "$error_count" -gt 0 ]; then
            log_warning "Found $error_count errors in rollback log"
        else
            log_success "No errors found in rollback log"
        fi
    else
        log_warning "Rollback log file not found"
    fi
    
    log_success "Health check completed"
}

# View rollback service logs
view_logs() {
    local log_type="${1:-service}"
    
    case "$log_type" in
        "service"|"s")
            if [ -f "/var/log/rollback/service.log" ]; then
                tail -f "/var/log/rollback/service.log"
            else
                log_error "Service log file not found"
                return 1
            fi
            ;;
        "rollback"|"r")
            if [ -f "/var/log/rollback/rollback-service.log" ]; then
                tail -f "/var/log/rollback/rollback-service.log"
            else
                log_error "Rollback log file not found"
                return 1
            fi
            ;;
        *)
            log_error "Invalid log type. Use 'service' or 'rollback'"
            return 1
            ;;
    esac
}

# Test rollback system
test_rollback() {
    log_info "Testing rollback system..."
    
    # Check if service is running
    if [ "$(check_service_status)" = "stopped" ]; then
        log_error "Cannot test rollback system - service is not running"
        return 1
    fi
    
    # Test configuration loading
    cd "$ROLLBACK_DIR"
    if python3 -c "import yaml; yaml.safe_load(open('rollback-config.yml'))" 2>/dev/null; then
        log_success "Configuration file is valid YAML"
    else
        log_error "Configuration file has invalid YAML syntax"
        return 1
    fi
    
    # Test Python imports
    if python3 -c "import docker, requests, yaml" 2>/dev/null; then
        log_success "All required Python packages are available"
    else
        log_error "Missing required Python packages"
        return 1
    fi
    
    # Test configuration structure
    if python3 -c "
import yaml
config = yaml.safe_load(open('rollback-config.yml'))
required_keys = ['rollback']
for key in required_keys:
    if key not in config:
        exit(1)
exit(0)
" 2>/dev/null; then
        log_success "Configuration structure is valid"
    else
        log_error "Configuration structure is invalid"
        return 1
    fi
    
    log_success "Rollback system test completed successfully"
}

# Show rollback statistics
show_stats() {
    log_info "Rollback system statistics..."
    
    # Check if service is running
    if [ "$(check_service_status)" = "stopped" ]; then
        log_error "Cannot show statistics - service is not running"
        return 1
    fi
    
    # This would typically query the rollback service API
    # For now, we'll show basic information
    
    log_info "Service Status: $(check_service_status)"
    
    if [ -f "/var/log/rollback/rollback-service.log" ]; then
        log_info "Rollback Log Size: $(du -h "/var/log/rollback/rollback-service.log" | cut -f1)"
        
        # Count rollback events
        rollback_count=$(grep -c "Rollback initiated" "/var/log/rollback/rollback-service.log" 2>/dev/null || echo "0")
        log_info "Total Rollbacks: $rollback_count"
        
        # Count successful rollbacks
        success_count=$(grep -c "Rollback completed successfully" "/var/log/rollback/rollback-service.log" 2>/dev/null || echo "0")
        log_info "Successful Rollbacks: $success_count"
        
        # Count failed rollbacks
        failed_count=$(grep -c "Rollback failed" "/var/log/rollback/rollback-service.log" 2>/dev/null || echo "0")
        log_info "Failed Rollbacks: $failed_count"
        
        if [ "$rollback_count" -gt 0 ]; then
            success_rate=$((success_count * 100 / rollback_count))
            log_info "Success Rate: ${success_rate}%"
        fi
    fi
    
    log_success "Statistics display completed"
}

# Backup rollback configuration
backup_config() {
    local backup_dir="${1:-$PROJECT_ROOT/backups}"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    
    log_info "Backing up rollback configuration..."
    
    # Create backup directory
    mkdir -p "$backup_dir"
    
    # Backup configuration files
    tar -czf "$backup_dir/rollback_config_$timestamp.tar.gz" \
        -C "$ROLLBACK_DIR" \
        rollback-config.yml \
        *.py \
        *.sh \
        README.md
    
    if [ $? -eq 0 ]; then
        log_success "Configuration backed up to $backup_dir/rollback_config_$timestamp.tar.gz"
    else
        log_error "Failed to backup configuration"
        return 1
    fi
}

# Restore rollback configuration
restore_config() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "Please specify backup file to restore"
        return 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring rollback configuration from $backup_file..."
    
    # Stop service if running
    if [ "$(check_service_status)" = "running" ]; then
        stop_service
    fi
    
    # Backup current configuration
    backup_config
    
    # Restore from backup
    cd "$ROLLBACK_DIR"
    tar -xzf "$backup_file"
    
    if [ $? -eq 0 ]; then
        log_success "Configuration restored successfully"
        
        # Restart service
        start_service
    else
        log_error "Failed to restore configuration"
        return 1
    fi
}

# Show help
show_help() {
    echo "Rollback Management Script"
    echo "========================="
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start           Start the rollback service"
    echo "  stop            Stop the rollback service"
    echo "  restart         Restart the rollback service"
    echo "  status          Show service status"
    echo "  health          Check service health"
    echo "  logs [TYPE]     View service logs (service|rollback)"
    echo "  test            Test rollback system"
    echo "  stats           Show rollback statistics"
    echo "  backup [DIR]    Backup rollback configuration"
    echo "  restore FILE    Restore rollback configuration"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start the service"
    echo "  $0 logs rollback           # View rollback logs"
    echo "  $0 backup /tmp/backups     # Backup to specific directory"
    echo "  $0 restore backup.tar.gz   # Restore from backup"
}

# Main function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            echo "Rollback Service Status: $(check_service_status)"
            ;;
        "health")
            check_health
            ;;
        "logs")
            view_logs "$2"
            ;;
        "test")
            test_rollback
            ;;
        "stats")
            show_stats
            ;;
        "backup")
            backup_config "$2"
            ;;
        "restore")
            restore_config "$2"
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"