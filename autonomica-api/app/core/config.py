"""
Configuration settings for Autonomica API
"""

import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    """Application settings"""
    
    # API Configuration
    API_VERSION: str = "1.0.0"
    PROJECT_NAME: str = "Autonomica API"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # CORS Configuration
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "https://autonomica.vercel.app",
            "https://*.vercel.app"
        ],
        env="ALLOWED_ORIGINS",
        description="Comma-separated list of allowed origins"
    )
    
    @field_validator('ALLOWED_ORIGINS', mode='after')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from environment variable or use default"""
        if isinstance(v, str):
            if v.strip() == "":
                return [
                    "http://localhost:3000",
                    "http://localhost:3001", 
                    "https://autonomica.vercel.app",
                    "https://*.vercel.app"
                ]
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # AI/LLM Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    AI_MODEL: str = Field(default="gpt-4-turbo", env="AI_MODEL")
    
    # Agent Configuration
    MAX_AGENTS: int = Field(default=10, env="MAX_AGENTS")
    AGENT_TIMEOUT_SECONDS: int = Field(default=300, env="AGENT_TIMEOUT_SECONDS")
    
    # OWL Framework Configuration
    OWL_WORKSPACE_PATH: str = Field(default="./owl_workspace", env="OWL_WORKSPACE_PATH")
    OWL_LOG_LEVEL: str = Field(default="INFO", env="OWL_LOG_LEVEL")
    OWL_MAX_CONCURRENT_WORKFLOWS: int = Field(default=5, env="OWL_MAX_CONCURRENT_WORKFLOWS")
    
    # Vector Storage Configuration
    VECTOR_DIMENSION: int = Field(default=768, env="VECTOR_DIMENSION")
    FAISS_INDEX_PATH: str = Field(default="./faiss_index", env="FAISS_INDEX_PATH")
    
    # Task Queue Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    CLERK_SECRET_KEY: Optional[str] = Field(default=None, env="CLERK_SECRET_KEY")
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Development Configuration
    RELOAD: bool = Field(default=True, env="RELOAD")
    LOG_LEVEL: str = Field(default="info", env="LOG_LEVEL")
    
    # Pydantic v2 style config is provided via model_config above


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


# Validate required settings
def validate_settings():
    """Validate that required settings are present"""
    errors = []
    
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        errors.append("At least one AI provider API key must be set (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    
    if os.getenv("ENVIRONMENT") == "production":
        if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("SECRET_KEY must be set to a secure value in production")
        if not settings.CLERK_SECRET_KEY:
            errors.append("CLERK_SECRET_KEY must be set in production")
    
    if errors:
        raise ValueError(f"Configuration errors: {'; '.join(errors)}")


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    RELOAD: bool = True
    LOG_LEVEL: str = "debug"


class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    RELOAD: bool = False
    LOG_LEVEL: str = "info"
    ALLOWED_ORIGINS: List[str] = [
        "https://autonomica.vercel.app",
        "https://autonomica.com"
    ]


def get_environment_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    else:
        return DevelopmentSettings() 