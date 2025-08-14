# Staging Environment

## Overview

The staging environment is a production-like environment used for testing and validation before deploying to production. It mirrors the production infrastructure while providing a safe space for testing new features, configurations, and deployments.

## Architecture

### Services
- **Frontend**: Next.js application running on port 3000
- **Backend API**: FastAPI application running on port 8000
- **Worker Pod**: Celery worker for background tasks on port 8001
- **Database**: PostgreSQL 15 with staging-specific data
- **Cache**: Redis 7 for session and task queue management
- **Load Balancer**: Traefik for routing and SSL termination
- **Monitoring**: Prometheus + Grafana for metrics and dashboards
- **Logging**: Elasticsearch + Kibana for centralized logging
- **Reverse Proxy**: Nginx for additional routing and caching

### Network Configuration
- **Subnet**: 172.20.0.0/16
- **Frontend**: staging-frontend.autonomica.ai
- **API**: staging-api.autonomica.ai
- **Worker**: staging-worker.autonomica.ai
- **Monitoring**: staging-monitoring.autonomica.ai
- **Grafana**: staging-grafana.autonomica.ai
- **Logs**: staging-logs.autonomica.ai

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ available disk space
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Required Tools
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt update
sudo apt install -y curl git jq htop
```

## Configuration

### Environment Variables
Copy the `staging.env` file and customize it for your environment:

```bash
cp staging.env .env.staging
# Edit .env.staging with your specific values
```

### Required Configuration
1. **OpenAI API Key**: Valid API key for AI functionality
2. **Clerk Keys**: Authentication service credentials
3. **Database Password**: Secure password for PostgreSQL
4. **Secret Keys**: Application encryption keys
5. **External API Keys**: Twitter, LinkedIn, etc.

### SSL Certificates
Place SSL certificates in the `traefik/ssl/` directory:
- `autonomica.ai.crt` - Public certificate
- `autonomica.ai.key` - Private key
- `ca.crt` - Certificate authority (if applicable)

## Deployment

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-org/autonomica.git
cd autonomica

# Make scripts executable
chmod +x scripts/*.sh

# Deploy staging environment
./scripts/deploy-staging.sh
```

### Deployment Options
```bash
# Skip tests for faster deployment
./scripts/deploy-staging.sh --skip-tests

# Skip database migrations
./scripts/deploy-staging.sh --skip-migrations

# Force rebuild all images
./scripts/deploy-staging.sh --force-rebuild

# Show help
./scripts/deploy-staging.sh --help
```

### Manual Deployment Steps
1. **Build Images**:
   ```bash
   docker build -t autonomica-frontend:staging ./autonomica-frontend
   docker build -t autonomica-api:staging ./autonomica-api
   docker build -t autonomica-worker:staging ./autonomica-worker
   ```

2. **Start Services**:
   ```bash
   docker-compose -f docker-compose.staging.yml up -d
   ```

3. **Run Migrations**:
   ```bash
   cd autonomica-api
   alembic upgrade head
   ```

4. **Verify Deployment**:
   ```bash
   ./scripts/healthcheck.sh
   ```

## Management

### Service Management
```bash
# View all services
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f

# Restart specific service
docker-compose -f docker-compose.staging.yml restart api-staging

# Scale services
docker-compose -f docker-compose.staging.yml up -d --scale api-staging=3

# Stop all services
docker-compose -f docker-compose.staging.yml down

# Stop and remove volumes
docker-compose -f docker-compose.staging.yml down -v
```

### Health Monitoring
```bash
# Run health check
./scripts/healthcheck.sh

# Check specific service
curl http://localhost:8000/health

# Monitor resource usage
docker stats

# View container logs
docker logs autonomica-api-staging
```

### Database Management
```bash
# Access database
docker-compose -f docker-compose.staging.yml exec staging-db psql -U staging_user -d autonomica_staging

# Backup database
docker-compose -f docker-compose.staging.yml exec staging-db pg_dump -U staging_user autonomica_staging > backup.sql

# Restore database
docker-compose -f docker-compose.staging.yml exec -T staging-db psql -U staging_user -d autonomica_staging < backup.sql
```

## Monitoring and Logging

### Prometheus Metrics
- **URL**: http://localhost:9090
- **Metrics**: Application performance, resource usage, custom business metrics
- **Retention**: 7 days
- **Alerts**: CPU, memory, disk usage thresholds

### Grafana Dashboards
- **URL**: http://localhost:3001
- **Username**: admin
- **Password**: staging_grafana_password
- **Dashboards**: System overview, application metrics, business KPIs

### Elasticsearch Logs
- **URL**: http://localhost:9200
- **Indices**: Application logs, access logs, error logs
- **Retention**: Configurable (default: 30 days)

### Kibana Interface
- **URL**: http://localhost:5601
- **Features**: Log search, visualization, alerting
- **Use Cases**: Debugging, performance analysis, security monitoring

## Security

### Network Security
- **Firewall**: Only necessary ports exposed
- **SSL/TLS**: All external communication encrypted
- **Internal Network**: Services isolated in Docker network

### Access Control
- **Authentication**: Clerk-based user management
- **Authorization**: Role-based access control
- **API Keys**: Secure storage and rotation

### Data Protection
- **Encryption**: Data encrypted at rest and in transit
- **Backups**: Regular automated backups
- **PII Handling**: Personal data anonymized in staging

## Backup and Recovery

### Automated Backups
```bash
# Backup schedule: Daily at 2 AM
# Retention: 7 days
# Location: ./database/backups/

# Manual backup
docker-compose -f docker-compose.staging.yml exec staging-db pg_dump -U staging_user autonomica_staging > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Recovery Procedures
1. **Stop Services**:
   ```bash
   docker-compose -f docker-compose.staging.yml down
   ```

2. **Restore Database**:
   ```bash
   docker-compose -f docker-compose.staging.yml up -d staging-db
   sleep 10
   docker-compose -f docker-compose.staging.yml exec -T staging-db psql -U staging_user -d autonomica_staging < backup_file.sql
   ```

3. **Restart Services**:
   ```bash
   docker-compose -f docker-compose.staging.yml up -d
   ```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs [service-name]

# Check resource usage
docker stats

# Verify configuration
docker-compose -f docker-compose.staging.yml config
```

#### Database Connection Issues
```bash
# Check database status
docker-compose -f docker-compose.staging.yml exec staging-db pg_isready -U staging_user

# Check database logs
docker-compose -f docker-compose.staging.yml logs staging-db

# Verify environment variables
docker-compose -f docker-compose.staging.yml exec api-staging env | grep DATABASE
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor application metrics
curl http://localhost:8000/metrics

# Check database performance
docker-compose -f docker-compose.staging.yml exec staging-db psql -U staging_user -d autonomica_staging -c "SELECT * FROM pg_stat_activity;"
```

### Debug Commands
```bash
# Enter running container
docker-compose -f docker-compose.staging.yml exec api-staging bash

# Check network connectivity
docker-compose -f docker-compose.staging.yml exec api-staging ping staging-db

# View real-time logs
docker-compose -f docker-compose.staging.yml logs -f --tail=100

# Check service dependencies
docker-compose -f docker-compose.staging.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

## Maintenance

### Regular Tasks
- **Daily**: Health checks, log rotation
- **Weekly**: Security updates, dependency updates
- **Monthly**: Performance review, capacity planning

### Updates and Upgrades
```bash
# Update images
docker-compose -f docker-compose.staging.yml pull

# Rebuild and restart
docker-compose -f docker-compose.staging.yml up -d --build

# Update dependencies
cd autonomica-api && pip install -r requirements.txt --upgrade
cd ../autonomica-frontend && npm update
```

### Cleanup
```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Full cleanup (use with caution)
docker system prune -a -f
```

## Integration

### CI/CD Pipeline
The staging environment integrates with the CI/CD pipeline:
- **Automated Testing**: Pre-deployment validation
- **Quality Gates**: Code quality and security checks
- **Deployment**: Automated deployment to staging
- **Validation**: Post-deployment health checks

### External Services
- **Monitoring**: Integration with external monitoring services
- **Alerting**: Slack, email, or webhook notifications
- **Backup**: Integration with cloud storage services
- **Logging**: Centralized logging aggregation

## Best Practices

### Development Workflow
1. **Feature Development**: Develop in feature branches
2. **Testing**: Run tests locally before pushing
3. **Code Review**: Require peer review for all changes
4. **Staging Deployment**: Deploy to staging for validation
5. **Production Deployment**: Deploy to production after staging validation

### Environment Management
- **Configuration**: Use environment variables for configuration
- **Secrets**: Never commit secrets to version control
- **Documentation**: Keep configuration and procedures documented
- **Versioning**: Version all configuration changes

### Monitoring and Alerting
- **Health Checks**: Implement comprehensive health checks
- **Metrics**: Collect relevant business and technical metrics
- **Alerts**: Set up alerts for critical issues
- **Dashboards**: Create informative monitoring dashboards

## Support

### Getting Help
- **Documentation**: Check this document and related guides
- **Logs**: Review application and system logs
- **Community**: Reach out to the development team
- **Issues**: Create GitHub issues for bugs or feature requests

### Emergency Procedures
1. **Service Down**: Check health status and restart if needed
2. **Data Loss**: Restore from latest backup
3. **Security Breach**: Isolate affected services and investigate
4. **Performance Issues**: Scale services or optimize configuration

## Conclusion

The staging environment provides a robust, production-like environment for testing and validation. By following the established procedures and best practices, teams can confidently test new features and configurations before deploying to production.

For questions or issues with the staging environment, please refer to the troubleshooting section or contact the development team.