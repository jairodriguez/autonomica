"""
Staging Environment Configuration Template
Copy this file to .env.staging and fill in the actual values
"""

import os
from typing import Optional

class StagingConfig:
    """Staging environment configuration"""
    
    # Environment
    ENVIRONMENT = "staging"
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    DATABASE_URL = "postgresql://staging_user:staging_password@staging-db.autonomica.app:5432/autonomica_staging"
    DATABASE_POOL_SIZE = 10
    DATABASE_MAX_OVERFLOW = 20
    
    # Redis Configuration
    REDIS_URL = "redis://staging-redis.autonomica.app:6379/0"
    REDIS_PASSWORD = "staging_redis_password"
    
    # Authentication (Clerk)
    CLERK_SECRET_KEY = "sk_test_staging_secret_key_here"
    CLERK_PUBLISHABLE_KEY = "pk_test_staging_publishable_key_here"
    CLERK_JWT_ISSUER = "https://clerk.staging.autonomica.app"
    
    # AI Service API Keys
    OPENAI_API_KEY = "sk-staging-openai-key-here"
    ANTHROPIC_API_KEY = "sk-ant-staging-anthropic-key-here"
    GOOGLE_API_KEY = "staging-google-api-key-here"
    MISTRAL_API_KEY = "staging-mistral-api-key-here"
    
    # External Services
    SEARCH_ENGINE_API_KEY = "staging-search-engine-key-here"
    ANALYTICS_API_KEY = "staging-analytics-key-here"
    
    # Security
    SECRET_KEY = "staging-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # CORS
    CORS_ORIGINS = [
        "https://staging.autonomica.app",
        "https://staging-admin.autonomica.app",
        "http://localhost:3000",  # Local development
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 100
    RATE_LIMIT_PER_HOUR = 1000
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"
    
    # Monitoring
    SENTRY_DSN = "https://staging-sentry-dsn-here"
    NEW_RELIC_LICENSE_KEY = "staging-new-relic-key-here"
    
    # Performance
    CACHE_TTL = 300  # 5 minutes
    SESSION_TIMEOUT = 3600  # 1 hour
    
    # Feature Flags
    FEATURE_AGENT_MANAGEMENT = True
    FEATURE_PROJECT_MANAGEMENT = True
    FEATURE_ANALYTICS = True
    FEATURE_SEO_TOOLS = True
    FEATURE_ADVANCED_REPORTING = False
    
    # Testing
    TEST_DATABASE_URL = "sqlite:///./test_staging.db"
    TEST_REDIS_URL = "redis://localhost:6379/1"
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL from environment or default"""
        return os.getenv("DATABASE_URL", cls.DATABASE_URL)
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis URL from environment or default"""
        return os.getenv("REDIS_URL", cls.REDIS_URL)
    
    @classmethod
    def get_clerk_secret_key(cls) -> str:
        """Get Clerk secret key from environment or default"""
        return os.getenv("CLERK_SECRET_KEY", cls.CLERK_SECRET_KEY)
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key from environment or default"""
        return os.getenv("OPENAI_API_KEY", cls.OPENAI_API_KEY)
    
    @classmethod
    def get_anthropic_api_key(cls) -> Optional[str]:
        """Get Anthropic API key from environment or default"""
        return os.getenv("ANTHROPIC_API_KEY", cls.ANTHROPIC_API_KEY)
    
    @classmethod
    def get_google_api_key(cls) -> Optional[str]:
        """Get Google API key from environment or default"""
        return os.getenv("GOOGLE_API_KEY", cls.GOOGLE_API_KEY)
    
    @classmethod
    def get_mistral_api_key(cls) -> Optional[str]:
        """Get Mistral API key from environment or default"""
        return os.getenv("MISTRAL_API_KEY", cls.MISTRAL_API_KEY)

# Usage:
# 1. Copy this file to .env.staging
# 2. Replace placeholder values with actual staging environment values
# 3. Ensure .env.staging is in .gitignore
# 4. Import and use in your FastAPI application
# 5. Override with environment variables as needed

