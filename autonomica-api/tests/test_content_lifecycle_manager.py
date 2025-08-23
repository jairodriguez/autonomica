import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.content_lifecycle_manager import (
    ContentLifecycleManager, ContentLifecycleState, LifecycleStage,
    ApprovalStatus, LifecycleTransition
)
from app.services.content_types import ContentType, Platform, ContentFormat
from app.services.content_versioning import ChangeType
from app.services.content_quality_checker import QualityCheckResult, QualityCheckStatus
from app.services.content_review_workflow import ReviewPriority

class TestContentLifecycleManager:
    """Test cases for the ContentLifecycleManager."""
    
    @pytest.fixture
    def lifecycle_manager(self):
        return ContentLifecycleManager()
    
    @pytest.fixture
    def sample_content(self):
        return "This is a sample blog post content for testing purposes."
    
    @pytest.fixture
    def sample_metadata(self):
        return {
            "title": "Test Blog Post",
            "author": "Test Author",
            "category": "Technology"
        }
    
    @pytest.mark.asyncio
    async def test_create_content_success(self, lifecycle_manager, sample_content, sample_metadata):
        """Test successful content creation with lifecycle initialization."""
        
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_001",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE, Platform.TWITTER],
            brand_voice="Professional and engaging",
            tags=["test", "blog"],
            metadata=sample_metadata
        )
        
        assert isinstance(version, ContentVersion)
        assert isinstance(lifecycle_state, ContentLifecycleState)
        assert lifecycle_state.content_id == "test_001"
        assert lifecycle_state.current_stage == LifecycleStage.DRAFT
        assert lifecycle_state.approval_status == ApprovalStatus.PENDING
        assert lifecycle_state.current_version_id == version.version_id
        assert lifecycle_state.last_modified is not None
        
        # Check that lifecycle state is stored
        assert "test_001" in lifecycle_manager.lifecycle_states
        assert "test_001" in lifecycle_manager.transition_history
    
    @pytest.mark.asyncio
    async def test_submit_for_review_success(self, lifecycle_manager, sample_content):
        """Test successful content submission for review."""
        
        # Create content first
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_002",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE],
            brand_voice="Professional"
        )
        
        # Mock the review workflow to avoid dependency issues
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_001"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            # Submit for review
            success = await lifecycle_manager.submit_for_review(
                content_id="test_002",
                author_id="user_001",
                review_priority=ReviewPriority.NORMAL
            )
            
            assert success is True
            
            # Check lifecycle state changes
            updated_state = lifecycle_manager.lifecycle_states["test_002"]
            assert updated_state.current_stage == LifecycleStage.IN_REVIEW
            assert updated_state.assigned_reviewer == "reviewer_001"
            assert updated_state.review_deadline is not None
            
            # Check transition history
            transitions = lifecycle_manager.transition_history["test_002"]
            assert len(transitions) == 2  # Created + Submitted for review
            assert transitions[-1].to_stage == LifecycleStage.IN_REVIEW
            assert transitions[-1].transition_reason == "Submitted for review"
    
    @pytest.mark.asyncio
    async def test_approve_content_success(self, lifecycle_manager, sample_content):
        """Test successful content approval."""
        
        # Create and submit content for review
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_003",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Mock review workflow
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_002"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            await lifecycle_manager.submit_for_review("test_003", "user_001")
        
        # Approve content
        scheduled_publish = datetime.utcnow() + timedelta(days=1)
        success = await lifecycle_manager.approve_content(
            content_id="test_003",
            reviewer_id="reviewer_001",
            approval_notes="Content looks great!",
            scheduled_publish_date=scheduled_publish
        )
        
        assert success is True
        
        # Check lifecycle state changes
        updated_state = lifecycle_manager.lifecycle_states["test_003"]
        assert updated_state.current_stage == LifecycleStage.APPROVED
        assert updated_state.approval_status == ApprovalStatus.APPROVED
        assert updated_state.scheduled_publish_date == scheduled_publish
        
        # Check transition history
        transitions = lifecycle_manager.transition_history["test_003"]
        assert len(transitions) == 3  # Created + Submitted + Approved
        assert transitions[-1].to_stage == LifecycleStage.APPROVED
        assert transitions[-1].transition_reason == "Content approved"
    
    @pytest.mark.asyncio
    async def test_reject_content_success(self, lifecycle_manager, sample_content):
        """Test successful content rejection."""
        
        # Create and submit content for review
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_004",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Mock review workflow
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_003"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            await lifecycle_manager.submit_for_review("test_004", "user_001")
        
        # Reject content with revision required
        success = await lifecycle_manager.reject_content(
            content_id="test_004",
            reviewer_id="reviewer_001",
            rejection_reason="Content needs more detail",
            revision_required=True
        )
        
        assert success is True
        
        # Check lifecycle state changes
        updated_state = lifecycle_manager.lifecycle_states["test_004"]
        assert updated_state.current_stage == LifecycleStage.DRAFT
        assert updated_state.approval_status == ApprovalStatus.NEEDS_REVISION
        
        # Check transition history
        transitions = lifecycle_manager.transition_history["test_004"]
        assert len(transitions) == 3  # Created + Submitted + Rejected
        assert transitions[-1].to_stage == LifecycleStage.DRAFT
        assert "Content rejected" in transitions[-1].transition_reason
    
    @pytest.mark.asyncio
    async def test_publish_content_success(self, lifecycle_manager, sample_content):
        """Test successful content publication."""
        
        # Create, submit, and approve content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_005",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Mock review workflow
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_004"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            await lifecycle_manager.submit_for_review("test_005", "user_001")
        
        # Approve content
        await lifecycle_manager.approve_content("test_005", "reviewer_001")
        
        # Publish content
        success = await lifecycle_manager.publish_content(
            content_id="test_005",
            publisher_id="publisher_001",
            publish_notes="Published to website"
        )
        
        assert success is True
        
        # Check lifecycle state changes
        updated_state = lifecycle_manager.lifecycle_states["test_005"]
        assert updated_state.current_stage == LifecycleStage.PUBLISHED
        assert updated_state.actual_publish_date is not None
        
        # Check transition history
        transitions = lifecycle_manager.transition_history["test_005"]
        assert len(transitions) == 4  # Created + Submitted + Approved + Published
        assert transitions[-1].to_stage == LifecycleStage.PUBLISHED
        assert transitions[-1].transition_reason == "Content published"
    
    @pytest.mark.asyncio
    async def test_update_content_success(self, lifecycle_manager, sample_content):
        """Test successful content update with lifecycle reset."""
        
        # Create and publish content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_006",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Mock review workflow and approve
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_005"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            await lifecycle_manager.submit_for_review("test_006", "user_001")
        
        await lifecycle_manager.approve_content("test_006", "reviewer_001")
        await lifecycle_manager.publish_content("test_006", "publisher_001")
        
        # Update content
        updated_content = "This is updated content with new information."
        new_version = await lifecycle_manager.update_content(
            content_id="test_006",
            new_content_data=updated_content,
            author_id="user_001",
            change_log="Added new information",
            change_type=ChangeType.UPDATED
        )
        
        assert isinstance(new_version, ContentVersion)
        assert new_version.content_data == updated_content
        
        # Check lifecycle state reset
        updated_state = lifecycle_manager.lifecycle_states["test_006"]
        assert updated_state.current_stage == LifecycleStage.DRAFT
        assert updated_state.approval_status == ApprovalStatus.PENDING
        assert updated_state.current_version_id == new_version.version_id
        assert updated_state.assigned_reviewer is None
        assert updated_state.review_deadline is None
        assert updated_state.scheduled_publish_date is None
        
        # Check transition history
        transitions = lifecycle_manager.transition_history["test_006"]
        assert len(transitions) == 5  # Created + Submitted + Approved + Published + Updated
        assert transitions[-1].to_stage == LifecycleStage.DRAFT
        assert "Content updated" in transitions[-1].transition_reason
    
    @pytest.mark.asyncio
    async def test_archive_content_success(self, lifecycle_manager, sample_content):
        """Test successful content archiving."""
        
        # Create and publish content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_007",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Mock review workflow and approve
        with patch.object(lifecycle_manager.review_workflow, 'submit_for_review') as mock_submit:
            mock_review_request = Mock()
            mock_review_request.review_id = "review_006"
            mock_review_request.assigned_reviewer = "reviewer_001"
            mock_review_request.deadline = datetime.utcnow() + timedelta(days=3)
            mock_submit.return_value = mock_review_request
            
            await lifecycle_manager.submit_for_review("test_007", "user_001")
        
        await lifecycle_manager.approve_content("test_007", "reviewer_001")
        await lifecycle_manager.publish_content("test_007", "publisher_001")
        
        # Archive content
        success = await lifecycle_manager.archive_content(
            content_id="test_007",
            archiver_id="archiver_001",
            archive_reason="Content is outdated"
        )
        
        assert success is True
        
        # Check lifecycle state changes
        updated_state = lifecycle_manager.lifecycle_states["test_007"]
        assert updated_state.current_stage == LifecycleStage.ARCHIVED
        assert updated_state.archive_date is not None
        
        # Check transition history
        transitions = lifecycle_manager.transition_history["test_007"]
        assert len(transitions) == 5  # Created + Submitted + Approved + Published + Archived
        assert transitions[-1].to_stage == LifecycleStage.ARCHIVED
        assert "Content archived" in transitions[-1].transition_reason
    
    @pytest.mark.asyncio
    async def test_get_lifecycle_state(self, lifecycle_manager, sample_content):
        """Test getting lifecycle state."""
        
        # Create content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_008",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Get lifecycle state
        retrieved_state = await lifecycle_manager.get_lifecycle_state("test_008")
        
        assert retrieved_state is not None
        assert retrieved_state.content_id == "test_008"
        assert retrieved_state.current_stage == LifecycleStage.DRAFT
        assert retrieved_state.approval_status == ApprovalStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_get_transition_history(self, lifecycle_manager, sample_content):
        """Test getting transition history."""
        
        # Create content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_009",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Get transition history
        transitions = await lifecycle_manager.get_transition_history("test_009")
        
        assert len(transitions) == 1  # Created
        assert transitions[0].to_stage == LifecycleStage.DRAFT
        assert transitions[0].transition_reason == "Content created"
        
        # Get limited history
        limited_transitions = await lifecycle_manager.get_transition_history("test_009", limit=1)
        assert len(limited_transitions) == 1
    
    @pytest.mark.asyncio
    async def test_get_content_by_stage(self, lifecycle_manager, sample_content):
        """Test getting content by lifecycle stage."""
        
        # Create multiple content items
        await lifecycle_manager.create_content(
            content_id="test_010",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        await lifecycle_manager.create_content(
            content_id="test_011",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Get content by stage
        draft_content = await lifecycle_manager.get_content_by_stage(LifecycleStage.DRAFT)
        assert len(draft_content) >= 2
        
        # Get limited content
        limited_draft = await lifecycle_manager.get_content_by_stage(LifecycleStage.DRAFT, limit=1)
        assert len(limited_draft) == 1
    
    @pytest.mark.asyncio
    async def test_get_content_summary(self, lifecycle_manager, sample_content):
        """Test getting content lifecycle summary."""
        
        # Create content
        version, lifecycle_state = await lifecycle_manager.create_content(
            content_id="test_012",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            target_platforms=[Platform.WEBSITE]
        )
        
        # Get content summary
        summary = await lifecycle_manager.get_content_summary("test_012")
        
        assert isinstance(summary, dict)
        assert summary["content_id"] == "test_012"
        assert summary["current_stage"] == LifecycleStage.DRAFT.value
        assert summary["approval_status"] == ApprovalStatus.PENDING.value
        assert "current_version" in summary
        assert "lifecycle_metadata" in summary
        assert "review_info" in summary
        assert "transition_count" in summary
    
    @pytest.mark.asyncio
    async def test_error_handling(self, lifecycle_manager, sample_content):
        """Test error handling for invalid operations."""
        
        # Test submitting non-existent content for review
        with pytest.raises(ValueError, match="Content.*not found in lifecycle"):
            await lifecycle_manager.submit_for_review("non_existent", "user_001")
        
        # Test approving content not in review stage
        with pytest.raises(ValueError, match="Content must be in IN_REVIEW stage"):
            await lifecycle_manager.approve_content("non_existent", "reviewer_001")
        
        # Test rejecting content not in review stage
        with pytest.raises(ValueError, match="Content must be in IN_REVIEW stage"):
            await lifecycle_manager.reject_content("non_existent", "reviewer_001")
        
        # Test publishing content not in approved stage
        with pytest.raises(ValueError, match="Content must be in APPROVED stage"):
            await lifecycle_manager.publish_content("non_existent", "publisher_001")
        
        # Test archiving content not in published/approved stage
        with pytest.raises(ValueError, match="Content must be PUBLISHED or APPROVED"):
            await lifecycle_manager.archive_content("non_existent", "archiver_001", "test")
    
    @pytest.mark.asyncio
    async def test_lifecycle_policies(self, lifecycle_manager):
        """Test lifecycle policies initialization."""
        
        policies = lifecycle_manager.lifecycle_policies
        
        assert "stage_transitions" in policies
        assert "auto_transitions" in policies
        assert "required_approvals" in policies
        
        # Check stage transitions
        stage_transitions = policies["stage_transitions"]
        assert LifecycleStage.DRAFT in stage_transitions
        assert LifecycleStage.IN_REVIEW in stage_transitions
        assert LifecycleStage.APPROVED in stage_transitions
        assert LifecycleStage.PUBLISHED in stage_transitions
        
        # Check auto transitions
        auto_transitions = policies["auto_transitions"]
        assert "publish_after_approval" in auto_transitions
        assert "archive_after_days" in auto_transitions
        assert "review_timeout_days" in auto_transitions
        
        # Check required approvals
        required_approvals = policies["required_approvals"]
        assert ContentType.BLOG_POST in required_approvals
        assert ContentType.VIDEO_SCRIPT in required_approvals
    
    @pytest.mark.asyncio
    async def test_health_check(self, lifecycle_manager):
        """Test health check functionality."""
        
        health_status = await lifecycle_manager.health_check()
        
        assert isinstance(health_status, dict)
        assert health_status["status"] == "healthy"
        assert health_status["service"] == "ContentLifecycleManager"
        assert "timestamp" in health_status
        assert "statistics" in health_status
        assert "components" in health_status
        
        # Check statistics
        stats = health_status["statistics"]
        assert "total_content" in stats
        assert "stage_distribution" in stats
        assert "approval_distribution" in stats
        
        # Check components
        components = health_status["components"]
        assert "versioning_service" in components
        assert "quality_checker" in components
        assert "review_workflow" in components

if __name__ == "__main__":
    pytest.main([__file__])




