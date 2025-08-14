import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from content_types_simple import ContentType, ContentFormat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VersionStatus(str, Enum):
    """Status of content versions"""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


class ChangeType(str, Enum):
    """Types of changes made to content"""
    CREATED = "created"
    UPDATED = "updated"
    REPURPOSED = "repurposed"
    QUALITY_CHECKED = "quality_checked"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    ROLLBACK = "rollback"


@dataclass
class ContentVersion:
    """Represents a version of content"""
    version_id: str
    content_id: str
    version_number: int
    content: str
    content_type: ContentType
    format: ContentFormat
    metadata: Dict[str, Any]
    status: VersionStatus
    created_at: datetime
    created_by: str
    parent_version_id: Optional[str] = None
    change_summary: Optional[str] = None
    quality_score: Optional[float] = None
    approval_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentVersion':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class VersionChange:
    """Represents a change made to content"""
    change_id: str
    version_id: str
    change_type: ChangeType
    timestamp: datetime
    user_id: str
    description: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VersionChange':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ContentBranch:
    """Represents a branch of content versions"""
    branch_id: str
    branch_name: str
    content_id: str
    current_version_id: str
    created_at: datetime
    created_by: str
    is_active: bool = True
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentBranch':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class ContentVersioningSystem:
    """Manages content versioning, branching, and rollbacks"""
    
    def __init__(self):
        self.versions: Dict[str, ContentVersion] = {}
        self.changes: Dict[str, VersionChange] = {}
        self.branches: Dict[str, ContentBranch] = {}
        self.content_versions: Dict[str, List[str]] = {}  # content_id -> [version_ids]
        self.version_changes: Dict[str, List[str]] = {}   # version_id -> [change_ids]
        
    def create_content(self, 
                      content: str, 
                      content_type: ContentType, 
                      format: ContentFormat,
                      metadata: Dict[str, Any],
                      user_id: str,
                      content_id: Optional[str] = None) -> str:
        """Create new content with initial version"""
        
        if content_id is None:
            content_id = str(uuid.uuid4())
        
        version_id = str(uuid.uuid4())
        version = ContentVersion(
            version_id=version_id,
            content_id=content_id,
            version_number=1,
            content=content,
            content_type=content_type,
            format=format,
            metadata=metadata,
            status=VersionStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            created_by=user_id
        )
        
        # Store version
        self.versions[version_id] = version
        
        # Initialize content versions list
        if content_id not in self.content_versions:
            self.content_versions[content_id] = []
        self.content_versions[content_id].append(version_id)
        
        # Create main branch
        branch = ContentBranch(
            branch_id=str(uuid.uuid4()),
            branch_name="main",
            content_id=content_id,
            current_version_id=version_id,
            created_at=datetime.now(timezone.utc),
            created_by=user_id
        )
        self.branches[branch.branch_id] = branch
        
        # Record change
        change = VersionChange(
            change_id=str(uuid.uuid4()),
            version_id=version_id,
            change_type=ChangeType.CREATED,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            description="Initial content creation",
            metadata={"content_type": content_type.value, "format": format.value}
        )
        self.changes[change.change_id] = change
        
        if version_id not in self.version_changes:
            self.version_changes[version_id] = []
        self.version_changes[version_id].append(change.change_id)
        
        logger.info(f"Created content {content_id} with version {version_id}")
        return content_id
    
    def create_version(self,
                      content_id: str,
                      content: str,
                      user_id: str,
                      change_summary: str,
                      parent_version_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new version of existing content"""
        
        if content_id not in self.content_versions:
            raise ValueError(f"Content {content_id} not found")
        
        # Get current version info
        current_versions = self.content_versions[content_id]
        if not current_versions:
            raise ValueError(f"No versions found for content {content_id}")
        
        # Determine parent version
        if parent_version_id is None:
            parent_version_id = current_versions[-1]  # Latest version
        
        if parent_version_id not in self.versions:
            raise ValueError(f"Parent version {parent_version_id} not found")
        
        parent_version = self.versions[parent_version_id]
        
        # Create new version
        version_id = str(uuid.uuid4())
        version = ContentVersion(
            version_id=version_id,
            content_id=content_id,
            version_number=len(current_versions) + 1,
            content=content,
            content_type=parent_version.content_type,
            format=parent_version.format,
            metadata=metadata or parent_version.metadata.copy(),
            status=VersionStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            parent_version_id=parent_version_id,
            change_summary=change_summary
        )
        
        # Store version
        self.versions[version_id] = version
        self.content_versions[content_id].append(version_id)
        
        # Record change
        change = VersionChange(
            change_id=str(uuid.uuid4()),
            version_id=version_id,
            change_type=ChangeType.UPDATED,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            description=change_summary,
            metadata={"parent_version": parent_version_id}
        )
        self.changes[change.change_id] = change
        
        if version_id not in self.version_changes:
            self.version_changes[version_id] = []
        self.version_changes[version_id].append(change.change_id)
        
        logger.info(f"Created version {version_id} for content {content_id}")
        return version_id
    
    def create_branch(self,
                     content_id: str,
                     branch_name: str,
                     base_version_id: str,
                     user_id: str,
                     description: Optional[str] = None) -> str:
        """Create a new branch from a specific version"""
        
        if content_id not in self.content_versions:
            raise ValueError(f"Content {content_id} not found")
        
        if base_version_id not in self.versions:
            raise ValueError(f"Base version {base_version_id} not found")
        
        # Check if branch name already exists for this content
        for branch in self.branches.values():
            if branch.content_id == content_id and branch.branch_name == branch_name:
                raise ValueError(f"Branch {branch_name} already exists for content {content_id}")
        
        branch = ContentBranch(
            branch_id=str(uuid.uuid4()),
            branch_name=branch_name,
            content_id=content_id,
            current_version_id=base_version_id,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            description=description
        )
        
        self.branches[branch.branch_id] = branch
        
        logger.info(f"Created branch {branch_name} for content {content_id}")
        return branch.branch_id
    
    def update_version_status(self,
                             version_id: str,
                             new_status: VersionStatus,
                             user_id: str,
                             notes: Optional[str] = None) -> None:
        """Update the status of a version"""
        
        if version_id not in self.versions:
            raise ValueError(f"Version {version_id} not found")
        
        version = self.versions[version_id]
        old_status = version.status
        version.status = new_status
        
        if notes:
            version.approval_notes = notes
        
        # Record change
        change = VersionChange(
            change_id=str(uuid.uuid4()),
            version_id=version_id,
            change_type=ChangeType.APPROVED if new_status == VersionStatus.APPROVED else ChangeType.UPDATED,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            description=f"Status changed from {old_status} to {new_status}",
            metadata={"old_status": old_status, "new_status": new_status, "notes": notes}
        )
        self.changes[change.change_id] = change
        
        if version_id not in self.version_changes:
            self.version_changes[version_id] = []
        self.version_changes[version_id].append(change.change_id)
        
        logger.info(f"Updated version {version_id} status to {new_status}")
    
    def rollback_to_version(self,
                           content_id: str,
                           target_version_id: str,
                           user_id: str,
                           reason: str) -> str:
        """Rollback content to a previous version"""
        
        if content_id not in self.content_versions:
            raise ValueError(f"Content {content_id} not found")
        
        if target_version_id not in self.versions:
            raise ValueError(f"Target version {target_version_id} not found")
        
        target_version = self.versions[target_version_id]
        
        # Create new version with rollback content
        version_id = str(uuid.uuid4())
        version = ContentVersion(
            version_id=version_id,
            content_id=content_id,
            version_number=len(self.content_versions[content_id]) + 1,
            content=target_version.content,
            content_type=target_version.content_type,
            format=target_version.format,
            metadata=target_version.metadata.copy(),
            status=VersionStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            parent_version_id=target_version_id,
            change_summary=f"Rollback to version {target_version.version_number}: {reason}"
        )
        
        # Store version
        self.versions[version_id] = version
        self.content_versions[content_id].append(version_id)
        
        # Record change
        change = VersionChange(
            change_id=str(uuid.uuid4()),
            version_id=version_id,
            change_type=ChangeType.ROLLBACK,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            description=f"Rollback to version {target_version.version_number}",
            metadata={"target_version": target_version_id, "reason": reason}
        )
        self.changes[change.change_id] = change
        
        if version_id not in self.version_changes:
            self.version_changes[version_id] = []
        self.version_changes[version_id].append(change.change_id)
        
        logger.info(f"Rolled back content {content_id} to version {target_version_id}")
        return version_id
    
    def get_version_history(self, content_id: str) -> List[ContentVersion]:
        """Get the complete version history for content"""
        
        if content_id not in self.content_versions:
            return []
        
        version_ids = self.content_versions[content_id]
        versions = [self.versions[vid] for vid in version_ids if vid in self.versions]
        return sorted(versions, key=lambda v: v.version_number)
    
    def get_version_changes(self, version_id: str) -> List[VersionChange]:
        """Get all changes for a specific version"""
        
        if version_id not in self.version_changes:
            return []
        
        change_ids = self.version_changes[version_id]
        changes = [self.changes[cid] for cid in change_ids if cid in self.changes]
        return sorted(changes, key=lambda c: c.timestamp)
    
    def get_content_branches(self, content_id: str) -> List[ContentBranch]:
        """Get all branches for content"""
        
        branches = [b for b in self.branches.values() if b.content_id == content_id]
        return sorted(branches, key=lambda b: b.created_at)
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """Compare two versions of content"""
        
        if version_id_1 not in self.versions or version_id_2 not in self.versions:
            raise ValueError("One or both versions not found")
        
        v1 = self.versions[version_id_1]
        v2 = self.versions[version_id_2]
        
        # Calculate content hash for comparison
        hash1 = hashlib.md5(v1.content.encode()).hexdigest()
        hash2 = hashlib.md5(v2.content.encode()).hexdigest()
        
        # Simple content comparison
        content_changed = hash1 != hash2
        content_length_diff = len(v2.content) - len(v1.content)
        
        # Metadata comparison
        metadata_changed = v1.metadata != v2.metadata
        
        return {
            "version_1": {
                "version_id": v1.version_id,
                "version_number": v1.version_number,
                "created_at": v1.created_at,
                "status": v1.status,
                "content_length": len(v1.content)
            },
            "version_2": {
                "version_id": v2.version_id,
                "version_number": v2.version_number,
                "created_at": v2.created_at,
                "status": v2.status,
                "content_length": len(v2.content)
            },
            "changes": {
                "content_changed": content_changed,
                "content_length_diff": content_length_diff,
                "metadata_changed": metadata_changed,
                "status_changed": v1.status != v2.status
            }
        }
    
    def export_version_data(self, content_id: str) -> Dict[str, Any]:
        """Export all version data for content"""
        
        if content_id not in self.content_versions:
            return {}
        
        versions = self.get_version_history(content_id)
        branches = self.get_content_branches(content_id)
        
        export_data = {
            "content_id": content_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "versions": [v.to_dict() for v in versions],
            "branches": [b.to_dict() for b in branches],
            "changes": {}
        }
        
        # Include changes for each version
        for version in versions:
            changes = self.get_version_changes(version.version_id)
            export_data["changes"][version.version_id] = [c.to_dict() for c in changes]
        
        return export_data
    
    def import_version_data(self, data: Dict[str, Any]) -> None:
        """Import version data from export"""
        
        content_id = data.get("content_id")
        if not content_id:
            raise ValueError("Invalid export data: missing content_id")
        
        # Import versions
        for version_data in data.get("versions", []):
            version = ContentVersion.from_dict(version_data)
            self.versions[version.version_id] = version
        
        # Import branches
        for branch_data in data.get("branches", []):
            branch = ContentBranch.from_dict(branch_data)
            self.branches[branch.branch_id] = branch
        
        # Import changes
        for version_id, changes_data in data.get("changes", {}).items():
            if version_id not in self.version_changes:
                self.version_changes[version_id] = []
            
            for change_data in changes_data:
                change = VersionChange.from_dict(change_data)
                self.changes[change.change_id] = change
                self.version_changes[version_id].append(change.change_id)
        
        # Rebuild content versions mapping
        if content_id not in self.content_versions:
            self.content_versions[content_id] = []
        
        for version in self.versions.values():
            if version.content_id == content_id:
                if version.version_id not in self.content_versions[content_id]:
                    self.content_versions[content_id].append(version.version_id)
        
        logger.info(f"Imported version data for content {content_id}")


# Global instance
_versioning_system = None

def get_versioning_system() -> ContentVersioningSystem:
    """Get the global versioning system instance"""
    global _versioning_system
    if _versioning_system is None:
        _versioning_system = ContentVersioningSystem()
    return _versioning_system