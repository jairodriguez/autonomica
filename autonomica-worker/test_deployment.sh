#!/bin/bash

echo "🧪 Starting Autonomica Worker Pod Testing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✅ $message - OK${NC}"
    elif [ "$status" = "FAILED" ]; then
        echo -e "${RED}❌ $message - FAILED${NC}"
    else
        echo -e "${YELLOW}ℹ️  $message${NC}"
    fi
}

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    echo "Testing $name at $url"
    
    if curl -f -s "$url" > /dev/null; then
        print_status "OK" "$name"
        return 0
    else
        print_status "FAILED" "$name"
        return 1
    fi
}

# Function to test JSON endpoint
test_json_endpoint() {
    local url=$1
    local name=$2
    echo "Testing JSON endpoint $name at $url"
    
    response=$(curl -s "$url")
    if echo "$response" | jq . > /dev/null 2>&1; then
        print_status "OK" "$name - Valid JSON response"
        echo "$response" | jq .
        return 0
    else
        print_status "FAILED" "$name - Invalid JSON response"
        echo "Response: $response"
        return 1
    fi
}

# Function to test task submission and processing
test_task_workflow() {
    local base_url=$1
    echo ""
    echo "🔄 Testing complete task workflow..."
    
    # Submit test task
    task_response=$(curl -s -X POST "$base_url/tasks/submit" \
      -H "Content-Type: application/json" \
      -d '{
        "task_type": "web_scraping",
        "payload": {
          "url": "https://httpbin.org/json",
          "method": "GET"
        },
        "priority": "normal"
      }')

    if echo "$task_response" | jq . > /dev/null 2>&1; then
        print_status "OK" "Task submission"
        task_id=$(echo "$task_response" | jq -r '.task_id')
        echo "Task ID: $task_id"
        
        # Wait for task to process
        echo "Waiting for task to process..."
        sleep 5
        
        # Check task status
        status_response=$(curl -s "$base_url/tasks/$task_id/status")
        if echo "$status_response" | jq . > /dev/null 2>&1; then
            print_status "OK" "Task status check"
            echo "Task Status Response:"
            echo "$status_response" | jq .
            
            # Check if task completed
            task_status=$(echo "$status_response" | jq -r '.status')
            if [ "$task_status" = "SUCCESS" ]; then
                print_status "OK" "Task completed successfully"
            elif [ "$task_status" = "PENDING" ]; then
                print_status "INFO" "Task is still processing"
            else
                print_status "FAILED" "Task failed or has unexpected status: $task_status"
            fi
        else
            print_status "FAILED" "Task status check - Invalid response"
            echo "Response: $status_response"
        fi
    else
        print_status "FAILED" "Task submission"
        echo "Response: $task_response"
        return 1
    fi
}

# Parse command line arguments
ENVIRONMENT=${1:-"local"}
BASE_URL=""
FLOWER_URL=""

case $ENVIRONMENT in
    "local")
        BASE_URL="http://localhost:8080"
        FLOWER_URL="http://localhost:5555"
        ;;
    "staging")
        BASE_URL="https://autonomica-worker-staging.railway.app"
        FLOWER_URL="https://autonomica-flower-staging.railway.app"
        ;;
    "production")
        BASE_URL="https://autonomica-worker.railway.app"
        FLOWER_URL="https://autonomica-flower.railway.app"
        ;;
    *)
        # Custom URLs provided
        BASE_URL=$1
        FLOWER_URL=$2
        ;;
esac

echo "🎯 Testing Environment: $ENVIRONMENT"
echo "🔗 Worker URL: $BASE_URL"
echo "🌸 Flower URL: $FLOWER_URL"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ jq is not installed. Please install jq to run this test."
    echo "On macOS: brew install jq"
    echo "On Ubuntu: sudo apt-get install jq"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "❌ curl is not installed. Please install curl to run this test."
    exit 1
fi

# Start testing
echo "🚀 Beginning health checks..."

# Test main worker health endpoint
test_json_endpoint "$BASE_URL/health" "Worker Health Check"

# Test Flower dashboard availability
check_url "$FLOWER_URL" "Flower Dashboard"

# Test task workflow
test_task_workflow "$BASE_URL"

# Additional endpoint tests
echo ""
echo "🔍 Testing additional endpoints..."

# Test root endpoint (if it exists)
check_url "$BASE_URL/" "Root Endpoint"

# Test docs endpoint (FastAPI auto-docs)
check_url "$BASE_URL/docs" "API Documentation"

# Test metrics endpoint (if it exists)
check_url "$BASE_URL/metrics" "Metrics Endpoint"

# Environment-specific tests
if [ "$ENVIRONMENT" = "local" ]; then
    echo ""
    echo "🐳 Local Docker Testing..."
    
    # Check if Docker Compose is running
    if command -v docker-compose &> /dev/null; then
        echo "Checking Docker Compose services..."
        docker-compose ps
        
        # Check Redis connectivity
        echo "Testing Redis connectivity..."
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_status "OK" "Redis connectivity"
        else
            print_status "FAILED" "Redis connectivity"
        fi
        
        # Check Celery worker status
        echo "Testing Celery worker status..."
        if docker-compose exec -T celery-worker celery -A worker.celery_app inspect ping > /dev/null 2>&1; then
            print_status "OK" "Celery worker connectivity"
        else
            print_status "FAILED" "Celery worker connectivity"
        fi
    else
        echo "Docker Compose not available - skipping container tests"
    fi
fi

# Performance test (basic)
echo ""
echo "⚡ Running basic performance test..."
echo "Making 10 concurrent requests to health endpoint..."

# Simple concurrent test
for i in {1..10}; do
    curl -s "$BASE_URL/health" > /dev/null &
done
wait

print_status "OK" "Concurrent requests test completed"

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="
echo "Environment: $ENVIRONMENT"
echo "Worker URL: $BASE_URL"
echo "Flower URL: $FLOWER_URL"
echo ""
echo "🏁 Testing complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Check logs if any tests failed"
echo "   2. Verify environment variables are set correctly"
echo "   3. Monitor the Flower dashboard for task processing"
echo "   4. Run load tests if basic tests pass"
echo ""
echo "🔧 Troubleshooting:"
echo "   - For local testing: docker-compose logs -f"
echo "   - For Railway: railway logs --follow"
echo "   - Check API keys are set correctly"
echo "   - Verify network connectivity" 