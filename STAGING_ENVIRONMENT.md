# Staging Environment Configuration

## Overview
This document provides comprehensive information about the staging environment setup for the Autonomica project, including configuration, deployment processes, and management procedures.

## Environment Architecture

### Staging Environment Components

#### 1. Frontend (Next.js)
- **Platform**: Vercel
- **URL**: https://staging.autonomica.app
- **Branch**: `develop`
- **Auto-deploy**: Yes (on push to develop)
- **Preview URLs**: Yes (on PR)

#### 2. Backend API (FastAPI)
- **Platform**: Railway
- **URL**: https://staging-api.autonomica.app
- **Branch**: `develop`
- **Auto-deploy**: Yes (on push to develop)
- **Database**: PostgreSQL (staging instance)

#### 3. Worker Pod (Python)
- **Platform**: Railway
- **Branch**: `develop`
- **Auto-deploy**: Yes (on push to develop)
- **Queue**: Redis (staging instance)

#### 4. Database
- **Platform**: Railway
- **Type**: PostgreSQL
- **Environment**: Staging
- **Backup**: Daily automated backups

#### 5. Cache & Queue
- **Platform**: Railway
- **Redis**: Staging instance
- **Queue Management**: Celery with Redis backend

## Environment Variables

### Frontend Environment Variables
```bash
# Staging Environment
NEXT_PUBLIC_API_URL=https://staging-api.autonomica.app
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_ANALYTICS_ID=G-...
```

### Backend Environment Variables
```bash
# Staging Environment
ENVIRONMENT=staging
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CLERK_SECRET_KEY=sk_test_...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

### Worker Environment Variables
```bash
# Staging Environment
ENVIRONMENT=staging
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CLERK_SECRET_KEY=sk_test_...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

## Deployment Process

### Automatic Deployment
1. **Trigger**: Push to `develop` branch
2. **CI/CD Pipeline**: Runs all tests and quality checks
3. **Staging Deployment**: Automatic deployment to staging environment
4. **Health Checks**: Automated health checks after deployment
5. **Notification**: Team notification of deployment status

### Manual Deployment
```bash
# Deploy to staging manually
gh workflow run deploy-staging.yml

# Deploy specific service
gh workflow run deploy-staging.yml --field service=frontend
gh workflow run deploy-staging.yml --field service=backend
gh workflow run deploy-staging.yml --field service=worker
```

## Environment Management

### Access Control
- **Admin Access**: @jairodriguez
- **Developer Access**: Team members with appropriate permissions
- **Read-only Access**: Stakeholders and QA team

### Environment Isolation
- **Separate Databases**: Staging and production use different database instances
- **Separate API Keys**: Different API keys for staging and production
- **Separate Domains**: Completely isolated domains and subdomains
- **Separate Storage**: Different storage buckets and CDN configurations

### Data Management
- **Test Data**: Staging environment uses test/sample data
- **No Production Data**: Staging never contains real user data
- **Data Refresh**: Weekly data refresh from production schema
- **Backup Strategy**: Daily backups with 7-day retention

## Monitoring and Health Checks

### Health Check Endpoints
```bash
# Frontend Health Check
curl https://staging.autonomica.app/api/health

# Backend Health Check
curl https://staging-api.autonomica.app/health

# Worker Health Check
curl https://staging-worker.autonomica.app/health
```

### Monitoring Dashboard
- **URL**: https://staging.autonomica.app/monitoring
- **Metrics**: Response times, error rates, throughput
- **Alerts**: Automated alerts for critical issues
- **Logs**: Centralized logging with search capabilities

### Performance Metrics
- **Response Time**: < 200ms for API calls
- **Uptime**: > 99.9%
- **Error Rate**: < 0.1%
- **Throughput**: > 1000 requests/minute

## Testing in Staging

### Test Types
1. **Integration Tests**: End-to-end workflow testing
2. **Performance Tests**: Load and stress testing
3. **User Acceptance Tests**: Stakeholder testing
4. **Security Tests**: Vulnerability scanning
5. **Compatibility Tests**: Browser and device testing

### Test Data
- **User Accounts**: Test user accounts with various permission levels
- **Sample Projects**: Pre-populated with sample marketing projects
- **Agent Configurations**: Test agent setups and configurations
- **Analytics Data**: Sample analytics and reporting data

### Test Automation
- **Scheduled Tests**: Daily automated test runs
- **PR Tests**: Automatic testing on pull requests
- **Regression Tests**: Automated regression testing
- **Performance Tests**: Weekly performance benchmarking

## Troubleshooting

### Common Issues

#### 1. Deployment Failures
```bash
# Check deployment status
gh run list --workflow=deploy-staging.yml

# View deployment logs
gh run view --log

# Retry failed deployment
gh run rerun <run-id>
```

#### 2. Environment Variable Issues
```bash
# Check environment variables
gh secret list

# Update environment variable
gh secret set ENVIRONMENT --body "staging"

# View secret value (admin only)
gh secret view ENVIRONMENT
```

#### 3. Database Connection Issues
```bash
# Check database status
railway status

# View database logs
railway logs

# Restart database service
railway service restart
```

#### 4. Performance Issues
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s "https://staging-api.autonomica.app/health"

# Monitor resource usage
railway status --service=backend
```

### Debugging Tools
- **Logs**: Centralized logging with search and filtering
- **Metrics**: Real-time performance metrics
- **Tracing**: Distributed tracing for request flows
- **Profiling**: Performance profiling tools

## Security Considerations

### Access Control
- **Environment Isolation**: Complete separation from production
- **API Key Management**: Separate API keys for staging
- **User Authentication**: Test user accounts only
- **Network Security**: VPC and firewall configurations

### Data Protection
- **No PII**: Staging environment contains no personal data
- **Encryption**: All data encrypted in transit and at rest
- **Backup Security**: Encrypted backups with access controls
- **Audit Logging**: Comprehensive audit trail

### Compliance
- **GDPR**: No real user data in staging
- **SOC 2**: Security controls and monitoring
- **PCI DSS**: Payment data handling procedures
- **ISO 27001**: Information security management

## Maintenance Procedures

### Regular Maintenance
- **Weekly**: Data refresh and cleanup
- **Monthly**: Security updates and patches
- **Quarterly**: Performance optimization
- **Annually**: Security audit and compliance review

### Emergency Procedures
- **Service Outage**: Immediate notification and escalation
- **Security Incident**: Security team notification and response
- **Data Breach**: Incident response and containment
- **Performance Degradation**: Performance team investigation

### Backup and Recovery
- **Backup Schedule**: Daily automated backups
- **Recovery Time**: < 4 hours for full environment recovery
- **Data Retention**: 7 days for staging backups
- **Testing**: Monthly backup restoration testing

## Future Enhancements

### Planned Improvements
1. **Multi-region Staging**: Geographic distribution for global testing
2. **Environment Templates**: Automated environment provisioning
3. **Advanced Monitoring**: AI-powered anomaly detection
4. **Self-service Portal**: Developer self-service environment management
5. **Cost Optimization**: Automated resource scaling and optimization

### Technology Upgrades
1. **Container Orchestration**: Kubernetes deployment
2. **Service Mesh**: Istio for service communication
3. **Observability**: Advanced observability stack
4. **Security**: Enhanced security scanning and monitoring
5. **Performance**: Advanced performance optimization tools

## Resources and References

### Documentation
- [Vercel Staging Deployment](https://vercel.com/docs/concepts/deployments/environments)
- [Railway Environment Management](https://docs.railway.app/deploy/environments)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments)

### Support
- **Platform Support**: Vercel, Railway, GitHub
- **Internal Support**: DevOps team, Platform team
- **Emergency Contacts**: On-call engineers, Security team

### Monitoring
- **Dashboard**: Staging monitoring dashboard
- **Alerts**: PagerDuty integration
- **Metrics**: Prometheus and Grafana
- **Logs**: Centralized logging platform

