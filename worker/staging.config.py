"""
Staging Environment Configuration Template for Worker Pod
Copy this file to .env.staging and fill in the actual values
"""

import os
from typing import Optional

class WorkerStagingConfig:
    """Staging environment configuration for worker pod"""
    
    # Environment
    ENVIRONMENT = "staging"
    DEBUG = False
    TESTING = False
    
    # Worker Configuration
    WORKER_NAME = "staging-worker-1"
    WORKER_POOL_SIZE = 5
    MAX_CONCURRENT_TASKS = 10
    TASK_TIMEOUT = 300  # 5 minutes
    
    # Database Configuration
    DATABASE_URL = "postgresql://staging_user:staging_password@staging-db.autonomica.app:5432/autonomica_staging"
    DATABASE_POOL_SIZE = 5
    DATABASE_MAX_OVERFLOW = 10
    
    # Redis Configuration
    REDIS_URL = "redis://staging-redis.autonomica.app:6379/0"
    REDIS_PASSWORD = "staging_redis_password"
    REDIS_DB = 0
    
    # Queue Configuration
    QUEUE_NAME = "staging_task_queue"
    PRIORITY_QUEUE_NAME = "staging_priority_queue"
    DEAD_LETTER_QUEUE = "staging_dead_letter_queue"
    
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
    SEO_TOOLS_API_KEY = "staging-seo-tools-key-here"
    
    # Task Processing
    TASK_RETRY_LIMIT = 3
    TASK_RETRY_DELAY = 60  # 1 minute
    TASK_MAX_EXECUTION_TIME = 1800  # 30 minutes
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 50
    RATE_LIMIT_PER_HOUR = 500
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "json"
    LOG_FILE = "/var/log/worker/staging.log"
    
    # Monitoring
    SENTRY_DSN = "https://staging-sentry-dsn-here"
    NEW_RELIC_LICENSE_KEY = "staging-new-relic-key-here"
    METRICS_ENDPOINT = "https://staging-metrics.autonomica.app"
    
    # Performance
    CACHE_TTL = 300  # 5 minutes
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_MEMORY_USAGE = "2GB"
    MAX_CPU_USAGE = "80%"
    
    # Feature Flags
    FEATURE_AGENT_MANAGEMENT = True
    FEATURE_PROJECT_MANAGEMENT = True
    FEATURE_ANALYTICS = True
    FEATURE_SEO_TOOLS = True
    FEATURE_ADVANCED_REPORTING = False
    FEATURE_BATCH_PROCESSING = True
    
    # Testing
    TEST_DATABASE_URL = "sqlite:///./test_staging_worker.db"
    TEST_REDIS_URL = "redis://localhost:6379/2"
    
    # Health Check
    HEALTH_CHECK_INTERVAL = 30  # seconds
    HEALTH_CHECK_TIMEOUT = 10   # seconds
    
    # Scaling
    AUTO_SCALE_ENABLED = True
    MIN_WORKERS = 2
    MAX_WORKERS = 10
    SCALE_UP_THRESHOLD = 80  # CPU usage percentage
    SCALE_DOWN_THRESHOLD = 20  # CPU usage percentage
    
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
    
    @classmethod
    def get_worker_name(cls) -> str:
        """Get worker name from environment or default"""
        return os.getenv("WORKER_NAME", cls.WORKER_NAME)
    
    @classmethod
    def get_queue_name(cls) -> str:
        """Get queue name from environment or default"""
        return os.getenv("QUEUE_NAME", cls.QUEUE_NAME)

# Usage:
# 1. Copy this file to .env.staging
# 2. Replace placeholder values with actual staging environment values
# 3. Ensure .env.staging is in .gitignore
# 4. Import and use in your worker application
# 5. Override with environment variables as needed
# 6. Use in Docker containers and deployment scripts
