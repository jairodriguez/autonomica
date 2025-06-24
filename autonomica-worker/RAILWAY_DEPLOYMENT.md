# Railway Deployment Guide for Autonomica Worker Pod

This guide provides step-by-step instructions for deploying the Autonomica Worker Pod to Railway.

## 🚂 Overview

The Autonomica Worker Pod consists of multiple services that work together:

- **`autonomica-worker`**: Main FastAPI service with health checks and task management
- **`autonomica-celery`**: Dedicated Celery workers for background processing
- **`autonomica-redis`**: Redis service for task queues and caching
- **`autonomica-flower`**: Celery task monitoring dashboard (optional)

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **Railway CLI**: Install with `npm install -g @railway/cli`
3. **GitHub Repository**: Your code should be in a GitHub repository
4. **API Keys**: Gather all required API keys (see Environment Variables section)

## 🛠️ Deployment Steps

### Step 1: Initialize Railway Project

```bash
# Navigate to your project directory
cd autonomica-worker

# Login to Railway
railway login

# Create a new Railway project
railway init

# Connect to GitHub repository
railway connect
```

### Step 2: Configure Environment Variables

Set up the following environment variables in the Railway dashboard:

#### **Required API Keys**
```bash
# OpenAI API for AI processing
OPENAI_API_KEY=your-openai-api-key

# Anthropic API for Claude integration
ANTHROPIC_API_KEY=your-anthropic-api-key

# Clerk authentication
CLERK_SECRET_KEY=your-clerk-secret-key
```

#### **Optional API Keys**
```bash
# SEMrush for SEO analysis
SEMRUSH_API_KEY=your-semrush-api-key

# Vercel KV for distributed caching
KV_REST_API_URL=your-vercel-kv-url
KV_REST_API_TOKEN=your-vercel-kv-token
```

#### **Automatic Variables**
These are automatically set by Railway based on `railway.toml`:
```bash
REDIS_URL=redis://autonomica-redis:6379/0
CELERY_BROKER_URL=redis://autonomica-redis:6379/1
CELERY_RESULT_BACKEND=redis://autonomica-redis:6379/1
```

### Step 3: Deploy Services

Deploy each service in the correct order:

```bash
# Deploy Redis first (dependency for other services)
railway up --service autonomica-redis

# Deploy the main worker service
railway up --service autonomica-worker

# Deploy Celery workers
railway up --service autonomica-celery

# Optional: Deploy Flower monitoring
railway up --service autonomica-flower
```

### Step 4: Verify Deployment

Check the health of your services:

```bash
# Check service status
railway status

# View logs
railway logs --service autonomica-worker

# Test health endpoint
curl https://your-worker-domain.railway.app/health
```

## 🔧 Configuration Details

### Multi-Service Architecture

The `railway.toml` file defines a multi-service deployment:

```toml
# Main worker service
[[services]]
name = "autonomica-worker"
# Handles HTTP requests and coordination

# Dedicated Celery workers
[[services]]
name = "autonomica-celery"
# Processes background tasks in parallel

# Redis service
[[services]]
name = "autonomica-redis"
# Provides task queue and caching

# Monitoring service
[[services]]
name = "autonomica-flower"
# Web UI for monitoring Celery tasks
```

### Autoscaling Configuration

Each service has optimized autoscaling:

```toml
[services.autoscaling]
enabled = true
minReplicas = 0      # Scale to zero when idle
maxReplicas = 5      # Scale up under load
scaleDownDelay = "5m" # Wait before scaling down
```

### Resource Allocation

Optimized resource allocation per service:

- **Worker Service**: 1.5GB RAM, 1 CPU core
- **Celery Service**: 2GB RAM, 1.5 CPU cores  
- **Redis Service**: 512MB RAM, 0.5 CPU core
- **Flower Service**: 256MB RAM, 0.25 CPU core

## 🔒 Security Configuration

### Environment Variables Security

Never commit sensitive data to your repository. Use Railway's environment variable management:

1. Go to your Railway project dashboard
2. Navigate to "Variables" tab
3. Add each required variable
4. Railway will automatically inject them into your containers

### Network Security

The configuration includes network security measures:

```toml
[networking]
allowPublicNetworking = true  # Only for external API access
```

Internal service communication is secured within Railway's private network.

## 📊 Monitoring and Logging

### Health Checks

Each service includes comprehensive health checks:

```toml
[services.healthcheck]
path = "/health"
interval = 30
timeout = 10
retries = 3
startPeriod = 60
```

### Logging Configuration

Structured logging is configured for production:

```python
LOG_LEVEL = "INFO"  # Production
LOG_LEVEL = "DEBUG" # Development
```

### Flower Monitoring

Access Celery task monitoring at:
```
https://your-flower-domain.railway.app
```

## 🔄 Deployment Strategies

### Rolling Deployments

The configuration uses rolling deployments for zero-downtime updates:

```toml
[deployment]
strategy = "rolling"
maxUnavailable = 1
maxSurge = 1
```

### Blue-Green Deployments

For critical updates, use Railway's blue-green deployment:

```bash
# Deploy to staging environment
railway up --environment staging

# Test staging deployment
railway run --environment staging pytest

# Promote to production
railway promote --environment staging
```

## 🐛 Troubleshooting

### Common Issues

1. **Service Won't Start**
   - Check environment variables are set
   - Verify Dockerfile builds successfully
   - Check Railway logs for errors

2. **Redis Connection Issues**
   - Ensure Redis service is running
   - Check `REDIS_URL` environment variable
   - Verify network connectivity

3. **Celery Tasks Not Processing**
   - Check Celery worker logs
   - Verify task queues are properly configured
   - Ensure Redis is accessible

### Debugging Commands

```bash
# View all services
railway service list

# Check specific service logs
railway logs --service autonomica-worker --follow

# Connect to service shell
railway shell --service autonomica-worker

# Check environment variables
railway variables --service autonomica-worker
```

## 📈 Performance Optimization

### Scaling Strategies

1. **Horizontal Scaling**: Increase `maxReplicas` for high-traffic periods
2. **Vertical Scaling**: Adjust `memory` and `cpu` resources
3. **Queue Optimization**: Use dedicated queues for different task types

### Resource Monitoring

Monitor resource usage in Railway dashboard:

- CPU utilization
- Memory usage
- Network traffic  
- Disk I/O

### Cost Optimization

- Use scale-to-zero for development environments
- Optimize resource allocation based on actual usage
- Implement efficient caching strategies

## 🔄 Continuous Deployment

### GitHub Actions Integration

Set up automated deployments with GitHub Actions:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        uses: railway-app/railway-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
          service: autonomica-worker
```

### Environment Promotion

Use Railway's environment system for staged deployments:

1. **Development**: Feature development and testing
2. **Staging**: Pre-production validation
3. **Production**: Live user traffic

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Celery Documentation](https://docs.celeryq.dev)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Redis Documentation](https://redis.io/docs)

## 🎯 Next Steps

After successful deployment:

1. Set up monitoring and alerting
2. Implement CI/CD pipeline
3. Configure backup strategies
4. Set up staging environments
5. Optimize performance based on metrics

---

**Need Help?** Check the Railway documentation or contact the development team. 