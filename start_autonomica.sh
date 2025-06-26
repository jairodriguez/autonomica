#!/bin/bash

# 🦉 Autonomica OWL System Deployment Script
# This script starts your complete multi-agent marketing platform

echo "🦉 Starting Autonomica Production System..."
echo "============================================"

# Check if required files exist
if [ ! -f "autonomica-api/main_api.py" ]; then
    echo "❌ Error: main_api.py not found!"
    exit 1
fi

if [ ! -d "autonomica-frontend" ]; then
    echo "❌ Error: autonomica-frontend directory not found!"
    exit 1
fi

# Start Backend (Production OWL API)
echo "🚀 Starting Production Backend API..."
cd autonomica-api
source venv/bin/activate
python main_api.py &
BACKEND_PID=$!
echo "✅ Production API started (PID: $BACKEND_PID) on http://localhost:8000"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Test backend health
echo "🔍 Testing backend health..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend healthy and ready!"
else
    echo "❌ Backend health check failed!"
    kill $BACKEND_PID
    exit 1
fi

# Start Frontend
echo "🌐 Starting Production Frontend..."
cd ../autonomica-frontend
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID) on http://localhost:3001"

echo ""
echo "🎉 Autonomica Production System Online!"
echo "======================================="
echo "🦉 Backend API: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3001"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 To test: ./test_autonomica.sh"
echo "🛑 To stop: Ctrl+C or kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Store PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user to stop
wait 