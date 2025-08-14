#!/bin/bash

# Start monitoring services
echo "Starting monitoring services..."

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service status
echo "Checking service status..."
docker-compose -f docker-compose.monitoring.yml ps

echo "Monitoring services started successfully!"
echo ""
echo "Access URLs:"
echo "  Prometheus: http://localhost:9090"
echo "  Alertmanager: http://localhost:9093"
echo "  Grafana: http://localhost:3001"
echo "  Node Exporter: http://localhost:9100"
echo "  Postgres Exporter: http://localhost:9187"
echo "  Redis Exporter: http://localhost:9121"