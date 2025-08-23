import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.content_versioning import (
    ContentVersioningService, ContentVersion, VersionStatus, ChangeType,
    VersionDiff, VersionBranch
)
from app.services.content_types import ContentType, Platform, ContentFormat
from app.services.content_quality_checker import QualityCheckResult, QualityCheckStatus

class TestContentVersioning:
    """Test cases for the ContentVersioningService."""
    
    @pytest.fixture
    def versioning_service(self):
        return ContentVersioningService()
    
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
    async def test_create_version_success(self, versioning_service, sample_content, sample_metadata):
        """Test successful version creation."""
        
        version = await versioning_service.create_version(
            content_id="test_001",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation",
            metadata=sample_metadata,
            tags=["test", "blog"]
        )
        
        assert isinstance(version, ContentVersion)
        assert version.content_id == "test_001"
        assert version.content_data == sample_content
        assert version.content_type == ContentType.BLOG_POST
        assert version.content_format == ContentFormat.MARKDOWN
        assert version.author_id == "user_001"
        assert version.change_log == "Initial content creation"
        assert version.change_type == ChangeType.CREATED
        assert version.version_number == "1.0.0"
        assert version.review_status == VersionStatus.DRAFT
        assert version.is_active is True
        assert "test" in version.tags
        assert "blog" in version.tags
        
        # Check that version is stored
        assert version.version_id in versioning_service.versions
        assert versioning_service.active_versions["test_001"] == version.version_id
        assert "test_001" in versioning_service.version_history
    
    @pytest.mark.asyncio
    async def test_update_version_success(self, versioning_service, sample_content, sample_metadata):
        """Test successful version update."""
        
        # Create initial version
        initial_version = await versioning_service.create_version(
            content_id="test_002",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation",
            metadata=sample_metadata
        )
        
        # Update content
        updated_content = "This is an updated blog post content with new information."
        updated_version = await versioning_service.update_version(
            content_id="test_002",
            new_content_data=updated_content,
            author_id="user_001",
            change_log="Updated content with new information",
            change_type=ChangeType.UPDATED
        )
        
        assert isinstance(updated_version, ContentVersion)
        assert updated_version.content_data == updated_content
        assert updated_version.change_log == "Updated content with new information"
        assert updated_version.change_type == ChangeType.UPDATED
        assert updated_version.version_number == "1.1.0"
        assert updated_version.parent_version_id == initial_version.version_id
        
        # Check that active version is updated
        assert versioning_service.active_versions["test_002"] == updated_version.version_id
    
    @pytest.mark.asyncio
    async def test_create_branch_success(self, versioning_service, sample_content):
        """Test successful branch creation."""
        
        # Create initial version
        version = await versioning_service.create_version(
            content_id="test_003",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Create branch
        branch = await versioning_service.create_branch(
            branch_name="feature-branch",
            base_version_id=version.version_id,
            created_by="user_001",
            description="Feature development branch",
            target_platforms=[Platform.WEBSITE, Platform.TWITTER]
        )
        
        assert isinstance(branch, VersionBranch)
        assert branch.branch_name == "feature-branch"
        assert branch.base_version_id == version.version_id
        assert branch.current_version_id == version.version_id
        assert branch.created_by == "user_001"
        assert branch.description == "Feature development branch"
        assert Platform.WEBSITE in branch.target_platforms
        assert Platform.TWITTER in branch.target_platforms
        
        # Check that branch is stored
        assert "feature-branch" in versioning_service.branches
    
    @pytest.mark.asyncio
    async def test_merge_branch_success(self, versioning_service, sample_content):
        """Test successful branch merge."""
        
        # Create initial version
        version = await versioning_service.create_version(
            content_id="test_004",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Create source branch
        source_branch = await versioning_service.create_branch(
            branch_name="source-branch",
            base_version_id=version.version_id,
            created_by="user_001"
        )
        
        # Create target branch
        target_branch = await versioning_service.create_branch(
            branch_name="target-branch",
            base_version_id=version.version_id,
            created_by="user_001"
        )
        
        # Update source branch with new content
        source_version = await versioning_service.update_version(
            content_id="test_004",
            new_content_data="Updated content in source branch",
            author_id="user_001",
            change_log="Updated in source branch",
            branch_name="source-branch"
        )
        
        # Update target branch with different content
        target_version = await versioning_service.update_version(
            content_id="test_004",
            new_content_data="Updated content in target branch",
            author_id="user_001",
            change_log="Updated in target branch",
            branch_name="target-branch"
        )
        
        # Merge source into target
        merged_version = await versioning_service.merge_branch(
            source_branch_name="source-branch",
            target_branch_name="target-branch",
            author_id="user_001",
            merge_strategy="auto"
        )
        
        assert isinstance(merged_version, ContentVersion)
        assert merged_version.change_log == "Merged changes from branch source-branch"
        assert merged_version.change_type == ChangeType.UPDATED
        
        # Check that target branch is updated
        assert versioning_service.branches["target-branch"].current_version_id == merged_version.version_id
    
    @pytest.mark.asyncio
    async def test_rollback_version_success(self, versioning_service, sample_content):
        """Test successful version rollback."""
        
        # Create initial version
        initial_version = await versioning_service.create_version(
            content_id="test_005",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Update content
        updated_version = await versioning_service.update_version(
            content_id="test_005",
            new_content_data="Updated content that will be rolled back",
            author_id="user_001",
            change_log="Update before rollback"
        )
        
        # Rollback to initial version
        rollback_version = await versioning_service.rollback_version(
            content_id="test_005",
            target_version_id=initial_version.version_id,
            author_id="user_001",
            rollback_reason="Testing rollback functionality"
        )
        
        assert isinstance(rollback_version, ContentVersion)
        assert rollback_version.content_data == initial_version.content_data
        assert rollback_version.change_type == ChangeType.ROLLED_BACK
        assert "rollback" in rollback_version.tags
        assert rollback_version.change_log.startswith("Rollback to version")
        
        # Check that active version is updated
        assert versioning_service.active_versions["test_005"] == rollback_version.version_id
    
    @pytest.mark.asyncio
    async def test_get_version_history(self, versioning_service, sample_content):
        """Test getting version history."""
        
        # Create multiple versions
        version1 = await versioning_service.create_version(
            content_id="test_006",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Version 1"
        )
        
        version2 = await versioning_service.update_version(
            content_id="test_006",
            new_content_data="Updated content",
            author_id="user_001",
            change_log="Version 2"
        )
        
        version3 = await versioning_service.update_version(
            content_id="test_006",
            new_content_data="Further updated content",
            author_id="user_001",
            change_log="Version 3"
        )
        
        # Get full history
        history = await versioning_service.get_version_history("test_006", include_content=True)
        assert len(history) == 3
        
        # Check order (most recent first)
        assert history[0].version_id == version3.version_id
        assert history[1].version_id == version2.version_id
        assert history[2].version_id == version1.version_id
        
        # Get limited history
        limited_history = await versioning_service.get_version_history("test_006", limit=2)
        assert len(limited_history) == 2
        assert limited_history[0].version_id == version3.version_id
        assert limited_history[1].version_id == version2.version_id
    
    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning_service, sample_content):
        """Test version comparison."""
        
        # Create initial version
        version1 = await versioning_service.create_version(
            content_id="test_007",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Version 1"
        )
        
        # Create updated version
        version2 = await versioning_service.update_version(
            content_id="test_007",
            new_content_data="Updated content with changes",
            author_id="user_001",
            change_log="Version 2"
        )
        
        # Compare versions
        diff = await versioning_service.compare_versions(version1.version_id, version2.version_id)
        
        assert isinstance(diff, VersionDiff)
        assert diff.from_version == version1.version_id
        assert diff.to_version == version2.version_id
        assert len(diff.content_changes) > 0
        assert "Changes:" in diff.change_summary
    
    @pytest.mark.asyncio
    async def test_get_active_version(self, versioning_service, sample_content):
        """Test getting active version."""
        
        # Create version
        version = await versioning_service.create_version(
            content_id="test_008",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Get active version
        active_version = await versioning_service.get_active_version("test_008")
        
        assert active_version is not None
        assert active_version.version_id == version.version_id
        assert active_version.content_data == sample_content
    
    @pytest.mark.asyncio
    async def test_archive_version_success(self, versioning_service, sample_content):
        """Test successful version archiving."""
        
        # Create version
        version = await versioning_service.create_version(
            content_id="test_009",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Archive version
        success = await versioning_service.archive_version(
            version_id=version.version_id,
            author_id="user_001",
            archive_reason="Testing archive functionality"
        )
        
        assert success is True
        
        # Check that version is archived
        archived_version = versioning_service.versions[version.version_id]
        assert archived_version.review_status == VersionStatus.ARCHIVED
        assert archived_version.is_active is False
        assert "archived_at" in archived_version.metadata
        assert "archived_by" in archived_version.metadata
        assert "archive_reason" in archived_version.metadata
    
    @pytest.mark.asyncio
    async def test_version_number_generation(self, versioning_service, sample_content):
        """Test semantic version number generation."""
        
        # Test initial version
        version1 = await versioning_service.create_version(
            content_id="test_010",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        assert version1.version_number == "1.0.0"
        
        # Test minor update
        version2 = await versioning_service.update_version(
            content_id="test_010",
            new_content_data="Updated content",
            author_id="user_001",
            change_log="Minor update",
            change_type=ChangeType.UPDATED
        )
        assert version2.version_number == "1.1.0"
        
        # Test major update (repurposed)
        version3 = await versioning_service.update_version(
            content_id="test_010",
            new_content_data="Repurposed content",
            author_id="user_001",
            change_log="Major repurposing",
            change_type=ChangeType.REPURPOSED
        )
        assert version3.version_number == "2.0.0"
        
        # Test patch update
        version4 = await versioning_service.update_version(
            content_id="test_010",
            new_content_data="Minor formatting change",
            author_id="user_001",
            change_log="Formatting update",
            change_type=ChangeType.FORMATTED
        )
        assert version4.version_number == "2.0.1"
    
    @pytest.mark.asyncio
    async def test_metadata_merging(self, versioning_service, sample_content):
        """Test metadata merging functionality."""
        
        # Create initial version with metadata
        initial_metadata = {"title": "Initial Title", "author": "Author 1"}
        version1 = await versioning_service.create_version(
            content_id="test_011",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation",
            metadata=initial_metadata
        )
        
        # Update with new metadata
        metadata_updates = {"title": "Updated Title", "category": "Technology"}
        version2 = await versioning_service.update_version(
            content_id="test_011",
            new_content_data="Updated content",
            author_id="user_001",
            change_log="Update with metadata changes",
            metadata_updates=metadata_updates
        )
        
        # Check that metadata is merged correctly
        assert version2.metadata["title"] == "Updated Title"
        assert version2.metadata["author"] == "Author 1"  # Preserved from original
        assert version2.metadata["category"] == "Technology"  # Added from update
    
    @pytest.mark.asyncio
    async def test_content_hash_generation(self, versioning_service, sample_content):
        """Test content hash generation for change detection."""
        
        # Create version
        version = await versioning_service.create_version(
            content_id="test_012",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Initial content creation"
        )
        
        # Check that hash is generated
        assert version.content_hash is not None
        assert len(version.content_hash) == 64  # SHA-256 hash length
        
        # Create version with same content (should have same hash)
        version2 = await versioning_service.create_version(
            content_id="test_013",
            content_data=sample_content,
            content_type=ContentType.BLOG_POST,
            content_format=ContentFormat.MARKDOWN,
            author_id="user_001",
            change_log="Same content, different ID"
        )
        
        assert version.content_hash == version2.content_hash
    
    @pytest.mark.asyncio
    async def test_error_handling(self, versioning_service, sample_content):
        """Test error handling for invalid operations."""
        
        # Test updating non-existent content
        with pytest.raises(ValueError, match="No active version found"):
            await versioning_service.update_version(
                content_id="non_existent",
                new_content_data="New content",
                author_id="user_001",
                change_log="Update non-existent content"
            )
        
        # Test creating branch with non-existent version
        with pytest.raises(ValueError, match="Base version.*not found"):
            await versioning_service.create_branch(
                branch_name="test-branch",
                base_version_id="non_existent_version",
                created_by="user_001"
            )
        
        # Test comparing non-existent versions
        with pytest.raises(ValueError, match="One or both versions not found"):
            await versioning_service.compare_versions("version1", "version2")
    
    @pytest.mark.asyncio
    async def test_health_check(self, versioning_service):
        """Test health check functionality."""
        
        health_status = await versioning_service.health_check()
        
        assert isinstance(health_status, dict)
        assert health_status["status"] == "healthy"
        assert health_status["service"] == "ContentVersioningService"
        assert "timestamp" in health_status
        assert "statistics" in health_status
        assert "system_status" in health_status
        
        # Check statistics
        stats = health_status["statistics"]
        assert "total_versions" in stats
        assert "total_branches" in stats
        assert "active_content" in stats
        assert "version_counter" in stats

if __name__ == "__main__":
    pytest.main([__file__])




