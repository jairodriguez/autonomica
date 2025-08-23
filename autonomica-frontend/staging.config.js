/**
 * Staging Environment Configuration Template
 * Copy this file to .env.staging and fill in the actual values
 */

module.exports = {
  // Staging Environment Configuration
  NODE_ENV: 'production',
  NEXT_PUBLIC_ENVIRONMENT: 'staging',

  // API Configuration
  NEXT_PUBLIC_API_URL: 'https://staging-api.autonomica.app',
  NEXT_PUBLIC_API_VERSION: 'v1',

  // Authentication (Clerk)
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: 'pk_test_staging_key_here',
  NEXT_PUBLIC_CLERK_SIGN_IN_URL: '/sign-in',
  NEXT_PUBLIC_CLERK_SIGN_UP_URL: '/sign-up',
  NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL: '/dashboard',
  NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL: '/onboarding',

  // Analytics
  NEXT_PUBLIC_ANALYTICS_ID: 'G-STAGING-ANALYTICS-ID',
  NEXT_PUBLIC_ANALYTICS_ENABLED: true,

  // Feature Flags
  NEXT_PUBLIC_FEATURE_FLAGS_ENABLED: true,
  NEXT_PUBLIC_FEATURE_AGENT_MANAGEMENT: true,
  NEXT_PUBLIC_FEATURE_PROJECT_MANAGEMENT: true,
  NEXT_PUBLIC_FEATURE_ANALYTICS: true,
  NEXT_PUBLIC_FEATURE_SEO_TOOLS: true,

  // External Services
  NEXT_PUBLIC_SUPPORT_EMAIL: 'support-staging@autonomica.app',
  NEXT_PUBLIC_DOCS_URL: 'https://docs-staging.autonomica.app',

  // Performance
  NEXT_PUBLIC_PERFORMANCE_MONITORING: true,
  NEXT_PUBLIC_ERROR_TRACKING: true,

  // Development Tools (disabled in staging)
  NEXT_PUBLIC_DEBUG_MODE: false,
  NEXT_PUBLIC_SHOW_DEV_TOOLS: false,
}

// Usage:
// 1. Copy this file to .env.staging
// 2. Replace placeholder values with actual staging environment values
// 3. Ensure .env.staging is in .gitignore
// 4. Use in deployment scripts and CI/CD pipelines

