# Autonomica Branching Strategy

## Overview
This document outlines the branching strategy and workflow for the Autonomica project, ensuring code quality, collaboration, and deployment safety.

## Branch Structure

### Main Branches
- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features, staging deployments

### Supporting Branches
- **`feature/*`** - Feature development branches
- **`bugfix/*`** - Bug fix branches
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation branches

## Branch Protection Rules

### Main Branch (`main`)
- **Require pull request reviews before merging**
  - Required approving reviews: 2
  - Dismiss stale PR approvals when new commits are pushed
  - Require review from code owners
- **Require status checks to pass before merging**
  - All CI/CD checks must pass
  - Frontend tests must pass
  - Backend tests must pass
  - Worker tests must pass
  - Integration tests must pass
  - Security scans must pass
- **Require branches to be up to date before merging**
- **Require linear history**
- **Restrict pushes that create files larger than 100 MB**
- **Require signed commits**

### Develop Branch (`develop`)
- **Require pull request reviews before merging**
  - Required approving reviews: 1
  - Dismiss stale PR approvals when new commits are pushed
- **Require status checks to pass before merging**
  - All CI/CD checks must pass
- **Require branches to be up to date before merging**
- **Allow force pushes for maintainers only**

## Workflow

### Feature Development
1. Create feature branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/ci-cd-pipeline
   ```
2. Develop and test feature
3. Push feature branch and create PR to `develop`
4. Code review and approval required
5. Merge to `develop` after approval

### Release Process
1. Create release branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.0.0
   ```
2. Final testing and bug fixes
3. Update version numbers and changelog
4. Create PR to `main`
5. Code review and approval required
6. Merge to `main` and tag release
7. Merge back to `develop`

### Hotfix Process
1. Create hotfix branch from `main`
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-security-fix
   ```
2. Fix critical issue
3. Create PR to `main`
4. Code review and approval required
5. Merge to `main` and tag hotfix release
6. Merge back to `develop`

## Commit Message Convention

Use conventional commits format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add user authentication endpoint
fix(frontend): resolve navigation menu bug
docs(readme): update installation instructions
```

## Code Review Guidelines

### What to Review
- Code functionality and logic
- Security implications
- Performance considerations
- Test coverage
- Documentation updates
- Error handling
- Logging and monitoring

### Review Process
1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one approval required
3. **Testing**: Feature must be tested in staging environment
4. **Documentation**: Code must be properly documented
5. **Security**: Security scan must pass

## Deployment Strategy

### Staging Deployments
- Automatic deployment on `develop` branch
- Used for integration testing
- Available at staging.autonomica.app

### Production Deployments
- Manual deployment from `main` branch
- Requires approval from maintainers
- Available at autonomica.app

### Rollback Strategy
- Automatic rollback on deployment failure
- Manual rollback capability for critical issues
- Database migration safety checks

## Environment Management

### Environment Variables
- Use `.env.example` files for documentation
- Store sensitive values in GitHub Secrets
- Use environment-specific configurations

### Configuration Management
- Version control configuration files
- Environment-specific overrides
- Feature flags for gradual rollouts

## Monitoring and Alerting

### Deployment Monitoring
- Health check endpoints
- Performance metrics
- Error tracking
- User experience monitoring

### Alerting
- Deployment failures
- Performance degradation
- Security incidents
- Service outages

## Best Practices

### General
- Keep branches short-lived (max 2 weeks)
- Regular merges from `develop` to feature branches
- Use descriptive branch names
- Write clear commit messages
- Update documentation with code changes

### Testing
- Write tests for new features
- Maintain test coverage above 80%
- Run tests locally before pushing
- Use staging environment for integration testing

### Security
- Regular security scans
- Dependency vulnerability checks
- Code security reviews
- Access control and permissions

## Tools and Integrations

### CI/CD
- GitHub Actions for automation
- Vercel for frontend deployment
- Railway for worker deployment
- Docker for containerization

### Code Quality
- ESLint for JavaScript/TypeScript
- Flake8 for Python
- Black for Python formatting
- Pre-commit hooks for consistency

### Testing
- Jest for frontend testing
- Pytest for backend testing
- Playwright for E2E testing
- Coverage reporting

## Troubleshooting

### Common Issues
- **Merge Conflicts**: Resolve conflicts locally before pushing
- **Failed Tests**: Fix issues before requesting review
- **Deployment Failures**: Check logs and rollback if necessary
- **Permission Issues**: Contact repository administrators

### Getting Help
- Check GitHub Issues for known problems
- Review CI/CD logs for error details
- Consult team members for guidance
- Document solutions for future reference
