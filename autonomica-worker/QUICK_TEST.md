# Quick Test Guide - Railway Deployment

## 🚀 Quick Start Testing

### 1. Local Testing (Recommended First Step)

```bash
cd autonomica-worker

# Start all services with Docker Compose
docker-compose up -d --build

# Wait for services to start (30-60 seconds)
sleep 60

# Run automated tests
./test_deployment.sh local

# View logs if needed
docker-compose logs -f

# Clean up when done
docker-compose down
```

### 2. Test Individual Services

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test task submission
curl -X POST http://localhost:8080/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "web_scraping",
    "payload": {"url": "https://httpbin.org/json"},
    "priority": "normal"
  }'

# View Flower dashboard
open http://localhost:5555
```

### 3. Railway Staging Test

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Deploy to staging
railway up --environment staging

# Test staging deployment
./test_deployment.sh staging
```

### 4. Performance Testing

```bash
# Install Artillery for load testing
npm install -g artillery

# Create simple load test
echo 'config:
  target: "http://localhost:8080"
  phases:
    - duration: 60
      arrivalRate: 5
scenarios:
  - flow:
      - get:
          url: "/health"' > quick-load-test.yml

# Run load test
artillery run quick-load-test.yml
```

## ✅ Expected Test Results

### Health Check Response
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "worker_name": "autonomica-worker",
  "redis_connected": true,
  "active_tasks": 0
}
```

### Task Submission Response
```json
{
  "task_id": "abc-123-def",
  "task_type": "web_scraping", 
  "status": "submitted",
  "message": "Task submitted successfully"
}
```

## 🔧 Quick Fixes for Common Issues

### Services Won't Start
```bash
# Check what's running on ports
lsof -i :8080 -i :5555 -i :6379

# Kill conflicting processes
pkill -f "port 8080"

# Rebuild everything
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Redis Connection Failed
```bash
# Check Redis status
docker-compose logs redis

# Test Redis directly
docker-compose exec redis redis-cli ping
```

### Celery Workers Not Processing
```bash
# Check Celery worker logs
docker-compose logs celery-worker

# Check active workers
docker-compose exec celery-worker celery -A worker.celery_app inspect active
```

## 🎯 Testing Priorities

1. **✅ Critical Tests** (Must Pass):
   - Health endpoint responds
   - Redis connection works
   - Services start without errors

2. **⚡ Important Tests** (Should Pass):
   - Task submission works
   - Celery workers process tasks
   - Flower dashboard accessible

3. **🚀 Performance Tests** (Nice to Have):
   - Load testing passes
   - Memory usage acceptable
   - Response times under 1s

## 📞 Get Help

If tests fail:
1. Check the full [Testing Guide](./TESTING_GUIDE.md)
2. Review [Railway Deployment Guide](./RAILWAY_DEPLOYMENT.md)
3. Check Docker logs: `docker-compose logs -f`
4. Verify environment variables are set correctly

---

**Quick Test Complete!** ✨ 