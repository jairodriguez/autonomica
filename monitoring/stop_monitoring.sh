#!/bin/bash

# Autonomica Monitoring Stack Stop Script
# This script stops the monitoring stack and cleans up resources

set -e

echo "🛑 Stopping Autonomica Monitoring Stack..."

# Navigate to monitoring directory
cd "$(dirname "$0")"

# Stop and remove containers
echo "🔧 Stopping monitoring services..."
docker-compose down --remove-orphans

# Remove volumes (optional - uncomment if you want to clear all data)
# echo "🗑️  Removing monitoring data volumes..."
# docker-compose down -v

echo "✅ Monitoring stack stopped successfully!"
echo ""
echo "📋 To start again, run: ./start_monitoring.sh"
echo "📋 To view logs: docker-compose logs [service]"