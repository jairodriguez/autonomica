import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from .content_types import ContentType, Platform
from .content_quality_checker import ContentQualityChecker, QualityCheckResult, QualityCheckStatus
from .content_review_workflow import ContentReviewWorkflow, ReviewRequest, ReviewStatus, ReviewPriority

logger = logging.getLogger(__name__)

@dataclass
class QualityWorkflowResult:
    """Result of the complete quality workflow."""
    content_id: str
    content_type: ContentType
    quality_check_result: QualityCheckResult
    review_request: Optional[ReviewRequest] = None
    final_status: str = "pending"
    workflow_completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None

class ContentQualityOrchestrator:
    """Orchestrates the complete content quality workflow including checks and review."""
    
    def __init__(self):
        self.quality_checker = ContentQualityChecker()
        self.review_workflow = ContentReviewWorkflow()
        self.workflow_history: Dict[str, QualityWorkflowResult] = {}
    
    async def process_content_quality(
        self,
        content_id: str,
        content: str,
        content_type: ContentType,
        target_platforms: List[Platform],
        brand_voice: str = "Professional and engaging",
        auto_submit_for_review: bool = True,
        review_priority: ReviewPriority = ReviewPriority.NORMAL,
        requested_by: str = "system",
        **kwargs
    ) -> QualityWorkflowResult:
        """Process content through the complete quality workflow."""
        
        start_time = datetime.utcnow()
        logger.info(f"Starting quality workflow for content {content_id}")
        
        try:
            # Step 1: Perform quality check
            quality_check_result = await self.quality_checker.check_content_quality(
                content=content,
                content_type=content_type,
                target_platforms=target_platforms,
                brand_voice=brand_voice,
                content_id=content_id,
                **kwargs
            )
            
            # Step 2: Determine next steps based on quality score
            review_request = None
            final_status = "quality_check_completed"
            
            if auto_submit_for_review and quality_check_result.status != QualityCheckStatus.PASSED:
                # Submit for human review if quality check didn't pass
                review_request = await self.review_workflow.submit_for_review(
                    content_id=content_id,
                    content_type=content_type,
                    content_preview=content[:200] + "..." if len(content) > 200 else content,
                    target_platforms=target_platforms,
                    brand_voice=brand_voice,
                    quality_check_result=quality_check_result,
                    requested_by=requested_by,
                    priority=review_priority
                )
                
                if review_request.status == ReviewStatus.APPROVED:
                    final_status = "auto_approved"
                else:
                    final_status = "submitted_for_review"
            
            elif quality_check_result.status == QualityCheckStatus.PASSED:
                final_status = "quality_check_passed"
            
            # Step 3: Create workflow result
            workflow_completed_at = datetime.utcnow()
            total_processing_time = (workflow_completed_at - start_time).total_seconds()
            
            workflow_result = QualityWorkflowResult(
                content_id=content_id,
                content_type=content_type,
                quality_check_result=quality_check_result,
                review_request=review_request,
                final_status=final_status,
                workflow_completed_at=workflow_completed_at,
                total_processing_time=total_processing_time
            )
            
            # Store in history
            self.workflow_history[content_id] = workflow_result
            
            logger.info(f"Quality workflow completed for content {content_id}. Status: {final_status}")
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in quality workflow for content {content_id}: {e}")
            # Return error result
            error_quality_result = QualityCheckResult(
                content_id=content_id,
                content_type=content_type,
                overall_score=0.0,
                status=QualityCheckStatus.FAILED,
                issues=[],
                checks_performed=[],
                metadata={"error": str(e)},
                timestamp=datetime.utcnow()
            )
            
            return QualityWorkflowResult(
                content_id=content_id,
                content_type=content_type,
                quality_check_result=error_quality_result,
                final_status="error",
                workflow_completed_at=datetime.utcnow(),
                total_processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def get_content_quality_summary(
        self,
        content_id: str
    ) -> Dict[str, Any]:
        """Get a summary of content quality and review status."""
        
        if content_id not in self.workflow_history:
            return {"error": "Content not found in workflow history"}
        
        workflow_result = self.workflow_history[content_id]
        quality_result = workflow_result.quality_check_result
        
        summary = {
            "content_id": content_id,
            "content_type": workflow_result.content_type.value,
            "overall_quality_score": quality_result.overall_score,
            "quality_status": quality_result.status.value,
            "final_workflow_status": workflow_result.final_status,
            "total_issues_found": len(quality_result.issues),
            "checks_performed": quality_result.checks_performed,
            "workflow_completed_at": workflow_result.workflow_completed_at.isoformat() if workflow_result.workflow_completed_at else None,
            "total_processing_time": workflow_result.total_processing_time
        }
        
        # Add review information if available
        if workflow_result.review_request:
            review = workflow_result.review_request
            summary.update({
                "review_id": review.review_id,
                "review_status": review.status.value,
                "review_priority": review.priority.value,
                "assigned_reviewer": review.assigned_reviewer,
                "review_deadline": review.deadline.isoformat(),
                "review_notes": review.review_notes
            })
        
        # Add issue breakdown
        issue_breakdown = {}
        for issue in quality_result.issues:
            issue_type = issue.issue_type
            if issue_type not in issue_breakdown:
                issue_breakdown[issue_type] = {"total": 0, "by_severity": {}}
            
            issue_breakdown[issue_type]["total"] += 1
            severity = issue.severity.value
            if severity not in issue_breakdown[issue_type]["by_severity"]:
                issue_breakdown[issue_type]["by_severity"][severity] = 0
            issue_breakdown[issue_type]["by_severity"][severity] += 1
        
        summary["issue_breakdown"] = issue_breakdown
        
        return summary
    
    async def get_workflow_analytics(self) -> Dict[str, Any]:
        """Get analytics about the quality workflow system."""
        
        total_content_processed = len(self.workflow_history)
        if total_content_processed == 0:
            return {"message": "No content has been processed yet"}
        
        # Calculate statistics
        quality_scores = [r.quality_check_result.overall_score for r in self.workflow_history.values()]
        avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        status_counts = {}
        final_status_counts = {}
        
        for workflow_result in self.workflow_history.values():
            # Quality check status counts
            quality_status = workflow_result.quality_check_result.status.value
            status_counts[quality_status] = status_counts.get(quality_status, 0) + 1
            
            # Final workflow status counts
            final_status = workflow_result.final_status
            final_status_counts[final_status] = final_status_counts.get(final_status, 0) + 1
        
        # Processing time statistics
        processing_times = [r.total_processing_time for r in self.workflow_history.values() if r.total_processing_time]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Review workflow statistics
        review_stats = await self.review_workflow.health_check()
        
        analytics = {
            "total_content_processed": total_content_processed,
            "average_quality_score": round(avg_quality_score, 3),
            "quality_status_distribution": status_counts,
            "final_status_distribution": final_status_counts,
            "average_processing_time_seconds": round(avg_processing_time, 3),
            "review_workflow_stats": review_stats,
            "workflow_efficiency": {
                "auto_approved": final_status_counts.get("auto_approved", 0),
                "quality_check_passed": final_status_counts.get("quality_check_passed", 0),
                "submitted_for_review": final_status_counts.get("submitted_for_review", 0),
                "error_rate": final_status_counts.get("error", 0) / total_content_processed if total_content_processed > 0 else 0
            }
        }
        
        return analytics
    
    async def force_content_review(
        self,
        content_id: str,
        reviewer_id: str,
        priority: ReviewPriority = ReviewPriority.HIGH,
        **kwargs
    ) -> ReviewRequest:
        """Force content to be reviewed by a specific reviewer regardless of quality score."""
        
        if content_id not in self.workflow_history:
            raise ValueError(f"Content {content_id} not found in workflow history")
        
        workflow_result = self.workflow_history[content_id]
        
        # Create a review request with forced assignment
        review_request = await self.review_workflow.submit_for_review(
            content_id=content_id,
            content_type=workflow_result.content_type,
            content_preview=workflow_result.quality_check_result.metadata.get("content_preview", "Forced review"),
            target_platforms=workflow_result.quality_check_result.metadata.get("target_platforms", []),
            brand_voice=workflow_result.quality_check_result.metadata.get("brand_voice", "Professional"),
            quality_check_result=workflow_result.quality_check_result,
            requested_by=kwargs.get("requested_by", "system"),
            priority=priority
        )
        
        # Manually assign the specified reviewer
        if reviewer_id:
            await self.review_workflow.assign_reviewer(
                review_request.review_id,
                reviewer_id,
                "system"
            )
        
        # Update workflow result
        workflow_result.review_request = review_request
        workflow_result.final_status = "forced_review"
        
        return review_request
    
    async def get_content_recommendations(
        self,
        content_id: str
    ) -> Dict[str, Any]:
        """Get recommendations for improving content quality."""
        
        if content_id not in self.workflow_history:
            return {"error": "Content not found in workflow history"}
        
        workflow_result = self.workflow_history[content_id]
        quality_result = workflow_result.quality_check_result
        
        recommendations = {
            "content_id": content_id,
            "overall_score": quality_result.overall_score,
            "priority_improvements": [],
            "quick_fixes": [],
            "long_term_improvements": []
        }
        
        # Categorize issues and provide recommendations
        for issue in quality_result.issues:
            if issue.severity.value in ["high", "critical"]:
                recommendations["priority_improvements"].append({
                    "issue": issue.description,
                    "suggestion": issue.suggestion,
                    "location": issue.location
                })
            elif issue.severity.value == "medium":
                recommendations["quick_fixes"].append({
                    "issue": issue.description,
                    "suggestion": issue.suggestion,
                    "location": issue.location
                })
            else:
                recommendations["long_term_improvements"].append({
                    "issue": issue.description,
                    "suggestion": issue.suggestion,
                    "location": issue.location
                })
        
        # Add general recommendations based on content type
        content_type = workflow_result.content_type
        if content_type == ContentType.SOCIAL_MEDIA_POST:
            recommendations["content_type_tips"] = [
                "Use engaging questions to encourage interaction",
                "Include relevant hashtags for discoverability",
                "Keep content concise and impactful",
                "Use emojis strategically to enhance engagement"
            ]
        elif content_type == ContentType.BLOG_POST:
            recommendations["content_type_tips"] = [
                "Break content into digestible sections",
                "Use subheadings for better readability",
                "Include internal and external links",
                "End with a strong call-to-action"
            ]
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the quality orchestrator system."""
        
        quality_checker_health = await self.quality_checker.health_check()
        review_workflow_health = await self.review_workflow.health_check()
        
        return {
            "status": "healthy",
            "service": "ContentQualityOrchestrator",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "quality_checker": quality_checker_health,
                "review_workflow": review_workflow_health
            },
            "workflow_history_size": len(self.workflow_history),
            "system_status": "operational"
        }




