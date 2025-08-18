# GitHub Actions Status Badges

These badges can be embedded in your README.md to show the current status of your CI/CD pipeline.

## Main CI/CD Pipeline
```markdown
![CI/CD Pipeline](https://github.com/jairodriguez/autonomica/workflows/CI%3ACD%20Pipeline/badge.svg)
```

## Security Scanning
```markdown
![Security Scan](https://github.com/jairodriguez/autonomica/workflows/Security%20Scanning/badge.svg)
```

## Performance Testing
```markdown
![Performance Test](https://github.com/jairodriguez/autonomica/workflows/Performance%20Testing/badge.svg)
```

## Dependency Caching
```markdown
![Dependency Cache](https://github.com/jairodriguez/autonomica/workflows/Dependency%20Caching/badge.svg)
```

## All Workflows
```markdown
![CI/CD Pipeline](https://github.com/jairodriguez/autonomica/workflows/CI%3ACD%20Pipeline/badge.svg)
![Security Scan](https://github.com/jairodriguez/autonomica/workflows/Security%20Scanning/badge.svg)
![Performance Test](https://github.com/jairodriguez/autonomica/workflows/Performance%20Testing/badge.svg)
![Dependency Cache](https://github.com/jairodriguez/autonomica/workflows/Dependency%20Caching/badge.svg)
```

## Code Quality Badges
```markdown
![Code Coverage](https://codecov.io/gh/jairodriguez/autonomica/branch/main/graph/badge.svg)
![Maintainability](https://api.codeclimate.com/v1/badges/maintainability)
![Security Rating](https://api.codeclimate.com/v1/badges/security)
```

## Deployment Status
```markdown
![Vercel](https://vercel.com/button)
![Railway](https://railway.app/button.svg)
```

## Usage Instructions

1. Copy the desired badge markdown
2. Paste it into your README.md file
3. The badge will automatically update based on workflow status
4. Click on the badge to view detailed workflow information

## Badge Status Colors

- **Green**: All checks passed
- **Yellow**: Some checks failed but not critical
- **Red**: Critical checks failed
- **Gray**: Workflow not running or status unknown

## Customization

You can customize badge appearance by adding query parameters:

```markdown
![CI/CD Pipeline](https://github.com/jairodriguez/autonomica/workflows/CI%3ACD%20Pipeline/badge.svg?style=flat-square&label=Build%20Status)
```

## Troubleshooting

If badges don't appear:
1. Ensure the workflow file exists in `.github/workflows/`
2. Check that the workflow has run at least once
3. Verify the repository name in the badge URL
4. Ensure the workflow name matches exactly (including URL encoding)
