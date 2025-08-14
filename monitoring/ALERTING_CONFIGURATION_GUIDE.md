# Autonomica Alerting Configuration Guide

## Overview
This guide explains how to configure and manage the comprehensive alerting system for Autonomica, implementing **Subtask 8.3: Configure alert thresholds and notifications**.

## 🏗️ Alerting Architecture

The alerting system consists of three main components:

1. **Prometheus Alert Rules** - Define when alerts should fire
2. **Alertmanager** - Routes and manages alert notifications
3. **Notification Webhook Service** - Receives and processes alerts for testing

## 📊 Alert Categories

### 1. System Alerts (Infrastructure)
- **CPU Usage**: Warning at 80%, Critical at 95%
- **Memory Usage**: Warning at 85%, Critical at 95%
- **Disk Space**: Warning at 15%, Critical at 5%
- **Load Average**: Warning when above 80% of CPU cores
- **Network Traffic**: Warning above 1GB/s
- **Process Count**: Warning above 1000 processes

### 2. Application Alerts
- **API Response Time**: Warning above 2s, Critical above 5s
- **API Error Rate**: Warning above 5%, Critical above 20%
- **Request Rate**: Warning above 1000 req/s, Critical above 5000 req/s
- **Service Health**: Critical when service is down

### 3. Worker Alerts
- **Queue Backlog**: Warning above 100 tasks, Critical above 500
- **Error Rate**: Warning above 0.1 errors/s
- **Task Processing**: Warning when 95th percentile > 60s

### 4. Business Alerts
- **Active Agents**: Warning below 5, Critical at 0
- **Task Failure Rate**: Warning above 10%, Critical above 50%

## 🚨 Alert Severity Levels

### Warning (Yellow)
- **Duration**: 5-10 minutes before firing
- **Repeat Interval**: 1 hour
- **Action**: Monitor and investigate
- **Notification**: Email to devops team, Slack warning channel

### Critical (Red)
- **Duration**: 1-2 minutes before firing
- **Repeat Interval**: 15-30 minutes
- **Action**: Immediate investigation required
- **Notification**: Email to oncall team, Slack critical channel, PagerDuty

## 📧 Notification Channels

### 1. Email Notifications
```yaml
email_configs:
  - to: 'oncall@autonomica.local'
    send_resolved: true
    headers:
      subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
```

### 2. Slack Notifications
```yaml
slack_configs:
  - channel: '#alerts-critical'
    title: '🚨 Critical Alert: {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}\n{{ end }}'
    send_resolved: true
```

### 3. Webhook Notifications
```yaml
webhook_configs:
  - url: 'http://127.0.0.1:5001/critical'
    send_resolved: true
    http_config:
      basic_auth:
        username: 'alertmanager'
        password: 'secure_password'
```

## ⚙️ Configuration Files

### 1. Prometheus Alert Rules (`prometheus/rules/alerts.yml`)
Contains all alert definitions with thresholds and conditions.

### 2. Alertmanager Config (`alerts/alertmanager.yml`)
Defines notification routing, grouping, and channel configuration.

### 3. Notification Webhook (`scripts/notification_webhook.py`)
Receives and processes alerts for testing and development.

## 🔧 Alert Rule Configuration

### Basic Alert Structure
```yaml
- alert: AlertName
  expr: metric_expression > threshold
  for: duration
  labels:
    severity: warning|critical
    category: system|application|worker|business
    service: service_name
  annotations:
    summary: "Brief description"
    description: "Detailed description with {{ $value }}"
    dashboard: "Dashboard name"
    runbook: "Troubleshooting steps"
```

### Example: CPU Usage Alert
```yaml
- alert: HighCPUUsage
  expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
  for: 5m
  labels:
    severity: warning
    category: system
    service: infrastructure
  annotations:
    summary: "High CPU usage on {{ $labels.instance }}"
    description: "CPU usage is above 80% for more than 5 minutes. Current value: {{ $value }}%"
    dashboard: "System Overview"
    runbook: "Check for runaway processes, high load, or resource-intensive operations"
```

## 📋 Alert Routing Configuration

### Route Structure
```yaml
route:
  group_by: ['alertname', 'cluster', 'service', 'category']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      repeat_interval: 15m
      group_by: ['alertname', 'instance']
```

### Receiver Configuration
```yaml
receivers:
  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/critical'
        send_resolved: true
    slack_configs:
      - channel: '#alerts-critical'
        title: '🚨 Critical Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}\n{{ end }}'
        send_resolved: true
    email_configs:
      - to: 'oncall@autonomica.local'
        send_resolved: true
        headers:
          subject: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
```

## 🧪 Testing the Alerting System

### 1. Start the Notification Webhook Service
```bash
cd monitoring/scripts
./start_webhook.sh
```

### 2. Test Alert Generation
```bash
# Test the webhook service
curl -X POST http://localhost:5001/alerts/test

# Check current alerts
curl http://localhost:5001/alerts

# Check alert summary
curl http://localhost:5001/alerts/summary
```

### 3. Test Alert Rules
```bash
# Test Prometheus alert rules
curl http://localhost:9090/api/v1/rules

# Check alert status
curl http://localhost:9090/api/v1/alerts
```

### 4. Test Notification Channels
```bash
# Test webhook endpoint
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [{
      "labels": {"alertname": "TestAlert", "severity": "critical"},
      "annotations": {"summary": "Test", "description": "Test alert"},
      "status": "firing"
    }]
  }'
```

## 📈 Alert Thresholds Best Practices

### 1. Graduated Thresholds
- **Warning**: Early indication of potential issues
- **Critical**: Immediate action required
- **Use different durations**: Warning (5-10 min), Critical (1-2 min)

### 2. Business Impact Considerations
- **High Impact**: Lower thresholds, faster escalation
- **Low Impact**: Higher thresholds, slower escalation
- **Consider SLAs**: Align thresholds with service level agreements

### 3. Resource Utilization
- **CPU/Memory**: 80% warning, 95% critical
- **Disk Space**: 15% warning, 5% critical
- **Network**: Based on capacity and historical patterns

### 4. Application Performance
- **Response Time**: 95th percentile thresholds
- **Error Rate**: Percentage-based thresholds
- **Throughput**: Rate-based thresholds

## 🔒 Security Considerations

### 1. Authentication
```yaml
http_config:
  basic_auth:
    username: 'alertmanager'
    password: 'secure_password'
```

### 2. Network Security
- Use HTTPS for external webhooks
- Restrict webhook access to trusted sources
- Implement rate limiting

### 3. Sensitive Information
- Avoid including sensitive data in alert messages
- Use environment variables for credentials
- Log access to alert endpoints

## 📊 Monitoring the Alerting System

### 1. Alertmanager Metrics
- `alertmanager_alerts_received_total`
- `alertmanager_alerts_invalid_total`
- `alertmanager_notification_latency_seconds`

### 2. Alert Rule Evaluation
- `prometheus_rule_evaluation_duration_seconds`
- `prometheus_rule_evaluation_failures_total`
- `prometheus_rule_group_duration_seconds`

### 3. Notification Success Rates
- Monitor webhook response times
- Track email delivery success
- Monitor Slack API rate limits

## 🚀 Advanced Features

### 1. Alert Inhibition
```yaml
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance', 'service']
```

### 2. Alert Grouping
```yaml
route:
  group_by: ['alertname', 'cluster', 'service', 'category']
  group_wait: 10s
  group_interval: 10s
```

### 3. Time-based Routing
```yaml
routes:
  - match:
      severity: critical
    time_intervals:
      - name: business_hours
        time_intervals:
          - weekdays: ['monday:friday']
            times:
              - start_time: 09:00
                end_time: 17:00
    receiver: 'business-hours-critical'
```

## 🔍 Troubleshooting

### Common Issues

1. **Alerts Not Firing**
   - Check Prometheus rule evaluation
   - Verify metric expressions
   - Check alert rule syntax

2. **Notifications Not Sent**
   - Check Alertmanager configuration
   - Verify webhook endpoints
   - Check network connectivity

3. **Too Many Alerts**
   - Adjust thresholds
   - Implement alert grouping
   - Use inhibition rules

4. **Alert Fatigue**
   - Review alert importance
   - Implement proper escalation
   - Use runbooks for common issues

### Debug Commands
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check alert rules
curl http://localhost:9090/api/v1/rules

# Check Alertmanager status
curl http://localhost:9093/api/v1/status

# Test webhook connectivity
curl -X POST http://localhost:5001/alerts/test
```

## 📚 Next Steps

With the alerting system configured, you can:

1. **Customize Thresholds**: Adjust based on your infrastructure and requirements
2. **Add Notification Channels**: Integrate with PagerDuty, Teams, or other services
3. **Create Dashboards**: Build Grafana dashboards for alert visualization
4. **Implement Runbooks**: Create detailed troubleshooting guides for each alert
5. **Set Up Escalation**: Configure automatic escalation for critical alerts

## 📝 Status

**Subtask 8.3**: ✅ **COMPLETED** - Configure alert thresholds and notifications
- Comprehensive alert rules with proper thresholds
- Multi-channel notification system (Email, Slack, Webhook)
- Advanced routing and grouping configuration
- Testing and validation tools
- Complete documentation and best practices

**Overall Progress**: 3/4 subtasks completed for Task 8
- ✅ Subtask 8.1: Choose and install monitoring solution
- ✅ Subtask 8.2: Set up performance metrics collection
- ✅ Subtask 8.3: Configure alert thresholds and notifications
- ⏳ Subtask 8.4: Test monitoring and alerting system