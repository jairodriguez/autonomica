from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

from ..services.content_types import ContentType, Platform, ContentFormat
from ..services.content_generation import StandaloneContentGenerationService
from ..services.langchain_content_generation import LangChainContentGenerator
from ..services.content_repurposing import ContentRepurposingService
from ..services.content_quality_orchestrator import ContentQualityOrchestrator
from ..services.content_versioning import ContentVersioningService, ChangeType
from ..services.content_lifecycle_manager import ContentLifecycleManager, LifecycleStage

router = APIRouter(prefix="/content", tags=["Content Management"])

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

@router.post("/generate", response_model=Dict[str, Any])
async def generate_content(request: ContentGenerationRequest):
    """Generate new content using AI."""
    try:
        # Generate content
        result = await content_generation_service.generate_content(
            content_type=request.content_type,
            prompt=request.prompt,
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            tags=request.tags,
            **request.metadata or {}
        )
        
        # Create content with lifecycle management
        content_id = f"gen_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id=content_id,
            content_data=result.get("content", ""),
            content_type=request.content_type,
            content_format=ContentFormat.MARKDOWN,
            author_id=request.metadata.get("author_id", "system") if request.metadata else "system",
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice,
            tags=request.tags,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "version_id": version.version_id,
            "generated_content": result,
            "lifecycle_state": {
                "stage": lifecycle_state.current_stage.value,
                "status": lifecycle_state.approval_status.value
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@router.post("/repurpose", response_model=Dict[str, Any])
async def repurpose_content(request: ContentRepurposingRequest):
    """Repurpose existing content into different formats."""
    try:
        # Repurpose content
        result = await repurposing_service.repurpose_content(
            source_content=request.source_content,
            source_type=request.source_type,
            target_type=request.target_type,
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice
        )
        
        # Create new version for repurposed content
        content_id = f"rep_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id=content_id,
            content_data=result.repurposed_content,
            content_type=request.target_type,
            content_format=ContentFormat.MARKDOWN,
            author_id="system",
            target_platforms=request.target_platforms,
            brand_voice=request.brand_voice,
            tags=result.tags or [],
            metadata={
                "source_content_id": "original",
                "repurposing_type": f"{request.source_type.value}_to_{request.target_type.value}",
                "quality_metrics": result.quality_metrics
            }
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "version_id": version.version_id,
            "repurposed_content": result.repurposed_content,
            "quality_metrics": result.quality_metrics,
            "lifecycle_state": {
                "stage": lifecycle_state.current_stage.value,
                "status": lifecycle_state.approval_status.value
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content repurposing failed: {str(e)}")

@router.post("/{content_id}/langchain-repurpose", response_model=Dict[str, Any])
async def langchain_repurpose_content(
    content_id: str,
    target_format: str = Query(..., description="Target format: tweets, thread, carousel, video_script"),
    brand_voice: str = Query("Professional and engaging", description="Brand voice for repurposing"),
    num_items: int = Query(3, description="Number of items to generate")
):
    """Use LangChain to repurpose content into specific formats."""
    try:
        # Get current content
        current_version = await versioning_service.get_active_version(content_id)
        if not current_version:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Repurpose based on target format
        if target_format == "tweets":
            result = await langchain_service.repurpose_blog_to_tweets(
                blog_content=current_version.content_data,
                brand_voice=brand_voice,
                num_tweets=num_items
            )
        elif target_format == "thread":
            result = await langchain_service.generate_thread_from_content(
                content=current_version.content_data,
                target_platform=Platform.TWITTER,
                brand_voice=brand_voice,
                num_posts=num_items
            )
        elif target_format == "carousel":
            result = await langchain_service.generate_carousel_content(
                content=current_version.content_data,
                num_slides=num_items,
                brand_voice=brand_voice
            )
        elif target_format == "video_script":
            result = await langchain_service.generate_video_script(
                content=current_version.content_data,
                video_length="short-form",
                brand_voice=brand_voice
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target format: {target_format}")
        
        return {
            "success": True,
            "content_id": content_id,
            "target_format": target_format,
            "generated_content": result,
            "brand_voice": brand_voice
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangChain repurposing failed: {str(e)}")

@router.put("/{content_id}/update", response_model=Dict[str, Any])
async def update_content(content_id: str, request: ContentUpdateRequest):
    """Update existing content with a new version."""
    try:
        # Update content
        new_version = await lifecycle_manager.update_content(
            content_id=content_id,
            new_content_data=request.new_content_data,
            author_id="user",  # This should come from authentication
            change_log=request.change_log,
            change_type=request.change_type,
            branch_name=request.branch_name,
            metadata_updates=request.metadata_updates
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "new_version_id": new_version.version_id,
            "version_number": new_version.version_number,
            "change_log": new_version.change_log,
            "lifecycle_state": "draft"  # Content returns to draft after update
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content update failed: {str(e)}")

@router.post("/{content_id}/submit-review", response_model=Dict[str, Any])
async def submit_for_review(content_id: str, author_id: str = Query(..., description="Author ID")):
    """Submit content for review."""
    try:
        success = await lifecycle_manager.submit_for_review(
            content_id=content_id,
            author_id=author_id
        )
        
        if success:
            lifecycle_state = await lifecycle_manager.get_lifecycle_state(content_id)
            return {
                "success": True,
                "content_id": content_id,
                "status": "submitted_for_review",
                "current_stage": lifecycle_state.current_stage.value,
                "assigned_reviewer": lifecycle_state.assigned_reviewer,
                "review_deadline": lifecycle_state.review_deadline.isoformat() if lifecycle_state.review_deadline else None
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to submit for review")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review submission failed: {str(e)}")

@router.post("/{content_id}/review", response_model=Dict[str, Any])
async def review_content(content_id: str, request: ContentReviewRequest):
    """Review and approve/reject content."""
    try:
        if request.approved:
            success = await lifecycle_manager.approve_content(
                content_id=content_id,
                reviewer_id=request.reviewer_id,
                approval_notes=request.review_notes,
                scheduled_publish_date=request.scheduled_publish_date
            )
            action = "approved"
        else:
            success = await lifecycle_manager.reject_content(
                content_id=content_id,
                reviewer_id=request.reviewer_id,
                rejection_reason=request.review_notes,
                revision_required=True
            )
            action = "rejected"
        
        if success:
            lifecycle_state = await lifecycle_manager.get_lifecycle_state(content_id)
            return {
                "success": True,
                "content_id": content_id,
                "action": action,
                "current_stage": lifecycle_state.current_stage.value,
                "reviewer_id": request.reviewer_id,
                "review_notes": request.review_notes
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to {action} content")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content review failed: {str(e)}")

@router.post("/{content_id}/publish", response_model=Dict[str, Any])
async def publish_content(content_id: str, request: ContentPublishRequest):
    """Publish approved content."""
    try:
        success = await lifecycle_manager.publish_content(
            content_id=content_id,
            publisher_id=request.publisher_id,
            publish_notes=request.publish_notes
        )
        
        if success:
            lifecycle_state = await lifecycle_manager.get_lifecycle_state(content_id)
            return {
                "success": True,
                "content_id": content_id,
                "status": "published",
                "current_stage": lifecycle_state.current_stage.value,
                "publisher_id": request.publisher_id,
                "publish_notes": request.publish_notes,
                "publish_date": lifecycle_state.actual_publish_date.isoformat() if lifecycle_state.actual_publish_date else None
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to publish content")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content publication failed: {str(e)}")

@router.get("/{content_id}", response_model=Dict[str, Any])
async def get_content(content_id: str, include_versions: bool = Query(False, description="Include version history")):
    """Get content details and current state."""
    try:
        # Get lifecycle state
        lifecycle_state = await lifecycle_manager.get_lifecycle_state(content_id)
        if not lifecycle_state:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Get current version
        current_version = await versioning_service.get_active_version(content_id)
        if not current_version:
            raise HTTPException(status_code=404, detail="Current version not found")
        
        # Get content summary
        summary = await lifecycle_manager.get_content_summary(content_id)
        
        result = {
            "content_id": content_id,
            "current_version": {
                "version_id": current_version.version_id,
                "version_number": current_version.version_number,
                "content_data": current_version.content_data,
                "content_type": current_version.content_type.value,
                "content_format": current_version.content_format.value,
                "created_at": current_version.created_at.isoformat(),
                "author_id": current_version.author_id,
                "tags": current_version.tags,
                "metadata": current_version.metadata
            },
            "lifecycle_state": {
                "current_stage": lifecycle_state.current_stage.value,
                "approval_status": lifecycle_state.approval_status.value,
                "assigned_reviewer": lifecycle_state.assigned_reviewer,
                "review_deadline": lifecycle_state.review_deadline.isoformat() if lifecycle_state.review_deadline else None,
                "scheduled_publish_date": lifecycle_state.scheduled_publish_date.isoformat() if lifecycle_state.scheduled_publish_date else None,
                "actual_publish_date": lifecycle_state.actual_publish_date.isoformat() if lifecycle_state.actual_publish_date else None,
                "last_modified": lifecycle_state.last_modified.isoformat() if lifecycle_state.last_modified else None
            },
            "summary": summary
        }
        
        # Include version history if requested
        if include_versions:
            versions = await versioning_service.get_version_history(content_id, include_content=False)
            result["version_history"] = [
                {
                    "version_id": v.version_id,
                    "version_number": v.version_number,
                    "change_log": v.change_log,
                    "change_type": v.change_type.value,
                    "created_at": v.created_at.isoformat(),
                    "author_id": v.author_id
                }
                for v in versions
            ]
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content: {str(e)}")

@router.get("/{content_id}/versions", response_model=Dict[str, Any])
async def get_content_versions(content_id: str, limit: int = Query(10, description="Number of versions to return")):
    """Get version history for content."""
    try:
        versions = await versioning_service.get_version_history(content_id, include_content=True, limit=limit)
        
        return {
            "content_id": content_id,
            "versions": [
                {
                    "version_id": v.version_id,
                    "version_number": v.version_number,
                    "content_data": v.content_data,
                    "change_log": v.change_log,
                    "change_type": v.change_type.value,
                    "created_at": v.created_at.isoformat(),
                    "author_id": v.author_id,
                    "tags": v.tags,
                    "metadata": v.metadata
                }
                for v in versions
            ],
            "total_versions": len(versions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get version history: {str(e)}")

@router.post("/{content_id}/rollback/{version_id}", response_model=Dict[str, Any])
async def rollback_content(content_id: str, version_id: str, rollback_reason: str = Query(..., description="Reason for rollback")):
    """Rollback content to a previous version."""
    try:
        rollback_version = await versioning_service.rollback_version(
            content_id=content_id,
            target_version_id=version_id,
            author_id="user",  # This should come from authentication
            rollback_reason=rollback_reason
        )
        
        return {
            "success": True,
            "content_id": content_id,
            "rollback_version_id": rollback_version.version_id,
            "rollback_version_number": rollback_version.version_number,
            "rollback_reason": rollback_reason,
            "lifecycle_state": "draft"  # Content returns to draft after rollback
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

@router.post("/{content_id}/archive", response_model=Dict[str, Any])
async def archive_content(content_id: str, archive_reason: str = Query(..., description="Reason for archiving")):
    """Archive content."""
    try:
        success = await lifecycle_manager.archive_content(
            content_id=content_id,
            archiver_id="user",  # This should come from authentication
            archive_reason=archive_reason
        )
        
        if success:
            lifecycle_state = await lifecycle_manager.get_lifecycle_state(content_id)
            return {
                "success": True,
                "content_id": content_id,
                "status": "archived",
                "current_stage": lifecycle_state.current_stage.value,
                "archive_reason": archive_reason
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to archive content")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archive failed: {str(e)}")

@router.post("/search", response_model=Dict[str, Any])
async def search_content(request: ContentSearchRequest):
    """Search and filter content."""
    try:
        # This is a simplified search - in production, you'd use a proper search engine
        all_content = lifecycle_manager.lifecycle_states.values()
        
        # Apply filters
        filtered_content = []
        for content_state in all_content:
            # Apply content type filter
            if request.content_type and content_state.content_type != request.content_type:
                continue
                
            # Apply status filter
            if request.status and content_state.current_stage.value != request.status:
                continue
                
            # Apply date filters
            if request.date_from and content_state.last_modified < request.date_from:
                continue
            if request.date_to and content_state.last_modified > request.date_to:
                continue
            
            # Get content details
            current_version = await versioning_service.get_active_version(content_state.content_id)
            if current_version:
                filtered_content.append({
                    "content_id": content_state.content_id,
                    "current_stage": content_state.current_stage.value,
                    "approval_status": content_state.approval_status.value,
                    "content_type": current_version.content_type.value,
                    "title": current_version.metadata.get("title", "Untitled"),
                    "author_id": current_version.author_id,
                    "created_at": current_version.created_at.isoformat(),
                    "last_modified": content_state.last_modified.isoformat() if content_state.last_modified else None,
                    "tags": current_version.tags
                })
        
        # Apply pagination
        total_count = len(filtered_content)
        paginated_content = filtered_content[request.offset:request.offset + request.limit]
        
        return {
            "success": True,
            "content": paginated_content,
            "pagination": {
                "total_count": total_count,
                "limit": request.limit,
                "offset": request.offset,
                "has_more": request.offset + request.limit < total_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get content by stage
        draft_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.DRAFT)
        review_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.IN_REVIEW)
        approved_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.APPROVED)
        published_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.PUBLISHED)
        archived_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.ARCHIVED)
        
        # Get versioning stats
        versioning_health = await versioning_service.health_check()
        lifecycle_health = await lifecycle_manager.health_check()
        
        return {
            "success": True,
            "content_distribution": {
                "draft": len(draft_content),
                "in_review": len(review_content),
                "approved": len(approved_content),
                "published": len(published_content),
                "archived": len(archived_content)
            },
            "versioning_stats": versioning_health["statistics"],
            "lifecycle_stats": lifecycle_health["statistics"],
            "system_health": {
                "versioning_service": versioning_health["status"],
                "lifecycle_manager": lifecycle_health["status"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Check the health of all content management services."""
    try:
        # Check all services
        versioning_health = await versioning_service.health_check()
        lifecycle_health = await lifecycle_manager.health_check()
        quality_health = await quality_orchestrator.health_check()
        
        # Determine overall health
        overall_status = "healthy"
        if any(h["status"] != "healthy" for h in [versioning_health, lifecycle_health, quality_health]):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "versioning_service": versioning_health,
                "lifecycle_manager": lifecycle_health,
                "quality_orchestrator": quality_health
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }




