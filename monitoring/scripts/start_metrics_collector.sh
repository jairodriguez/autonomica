#!/bin/bash

# Autonomica System Metrics Collector Startup Script
# This script starts the system metrics collector service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"
METRICS_DIR="$MONITORING_DIR/metrics"

echo "🚀 Starting Autonomica System Metrics Collector..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import prometheus_client" 2>/dev/null; then
    echo "⚠️  prometheus_client not found. Installing dependencies..."
    if [ -f "$METRICS_DIR/requirements.txt" ]; then
        pip3 install -r "$METRICS_DIR/requirements.txt"
    else
        pip3 install prometheus_client psutil
    fi
fi

# Check if psutil is available
if ! python3 -c "import psutil" 2>/dev/null; then
    echo "⚠️  psutil not found. Installing..."
    pip3 install psutil
fi

# Navigate to monitoring directory
cd "$MONITORING_DIR"

# Default configuration
PORT=${METRICS_PORT:-8000}
HOST=${METRICS_HOST:-"0.0.0.0"}
INTERVAL=${METRICS_INTERVAL:-15}

echo "📊 Configuration:"
echo "   Port: $PORT"
echo "   Host: $HOST"
echo "   Collection Interval: ${INTERVAL}s"
echo ""

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use. Using next available port..."
    # Find next available port
    for ((p=PORT+1; p<PORT+10; p++)); do
        if ! lsof -Pi :$p -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT=$p
            echo "✅ Using port $PORT instead"
            break
        fi
    done
fi

# Start the metrics collector
echo "🔧 Starting metrics collector..."
python3 "$SCRIPT_DIR/system_metrics_collector.py" \
    --port "$PORT" \
    --host "$HOST" \
    --interval "$INTERVAL"

echo "✅ Metrics collector started successfully!"
echo "📊 Metrics available at: http://$HOST:$PORT/metrics"
echo "📋 To stop: Press Ctrl+C"