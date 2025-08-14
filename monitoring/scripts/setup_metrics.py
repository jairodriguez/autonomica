#!/usr/bin/env python3
"""
Autonomica Metrics Setup Script
This script sets up Prometheus metrics collection for Autonomica services.

Implements Subtask 8.2: Set up performance metrics collection
"""

import os
import sys
from pathlib import Path

def create_metrics_config():
    """Create metrics configuration files for different services."""
    
    # API Service Metrics Configuration
    api_metrics = '''# Autonomica API Metrics Configuration
# This file configures Prometheus metrics collection for the API service

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request
from fastapi.responses import Response
import time

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
ACTIVE_AGENTS = Gauge(
    'autonomica_active_agents',
    'Number of currently active agents'
)

TASKS_PROCESSED = Counter(
    'autonomica_tasks_processed_total',
    'Total number of tasks processed',
    ['agent_type', 'status']
)

# Performance metrics
API_RESPONSE_TIME = Histogram(
    'api_response_time_seconds',
    'API response time in seconds',
    ['endpoint', 'method']
)

# Error metrics
ERROR_COUNT = Counter(
    'autonomica_errors_total',
    'Total number of errors',
    ['service', 'error_type']
)

# Database metrics
DB_CONNECTION_STATUS = Gauge(
    'db_connection_status',
    'Database connection status (1=connected, 0=disconnected)'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

def setup_metrics_middleware(app: FastAPI):
    """Setup FastAPI middleware for metrics collection."""
    
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response

def metrics_endpoint():
    """Return Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Custom metrics functions
def update_active_agents(count: int):
    """Update the active agents count."""
    ACTIVE_AGENTS.set(count)

def record_task_processed(agent_type: str, status: str):
    """Record a processed task."""
    TASKS_PROCESSED.labels(agent_type=agent_type, status=status).inc()

def record_error(service: str, error_type: str):
    """Record an error occurrence."""
    ERROR_COUNT.labels(service=service, error_type=error_type).inc()

def update_db_status(connected: bool):
    """Update database connection status."""
    DB_CONNECTION_STATUS.set(1 if connected else 0)

def record_db_query(query_type: str, duration: float):
    """Record database query duration."""
    DB_QUERY_DURATION.labels(query_type=query_type).observe(duration)
'''
    
    # Worker Service Metrics Configuration
    worker_metrics = '''# Autonomica Worker Metrics Configuration
# This file configures Prometheus metrics collection for the worker service

from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

# Queue metrics
QUEUE_SIZE = Gauge(
    'autonomica_worker_queue_size',
    'Current number of tasks in the worker queue'
)

QUEUE_PROCESSING_TIME = Histogram(
    'autonomica_worker_queue_processing_seconds',
    'Time spent processing tasks from queue',
    ['task_type']
)

# Task processing metrics
TASKS_STARTED = Counter(
    'autonomica_worker_tasks_started_total',
    'Total number of tasks started',
    ['agent_type', 'priority']
)

TASKS_COMPLETED = Counter(
    'autonomica_worker_tasks_completed_total',
    'Total number of tasks completed',
    ['agent_type', 'status']
)

TASK_DURATION = Histogram(
    'autonomica_worker_task_duration_seconds',
    'Task processing duration in seconds',
    ['agent_type', 'task_type']
)

# Resource usage metrics
WORKER_CPU_USAGE = Gauge(
    'autonomica_worker_cpu_usage_percent',
    'Current CPU usage percentage'
)

WORKER_MEMORY_USAGE = Gauge(
    'autonomica_worker_memory_usage_bytes',
    'Current memory usage in bytes'
)

WORKER_DISK_USAGE = Gauge(
    'autonomica_worker_disk_usage_bytes',
    'Current disk usage in bytes'
)

# Agent performance metrics
AGENT_ACTIVITY = Gauge(
    'autonomica_worker_agent_activity',
    'Agent activity status (1=active, 0=idle)',
    ['agent_id', 'agent_type']
)

AGENT_TASK_COUNT = Counter(
    'autonomica_worker_agent_task_count_total',
    'Total tasks processed by agent',
    ['agent_id', 'agent_type']
)

# Error metrics
WORKER_ERRORS = Counter(
    'autonomica_worker_errors_total',
    'Total number of worker errors',
    ['error_type', 'agent_type']
)

# Custom metrics functions
def update_queue_size(size: int):
    """Update the current queue size."""
    QUEUE_SIZE.set(size)

def record_task_started(agent_type: str, priority: str):
    """Record a task start."""
    TASKS_STARTED.labels(agent_type=agent_type, priority=priority).inc()

def record_task_completed(agent_type: str, status: str):
    """Record a task completion."""
    TASKS_COMPLETED.labels(agent_type=agent_type, status=status).inc()

def record_task_duration(agent_type: str, task_type: str, duration: float):
    """Record task processing duration."""
    TASK_DURATION.labels(agent_type=agent_type, task_type=task_type).observe(duration)

def update_worker_resources(cpu_percent: float, memory_bytes: int, disk_bytes: int):
    """Update worker resource usage metrics."""
    WORKER_CPU_USAGE.set(cpu_percent)
    WORKER_MEMORY_USAGE.set(memory_bytes)
    WORKER_DISK_USAGE.set(disk_bytes)

def update_agent_activity(agent_id: str, agent_type: str, active: bool):
    """Update agent activity status."""
    AGENT_ACTIVITY.labels(agent_id=agent_id, agent_type=agent_type).set(1 if active else 0)

def record_worker_error(error_type: str, agent_type: str):
    """Record a worker error."""
    WORKER_ERRORS.labels(error_type=error_type, agent_type=agent_type).inc()

def metrics_endpoint():
    """Return Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
'''
    
    # Frontend Metrics Configuration
    frontend_metrics = '''# Autonomica Frontend Metrics Configuration
# This file configures Prometheus metrics collection for the frontend

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

# Page load metrics
PAGE_LOAD_TIME = Histogram(
    'frontend_page_load_seconds',
    'Frontend page load time in seconds',
    ['page', 'route']
)

PAGE_VIEWS = Counter(
    'frontend_page_views_total',
    'Total number of page views',
    ['page', 'route']
)

# User interaction metrics
USER_ACTIONS = Counter(
    'frontend_user_actions_total',
    'Total number of user actions',
    ['action_type', 'component']
)

# API call metrics
API_CALLS = Counter(
    'frontend_api_calls_total',
    'Total number of API calls from frontend',
    ['endpoint', 'method', 'status']
)

API_CALL_DURATION = Histogram(
    'frontend_api_call_duration_seconds',
    'API call duration from frontend in seconds',
    ['endpoint', 'method']
)

# Error metrics
FRONTEND_ERRORS = Counter(
    'frontend_errors_total',
    'Total number of frontend errors',
    ['error_type', 'component']
)

# Performance metrics
JS_BUNDLE_SIZE = Gauge(
    'frontend_js_bundle_size_bytes',
    'JavaScript bundle size in bytes'
)

CSS_BUNDLE_SIZE = Gauge(
    'frontend_css_bundle_size_bytes',
    'CSS bundle size in bytes'
)

# Custom metrics functions
def record_page_load(page: str, route: str, duration: float):
    """Record page load time."""
    PAGE_LOAD_TIME.labels(page=page, route=route).observe(duration)

def record_page_view(page: str, route: str):
    """Record a page view."""
    PAGE_VIEWS.labels(page=page, route=route).inc()

def record_user_action(action_type: str, component: str):
    """Record a user action."""
    USER_ACTIONS.labels(action_type=action_type, component=component).inc()

def record_api_call(endpoint: str, method: str, status: int, duration: float):
    """Record an API call from frontend."""
    API_CALLS.labels(endpoint=endpoint, method=method, status=status).inc()
    API_CALL_DURATION.labels(endpoint=endpoint, method=method).observe(duration)

def record_frontend_error(error_type: str, component: str):
    """Record a frontend error."""
    FRONTEND_ERRORS.labels(error_type=error_type, component=component).inc()

def update_bundle_sizes(js_bytes: int, css_bytes: int):
    """Update bundle size metrics."""
    JS_BUNDLE_SIZE.set(js_bytes)
    CSS_BUNDLE_SIZE.set(css_bytes)

def metrics_endpoint():
    """Return Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
'''
    
    # Create the metrics directory structure
    metrics_dir = Path("metrics")
    metrics_dir.mkdir(exist_ok=True)
    
    # Write API metrics configuration
    with open(metrics_dir / "api_metrics.py", "w") as f:
        f.write(api_metrics)
    
    # Write Worker metrics configuration
    with open(metrics_dir / "worker_metrics.py", "w") as f:
        f.write(worker_metrics)
    
    # Write Frontend metrics configuration
    with open(metrics_dir / "frontend_metrics.py", "w") as f:
        f.write(frontend_metrics)
    
    print("✅ Metrics configuration files created successfully!")
    print(f"📁 Location: {metrics_dir.absolute()}")
    print("📋 Files created:")
    print("   - api_metrics.py")
    print("   - worker_metrics.py")
    print("   - frontend_metrics.py")

def create_requirements_file():
    """Create requirements.txt for metrics dependencies."""
    
    requirements = '''# Metrics collection dependencies
prometheus-client>=0.17.0
fastapi>=0.104.0
uvicorn>=0.24.0
psutil>=5.9.0
redis>=4.6.0
'''
    
    with open("metrics/requirements.txt", "w") as f:
        f.write(requirements)
    
    print("✅ Requirements file created: metrics/requirements.txt")

def create_integration_guide():
    """Create integration guide for implementing metrics."""
    
    guide = '''# Autonomica Metrics Integration Guide

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
'''
    
    with open("metrics/INTEGRATION_GUIDE.md", "w") as f:
        f.write(guide)
    
    print("✅ Integration guide created: metrics/INTEGRATION_GUIDE.md")

def main():
    """Main function to setup metrics collection."""
    print("🚀 Setting up Autonomica Metrics Collection...")
    print("📋 Subtask 8.2: Set up performance metrics collection")
    print()
    
    try:
        create_metrics_config()
        print()
        create_requirements_file()
        print()
        create_integration_guide()
        print()
        
        print("🎉 Metrics collection setup completed successfully!")
        print()
        print("📋 Next steps:")
        print("   1. Install dependencies: pip install -r metrics/requirements.txt")
        print("   2. Integrate metrics into your services")
        print("   3. Test metrics endpoints")
        print("   4. Verify Prometheus can scrape metrics")
        print()
        print("📚 See metrics/INTEGRATION_GUIDE.md for detailed instructions")
        
    except Exception as e:
        print(f"❌ Error setting up metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()