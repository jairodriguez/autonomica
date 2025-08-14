"""
SEO Research and Analysis API Routes

This module provides API endpoints for:
- Keyword research and analysis
- SERP analysis and competitor research
- Keyword clustering and opportunity identification
- SEO scoring and recommendations
"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.seo_service import (
    SEOService, 
    create_seo_service, 
    KeywordRecord, 
    SERPResult, 
    KeywordCluster, 
    SEOAnalysis
)
from app.auth.clerk_middleware import get_current_user, ClerkUser

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/seo", tags=["SEO Research"])

# Request/Response Models
class KeywordAnalysisRequest(BaseModel):
    """Request model for keyword analysis"""
    keyword: str = Field(..., description="Target keyword to analyze")
    domain: Optional[str] = Field(None, description="Optional domain to analyze against")
    include_serp: bool = Field(True, description="Whether to include SERP analysis")
    include_clustering: bool = Field(True, description="Whether to include keyword clustering")

class KeywordResearchRequest(BaseModel):
    """Request model for keyword research"""
    seed_keyword: str = Field(..., description="Seed keyword to research")
    max_related: int = Field(50, description="Maximum number of related keywords to find")
    min_volume: Optional[int] = Field(None, description="Minimum search volume threshold")
    max_difficulty: Optional[int] = Field(None, description="Maximum difficulty threshold")

class SERPResearchRequest(BaseModel):
    """Request model for SERP research"""
    keyword: str = Field(..., description="Keyword to research SERP for")
    num_results: int = Field(10, description="Number of results to analyze")
    include_features: bool = Field(True, description="Whether to include featured snippets and PAA")

class KeywordClusteringRequest(BaseModel):
    """Request model for keyword clustering"""
    keywords: List[str] = Field(..., description="List of keywords to cluster")
    clustering_threshold: float = Field(0.85, description="Similarity threshold for clustering")
    max_clusters: int = Field(10, description="Maximum number of clusters to create")

class SEOOpportunityRequest(BaseModel):
    """Request model for opportunity analysis"""
    keywords: List[str] = Field(..., description="Keywords to analyze for opportunities")
    min_volume: int = Field(1000, description="Minimum search volume threshold")
    max_difficulty: int = Field(50, description="Maximum difficulty threshold")
    min_cpc: float = Field(1.0, description="Minimum CPC threshold")

# Response Models
class KeywordAnalysisResponse(BaseModel):
    """Response model for keyword analysis"""
    success: bool
    analysis: Optional[SEOAnalysis] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

class KeywordResearchResponse(BaseModel):
    """Response model for keyword research"""
    success: bool
    seed_keyword: str
    related_keywords: List[KeywordRecord]
    total_volume: int
    avg_difficulty: float
    avg_cpc: float
    opportunities: List[str]
    error: Optional[str] = None

class SERPResearchResponse(BaseModel):
    """Response model for SERP research"""
    success: bool
    keyword: str
    serp_results: List[SERPResult]
    featured_snippets: int
    paa_questions: int
    competition_analysis: dict
    error: Optional[str] = None

class KeywordClusteringResponse(BaseModel):
    """Response model for keyword clustering"""
    success: bool
    clusters: List[KeywordCluster]
    total_keywords: int
    clustering_quality: float
    error: Optional[str] = None

class SEOOpportunityResponse(BaseModel):
    """Response model for opportunity analysis"""
    success: bool
    opportunities: List[dict]
    total_volume: int
    avg_difficulty: float
    avg_cpc: float
    recommendations: List[str]
    error: Optional[str] = None

# Helper function to get SEO service
def get_seo_service() -> SEOService:
    """Get configured SEO service instance"""
    semrush_api_key = os.getenv("SEMRUSH_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not semrush_api_key:
        raise HTTPException(
            status_code=500,
            detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
        )
    
    return create_seo_service(
        semrush_api_key=semrush_api_key,
        openai_api_key=openai_api_key
    )

# API Endpoints

@router.post("/analyze", response_model=KeywordAnalysisResponse)
async def analyze_keyword(
    request: KeywordAnalysisRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Perform comprehensive SEO analysis for a target keyword
    
    This endpoint provides:
    - Keyword metrics from SEMrush
    - SERP analysis and competitor research
    - Keyword clustering and opportunity identification
    - SEO scoring and actionable recommendations
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"User {current_user.user_id} requesting SEO analysis for keyword: {request.keyword}")
        
        # Perform comprehensive analysis
        analysis = await seo_service.analyze_keyword(
            keyword=request.keyword,
            domain=request.domain
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return KeywordAnalysisResponse(
            success=True,
            analysis=analysis,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error during SEO analysis for user {current_user.user_id}: {str(e)}")
        return KeywordAnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )

@router.post("/research", response_model=KeywordResearchResponse)
async def research_keywords(
    request: KeywordResearchRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Research related keywords and identify opportunities
    
    This endpoint provides:
    - Related keyword discovery
    - Volume and difficulty analysis
    - Opportunity identification
    - Strategic recommendations
    """
    try:
        logger.info(f"User {current_user.user_id} requesting keyword research for: {request.seed_keyword}")
        
        # Get related keywords
        related_keywords = await seo_service.semrush_client.get_related_keywords(
            request.seed_keyword, 
            request.max_related
        )
        
        # Get data for each related keyword
        keyword_records = []
        total_volume = 0
        difficulties = []
        cpcs = []
        
        for keyword in related_keywords[:20]:  # Limit to top 20 for performance
            try:
                record = await seo_service.semrush_client.get_keyword_data(keyword)
                if record.search_volume and record.difficulty and record.cpc:
                    # Apply filters
                    if (request.min_volume is None or record.search_volume >= request.min_volume) and \
                       (request.max_difficulty is None or record.difficulty <= request.max_difficulty):
                        keyword_records.append(record)
                        total_volume += record.search_volume
                        difficulties.append(record.difficulty)
                        cpcs.append(record.cpc)
            except Exception as e:
                logger.warning(f"Could not get data for keyword {keyword}: {str(e)}")
                continue
        
        # Calculate averages
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
        avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0
        
        # Identify opportunities
        opportunities = []
        for record in keyword_records:
            if record.search_volume and record.difficulty and record.cpc:
                if record.search_volume > 5000 and record.difficulty < 40:
                    opportunities.append(f"High volume ({record.search_volume}) with low difficulty ({record.difficulty}): {record.keyword}")
                if record.cpc > 2.0:
                    opportunities.append(f"High CPC (${record.cpc:.2f}): {record.keyword}")
        
        return KeywordResearchResponse(
            success=True,
            seed_keyword=request.seed_keyword,
            related_keywords=keyword_records,
            total_volume=total_volume,
            avg_difficulty=avg_difficulty,
            avg_cpc=avg_cpc,
            opportunities=opportunities
        )
        
    except Exception as e:
        logger.error(f"Error during keyword research for user {current_user.user_id}: {str(e)}")
        return KeywordResearchResponse(
            success=False,
            seed_keyword=request.seed_keyword,
            related_keywords=[],
            total_volume=0,
            avg_difficulty=0,
            avg_cpc=0,
            opportunities=[],
            error=f"Research failed: {str(e)}"
        )

@router.post("/serp", response_model=SERPResearchResponse)
async def research_serp(
    request: SERPResearchRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Research search engine results page (SERP) for a keyword
    
    This endpoint provides:
    - Top search results analysis
    - Featured snippet identification
    - People Also Ask questions
    - Competition analysis
    """
    try:
        logger.info(f"User {current_user.user_id} requesting SERP research for keyword: {request.keyword}")
        
        # Get SERP results
        serp_results = await seo_service.scraper.scrape_serp(
            request.keyword, 
            request.num_results
        )
        
        # Analyze SERP features
        featured_snippets = sum(1 for r in serp_results if r.featured_snippet)
        paa_questions = sum(1 for r in serp_results if r.paa_questions)
        
        # Competition analysis
        competition_analysis = {
            "total_results": len(serp_results),
            "featured_snippets": featured_snippets,
            "paa_questions": paa_questions,
            "top_domains": [r.url.split('/')[2] for r in serp_results[:5] if r.url],
            "avg_title_length": sum(len(r.title) for r in serp_results) / len(serp_results) if serp_results else 0
        }
        
        return SERPResearchResponse(
            success=True,
            keyword=request.keyword,
            serp_results=serp_results,
            featured_snippets=featured_snippets,
            paa_questions=paa_questions,
            competition_analysis=competition_analysis
        )
        
    except Exception as e:
        logger.error(f"Error during SERP research for user {current_user.user_id}: {str(e)}")
        return SERPResearchResponse(
            success=False,
            keyword=request.keyword,
            serp_results=[],
            featured_snippets=0,
            paa_questions=0,
            competition_analysis={},
            error=f"SERP research failed: {str(e)}"
        )

@router.post("/cluster", response_model=KeywordClusteringResponse)
async def cluster_keywords(
    request: KeywordClusteringRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Cluster keywords based on semantic similarity
    
    This endpoint provides:
    - Keyword clustering using embeddings
    - Cluster analysis and metrics
    - Opportunity identification within clusters
    - Strategic grouping recommendations
    """
    try:
        logger.info(f"User {current_user.user_id} requesting keyword clustering for {len(request.keywords)} keywords")
        
        # Perform keyword clustering
        clusters = await seo_service._cluster_keywords(request.keywords)
        
        # Calculate clustering quality (simplified metric)
        total_keywords = len(request.keywords)
        clustering_quality = len(clusters) / max(1, total_keywords // 5)  # Normalize by expected cluster count
        
        return KeywordClusteringResponse(
            success=True,
            clusters=clusters,
            total_keywords=total_keywords,
            clustering_quality=min(clustering_quality, 1.0)
        )
        
    except Exception as e:
        logger.error(f"Error during keyword clustering for user {current_user.user_id}: {str(e)}")
        return KeywordClusteringResponse(
            success=False,
            clusters=[],
            total_keywords=len(request.keywords),
            clustering_quality=0.0,
            error=f"Clustering failed: {str(e)}"
        )

@router.post("/opportunities", response_model=SEOOpportunityResponse)
async def find_opportunities(
    request: SEOOpportunityRequest,
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Find SEO opportunities based on keyword criteria
    
    This endpoint provides:
    - Opportunity identification based on filters
    - Volume, difficulty, and CPC analysis
    - Strategic recommendations
    - Actionable insights
    """
    try:
        logger.info(f"User {current_user.user_id} requesting opportunity analysis for {len(request.keywords)} keywords")
        
        opportunities = []
        total_volume = 0
        difficulties = []
        cpcs = []
        
        # Analyze each keyword for opportunities
        for keyword in request.keywords:
            try:
                record = await seo_service.semrush_client.get_keyword_data(keyword)
                if record.search_volume and record.difficulty and record.cpc:
                    if (record.search_volume >= request.min_volume and 
                        record.difficulty <= request.max_difficulty and 
                        record.cpc >= request.min_cpc):
                        
                        opportunity = {
                            "keyword": keyword,
                            "search_volume": record.search_volume,
                            "difficulty": record.difficulty,
                            "cpc": record.cpc,
                            "score": (record.search_volume / 1000) * (1 - record.difficulty / 100) * record.cpc
                        }
                        opportunities.append(opportunity)
                        
                        total_volume += record.search_volume
                        difficulties.append(record.difficulty)
                        cpcs.append(record.cpc)
                        
            except Exception as e:
                logger.warning(f"Could not analyze keyword {keyword}: {str(e)}")
                continue
        
        # Sort opportunities by score
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate averages
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
        avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0
        
        # Generate recommendations
        recommendations = []
        if opportunities:
            if avg_difficulty < 30:
                recommendations.append("Low competition keywords detected - great opportunity for quick wins")
            if avg_cpc > 3.0:
                recommendations.append("High CPC keywords found - strong commercial potential")
            if len(opportunities) > 10:
                recommendations.append("Multiple opportunities available - consider content cluster strategy")
        
        return SEOOpportunityResponse(
            success=True,
            opportunities=opportunities,
            total_volume=total_volume,
            avg_difficulty=avg_difficulty,
            avg_cpc=avg_cpc,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error during opportunity analysis for user {current_user.user_id}: {str(e)}")
        return SEOOpportunityResponse(
            success=False,
            opportunities=[],
            total_volume=0,
            avg_difficulty=0,
            avg_cpc=0,
            recommendations=[],
            error=f"Opportunity analysis failed: {str(e)}"
        )

@router.get("/health")
async def seo_service_health(
    current_user: ClerkUser = Depends(get_current_user),
    seo_service: SEOService = Depends(get_seo_service)
):
    """
    Check SEO service health and configuration
    
    This endpoint provides:
    - Service status
    - API configuration status
    - Rate limit information
    """
    try:
        # Check SEMrush API connectivity
        semrush_status = "unknown"
        try:
            # Try a simple API call
            test_record = await seo_service.semrush_client.get_keyword_data("test")
            semrush_status = "connected" if test_record.keyword == "test" else "error"
        except Exception:
            semrush_status = "error"
        
        # Check OpenAI API if configured
        openai_status = "not_configured"
        if seo_service.config.openai_api_key:
            openai_status = "configured"
        
        return {
            "status": "healthy",
            "service": "SEO Research Service",
            "semrush_api": semrush_status,
            "openai_api": openai_status,
            "user_id": current_user.user_id,
            "timestamp": "2024-01-01T00:00:00Z"  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Error checking SEO service health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")