"""
Keyword Suggestions API Routes
Provides endpoints for generating intelligent keyword suggestions
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.keyword_suggestion import (
    create_keyword_suggestion_service,
    KeywordSuggestionService,
    SuggestionRequest,
    SuggestionResponse,
    SuggestionType,
    SuggestionSource
)

router = APIRouter(prefix="/api/seo/suggestions", tags=["Keyword Suggestions"])

class SuggestionRequestModel(BaseModel):
    """Request model for keyword suggestions"""
    seed_keywords: List[str] = Field(..., description="List of seed keywords to generate suggestions from", min_items=1, max_items=20)
    target_language: str = Field(default="en", description="Target language for suggestions")
    suggestion_types: List[str] = Field(default=["related", "long_tail"], description="Types of suggestions to generate")
    max_suggestions: int = Field(default=50, description="Maximum number of suggestions to return", ge=1, le=200)
    min_relevance_score: float = Field(default=0.3, description="Minimum relevance score for suggestions", ge=0.0, le=1.0)
    include_metrics: bool = Field(default=True, description="Whether to include keyword metrics")
    include_explanations: bool = Field(default=True, description="Whether to include explanation for each suggestion")
    target_difficulty: Optional[str] = Field(default=None, description="Target difficulty level: easy, medium, hard")
    target_intent: Optional[str] = Field(default=None, description="Target search intent: informational, navigational, commercial, transactional")
    exclude_keywords: List[str] = Field(default=[], description="Keywords to exclude from suggestions")
    competitor_domains: List[str] = Field(default=[], description="Competitor domains for competitor-based suggestions")

class SuggestionResponseModel(BaseModel):
    """Response model for keyword suggestions"""
    request_id: str
    seed_keywords: List[str]
    suggestions: List[Dict[str, Any]]
    total_suggestions: int
    suggestion_breakdown: Dict[str, int]
    processing_time: float
    metadata: Dict[str, Any]
    generated_at: datetime

class SuggestionTypeResponse(BaseModel):
    """Response model for available suggestion types"""
    suggestion_types: List[Dict[str, str]]
    sources: List[Dict[str, str]]
    supported_languages: List[str]

class SuggestionStatisticsResponse(BaseModel):
    """Response model for suggestion statistics"""
    cache_size: int
    cache_hit_rate: float
    total_requests_processed: int
    average_processing_time: float
    suggestion_types_generated: List[str]
    sources_available: List[str]

_suggestion_service_instance: Optional[KeywordSuggestionService] = None

async def get_suggestion_service() -> KeywordSuggestionService:
    """Get or create the global suggestion service instance"""
    global _suggestion_service_instance
    if _suggestion_service_instance is None:
        _suggestion_service_instance = await create_keyword_suggestion_service()
    return _suggestion_service_instance

@router.post("/generate", response_model=SuggestionResponseModel)
async def generate_keyword_suggestions(
    request: SuggestionRequestModel,
    current_user: ClerkUser = Depends(get_current_user),
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Generate keyword suggestions based on seed keywords"""
    try:
        # Convert string suggestion types to enum values
        suggestion_types = []
        for suggestion_type_str in request.suggestion_types:
            try:
                suggestion_types.append(SuggestionType(suggestion_type_str))
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid suggestion type: {suggestion_type_str}"
                )
        
        # Convert string intent to enum if provided
        target_intent = None
        if request.target_intent:
            try:
                from app.services.keyword_analysis import KeywordIntent
                target_intent = KeywordIntent(request.target_intent)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid target intent: {request.target_intent}"
                )
        
        # Create suggestion request
        suggestion_request = SuggestionRequest(
            seed_keywords=request.seed_keywords,
            target_language=request.target_language,
            suggestion_types=suggestion_types,
            max_suggestions=request.max_suggestions,
            min_relevance_score=request.min_relevance_score,
            include_metrics=request.include_metrics,
            include_explanations=request.include_explanations,
            target_difficulty=request.target_difficulty,
            target_intent=target_intent,
            exclude_keywords=request.exclude_keywords,
            competitor_domains=request.competitor_domains
        )
        
        # Generate suggestions
        response = await suggestion_service.generate_suggestions(suggestion_request)
        
        # Convert suggestions to dict format for API response
        suggestions_dict = []
        for suggestion in response.suggestions:
            suggestion_data = {
                "keyword": suggestion.keyword,
                "suggestion_type": suggestion.suggestion_type.value,
                "source": suggestion.source.value,
                "relevance_score": suggestion.relevance_score,
                "explanation": suggestion.explanation if request.include_explanations else None
            }
            
            # Add optional fields if requested
            if request.include_metrics:
                if suggestion.difficulty_score is not None:
                    suggestion_data["difficulty_score"] = suggestion.difficulty_score
                if suggestion.search_volume is not None:
                    suggestion_data["search_volume"] = suggestion.search_volume
                if suggestion.cpc is not None:
                    suggestion_data["cpc"] = suggestion.cpc
                if suggestion.competition is not None:
                    suggestion_data["competition"] = suggestion.competition
                if suggestion.intent is not None:
                    suggestion_data["intent"] = suggestion.intent.value
                if suggestion.keyword_type is not None:
                    suggestion_data["keyword_type"] = suggestion.keyword_type.value
            
            suggestions_dict.append(suggestion_data)
        
        # Convert breakdown to string keys for JSON serialization
        breakdown_dict = {k.value: v for k, v in response.suggestion_breakdown.items()}
        
        return SuggestionResponseModel(
            request_id=response.request_id,
            seed_keywords=response.seed_keywords,
            suggestions=suggestions_dict,
            total_suggestions=response.total_suggestions,
            suggestion_breakdown=breakdown_dict,
            processing_time=response.processing_time,
            metadata=response.metadata,
            generated_at=response.generated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")

@router.get("/types", response_model=SuggestionTypeResponse)
async def get_available_suggestion_types(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get available suggestion types and sources"""
    try:
        suggestion_types = [
            {"value": suggestion_type.value, "name": suggestion_type.value.replace("_", " ").title()}
            for suggestion_type in SuggestionType
        ]
        
        sources = [
            {"value": source.value, "name": source.value.replace("_", " ").title()}
            for source in SuggestionSource
        ]
        
        supported_languages = ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "ko", "zh"]
        
        return SuggestionTypeResponse(
            suggestion_types=suggestion_types,
            sources=sources,
            supported_languages=supported_languages
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestion types: {str(e)}")

@router.get("/statistics", response_model=SuggestionStatisticsResponse)
async def get_suggestion_statistics(
    current_user: ClerkUser = Depends(get_current_user),
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Get statistics about suggestion generation"""
    try:
        stats = await suggestion_service.get_suggestion_statistics()
        return SuggestionStatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.post("/clear-cache")
async def clear_suggestion_cache(
    current_user: ClerkUser = Depends(get_current_user),
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Clear the suggestion cache"""
    try:
        await suggestion_service.clear_cache()
        return {"message": "Suggestion cache cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/health")
async def health_check(
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Health check for the suggestion service"""
    try:
        # Basic health check
        stats = await suggestion_service.get_suggestion_statistics()
        return {
            "status": "healthy",
            "service": "keyword_suggestions",
            "cache_size": stats["cache_size"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "keyword_suggestions",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/batch-generate")
async def batch_generate_suggestions(
    requests: List[SuggestionRequestModel],
    current_user: ClerkUser = Depends(get_current_user),
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Generate suggestions for multiple requests in batch"""
    try:
        if len(requests) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 requests allowed in batch"
            )
        
        results = []
        for i, request in enumerate(requests):
            try:
                # Convert request to internal format (similar to single request)
                suggestion_types = []
                for suggestion_type_str in request.suggestion_types:
                    try:
                        suggestion_types.append(SuggestionType(suggestion_type_str))
                    except ValueError:
                        results.append({
                            "index": i,
                            "success": False,
                            "error": f"Invalid suggestion type: {suggestion_type_str}"
                        })
                        continue
                
                # Convert string intent to enum if provided
                target_intent = None
                if request.target_intent:
                    try:
                        from app.services.keyword_analysis import KeywordIntent
                        target_intent = KeywordIntent(request.target_intent)
                    except ValueError:
                        results.append({
                            "index": i,
                            "success": False,
                            "error": f"Invalid target intent: {request.target_intent}"
                        })
                        continue
                
                # Create suggestion request
                suggestion_request = SuggestionRequest(
                    seed_keywords=request.seed_keywords,
                    target_language=request.target_language,
                    suggestion_types=suggestion_types,
                    max_suggestions=request.max_suggestions,
                    min_relevance_score=request.min_relevance_score,
                    include_metrics=request.include_metrics,
                    include_explanations=request.include_explanations,
                    target_difficulty=request.target_difficulty,
                    target_intent=target_intent,
                    exclude_keywords=request.exclude_keywords,
                    competitor_domains=request.competitor_domains
                )
                
                # Generate suggestions
                response = await suggestion_service.generate_suggestions(suggestion_request)
                
                # Convert to dict format
                suggestions_dict = []
                for suggestion in response.suggestions:
                    suggestion_data = {
                        "keyword": suggestion.keyword,
                        "suggestion_type": suggestion.suggestion_type.value,
                        "source": suggestion.source.value,
                        "relevance_score": suggestion.relevance_score,
                        "explanation": suggestion.explanation if request.include_explanations else None
                    }
                    
                    if request.include_metrics:
                        if suggestion.difficulty_score is not None:
                            suggestion_data["difficulty_score"] = suggestion.difficulty_score
                        if suggestion.search_volume is not None:
                            suggestion_data["search_volume"] = suggestion.search_volume
                        if suggestion.cpc is not None:
                            suggestion_data["cpc"] = suggestion.cpc
                        if suggestion.competition is not None:
                            suggestion_data["competition"] = suggestion.competition
                        if suggestion.intent is not None:
                            suggestion_data["intent"] = suggestion.intent.value
                        if suggestion.keyword_type is not None:
                            suggestion_data["keyword_type"] = suggestion.keyword_type.value
                    
                    suggestions_dict.append(suggestion_data)
                
                # Convert breakdown to string keys
                breakdown_dict = {k.value: v for k, v in response.suggestion_breakdown.items()}
                
                results.append({
                    "index": i,
                    "success": True,
                    "request_id": response.request_id,
                    "seed_keywords": response.seed_keywords,
                    "suggestions": suggestions_dict,
                    "total_suggestions": response.total_suggestions,
                    "suggestion_breakdown": breakdown_dict,
                    "processing_time": response.processing_time,
                    "metadata": response.metadata,
                    "generated_at": response.generated_at
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_requests": len(requests),
            "successful_requests": len([r for r in results if r["success"]]),
            "failed_requests": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch generation: {str(e)}")

@router.get("/suggestions/{request_id}")
async def get_cached_suggestions(
    request_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    suggestion_service: KeywordSuggestionService = Depends(get_suggestion_service)
):
    """Get cached suggestions by request ID"""
    try:
        # This would require adding a method to get cached suggestions by ID
        # For now, return a message indicating this feature needs implementation
        return {
            "message": "Cached suggestions retrieval by ID not yet implemented",
            "request_id": request_id,
            "note": "This endpoint will be implemented to retrieve previously generated suggestions"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cached suggestions: {str(e)}")
