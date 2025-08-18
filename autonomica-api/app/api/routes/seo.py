"""
SEO API Routes for Autonomica API
Provides endpoints for keyword research, domain analysis, and competitor research
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.seo_service import create_seo_service, SEOService

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/seo", tags=["SEO"])

# Pydantic models for request/response
class KeywordAnalysisRequest(BaseModel):
    keyword: str = Field(..., description="Keyword to analyze")
    database: str = Field(default="us", description="Target database (us, uk, ca, etc.)")
    include_competitors: bool = Field(default=True, description="Include competitor analysis")
    include_related: bool = Field(default=True, description="Include related keywords")


class DomainAnalysisRequest(BaseModel):
    domain: str = Field(..., description="Domain to analyze")
    include_keywords: bool = Field(default=True, description="Include top keywords")


class BatchKeywordRequest(BaseModel):
    keywords: List[str] = Field(..., description="List of keywords to analyze")
    max_concurrent: int = Field(default=5, description="Maximum concurrent API calls")


class KeywordRecordResponse(BaseModel):
    keyword: str
    search_volume: Optional[int] = None
    cpc: Optional[float] = None
    keyword_difficulty: Optional[int] = None
    competition: Optional[float] = None
    source_url: Optional[str] = None
    timestamp: datetime


class DomainAnalysisResponse(BaseModel):
    domain: str
    authority_score: Optional[int] = None
    organic_keywords: Optional[int] = None
    organic_traffic: Optional[int] = None
    backlinks: Optional[int] = None
    referring_domains: Optional[int] = None
    timestamp: datetime


class CompetitorAnalysisResponse(BaseModel):
    keyword: str
    competitors: List[Dict[str, Any]]
    serp_features: List[str]
    featured_snippets: List[Dict[str, Any]]
    paa_boxes: List[Dict[str, Any]]
    timestamp: datetime


class KeywordAnalysisResponse(BaseModel):
    keyword: KeywordRecordResponse
    competitors: Optional[CompetitorAnalysisResponse] = None
    related_keywords: Optional[List[KeywordRecordResponse]] = None
    analysis_timestamp: str


class DomainAnalysisFullResponse(BaseModel):
    domain: DomainAnalysisResponse
    top_keywords: Optional[List[KeywordRecordResponse]] = None
    analysis_timestamp: str


class BatchAnalysisResponse(BaseModel):
    keywords_analyzed: int
    successful_analyses: int
    failed_analyses: int
    results: Dict[str, Any]
    batch_timestamp: str


class ServiceStatusResponse(BaseModel):
    status: str
    api_client: str
    rate_limits: Dict[str, Any]
    cache_info: Dict[str, Any]
    last_updated: str


# Dependency to get SEO service
async def get_seo_service() -> SEOService:
    """Get configured SEO service instance"""
    return create_seo_service()


@router.post("/keyword/analyze", response_model=KeywordAnalysisResponse)
async def analyze_keyword(
    request: KeywordAnalysisRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Analyze a single keyword with comprehensive data
    
    Returns keyword metrics, competitor analysis, and related keywords
    """
    try:
        result = await seo_service.analyze_keyword(
            keyword=request.keyword,
            include_competitors=request.include_competitors,
            include_related=request.include_related
        )
        
        return KeywordAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing keyword {request.keyword}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze keyword: {str(e)}"
        )


@router.post("/domain/analyze", response_model=DomainAnalysisFullResponse)
async def analyze_domain(
    request: DomainAnalysisRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Analyze a domain with comprehensive metrics
    
    Returns domain authority, traffic, backlinks, and top keywords
    """
    try:
        result = await seo_service.analyze_domain(
            domain=request.domain,
            include_keywords=request.include_keywords
        )
        
        return DomainAnalysisFullResponse(**result)
        
    except Exception as e:
        logger.error(f"Error analyzing domain {request.domain}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze domain: {str(e)}"
        )


@router.post("/keywords/batch", response_model=BatchAnalysisResponse)
async def batch_keyword_analysis(
    request: BatchKeywordRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Analyze multiple keywords concurrently
    
    Efficiently processes multiple keywords with rate limiting
    """
    try:
        # Validate input
        if len(request.keywords) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 keywords allowed per batch request"
            )
        
        result = await seo_service.batch_keyword_analysis(
            keywords=request.keywords,
            max_concurrent=request.max_concurrent
        )
        
        return BatchAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in batch keyword analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze keywords: {str(e)}"
        )


@router.get("/keyword/{keyword}", response_model=KeywordRecordResponse)
async def get_keyword_data(
    keyword: str,
    database: str = Query(default="us", description="Target database"),
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get basic keyword data without competitor analysis
    
    Faster response for basic keyword metrics
    """
    try:
        result = await seo_service.api_client.get_keyword_analysis(
            keyword=keyword,
            database=database
        )
        
        return KeywordRecordResponse(
            keyword=result.keyword,
            search_volume=result.search_volume,
            cpc=result.cpc,
            keyword_difficulty=result.keyword_difficulty,
            competition=result.competition,
            source_url=result.source_url,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error getting keyword data for {keyword}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get keyword data: {str(e)}"
        )


@router.get("/domain/{domain}", response_model=DomainAnalysisResponse)
async def get_domain_data(
    domain: str,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get basic domain data without keyword analysis
    
    Faster response for basic domain metrics
    """
    try:
        result = await seo_service.api_client.get_domain_overview(domain)
        
        return DomainAnalysisResponse(
            domain=result.domain,
            authority_score=result.authority_score,
            organic_keywords=result.organic_keywords,
            organic_traffic=result.organic_traffic,
            backlinks=result.backlinks,
            referring_domains=result.referring_domains,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error getting domain data for {domain}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get domain data: {str(e)}"
        )


@router.get("/competitors/{keyword}", response_model=CompetitorAnalysisResponse)
async def get_competitor_analysis(
    keyword: str,
    database: str = Query(default="us", description="Target database"),
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get competitor analysis for a specific keyword
    
    Returns top competitors, SERP features, and rich snippets
    """
    try:
        result = await seo_service.api_client.get_competitor_analysis(
            keyword=keyword,
            database=database
        )
        
        return CompetitorAnalysisResponse(
            keyword=result.keyword,
            competitors=result.competitors,
            serp_features=result.serp_features,
            featured_snippets=result.featured_snippets,
            paa_boxes=result.paa_boxes,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error getting competitor analysis for {keyword}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get competitor analysis: {str(e)}"
        )


@router.get("/keywords/related/{keyword}", response_model=List[KeywordRecordResponse])
async def get_related_keywords(
    keyword: str,
    database: str = Query(default="us", description="Target database"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum keywords to return"),
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get related keywords for a seed keyword
    
    Useful for keyword expansion and content planning
    """
    try:
        results = await seo_service.api_client.get_related_keywords(
            keyword=keyword,
            database=database,
            limit=limit
        )
        
        return [
            KeywordRecordResponse(
                keyword=kw.keyword,
                search_volume=kw.search_volume,
                cpc=kw.cpc,
                keyword_difficulty=kw.keyword_difficulty,
                competition=kw.competition,
                timestamp=kw.timestamp
            )
            for kw in results
        ]
        
    except Exception as e:
        logger.error(f"Error getting related keywords for {keyword}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get related keywords: {str(e)}"
        )


@router.get("/domains/keywords/{domain}", response_model=List[KeywordRecordResponse])
async def get_domain_keywords(
    domain: str,
    database: str = Query(default="us", description="Target database"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum keywords to return"),
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get keywords that a domain ranks for
    
    Useful for competitor analysis and content gap identification
    """
    try:
        results = await seo_service.api_client.get_domain_keywords(
            domain=domain,
            database=database,
            limit=limit
        )
        
        return [
            KeywordRecordResponse(
                keyword=kw.keyword,
                search_volume=kw.search_volume,
                cpc=kw.cpc,
                keyword_difficulty=kw.keyword_difficulty,
                competition=kw.competition,
                timestamp=kw.timestamp
            )
            for kw in results
        ]
        
    except Exception as e:
        logger.error(f"Error getting domain keywords for {domain}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get domain keywords: {str(e)}"
        )


@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status(
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Get SEO service status and health information
    
    Returns rate limit status, cache info, and service health
    """
    try:
        status = seo_service.get_service_status()
        return ServiceStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Clear the SEO service response cache
    
    Useful for testing or when fresh data is needed
    """
    try:
        seo_service.api_client.clear_cache()
        return {"message": "Cache cleared successfully", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns service availability without authentication
    """
    return {
        "status": "healthy",
        "service": "SEO API",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
