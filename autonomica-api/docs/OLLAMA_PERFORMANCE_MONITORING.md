# Ollama Performance Monitoring System

This document describes the comprehensive performance monitoring system for Ollama AI models in the Autonomica platform. The system provides real-time monitoring, alerting, and optimization recommendations for local AI model execution.

## 🚀 Features

### Core Monitoring Capabilities
- **Real-time Performance Tracking**: Monitor response times, token generation rates, and success rates
- **System Resource Monitoring**: Track CPU, memory, GPU, and disk utilization
- **GPU Detection & Monitoring**: Automatic detection and monitoring of CUDA-enabled GPUs
- **Model-specific Metrics**: Detailed performance data for individual Ollama models
- **Historical Data Storage**: Time-series data storage with configurable retention

### Advanced Analytics
- **Performance Scoring**: AI-powered performance scoring (0-10 scale) for models
- **Alert System**: Intelligent alerting for performance degradation and resource issues
- **Optimization Recommendations**: AI-generated suggestions for improving model performance
- **Trend Analysis**: Historical performance trends and patterns

### Data Management
- **Export Functionality**: Export metrics in JSON or CSV formats
- **Automatic Cleanup**: Configurable data retention and cleanup policies
- **Storage Optimization**: Efficient storage with configurable data limits
- **Backup & Recovery**: Data persistence across service restarts

## 🏗️ Architecture

### Core Components

```
autonomica-api/
├── app/ai/
│   ├── ollama_performance_monitor.py    # Main monitoring system
│   ├── performance_monitor.py           # Base performance monitor
│   └── providers/
│       └── ollama_model.py             # Enhanced Ollama integration
├── ollama-performance-dashboard.html    # Web dashboard
├── test_ollama_performance.py          # Test suite
└── docs/
    └── OLLAMA_PERFORMANCE_MONITORING.md # This documentation
```

### Data Flow

1. **Metrics Collection**: Ollama model requests automatically trigger metrics collection
2. **Real-time Processing**: Metrics are processed and analyzed in real-time
3. **Alert Generation**: Performance thresholds trigger intelligent alerts
4. **Data Storage**: Metrics are stored in time-series format with configurable retention
5. **API Exposure**: All data is accessible via RESTful API endpoints
6. **Dashboard Visualization**: Real-time charts and metrics display

## 📊 Metrics Collected

### Model Performance Metrics
- **Response Time**: Total time from request to completion
- **Token Generation**: Input/output token counts and rates
- **Ollama-specific Timing**: Load duration, eval duration, prompt processing time
- **Model Information**: Model size, context length, parameters
- **Error Tracking**: Failed requests and error messages

### System Resource Metrics
- **CPU Usage**: Current and historical CPU utilization
- **Memory Usage**: RAM usage and availability
- **GPU Utilization**: GPU usage percentage and memory consumption
- **Disk Usage**: Storage utilization and I/O metrics
- **Network I/O**: Network traffic and connection counts

### Derived Metrics
- **Performance Score**: AI-calculated performance rating (0-10)
- **Success Rate**: Percentage of successful requests
- **Tokens per Second**: Generation efficiency metric
- **Resource Efficiency**: Resource utilization per request

## 🔧 API Endpoints

### Performance Monitoring

#### Get Performance Summary
```http
GET /api/ai/ollama/performance/summary
```
Returns comprehensive performance overview including:
- Monitoring status and GPU availability
- Model performance summaries
- System health metrics
- Recent alerts and recommendations

#### Get Model Performance
```http
GET /api/ai/ollama/performance/metrics/{model_name}
```
Returns detailed performance data for a specific model:
- Request counts and success rates
- Average response times
- Performance scores
- Last usage timestamps

#### Get System Metrics
```http
GET /api/ai/ollama/performance/system?hours={hours}
```
Returns system resource metrics for specified time period:
- CPU, memory, GPU utilization
- Disk usage and network I/O
- Active connections and model counts

#### Get Performance Alerts
```http
GET /api/ai/ollama/performance/alerts?severity={level}&limit={count}
```
Returns performance alerts with filtering options:
- Alert type and severity
- Timestamps and messages
- Optimization recommendations
- Model-specific alerts

### Monitoring Control

#### Start Monitoring
```http
POST /api/ai/ollama/performance/monitoring/start
Content-Type: application/json

{
  "interval": 5.0
}
```

#### Stop Monitoring
```http
POST /api/ai/ollama/performance/monitoring/stop
```

#### Get Monitoring Status
```http
GET /api/ai/ollama/performance/status
```

### Data Management

#### Export Metrics
```http
POST /api/ai/ollama/performance/export
Content-Type: application/json

{
  "format": "json",
  "filepath": "optional_custom_path"
}
```

#### Cleanup Old Metrics
```http
POST /api/ai/ollama/performance/cleanup
Content-Type: application/json

{
  "days_to_keep": 30
}
```

## 🎯 Alert System

### Alert Types

#### Performance Alerts
- **Slow Response**: Response time exceeds threshold (configurable)
- **Model Load Issues**: Slow model loading times
- **Context Overflow**: Input exceeds model context window
- **Low Success Rate**: High failure rates

#### Resource Alerts
- **High Memory Usage**: System memory utilization above threshold
- **High CPU Usage**: CPU utilization approaching limits
- **High GPU Usage**: GPU memory or utilization issues
- **Disk Space**: Storage utilization warnings

### Alert Severity Levels
- **Low**: Informational alerts, no immediate action required
- **Medium**: Performance degradation, consider optimization
- **High**: Significant issues, immediate attention recommended
- **Critical**: System stability at risk, urgent action required

### Alert Configuration
```python
# Configurable thresholds in OllamaPerformanceMonitor
self.ollama_alert_thresholds = {
    "response_time_ms": 30000,        # 30 seconds
    "error_rate_percent": 10.0,       # 10% error rate
    "memory_usage_percent": 95.0,     # 95% memory usage
    "cpu_usage_percent": 98.0,        # 98% CPU usage
    "gpu_usage_percent": 95.0,        # 95% GPU usage
    "model_load_time_ms": 60000,      # 60 seconds to load model
    "context_length_utilization": 90.0,  # 90% of max context length
}
```

## 🎨 Dashboard

### Features
- **Real-time Charts**: Live updating performance visualizations
- **System Status**: Current resource utilization and health
- **Model Performance**: Individual model metrics and comparisons
- **Alert Management**: Real-time alert display and management
- **Export Controls**: Easy access to data export functionality

### Access
Navigate to `/ollama-performance-dashboard` in your browser to access the performance dashboard.

### Dashboard Sections
1. **Status Bar**: Overview of monitoring status and key metrics
2. **System Performance**: Real-time CPU, memory, and GPU charts
3. **Model Performance**: Response times and success rates by model
4. **Performance Alerts**: Active alerts with severity indicators
5. **Optimization Recommendations**: AI-generated improvement suggestions
6. **Historical Trends**: Performance patterns over time

## 🧪 Testing

### Test Suite
Run the comprehensive test suite to verify all functionality:

```bash
cd autonomica-api
python test_ollama_performance.py
```

### Test Coverage
- API endpoint functionality
- Metrics collection and storage
- Alert generation and management
- Export and cleanup operations
- Dashboard accessibility
- Monitoring start/stop operations

### Test Results
Test results are automatically saved to timestamped JSON files for analysis and debugging.

## ⚙️ Configuration

### Environment Variables
```bash
# Optional: Customize storage path
OLLAMA_PERFORMANCE_STORAGE_PATH=.taskmaster/ollama_performance_data

# Optional: Customize monitoring interval
OLLAMA_MONITORING_INTERVAL=5.0
```

### Storage Configuration
```python
# Default storage limits
self.ollama_metrics: deque(maxlen=50000)      # 50k Ollama metrics
self.system_metrics: deque(maxlen=10000)      # 10k system snapshots
self.performance_alerts: deque(maxlen=1000)   # 1k alerts
```

### GPU Detection
The system automatically detects GPU availability:
- NVIDIA GPU detection via `/proc/driver/nvidia`
- CUDA environment variable checking
- GPU process monitoring
- Fallback to CPU-only monitoring if no GPU detected

## 🚀 Getting Started

### 1. Start the API Server
```bash
cd autonomica-api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8000/ollama-performance-dashboard
```

### 3. Start Monitoring
Click "Start Monitoring" in the dashboard or use the API:
```bash
curl -X POST http://localhost:8000/api/ai/ollama/performance/monitoring/start \
  -H "Content-Type: application/json" \
  -d '{"interval": 5.0}'
```

### 4. Generate Metrics
Make some Ollama model requests to generate performance data:
```bash
curl http://localhost:8000/api/ai/ollama/health
```

### 5. View Performance Data
Access performance data via API or dashboard:
```bash
curl http://localhost:8000/api/ai/ollama/performance/summary
```

## 🔍 Troubleshooting

### Common Issues

#### No Metrics Being Collected
- Verify Ollama service is running
- Check API server logs for errors
- Ensure monitoring is started
- Verify Ollama health check endpoint

#### Dashboard Not Loading
- Check if dashboard file exists
- Verify API server is running
- Check browser console for JavaScript errors
- Ensure proper authentication if required

#### GPU Monitoring Not Working
- Verify NVIDIA drivers are installed
- Check if `nvidia-smi` command works
- Ensure CUDA environment is properly configured
- Check system logs for GPU-related errors

#### High Memory Usage
- Reduce metrics storage limits
- Increase cleanup frequency
- Monitor for memory leaks
- Consider using quantized models

### Debug Mode
Enable debug logging for detailed troubleshooting:
```python
import logging
logging.getLogger('ollama_performance_monitor').setLevel(logging.DEBUG)
```

### Performance Tuning
- Adjust monitoring intervals based on system resources
- Configure appropriate alert thresholds
- Set reasonable data retention periods
- Monitor storage usage and cleanup regularly

## 🔮 Future Enhancements

### Planned Features
- **Machine Learning Insights**: AI-powered performance prediction
- **Advanced Analytics**: Statistical analysis and trend detection
- **Integration APIs**: Third-party monitoring system integration
- **Custom Dashboards**: User-configurable dashboard layouts
- **Performance Benchmarking**: Model comparison and ranking

### Extensibility
The system is designed for easy extension:
- Add new metric types
- Implement custom alert rules
- Create specialized dashboards
- Integrate with external monitoring systems

## 📚 API Reference

### Data Models

#### OllamaModelMetrics
```python
@dataclass
class OllamaModelMetrics:
    model_name: str
    timestamp: datetime
    response_time_ms: float
    tokens_generated: int
    tokens_input: int
    eval_duration_ms: float
    load_duration_ms: float
    prompt_eval_duration_ms: float
    total_duration_ms: float
    memory_usage_mb: float
    gpu_utilization_percent: Optional[float]
    model_size_gb: Optional[float]
    context_length: Optional[int]
    temperature: Optional[float]
    top_p: Optional[float]
    error_occurred: bool
    error_message: Optional[str]
```

#### OllamaSystemMetrics
```python
@dataclass
class OllamaSystemMetrics:
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_gb: float
    gpu_usage_percent: Optional[float]
    gpu_memory_used_gb: Optional[float]
    gpu_memory_total_gb: Optional[float]
    disk_usage_percent: float
    network_io_mbps: float
    active_connections: int
    models_loaded: int
    total_models: int
```

#### OllamaPerformanceAlert
```python
@dataclass
class OllamaPerformanceAlert:
    timestamp: datetime
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    model_name: Optional[str]
    metric_value: Optional[float]
    threshold: Optional[float]
    recommendation: Optional[str]
```

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python test_ollama_performance.py`
4. Make changes and test thoroughly
5. Submit pull request with detailed description

### Code Style
- Follow PEP 8 guidelines
- Use type hints throughout
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check this documentation first
2. Review the troubleshooting section
3. Check GitHub issues for similar problems
4. Create a new issue with detailed information
5. Include logs and error messages

---

**Note**: This performance monitoring system is designed to work with Ollama models running locally. For cloud-based models, consider using the existing cloud provider monitoring capabilities.
