# Analytics and Reporting System

## Overview

The Analytics and Reporting System is a comprehensive solution for collecting, processing, analyzing, and visualizing data from multiple sources. It provides real-time KPI dashboards, automated report generation, and robust privacy compliance features.

## Architecture

The system is built with a modular, service-oriented architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Service                        │
│                 (Main Orchestrator)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Data     │ │    KPI      │ │ Dashboard  │          │
│  │ Collection │ │Calculation  │ │  Service   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Report   │ │  Report    │ │   Auth     │          │
│  │Generation  │ │Scheduling  │ │  Service   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐                          │
│  │   Data     │ │   Vercel   │                          │
│  │  Privacy   │ │     KV     │                          │
│  │  Service   │ │  Service   │                          │
│  └─────────────┘ └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Core Services

### 1. AnalyticsDataCollector
Collects data from various sources:
- Google Search Console API
- Social Media APIs (Twitter, Facebook, LinkedIn, Instagram)
- SEMrush API
- Internal analytics data
- Token usage tracking
- Time savings calculations

**Features:**
- Rate limiting and error handling
- Configurable collection frequencies
- Job management and monitoring
- Data validation and cleaning

### 2. KPICalculationService
Transforms raw data into actionable insights:

**Basic KPIs:**
- Growth metrics (impressions, clicks, engagement)
- Performance indicators
- Conversion rates
- ROI calculations
- Time savings metrics

**Advanced KPIs:**
- Velocity and momentum analysis
- Volatility and seasonality detection
- Forecasting with confidence intervals
- Trend strength analysis

**Business Intelligence:**
- Performance scoring
- Alert system
- Recommendation engine
- Opportunity identification
- Risk assessment

### 3. KPIDashboardService
Provides interactive visualizations:

**Default Dashboards:**
- Overview: High-level metrics and trends
- Performance: Detailed performance analysis
- Growth: Growth metrics and forecasts

**Widget Types:**
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distributions
- Gauge charts for targets
- Metric cards for key numbers

**Features:**
- Real-time data updates
- Customizable layouts
- Interactive filtering
- Export capabilities

### 4. ReportGenerationService
Creates comprehensive reports:

**Report Types:**
- Daily overview
- Weekly performance
- Monthly analytics
- Custom reports

**Export Formats:**
- JSON
- CSV
- PDF (placeholder)
- HTML
- Excel

**Features:**
- Template-based generation
- Customizable sections
- Automated insights
- Multi-format export

### 5. ReportSchedulerService
Automates report delivery:

**Scheduling:**
- Cron-based scheduling
- Timezone support
- Multiple delivery methods

**Delivery Methods:**
- Email (placeholder)
- Webhook (placeholder)
- Storage
- API

**Features:**
- Automatic execution
- Delivery tracking
- Error handling
- Retry mechanisms

### 6. AnalyticsAuthService
Manages access control:

**User Roles:**
- Viewer: Basic access to dashboards and reports
- Analyst: Export capabilities
- Manager: Report scheduling
- Admin: Full system access
- Owner: User management

**Access Levels:**
- Own: User's data only
- Team: Team member data
- Organization: Organization-wide data
- All: System-wide data

**Features:**
- Role-based permissions
- API token management
- Audit logging
- Multi-tenant isolation

### 7. DataPrivacyService
Ensures GDPR compliance:

**Data Rights:**
- Access: View personal data
- Rectification: Correct inaccurate data
- Erasure: Right to be forgotten
- Portability: Data export
- Restriction: Limit processing
- Objection: Object to processing

**Features:**
- Consent management
- Data retention policies
- Automated cleanup
- Audit trails
- Legal basis tracking

### 8. VercelKVService
Provides data storage:

**Features:**
- Redis-compatible storage
- Multi-tenant namespacing
- Configurable retention
- Automatic fallback to Redis
- Health monitoring

## API Endpoints

### Data Collection
```
POST /analytics/collect/start
GET  /analytics/collect/status
```

### KPIs
```
GET /analytics/kpis
GET /analytics/kpis/{kpi_type}
```

### Dashboards
```
GET  /analytics/dashboards
GET  /analytics/dashboards/{dashboard_id}
POST /analytics/dashboards
```

### Reports
```
GET  /analytics/reports/templates
POST /analytics/reports/generate
POST /analytics/reports/schedule
GET  /analytics/reports/schedules
```

### Privacy & GDPR
```
POST /analytics/privacy/consent
POST /analytics/privacy/consent/revoke
POST /analytics/privacy/dsr
GET  /analytics/privacy/dsr
```

### System Status
```
GET /analytics/status
GET /analytics/metrics
GET /analytics/health
```

### Admin Operations
```
POST /analytics/admin/cleanup
POST /analytics/admin/process-scheduled-reports
GET  /analytics/admin/audit-logs
```

## Usage Examples

### Starting Data Collection

```python
import requests

# Start collecting from Google Search Console
response = requests.post(
    "http://localhost:8000/analytics/collect/start",
    json={
        "data_sources": ["google_search_console"],
        "collection_frequency": "daily"
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### Getting KPIs

```python
# Get comprehensive KPIs for the last month
response = requests.get(
    "http://localhost:8000/analytics/kpis",
    params={
        "date_range": "2024-01-01,2024-01-31",
        "include_advanced": True,
        "include_business_intelligence": True
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

kpis = response.json()
print(f"Growth Rate: {kpis['kpi_data']['basic_kpis']['growth_metrics']['total_growth']}%")
```

### Creating a Custom Dashboard

```python
# Create a custom dashboard
dashboard_config = {
    "name": "Marketing Performance",
    "description": "Track marketing campaign performance",
    "widgets": [
        {
            "type": "line_chart",
            "title": "Campaign ROI Over Time",
            "config": {
                "data_source": "roi_metrics",
                "x_axis": "date",
                "y_axis": "roi_percentage"
            }
        },
        {
            "type": "metric_card",
            "title": "Total Conversions",
            "config": {
                "data_source": "conversion_metrics",
                "metric": "total_conversions"
            }
        }
    ]
}

response = requests.post(
    "http://localhost:8000/analytics/dashboards",
    json=dashboard_config,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### Scheduling a Report

```python
# Schedule a weekly performance report
schedule_data = {
    "template_id": "weekly_performance",
    "name": "Weekly Marketing Report",
    "description": "Weekly marketing performance summary",
    "cron_expression": "0 9 * * 1",  # Every Monday at 9 AM
    "timezone": "UTC",
    "delivery_methods": ["email", "storage"],
    "export_formats": ["pdf", "csv"],
    "filters": {
        "campaign_type": "paid_search",
        "date_range": "last_7_days"
    }
}

response = requests.post(
    "http://localhost:8000/analytics/reports/schedule",
    json=schedule_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### Managing Privacy Consent

```python
# Record user consent for analytics
consent_data = {
    "data_category": "analytics",
    "consent_given": True,
    "consent_version": "1.0",
    "legal_basis": "Legitimate interest",
    "purpose": "Analytics and performance improvement"
}

response = requests.post(
    "http://localhost:8000/analytics/privacy/consent",
    json=consent_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

### Creating a Data Subject Request

```python
# Request access to personal data
dsr_data = {
    "request_type": "access",
    "description": "Request access to all personal data stored in the system"
}

response = requests.post(
    "http://localhost:8000/analytics/privacy/dsr",
    json=dsr_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
```

## Configuration

### Environment Variables

```bash
# Vercel KV Configuration
VERCEL_KV_URL=your_vercel_kv_url
VERCEL_KV_REST_API_URL=your_vercel_kv_rest_api_url
VERCEL_KV_REST_API_TOKEN=your_vercel_kv_token
VERCEL_KV_REST_API_READ_ONLY_TOKEN=your_readonly_token

# Redis Configuration (fallback)
REDIS_URL=redis://localhost:6379

# Google Search Console API
GOOGLE_SEARCH_CONSOLE_CREDENTIALS_FILE=path/to/credentials.json

# SEMrush API
SEMRUSH_API_KEY=your_semrush_api_key

# Social Media APIs
TWITTER_API_KEY=your_twitter_api_key
FACEBOOK_API_KEY=your_facebook_api_key
LINKEDIN_API_KEY=your_linkedin_api_key
INSTAGRAM_API_KEY=your_instagram_api_key
```

### Service Configuration

```python
# Example service configuration
analytics_config = {
    "data_collection": {
        "default_frequency": "daily",
        "rate_limits": {
            "google_search_console": 1000,
            "semrush": 500,
            "social_media": 200
        },
        "retry_attempts": 3,
        "retry_delay": 60
    },
    "kpi_calculation": {
        "calculation_periods": ["daily", "weekly", "monthly"],
        "statistical_config": {
            "confidence_level": 0.95,
            "forecast_periods": 12,
            "seasonality_detection": True
        }
    },
    "dashboard": {
        "default_widgets": ["kpi_overview", "growth_metrics", "performance_summary"],
        "refresh_interval": 300,
        "max_widgets_per_dashboard": 20
    },
    "reporting": {
        "default_templates": ["daily_overview", "weekly_performance", "monthly_analytics"],
        "export_formats": ["json", "csv", "pdf"],
        "max_report_size": "10MB"
    },
    "privacy": {
        "default_retention_days": 90,
        "consent_required": True,
        "dsr_response_time": 30,
        "audit_log_retention": 365
    }
}
```

## Data Models

### Analytics Data Point

```python
@dataclass
class AnalyticsDataPoint:
    id: str
    user_id: str
    source_type: DataSourceType
    metric_name: str
    metric_value: float
    timestamp: datetime
    metadata: Dict[str, Any]
    created_at: datetime
```

### KPI Calculation

```python
@dataclass
class KPICalculation:
    id: str
    user_id: str
    kpi_type: KPIType
    value: float
    target: Optional[float]
    status: TargetStatus
    period: str
    calculated_at: datetime
```

### Dashboard Widget

```python
@dataclass
class DashboardWidget:
    id: str
    type: ChartType
    title: str
    description: str
    config: Dict[str, Any]
    data: Dict[str, Any]
    position: Dict[str, int]
```

## Security Features

### Authentication & Authorization
- Clerk integration for user management
- Role-based access control (RBAC)
- API token management
- Multi-tenant data isolation

### Data Privacy
- GDPR compliance
- Data retention policies
- Consent management
- Data subject rights
- Audit logging

### Data Protection
- Encryption at rest and in transit
- Secure API endpoints
- Rate limiting
- Input validation

## Performance Considerations

### Caching Strategy
- Redis caching for frequently accessed data
- Vercel KV for persistent storage
- Automatic cache invalidation
- Cache warming for dashboards

### Data Processing
- Asynchronous processing
- Batch operations for large datasets
- Background job queues
- Optimized database queries

### Scalability
- Horizontal scaling support
- Load balancing ready
- Database connection pooling
- Memory-efficient data structures

## Monitoring & Health Checks

### System Health
```python
# Check overall system health
response = requests.get("http://localhost:8000/analytics/health")
health_status = response.json()

if health_status["status"] == "healthy":
    print("All services are running normally")
else:
    print(f"System status: {health_status['status']}")
    print(f"Services: {health_status['services']}")
```

### Metrics Dashboard
```python
# Get system metrics
response = requests.get(
    "http://localhost:8000/analytics/metrics",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
metrics = response.json()

print(f"Total data points: {metrics['metrics']['total_data_points']}")
print(f"Active collections: {metrics['metrics']['active_collections']}")
print(f"Data retention compliance: {metrics['metrics']['data_retention_compliance']:.1%}")
```

### Audit Logs
```python
# Get privacy audit logs (admin only)
response = requests.get(
    "http://localhost:8000/analytics/admin/audit-logs",
    params={"limit": 100},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
audit_logs = response.json()

for log in audit_logs["logs"]:
    print(f"{log['timestamp']}: {log['user_id']} - {log['action']}")
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_analytics_system.py -v

# Run specific test class
pytest tests/test_analytics_system.py::TestAnalyticsDataCollector -v

# Run with coverage
pytest tests/test_analytics_system.py --cov=app.services --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual service functionality
- **Integration Tests**: Service interactions
- **Performance Tests**: Large dataset handling
- **Security Tests**: Authentication and authorization
- **Privacy Tests**: GDPR compliance

## Deployment

### Vercel Deployment
```bash
# Deploy to Vercel
vercel --prod

# Set environment variables
vercel env add VERCEL_KV_URL
vercel env add VERCEL_KV_REST_API_TOKEN
vercel env add GOOGLE_SEARCH_CONSOLE_CREDENTIALS
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the service
uvicorn app.main:app --reload
```

## Troubleshooting

### Common Issues

1. **Vercel KV Connection Failed**
   - Check environment variables
   - Verify network connectivity
   - Check Vercel KV service status

2. **Permission Denied Errors**
   - Verify user role and permissions
   - Check access level requirements
   - Review audit logs

3. **Data Collection Failures**
   - Check API rate limits
   - Verify API credentials
   - Review error logs

4. **Performance Issues**
   - Monitor cache hit rates
   - Check database query performance
   - Review background job queues

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check service health
analytics_service = AnalyticsService(db, redis, cache, vercel_kv)
health = await analytics_service.health_check()
print(health)
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for all classes and methods
- Write comprehensive tests
- Update documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide
- Contact the development team

## Roadmap

### Upcoming Features
- Real-time notifications
- Advanced machine learning insights
- Custom KPI builder
- Mobile app support
- Advanced export options
- Integration with more data sources

### Performance Improvements
- GraphQL API support
- Advanced caching strategies
- Database optimization
- Background job improvements
- Real-time data streaming




