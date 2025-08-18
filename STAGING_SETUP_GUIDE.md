# Staging Environment Setup Guide

## Overview
This guide provides step-by-step instructions for setting up the staging environment for the Autonomica project. The staging environment is used for testing, quality assurance, and pre-production validation.

## Prerequisites

### Required Tools
- **GitHub CLI**: For repository management and secrets
- **Vercel CLI**: For frontend deployment
- **Railway CLI**: For backend and worker deployment
- **Docker**: For building container images
- **Node.js**: For frontend build tools
- **Python**: For backend tools and testing

### Required Accounts
- **GitHub**: Repository access and secrets management
- **Vercel**: Frontend hosting and deployment
- **Railway**: Backend hosting, worker hosting, and database
- **Clerk**: Authentication service (staging instance)
- **AI Service Providers**: OpenAI, Anthropic, Google, Mistral (staging keys)

## Step-by-Step Setup

### 1. Repository Setup

#### 1.1 Create Develop Branch
```bash
# Ensure you're on the main branch
git checkout main

# Create and switch to develop branch
git checkout -b develop

# Push develop branch to remote
git push -u origin develop
```

#### 1.2 Configure Branch Protection
1. Go to GitHub repository settings
2. Navigate to "Branches" → "Add rule"
3. Set branch name pattern: `develop`
4. Configure protection rules:
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging

### 2. Environment Configuration

#### 2.1 Frontend Configuration (Vercel)
```bash
# Navigate to frontend directory
cd autonomica-frontend

# Login to Vercel
vercel login

# Link project to Vercel
vercel link

# Set staging environment variables
vercel env add NEXT_PUBLIC_ENVIRONMENT
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
vercel env add NEXT_PUBLIC_ANALYTICS_ID

# Deploy to staging
vercel --env NEXT_PUBLIC_ENVIRONMENT=staging
```

#### 2.2 Backend Configuration (Railway)
```bash
# Navigate to backend directory
cd autonomica-api

# Login to Railway
railway login

# Initialize Railway project
railway init

# Add environment variables
railway variables set ENVIRONMENT=staging
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...
railway variables set CLERK_SECRET_KEY=sk_test_...
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set GOOGLE_API_KEY=...
railway variables set MISTRAL_API_KEY=...

# Deploy to Railway
railway up
```

#### 2.3 Worker Configuration (Railway)
```bash
# Navigate to worker directory
cd worker

# Initialize Railway project
railway init

# Add environment variables
railway variables set ENVIRONMENT=staging
railway variables set DATABASE_URL=postgresql://...
railway variables set REDIS_URL=redis://...
railway variables set CLERK_SECRET_KEY=sk_test_...
railway variables set OPENAI_API_KEY=sk-...
railway variables set ANTHROPIC_API_KEY=sk-ant-...
railway variables set GOOGLE_API_KEY=...
railway variables set MISTRAL_API_KEY=...

# Deploy to Railway
railway up
```

### 3. Database Setup

#### 3.1 PostgreSQL Database (Railway)
1. Create new PostgreSQL service in Railway
2. Note the connection details
3. Set environment variables in backend and worker services
4. Run database migrations:
```bash
cd autonomica-api
railway run python -m alembic upgrade head
```

#### 3.2 Redis Setup (Railway)
1. Create new Redis service in Railway
2. Note the connection details
3. Set environment variables in backend and worker services

### 4. Authentication Setup (Clerk)

#### 4.1 Create Staging Application
1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Create new application: `autonomica-staging`
3. Configure domains:
   - `staging.autonomica.app`
   - `staging-api.autonomica.app`
4. Note the publishable and secret keys

#### 4.2 Configure Environment Variables
```bash
# Frontend (Vercel)
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

# Backend (Railway)
railway variables set CLERK_SECRET_KEY=sk_test_...
railway variables set CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 5. AI Service Configuration

#### 5.1 OpenAI
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create new API key for staging
3. Set environment variable:
```bash
railway variables set OPENAI_API_KEY=sk-staging-key-here
```

#### 5.2 Anthropic
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create new API key for staging
3. Set environment variable:
```bash
railway variables set ANTHROPIC_API_KEY=sk-ant-staging-key-here
```

#### 5.3 Google AI
1. Go to [Google AI Studio](https://makersuite.google.com/)
2. Create new API key for staging
3. Set environment variable:
```bash
railway variables set GOOGLE_API_KEY=staging-key-here
```

#### 5.4 Mistral
1. Go to [Mistral AI Console](https://console.mistral.ai/)
2. Create new API key for staging
3. Set environment variable:
```bash
railway variables set MISTRAL_API_KEY=staging-key-here
```

### 6. Domain Configuration

#### 6.1 Frontend Domain (Vercel)
1. Go to Vercel project settings
2. Add custom domain: `staging.autonomica.app`
3. Configure DNS records as instructed by Vercel

#### 6.2 Backend Domain (Railway)
1. Go to Railway project settings
2. Add custom domain: `staging-api.autonomica.app`
3. Configure DNS records as instructed by Railway

#### 6.3 Worker Domain (Railway)
1. Go to Railway project settings
2. Add custom domain: `staging-worker.autonomica.app`
3. Configure DNS records as instructed by Railway

### 7. Monitoring and Analytics

#### 7.1 Sentry (Error Tracking)
1. Create new Sentry project for staging
2. Get the DSN
3. Set environment variable:
```bash
railway variables set SENTRY_DSN=https://staging-sentry-dsn-here
```

#### 7.2 Google Analytics
1. Create new Google Analytics property for staging
2. Get the measurement ID
3. Set environment variable:
```bash
vercel env add NEXT_PUBLIC_ANALYTICS_ID
```

### 8. Testing Configuration

#### 8.1 Test Data Setup
```bash
# Navigate to backend directory
cd autonomica-api

# Run test data setup
railway run python scripts/setup_test_data.py
```

#### 8.2 Health Check Endpoints
Ensure the following endpoints are accessible:
- Frontend: `https://staging.autonomica.app/api/health`
- Backend: `https://staging-api.autonomica.app/health`
- Worker: `https://staging-worker.autonomica.app/health`

### 9. CI/CD Pipeline Configuration

#### 9.1 GitHub Actions
1. Go to repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add the following secrets:
   - `VERCEL_TOKEN`: Vercel deployment token
   - `RAILWAY_TOKEN`: Railway deployment token
   - `STAGING_DATABASE_URL`: Staging database connection string
   - `STAGING_REDIS_URL`: Staging Redis connection string

#### 9.2 Environment Protection
1. Go to repository settings
2. Navigate to "Environments"
3. Create `staging` environment
4. Configure protection rules:
   - Required reviewers: `@jairodriguez`
   - Wait timer: 0 minutes
   - Deployment branches: `develop`

### 10. Verification and Testing

#### 10.1 Manual Verification
```bash
# Test frontend deployment
curl -f https://staging.autonomica.app/api/health

# Test backend deployment
curl -f https://staging-api.autonomica.app/health

# Test worker deployment
curl -f https://staging-worker.autonomica.app/health
```

#### 10.2 Automated Testing
```bash
# Run staging-specific tests
npm run test:staging

# Run integration tests against staging
npm run test:integration:staging
```

#### 10.3 Performance Testing
```bash
# Run load tests against staging
npm run test:load:staging

# Run performance benchmarks
npm run test:performance:staging
```

## Troubleshooting

### Common Issues

#### 1. Environment Variable Issues
- Ensure all required environment variables are set
- Check for typos in variable names
- Verify variable values are correct

#### 2. Database Connection Issues
- Verify database service is running
- Check connection string format
- Ensure database migrations have been run

#### 3. Authentication Issues
- Verify Clerk configuration
- Check domain settings
- Ensure API keys are correct

#### 4. Deployment Failures
- Check build logs for errors
- Verify all dependencies are installed
- Check for syntax errors in code

### Debugging Commands
```bash
# Check Railway service status
railway status

# View Railway logs
railway logs

# Check Vercel deployment status
vercel ls

# View Vercel logs
vercel logs

# Check GitHub Actions status
gh run list --workflow=deploy-staging.yml
```

## Maintenance

### Regular Tasks
- **Weekly**: Update test data and verify functionality
- **Monthly**: Review and update environment variables
- **Quarterly**: Security audit and dependency updates
- **Annually**: Performance review and optimization

### Monitoring
- Set up alerts for service downtime
- Monitor resource usage and costs
- Track error rates and performance metrics
- Regular health check verification

## Security Considerations

### Access Control
- Limit access to staging environment
- Use separate API keys for staging
- Regular rotation of credentials
- Audit access logs

### Data Protection
- No production data in staging
- Regular data cleanup
- Encrypted data transmission
- Secure credential storage

## Cost Optimization

### Resource Management
- Monitor resource usage
- Scale down during off-hours
- Use appropriate instance sizes
- Regular cost review

### Optimization Strategies
- Implement caching strategies
- Optimize database queries
- Use CDN for static assets
- Regular performance tuning

## Support and Resources

### Documentation
- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app/)
- [Clerk Documentation](https://clerk.com/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Support Channels
- Platform support: Vercel, Railway, Clerk
- Internal support: DevOps team, Platform team
- Emergency contacts: On-call engineers

### Monitoring Tools
- Vercel Analytics
- Railway Metrics
- Sentry Error Tracking
- Custom monitoring dashboards
