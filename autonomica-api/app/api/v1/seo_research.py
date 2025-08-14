"""
SEO Research API Endpoints

This module provides a user-friendly interface for SEO research and analysis:
- Keyword research and analysis
- SERP data visualization
- Keyword clustering results
- SEO scoring and recommendations
- Data export and reporting
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional, Dict, Any
import json
import csv
import io
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from app.services.seo_service import SEOService
from app.services.serp_scraper import SERPScraper
from app.services.keyword_clustering import KeywordClusteringService
from app.services.keyword_analyzer import KeywordAnalyzer
from app.services.seo_data_pipeline import SEODataPipeline
from app.services.keyword_suggester import KeywordSuggester
from app.services.seo_scorer import SEOScorer
from app.services.seo_cache_manager import SEOCacheManager
from app.core.auth import get_current_user
from app.schemas.user import User

router = APIRouter(prefix="/seo-research", tags=["SEO Research"])

# Initialize services
seo_service = SEOService()
serp_scraper = SERPScraper()
clustering_service = KeywordClusteringService()
analyzer_service = KeywordAnalyzer()
pipeline_service = SEODataPipeline()
suggester_service = KeywordSuggester()
scorer_service = SEOScorer()
cache_manager = SEOCacheManager()

@router.get("/health")
async def seo_research_health():
    """Check health status of all SEO services"""
    try:
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "cache": {},
            "overall_status": "healthy"
        }
        
        # Check cache health
        cache_health = await cache_manager.get_cache_health()
        health_status["cache"] = cache_health
        
        # Check service connectivity
        try:
            # Test basic service functionality
            await seo_service.ping()
            health_status["services"]["seo_service"] = "healthy"
        except Exception as e:
            health_status["services"]["seo_service"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"
        
        try:
            await serp_scraper.ping()
            health_status["services"]["serp_scraper"] = "healthy"
        except Exception as e:
            health_status["services"]["serp_scraper"] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"
        
        # Check cache performance
        cache_stats = await cache_manager.get_cache_stats()
        health_status["cache"]["performance"] = {
            "hit_rate": cache_stats.hit_rate,
            "total_entries": cache_stats.total_entries,
            "total_size_mb": round(cache_stats.total_size_bytes / (1024 * 1024), 2)
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/keyword-research")
async def research_keywords(
    keywords: List[str],
    country: str = "us",
    language: str = "en",
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive keyword research
    
    Args:
        keywords: List of keywords to research
        country: Target country for research
        language: Target language for research
        current_user: Authenticated user
    
    Returns:
        Comprehensive keyword research results
    """
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "keywords_researched": len(keywords),
            "country": country,
            "language": language,
            "results": []
        }
        
        for keyword in keywords:
            try:
                # Get keyword data
                keyword_data = await seo_service.get_keyword_data(keyword, country)
                
                # Get SERP data
                serp_data = await serp_scraper.scrape_google(keyword, country, language)
                
                # Analyze keyword
                analysis = await analyzer_service.analyze_keyword(keyword, country)
                
                # Calculate opportunity score
                opportunity = await analyzer_service.calculate_opportunity_score(keyword, country)
                
                keyword_result = {
                    "keyword": keyword,
                    "keyword_data": keyword_data,
                    "serp_analysis": {
                        "organic_results": len(serp_data.organic_results),
                        "featured_snippet": serp_data.featured_snippet is not None,
                        "people_also_ask": len(serp_data.people_also_ask),
                        "related_searches": len(serp_data.related_searches)
                    },
                    "analysis": analysis,
                    "opportunity_score": opportunity,
                    "status": "completed"
                }
                
                results["results"].append(keyword_result)
                
            except Exception as e:
                results["results"].append({
                    "keyword": keyword,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword research failed: {str(e)}")

@router.post("/keyword-clustering")
async def cluster_keywords(
    keywords: List[str],
    algorithm: str = "kmeans",
    n_clusters: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Perform keyword clustering analysis
    
    Args:
        keywords: List of keywords to cluster
        algorithm: Clustering algorithm (kmeans, agglomerative, dbscan)
        n_clusters: Number of clusters (auto-determined if None)
        current_user: Authenticated user
    
    Returns:
        Keyword clustering results with insights
    """
    try:
        # Perform clustering
        clustering_result = await clustering_service.cluster_keywords(
            keywords, algorithm, n_clusters
        )
        
        # Analyze clusters
        cluster_insights = []
        for cluster in clustering_result.clusters:
            # Get intent analysis for cluster
            intent_analysis = await clustering_service.analyze_cluster_intent(cluster)
            
            # Calculate cluster metrics
            cluster_metrics = await clustering_service.calculate_cluster_metrics(cluster)
            
            cluster_insight = {
                "cluster_id": cluster.cluster_id,
                "keywords": cluster.keywords,
                "size": len(cluster.keywords),
                "intent": intent_analysis,
                "metrics": cluster_metrics,
                "representative_keywords": cluster.representative_keywords
            }
            
            cluster_insights.append(cluster_insight)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "algorithm": algorithm,
            "total_clusters": len(clustering_result.clusters),
            "quality_metrics": clustering_result.quality_metrics,
            "clusters": cluster_insights,
            "recommendations": clustering_result.recommendations
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword clustering failed: {str(e)}")

@router.post("/serp-analysis")
async def analyze_serp(
    keyword: str,
    country: str = "us",
    language: str = "en",
    include_competitors: bool = True,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze SERP data for a keyword
    
    Args:
        keyword: Target keyword
        country: Target country
        language: Target language
        include_competitors: Whether to analyze competitor content
        current_user: Authenticated user
    
    Returns:
        Comprehensive SERP analysis
    """
    try:
        # Scrape SERP data
        serp_data = await serp_scraper.scrape_google(keyword, country, language)
        
        # Analyze top-ranking content
        content_analysis = []
        if include_competitors and serp_data.organic_results:
            for i, result in enumerate(serp_data.organic_results[:5]):  # Top 5 results
                try:
                    # Get page content analysis
                    page_analysis = await scorer_service.analyze_page_content(result.url)
                    
                    content_analysis.append({
                        "position": i + 1,
                        "url": result.url,
                        "title": result.title,
                        "snippet": result.snippet,
                        "seo_score": page_analysis.overall_score,
                        "content_quality": page_analysis.content_analysis,
                        "technical_seo": page_analysis.technical_analysis
                    })
                except Exception as e:
                    content_analysis.append({
                        "position": i + 1,
                        "url": result.url,
                        "title": result.title,
                        "snippet": result.snippet,
                        "error": str(e)
                    })
        
        # Analyze SERP features
        serp_features = {
            "featured_snippet": {
                "present": serp_data.featured_snippet is not None,
                "content": serp_data.featured_snippet.text if serp_data.featured_snippet else None
            },
            "people_also_ask": {
                "count": len(serp_data.people_also_ask),
                "questions": [paa.question for paa in serp_data.people_also_ask]
            },
            "related_searches": {
                "count": len(serp_data.related_searches),
                "searches": serp_data.related_searches
            }
        }
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "keyword": keyword,
            "country": country,
            "language": language,
            "serp_features": serp_features,
            "content_analysis": content_analysis,
            "total_organic_results": len(serp_data.organic_results),
            "recommendations": _generate_serp_recommendations(serp_data, content_analysis)
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SERP analysis failed: {str(e)}")

@router.post("/keyword-suggestions")
async def get_keyword_suggestions(
    seed_keyword: str,
    context: Optional[str] = None,
    max_suggestions: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get keyword suggestions based on seed keyword
    
    Args:
        seed_keyword: Base keyword for suggestions
        context: Additional context for suggestions
        max_suggestions: Maximum number of suggestions
        current_user: Authenticated user
    
    Returns:
        Relevant keyword suggestions with metrics
    """
    try:
        # Get various types of suggestions
        semantic_suggestions = await suggester_service.generate_semantic_suggestions(
            seed_keyword, max_suggestions // 4
        )
        
        intent_suggestions = await suggester_service.generate_intent_suggestions(
            seed_keyword, max_suggestions // 4
        )
        
        long_tail_suggestions = await suggester_service.generate_long_tail_suggestions(
            seed_keyword, max_suggestions // 4
        )
        
        competitor_suggestions = await suggester_service.generate_competitor_suggestions(
            seed_keyword, max_suggestions // 4
        )
        
        # Combine and rank suggestions
        all_suggestions = (
            semantic_suggestions.suggestions +
            intent_suggestions.suggestions +
            long_tail_suggestions.suggestions +
            competitor_suggestions.suggestions
        )
        
        # Sort by relevance score
        all_suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit to max_suggestions
        final_suggestions = all_suggestions[:max_suggestions]
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "seed_keyword": seed_keyword,
            "context": context,
            "total_suggestions": len(final_suggestions),
            "suggestions": [
                {
                    "keyword": suggestion.keyword,
                    "type": suggestion.suggestion_type,
                    "relevance_score": suggestion.relevance_score,
                    "search_volume": suggestion.search_volume,
                    "difficulty": suggestion.difficulty,
                    "cpc": suggestion.cpc,
                    "intent": suggestion.intent,
                    "opportunity_score": suggestion.opportunity_score
                }
                for suggestion in final_suggestions
            ],
            "suggestion_breakdown": {
                "semantic": len(semantic_suggestions.suggestions),
                "intent_based": len(intent_suggestions.suggestions),
                "long_tail": len(long_tail_suggestions.suggestions),
                "competitor_based": len(competitor_suggestions.suggestions)
            }
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keyword suggestions failed: {str(e)}")

@router.post("/seo-analysis")
async def analyze_seo(
    url: str,
    target_keywords: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive SEO analysis of a URL
    
    Args:
        url: URL to analyze
        target_keywords: Keywords to focus analysis on
        current_user: Authenticated user
    
    Returns:
        Detailed SEO analysis with recommendations
    """
    try:
        # Get comprehensive SEO score
        seo_score = await scorer_service.calculate_seo_score(url, target_keywords)
        
        # Analyze content quality
        content_analysis = await scorer_service.analyze_content_quality(url)
        
        # Analyze technical SEO
        technical_analysis = await scorer_service.analyze_technical_seo(url)
        
        # Generate recommendations
        recommendations = _generate_seo_recommendations(seo_score, content_analysis, technical_analysis)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "overall_score": seo_score.overall_score,
            "grade": seo_score.grade,
            "detailed_scores": {
                "on_page": seo_score.on_page_score,
                "technical": seo_score.technical_score,
                "content": seo_score.content_score,
                "user_experience": seo_score.user_experience_score,
                "mobile": seo_score.mobile_score,
                "security": seo_score.security_score
            },
            "content_analysis": content_analysis,
            "technical_analysis": technical_analysis,
            "recommendations": recommendations,
            "priority_actions": _get_priority_actions(seo_score, recommendations)
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO analysis failed: {str(e)}")

@router.post("/batch-analysis")
async def batch_analysis(
    keywords: List[str],
    countries: List[str] = ["us"],
    analysis_types: List[str] = ["keyword", "serp", "clustering"],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Perform batch analysis on multiple keywords
    
    Args:
        keywords: List of keywords to analyze
        countries: List of target countries
        analysis_types: Types of analysis to perform
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
    
    Returns:
        Batch analysis job details
    """
    try:
        # Create batch job
        job_id = f"batch_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{current_user.id}"
        
        # Start background processing
        background_tasks.add_task(
            _process_batch_analysis,
            job_id,
            keywords,
            countries,
            analysis_types,
            current_user.id
        )
        
        results = {
            "job_id": job_id,
            "status": "started",
            "timestamp": datetime.now().isoformat(),
            "keywords_count": len(keywords),
            "countries": countries,
            "analysis_types": analysis_types,
            "estimated_completion": _estimate_completion_time(len(keywords), len(countries), analysis_types)
        }
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")

@router.get("/batch-status/{job_id}")
async def get_batch_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of a batch analysis job"""
    try:
        # In a real implementation, you'd store job status in database/cache
        # For now, return a mock status
        status = {
            "job_id": job_id,
            "status": "processing",  # Mock status
            "progress": 75,  # Mock progress
            "completed": 15,
            "total": 20,
            "estimated_completion": datetime.now() + timedelta(minutes=5)
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")

@router.get("/export-results")
async def export_results(
    format: str = Query("json", regex="^(json|csv|excel)$"),
    data_type: str = Query("all", regex="^(all|keywords|serp|clustering|seo_scores)$"),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Export SEO research results
    
    Args:
        format: Export format (json, csv, excel)
        data_type: Type of data to export
        date_from: Start date for export
        date_to: End date for export
        current_user: Authenticated user
    
    Returns:
        Exported data in requested format
    """
    try:
        # In a real implementation, you'd query your database for results
        # For now, return mock data
        
        if format.lower() == "json":
            export_data = {
                "export_info": {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": current_user.id,
                    "data_type": data_type,
                    "date_range": {"from": date_from, "to": date_to}
                },
                "data": _get_mock_export_data(data_type)
            }
            
            return JSONResponse(content=export_data)
            
        elif format.lower() == "csv":
            # Generate CSV data
            csv_data = _generate_csv_export(data_type)
            
            # Create streaming response
            output = io.StringIO()
            output.write(csv_data)
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=seo_export_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/cache-stats")
async def get_cache_statistics(current_user: User = Depends(get_current_user)):
    """Get cache performance statistics"""
    try:
        stats = await cache_manager.get_cache_stats()
        health = await cache_manager.get_cache_health()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": {
                "total_entries": stats.total_entries,
                "total_size_mb": round(stats.total_size_bytes / (1024 * 1024), 2),
                "hit_rate": stats.hit_rate,
                "miss_rate": stats.miss_rate,
                "eviction_count": stats.eviction_count,
                "average_access_time": stats.average_access_time,
                "cache_efficiency": stats.cache_efficiency
            },
            "health": health
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.post("/cache-optimize")
async def optimize_cache(current_user: User = Depends(get_current_user)):
    """Optimize cache performance"""
    try:
        optimization_results = await cache_manager.optimize_cache()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "optimization_results": optimization_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache optimization failed: {str(e)}")

# Helper functions

def _generate_serp_recommendations(serp_data, content_analysis):
    """Generate SERP analysis recommendations"""
    recommendations = []
    
    if not serp_data.featured_snippet:
        recommendations.append({
            "type": "featured_snippet",
            "priority": "high",
            "description": "Create content targeting featured snippet for this keyword",
            "action": "Develop comprehensive answer content with clear structure"
        })
    
    if len(serp_data.people_also_ask) > 0:
        recommendations.append({
            "type": "people_also_ask",
            "priority": "medium",
            "description": "Address common questions in your content",
            "action": "Include FAQ section covering identified questions"
        })
    
    # Analyze competitor strengths
    if content_analysis:
        avg_score = sum(item.get("seo_score", 0) for item in content_analysis) / len(content_analysis)
        if avg_score > 80:
            recommendations.append({
                "type": "competition",
                "priority": "high",
                "description": "High competition with strong competitors",
                "action": "Focus on unique value proposition and long-tail variations"
            })
    
    return recommendations

def _generate_seo_recommendations(seo_score, content_analysis, technical_analysis):
    """Generate SEO improvement recommendations"""
    recommendations = []
    
    # Content recommendations
    if seo_score.content_score < 70:
        recommendations.append({
            "category": "content",
            "priority": "high",
            "description": "Improve content quality and depth",
            "actions": [
                "Increase word count to at least 1500 words",
                "Improve readability score",
                "Add more relevant keywords naturally"
            ]
        })
    
    # Technical recommendations
    if seo_score.technical_score < 70:
        recommendations.append({
            "category": "technical",
            "priority": "high",
            "description": "Fix technical SEO issues",
            "actions": [
                "Ensure proper meta tags",
                "Fix broken links",
                "Optimize page load speed"
            ]
        })
    
    # Mobile recommendations
    if seo_score.mobile_score < 70:
        recommendations.append({
            "category": "mobile",
            "priority": "medium",
            "description": "Improve mobile optimization",
            "actions": [
                "Ensure responsive design",
                "Optimize for mobile page speed",
                "Test mobile user experience"
            ]
        })
    
    return recommendations

def _get_priority_actions(seo_score, recommendations):
    """Get prioritized action items"""
    priority_actions = []
    
    # Sort recommendations by priority and score impact
    for rec in recommendations:
        if rec["priority"] == "high":
            priority_actions.extend(rec["actions"])
    
    # Limit to top 5 actions
    return priority_actions[:5]

def _estimate_completion_time(keywords_count, countries_count, analysis_types):
    """Estimate batch analysis completion time"""
    # Rough estimation: 30 seconds per keyword per country per analysis type
    total_operations = keywords_count * countries_count * len(analysis_types)
    estimated_seconds = total_operations * 30
    
    return datetime.now() + timedelta(seconds=estimated_seconds)

def _get_mock_export_data(data_type):
    """Get mock data for export (replace with real database queries)"""
    if data_type == "keywords":
        return [
            {"keyword": "seo tools", "search_volume": 12000, "difficulty": 65, "cpc": 2.50},
            {"keyword": "keyword research", "search_volume": 8900, "difficulty": 58, "cpc": 1.80}
        ]
    elif data_type == "serp":
        return [
            {"keyword": "seo tools", "organic_results": 100, "featured_snippet": True},
            {"keyword": "keyword research", "organic_results": 95, "featured_snippet": False}
        ]
    else:
        return {"message": "Mock data for export"}

def _generate_csv_export(data_type):
    """Generate CSV export data"""
    if data_type == "keywords":
        return "keyword,search_volume,difficulty,cpc\nseo tools,12000,65,2.50\nkeyword research,8900,58,1.80"
    else:
        return "data_type,value\nmock,data"

async def _process_batch_analysis(job_id, keywords, countries, analysis_types, user_id):
    """Background task for processing batch analysis"""
    try:
        # In a real implementation, you'd:
        # 1. Update job status to "processing"
        # 2. Process each keyword/country combination
        # 3. Update progress
        # 4. Store results
        # 5. Update job status to "completed"
        
        logger.info(f"Started batch analysis job {job_id} for user {user_id}")
        
        # Mock processing delay
        await asyncio.sleep(2)
        
        logger.info(f"Completed batch analysis job {job_id}")
        
    except Exception as e:
        logger.error(f"Batch analysis job {job_id} failed: {e}")
        # Update job status to "failed"