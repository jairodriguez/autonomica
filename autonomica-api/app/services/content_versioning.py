import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import difflib
import re

from .content_types import ContentType, Platform, ContentFormat
from .content_quality_checker import QualityCheckResult

logger = logging.getLogger(__name__)

class VersionStatus(str, Enum):
    """Status of content versions."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"

class ChangeType(str, Enum):
    """Types of changes made to content."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    REPURPOSED = "repurposed"
    TRANSLATED = "translated"
    FORMATTED = "formatted"
    QUALITY_IMPROVED = "quality_improved"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ROLLED_BACK = "rolled_back"

@dataclass
class ContentVersion:
    """Represents a version of content."""
    version_id: str
    content_id: str
    version_number: str  # e.g., "1.0.0", "2.1.3"
    content_hash: str
    content_type: ContentType
    content_format: ContentFormat
    content_data: str
    metadata: Dict[str, Any]
    change_log: str
    change_type: ChangeType
    author_id: str
    created_at: datetime
    parent_version_id: Optional[str] = None
    branch_name: Optional[str] = None
    tags: List[str] = None
    quality_check_result: Optional[QualityCheckResult] = None
    review_status: VersionStatus = VersionStatus.DRAFT
    is_active: bool = True

@dataclass
class VersionDiff:
    """Represents differences between two content versions."""
    from_version: str
    to_version: str
    content_changes: List[Dict[str, Any]]
    metadata_changes: List[Dict[str, Any]]
    change_summary: str
    diff_timestamp: datetime
    diff_author: str

@dataclass
class VersionBranch:
    """Represents a branch in the version tree."""
    branch_name: str
    base_version_id: str
    current_version_id: str
    created_at: datetime
    created_by: str
    is_active: bool = True
    description: Optional[str] = None
    target_platforms: List[Platform] = None

class ContentVersioningService:
    """Service for managing content versioning and change tracking."""
    
    def __init__(self):
        self.versions: Dict[str, ContentVersion] = {}
        self.branches: Dict[str, VersionBranch] = {}
        self.version_counter: Dict[str, int] = {}  # Track version numbers per content
        self.active_versions: Dict[str, str] = {}  # content_id -> active_version_id
        self.version_history: Dict[str, List[str]] = {}  # content_id -> list of version_ids
    
    async def create_version(
        self,
        content_id: str,
        content_data: str,
        content_type: ContentType,
        content_format: ContentFormat,
        author_id: str,
        change_log: str,
        change_type: ChangeType = ChangeType.CREATED,
        parent_version_id: Optional[str] = None,
        branch_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> ContentVersion:
        """Create a new version of content."""
        
        logger.info(f"Creating new version for content {content_id}")
        
        # Generate content hash
        content_hash = self._generate_content_hash(content_data)
        
        # Generate version number
        version_number = self._generate_version_number(content_id, change_type)
        
        # Create version ID
        version_id = f"{content_id}_v{version_number}_{int(datetime.utcnow().timestamp())}"
        
        # Initialize metadata
        if metadata is None:
            metadata = {}
        
        # Add system metadata
        metadata.update({
            "created_at": datetime.utcnow().isoformat(),
            "author_id": author_id,
            "change_type": change_type.value,
            "content_length": len(content_data),
            "word_count": len(content_data.split()),
            "platforms": kwargs.get("target_platforms", []),
            "brand_voice": kwargs.get("brand_voice", "Professional")
        })
        
        # Create version object
        version = ContentVersion(
            version_id=version_id,
            content_id=content_id,
            version_number=version_number,
            content_hash=content_hash,
            content_type=content_type,
            content_format=content_format,
            content_data=content_data,
            metadata=metadata,
            change_log=change_log,
            change_type=change_type,
            author_id=author_id,
            created_at=datetime.utcnow(),
            parent_version_id=parent_version_id,
            branch_name=branch_name,
            tags=tags or [],
            review_status=VersionStatus.DRAFT
        )
        
        # Store version
        self.versions[version_id] = version
        
        # Update version counter
        if content_id not in self.version_counter:
            self.version_counter[content_id] = 0
        self.version_counter[content_id] += 1
        
        # Update version history
        if content_id not in self.version_history:
            self.version_history[content_id] = []
        self.version_history[content_id].append(version_id)
        
        # Set as active version if it's the first one
        if content_id not in self.active_versions:
            self.active_versions[content_id] = version_id
        
        # Handle branch creation
        if branch_name and branch_name not in self.branches:
            await self._create_branch(branch_name, version_id, author_id, **kwargs)
        
        logger.info(f"Created version {version_id} for content {content_id}")
        return version
    
    async def update_version(
        self,
        content_id: str,
        new_content_data: str,
        author_id: str,
        change_log: str,
        change_type: ChangeType = ChangeType.UPDATED,
        branch_name: Optional[str] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ContentVersion:
        """Update existing content with a new version."""
        
        logger.info(f"Updating content {content_id} with new version")
        
        # Get current active version
        current_version_id = self.active_versions.get(content_id)
        if not current_version_id:
            raise ValueError(f"No active version found for content {content_id}")
        
        current_version = self.versions[current_version_id]
        
        # Create new version based on current one
        new_version = await self.create_version(
            content_id=content_id,
            content_data=new_content_data,
            content_type=current_version.content_type,
            content_format=current_version.content_format,
            author_id=author_id,
            change_log=change_log,
            change_type=change_type,
            parent_version_id=current_version_id,
            branch_name=branch_name or current_version.branch_name,
            metadata=self._merge_metadata(current_version.metadata, metadata_updates or {}),
            tags=current_version.tags,
            **kwargs
        )
        
        # Update active version
        self.active_versions[content_id] = new_version.version_id
        
        # Update branch if specified
        if branch_name and branch_name in self.branches:
            self.branches[branch_name].current_version_id = new_version.version_id
        
        logger.info(f"Updated content {content_id} to version {new_version.version_id}")
        return new_version
    
    async def create_branch(
        self,
        branch_name: str,
        base_version_id: str,
        created_by: str,
        description: Optional[str] = None,
        target_platforms: Optional[List[Platform]] = None,
        **kwargs
    ) -> VersionBranch:
        """Create a new branch from an existing version."""
        
        if branch_name in self.branches:
            raise ValueError(f"Branch {branch_name} already exists")
        
        if base_version_id not in self.versions:
            raise ValueError(f"Base version {base_version_id} not found")
        
        branch = VersionBranch(
            branch_name=branch_name,
            base_version_id=base_version_id,
            current_version_id=base_version_id,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=description,
            target_platforms=target_platforms or []
        )
        
        self.branches[branch_name] = branch
        logger.info(f"Created branch {branch_name} from version {base_version_id}")
        return branch
    
    async def merge_branch(
        self,
        source_branch_name: str,
        target_branch_name: str,
        author_id: str,
        merge_strategy: str = "auto",
        **kwargs
    ) -> ContentVersion:
        """Merge changes from one branch to another."""
        
        if source_branch_name not in self.branches:
            raise ValueError(f"Source branch {source_branch_name} not found")
        
        if target_branch_name not in self.branches:
            raise ValueError(f"Target branch {target_branch_name} not found")
        
        source_branch = self.branches[source_branch_name]
        target_branch = self.branches[target_branch_name]
        
        source_version = self.versions[source_branch.current_version_id]
        target_version = self.versions[target_branch.current_version_id]
        
        # Perform merge based on strategy
        if merge_strategy == "auto":
            merged_content = await self._auto_merge_content(
                source_version.content_data,
                target_version.content_data
            )
        elif merge_strategy == "source_wins":
            merged_content = source_version.content_data
        elif merge_strategy == "target_wins":
            merged_content = target_version.content_data
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")
        
        # Create merged version
        merged_version = await self.create_version(
            content_id=target_version.content_id,
            content_data=merged_content,
            content_type=target_version.content_type,
            content_format=target_version.content_format,
            author_id=author_id,
            change_log=f"Merged changes from branch {source_branch_name}",
            change_type=ChangeType.UPDATED,
            parent_version_id=target_version.version_id,
            branch_name=target_branch_name,
            metadata=target_version.metadata
        )
        
        # Update target branch
        target_branch.current_version_id = merged_version.version_id
        
        logger.info(f"Merged branch {source_branch_name} into {target_branch_name}")
        return merged_version
    
    async def rollback_version(
        self,
        content_id: str,
        target_version_id: str,
        author_id: str,
        rollback_reason: str,
        **kwargs
    ) -> ContentVersion:
        """Rollback content to a previous version."""
        
        logger.info(f"Rolling back content {content_id} to version {target_version_id}")
        
        if target_version_id not in self.versions:
            raise ValueError(f"Target version {target_version_id} not found")
        
        target_version = self.versions[target_version_id]
        
        # Create rollback version
        rollback_version = await self.create_version(
            content_id=content_id,
            content_data=target_version.content_data,
            content_type=target_version.content_type,
            content_format=target_version.content_format,
            author_id=author_id,
            change_log=f"Rollback to version {target_version_id}: {rollback_reason}",
            change_type=ChangeType.ROLLED_BACK,
            parent_version_id=self.active_versions.get(content_id),
            branch_name=target_version.branch_name,
            metadata=target_version.metadata,
            tags=target_version.tags + ["rollback"]
        )
        
        # Update active version
        self.active_versions[content_id] = rollback_version.version_id
        
        logger.info(f"Rolled back content {content_id} to version {target_version_id}")
        return rollback_version
    
    async def get_version_history(
        self,
        content_id: str,
        include_metadata: bool = True,
        include_content: bool = False,
        limit: Optional[int] = None
    ) -> List[ContentVersion]:
        """Get version history for a specific content item."""
        
        if content_id not in self.version_history:
            return []
        
        version_ids = self.version_history[content_id]
        if limit:
            version_ids = version_ids[-limit:]
        
        versions = []
        for version_id in version_ids:
            version = self.versions[version_id]
            
            # Create a copy with optional data filtering
            version_copy = ContentVersion(
                version_id=version.version_id,
                content_id=version.content_id,
                version_number=version.version_number,
                content_hash=version.content_hash,
                content_type=version.content_type,
                content_format=version.content_format,
                content_data=version.content_data if include_content else "",
                metadata=version.metadata if include_metadata else {},
                change_log=version.change_log,
                change_type=version.change_type,
                author_id=version.author_id,
                created_at=version.created_at,
                parent_version_id=version.parent_version_id,
                branch_name=version.branch_name,
                tags=version.tags,
                quality_check_result=version.quality_check_result,
                review_status=version.review_status,
                is_active=version.is_active
            )
            versions.append(version_copy)
        
        return versions
    
    async def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> VersionDiff:
        """Compare two versions of content."""
        
        if version_id_1 not in self.versions or version_id_2 not in self.versions:
            raise ValueError("One or both versions not found")
        
        version_1 = self.versions[version_id_1]
        version_2 = self.versions[version_id_2]
        
        # Generate content diff
        content_changes = self._generate_content_diff(
            version_1.content_data,
            version_2.content_data
        )
        
        # Generate metadata diff
        metadata_changes = self._generate_metadata_diff(
            version_1.metadata,
            version_2.metadata
        )
        
        # Create change summary
        change_summary = self._create_change_summary(content_changes, metadata_changes)
        
        diff = VersionDiff(
            from_version=version_id_1,
            to_version=version_id_2,
            content_changes=content_changes,
            metadata_changes=metadata_changes,
            change_summary=change_summary,
            diff_timestamp=datetime.utcnow(),
            diff_author="system"
        )
        
        return diff
    
    async def get_active_version(self, content_id: str) -> Optional[ContentVersion]:
        """Get the currently active version of content."""
        
        active_version_id = self.active_versions.get(content_id)
        if not active_version_id:
            return None
        
        return self.versions.get(active_version_id)
    
    async def archive_version(
        self,
        version_id: str,
        author_id: str,
        archive_reason: str
    ) -> bool:
        """Archive a specific version of content."""
        
        if version_id not in self.versions:
            return False
        
        version = self.versions[version_id]
        version.review_status = VersionStatus.ARCHIVED
        version.is_active = False
        
        # Add archive metadata
        version.metadata["archived_at"] = datetime.utcnow().isoformat()
        version.metadata["archived_by"] = author_id
        version.metadata["archive_reason"] = archive_reason
        
        # If this was the active version, find the next most recent active version
        if self.active_versions.get(version.content_id) == version_id:
            content_versions = await self.get_version_history(version.content_id)
            for v in reversed(content_versions):
                if v.is_active and v.version_id != version_id:
                    self.active_versions[version.content_id] = v.version_id
                    break
        
        logger.info(f"Archived version {version_id}")
        return True
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content to detect changes."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _generate_version_number(self, content_id: str, change_type: ChangeType) -> str:
        """Generate semantic version number based on change type."""
        
        if change_type == ChangeType.CREATED:
            return "1.0.0"
        
        # Get current version number
        current_version = self.active_versions.get(content_id)
        if not current_version:
            return "1.0.0"
        
        current_version_obj = self.versions.get(current_version)
        if not current_version_obj:
            return "1.0.0"
        
        # Parse current version
        try:
            major, minor, patch = map(int, current_version_obj.version_number.split('.'))
        except (ValueError, AttributeError):
            major, minor, patch = 1, 0, 0
        
        # Increment based on change type
        if change_type in [ChangeType.REPURPOSED, ChangeType.TRANSLATED]:
            major += 1
            minor = 0
            patch = 0
        elif change_type in [ChangeType.UPDATED, ChangeType.QUALITY_IMPROVED]:
            minor += 1
            patch = 0
        else:
            patch += 1
        
        return f"{major}.{minor}.{patch}"
    
    def _merge_metadata(self, base_metadata: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge metadata updates with base metadata."""
        merged = base_metadata.copy()
        
        for key, value in updates.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Deep merge for nested dictionaries
                merged[key] = self._merge_metadata(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    async def _auto_merge_content(
        self,
        source_content: str,
        target_content: str
    ) -> str:
        """Automatically merge content from two versions."""
        
        # Simple merge strategy: combine unique content
        source_lines = set(source_content.split('\n'))
        target_lines = set(target_content.split('\n'))
        
        # Find unique lines from source
        unique_source_lines = source_lines - target_lines
        
        # Combine content
        merged_lines = list(target_lines) + list(unique_source_lines)
        
        return '\n'.join(merged_lines)
    
    def _generate_content_diff(
        self,
        content_1: str,
        content_2: str
    ) -> List[Dict[str, Any]]:
        """Generate diff between two content strings."""
        
        diff = difflib.unified_diff(
            content_1.splitlines(keepends=True),
            content_2.splitlines(keepends=True),
            fromfile="version_1",
            tofile="version_2"
        )
        
        changes = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                changes.append({
                    "type": "addition",
                    "line": line[1:].rstrip(),
                    "change": "added"
                })
            elif line.startswith('-') and not line.startswith('---'):
                changes.append({
                    "type": "deletion",
                    "line": line[1:].rstrip(),
                    "change": "removed"
                })
        
        return changes
    
    def _generate_metadata_diff(
        self,
        metadata_1: Dict[str, Any],
        metadata_2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate diff between two metadata dictionaries."""
        
        changes = []
        all_keys = set(metadata_1.keys()) | set(metadata_2.keys())
        
        for key in all_keys:
            if key not in metadata_1:
                changes.append({
                    "type": "addition",
                    "field": key,
                    "old_value": None,
                    "new_value": metadata_2[key],
                    "change": "added"
                })
            elif key not in metadata_2:
                changes.append({
                    "type": "deletion",
                    "field": key,
                    "old_value": metadata_1[key],
                    "new_value": None,
                    "change": "removed"
                })
            elif metadata_1[key] != metadata_2[key]:
                changes.append({
                    "type": "modification",
                    "field": key,
                    "old_value": metadata_1[key],
                    "new_value": metadata_2[key],
                    "change": "modified"
                })
        
        return changes
    
    def _create_change_summary(
        self,
        content_changes: List[Dict[str, Any]],
        metadata_changes: List[Dict[str, Any]]
    ) -> str:
        """Create a human-readable summary of changes."""
        
        content_additions = len([c for c in content_changes if c["type"] == "addition"])
        content_deletions = len([c for c in content_changes if c["type"] == "deletion"])
        metadata_changes_count = len(metadata_changes)
        
        summary_parts = []
        
        if content_additions > 0:
            summary_parts.append(f"{content_additions} content additions")
        if content_deletions > 0:
            summary_parts.append(f"{content_deletions} content deletions")
        if metadata_changes_count > 0:
            summary_parts.append(f"{metadata_changes_count} metadata changes")
        
        if not summary_parts:
            return "No changes detected"
        
        return f"Changes: {', '.join(summary_parts)}"
    
    async def _create_branch(
        self,
        branch_name: str,
        base_version_id: str,
        created_by: str,
        **kwargs
    ) -> VersionBranch:
        """Internal method to create a branch."""
        
        branch = VersionBranch(
            branch_name=branch_name,
            base_version_id=base_version_id,
            current_version_id=base_version_id,
            created_at=datetime.utcnow(),
            created_by=created_by,
            description=kwargs.get("description"),
            target_platforms=kwargs.get("target_platforms", [])
        )
        
        self.branches[branch_name] = branch
        return branch
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the versioning system."""
        
        total_versions = len(self.versions)
        total_branches = len(self.branches)
        active_content = len(self.active_versions)
        
        return {
            "status": "healthy",
            "service": "ContentVersioningService",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": {
                "total_versions": total_versions,
                "total_branches": total_branches,
                "active_content": active_content,
                "version_counter": self.version_counter
            },
            "system_status": "operational"
        }




