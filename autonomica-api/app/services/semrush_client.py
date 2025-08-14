"""
SEMrush API Client for SEO research and keyword analysis.

This module provides a comprehensive interface to the SEMrush API with:
- Secure API key authentication
- Rate limiting and request throttling
- Comprehensive error handling
- Response caching
- Retry logic with exponential backoff
"""

import asyncio
import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode
import httpx
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.redis_service import RedisService


class SEMrushRateLimitError(Exception):
    """Raised when SEMrush API rate limit is exceeded."""
    pass


class SEMrushAuthenticationError(Exception):
    """Raised when SEMrush API authentication fails."""
    pass


class SEMrushAPIError(Exception):
    """Raised when SEMrush API returns an error."""
    pass


class KeywordData(BaseModel):
    """Model for keyword data returned by SEMrush API."""
    keyword: str = Field(..., description="The keyword term")
    search_volume: Optional[int] = Field(None, description="Monthly search volume")
    cpc: Optional[float] = Field(None, description="Cost per click in USD")
    competition: Optional[float] = Field(None, description="Competition level (0-1)")
    keyword_difficulty: Optional[int] = Field(None, description="Keyword difficulty score (0-100)")
    results_count: Optional[int] = Field(None, description="Number of search results")
    trend: Optional[List[int]] = Field(None, description="Monthly trend data")
    related_keywords: Optional[List[str]] = Field(None, description="Related keyword suggestions")
    serp_features: Optional[List[str]] = Field(None, description="SERP features present")
    source_url: Optional[str] = Field(None, description="Source URL for the data")
    created_at: Optional[str] = Field(None, description="Timestamp when data was collected")


class DomainData(BaseModel):
    """Model for domain data returned by SEMrush API."""
    domain: str = Field(..., description="The domain name")
    authority_score: Optional[int] = Field(None, description="Domain authority score")
    organic_keywords: Optional[int] = Field(None, description="Number of organic keywords")
    organic_traffic: Optional[int] = Field(None, description="Organic traffic volume")
    organic_cost: Optional[float] = Field(None, description="Organic traffic value")
    paid_keywords: Optional[int] = Field(None, description="Number of paid keywords")
    paid_traffic: Optional[int] = Field(None, description="Paid traffic volume")
    paid_cost: Optional[float] = Field(None, description="Paid traffic cost")
    backlinks: Optional[int] = Field(None, description="Number of backlinks")
    referring_domains: Optional[int] = Field(None, description="Number of referring domains")
    created_at: Optional[str] = Field(None, description="Timestamp when data was collected")


class CompetitorData(BaseModel):
    """Model for competitor data returned by SEMrush API."""
    domain: str = Field(..., description="Competitor domain name")
    overlap_score: Optional[float] = Field(None, description="Keyword overlap score")
    common_keywords: Optional[int] = Field(None, description="Number of common keywords")
    organic_keywords: Optional[int] = Field(None, description="Total organic keywords")
    organic_traffic: Optional[int] = Field(None, description="Organic traffic volume")
    authority_score: Optional[int] = Field(None, description="Domain authority score")
    created_at: Optional[str] = Field(None, description="Timestamp when data was collected")


class SEMrushClient:
    """
    SEMrush API client with authentication, rate limiting, and caching.
    
    Features:
    - Secure API key authentication
    - Rate limiting (100 requests/day free, 10,000/day paid)
    - Response caching with Redis
    - Automatic retry with exponential backoff
    - Comprehensive error handling
    """
    
    BASE_URL = "https://api.semrush.com"
    API_VERSION = "v3"
    
    def __init__(self, api_key: Optional[str] = None, redis_service: Optional[RedisService] = None):
        """
        Initialize SEMrush API client.
        
        Args:
            api_key: SEMrush API key (defaults to settings.SEMRUSH_API_KEY)
            redis_service: Redis service for caching (optional)
        """
        self.api_key = api_key or settings.SEMRUSH_API_KEY
        if not self.api_key:
            raise ValueError("SEMrush API key is required")
        
        self.redis_service = redis_service
        self.session: Optional[httpx.AsyncClient] = None
        self.rate_limit_remaining = 100  # Default free tier limit
        self.rate_limit_reset_time = 0
        self.request_count = 0
        self.last_request_time = 0
        
        # Rate limiting configuration
        self.max_requests_per_day = 100  # Will be updated based on plan
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0
        
        logger.info(f"SEMrush client initialized with API key: {self.api_key[:8]}...")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
    
    async def _create_session(self):
        """Create HTTP session with proper headers."""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "User-Agent": "Autonomica-SEMrush-Client/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )
            logger.debug("Created new HTTP session for SEMrush API")
    
    async def _close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.aclose()
            self.session = None
            logger.debug("Closed HTTP session for SEMrush API")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for API requests.
        
        Args:
            params: Request parameters
            
        Returns:
            HMAC signature string
        """
        # Sort parameters alphabetically
        sorted_params = dict(sorted(params.items()))
        
        # Create query string
        query_string = urlencode(sorted_params)
        
        # Generate HMAC signature
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        
        # Check if we need to reset daily counter
        if current_time > self.rate_limit_reset_time:
            self.request_count = 0
            self.rate_limit_reset_time = current_time + 86400  # 24 hours
        
        # Check daily limit
        if self.request_count >= self.max_requests_per_day:
            wait_time = self.rate_limit_reset_time - current_time
            raise SEMrushRateLimitError(
                f"Daily rate limit exceeded. Reset in {wait_time:.0f} seconds"
            )
        
        # Check minimum interval between requests
        if current_time - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval)
        
        self.request_count += 1
        self.last_request_time = current_time
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any], 
        use_cache: bool = True,
        cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Make authenticated request to SEMrush API with caching and retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Request parameters
            use_cache: Whether to use Redis caching
            cache_ttl: Cache TTL in seconds
            
        Returns:
            API response data
            
        Raises:
            SEMrushAuthenticationError: Authentication failed
            SEMrushRateLimitError: Rate limit exceeded
            SEMrushAPIError: API returned an error
        """
        await self._check_rate_limit()
        
        # Add authentication parameters
        params.update({
            "key": self.api_key,
            "database": "us",  # Default to US database
            "export_columns": "Dn,Kw,Po,Co,Tr,Tc,Co2,Tr2,Tc2,Lr,Ur,Ur2"  # Default columns
        })
        
        # Generate signature
        signature = self._generate_signature(params)
        params["signature"] = signature
        
        # Check cache first
        if use_cache and self.redis_service:
            cache_key = f"semrush:{endpoint}:{hash(json.dumps(params, sort_keys=True))}"
            cached_response = await self.redis_service.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for SEMrush request: {endpoint}")
                return json.loads(cached_response)
        
        # Make API request with retry logic
        for attempt in range(self.max_retries):
            try:
                url = f"{self.BASE_URL}/{endpoint}"
                
                logger.debug(f"Making SEMrush API request: {endpoint} (attempt {attempt + 1})")
                response = await self.session.post(url, data=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.base_delay))
                    logger.warning(f"Rate limited by SEMrush API. Retrying in {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    continue
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise SEMrushAuthenticationError("Invalid SEMrush API key")
                
                # Handle other HTTP errors
                response.raise_for_status()
                
                # Parse response
                response_data = response.text
                
                # SEMrush returns CSV format, convert to JSON
                if response_data.strip():
                    parsed_data = self._parse_csv_response(response_data)
                else:
                    parsed_data = {"data": [], "total": 0}
                
                # Cache successful response
                if use_cache and self.redis_service:
                    await self.redis_service.set(
                        cache_key, 
                        json.dumps(parsed_data), 
                        expire=cache_ttl
                    )
                
                logger.debug(f"SEMrush API request successful: {endpoint}")
                return parsed_data
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error, retry with exponential backoff
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"SEMrush API server error: {e}. Retrying in {delay} seconds")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Client error, don't retry
                    raise SEMrushAPIError(f"SEMrush API error: {e}")
            
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"SEMrush API request failed: {e}. Retrying in {delay} seconds")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise SEMrushAPIError(f"SEMrush API request failed after {self.max_retries} attempts: {e}")
        
        raise SEMrushAPIError("Maximum retry attempts exceeded")
    
    def _parse_csv_response(self, csv_data: str) -> Dict[str, Any]:
        """
        Parse SEMrush CSV response into structured data.
        
        Args:
            csv_data: Raw CSV response from SEMrush API
            
        Returns:
            Parsed data with headers and rows
        """
        lines = csv_data.strip().split('\n')
        if not lines:
            return {"data": [], "total": 0}
        
        # Parse headers
        headers = lines[0].split(';')
        
        # Parse data rows
        data = []
        for line in lines[1:]:
            if line.strip():
                values = line.split(';')
                row = {}
                for i, header in enumerate(headers):
                    if i < len(values):
                        row[header] = values[i].strip()
                    else:
                        row[header] = ""
                data.append(row)
        
        return {
            "data": data,
            "total": len(data),
            "headers": headers
        }
    
    async def get_keyword_overview(
        self, 
        keyword: str, 
        database: str = "us",
        use_cache: bool = True
    ) -> KeywordData:
        """
        Get comprehensive keyword overview data.
        
        Args:
            keyword: Target keyword
            database: Target database (us, uk, ca, ru, etc.)
            use_cache: Whether to use caching
            
        Returns:
            KeywordData object with comprehensive keyword information
        """
        endpoint = "analytics/overview"
        params = {
            "type": "phrase_this",
            "key": keyword,
            "database": database
        }
        
        response = await self._make_request(endpoint, params, use_cache=use_cache)
        
        if not response.get("data"):
            raise SEMrushAPIError(f"No data returned for keyword: {keyword}")
        
        # Parse the first result
        data = response["data"][0]
        
        return KeywordData(
            keyword=keyword,
            search_volume=int(data.get("Search Volume", 0)) if data.get("Search Volume") else None,
            cpc=float(data.get("CPC", 0)) if data.get("CPC") else None,
            competition=float(data.get("Competition", 0)) if data.get("Competition") else None,
            keyword_difficulty=int(data.get("Keyword Difficulty", 0)) if data.get("Keyword Difficulty") else None,
            results_count=int(data.get("Results", 0)) if data.get("Results") else None,
            source_url=f"https://www.semrush.com/analytics/overview/?q={keyword}&searchType=phrase",
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    async def get_domain_overview(
        self, 
        domain: str, 
        database: str = "us",
        use_cache: bool = True
    ) -> DomainData:
        """
        Get comprehensive domain overview data.
        
        Args:
            domain: Target domain
            database: Target database (us, uk, ca, ru, etc.)
            use_cache: Whether to use caching
            
        Returns:
            DomainData object with comprehensive domain information
        """
        endpoint = "domain/overview"
        params = {
            "key": domain,
            "database": database
        }
        
        response = await self._make_request(endpoint, params, use_cache=use_cache)
        
        if not response.get("data"):
            raise SEMrushAPIError(f"No data returned for domain: {domain}")
        
        # Parse the first result
        data = response["data"][0]
        
        return DomainData(
            domain=domain,
            authority_score=int(data.get("Authority Score", 0)) if data.get("Authority Score") else None,
            organic_keywords=int(data.get("Organic Keywords", 0)) if data.get("Organic Keywords") else None,
            organic_traffic=int(data.get("Organic Traffic", 0)) if data.get("Organic Traffic") else None,
            organic_cost=float(data.get("Organic Cost", 0)) if data.get("Organic Cost") else None,
            paid_keywords=int(data.get("Paid Keywords", 0)) if data.get("Paid Keywords") else None,
            paid_traffic=int(data.get("Paid Traffic", 0)) if data.get("Paid Traffic") else None,
            paid_cost=float(data.get("Paid Cost", 0)) if data.get("Paid Cost") else None,
            backlinks=int(data.get("Backlinks", 0)) if data.get("Backlinks") else None,
            referring_domains=int(data.get("Referring Domains", 0)) if data.get("Referring Domains") else None,
            source_url=f"https://www.semrush.com/analytics/overview/?q={domain}",
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    async def get_competitors(
        self, 
        domain: str, 
        database: str = "us",
        limit: int = 20,
        use_cache: bool = True
    ) -> List[CompetitorData]:
        """
        Get competitor analysis for a domain.
        
        Args:
            domain: Target domain
            database: Target database (us, uk, ca, ru, etc.)
            limit: Maximum number of competitors to return
            use_cache: Whether to use caching
            
        Returns:
            List of CompetitorData objects
        """
        endpoint = "analytics/competitors"
        params = {
            "key": domain,
            "database": database,
            "display_limit": str(limit)
        }
        
        response = await self._make_request(endpoint, params, use_cache=use_cache)
        
        competitors = []
        for data in response.get("data", [])[:limit]:
            competitor = CompetitorData(
                domain=data.get("Domain", ""),
                overlap_score=float(data.get("Overlap Score", 0)) if data.get("Overlap Score") else None,
                common_keywords=int(data.get("Common Keywords", 0)) if data.get("Common Keywords") else None,
                organic_keywords=int(data.get("Organic Keywords", 0)) if data.get("Organic Keywords") else None,
                organic_traffic=int(data.get("Organic Traffic", 0)) if data.get("Organic Traffic") else None,
                authority_score=int(data.get("Authority Score", 0)) if data.get("Authority Score") else None,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            competitors.append(competitor)
        
        return competitors
    
    async def get_keyword_suggestions(
        self, 
        seed_keyword: str, 
        database: str = "us",
        limit: int = 100,
        use_cache: bool = True
    ) -> List[KeywordData]:
        """
        Get keyword suggestions based on a seed keyword.
        
        Args:
            seed_keyword: Seed keyword for suggestions
            database: Target database (us, uk, ca, ru, etc.)
            limit: Maximum number of suggestions to return
            use_cache: Whether to use caching
            
        Returns:
            List of KeywordData objects with suggestions
        """
        endpoint = "analytics/keywords"
        params = {
            "type": "phrase_related",
            "key": seed_keyword,
            "database": database,
            "display_limit": str(limit)
        }
        
        response = await self._make_request(endpoint, params, use_cache=use_cache)
        
        suggestions = []
        for data in response.get("data", [])[:limit]:
            keyword_data = KeywordData(
                keyword=data.get("Keyword", ""),
                search_volume=int(data.get("Search Volume", 0)) if data.get("Search Volume") else None,
                cpc=float(data.get("CPC", 0)) if data.get("CPC") else None,
                competition=float(data.get("Competition", 0)) if data.get("Competition") else None,
                keyword_difficulty=int(data.get("Keyword Difficulty", 0)) if data.get("Keyword Difficulty") else None,
                results_count=int(data.get("Results", 0)) if data.get("Results") else None,
                source_url=f"https://www.semrush.com/analytics/overview/?q={data.get('Keyword', '')}",
                created_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            suggestions.append(keyword_data)
        
        return suggestions
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            "requests_remaining": self.max_requests_per_day - self.request_count,
            "requests_used": self.request_count,
            "daily_limit": self.max_requests_per_day,
            "reset_time": self.rate_limit_reset_time,
            "seconds_until_reset": max(0, self.rate_limit_reset_time - time.time())
        }
    
    async def update_rate_limit_info(self, remaining: int, reset_time: int):
        """
        Update rate limit information from API response headers.
        
        Args:
            remaining: Remaining requests
            reset_time: Time when rate limit resets
        """
        self.rate_limit_remaining = remaining
        self.rate_limit_reset_time = reset_time
        logger.debug(f"Updated rate limit: {remaining} requests remaining, reset at {reset_time}")


# Example usage and testing
async def test_semrush_client():
    """Test the SEMrush client functionality."""
    try:
        async with SEMrushClient() as client:
            # Test keyword overview
            keyword_data = await client.get_keyword_overview("digital marketing")
            print(f"Keyword: {keyword_data.keyword}")
            print(f"Search Volume: {keyword_data.search_volume}")
            print(f"CPC: ${keyword_data.cpc}")
            print(f"Difficulty: {keyword_data.keyword_difficulty}")
            
            # Test domain overview
            domain_data = await client.get_domain_overview("google.com")
            print(f"Domain: {domain_data.domain}")
            print(f"Authority: {domain_data.authority_score}")
            print(f"Organic Keywords: {domain_data.organic_keywords}")
            
            # Test rate limit status
            rate_limit = await client.get_rate_limit_status()
            print(f"Rate Limit Status: {rate_limit}")
            
    except Exception as e:
        logger.error(f"SEMrush client test failed: {e}")


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_semrush_client())