# Autonomica Metrics Integration Guide

## Overview
This guide explains how to integrate Prometheus metrics into your Autonomica services.

## Quick Integration

### 1. API Service (FastAPI)

```python
from fastapi import FastAPI
from metrics.api_metrics import setup_metrics_middleware, metrics_endpoint

app = FastAPI()

# Setup metrics middleware
setup_metrics_middleware(app)

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint)

# Use custom metrics in your code
from metrics.api_metrics import update_active_agents, record_task_processed

@app.get("/agents")
async def get_agents():
    agents = await fetch_agents()
    update_active_agents(len(agents))
    return agents

@app.post("/tasks")
async def create_task(task: Task):
    try:
        result = await process_task(task)
        record_task_processed(task.agent_type, "success")
        return result
    except Exception as e:
        record_task_processed(task.agent_type, "error")
        raise
```

### 2. Worker Service

```python
from metrics.worker_metrics import (
    update_queue_size, record_task_started, 
    record_task_completed, update_worker_resources
)

# Update queue size
update_queue_size(len(task_queue))

# Record task processing
record_task_started(task.agent_type, task.priority)

# Update resource usage
import psutil
cpu_percent = psutil.cpu_percent()
memory_bytes = psutil.virtual_memory().used
disk_bytes = psutil.disk_usage('/').used
update_worker_resources(cpu_percent, memory_bytes, disk_bytes)
```

### 3. Frontend (Next.js)

```typescript
// metrics.ts
export const recordPageLoad = (page: string, route: string, duration: number) => {
  fetch('/api/metrics/page-load', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ page, route, duration })
  });
};

export const recordUserAction = (actionType: string, component: string) => {
  fetch('/api/metrics/user-action', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actionType, component })
  });
};

// Usage in components
useEffect(() => {
  const startTime = performance.now();
  
  return () => {
    const duration = performance.now() - startTime;
    recordPageLoad('dashboard', '/dashboard', duration / 1000);
  };
}, []);
```

## Metrics Endpoints

All services should expose a `/metrics` endpoint that returns Prometheus-formatted metrics.

## Testing Metrics

1. Start your service
2. Visit `/metrics` endpoint
3. Verify metrics are being collected
4. Check Prometheus targets are healthy

## Best Practices

1. **Naming**: Use descriptive metric names with consistent prefixes
2. **Labels**: Use labels sparingly to avoid cardinality issues
3. **Documentation**: Document all custom metrics
4. **Testing**: Test metrics collection in development
5. **Monitoring**: Monitor metrics collection itself

## Troubleshooting

- Check `/metrics` endpoint returns data
- Verify Prometheus can scrape your service
- Check service logs for metric errors
- Ensure ports are accessible
