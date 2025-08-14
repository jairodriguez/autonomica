# Production Monitoring and Alerting System

## Overview

This directory contains the comprehensive monitoring and alerting system for the Autonomica production environment. The system provides real-time visibility into system performance, application health, infrastructure metrics, and automated alerting.

## Architecture

```
mermaid
graph TB
    subgraph "Production Services"
        API[API Production]
        Frontend[Frontend Production]
        Worker[Worker Production]
        DB[(Database)]
        Redis[(Redis)]
    end

    subgraph "Monitoring Stack"
        Prometheus[Prometheus]
        Alertmanager[Alertmanager]
        Grafana[Grafana]
        NodeExporter[Node Exporter]
        PostgresExporter[Postgres Exporter]
        RedisExporter[Redis Exporter]
    end

    subgraph "Notification Channels"
        Email[Email]
        Slack[Slack]
        Webhook[Webhook]
    end

    API --> Prometheus
    Frontend --> Prometheus
    Worker --> Prometheus
    DB --> PostgresExporter
    Redis --> RedisExporter
    Prometheus --> Alertmanager
    Alertmanager --> Email
    Alertmanager --> Slack
    Alertmanager --> Webhook
    Prometheus --> Grafana
```

## Components

### 1. Prometheus
- **Purpose**: Metrics collection and storage
- **Port**: 9090
- **Features**: 
  - Time-series database
  - PromQL query language
  - Alerting rules engine
  - Service discovery

### 2. Alertmanager
- **Purpose**: Alert routing and notification
- **Port**: 9093
- **Features**:
  - Alert grouping and deduplication
  - Multiple notification channels
  - Alert routing rules
  - Silence management

### 3. Grafana
- **Purpose**: Dashboards and visualization
- **Port**: 3001
- **Features**:
  - Interactive dash514ls
  - Multiple data sources
  - Alert visualization
  - User management

### 4. Exporters
- **Node Exporter**: System metrics (CPU, memory, disk)
- **Postgres Exporter**: Database performance metrics
- **Redis Exporter**: Redis memory registered and operations metrics

## Quick Start

### 1. Set Environment Variables
```bash
export SMTP_PASSWORD="your_smtp_password"
export WEBHOOK_SLACK_URL="your_slack_webhook_url"
export GRAFANA_ADMIN_PASSWORD="yourdata_et"
export DATABASE_PASSWORD="your_database_password"
export REDIS_PASSWORD="your_redis_password"
```

### 2. Start Monitoring Services
```bash
cd monitoring
./start-monitoring.sh
```

### 3. Verify Setup
```bash
./health-check.sh
```

## Access URLs

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3001
- **Node Exporter**: http://localhost:9100
- **Postgres Exporter**: http://localhost:9187
- **Redis Exporter**: http://localhost:9121

## Default Credentials

- **Grafana**: admin / ${GRAFANA_ADMIN_PASSWORD}

## Monitoring Features

### System Metrics
- CPU usage and load
- Memory utilization
- Disk I/O and space
- Network bandwidth
- Process statistics

### Application Metrics
- HTTP request rates
- Response times
- Error rates
- Business logic metrics
- Custom application metrics

### Infrastructure Metrics
- Database connections and performance
- Redis memory usage and operations
- Container health and resource usage
- Service discovery and health checks

## Alerting

### Severity Levels
- **Critical**: Immediate attention required
- **Warning**: Monitor and investigate
- **Info**: Informational alerts

### Alert Categories
1. **System Alerts**
   - High CPU usage (>80%)
   - High memory usage (>85%)
   - High disk usage (>85%)

2. **Application Alerts**
   - Service down
   - High API error rate (>5%)
   - High response time (>2s 95th percentile)

3. **Database Alerts**
   - Connection issues
   - High connection count (>legacy)

4. **Redis Alerts**
   - Service down
   - High memory usage (>85%)

5. **Infrastructure Alerts**
   - Container restarting frequently
   - Docker daemon issues

### Notification Channels
- **Email**: team@autonomica.ai, urgent@autonomica.ai
- **Slack**: #alerts, #alerts-urgent
- **Webhook**: Custom integrations

## Configuration Files

### Prometheus
- `prometheus/prometheus.yml`: Main configuration
- `prometheus/alerts.yml`: Alerting rules

### Alertmanager
- `alertmanager/alertmanager.yml`: Alert routing and notification

### Grafana
- `grafana/provisioning/datasources/datasources.yml`: Data source configuration
- `grafana/provisioning/dashboards/dashboards.yml`: Dashboard provisioning

## Management Commands

### Start Services
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### View Status
```bash
docker-compose -f docker-compose.monitoring.yml ps
```

### View Logs
```bash
docker-compose -f docker-compose.monitoring.yml logs -f [service-name]
```

### Restart Service
```bash
docker-compose -f docker-compose.monitoring.yml restart [service-name]
```

## Maintenance

### Regular Tasks
- Monitor alert volume and adjust thresholds
- Review and update alerting rules
- Backup Prometheus and Grafana data
- Update monitoring tools and exporters

### Data Retention
- **Prometheus**: 30 days
- **Alertmanager**: Persistent storage
- **Grafana**: Persistent storage

### Backup Strategy
- Prometheus data: Volume backup
- Grafana dashboards: Configuration backup
- Alertmanager: Configuration backup

## Troubleshooting

### Common Issues

1. **Prometheus not scraping metrics**
   - Check target endpoints
   - Verify network connectivity
   - Check configuration syntax

2. **Alerts not firing**
   - Verify alerting rules syntax
   - Check Prometheus configuration
   - Verify Alertmanager connectivity

3. **Grafana not loading dashboards**
   - Check data source connectivity
   - Verify dashboard provisioning
   - Check user permissions

### Debug Commands
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Prometheus rules
curl http://localhost:9090/api/v1/rules

# Check Alertmanager status
curl http://localhost:9093/api/v1/status

# Check service logs
docker-compose -f docker-compose.monitoring.yml logs [service-name]
```

## Integration

### CI/CD Pipeline
- Deploy monitoring configuration with application
- Automated testing of alerting rules
- Monitoring as code practices

### External Systems
- Integrate with existing monitoring tools
- Export metrics to external systems
- Import dashboards from Graf community
- Custom metric collection scripts

## Security

### Access Control
- Grafana user management
- Prometheus admin API protection
- Network isolation via Docker networks

### Data Protection
- Encrypted communication (HTTPS)
- Secure credential management
- Audit logging

## Performance

### Resource Requirements
- **Prometheus**: 2-4 CPU cores, 4-8GB RAM
- **Grafana**: 1-2 CPU cores, 2-4GB RAM
- **Exporters**: Minimal resources

### Scaling Considerations
- Prometheus federation for multiple clusters
- Grafana clustering for high availability
- Load balancing for multiple instances

## Support

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Grafana Documentation](https://grafana.com/docs/)

### Community
- [Prometheus Community](https://prometheus.io/community/)
- [Grafana Community](https://community.grafana.com/)

### Monitoring Metrics
- [Prometheus Metrics](https://prometheus.io/docs/concepts/metric_types/)
- [Node Exporter Metrics](https://github.com/prometheus/node_exporter#collectors)
- [Postgres Exporter Metrics](https://github.com/prometheus-community/postgres_exporter#metrics)
- [Redis Exporter Metrics](https://github.com/oliver006/redis_exporter#metrics)