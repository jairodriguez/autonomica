"""
SEO Score Calculator API Routes
Provides endpoints for calculating comprehensive SEO scores
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import asyncio

from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.seo_score_calculator import (
    create_seo_score_calculator,
    SEOScoreCalculator,
    SEOScore,
    ScoreCategory,
    ScoreLevel
)

router = APIRouter(prefix="/api/seo/scores", tags=["SEO Scores"])

class ScoreCalculationRequest(BaseModel):
    """Request to calculate SEO score"""
    url: HttpUrl = Field(..., description="URL of the page to analyze")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth: basic, comprehensive, or deep")
    include_competitor_analysis: bool = Field(default=False, description="Whether to include competitor comparison")
    custom_weights: Optional[Dict[str, float]] = Field(default=None, description="Custom category weights")

class ScoreCalculationResponse(BaseModel):
    """Response containing SEO score calculation"""
    url: str
    domain: str
    analyzed_at: datetime
    overall_score: float
    max_possible_score: float
    percentage: float
    level: str
    categories: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]
    recommendations: List[str]
    critical_issues: List[str]
    improvement_opportunities: List[str]
    processing_time: float

class BatchScoreRequest(BaseModel):
    """Request for batch score calculation"""
    urls: List[HttpUrl] = Field(..., description="List of URLs to analyze", min_items=1, max_items=20)
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth for all URLs")
    include_competitor_analysis: bool = Field(default=False, description="Whether to include competitor analysis")

class BatchScoreResponse(BaseModel):
    """Response for batch score calculation"""
    batch_id: str
    total_urls: int
    successful_analyses: int
    failed_analyses: int
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]

class ScoreStatisticsResponse(BaseModel):
    """Response for scoring statistics"""
    total_categories: int
    total_factors: int
    category_weights: Dict[str, float]
    scoring_config: Dict[str, Any]

class ScoreComparisonRequest(BaseModel):
    """Request for score comparison"""
    primary_url: HttpUrl = Field(..., description="Primary URL to analyze")
    competitor_urls: List[HttpUrl] = Field(..., description="Competitor URLs to compare against", max_items=10)
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth for comparison")

class ScoreComparisonResponse(BaseModel):
    """Response for score comparison"""
    primary_score: Dict[str, Any]
    competitor_scores: List[Dict[str, Any]]
    comparison_metrics: Dict[str, Any]
    competitive_analysis: Dict[str, Any]

_seo_score_calculator_instance: Optional[SEOScoreCalculator] = None

async def get_seo_score_calculator() -> SEOScoreCalculator:
    """Get or create the global SEO score calculator instance"""
    global _seo_score_calculator_instance
    if _seo_score_calculator_instance is None:
        _seo_score_calculator_instance = await create_seo_score_calculator()
    return _seo_score_calculator_instance

@router.post("/calculate", response_model=ScoreCalculationResponse)
async def calculate_seo_score(
    request: ScoreCalculationRequest,
    current_user: ClerkUser = Depends(get_current_user),
    calculator: SEOScoreCalculator = Depends(get_seo_score_calculator)
):
    """Calculate comprehensive SEO score for a web page"""
    try:
        start_time = datetime.now()
        
        # Calculate SEO score
        seo_score = await calculator.calculate_seo_score(
            url=str(request.url),
            analysis_depth=request.analysis_depth
        )
        
        # Convert categories to serializable format
        categories_dict = {}
        for category, category_score in seo_score.categories.items():
            factors_list = []
            for factor in category_score.factors:
                factors_list.append({
                    "factor_name": factor.factor_name,
                    "score": factor.score,
                    "weight": factor.weight,
                    "weighted_score": factor.weighted_score,
                    "max_score": factor.max_score,
                    "details": factor.details,
                    "recommendations": factor.recommendations,
                    "status": factor.status
                })
            
            categories_dict[category.value] = {
                "total_score": category_score.total_score,
                "max_possible_score": category_score.max_possible_score,
                "percentage": category_score.percentage,
                "level": category_score.level.value,
                "weight": category_score.weight,
                "weighted_score": category_score.weighted_score,
                "factors": factors_list
            }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ScoreCalculationResponse(
            url=seo_score.url,
            domain=seo_score.domain,
            analyzed_at=seo_score.analyzed_at,
            overall_score=seo_score.overall_score,
            max_possible_score=seo_score.max_possible_score,
            percentage=seo_score.percentage,
            level=seo_score.level.value,
            categories=categories_dict,
            summary=seo_score.summary,
            recommendations=seo_score.recommendations,
            critical_issues=seo_score.critical_issues,
            improvement_opportunities=seo_score.improvement_opportunities,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating SEO score: {str(e)}")

@router.post("/batch-calculate", response_model=BatchScoreResponse)
async def batch_calculate_seo_scores(
    request: BatchScoreRequest,
    current_user: ClerkUser = Depends(get_current_user),
    calculator: SEOScoreCalculator = Depends(get_seo_score_calculator)
):
    """Calculate SEO scores for multiple URLs in batch"""
    try:
        start_time = datetime.now()
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        results = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(request.urls):
            try:
                # Calculate score for this URL
                seo_score = await calculator.calculate_seo_score(
                    url=str(url),
                    analysis_depth=request.analysis_depth
                )
                
                # Convert to dict format
                score_dict = {
                    "index": i,
                    "url": seo_score.url,
                    "success": True,
                    "overall_score": seo_score.overall_score,
                    "percentage": seo_score.percentage,
                    "level": seo_score.level.value,
                    "critical_issues_count": len(seo_score.critical_issues),
                    "recommendations_count": len(seo_score.recommendations)
                }
                
                results.append(score_dict)
                successful += 1
                
            except Exception as e:
                results.append({
                    "index": i,
                    "url": str(url),
                    "success": False,
                    "error": str(e)
                })
                failed += 1
        
        # Generate summary
        if successful > 0:
            scores = [r["overall_score"] for r in results if r.get("success")]
            summary = {
                "average_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "score_distribution": {
                    "excellent": len([s for s in scores if s >= 90]),
                    "good": len([s for s in scores if 75 <= s < 90]),
                    "average": len([s for s in scores if 60 <= s < 75]),
                    "poor": len([s for s in scores if 40 <= s < 60]),
                    "critical": len([s for s in scores if s < 40])
                }
            }
        else:
            summary = {"error": "No successful analyses"}
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return BatchScoreResponse(
            batch_id=batch_id,
            total_urls=len(request.urls),
            successful_analyses=successful,
            failed_analyses=failed,
            results=results,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch calculation: {str(e)}")

@router.post("/compare", response_model=ScoreComparisonResponse)
async def compare_seo_scores(
    request: ScoreComparisonRequest,
    current_user: ClerkUser = Depends(get_current_user),
    calculator: SEOScoreCalculator = Depends(get_seo_score_calculator)
):
    """Compare SEO scores between primary URL and competitors"""
    try:
        # Calculate score for primary URL
        primary_score = await calculator.calculate_seo_score(
            url=str(request.primary_url),
            analysis_depth=request.analysis_depth
        )
        
        # Calculate scores for competitor URLs
        competitor_scores = []
        for competitor_url in request.competitor_urls:
            try:
                competitor_score = await calculator.calculate_seo_score(
                    url=str(competitor_url),
                    analysis_depth=request.analysis_depth
                )
                competitor_scores.append({
                    "url": competitor_score.url,
                    "overall_score": competitor_score.overall_score,
                    "percentage": competitor_score.percentage,
                    "level": competitor_score.level.value,
                    "categories": len(competitor_score.categories)
                })
            except Exception as e:
                competitor_scores.append({
                    "url": str(competitor_url),
                    "error": str(e)
                })
        
        # Generate comparison metrics
        if competitor_scores:
            valid_scores = [cs for cs in competitor_scores if "overall_score" in cs]
            if valid_scores:
                competitor_avg = sum(cs["overall_score"] for cs in valid_scores) / len(valid_scores)
                comparison_metrics = {
                    "primary_score": primary_score.overall_score,
                    "competitor_average": competitor_avg,
                    "score_difference": primary_score.overall_score - competitor_avg,
                    "competitive_position": "above_average" if primary_score.overall_score > competitor_avg else "below_average"
                }
            else:
                comparison_metrics = {"error": "No valid competitor scores"}
        else:
            comparison_metrics = {"error": "No competitor analysis"}
        
        # Generate competitive analysis
        competitive_analysis = {
            "primary_strengths": [],
            "primary_weaknesses": [],
            "competitive_advantages": [],
            "improvement_areas": []
        }
        
        # Analyze primary score for insights
        for category, category_score in primary_score.categories.items():
            if category_score.level in [ScoreLevel.EXCELLENT, ScoreLevel.GOOD]:
                competitive_analysis["primary_strengths"].append(f"Strong {category.value}")
            elif category_score.level in [ScoreLevel.POOR, ScoreLevel.CRITICAL]:
                competitive_analysis["primary_weaknesses"].append(f"Weak {category.value}")
        
        # Convert primary score to dict format
        primary_dict = {
            "url": primary_score.url,
            "overall_score": primary_score.overall_score,
            "percentage": primary_score.percentage,
            "level": primary_score.level.value,
            "categories_count": len(primary_score.categories),
            "critical_issues_count": len(primary_score.critical_issues),
            "recommendations_count": len(primary_score.recommendations)
        }
        
        return ScoreComparisonResponse(
            primary_score=primary_dict,
            competitor_scores=competitor_scores,
            comparison_metrics=comparison_metrics,
            competitive_analysis=competitive_analysis
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing scores: {str(e)}")

@router.get("/statistics", response_model=ScoreStatisticsResponse)
async def get_scoring_statistics(
    current_user: ClerkUser = Depends(get_current_user),
    calculator: SEOScoreCalculator = Depends(get_seo_score_calculator)
):
    """Get statistics about the scoring system"""
    try:
        stats = await calculator.get_scoring_statistics()
        return ScoreStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/categories")
async def get_score_categories(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get available score categories and their descriptions"""
    try:
        categories = []
        for category in ScoreCategory:
            categories.append({
                "value": category.value,
                "name": category.value.replace("_", " ").title(),
                "description": f"SEO factors related to {category.value.replace('_', ' ')}"
            })
        
        return {
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@router.get("/levels")
async def get_score_levels(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get available score levels and their thresholds"""
    try:
        levels = [
            {
                "value": ScoreLevel.EXCELLENT.value,
                "name": "Excellent",
                "threshold": "90-100%",
                "description": "Outstanding SEO performance"
            },
            {
                "value": ScoreLevel.GOOD.value,
                "name": "Good",
                "threshold": "75-89%",
                "description": "Above average SEO performance"
            },
            {
                "value": ScoreLevel.AVERAGE.value,
                "name": "Average",
                "threshold": "60-74%",
                "description": "Moderate SEO performance"
            },
            {
                "value": ScoreLevel.POOR.value,
                "name": "Poor",
                "threshold": "40-59%",
                "description": "Below average SEO performance"
            },
            {
                "value": ScoreLevel.CRITICAL.value,
                "name": "Critical",
                "threshold": "0-39%",
                "description": "Critical SEO issues requiring immediate attention"
            }
        ]
        
        return {
            "levels": levels,
            "total_levels": len(levels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting levels: {str(e)}")

@router.get("/health")
async def health_check(
    calculator: SEOScoreCalculator = Depends(get_seo_score_calculator)
):
    """Health check for the SEO score calculator service"""
    try:
        stats = await calculator.get_scoring_statistics()
        return {
            "status": "healthy",
            "service": "seo_score_calculator",
            "total_categories": stats["total_categories"],
            "total_factors": stats["total_factors"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "seo_score_calculator",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
