# Autonomica Worker Metrics Configuration
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
