# Monitoring and Alerting Guide

## Overview
This guide provides comprehensive information about the monitoring and alerting system implemented for the Autonomica project. The system provides real-time visibility into system health, performance, and business metrics with intelligent alerting and notification management.

## Architecture

### Monitoring Stack
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │    │   Infrastructure│    │   Business      │
│   (Frontend,    │    │   (Database,    │    │   Metrics       │
│   Backend,      │───▶│   Redis,        │───▶│   (User         │
│   Worker)       │    │   System)       │    │   Engagement)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Prometheus                                  │
│              (Metrics Collection)                              │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │  AlertManager   │    │   External      │
│ (Dashboards &   │    │ (Alert Routing) │    │   Services      │
│  Visualization) │    │                 │    │ (Sentry, etc.)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Notification Channels                        │
│              (Slack, Email, PagerDuty)                        │
└─────────────────────────────────────────────────────────────────┘
```

### Components
1. **Prometheus**: Metrics collection and storage
2. **AlertManager**: Alert routing and notification management
3. **Grafana**: Dashboard and visualization
4. **External Services**: Sentry (APM), New Relic, Datadog
5. **Notification Channels**: Slack, Email, PagerDuty

## Metrics Collection

### Application Metrics

#### Frontend (Next.js)
```typescript
// Core Web Vitals
export const coreWebVitals = {
  LCP: 'largest_contentful_paint',
  FID: 'first_input_delay',
  CLS: 'cumulative_layout_shift'
};

// Custom Business Metrics
export const businessMetrics = {
  userSatisfaction: 'user_satisfaction_score',
  featureUsage: 'feature_usage_count',
  conversionRate: 'conversion_rate'
};

// Performance Metrics
export const performanceMetrics = {
  pageLoadTime: 'page_load_time',
  apiResponseTime: 'api_response_time',
  errorRate: 'error_rate'
};
```

#### Backend (FastAPI)
```python
# Request Metrics
from prometheus_client import Counter, Histogram, Gauge

# HTTP request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Active connections gauge
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

# Custom business metrics
tasks_processed = Counter(
    'tasks_processed_total',
    'Total tasks processed',
    ['task_type', 'status']
)
```

#### Worker Service
```python
# Queue Metrics
queue_length = Gauge(
    'queue_length',
    'Current queue length',
    ['queue_name']
)

# Processing Metrics
task_processing_duration = Histogram(
    'task_processing_duration_seconds',
    'Task processing duration in seconds',
    ['task_type']
)

# Resource Usage
memory_usage_bytes = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

cpu_usage_percent = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)
```

### Infrastructure Metrics

#### Database (PostgreSQL)
```sql
-- Connection metrics
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Query performance
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Lock metrics
SELECT 
    locktype,
    mode,
    granted,
    pid
FROM pg_locks;
```

#### Redis Cache
```bash
# Memory usage
redis-cli info memory

# Hit rate
redis-cli info stats | grep keyspace

# Connection count
redis-cli info clients

# Command statistics
redis-cli info commandstats
```

#### System Metrics
```bash
# CPU usage
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}'

# Memory usage
free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2 }'

# Disk usage
df -h | awk '$NF=="/"{printf "%s", $5}'

# Network I/O
cat /proc/net/dev | grep eth0 | awk '{print $2, $10}'
```

## Alerting Rules

### Critical Alerts (Immediate Response)

#### Service Down
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 0m
  labels:
    severity: critical
    service: "{{ $labels.job }}"
  annotations:
    summary: "Service {{ $labels.job }} is down"
    description: "Service {{ $labels.job }} has been down for more than 0 minutes."
    runbook_url: "https://runbook.autonomica.app/service-down"
```

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 1m
  labels:
    severity: critical
    service: "{{ $labels.service }}"
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.service }}"
    runbook_url: "https://runbook.autonomica.app/high-error-rate"
```

#### Database Connection Failure
```yaml
- alert: DatabaseConnectionFailure
  expr: pg_up == 0
  for: 0m
  labels:
    severity: critical
    service: database
  annotations:
    summary: "Database connection failed"
    description: "Cannot connect to PostgreSQL database"
    runbook_url: "https://runbook.autonomica.app/database-connection-failure"
```

### High Priority Alerts (30-minute response)

#### Performance Degradation
```yaml
- alert: PerformanceDegradation
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: high
    service: "{{ $labels.service }}"
  annotations:
    summary: "Performance degradation detected"
    description: "95th percentile response time is {{ $value }}s for {{ $labels.service }}"
    runbook_url: "https://runbook.autonomica.app/performance-degradation"
```

#### High Memory Usage
```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.8
  for: 5m
  labels:
    severity: high
    service: system
  annotations:
    summary: "High memory usage detected"
    description: "Memory usage is {{ $value | humanizePercentage }}"
    runbook_url: "https://runbook.autonomica.app/high-memory-usage"
```

### Medium Priority Alerts (2-hour response)

#### Increased Error Rate
```yaml
- alert: IncreasedErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01
  for: 10m
  labels:
    severity: medium
    service: "{{ $labels.service }}"
  annotations:
    summary: "Increased error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.service }}"
    runbook_url: "https://runbook.autonomica.app/increased-error-rate"
```

#### Slow Queries
```yaml
- alert: SlowQueries
  expr: pg_stat_statements_mean_time_seconds > 1
  for: 5m
  labels:
    severity: medium
    service: database
  annotations:
    summary: "Slow database queries detected"
    description: "Average query time is {{ $value }}s"
    runbook_url: "https://runbook.autonomica.app/slow-queries"
```

## Dashboards

### Overview Dashboard
- **System Health**: Overall status of all services
- **Response Times**: API and frontend response times
- **Error Rates**: Error rates across all services
- **Throughput**: Requests per second for each service
- **Resource Usage**: CPU, memory, and disk usage

### Performance Dashboard
- **API Performance**: Response time percentiles (P50, P95, P99)
- **Database Performance**: Query times, connection counts, lock wait times
- **Cache Performance**: Hit rates, memory usage, connection counts
- **Resource Usage**: Detailed system resource metrics

### Business Dashboard
- **User Experience**: Core Web Vitals (LCP, FID, CLS)
- **Feature Usage**: Usage statistics for key features
- **User Engagement**: Daily active users, session duration, bounce rate
- **Business Metrics**: User satisfaction, conversion rates, cost per request

## Notification Management

### Alert Routing
1. **Critical Alerts**: PagerDuty (immediate), Slack (#alerts-critical)
2. **High Priority**: Slack (#alerts-high), Email (devops@)
3. **Medium Priority**: Slack (#alerts-medium), Email (devops@)
4. **Low Priority**: Slack (#alerts-low), Email (devops@)

### Escalation Policies
- **P1 (Critical)**: Immediate escalation to on-call engineer
- **P2 (High)**: Escalation within 30 minutes
- **P3 (Medium)**: Escalation within 2 hours
- **P4 (Low)**: Escalation within 24 hours

### Notification Channels

#### Slack
```yaml
# Critical alerts
- channel: '#alerts-critical'
  mentions: '@here'
  actions:
    - type: button
      text: 'View in Grafana'
      url: '{{ template "slack.autonomica.grafana" . }}'
    - type: button
      text: 'Acknowledge'
      url: '{{ template "slack.autonomica.acknowledge" . }}'
```

#### Email
```yaml
# Critical alerts
- to: 'oncall@autonomica.app'
  subject: '{{ template "email.autonomica.subject" . }}'
  html: '{{ template "email.autonomica.html" . }}'
  frequency: 'immediate'
```

#### PagerDuty
```yaml
# Critical alerts
- service_key: '${PAGERDUTY_CRITICAL_KEY}'
  description: '{{ template "pagerduty.autonomica.description" . }}'
  severity: '{{ if eq .GroupLabels.severity "critical" }}critical{{ else }}warning{{ end }}'
  class: '{{ .GroupLabels.service }}'
  group: 'autonomica'
```

## Maintenance and Operations

### Maintenance Windows
- **Weekly**: Sunday 2:00-4:00 AM UTC (alerts suppressed)
- **Monthly**: First Sunday 2:00-6:00 AM UTC (alerts suppressed)

### Alert Suppression
```yaml
# Suppress alerts during maintenance
time_intervals:
  - name: 'maintenance_window'
    time_intervals:
      - weekdays: ['sunday']
        times:
          - start_time: 02:00
            end_time: 04:00
        location: 'UTC'
```

### Runbook Integration
Each alert includes a runbook URL for troubleshooting:
- Service down procedures
- Performance degradation analysis
- Database connection troubleshooting
- Memory usage optimization
- Error rate investigation

## Custom Metrics

### Business Metrics
```python
# User satisfaction tracking
user_satisfaction_score = Gauge(
    'user_satisfaction_score',
    'User satisfaction score from feedback',
    ['service', 'feature', 'user_type']
)

# Business value tracking
business_value_delivered = Counter(
    'business_value_delivered',
    'Total business value delivered',
    ['service', 'feature', 'value_type']
)

# Cost tracking
cost_per_request = Gauge(
    'cost_per_request',
    'Cost per API request',
    ['service', 'endpoint', 'user_tier']
)
```

### Application-Specific Metrics
```python
# AI agent performance
agent_response_time = Histogram(
    'agent_response_time_seconds',
    'AI agent response time',
    ['agent_type', 'task_complexity']
)

agent_success_rate = Gauge(
    'agent_success_rate',
    'AI agent task success rate',
    ['agent_type', 'task_type']
)

# Project management metrics
project_completion_time = Histogram(
    'project_completion_time_hours',
    'Project completion time in hours',
    ['project_type', 'complexity']
)
```

## Troubleshooting

### Common Issues

#### 1. Metrics Not Collecting
```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Check service endpoints
curl http://api.autonomica.app/metrics
curl http://worker.autonomica.app/metrics

# Check Prometheus logs
docker logs prometheus
```

#### 2. Alerts Not Firing
```bash
# Check AlertManager status
curl http://alertmanager:9093/api/v1/status

# Check alert rules
curl http://prometheus:9090/api/v1/rules

# Check alert history
curl http://alertmanager:9093/api/v1/alerts
```

#### 3. Notifications Not Sending
```bash
# Check AlertManager logs
docker logs alertmanager

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test alert"}' \
  ${SLACK_WEBHOOK_URL}

# Check PagerDuty integration
curl -X POST -H 'Content-type: application/json' \
  --data '{"routing_key":"${PAGERDUTY_KEY}","event_action":"trigger","payload":{"summary":"Test alert"}}' \
  https://events.pagerduty.com/v2/enqueue
```

### Debugging Commands
```bash
# Check Prometheus targets
promtool check prometheus.yml

# Validate alert rules
promtool check rules alerts/*.yml

# Test alert queries
curl -G http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=up'

# Check metric values
curl -G http://prometheus:9090/api/v1/query_range \
  --data-urlencode 'query=rate(http_requests_total[5m])' \
  --data-urlencode 'start=2024-01-01T00:00:00Z' \
  --data-urlencode 'end=2024-01-01T23:59:59Z' \
  --data-urlencode 'step=1m'
```

## Best Practices

### 1. Metric Design
- Use descriptive names with consistent naming conventions
- Include relevant labels for filtering and grouping
- Avoid high cardinality labels
- Use appropriate metric types (Counter, Gauge, Histogram)

### 2. Alert Design
- Set appropriate thresholds based on SLOs/SLIs
- Use meaningful alert names and descriptions
- Include runbook URLs for troubleshooting
- Group related alerts to reduce noise

### 3. Dashboard Design
- Keep dashboards focused and uncluttered
- Use consistent color schemes and layouts
- Include context and annotations
- Optimize for different screen sizes

### 4. Notification Management
- Route alerts to appropriate teams
- Use escalation policies for critical issues
- Suppress alerts during maintenance windows
- Provide actionable information in notifications

## Future Enhancements

### Planned Improvements
1. **Machine Learning**: Anomaly detection for metrics
2. **Predictive Alerting**: Alert before issues occur
3. **Auto-remediation**: Automatic issue resolution
4. **Advanced Analytics**: Business intelligence integration
5. **Mobile Alerts**: Push notifications for critical issues

### Technology Upgrades
1. **Thanos**: Long-term metrics storage
2. **Cortex**: Multi-tenant metrics
3. **Loki**: Log aggregation
4. **Tempo**: Distributed tracing
5. **Mimir**: Metrics storage optimization

## Support and Resources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)

### Support Channels
- Platform support: Prometheus, Grafana, AlertManager
- External services: Sentry, New Relic, Datadog
- Internal support: DevOps team, Platform team
- Emergency contacts: On-call engineers

### Monitoring Tools
- Prometheus
- Grafana
- AlertManager
- External APM services
- Custom monitoring dashboards
