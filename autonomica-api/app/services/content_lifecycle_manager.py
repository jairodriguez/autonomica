import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .content_types import ContentType, Platform, ContentFormat
from .content_versioning import ContentVersioningService, ContentVersion, VersionStatus, ChangeType
from .content_quality_checker import ContentQualityChecker, QualityCheckResult
from .content_review_workflow import ContentReviewWorkflow, ReviewStatus, ReviewPriority

logger = logging.getLogger(__name__)

class LifecycleStage(str, Enum):
    """Stages in the content lifecycle."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class ApprovalStatus(str, Enum):
    """Status of content approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    AUTO_APPROVED = "auto_approved"

@dataclass
class ContentLifecycleState:
    """Represents the current state of content in its lifecycle."""
    content_id: str
    current_stage: LifecycleStage
    current_version_id: str
    approval_status: ApprovalStatus
    stage_transitions: List[Dict[str, Any]]
    scheduled_publish_date: Optional[datetime] = None
    actual_publish_date: Optional[datetime] = None
    archive_date: Optional[datetime] = None
    last_modified: datetime = None
    assigned_reviewer: Optional[str] = None
    review_deadline: Optional[datetime] = None

@dataclass
class LifecycleTransition:
    """Represents a transition between lifecycle stages."""
    from_stage: LifecycleStage
    to_stage: LifecycleStage
    transition_reason: str
    triggered_by: str
    timestamp: datetime
    metadata: Dict[str, Any]

class ContentLifecycleManager:
    """Manages the complete lifecycle of content from creation to publication."""
    
    def __init__(self):
        self.versioning_service = ContentVersioningService()
        self.quality_checker = ContentQualityChecker()
        self.review_workflow = ContentReviewWorkflow()
        self.lifecycle_states: Dict[str, ContentLifecycleState] = {}
        self.transition_history: Dict[str, List[LifecycleTransition]] = {}
        self.lifecycle_policies = self._initialize_lifecycle_policies()
    
    async def create_content(
        self,
        content_id: str,
        content_data: str,
        content_type: ContentType,
        content_format: ContentFormat,
        author_id: str,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[ContentVersion, ContentLifecycleState]:
        """Create new content and initialize its lifecycle."""
        
        logger.info(f"Creating new content {content_id} with lifecycle management")
        
        # Create initial version
        version = await self.versioning_service.create_version(
            content_id=content_id,
            content_data=content_data,
            content_type=content_type,
            content_format=content_format,
            author_id=author_id,
            change_log="Initial content creation",
            change_type=ChangeType.CREATED,
            target_platforms=target_platforms,
            brand_voice=brand_voice,
            tags=tags,
            metadata=metadata,
            **kwargs
        )
        
        # Initialize lifecycle state
        lifecycle_state = ContentLifecycleState(
            content_id=content_id,
            current_stage=LifecycleStage.DRAFT,
            current_version_id=version.version_id,
            approval_status=ApprovalStatus.PENDING,
            stage_transitions=[],
            last_modified=datetime.utcnow()
        )
        
        # Store lifecycle state
        self.lifecycle_states[content_id] = lifecycle_state
        
        # Initialize transition history
        self.transition_history[content_id] = []
        
        # Record initial transition
        await self._record_transition(
            content_id=content_id,
            from_stage=None,
            to_stage=LifecycleStage.DRAFT,
            transition_reason="Content created",
            triggered_by=author_id,
            metadata={"version_id": version.version_id}
        )
        
        logger.info(f"Content {content_id} created and lifecycle initialized")
        return version, lifecycle_state
    
    async def submit_for_review(
        self,
        content_id: str,
        author_id: str,
        review_priority: ReviewPriority = ReviewPriority.NORMAL,
        **kwargs
    ) -> bool:
        """Submit content for review, transitioning it to the review stage."""
        
        logger.info(f"Submitting content {content_id} for review")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Check if content can be submitted for review
        if lifecycle_state.current_stage != LifecycleStage.DRAFT:
            raise ValueError(f"Content must be in DRAFT stage to submit for review. Current stage: {lifecycle_state.current_stage}")
        
        # Get current version
        current_version = await self.versioning_service.get_active_version(content_id)
        if not current_version:
            raise ValueError(f"No active version found for content {content_id}")
        
        # Perform quality check
        quality_result = await self.quality_checker.check_content_quality(
            content=current_version.content_data,
            content_type=current_version.content_type,
            target_platforms=current_version.metadata.get("platforms", []),
            brand_voice=current_version.metadata.get("brand_voice", "Professional"),
            content_id=content_id
        )
        
        # Update version with quality check result
        current_version.quality_check_result = quality_result
        
        # Submit to review workflow
        review_request = await self.review_workflow.submit_for_review(
            content_id=content_id,
            content_type=current_version.content_type,
            content_preview=current_version.content_data[:200] + "..." if len(current_version.content_data) > 200 else current_version.content_data,
            target_platforms=current_version.metadata.get("platforms", []),
            brand_voice=current_version.metadata.get("brand_voice", "Professional"),
            quality_check_result=quality_result,
            requested_by=author_id,
            priority=review_priority
        )
        
        # Update lifecycle state
        lifecycle_state.current_stage = LifecycleStage.IN_REVIEW
        lifecycle_state.approval_status = ApprovalStatus.PENDING
        lifecycle_state.assigned_reviewer = review_request.assigned_reviewer
        lifecycle_state.review_deadline = review_request.deadline
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=LifecycleStage.DRAFT,
            to_stage=LifecycleStage.IN_REVIEW,
            transition_reason="Submitted for review",
            triggered_by=author_id,
            metadata={
                "review_id": review_request.review_id,
                "assigned_reviewer": review_request.assigned_reviewer,
                "review_deadline": review_request.deadline.isoformat() if review_request.deadline else None
            }
        )
        
        logger.info(f"Content {content_id} submitted for review")
        return True
    
    async def approve_content(
        self,
        content_id: str,
        reviewer_id: str,
        approval_notes: str = "",
        scheduled_publish_date: Optional[datetime] = None,
        **kwargs
    ) -> bool:
        """Approve content, transitioning it to the approved stage."""
        
        logger.info(f"Approving content {content_id}")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Check if content can be approved
        if lifecycle_state.current_stage != LifecycleStage.IN_REVIEW:
            raise ValueError(f"Content must be in IN_REVIEW stage to approve. Current stage: {lifecycle_state.current_stage}")
        
        # Update lifecycle state
        lifecycle_state.current_stage = LifecycleStage.APPROVED
        lifecycle_state.approval_status = ApprovalStatus.APPROVED
        lifecycle_state.scheduled_publish_date = scheduled_publish_date
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=LifecycleStage.IN_REVIEW,
            to_stage=LifecycleStage.APPROVED,
            transition_reason="Content approved",
            triggered_by=reviewer_id,
            metadata={
                "approval_notes": approval_notes,
                "scheduled_publish_date": scheduled_publish_date.isoformat() if scheduled_publish_date else None
            }
        )
        
        logger.info(f"Content {content_id} approved")
        return True
    
    async def reject_content(
        self,
        content_id: str,
        reviewer_id: str,
        rejection_reason: str,
        revision_required: bool = True,
        **kwargs
    ) -> bool:
        """Reject content, transitioning it back to draft stage."""
        
        logger.info(f"Rejecting content {content_id}")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Check if content can be rejected
        if lifecycle_state.current_stage != LifecycleStage.IN_REVIEW:
            raise ValueError(f"Content must be in IN_REVIEW stage to reject. Current stage: {lifecycle_state.current_stage}")
        
        # Determine next stage
        if revision_required:
            next_stage = LifecycleStage.DRAFT
            approval_status = ApprovalStatus.NEEDS_REVISION
        else:
            next_stage = LifecycleStage.DEPRECATED
            approval_status = ApprovalStatus.REJECTED
        
        # Update lifecycle state
        lifecycle_state.current_stage = next_stage
        lifecycle_state.approval_status = approval_status
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=LifecycleStage.IN_REVIEW,
            to_stage=next_stage,
            transition_reason=f"Content rejected: {rejection_reason}",
            triggered_by=reviewer_id,
            metadata={
                "rejection_reason": rejection_reason,
                "revision_required": revision_required
            }
        )
        
        logger.info(f"Content {content_id} rejected and moved to {next_stage}")
        return True
    
    async def publish_content(
        self,
        content_id: str,
        publisher_id: str,
        publish_notes: str = "",
        **kwargs
    ) -> bool:
        """Publish content, transitioning it to the published stage."""
        
        logger.info(f"Publishing content {content_id}")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Check if content can be published
        if lifecycle_state.current_stage != LifecycleStage.APPROVED:
            raise ValueError(f"Content must be in APPROVED stage to publish. Current stage: {lifecycle_state.current_stage}")
        
        # Update lifecycle state
        lifecycle_state.current_stage = LifecycleStage.PUBLISHED
        lifecycle_state.actual_publish_date = datetime.utcnow()
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=LifecycleStage.APPROVED,
            to_stage=LifecycleStage.PUBLISHED,
            transition_reason="Content published",
            triggered_by=publisher_id,
            metadata={
                "publish_notes": publish_notes,
                "actual_publish_date": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Content {content_id} published")
        return True
    
    async def update_content(
        self,
        content_id: str,
        new_content_data: str,
        author_id: str,
        change_log: str,
        change_type: ChangeType = ChangeType.UPDATED,
        **kwargs
    ) -> ContentVersion:
        """Update content with a new version and manage lifecycle transitions."""
        
        logger.info(f"Updating content {content_id}")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Create new version
        new_version = await self.versioning_service.update_version(
            content_id=content_id,
            new_content_data=new_content_data,
            author_id=author_id,
            change_log=change_log,
            change_type=change_type,
            **kwargs
        )
        
        # Update lifecycle state
        lifecycle_state.current_version_id = new_version.version_id
        lifecycle_state.current_stage = LifecycleStage.DRAFT
        lifecycle_state.approval_status = ApprovalStatus.PENDING
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Clear review-related fields
        lifecycle_state.assigned_reviewer = None
        lifecycle_state.review_deadline = None
        lifecycle_state.scheduled_publish_date = None
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=LifecycleStage.PUBLISHED if lifecycle_state.current_stage == LifecycleStage.PUBLISHED else LifecycleStage.APPROVED,
            to_stage=LifecycleStage.DRAFT,
            transition_reason=f"Content updated: {change_log}",
            triggered_by=author_id,
            metadata={
                "version_id": new_version.version_id,
                "change_type": change_type.value
            }
        )
        
        logger.info(f"Content {content_id} updated to version {new_version.version_id}")
        return new_version
    
    async def archive_content(
        self,
        content_id: str,
        archiver_id: str,
        archive_reason: str,
        **kwargs
    ) -> bool:
        """Archive content, transitioning it to the archived stage."""
        
        logger.info(f"Archiving content {content_id}")
        
        if content_id not in self.lifecycle_states:
            raise ValueError(f"Content {content_id} not found in lifecycle")
        
        lifecycle_state = self.lifecycle_states[content_id]
        
        # Check if content can be archived
        if lifecycle_state.current_stage not in [LifecycleStage.PUBLISHED, LifecycleStage.APPROVED]:
            raise ValueError(f"Content must be PUBLISHED or APPROVED to archive. Current stage: {lifecycle_state.current_stage}")
        
        # Update lifecycle state
        lifecycle_state.current_stage = LifecycleStage.ARCHIVED
        lifecycle_state.archive_date = datetime.utcnow()
        lifecycle_state.last_modified = datetime.utcnow()
        
        # Archive the current version
        await self.versioning_service.archive_version(
            version_id=lifecycle_state.current_version_id,
            author_id=archiver_id,
            archive_reason=archive_reason
        )
        
        # Record transition
        await self._record_transition(
            content_id=content_id,
            from_stage=lifecycle_state.current_stage,
            to_stage=LifecycleStage.ARCHIVED,
            transition_reason=f"Content archived: {archive_reason}",
            triggered_by=archiver_id,
            metadata={
                "archive_reason": archive_reason,
                "archive_date": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Content {content_id} archived")
        return True
    
    async def get_lifecycle_state(self, content_id: str) -> Optional[ContentLifecycleState]:
        """Get the current lifecycle state of content."""
        return self.lifecycle_states.get(content_id)
    
    async def get_transition_history(
        self,
        content_id: str,
        limit: Optional[int] = None
    ) -> List[LifecycleTransition]:
        """Get the transition history for content."""
        
        if content_id not in self.transition_history:
            return []
        
        transitions = self.transition_history[content_id]
        if limit:
            transitions = transitions[-limit:]
        
        return transitions
    
    async def get_content_by_stage(
        self,
        stage: LifecycleStage,
        limit: Optional[int] = None
    ) -> List[ContentLifecycleState]:
        """Get all content in a specific lifecycle stage."""
        
        matching_content = [
            state for state in self.lifecycle_states.values()
            if state.current_stage == stage
        ]
        
        # Sort by last modified date (most recent first)
        matching_content.sort(key=lambda x: x.last_modified, reverse=True)
        
        if limit:
            matching_content = matching_content[:limit]
        
        return matching_content
    
    async def get_content_summary(self, content_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of content lifecycle."""
        
        if content_id not in self.lifecycle_states:
            return {"error": "Content not found"}
        
        lifecycle_state = self.lifecycle_states[content_id]
        current_version = await self.versioning_service.get_active_version(content_id)
        transitions = await self.get_transition_history(content_id)
        
        summary = {
            "content_id": content_id,
            "current_stage": lifecycle_state.current_stage.value,
            "approval_status": lifecycle_state.approval_status.value,
            "current_version": {
                "version_id": lifecycle_state.current_version_id,
                "version_number": current_version.version_number if current_version else None,
                "created_at": current_version.created_at.isoformat() if current_version else None,
                "author_id": current_version.author_id if current_version else None
            },
            "lifecycle_metadata": {
                "scheduled_publish_date": lifecycle_state.scheduled_publish_date.isoformat() if lifecycle_state.scheduled_publish_date else None,
                "actual_publish_date": lifecycle_state.actual_publish_date.isoformat() if lifecycle_state.actual_publish_date else None,
                "archive_date": lifecycle_state.archive_date.isoformat() if lifecycle_state.archive_date else None,
                "last_modified": lifecycle_state.last_modified.isoformat() if lifecycle_state.last_modified else None
            },
            "review_info": {
                "assigned_reviewer": lifecycle_state.assigned_reviewer,
                "review_deadline": lifecycle_state.review_deadline.isoformat() if lifecycle_state.review_deadline else None
            },
            "transition_count": len(transitions),
            "total_time_in_current_stage": self._calculate_time_in_stage(lifecycle_state, transitions)
        }
        
        return summary
    
    async def _record_transition(
        self,
        content_id: str,
        from_stage: Optional[LifecycleStage],
        to_stage: LifecycleStage,
        transition_reason: str,
        triggered_by: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Record a lifecycle transition."""
        
        transition = LifecycleTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            transition_reason=transition_reason,
            triggered_by=triggered_by,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        if content_id not in self.transition_history:
            self.transition_history[content_id] = []
        
        self.transition_history[content_id].append(transition)
        
        # Update lifecycle state transitions
        if content_id in self.lifecycle_states:
            self.lifecycle_states[content_id].stage_transitions.append({
                "from_stage": from_stage.value if from_stage else None,
                "to_stage": to_stage.value,
                "timestamp": transition.timestamp.isoformat(),
                "triggered_by": triggered_by,
                "reason": transition_reason
            })
    
    def _calculate_time_in_stage(
        self,
        lifecycle_state: ContentLifecycleState,
        transitions: List[LifecycleTransition]
    ) -> Optional[str]:
        """Calculate how long content has been in its current stage."""
        
        if not transitions:
            return None
        
        # Find the last transition to current stage
        current_stage_transitions = [
            t for t in transitions
            if t.to_stage == lifecycle_state.current_stage
        ]
        
        if not current_stage_transitions:
            return None
        
        last_transition = max(current_stage_transitions, key=lambda x: x.timestamp)
        time_in_stage = datetime.utcnow() - last_transition.timestamp
        
        # Format duration
        if time_in_stage.days > 0:
            return f"{time_in_stage.days} days"
        elif time_in_stage.seconds > 3600:
            hours = time_in_stage.seconds // 3600
            return f"{hours} hours"
        elif time_in_stage.seconds > 60:
            minutes = time_in_stage.seconds // 60
            return f"{minutes} minutes"
        else:
            return f"{time_in_stage.seconds} seconds"
    
    def _initialize_lifecycle_policies(self) -> Dict[str, Any]:
        """Initialize lifecycle policies and rules."""
        return {
            "stage_transitions": {
                LifecycleStage.DRAFT: [LifecycleStage.IN_REVIEW, LifecycleStage.DEPRECATED],
                LifecycleStage.IN_REVIEW: [LifecycleStage.APPROVED, LifecycleStage.DRAFT, LifecycleStage.DEPRECATED],
                LifecycleStage.APPROVED: [LifecycleStage.PUBLISHED, LifecycleStage.DRAFT, LifecycleStage.ARCHIVED],
                LifecycleStage.PUBLISHED: [LifecycleStage.DRAFT, LifecycleStage.ARCHIVED],
                LifecycleStage.ARCHIVED: [LifecycleStage.DRAFT, LifecycleStage.DEPRECATED],
                LifecycleStage.DEPRECATED: [LifecycleStage.DRAFT]
            },
            "auto_transitions": {
                "publish_after_approval": False,  # Manual publish required
                "archive_after_days": 365,  # Auto-archive after 1 year
                "review_timeout_days": 7    # Auto-reject after 7 days
            },
            "required_approvals": {
                ContentType.BLOG_POST: 1,
                ContentType.SOCIAL_MEDIA_POST: 1,
                ContentType.VIDEO_SCRIPT: 2,
                ContentType.WHITEPAPER: 2
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the lifecycle management system."""
        
        total_content = len(self.lifecycle_states)
        stage_distribution = {}
        approval_distribution = {}
        
        for state in self.lifecycle_states.values():
            stage = state.current_stage.value
            approval = state.approval_status.value
            
            stage_distribution[stage] = stage_distribution.get(stage, 0) + 1
            approval_distribution[approval] = approval_distribution.get(approval, 0) + 1
        
        return {
            "status": "healthy",
            "service": "ContentLifecycleManager",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_content": total_content,
                "stage_distribution": stage_distribution,
                "approval_distribution": approval_distribution
            },
            "components": {
                "versioning_service": await self.versioning_service.health_check(),
                "quality_checker": await self.quality_checker.health_check(),
                "review_workflow": await self.review_workflow.health_check()
            },
            "system_status": "operational"
        }




