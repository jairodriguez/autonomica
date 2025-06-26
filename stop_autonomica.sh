#!/bin/bash

echo "🛑 Stopping Autonomica Production System..."

# Kill processes by PID if available
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🛑 Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
    fi
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🛑 Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
    fi
    rm .frontend.pid
fi

# Clean up any remaining processes
echo "🧹 Cleaning up any remaining processes..."
pkill -f "main_api.py" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
lsof -ti:3001,8000 | xargs kill -9 2>/dev/null || true

echo "✅ Autonomica Production System stopped!" 