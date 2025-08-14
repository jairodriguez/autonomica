# Git Branching Strategy

## Overview
This document outlines the Git branching strategy and workflow for the Autonomica project, following industry best practices for continuous integration and deployment.

## Branch Structure

### Main Branches
- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features, staging deployments

### Supporting Branches
- **`feature/*`** - Feature development branches (e.g., `feature/ci-cd-pipeline`)
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation branches

## Branch Protection Rules

### Main Branch (`main`)
- **Require pull request reviews**: 2 approvals minimum
- **Require status checks to pass**: All CI/CD checks must pass
- **Require branches to be up to date**: Must be rebased on latest main
- **Restrict pushes**: No direct pushes, only via pull requests
- **Require linear history**: No merge commits, only squash merges

### Develop Branch (`develop`)
- **Require pull request reviews**: 1 approval minimum
- **Require status checks to pass**: All CI/CD checks must pass
- **Allow force pushes**: Only for maintainers
- **Require branches to be up to date**: Must be rebased on latest develop

## Workflow

### Feature Development
1. Create feature branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/feature-name
   ```

2. Develop and commit changes
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

3. Push feature branch and create pull request
   ```bash
   git push -u origin feature/feature-name
   ```

4. Create pull request to `develop` branch
   - Ensure all CI/CD checks pass
   - Get code review approval
   - Merge using squash merge

### Release Process
1. Create release branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/version-number
   ```

2. Make release-specific changes (version bumps, changelog)
3. Create pull request to `main` and `develop`
4. Merge to `main` for production deployment
5. Merge back to `develop` to include release changes

### Hotfix Process
1. Create hotfix branch from `main`
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-fix
   ```

2. Fix the critical issue
3. Create pull request to `main` and `develop`
4. Merge to `main` for immediate production deployment
5. Merge back to `develop` to include hotfix

## Commit Message Convention

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies, etc.

### Examples
```
feat(auth): add Clerk authentication middleware
fix(api): resolve chat endpoint parameter bug
docs(readme): update deployment instructions
style(components): fix ESLint formatting issues
```

## CI/CD Integration

### Pull Request Requirements
- All automated tests must pass
- Code coverage must meet minimum thresholds
- Linting and formatting checks must pass
- Security scans must pass
- Performance tests must meet benchmarks

### Deployment Gates
- **Staging**: Automatic deployment from `develop` branch
- **Production**: Manual approval required for `main` branch deployments
- **Rollback**: Automatic rollback on deployment failures

## Best Practices

1. **Keep branches short-lived**: Feature branches should be merged within 1-2 weeks
2. **Regular integration**: Merge `develop` into feature branches regularly
3. **Clear descriptions**: Write descriptive commit messages and pull request descriptions
4. **Code review**: Always get code review before merging
5. **Testing**: Ensure all tests pass before creating pull requests
6. **Documentation**: Update documentation for any user-facing changes

## Emergency Procedures

### Critical Production Issues
1. Create hotfix branch from `main`
2. Fix the issue with minimal changes
3. Test thoroughly in staging environment
4. Deploy to production immediately
5. Create proper pull request for documentation

### Rollback Process
1. Identify the problematic deployment
2. Revert to previous stable commit
3. Deploy rollback immediately
4. Investigate root cause
5. Create fix in proper feature branch

## Tools and Automation

- **GitHub Actions**: CI/CD pipeline automation
- **Branch Protection**: Automated enforcement of rules
- **Status Checks**: Automated quality gates
- **Dependabot**: Automated dependency updates
- **CodeQL**: Automated security scanning

## Maintenance

This branching strategy should be reviewed and updated quarterly to ensure it continues to meet the project's needs and industry best practices.