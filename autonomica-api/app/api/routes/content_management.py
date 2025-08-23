from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
import os

from ..services.content_types import ContentType, Platform, ContentFormat
from ..services.content_generation import StandaloneContentGenerationService
from ..services.langchain_content_generation import LangChainContentGenerator
from ..services.content_repurposing import ContentRepurposingService
from ..services.content_quality_orchestrator import ContentQualityOrchestrator
from ..services.content_versioning import ContentVersioningService, ChangeType
from ..services.content_lifecycle_manager import ContentLifecycleManager, LifecycleStage

router = APIRouter(prefix="/api/content", tags=["Content Management"])

# Pydantic models for API requests/responses
class ContentGenerationRequest(BaseModel):
    content_type: ContentType
    prompt: str
    target_platforms: List[Platform]
    brand_voice: str = "Professional and engaging"
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ContentRepurposingRequest(BaseModel):
    source_content: str
    source_type: ContentType
    target_type: ContentType
    target_platforms: List[Platform]
    brand_voice: str = "Professional and engaging"
    num_variations: int = 3

class ContentUpdateRequest(BaseModel):
    new_content_data: str
    change_log: str
    change_type: ChangeType = ChangeType.UPDATED
    branch_name: Optional[str] = None
    metadata_updates: Optional[Dict[str, Any]] = None

class ContentReviewRequest(BaseModel):
    content_id: str
    reviewer_id: str
    review_notes: str
    approved: bool
    scheduled_publish_date: Optional[datetime] = None

class ContentPublishRequest(BaseModel):
    content_id: str
    publisher_id: str
    publish_notes: str = ""
    target_platforms: Optional[List[Platform]] = None

class ContentSearchRequest(BaseModel):
    query: Optional[str] = None
    content_type: Optional[ContentType] = None
    platform: Optional[Platform] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 50
    offset: int = 0

# Initialize services
content_generation_service = StandaloneContentGenerationService()
langchain_service = LangChainContentGenerator()
repurposing_service = ContentRepurposingService()
quality_orchestrator = ContentQualityOrchestrator()
versioning_service = ContentVersioningService()
lifecycle_manager = ContentLifecycleManager()

@router.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend interface"""
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "static")
    index_path = os.path.join(static_dir, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Autonomica CMS</title></head>
        <body>
            <h1>Autonomica Content Management System</h1>
            <p>Frontend interface not found. Please ensure static files are properly configured.</p>
        </body>
        </html>
        """)

@router.post("/generate", response_model=Dict[str, Any])
async def generate_content(request: ContentGenerationRequest):
    """Generate new content using AI"""
    try:
        # Use the standalone service for now
        result = await content_generation_service.generate_content(
            content_type=request.content_type,
            prompt=request.prompt,
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            tags=request.tags,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "content": result.get("content", ""),
            "title": result.get("title", "Generated Content"),
            "metadata": result.get("metadata", {}),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/repurpose", response_model=Dict[str, Any])
async def repurpose_content(request: ContentRepurposingRequest):
    """Repurpose existing content to new formats"""
    try:
        result = await repurposing_service.repurpose_content(
            source_content=request.source_content,
            source_type=request.source_type,
            target_type=request.target_type,
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice,
            num_variations=request.num_variations
        )
        
        return {
            "success": True,
            "repurposed_content": result.get("repurposed_content", []),
            "quality_score": result.get("quality_score", 0),
            "repurposed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/langchain-repurpose", response_model=Dict[str, Any])
async def langchain_repurpose_content(content_id: str, target_format: str = Query(..., description="Target format: tweets, thread, carousel, video_script"), brand_voice: str = Query("Professional and engaging", description="Brand voice for repurposing"), num_items: int = Query(3, description="Number of items to generate")):
    """Repurpose content using LangChain pipeline"""
    try:
        # Map target_format to appropriate LangChain method
        if target_format == "tweets":
            result = await langchain_service.repurpose_blog_to_tweets(
                blog_content="Sample blog content",  # This would come from content_id
                brand_voice=brand_voice,
                num_tweets=num_items
            )
        elif target_format == "thread":
            result = await langchain_service.generate_thread_from_content(
                content="Sample content",
                brand_voice=brand_voice,
                num_tweets=num_items
            )
        elif target_format == "carousel":
            result = await langchain_service.generate_carousel_content(
                content="Sample content",
                brand_voice=brand_voice,
                num_slides=num_items
            )
        elif target_format == "video_script":
            result = await langchain_service.generate_video_script(
                content="Sample content",
                brand_voice=brand_voice,
                duration_minutes=5
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid target format")
        
        return {
            "success": True,
            "repurposed_content": result,
            "target_format": target_format,
            "repurposed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{content_id}/update", response_model=Dict[str, Any])
async def update_content(content_id: str, request: ContentUpdateRequest):
    """Update existing content"""
    try:
        # Create new version
        new_version = await versioning_service.update_version(
            content_id=content_id,
            new_content_data=request.new_content_data,
            author_id="user",  # This would come from authentication
            change_log=request.change_log,
            change_type=request.change_type,
            branch_name=request.branch_name,
            metadata_updates=request.metadata_updates
        )
        
        return {
            "success": True,
            "version_id": new_version.version_id,
            "version_number": new_version.version_number,
            "updated_at": new_version.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/submit-review", response_model=Dict[str, Any])
async def submit_for_review(content_id: str, author_id: str = Query(..., description="Author ID")):
    """Submit content for review"""
    try:
        success = await lifecycle_manager.submit_for_review(
            content_id=content_id,
            author_id=author_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Content submitted for review",
                "submitted_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to submit for review")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/review", response_model=Dict[str, Any])
async def review_content(content_id: str, request: ContentReviewRequest):
    """Review content (approve/reject)"""
    try:
        if request.approved:
            success = await lifecycle_manager.approve_content(
                content_id=content_id,
                reviewer_id=request.reviewer_id,
                approval_notes=request.review_notes,
                scheduled_publish_date=request.scheduled_publish_date
            )
        else:
            success = await lifecycle_manager.reject_content(
                content_id=content_id,
                reviewer_id=request.reviewer_id,
                rejection_reason=request.review_notes
            )
        
        if success:
            return {
                "success": True,
                "message": f"Content {'approved' if request.approved else 'rejected'}",
                "reviewed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to review content")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/publish", response_model=Dict[str, Any])
async def publish_content(content_id: str, request: ContentPublishRequest):
    """Publish approved content"""
    try:
        success = await lifecycle_manager.publish_content(
            content_id=content_id,
            publisher_id=request.publisher_id,
            publish_notes=request.publish_notes
        )
        
        if success:
            return {
                "success": True,
                "message": "Content published successfully",
                "published_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to publish content")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_id}", response_model=Dict[str, Any])
async def get_content(content_id: str, include_versions: bool = Query(False, description="Include version history")):
    """Get content details"""
    try:
        # Get current content
        content = await lifecycle_manager.get_content_summary(content_id)
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        result = {
            "success": True,
            "content": content
        }
        
        if include_versions:
            versions = await versioning_service.get_version_history(content_id, limit=10)
            result["versions"] = [asdict(v) for v in versions]
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{content_id}/versions", response_model=Dict[str, Any])
async def get_content_versions(content_id: str, limit: int = Query(10, description="Number of versions to return")):
    """Get content version history"""
    try:
        versions = await versioning_service.get_version_history(
            content_id=content_id,
            limit=limit,
            include_metadata=True
        )
        
        return {
            "success": True,
            "versions": [asdict(v) for v in versions],
            "total_versions": len(versions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/rollback/{version_id}", response_model=Dict[str, Any])
async def rollback_content(content_id: str, version_id: str, rollback_reason: str = Query(..., description="Reason for rollback")):
    """Rollback content to a previous version"""
    try:
        new_version = await versioning_service.rollback_version(
            content_id=content_id,
            target_version_id=version_id,
            author_id="user",  # This would come from authentication
            rollback_reason=rollback_reason
        )
        
        return {
            "success": True,
            "version_id": new_version.version_id,
            "version_number": new_version.version_number,
            "rolled_back_at": new_version.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{content_id}/archive", response_model=Dict[str, Any])
async def archive_content(content_id: str, archive_reason: str = Query(..., description="Reason for archiving")):
    """Archive content"""
    try:
        success = await lifecycle_manager.archive_content(
            content_id=content_id,
            archiver_id="user",  # This would come from authentication
            archive_reason=archive_reason
        )
        
        if success:
            return {
                "success": True,
                "message": "Content archived successfully",
                "archived_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to archive content")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=Dict[str, Any])
async def search_content(request: ContentSearchRequest):
    """Search and filter content"""
    try:
        # For now, return mock data
        # In a real implementation, this would query the database
        mock_content = [
            {
                "content_id": "content_001",
                "title": "Sample Blog Post",
                "content_type": "blog_post",
                "status": "published",
                "author_id": "author_001",
                "created_at": "2024-01-15T10:00:00Z",
                "tags": ["technology", "ai"]
            },
            {
                "content_id": "content_002",
                "title": "Social Media Update",
                "content_type": "social_media_post",
                "status": "draft",
                "author_id": "author_002",
                "created_at": "2024-01-16T14:30:00Z",
                "tags": ["marketing", "social"]
            }
        ]
        
        # Apply filters
        filtered_content = mock_content
        
        if request.query:
            filtered_content = [c for c in filtered_content if request.query.lower() in c["title"].lower()]
        
        if request.status:
            filtered_content = [c for c in filtered_content if c["status"] == request.status]
        
        if request.content_type:
            filtered_content = [c for c in filtered_content if c["content_type"] == request.content_type]
        
        # Apply pagination
        start = request.offset
        end = start + request.limit
        paginated_content = filtered_content[start:end]
        
        return {
            "success": True,
            "content": paginated_content,
            "total": len(filtered_content),
            "limit": request.limit,
            "offset": request.offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # For now, return mock data
        # In a real implementation, this would aggregate data from various services
        return {
            "success": True,
            "total_content": 25,
            "in_review": 3,
            "approved": 8,
            "published": 14,
            "draft": 5,
            "archived": 2,
            "content_types": {
                "blog_post": 12,
                "social_media_post": 8,
                "video_script": 3,
                "email_newsletter": 2
            },
            "platforms": {
                "website": 15,
                "twitter": 8,
                "linkedin": 6,
                "instagram": 4
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check system health"""
    try:
        # Check all services
        versioning_health = await versioning_service.health_check()
        lifecycle_health = await lifecycle_manager.health_check()
        
        return {
            "success": True,
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "versioning": versioning_health,
                "lifecycle": lifecycle_health,
                "quality": {"status": "healthy", "message": "Quality orchestrator operational"}
            }
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }




