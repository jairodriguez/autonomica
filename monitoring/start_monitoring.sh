#!/bin/bash

# Autonomica Monitoring Stack Startup Script
# This script starts the monitoring stack (Prometheus, Grafana, Alertmanager)

set -e

echo "🚀 Starting Autonomica Monitoring Stack..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to monitoring directory
cd "$(dirname "$0")"

# Stop any existing containers
echo "🛑 Stopping existing monitoring containers..."
docker-compose down --remove-orphans

# Start the monitoring stack
echo "🔧 Starting monitoring services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Checking service status..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is running on http://localhost:9090"
else
    echo "❌ Prometheus failed to start"
    docker-compose logs prometheus
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo "✅ Grafana is running on http://localhost:3001"
    echo "   Username: admin"
    echo "   Password: autonomica2024"
else
    echo "❌ Grafana failed to start"
    docker-compose logs grafana
fi

# Check Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager is running on http://localhost:9093"
else
    echo "❌ Alertmanager failed to start"
    docker-compose logs alertmanager
fi

echo ""
echo "🎉 Monitoring stack is ready!"
echo ""
echo "📱 Access URLs:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana:    http://localhost:3001 (admin/autonomica2024)"
echo "   Alertmanager: http://localhost:9093"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop stack: docker-compose down"
echo "   Restart:   docker-compose restart"
echo ""

# Show running containers
echo "🐳 Running containers:"
docker-compose ps