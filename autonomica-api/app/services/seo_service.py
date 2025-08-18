"""
SEO Service Module for Autonomica API
Handles SEMrush API integration, keyword research, and competitor analysis
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import asyncio
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class KeywordRecord:
    """Data structure for keyword research results"""
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    keyword_difficulty: Optional[int] = None
    competition: Optional[float] = None
    source_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class DomainAnalysis:
    """Data structure for domain analysis results"""
    domain: str
    authority_score: Optional[int] = None
    organic_keywords: Optional[int] = None
    organic_traffic: Optional[int] = None
    backlinks: Optional[int] = None
    referring_domains: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class CompetitorAnalysis:
    """Data structure for competitor analysis results"""
    keyword: str
    competitors: List[Dict[str, Any]]
    serp_features: List[str]
    featured_snippets: List[Dict[str, Any]]
    paa_boxes: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SEMrushAPIError(Exception):
    """Custom exception for SEMrush API errors"""
    pass


class RateLimitExceeded(Exception):
    """Exception raised when API rate limit is exceeded"""
    pass


class SEMrushAPIClient:
    """
    SEMrush API client with authentication, rate limiting, and error handling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SEMrush API client
        
        Args:
            api_key: SEMrush API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("SEMRUSH_API_KEY")
        if not self.api_key:
            raise ValueError("SEMrush API key is required")
        
        # API configuration
        self.base_url = "https://api.semrush.com"
        self.api_version = "v3"
        
        # Rate limiting configuration
        self.requests_per_day = 1000  # Pro plan default
        self.requests_per_minute = 10
        self.request_history: List[datetime] = []
        
        # Cache configuration
        self.cache_duration = timedelta(hours=24)
        self.response_cache: Dict[str, Tuple[Any, datetime]] = {}
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Autonomica/1.0 (+https://autonomica.ai)",
                "Accept": "application/json"
            }
        )
        
        logger.info(f"SEMrush API client initialized with key: {self.api_key[:8]}...")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    def _check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits
        
        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.utcnow()
        
        # Remove old requests from history
        self.request_history = [
            req_time for req_time in self.request_history
            if now - req_time < timedelta(days=1)
        ]
        
        # Check daily limit
        if len(self.request_history) >= self.requests_per_day:
            logger.warning("Daily rate limit exceeded")
            return False
        
        # Check minute limit
        recent_requests = [
            req_time for req_time in self.request_history
            if now - req_time < timedelta(minutes=1)
        ]
        
        if len(recent_requests) >= self.requests_per_minute:
            logger.warning("Minute rate limit exceeded")
            return False
        
        return True
    
    def _add_request_to_history(self):
        """Add current request to history"""
        self.request_history.append(datetime.utcnow())
    
    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key for request
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Cache key string
        """
        # Sort parameters for consistent cache keys
        sorted_params = sorted(params.items())
        param_string = json.dumps(sorted_params, sort_keys=True)
        
        # Create hash of endpoint and parameters
        cache_string = f"{endpoint}:{param_string}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached response is still valid
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.response_cache:
            return False
        
        _, timestamp = self.response_cache[cache_key]
        return datetime.utcnow() - timestamp < self.cache_duration
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Make authenticated request to SEMrush API
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            use_cache: Whether to use caching
            
        Returns:
            API response data
            
        Raises:
            RateLimitExceeded: When rate limit is exceeded
            SEMrushAPIError: When API returns an error
        """
        # Check rate limiting
        if not self._check_rate_limit():
            raise RateLimitExceeded("API rate limit exceeded")
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(endpoint, params)
            if self._is_cache_valid(cache_key):
                logger.info(f"Returning cached response for {endpoint}")
                return self.response_cache[cache_key][0]
        
        # Prepare request
        request_params = {
            "key": self.api_key,
            "database": "us",  # Default to US database
            **params
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            # Add request to history
            self._add_request_to_history()
            
            # Make request
            logger.info(f"Making request to {endpoint} with params: {params}")
            response = await self.client.get(url, params=request_params)
            
            # Check response status
            if response.status_code == 429:
                raise RateLimitExceeded("Rate limit exceeded by API")
            elif response.status_code != 200:
                raise SEMrushAPIError(f"API request failed: {response.status_code}")
            
            # Parse response
            data = response.json()
            
            # Check for API errors
            if "error" in data:
                raise SEMrushAPIError(f"SEMrush API error: {data['error']}")
            
            # Cache successful response
            if use_cache:
                cache_key = self._generate_cache_key(endpoint, params)
                self.response_cache[cache_key] = (data, datetime.utcnow())
            
            return data
            
        except httpx.TimeoutException:
            logger.error(f"Request timeout for {endpoint}")
            raise SEMrushAPIError("Request timeout")
        except httpx.RequestError as e:
            logger.error(f"Request error for {endpoint}: {e}")
            raise SEMrushAPIError(f"Request failed: {e}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {endpoint}")
            raise SEMrushAPIError("Invalid response format")
    
    async def get_domain_overview(self, domain: str) -> DomainAnalysis:
        """
        Get comprehensive domain overview
        
        Args:
            domain: Domain to analyze
            
        Returns:
            DomainAnalysis object with domain metrics
        """
        try:
            data = await self._make_request(
                "analytics/overview",
                {"target": domain}
            )
            
            # Parse response data
            if data.get("data") and len(data["data"]) > 0:
                domain_data = data["data"][0]
                
                return DomainAnalysis(
                    domain=domain,
                    authority_score=domain_data.get("authority_score"),
                    organic_keywords=domain_data.get("organic_keywords"),
                    organic_traffic=domain_data.get("organic_traffic"),
                    backlinks=domain_data.get("backlinks"),
                    referring_domains=domain_data.get("referring_domains")
                )
            else:
                raise SEMrushAPIError("No domain data returned")
                
        except Exception as e:
            logger.error(f"Error getting domain overview for {domain}: {e}")
            raise
    
    async def get_keyword_analysis(
        self, 
        keyword: str, 
        database: str = "us"
    ) -> KeywordRecord:
        """
        Get keyword analysis data
        
        Args:
            keyword: Keyword to analyze
            database: Target database (us, uk, ca, etc.)
            
        Returns:
            KeywordRecord object with keyword metrics
        """
        try:
            data = await self._make_request(
                "analytics/keyword",
                {
                    "target": keyword,
                    "database": database
                }
            )
            
            # Parse response data
            if data.get("data") and len(data["data"]) > 0:
                keyword_data = data["data"][0]
                
                return KeywordRecord(
                    keyword=keyword,
                    search_volume=keyword_data.get("search_volume"),
                    cpc=keyword_data.get("cpc"),
                    keyword_difficulty=keyword_data.get("keyword_difficulty"),
                    competition=keyword_data.get("competition"),
                    source_url=f"https://www.semrush.com/analytics/keywordoverview/?q={keyword}"
                )
            else:
                raise SEMrushAPIError("No keyword data returned")
                
        except Exception as e:
            logger.error(f"Error getting keyword analysis for {keyword}: {e}")
            raise
    
    async def get_competitor_analysis(
        self, 
        keyword: str,
        database: str = "us"
    ) -> CompetitorAnalysis:
        """
        Get competitor analysis for a keyword
        
        Args:
            keyword: Keyword to analyze
            database: Target database
            
        Returns:
            CompetitorAnalysis object with competitor data
        """
        try:
            data = await self._make_request(
                "analytics/competitors",
                {
                    "target": keyword,
                    "database": database
                }
            )
            
            # Parse response data
            competitors = []
            serp_features = []
            featured_snippets = []
            paa_boxes = []
            
            if data.get("data"):
                for item in data["data"]:
                    competitors.append({
                        "domain": item.get("domain"),
                        "position": item.get("position"),
                        "title": item.get("title"),
                        "url": item.get("url")
                    })
                    
                    # Extract SERP features
                    if item.get("featured_snippet"):
                        featured_snippets.append({
                            "domain": item.get("domain"),
                            "snippet": item.get("featured_snippet")
                        })
                    
                    if item.get("paa_box"):
                        paa_boxes.append({
                            "domain": item.get("domain"),
                            "question": item.get("paa_box")
                        })
            
            return CompetitorAnalysis(
                keyword=keyword,
                competitors=competitors,
                serp_features=serp_features,
                featured_snippets=featured_snippets,
                paa_boxes=paa_boxes
            )
            
        except Exception as e:
            logger.error(f"Error getting competitor analysis for {keyword}: {e}")
            raise
    
    async def get_related_keywords(
        self, 
        keyword: str,
        database: str = "us",
        limit: int = 20
    ) -> List[KeywordRecord]:
        """
        Get related keywords
        
        Args:
            keyword: Seed keyword
            database: Target database
            limit: Maximum number of keywords to return
            
        Returns:
            List of KeywordRecord objects
        """
        try:
            data = await self._make_request(
                "analytics/related_keywords",
                {
                    "target": keyword,
                    "database": database,
                    "limit": limit
                }
            )
            
            keywords = []
            if data.get("data"):
                for item in data["data"]:
                    keywords.append(KeywordRecord(
                        keyword=item.get("keyword"),
                        search_volume=item.get("search_volume"),
                        cpc=item.get("cpc"),
                        keyword_difficulty=item.get("keyword_difficulty"),
                        competition=item.get("competition")
                    ))
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error getting related keywords for {keyword}: {e}")
            raise
    
    async def get_domain_keywords(
        self, 
        domain: str,
        database: str = "us",
        limit: int = 100
    ) -> List[KeywordRecord]:
        """
        Get keywords that a domain ranks for
        
        Args:
            domain: Domain to analyze
            database: Target database
            limit: Maximum number of keywords to return
            
        Returns:
            List of KeywordRecord objects
        """
        try:
            data = await self._make_request(
                "analytics/domain_keywords",
                {
                    "target": domain,
                    "database": database,
                    "limit": limit
                }
            )
            
            keywords = []
            if data.get("data"):
                for item in data["data"]:
                    keywords.append(KeywordRecord(
                        keyword=item.get("keyword"),
                        search_volume=item.get("search_volume"),
                        cpc=item.get("cpc"),
                        keyword_difficulty=item.get("keyword_difficulty"),
                        competition=item.get("competition")
                    ))
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error getting domain keywords for {domain}: {e}")
            raise
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status
        
        Returns:
            Dictionary with rate limit information
        """
        now = datetime.utcnow()
        
        # Daily requests
        daily_requests = len([
            req_time for req_time in self.request_history
            if now - req_time < timedelta(days=1)
        ])
        
        # Minute requests
        minute_requests = len([
            req_time for req_time in self.request_history
            if now - req_time < timedelta(minutes=1)
        ])
        
        return {
            "daily_requests": daily_requests,
            "daily_limit": self.requests_per_day,
            "daily_remaining": self.requests_per_day - daily_requests,
            "minute_requests": minute_requests,
            "minute_limit": self.requests_per_minute,
            "minute_remaining": self.requests_per_minute - minute_requests,
            "cache_size": len(self.response_cache)
        }
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        logger.info("Response cache cleared")


class SEOService:
    """
    High-level SEO service that coordinates API calls and data processing
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SEO service
        
        Args:
            api_key: SEMrush API key
        """
        self.api_client = SEMrushAPIClient(api_key)
        logger.info("SEO service initialized")
    
    async def analyze_keyword(
        self, 
        keyword: str,
        include_competitors: bool = True,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive keyword analysis
        
        Args:
            keyword: Keyword to analyze
            include_competitors: Whether to include competitor analysis
            include_related: Whether to include related keywords
            
        Returns:
            Comprehensive keyword analysis data
        """
        try:
            # Get basic keyword data
            keyword_data = await self.api_client.get_keyword_analysis(keyword)
            
            result = {
                "keyword": keyword_data,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add competitor analysis if requested
            if include_competitors:
                try:
                    competitor_data = await self.api_client.get_competitor_analysis(keyword)
                    result["competitors"] = competitor_data
                except Exception as e:
                    logger.warning(f"Failed to get competitor analysis: {e}")
                    result["competitors"] = None
            
            # Add related keywords if requested
            if include_related:
                try:
                    related_keywords = await self.api_client.get_related_keywords(keyword, limit=10)
                    result["related_keywords"] = related_keywords
                except Exception as e:
                    logger.warning(f"Failed to get related keywords: {e}")
                    result["related_keywords"] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive keyword analysis: {e}")
            raise
    
    async def analyze_domain(
        self, 
        domain: str,
        include_keywords: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive domain analysis
        
        Args:
            domain: Domain to analyze
            include_keywords: Whether to include top keywords
            
        Returns:
            Comprehensive domain analysis data
        """
        try:
            # Get domain overview
            domain_data = await self.api_client.get_domain_overview(domain)
            
            result = {
                "domain": domain_data,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add top keywords if requested
            if include_keywords:
                try:
                    keywords = await self.api_client.get_domain_keywords(domain, limit=20)
                    result["top_keywords"] = keywords
                except Exception as e:
                    logger.warning(f"Failed to get domain keywords: {e}")
                    result["top_keywords"] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive domain analysis: {e}")
            raise
    
    async def batch_keyword_analysis(
        self, 
        keywords: List[str],
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze multiple keywords concurrently
        
        Args:
            keywords: List of keywords to analyze
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            Batch analysis results
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def analyze_single_keyword(keyword: str) -> Tuple[str, Any]:
                async with semaphore:
                    try:
                        result = await self.analyze_keyword(keyword, include_competitors=False, include_related=False)
                        return keyword, result
                    except Exception as e:
                        logger.error(f"Error analyzing keyword {keyword}: {e}")
                        return keyword, {"error": str(e)}
            
            # Create tasks for all keywords
            tasks = [analyze_single_keyword(keyword) for keyword in keywords]
            
            # Execute tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            analysis_results = {}
            for keyword, result in results:
                if isinstance(result, Exception):
                    analysis_results[keyword] = {"error": str(result)}
                else:
                    analysis_results[keyword] = result
            
            return {
                "keywords_analyzed": len(keywords),
                "successful_analyses": len([r for r in analysis_results.values() if "error" not in r]),
                "failed_analyses": len([r for r in analysis_results.values() if "error" in r]),
                "results": analysis_results,
                "batch_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch keyword analysis: {e}")
            raise
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get SEO service status and health information
        
        Returns:
            Service status information
        """
        try:
            rate_limit_status = self.api_client.get_rate_limit_status()
            
            return {
                "status": "healthy",
                "api_client": "SEMrush",
                "rate_limits": rate_limit_status,
                "cache_info": {
                    "cache_size": rate_limit_status["cache_size"],
                    "cache_enabled": True
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close the service and cleanup resources"""
        await self.api_client.close()
        logger.info("SEO service closed")


# Factory function for creating SEO service
def create_seo_service(api_key: Optional[str] = None) -> SEOService:
    """
    Create and configure SEO service
    
    Args:
        api_key: Optional SEMrush API key
        
    Returns:
        Configured SEO service instance
    """
    return SEOService(api_key)
