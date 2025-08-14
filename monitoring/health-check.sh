#!/bin/bash

# Monitoring health check script

echo "Checking monitoring services health..."

# Check Prometheus
if curl -f http://localhost:9090/-/healthy &> /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not responding"
fi

# Check Alertmanager
if curl -f http://localhost:9093/-/healthy &> /dev/null; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager is not responding"
fi

# Check Grafana
if curl -f http://localhost:3001/api/health &> /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not responding"
fi

# Check Node Exporter
if curl -f http://localhost:9100/metrics &> /dev/null; then
    echo "✅ Node Exporter is healthy"
else
    echo "❌ Node Exporter is not responding"
fi

# Check Postgres Exporter
if curl -f http://localhost:9187/metrics &> /dev/null; then
    echo "✅ Postgres Exporter is healthy"
else
    echo "❌ Postgres Exporter is not responding"
fi

# Check Redis Exporter
if curl -f http://localhost:9121/metrics &> /dev/null; then
    echo "✅ Redis Exporter is healthy"
else
    echo "❌ Redis Exporter is not responding"
fi

echo ""
echo "Monitoring health check completed!"