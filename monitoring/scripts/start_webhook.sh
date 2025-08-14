#!/bin/bash

# Autonomica Notification Webhook Service Startup Script
# This script starts the notification webhook service for testing alerts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Autonomica Notification Webhook Service..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found. Installing..."
    pip3 install flask
fi

# Navigate to monitoring directory
cd "$MONITORING_DIR"

# Default configuration
PORT=${WEBHOOK_PORT:-5001}
HOST=${WEBHOOK_HOST:-"0.0.0.0"}

echo "📊 Configuration:"
echo "   Port: $PORT"
echo "   Host: $HOST"
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

# Start the webhook service
echo "🔧 Starting webhook service..."
python3 "$SCRIPT_DIR/notification_webhook.py" \
    --port "$PORT" \
    --host "$HOST"

echo "✅ Webhook service started successfully!"
echo "📊 Service available at: http://$HOST:$PORT"
echo "📋 To stop: Press Ctrl+C"