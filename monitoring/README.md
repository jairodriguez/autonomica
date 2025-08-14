# Autonomica Monitoring Stack

This directory contains the monitoring and alerting infrastructure for the Autonomica project, implementing **Task 8: Set up monitoring and alerting** from the CI/CD pipeline project.

## 🏗️ Architecture

The monitoring stack consists of three main components:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification management

## 📁 Directory Structure

```
monitoring/
├── docker-compose.yml          # Main orchestration file
├── start_monitoring.sh         # Startup script
├── stop_monitoring.sh          # Shutdown script
├── README.md                   # This file
├── prometheus/                 # Prometheus configuration
│   ├── prometheus.yml         # Main Prometheus config
│   └── rules/                 # Alerting rules
│       └── alerts.yml         # Alert definitions
├── grafana/                    # Grafana configuration
│   └── provisioning/          # Auto-provisioning configs
├── alerts/                     # Alertmanager configuration
│   └── alertmanager.yml       # Alert routing rules
└── scripts/                    # Utility scripts
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Ports 9090, 3001, and 9093 available

### Starting the Stack

```bash
cd monitoring
./start_monitoring.sh
```

### Stopping the Stack

```bash
cd monitoring
./stop_monitoring.sh
```

## 🌐 Access URLs

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `autonomica2024`
- **Alertmanager**: http://localhost:9093

## 📊 Metrics Collection

### System Metrics
- CPU usage, memory usage, disk space
- Network I/O and system load
- Container resource usage

### Application Metrics
- API response times and error rates
- Request throughput and queue sizes
- Service health and availability
- Database connection status

### Custom Metrics
- Worker queue backlog
- Task processing times
- Agent status and performance

## 🚨 Alerting Rules

### Warning Level Alerts
- High CPU usage (>80%)
- High memory usage (>85%)
- Low disk space (<15%)
- High API response time (>2s)
- High request rate (>1000 req/s)
- Worker queue backlog (>100 tasks)

### Critical Level Alerts
- Service down
- High API error rate (>5%)
- Database connection issues

## ⚙️ Configuration

### Prometheus Configuration
- Scrape interval: 15 seconds
- Evaluation interval: 15 seconds
- Data retention: 200 hours
- Targets: API, Worker, Frontend, System metrics

### Alertmanager Configuration
- Group wait: 10 seconds
- Group interval: 10 seconds
- Repeat interval: 1 hour (critical: 30 minutes)
- Receivers: Webhook, Email, Slack (configurable)

### Grafana Configuration
- Auto-provisioning enabled
- Default admin account
- Clock panel and Simple JSON datasource plugins

## 🔧 Customization

### Adding New Metrics
1. Expose metrics endpoint in your service
2. Add scrape configuration to `prometheus/prometheus.yml`
3. Create dashboards in Grafana

### Adding New Alerts
1. Define alert rules in `prometheus/rules/alerts.yml`
2. Configure notification channels in `alerts/alertmanager.yml`
3. Test alerts using Prometheus alert testing

### Adding New Data Sources
1. Configure datasource in Grafana
2. Update Prometheus scrape configs
3. Create relevant dashboards

## 🧪 Testing

### Test Alerts
```bash
# Test Prometheus connectivity
curl http://localhost:9090/-/healthy

# Test Grafana API
curl http://localhost:3001/api/health

# Test Alertmanager
curl http://localhost:9093/-/healthy
```

### Simulate High Load
```bash
# Generate load for testing alerts
ab -n 1000 -c 10 http://localhost:8000/api/health
```

## 📈 Dashboard Examples

### System Overview
- CPU, Memory, Disk usage trends
- Network I/O and system load
- Container resource utilization

### Application Performance
- API response time percentiles
- Request rate and error rates
- Service availability and health

### Business Metrics
- Task processing throughput
- Worker queue status
- Agent performance metrics

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 9090, 3001, 9093 are available
2. **Permission issues**: Ensure Docker has proper permissions
3. **Service startup failures**: Check logs with `docker-compose logs [service]`
4. **Metrics not showing**: Verify scrape targets are accessible

### Debug Commands

```bash
# View service logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f alertmanager

# Check container status
docker-compose ps

# Restart specific service
docker-compose restart prometheus

# View Prometheus targets
curl http://localhost:9090/api/v1/targets
```

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)

## 🎯 Next Steps

This monitoring stack provides the foundation for:
- Performance optimization
- Capacity planning
- Incident response
- SLA monitoring
- Business intelligence

## 📝 Status

**Subtask 8.1**: ✅ **DONE** - Choose and install monitoring solution (Grafana + Prometheus)
- Docker Compose configuration created
- Prometheus configuration with alerting rules
- Alertmanager configuration for notifications
- Startup and shutdown scripts
- Comprehensive documentation

**Next**: Subtask 8.2 - Set up performance metrics collection