# Autonomica API Metrics Configuration
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
