#!/bin/bash

# Autonomica Ollama Docker Management Script
# This script provides easy management of Ollama Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.ollama.yml"
PROJECT_NAME="autonomica-ollama"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Autonomica Ollama Manager${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install it and try again."
        exit 1
    fi
    print_status "Docker Compose is available"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p ollama-models
    mkdir -p ollama-config
    mkdir -p models
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/provisioning/datasources
    mkdir -p monitoring/grafana/dashboards
    
    print_status "Directories created successfully"
}

# Function to start Ollama services
start_services() {
    print_status "Starting Ollama services..."
    
    if [ "$1" = "full" ]; then
        print_status "Starting full monitoring stack..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d
    else
        print_status "Starting Ollama only..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME up -d ollama
    fi
    
    print_status "Services started successfully"
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Ollama is healthy and ready!"
    else
        print_warning "Ollama may still be starting up. Check logs with: docker-compose -f $COMPOSE_FILE logs ollama"
    fi
}

# Function to stop services
stop_services() {
    print_status "Stopping Ollama services..."
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down
    print_status "Services stopped successfully"
}

# Function to restart services
restart_services() {
    print_status "Restarting Ollama services..."
    stop_services
    sleep 5
    start_services
}

# Function to show service status
show_status() {
    print_status "Service status:"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME ps
    
    echo ""
    print_status "Container logs (last 10 lines):"
    docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs --tail=10
}

# Function to show logs
show_logs() {
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f
    else
        print_status "Showing logs for service: $1"
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME logs -f "$1"
    fi
}

# Function to install a model
install_model() {
    if [ -z "$1" ]; then
        print_error "Please specify a model name. Usage: $0 install <model_name>"
        exit 1
    fi
    
    print_status "Installing model: $1"
    
    # Check if Ollama is running
    if ! curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_error "Ollama is not running. Please start services first."
        exit 1
    fi
    
    # Install the model
    curl -X POST http://localhost:11434/api/pull -d "{\"name\": \"$1\"}"
    
    print_status "Model installation initiated. Check logs for progress."
}

# Function to list installed models
list_models() {
    print_status "Installed models:"
    
    if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        curl -s http://localhost:11434/api/tags | jq '.models[] | {name: .name, size: .size, modified: .modified_at}' 2>/dev/null || \
        curl -s http://localhost:11434/api/tags
    else
        print_error "Ollama is not running. Please start services first."
        exit 1
    fi
}

# Function to remove a model
remove_model() {
    if [ -z "$1" ]; then
        print_error "Please specify a model name. Usage: $0 remove <model_name>"
        exit 1
    fi
    
    print_status "Removing model: $1"
    
    # Check if Ollama is running
    if ! curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_error "Ollama is not running. Please start services first."
        exit 1
    fi
    
    # Remove the model
    curl -X DELETE http://localhost:11434/api/delete -d "{\"name\": \"$1\"}"
    
    print_status "Model removal initiated."
}

# Function to show resource usage
show_resources() {
    print_status "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Function to clean up
cleanup() {
    print_warning "This will remove all Ollama containers, volumes, and data. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_status "Cleaning up..."
        docker-compose -f $COMPOSE_FILE -p $PROJECT_NAME down -v --remove-orphans
        docker system prune -f
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to show help
show_help() {
    print_header
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [full]     Start Ollama services (use 'full' for monitoring stack)"
    echo "  stop             Stop all services"
    echo "  restart          Restart all services"
    echo "  status           Show service status and logs"
    echo "  logs [service]   Show logs (all services or specific service)"
    echo "  install <model>  Install a specific model"
    echo "  list             List installed models"
    echo "  remove <model>   Remove a specific model"
    echo "  resources        Show resource usage"
    echo "  cleanup          Remove all containers and volumes"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start full              # Start with monitoring"
    echo "  $0 install llama3.1:8b     # Install LLaMA 3.1 8B model"
    echo "  $0 logs ollama             # Show Ollama logs"
    echo "  $0 status                  # Show service status"
}

# Main script logic
main() {
    check_docker
    check_docker_compose
    
    case "${1:-help}" in
        start)
            create_directories
            start_services "$2"
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        install)
            install_model "$2"
            ;;
        list)
            list_models
            ;;
        remove)
            remove_model "$2"
            ;;
        resources)
            show_resources
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
