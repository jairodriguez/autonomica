"""
SEO Configuration for Autonomica API
Contains API keys, rate limits, and configuration settings for SEO services
"""

import os
from typing import Dict, Any
from pydantic_settings import BaseSettings

class SEOSettings(BaseSettings):
    """SEO service configuration settings"""
    
    # SEMrush API Configuration
    SEMRUSH_API_KEY: str = ""
    SEMRUSH_BASE_URL: str = "https://api.semrush.com"
    SEMRUSH_DATABASE: str = "us"  # Default database
    
    # Rate Limiting
    SEMRUSH_RATE_LIMIT: int = 100  # Requests per minute
    SEMRUSH_RATE_LIMIT_WINDOW: int = 60  # Seconds
    
    # Google APIs Configuration
    GOOGLE_API_KEY: str = ""
    GOOGLE_CUSTOM_SEARCH_ENGINE_ID: str = ""
    GOOGLE_SEARCH_QUOTA_LIMIT: int = 100  # Queries per day
    
    # Web Scraping Configuration
    SCRAPING_DELAY: float = 1.0  # Seconds between requests
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT: int = 30  # Seconds
    
    # Caching Configuration
    CACHE_TTL: int = 3600  # 1 hour in seconds
    CACHE_MAX_SIZE: int = 1000  # Maximum cached items
    
    # Analysis Configuration
    MAX_KEYWORDS_PER_ANALYSIS: int = 100
    MAX_COMPETITORS_PER_DOMAIN: int = 20
    KEYWORD_CLUSTERING_THRESHOLD: float = 0.7  # Similarity threshold
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }

# Create global settings instance
seo_settings = SEOSettings()

# Validate required settings
def validate_seo_config() -> Dict[str, Any]:
    """Validate SEO configuration and return status"""
    missing_keys = []
    
    if not seo_settings.SEMRUSH_API_KEY:
        missing_keys.append("SEMRUSH_API_KEY")
    
    if not seo_settings.GOOGLE_API_KEY:
        missing_keys.append("GOOGLE_API_KEY")
    
    return {
        "valid": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "semrush_configured": bool(seo_settings.SEMRUSH_API_KEY),
        "google_configured": bool(seo_settings.GOOGLE_API_KEY),
        "rate_limits": {
            "semrush_per_minute": seo_settings.SEMRUSH_RATE_LIMIT,
            "google_per_day": seo_settings.GOOGLE_SEARCH_QUOTA_LIMIT
        }
    }
