# Testing Guide for Autonomica Worker Pod

This guide provides comprehensive testing strategies to validate the Railway deployment configuration before going to production.

## 🧪 Testing Strategy Overview

We'll test the deployment using multiple approaches:

1. **Local Testing** - Docker Compose simulation
2. **Configuration Validation** - Railway.toml syntax check
3. **Railway Staging** - Deploy to staging environment
4. **Health Check Testing** - Validate endpoints
5. **End-to-End Testing** - Full workflow validation

## 🏠 Local Testing with Docker Compose

### Step 1: Prepare Environment

First, create a `.env` file for local testing:

```bash
# Navigate to worker directory
cd autonomica-worker

# Copy environment template
cp env.railway.template .env.test

# Edit the test environment file
# Add your actual API keys for testing
```

### Step 2: Local Docker Testing

Our Docker Compose setup mirrors the Railway configuration. Test locally:

```bash
# Build and start all services
docker-compose up --build

# Or start in background
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f worker
docker-compose logs -f celery-worker
docker-compose logs -f flower
docker-compose logs -f redis
```

### Step 3: Health Check Validation

Test each service's health endpoint:

```bash
# Main worker health check
curl http://localhost:8080/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2024-...",
#   "worker_name": "autonomica-worker",
#   "redis_connected": true,
#   "active_tasks": 0
# }

# Check Flower dashboard
open http://localhost:5555
# Login: admin / autonomica123

# Check Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG
```

### Step 4: Task Processing Test

Test background task processing:

```bash
# Submit a test task
curl -X POST http://localhost:8080/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "web_scraping",
    "payload": {
      "url": "https://httpbin.org/json",
      "method": "GET"
    },
    "priority": "normal"
  }'

# Check task status (use returned task_id)
curl http://localhost:8080/tasks/{task_id}/status

# Monitor in Flower dashboard
open http://localhost:5555
```

## ⚙️ Railway Configuration Validation

### Step 1: Install Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

### Step 2: Validate Configuration

```bash
# Validate railway.toml syntax
railway config validate

# Check environment variables
railway variables

# Validate service configuration
railway service list
```

### Step 3: Deploy to Staging

```bash
# Create staging environment
railway environment create staging

# Deploy to staging
railway up --environment staging

# Check deployment status
railway status --environment staging

# View logs
railway logs --environment staging --service autonomica-worker
```

## 🌐 Railway Staging Testing

### Step 1: Deploy Services in Order

```bash
# Deploy Redis first
railway up --service autonomica-redis --environment staging

# Deploy main worker
railway up --service autonomica-worker --environment staging

# Deploy Celery workers
railway up --service autonomica-celery --environment staging

# Deploy Flower monitoring
railway up --service autonomica-flower --environment staging
```

### Step 2: Configure Environment Variables

Set these in Railway dashboard for staging:

```bash
# Required for testing
OPENAI_API_KEY=your-test-key
ANTHROPIC_API_KEY=your-test-key
CLERK_SECRET_KEY=your-test-key

# Optional for full testing
SEMRUSH_API_KEY=your-test-key
```

### Step 3: Test Staging Deployment

```bash
# Get service URLs
railway service list --environment staging

# Test health endpoints
curl https://autonomica-worker-staging.railway.app/health

# Test Flower dashboard
open https://autonomica-flower-staging.railway.app

# Submit test task
curl -X POST https://autonomica-worker-staging.railway.app/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "ai_processing",
    "payload": {
      "prompt": "Hello, test message",
      "model": "gpt-3.5-turbo"
    }
  }'
```

## 🔍 Comprehensive Testing Script

Create an automated testing script:

```bash
# Create test script
cat > test_deployment.sh << 'EOF'
#!/bin/bash

echo "🧪 Starting Autonomica Worker Pod Testing..."

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    echo "Testing $name at $url"
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name - OK"
        return 0
    else
        echo "❌ $name - FAILED"
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
        echo "✅ $name - Valid JSON response"
        echo "$response" | jq .
        return 0
    else
        echo "❌ $name - Invalid JSON response"
        echo "Response: $response"
        return 1
    fi
}

# Set base URL (change for staging/production)
BASE_URL=${1:-"http://localhost:8080"}
FLOWER_URL=${2:-"http://localhost:5555"}

echo "Testing base URL: $BASE_URL"
echo "Testing Flower URL: $FLOWER_URL"

# Test health endpoints
test_json_endpoint "$BASE_URL/health" "Worker Health Check"

# Test task submission
echo "Testing task submission..."
task_response=$(curl -s -X POST "$BASE_URL/tasks/submit" \
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
    echo "✅ Task submission - OK"
    task_id=$(echo "$task_response" | jq -r '.task_id')
    echo "Task ID: $task_id"
    
    # Test task status
    sleep 2
    test_json_endpoint "$BASE_URL/tasks/$task_id/status" "Task Status Check"
else
    echo "❌ Task submission - FAILED"
    echo "Response: $task_response"
fi

# Test Flower dashboard
check_url "$FLOWER_URL" "Flower Dashboard"

echo "🏁 Testing complete!"
EOF

chmod +x test_deployment.sh
```

## 🔧 Performance Testing

### Load Testing with Artillery

```bash
# Install Artillery
npm install -g artillery

# Create load test configuration
cat > load-test.yml << 'EOF'
config:
  target: 'http://localhost:8080'
  phases:
    - duration: 60
      arrivalRate: 5
      name: "Warm up"
    - duration: 120
      arrivalRate: 10
      name: "Load test"
    - duration: 60
      arrivalRate: 20
      name: "Stress test"

scenarios:
  - name: "Health check"
    weight: 30
    flow:
      - get:
          url: "/health"
  
  - name: "Task submission"
    weight: 70
    flow:
      - post:
          url: "/tasks/submit"
          json:
            task_type: "web_scraping"
            payload:
              url: "https://httpbin.org/json"
              method: "GET"
            priority: "normal"
EOF

# Run load test
artillery run load-test.yml
```

### Memory and CPU Testing

```bash
# Monitor Docker containers
docker stats

# Check memory usage
docker-compose exec worker cat /proc/meminfo

# Check CPU usage
docker-compose exec worker top

# Check Redis memory
docker-compose exec redis redis-cli info memory
```

## 🔍 Monitoring and Debugging

### Real-time Monitoring

```bash
# Watch Docker logs in real-time
docker-compose logs -f

# Monitor specific service
docker-compose logs -f worker

# Monitor Celery tasks
docker-compose logs -f celery-worker

# Watch Railway logs
railway logs --follow --service autonomica-worker
```

### Debug Common Issues

```bash
# Check if services are running
docker-compose ps

# Check network connectivity
docker-compose exec worker ping redis

# Check Redis connectivity
docker-compose exec worker redis-cli -h redis ping

# Check Celery worker status
docker-compose exec celery-worker celery -A worker.celery_app inspect stats

# Check environment variables
docker-compose exec worker env | grep -E "(REDIS|CELERY|API)"
```

## 📊 Testing Checklist

### ✅ Local Testing Checklist

- [ ] Docker Compose builds successfully
- [ ] All services start without errors
- [ ] Health checks pass for all services
- [ ] Redis connection works
- [ ] Celery workers connect to Redis
- [ ] Tasks can be submitted and processed
- [ ] Flower dashboard is accessible
- [ ] Logs show no critical errors

### ✅ Railway Staging Checklist

- [ ] Railway.toml validates successfully
- [ ] All services deploy without errors
- [ ] Environment variables are set correctly
- [ ] Health endpoints respond correctly
- [ ] Services can communicate internally
- [ ] External API calls work (with valid keys)
- [ ] Autoscaling triggers work
- [ ] Monitoring dashboards are accessible

### ✅ Production Readiness Checklist

- [ ] All staging tests pass
- [ ] Performance tests show acceptable results
- [ ] Error handling works correctly
- [ ] Security configurations are proper
- [ ] Backup and recovery procedures tested
- [ ] Monitoring and alerting configured
- [ ] Documentation is complete
- [ ] Team is trained on deployment process

## 🚨 Troubleshooting Common Issues

### Service Won't Start

```bash
# Check logs for errors
docker-compose logs worker

# Check if ports are available
netstat -tulpn | grep :8080

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Redis Connection Issues

```bash
# Test Redis connectivity
docker-compose exec worker redis-cli -h redis ping

# Check Redis logs
docker-compose logs redis

# Verify Redis configuration
docker-compose exec redis cat /usr/local/etc/redis/redis.conf
```

### Celery Tasks Not Processing

```bash
# Check Celery worker status
docker-compose exec celery-worker celery -A worker.celery_app inspect active

# Check task queues
docker-compose exec celery-worker celery -A worker.celery_app inspect registered

# Monitor task execution
docker-compose logs -f celery-worker
```

## 🎯 Next Steps

After successful testing:

1. **Deploy to Production**: Use the same configuration for production deployment
2. **Set up Monitoring**: Configure alerts and dashboards
3. **Document Procedures**: Update deployment documentation
4. **Train Team**: Ensure team knows testing and deployment procedures
5. **Continuous Integration**: Set up automated testing in CI/CD pipeline

---

**Happy Testing!** 🚀 