# Ollama Docker Integration for Autonomica

This document describes the comprehensive Docker integration for Ollama AI models in the Autonomica platform, providing enterprise-grade deployment, monitoring, and management capabilities.

## 🚀 Features

### Core Docker Features
- **Containerized Ollama Service**: Isolated, reproducible Ollama deployment
- **Volume Persistence**: Model storage persists across container restarts
- **Resource Constraints**: Configurable CPU and memory limits
- **Health Checks**: Automatic health monitoring and restart policies
- **Auto-restart**: Service reliability with automatic recovery

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Beautiful dashboards and visualization
- **Redis**: Caching and session management
- **Custom Metrics**: Ollama-specific performance indicators

### Management Tools
- **Management Script**: Easy command-line operations
- **API Integration**: Seamless integration with Autonomica API
- **Dashboard Access**: Web-based management interface

## 📁 File Structure

```
autonomica-api/
├── docker-compose.ollama.yml          # Main Docker Compose configuration
├── scripts/
│   └── ollama-docker.sh              # Management script
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml            # Prometheus configuration
│   └── grafana/
│       ├── provisioning/
│       │   └── datasources/
│       │       └── prometheus.yml    # Grafana datasource
│       └── dashboards/
│           └── ollama-dashboard.json # Ollama dashboard
├── ollama-models/                     # Persistent model storage
├── ollama-config/                     # Custom configurations
├── models/                           # Host-mounted models (read-only)
└── docs/
    └── OLLAMA_DOCKER_INTEGRATION.md  # This file
```

## 🐳 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM available
- 20GB+ disk space for models

### 1. Start Ollama Services

**Basic Ollama only:**
```bash
./scripts/ollama-docker.sh start
```

**Full monitoring stack:**
```bash
./scripts/ollama-docker.sh start full
```

### 2. Install Models

```bash
# Install LLaMA 3.1 8B
./scripts/ollama-docker.sh install llama3.1:8b

# Install Mixtral 8x7B
./scripts/ollama-docker.sh install mixtral:8x7b

# Install CodeLlama
./scripts/ollama-docker.sh install codellama:7b
```

### 3. Check Status

```bash
./scripts/ollama-docker.sh status
```

### 4. Access Services

- **Ollama API**: http://localhost:11434
- **Grafana Dashboard**: http://localhost:3001 (admin/autonomica2024)
- **Prometheus**: http://localhost:9091
- **Redis**: localhost:6380

## 🔧 Management Commands

### Service Management
```bash
# Start services
./scripts/ollama-docker.sh start [full]

# Stop services
./scripts/ollama-docker.sh stop

# Restart services
./scripts/ollama-docker.sh restart

# Show status
./scripts/ollama-docker.sh status
```

### Model Management
```bash
# Install a model
./scripts/ollama-docker.sh install <model_name>

# List installed models
./scripts/ollama-docker.sh list

# Remove a model
./scripts/ollama-docker.sh remove <model_name>
```

### Monitoring
```bash
# Show logs
./scripts/ollama-docker.sh logs [service_name]

# Show resource usage
./scripts/ollama-docker.sh resources

# Clean up everything
./scripts/ollama-docker.sh cleanup
```

## 📊 Monitoring & Metrics

### Prometheus Metrics
The integration exposes the following metrics:

- `ollama_requests_total`: Total API requests
- `ollama_response_time_sum`: Cumulative response time
- `ollama_response_time_count`: Request count for averaging
- `ollama_errors_total`: Total errors
- `ollama_memory_usage_bytes`: Memory usage
- `ollama_cpu_usage_seconds_total`: CPU usage
- `ollama_models_total`: Number of installed models

### Grafana Dashboard
The included dashboard provides:

- **Service Status**: Real-time health monitoring
- **Performance Metrics**: Response times and throughput
- **Resource Usage**: CPU, memory, and network
- **Model Statistics**: Counts and performance scores
- **Error Tracking**: Error rates and trends

## ⚙️ Configuration

### Resource Limits
Adjust resource constraints in `docker-compose.ollama.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 8G        # Maximum memory
      cpus: '4.0'       # Maximum CPU cores
    reservations:
      memory: 2G        # Guaranteed memory
      cpus: '1.0'       # Guaranteed CPU cores
```

### Volume Mounts
- `ollama_models`: Persistent model storage
- `ollama-config`: Custom Ollama configurations
- `models`: Host-mounted models for faster access

### Environment Variables
```yaml
environment:
  - OLLAMA_HOST=0.0.0.0          # Bind to all interfaces
  - OLLAMA_ORIGINS=*             # Allow all origins
  - OLLAMA_MODELS=/models        # Custom model path
```

## 🔒 Security Considerations

### Network Isolation
- Services run on isolated `autonomica-network`
- Custom subnet (172.20.0.0/16) for internal communication
- Port exposure limited to necessary services

### Access Control
- Grafana password: `autonomica2024`
- Redis accessible only within Docker network
- Prometheus metrics exposed internally

### Data Persistence
- Model data persists in named volumes
- Configurations stored in host directories
- Backup and restore procedures documented

## 🚨 Troubleshooting

### Common Issues

**1. Port Conflicts**
```bash
# Check what's using port 11434
lsof -i :11434

# Stop conflicting services
sudo systemctl stop ollama  # If running system-wide
```

**2. Insufficient Resources**
```bash
# Check available memory
free -h

# Check available disk space
df -h

# Adjust limits in docker-compose.ollama.yml
```

**3. Model Installation Failures**
```bash
# Check Ollama logs
./scripts/ollama-docker.sh logs ollama

# Verify network connectivity
curl -f http://localhost:11434/api/tags

# Restart services
./scripts/ollama-docker.sh restart
```

### Debug Commands
```bash
# Check container status
docker ps -a

# Inspect container logs
docker logs autonomica-ollama

# Check resource usage
docker stats

# Access container shell
docker exec -it autonomica-ollama /bin/bash
```

## 📈 Performance Optimization

### Model Loading
- Use host-mounted models for faster access
- Implement model preloading strategies
- Monitor memory usage during model switching

### Caching
- Redis integration for response caching
- Implement model output caching
- Use volume mounts for persistent storage

### Resource Tuning
- Adjust CPU limits based on workload
- Monitor memory usage patterns
- Implement auto-scaling policies

## 🔄 Integration with Autonomica

### API Endpoints
The Docker integration works seamlessly with existing Autonomica API endpoints:

- `/api/ai/ollama/models` - List models
- `/api/ai/ollama/install` - Install models
- `/api/ai/ollama/status` - Service status
- `/api/ai/ollama/health` - Health checks
- `/api/ai/ollama/metrics` - Performance metrics

### Dashboard Integration
Access the Ollama management dashboard at:
- `/ollama-dashboard` - Full-featured management interface

### Model Selection
The system automatically detects Docker-managed Ollama models and integrates them into the AI model selection system.

## 📚 Additional Resources

### Documentation
- [Ollama Official Docs](https://ollama.ai/docs)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Community
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Autonomica Community](https://github.com/autonomica)

### Support
For issues specific to this integration:
1. Check the troubleshooting section above
2. Review container logs
3. Verify Docker and Docker Compose versions
4. Check system resource availability

## 🎯 Next Steps

After setting up the Docker integration:

1. **Install Models**: Start with recommended models like `llama3.1:8b`
2. **Configure Monitoring**: Set up Grafana alerts and dashboards
3. **Optimize Performance**: Tune resource limits and caching
4. **Scale Up**: Add more Ollama instances for load balancing
5. **Backup Strategy**: Implement model and configuration backups

---

**Note**: This integration is designed for production use and includes enterprise-grade monitoring, security, and management features. For development or testing, you may use the basic Ollama service without the full monitoring stack.
