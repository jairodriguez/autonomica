# Autonomica Frontend Metrics Configuration
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
