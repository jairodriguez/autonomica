# Testing and Deployment Pipeline

## Overview
This document provides comprehensive documentation for the complete testing and deployment pipeline implemented for the Autonomica project. The pipeline encompasses continuous integration, continuous deployment, testing frameworks, monitoring, alerting, and automated rollback capabilities.

## Table of Contents
1. [Pipeline Architecture](#pipeline-architecture)
2. [Testing Framework](#testing-framework)
3. [CI/CD Pipeline](#cicd-pipeline)
4. [Deployment Strategy](#deployment-strategy)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Automated Rollback](#automated-rollback)
7. [Environment Management](#environment-management)
8. [Security and Compliance](#security-and-compliance)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

## Pipeline Architecture

### High-Level Flow
```
Code Push → Tests → Quality Checks → Build → Deploy → Monitor → Alert → Rollback (if needed)
    ↓         ↓         ↓           ↓        ↓         ↓        ↓         ↓
  Git      Unit/     Linting/    Docker   Staging/   Health   Issues    Auto/
  Branch   Integration  Security   Images   Production  Metrics  Detected  Manual
```

### Component Overview
- **Version Control**: Git with branching strategy
- **CI/CD Tool**: GitHub Actions
- **Testing**: Pytest (Python), Jest (JavaScript), Integration tests
- **Quality**: Ruff, MyPy, ESLint, Prettier
- **Deployment**: Vercel (Frontend), Railway (Backend/Worker)
- **Monitoring**: Prometheus, Grafana, AlertManager
- **Rollback**: Automated rollback system

## Testing Framework

### Backend Testing (Python/FastAPI)

#### Unit Testing with Pytest
```python
# Example test structure
tests/
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/
│   ├── test_api_integration.py
│   └── test_database_integration.py
└── conftest.py

# Test configuration (pytest.ini)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

#### Test Coverage
```python
# Coverage configuration (.coveragerc)
[run]
source = autonomica_api
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### Frontend Testing (React/Next.js)

#### Unit Testing with Jest
```javascript
// Jest configuration (jest.config.js)
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testPathIgnorePatterns: ['<rootDir>/.next/', '<rootDir>/node_modules/'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
  ],
}
```

#### Integration Testing
```typescript
// Example integration test
import { render, screen, waitFor } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import Dashboard from '../Dashboard'

const server = setupServer(
  rest.get('/api/projects', (req, res, ctx) => {
    return res(ctx.json({ projects: [] }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('renders dashboard with projects', async () => {
  render(<Dashboard />)
  
  await waitFor(() => {
    expect(screen.getByText('Projects')).toBeInTheDocument()
  })
})
```

### Load Testing

#### Locust Configuration
```python
# locustfile.py
from locust import HttpUser, task, between

class AutonomicaUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def view_dashboard(self):
        self.client.get("/dashboard")
    
    @task(2)
    def create_project(self):
        self.client.post("/api/projects", json={
            "name": "Test Project",
            "description": "Test Description"
        })
    
    @task(1)
    def view_projects(self):
        self.client.get("/api/projects")
```

## CI/CD Pipeline

### GitHub Actions Workflows

#### Main CI/CD Pipeline
```yaml
# .github/workflows/ci-cd-pipeline.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test-and-quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Run tests and quality checks
        run: |
          # Frontend
          cd autonomica-frontend
          npm ci
          npm run lint
          npm run test:ci
          npm run build
          
          # Backend
          cd ../autonomica-api
          pip install -r requirements.txt
          pytest --cov=autonomica_api --cov-report=xml
          ruff check .
          mypy .
```

#### Staging Deployment
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [develop]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          # Deploy backend
          railway up --service backend
          
          # Deploy worker
          railway up --service worker
          
          # Deploy frontend
          vercel --prod --confirm
```

#### Production Deployment
```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          # Deploy backend
          railway up --service backend
          
          # Deploy worker
          railway up --service worker
          
          # Deploy frontend
          vercel --prod --confirm
```

### Pipeline Stages

#### 1. Code Quality Checks
- **Linting**: ESLint, Ruff, MyPy
- **Formatting**: Prettier, Black
- **Security**: Bandit, Safety, npm audit
- **Type Checking**: TypeScript, MyPy

#### 2. Testing
- **Unit Tests**: Jest, Pytest
- **Integration Tests**: API tests, database tests
- **E2E Tests**: Playwright
- **Load Tests**: Locust

#### 3. Building
- **Frontend**: Next.js build
- **Backend**: Python package build
- **Worker**: Docker image build

#### 4. Deployment
- **Staging**: Automatic on develop branch
- **Production**: Manual approval on main branch

## Deployment Strategy

### Environment Strategy

#### Staging Environment
- **Purpose**: Testing, QA, pre-production validation
- **URL**: https://staging.autonomica.app
- **Branch**: `develop`
- **Auto-deploy**: Yes
- **Database**: Staging instance
- **Features**: All features enabled

#### Production Environment
- **Purpose**: Live user-facing application
- **URL**: https://autonomica.app
- **Branch**: `main`
- **Auto-deploy**: No (manual approval required)
- **Database**: Production instance
- **Features**: Feature flags controlled

### Deployment Methods

#### Frontend (Vercel)
```bash
# Automatic deployment
git push origin develop  # Deploys to staging
git push origin main     # Deploys to production

# Manual deployment
vercel --prod --confirm

# Rollback
vercel rollback
```

#### Backend (Railway)
```bash
# Automatic deployment
git push origin develop  # Deploys to staging
git push origin main     # Deploys to production

# Manual deployment
railway up --service backend

# Rollback
railway rollback --service backend
```

#### Worker (Railway)
```bash
# Automatic deployment
git push origin develop  # Deploys to staging
git push origin main     # Deploys to production

# Manual deployment
railway up --service worker

# Rollback
railway rollback --service worker
```

### Feature Flags
```typescript
// Feature flag configuration
const featureFlags = {
  newDashboard: process.env.NEXT_PUBLIC_FEATURE_NEW_DASHBOARD === 'true',
  advancedAnalytics: process.env.NEXT_PUBLIC_FEATURE_ADVANCED_ANALYTICS === 'true',
  aiAssistance: process.env.NEXT_PUBLIC_FEATURE_AI_ASSISTANCE === 'true',
}

// Usage in components
if (featureFlags.newDashboard) {
  return <NewDashboard />
} else {
  return <LegacyDashboard />
}
```

## Monitoring and Alerting

### Monitoring Stack

#### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'frontend'
    static_configs:
      - targets: ['autonomica.app:3000']
    metrics_path: '/api/metrics'
    
  - job_name: 'backend'
    static_configs:
      - targets: ['api.autonomica.app:8000']
    metrics_path: '/metrics'
    
  - job_name: 'worker'
    static_configs:
      - targets: ['worker.autonomica.app:8000']
    metrics_path: '/metrics'
```

#### AlertManager Configuration
```yaml
# monitoring/alertmanager.yml
route:
  group_by: ['alertname', 'service', 'severity']
  receiver: 'slack-critical'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      group_wait: 0s
      repeat_interval: 0s

receivers:
  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        title: '{{ template "slack.autonomica.title" . }}'
        text: '{{ template "slack.autonomica.text" . }}'
```

### Key Metrics

#### Application Metrics
- **Response Time**: P50, P95, P99 percentiles
- **Error Rate**: Percentage of failed requests
- **Throughput**: Requests per second
- **Availability**: Uptime percentage

#### Business Metrics
- **User Engagement**: Daily active users, session duration
- **Feature Usage**: Feature adoption rates
- **Conversion Rates**: User conversion metrics
- **User Satisfaction**: Feedback scores

#### Infrastructure Metrics
- **CPU Usage**: Percentage of CPU utilization
- **Memory Usage**: RAM usage percentage
- **Disk Usage**: Storage utilization
- **Network I/O**: Network traffic patterns

## Automated Rollback

### Rollback Triggers

#### Health Check Failures
```yaml
# monitoring/rollback-config.yml
triggers:
  health_check:
    enabled: true
    thresholds:
      consecutive_failures: 3
      failure_window: '2m'
      recovery_threshold: 2
      recovery_window: '5m'
    
    endpoints:
      - name: 'frontend'
        url: 'https://autonomica.app/api/health'
        critical: true
      
      - name: 'backend'
        url: 'https://api.autonomica.app/health'
        critical: true
```

#### Performance Degradation
```yaml
performance:
  enabled: true
  thresholds:
    response_time_p95: '2s'
    response_time_p99: '5s'
    error_rate: '0.05'
    throughput_drop: '0.3'
  
  evaluation_window: '5m'
  consecutive_violations: 2
```

### Rollback Strategies

#### Immediate Rollback
- **Triggers**: Critical health failures, security issues
- **Actions**: Rollback all services, freeze deployments
- **Timeout**: 30 seconds
- **Notification**: PagerDuty, Slack, Email

#### Fast Rollback
- **Triggers**: Performance issues, non-critical failures
- **Actions**: Rollback affected service, investigate cause
- **Timeout**: 2 minutes
- **Notification**: Slack, Email

#### Gradual Rollback
- **Triggers**: Business metrics drops
- **Actions**: Reduce traffic, monitor, rollback if needed
- **Timeout**: 10 minutes
- **Notification**: Slack

### Rollback Workflow
```yaml
# .github/workflows/automated-rollback.yml
name: Automated Rollback

on:
  workflow_dispatch:
    inputs:
      service:
        description: 'Service to rollback'
        required: true
        type: choice
        options: [all, frontend, backend, worker]
      trigger:
        description: 'Rollback trigger'
        required: true
        type: choice
        options: [health_check_failure, performance_degradation, security_issue, manual]

jobs:
  assess_situation:
    name: Assess Situation
    runs-on: ubuntu-latest
    steps:
      - name: Check service health
        run: |
          # Check all services
          curl -f "$FRONTEND_URL/api/health"
          curl -f "$BACKEND_URL/health"
          curl -f "$WORKER_URL/health"
```

## Environment Management

### Environment Configuration

#### Staging Environment
```bash
# Environment variables
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_API_URL=https://staging-api.autonomica.app
DATABASE_URL=postgresql://staging_user:staging_password@staging-db.autonomica.app:5432/autonomica_staging
REDIS_URL=redis://staging-redis.autonomica.app:6379/0
```

#### Production Environment
```bash
# Environment variables
NODE_ENV=production
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_API_URL=https://api.autonomica.app
DATABASE_URL=postgresql://prod_user:prod_password@prod-db.autonomica.app:5432/autonomica_prod
REDIS_URL=redis://prod-redis.autonomica.app:6379/0
```

### Environment Protection

#### GitHub Environments
```yaml
# .github/environments/staging.yml
name: staging
url: https://staging.autonomica.app
protection_rules:
  required_reviewers:
    - jairodriguez
  wait_timer: 0
  deployment_branch_policy:
    protected_branches: true
    custom_branch_policies: false

# .github/environments/production.yml
name: production
url: https://autonomica.app
protection_rules:
  required_reviewers:
    - jairodriguez
  wait_timer: 5
  deployment_branch_policy:
    protected_branches: true
    custom_branch_policies: false
```

## Security and Compliance

### Security Measures

#### Code Quality and Security
- **Linting**: ESLint, Ruff with security rules
- **Security Scanning**: Bandit, Safety, npm audit
- **Dependency Management**: Regular updates, vulnerability scanning
- **Code Review**: Required for all changes

#### Infrastructure Security
- **Environment Variables**: Encrypted secrets
- **Access Control**: Role-based permissions
- **Network Security**: HTTPS only, firewall rules
- **Monitoring**: Security event logging

#### Deployment Security
- **Approval Process**: Required for production
- **Audit Logging**: All deployment actions logged
- **Rollback Capability**: Immediate rollback on security issues
- **Incident Response**: Security team notification

### Compliance

#### Data Protection
- **GDPR Compliance**: User data handling
- **Data Encryption**: At rest and in transit
- **Access Logging**: All data access logged
- **Data Retention**: Configurable retention policies

#### Audit Requirements
- **Change Tracking**: All changes version controlled
- **Deployment Logs**: Complete deployment history
- **Performance Metrics**: Continuous monitoring
- **Incident Reports**: Post-mortem documentation

## Troubleshooting

### Common Issues

#### 1. Pipeline Failures
```bash
# Check workflow status
gh run list --workflow=ci-cd-pipeline.yml

# View detailed logs
gh run view --log <run-id>

# Retry failed workflow
gh run rerun <run-id>
```

#### 2. Deployment Issues
```bash
# Check service status
railway status --service backend
vercel ls

# View service logs
railway logs --service backend
vercel logs

# Check environment variables
railway variables list --service backend
vercel env ls
```

#### 3. Monitoring Issues
```bash
# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets

# Check AlertManager status
curl http://alertmanager:9093/api/v1/status

# Test alert rules
curl -G http://prometheus:9090/api/v1/query --data-urlencode 'query=up'
```

### Debugging Commands

#### Frontend Debugging
```bash
# Check build output
cd autonomica-frontend
npm run build

# Check test coverage
npm run test:coverage

# Check linting
npm run lint

# Check types
npm run type-check
```

#### Backend Debugging
```bash
# Check test coverage
cd autonomica-api
pytest --cov=autonomica_api --cov-report=html

# Check linting
ruff check .

# Check types
mypy .

# Check security
bandit -r .
```

#### Infrastructure Debugging
```bash
# Check database connections
psql $DATABASE_URL -c "SELECT version();"

# Check Redis connections
redis-cli -u $REDIS_URL ping

# Check service health
curl -f https://api.autonomica.app/health
curl -f https://worker.autonomica.app/health
```

## Best Practices

### Development Workflow

#### 1. Code Quality
- Write tests for all new features
- Maintain high test coverage (>80%)
- Use linting and formatting tools
- Regular dependency updates

#### 2. Deployment Process
- Always test in staging first
- Use feature flags for gradual rollouts
- Monitor deployments closely
- Have rollback plan ready

#### 3. Monitoring and Alerting
- Set appropriate alert thresholds
- Use multiple notification channels
- Regular alert review and tuning
- Document alert procedures

#### 4. Security
- Regular security scans
- Keep dependencies updated
- Monitor for vulnerabilities
- Incident response planning

### Continuous Improvement

#### 1. Pipeline Optimization
- Regular performance reviews
- Optimize build times
- Improve test efficiency
- Reduce false positives

#### 2. Monitoring Enhancement
- Add new metrics as needed
- Optimize alert thresholds
- Improve dashboard usability
- Better error tracking

#### 3. Process Improvement
- Regular post-mortems
- Update documentation
- Team training
- Tool evaluation

## Support and Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vercel Deployment Guide](https://vercel.com/docs/deployments)
- [Railway Documentation](https://docs.railway.app/)
- [Prometheus Documentation](https://prometheus.io/docs/)

### Internal Resources
- [Testing Framework Guide](TESTING_FRAMEWORK.md)
- [Integration Testing Guide](INTEGRATION_TESTING.md)
- [Code Quality Framework](CODE_QUALITY_FRAMEWORK.md)
- [Staging Environment Guide](STAGING_ENVIRONMENT.md)
- [Automated Deployment Guide](AUTOMATED_DEPLOYMENT_GUIDE.md)
- [Monitoring and Alerting Guide](MONITORING_AND_ALERTING_GUIDE.md)
- [Automated Rollback Guide](AUTOMATED_ROLLBACK_GUIDE.md)

### Support Channels
- **Platform Support**: Vercel, Railway, GitHub
- **Internal Support**: DevOps team, Platform team
- **Emergency Contacts**: On-call engineers
- **Documentation**: Internal runbooks and guides

### Monitoring Tools
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards and visualization
- **AlertManager**: Alert routing and notification
- **GitHub Actions**: CI/CD pipeline
- **External Services**: Sentry, New Relic, Datadog

---

*This document is maintained by the DevOps team and should be updated whenever the pipeline configuration changes.*
