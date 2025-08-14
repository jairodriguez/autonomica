#!/bin/bash

# Autonomica Comprehensive Monitoring Test Suite
# This script runs comprehensive tests of the entire monitoring and alerting system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Autonomica Comprehensive Monitoring Test Suite..."
echo "📋 Subtask 8.4: Test monitoring and alerting system"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "⚠️  requests not found. Installing..."
    pip3 install requests
fi

# Navigate to monitoring directory
cd "$MONITORING_DIR"

echo "🔧 Configuration:"
echo "   Test Script: comprehensive_test.py"
echo "   Test Coverage: Full monitoring system validation"
echo "   Services: Prometheus, Grafana, Alertmanager, Metrics, Webhook"
echo ""

# Check if ports are available for testing
echo "🔍 Checking port availability..."
ports_to_check=(9090 3001 9093 8000 5001)
available_ports=()

for port in "${ports_to_check[@]}"; do
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        available_ports+=($port)
    else
        echo "⚠️  Port $port is in use"
    fi
done

if [ ${#available_ports[@]} -eq ${#ports_to_check[@]} ]; then
    echo "✅ All required ports are available"
else
    echo "⚠️  Some ports are in use. Tests may fail for those services."
fi

echo ""
echo "🧪 Starting comprehensive tests..."
echo "📊 This will test:"
echo "   - Docker availability and monitoring stack"
echo "   - Prometheus service functionality"
echo "   - Grafana service functionality"
echo "   - Alertmanager service functionality"
echo "   - System metrics collector"
echo "   - Notification webhook service"
echo "   - Alert integration and routing"
echo "   - Metrics ingestion and data flow"
echo "   - End-to-end monitoring workflow"
echo ""

# Run the comprehensive test suite
python3 "$SCRIPT_DIR/comprehensive_test.py"

echo ""
echo "🎯 Test suite completed!"
echo "📚 Check the output above for detailed results"
echo "🔧 Address any issues before proceeding to production"