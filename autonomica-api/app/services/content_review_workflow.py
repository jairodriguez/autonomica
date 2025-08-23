import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .content_types import ContentType, Platform
from .content_quality_checker import QualityCheckResult, QualityCheckStatus

logger = logging.getLogger(__name__)

class ReviewStatus(str, Enum):
    """Status of content review."""
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    EXPIRED = "expired"

class ReviewPriority(str, Enum):
    """Priority levels for content review."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Reviewer:
    """Represents a content reviewer."""
    reviewer_id: str
    name: str
    email: str
    expertise: List[str]
    max_reviews_per_day: int = 10
    current_reviews: int = 0
    is_active: bool = True
    preferred_content_types: List[ContentType] = None
    preferred_platforms: List[Platform] = None

@dataclass
class ReviewRequest:
    """Represents a content review request."""
    review_id: str
    content_id: str
    content_type: ContentType
    content_preview: str
    target_platforms: List[Platform]
    brand_voice: str
    quality_check_result: QualityCheckResult
    priority: ReviewPriority
    requested_by: str
    requested_at: datetime
    deadline: datetime
    assigned_reviewer: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    review_notes: Optional[str] = None
    review_completed_at: Optional[datetime] = None

@dataclass
class ReviewResult:
    """Result of a content review."""
    review_id: str
    content_id: str
    reviewer_id: str
    status: ReviewStatus
    review_notes: str
    quality_score: float
    approved_for_platforms: List[Platform]
    rejected_for_platforms: List[Platform]
    revision_required: bool
    review_completed_at: datetime
    time_to_review: timedelta
    revision_notes: Optional[str] = None

class ContentReviewWorkflow:
    """Manages the human review workflow for content approval."""
    
    def __init__(self):
        self.reviewers: Dict[str, Reviewer] = {}
        self.review_requests: Dict[str, ReviewRequest] = {}
        self.review_results: Dict[str, ReviewResult] = {}
        self.review_policies = self._initialize_review_policies()
        self.auto_approval_threshold = 0.95  # Auto-approve content with 95%+ quality score
    
    async def submit_for_review(
        self,
        content_id: str,
        content_type: ContentType,
        content_preview: str,
        target_platforms: List[Platform],
        brand_voice: str,
        quality_check_result: QualityCheckResult,
        requested_by: str,
        priority: ReviewPriority = ReviewPriority.NORMAL,
        **kwargs
    ) -> ReviewRequest:
        """Submit content for human review."""
        
        logger.info(f"Submitting content {content_id} for review")
        
        # Check if auto-approval is possible
        if quality_check_result.overall_score >= self.auto_approval_threshold:
            logger.info(f"Content {content_id} auto-approved due to high quality score")
            return await self._auto_approve_content(
                content_id, content_type, target_platforms, quality_check_result
            )
        
        # Create review request
        review_id = f"review_{content_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        deadline = datetime.utcnow() + timedelta(hours=self._get_review_deadline(priority))
        
        review_request = ReviewRequest(
            review_id=review_id,
            content_id=content_id,
            content_type=content_type,
            content_preview=content_preview[:200] + "..." if len(content_preview) > 200 else content_preview,
            target_platforms=target_platforms,
            brand_voice=brand_voice,
            quality_check_result=quality_check_result,
            priority=priority,
            requested_by=requested_by,
            requested_at=datetime.utcnow(),
            deadline=deadline
        )
        
        # Store the review request
        self.review_requests[review_id] = review_request
        
        # Auto-assign reviewer if possible
        await self._auto_assign_reviewer(review_request)
        
        logger.info(f"Review request {review_id} created for content {content_id}")
        return review_request
    
    async def assign_reviewer(
        self,
        review_id: str,
        reviewer_id: str,
        assigned_by: str
    ) -> bool:
        """Manually assign a reviewer to a review request."""
        
        if review_id not in self.review_requests:
            logger.error(f"Review request {review_id} not found")
            return False
        
        if reviewer_id not in self.reviewers:
            logger.error(f"Reviewer {reviewer_id} not found")
            return False
        
        review_request = self.review_requests[review_id]
        reviewer = self.reviewers[reviewer_id]
        
        # Check if reviewer is available
        if not reviewer.is_active or reviewer.current_reviews >= reviewer.max_reviews_per_day:
            logger.warning(f"Reviewer {reviewer_id} is not available for review")
            return False
        
        # Check if reviewer has expertise for this content type
        if not self._reviewer_has_expertise(reviewer, review_request):
            logger.warning(f"Reviewer {reviewer_id} lacks expertise for content type {review_request.content_type}")
            return False
        
        # Assign reviewer
        review_request.assigned_reviewer = reviewer_id
        review_request.status = ReviewStatus.IN_REVIEW
        reviewer.current_reviews += 1
        
        logger.info(f"Reviewer {reviewer_id} assigned to review {review_id}")
        return True
    
    async def complete_review(
        self,
        review_id: str,
        reviewer_id: str,
        status: ReviewStatus,
        review_notes: str,
        quality_score: float,
        approved_platforms: List[Platform],
        rejected_platforms: List[Platform],
        revision_required: bool = False,
        revision_notes: Optional[str] = None
    ) -> ReviewResult:
        """Complete a content review."""
        
        if review_id not in self.review_requests:
            raise ValueError(f"Review request {review_id} not found")
        
        review_request = self.review_requests[review_id]
        
        if review_request.assigned_reviewer != reviewer_id:
            raise ValueError(f"Reviewer {reviewer_id} is not assigned to review {review_id}")
        
        if review_request.status != ReviewStatus.IN_REVIEW:
            raise ValueError(f"Review {review_id} is not in review status")
        
        # Calculate time to review
        time_to_review = datetime.utcnow() - review_request.requested_at
        
        # Create review result
        review_result = ReviewResult(
            review_id=review_id,
            content_id=review_request.content_id,
            reviewer_id=reviewer_id,
            status=status,
            review_notes=review_notes,
            quality_score=quality_score,
            approved_for_platforms=approved_platforms,
            rejected_for_platforms=rejected_platforms,
            revision_required=revision_required,
            revision_notes=revision_notes,
            review_completed_at=datetime.utcnow(),
            time_to_review=time_to_review
        )
        
        # Update review request
        review_request.status = status
        review_request.review_notes = review_notes
        review_request.review_completed_at = datetime.utcnow()
        
        # Update reviewer workload
        if reviewer_id in self.reviewers:
            self.reviewers[reviewer_id].current_reviews = max(0, self.reviewers[reviewer_id].current_reviews - 1)
        
        # Store review result
        self.review_results[review_id] = review_result
        
        logger.info(f"Review {review_id} completed with status {status}")
        return review_result
    
    async def get_reviewer_workload(self, reviewer_id: str) -> Dict[str, Any]:
        """Get current workload for a reviewer."""
        if reviewer_id not in self.reviewers:
            return {"error": "Reviewer not found"}
        
        reviewer = self.reviewers[reviewer_id]
        active_reviews = [
            req for req in self.review_requests.values()
            if req.assigned_reviewer == reviewer_id and req.status == ReviewStatus.IN_REVIEW
        ]
        
        return {
            "reviewer_id": reviewer_id,
            "name": reviewer.name,
            "current_reviews": reviewer.current_reviews,
            "max_reviews_per_day": reviewer.max_reviews_per_day,
            "available_capacity": reviewer.max_reviews_per_day - reviewer.current_reviews,
            "active_reviews": len(active_reviews),
            "is_available": reviewer.is_active and reviewer.current_reviews < reviewer.max_reviews_per_day
        }
    
    async def get_pending_reviews(self, reviewer_id: Optional[str] = None) -> List[ReviewRequest]:
        """Get pending review requests, optionally filtered by reviewer."""
        pending_reviews = [
            req for req in self.review_requests.values()
            if req.status in [ReviewStatus.PENDING_REVIEW, ReviewStatus.IN_REVIEW]
        ]
        
        if reviewer_id:
            pending_reviews = [
                req for req in pending_reviews
                if req.assigned_reviewer == reviewer_id
            ]
        
        # Sort by priority and deadline
        pending_reviews.sort(key=lambda x: (
            self._priority_to_numeric(x.priority),
            x.deadline
        ))
        
        return pending_reviews
    
    async def add_reviewer(
        self,
        reviewer_id: str,
        name: str,
        email: str,
        expertise: List[str],
        max_reviews_per_day: int = 10,
        preferred_content_types: List[ContentType] = None,
        preferred_platforms: List[Platform] = None
    ) -> Reviewer:
        """Add a new reviewer to the system."""
        
        reviewer = Reviewer(
            reviewer_id=reviewer_id,
            name=name,
            email=email,
            expertise=expertise,
            max_reviews_per_day=max_reviews_per_day,
            preferred_content_types=preferred_content_types or [],
            preferred_platforms=preferred_platforms or []
        )
        
        self.reviewers[reviewer_id] = reviewer
        logger.info(f"Reviewer {reviewer_id} added to the system")
        return reviewer
    
    async def remove_reviewer(self, reviewer_id: str) -> bool:
        """Remove a reviewer from the system."""
        if reviewer_id not in self.reviewers:
            return False
        
        # Check if reviewer has active reviews
        active_reviews = [
            req for req in self.review_requests.values()
            if req.assigned_reviewer == reviewer_id and req.status == ReviewStatus.IN_REVIEW
        ]
        
        if active_reviews:
            logger.warning(f"Cannot remove reviewer {reviewer_id} with active reviews")
            return False
        
        del self.reviewers[reviewer_id]
        logger.info(f"Reviewer {reviewer_id} removed from the system")
        return True
    
    async def _auto_approve_content(
        self,
        content_id: str,
        content_type: ContentType,
        target_platforms: List[Platform],
        quality_check_result: QualityCheckResult
    ) -> ReviewRequest:
        """Automatically approve content that meets quality thresholds."""
        
        review_id = f"auto_approve_{content_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a review request marked as auto-approved
        review_request = ReviewRequest(
            review_id=review_id,
            content_id=content_id,
            content_type=content_type,
            content_preview="[Auto-approved content]",
            target_platforms=target_platforms,
            brand_voice="Auto-approved",
            quality_check_result=quality_check_result,
            priority=ReviewPriority.LOW,
            requested_by="system",
            requested_at=datetime.utcnow(),
            deadline=datetime.utcnow(),
            status=ReviewStatus.APPROVED,
            review_notes="Auto-approved due to high quality score",
            review_completed_at=datetime.utcnow()
        )
        
        self.review_requests[review_id] = review_request
        return review_request
    
    async def _auto_assign_reviewer(self, review_request: ReviewRequest) -> bool:
        """Automatically assign a suitable reviewer to a review request."""
        
        available_reviewers = [
            reviewer for reviewer in self.reviewers.values()
            if reviewer.is_active and reviewer.current_reviews < reviewer.max_reviews_per_day
        ]
        
        if not available_reviewers:
            logger.warning("No available reviewers for auto-assignment")
            return False
        
        # Score reviewers based on suitability
        scored_reviewers = []
        for reviewer in available_reviewers:
            score = self._calculate_reviewer_suitability(reviewer, review_request)
            scored_reviewers.append((reviewer, score))
        
        # Sort by score (highest first) and select the best available
        scored_reviewers.sort(key=lambda x: x[1], reverse=True)
        
        for reviewer, score in scored_reviewers:
            if await self.assign_reviewer(review_request.review_id, reviewer.reviewer_id, "system"):
                logger.info(f"Auto-assigned reviewer {reviewer.reviewer_id} to review {review_request.review_id}")
                return True
        
        return False
    
    def _calculate_reviewer_suitability(self, reviewer: Reviewer, review_request: ReviewRequest) -> float:
        """Calculate how suitable a reviewer is for a specific review request."""
        score = 0.0
        
        # Content type expertise
        if review_request.content_type in reviewer.preferred_content_types:
            score += 0.4
        
        # Platform expertise
        platform_overlap = set(review_request.target_platforms) & set(reviewer.preferred_platforms)
        if platform_overlap:
            score += 0.3 * (len(platform_overlap) / len(review_request.target_platforms))
        
        # Workload balance (prefer reviewers with lower current load)
        workload_ratio = reviewer.current_reviews / reviewer.max_reviews_per_day
        score += 0.3 * (1 - workload_ratio)
        
        return score
    
    def _reviewer_has_expertise(self, reviewer: Reviewer, review_request: ReviewRequest) -> bool:
        """Check if a reviewer has the necessary expertise for a review request."""
        # Check content type expertise
        if (reviewer.preferred_content_types and 
            review_request.content_type not in reviewer.preferred_content_types):
            return False
        
        # Check platform expertise
        if (reviewer.preferred_platforms and 
            not any(p in reviewer.preferred_platforms for p in review_request.target_platforms)):
            return False
        
        return True
    
    def _get_review_deadline(self, priority: ReviewPriority) -> int:
        """Get review deadline in hours based on priority."""
        deadline_hours = {
            ReviewPriority.LOW: 72,      # 3 days
            ReviewPriority.NORMAL: 48,   # 2 days
            ReviewPriority.HIGH: 24,     # 1 day
            ReviewPriority.URGENT: 4     # 4 hours
        }
        return deadline_hours.get(priority, 48)
    
    def _priority_to_numeric(self, priority: ReviewPriority) -> int:
        """Convert priority to numeric value for sorting."""
        priority_values = {
            ReviewPriority.LOW: 1,
            ReviewPriority.NORMAL: 2,
            ReviewPriority.HIGH: 3,
            ReviewPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    def _initialize_review_policies(self) -> Dict[str, Any]:
        """Initialize review policies and rules."""
        return {
            "auto_approval": {
                "enabled": True,
                "quality_threshold": 0.95,
                "content_types": [ContentType.SOCIAL_MEDIA_POST, ContentType.VIDEO_SCRIPT],
                "max_length": 280  # Only auto-approve short content
            },
            "review_deadlines": {
                "low_priority": 72,      # 3 days
                "normal_priority": 48,   # 2 days
                "high_priority": 24,     # 1 day
                "urgent_priority": 4     # 4 hours
            },
            "quality_thresholds": {
                "approval": 0.8,
                "revision": 0.6,
                "rejection": 0.4
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the review workflow system."""
        return {
            "status": "healthy",
            "service": "ContentReviewWorkflow",
            "timestamp": datetime.utcnow().isoformat(),
            "reviewers_count": len(self.reviewers),
            "active_reviewers": len([r for r in self.reviewers.values() if r.is_active]),
            "pending_reviews": len([r for r in self.review_requests.values() if r.status == ReviewStatus.PENDING_REVIEW]),
            "in_review": len([r for r in self.review_requests.values() if r.status == ReviewStatus.IN_REVIEW]),
            "completed_reviews": len(self.review_results),
            "auto_approval_enabled": self.review_policies["auto_approval"]["enabled"]
        }
