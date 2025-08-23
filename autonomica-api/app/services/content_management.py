"""
Content Management System Service
Handles creation, editing, and management of social media content
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import re
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.schema import ContentPiece, ContentStatus, SocialPost
from app.services.social_scheduler import ContentType, PlatformType, SocialMediaScheduler

logger = logging.getLogger(__name__)

class ContentFormat(Enum):
    """Supported content formats"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    POLL = "poll"
    LINK = "link"
    LOCATION = "location"

class ContentCategory(Enum):
    """Content categories for organization"""
    MARKETING = "marketing"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    PROMOTIONAL = "promotional"
    COMMUNITY = "community"
    PRODUCT = "product"
    SERVICE = "service"

@dataclass
class ContentMetadata:
    """Metadata for content pieces"""
    title: str
    description: Optional[str] = None
    tags: List[str] = None
    category: Optional[ContentCategory] = None
    campaign: Optional[str] = None
    target_audience: Optional[str] = None
    language: str = "en"
    seo_keywords: List[str] = None

@dataclass
class PlatformContent:
    """Platform-specific content adaptation"""
    platform: PlatformType
    content: str
    media_urls: List[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    call_to_action: Optional[str] = None
    platform_specific_data: Dict[str, Any] = None

@dataclass
class ContentVersion:
    """Content version tracking"""
    version_id: str
    content: str
    metadata: ContentMetadata
    created_at: datetime
    created_by: str
    change_summary: str

class ContentManagementService:
    """
    Comprehensive content management system for social media
    
    Features:
    - Content creation and editing
    - Multi-platform adaptation
    - Approval workflow
    - Version control
    - Content library management
    - Media asset handling
    """
    
    def __init__(self, db: Session, scheduler: SocialMediaScheduler):
        self.db = db
        self.scheduler = scheduler
        self.media_upload_path = "uploads/content"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Platform-specific content limits
        self.platform_limits = {
            PlatformType.TWITTER: {"max_length": 280, "media_limit": 4},
            PlatformType.FACEBOOK: {"max_length": 63206, "media_limit": 10},
            PlatformType.LINKEDIN: {"max_length": 3000, "media_limit": 9},
            PlatformType.INSTAGRAM: {"max_length": 2200, "media_limit": 10}
        }
        
        # Ensure upload directory exists
        os.makedirs(self.media_upload_path, exist_ok=True)
    
    async def create_content(
        self,
        content: str,
        content_type: ContentType,
        metadata: ContentMetadata,
        user_id: str,
        platforms: List[PlatformType] = None
    ) -> Dict[str, Any]:
        """
        Create new social media content
        
        Args:
            content: Main content text
            content_type: Type of content
            metadata: Content metadata
            user_id: User creating the content
            platforms: Target platforms
            
        Returns:
            Dict containing created content information
        """
        try:
            # Validate content
            validation_result = self._validate_content(content, content_type, platforms)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Content validation failed",
                    "details": validation_result["errors"]
                }
            
            # Create content piece
            content_piece = ContentPiece(
                title=metadata.title,
                content=content,
                type=content_type.value,
                status=ContentStatus.DRAFT,
                created_at=datetime.utcnow()
            )
            
            self.db.add(content_piece)
            self.db.commit()
            self.db.refresh(content_piece)
            
            # Create platform-specific content adaptations
            platform_contents = []
            if platforms:
                for platform in platforms:
                    platform_content = await self._adapt_content_for_platform(
                        content, content_type, platform, metadata
                    )
                    platform_contents.append(platform_content)
            
            # Store metadata as JSON in the database
            metadata_dict = {
                "tags": metadata.tags or [],
                "category": metadata.category.value if metadata.category else None,
                "campaign": metadata.campaign,
                "target_audience": metadata.target_audience,
                "language": metadata.language,
                "seo_keywords": metadata.seo_keywords or [],
                "platform_contents": [pc.__dict__ for pc in platform_contents]
            }
            
            # Update content piece with metadata
            content_piece.metadata = metadata_dict
            self.db.commit()
            
            logger.info(f"Created content {content_piece.id} by user {user_id}")
            
            return {
                "success": True,
                "content_id": content_piece.id,
                "status": content_piece.status.value,
                "platform_contents": [pc.__dict__ for pc in platform_contents],
                "validation": validation_result
            }
            
        except Exception as e:
            logger.error(f"Failed to create content: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_content(
        self,
        content_id: int,
        updates: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update existing content
        
        Args:
            content_id: ID of content to update
            updates: Fields to update
            user_id: User making the update
            
        Returns:
            Dict containing update result
        """
        try:
            content_piece = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content_piece:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            # Check if content can be updated
            if content_piece.status in [ContentStatus.PUBLISHED, ContentStatus.SCHEDULED]:
                return {
                    "success": False,
                    "error": "Cannot update published or scheduled content"
                }
            
            # Create version backup
            version = ContentVersion(
                version_id=str(uuid.uuid4()),
                content=content_piece.content,
                metadata=ContentMetadata(
                    title=content_piece.title,
                    tags=content_piece.metadata.get("tags") if content_piece.metadata else []
                ),
                created_at=datetime.utcnow(),
                created_by=user_id,
                change_summary="Content update"
            )
            
            # Update content fields
            if "content" in updates:
                content_piece.content = updates["content"]
                version.content = updates["content"]
            
            if "title" in updates:
                content_piece.title = updates["title"]
                version.metadata.title = updates["title"]
            
            if "metadata" in updates:
                # Merge metadata
                current_metadata = content_piece.metadata or {}
                current_metadata.update(updates["metadata"])
                content_piece.metadata = current_metadata
            
            # Update timestamp
            content_piece.updated_at = datetime.utcnow()
            
            # Store version history
            if not content_piece.metadata:
                content_piece.metadata = {}
            if "versions" not in content_piece.metadata:
                content_piece.metadata["versions"] = []
            
            content_piece.metadata["versions"].append(version.__dict__)
            
            self.db.commit()
            
            logger.info(f"Updated content {content_id} by user {user_id}")
            
            return {
                "success": True,
                "content_id": content_id,
                "status": content_piece.status.value,
                "version_id": version.version_id
            }
            
        except Exception as e:
            logger.error(f"Failed to update content {content_id}: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_content(self, content_id: int, user_id: str) -> Dict[str, Any]:
        """
        Delete content (soft delete by marking as cancelled)
        
        Args:
            content_id: ID of content to delete
            user_id: User deleting the content
            
        Returns:
            Dict containing deletion result
        """
        try:
            content_piece = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content_piece:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            # Check if content can be deleted
            if content_piece.status in [ContentStatus.PUBLISHED, ContentStatus.SCHEDULED]:
                return {
                    "success": False,
                    "error": "Cannot delete published or scheduled content"
                }
            
            # Soft delete by changing status
            content_piece.status = ContentStatus.CANCELLED
            content_piece.updated_at = datetime.utcnow()
            
            # Add deletion metadata
            if not content_piece.metadata:
                content_piece.metadata = {}
            content_piece.metadata["deleted_at"] = datetime.utcnow().isoformat()
            content_piece.metadata["deleted_by"] = user_id
            
            self.db.commit()
            
            logger.info(f"Deleted content {content_id} by user {user_id}")
            
            return {
                "success": True,
                "content_id": content_id,
                "message": "Content deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete content {content_id}: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_content(self, content_id: int) -> Dict[str, Any]:
        """
        Get content by ID
        
        Args:
            content_id: ID of content to retrieve
            
        Returns:
            Dict containing content information
        """
        try:
            content_piece = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content_piece:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            # Get associated social posts
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id
            ).all()
            
            return {
                "success": True,
                "content": {
                    "id": content_piece.id,
                    "title": content_piece.title,
                    "content": content_piece.content,
                    "type": content_piece.type,
                    "status": content_piece.status.value,
                    "metadata": content_piece.metadata,
                    "created_at": content_piece.created_at.isoformat(),
                    "updated_at": content_piece.updated_at.isoformat() if content_piece.updated_at else None,
                    "social_posts": [
                        {
                            "platform": post.platform,
                            "status": post.status.value,
                            "publish_date": post.publish_date.isoformat() if post.publish_date else None,
                            "metrics": post.metrics
                        }
                        for post in social_posts
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get content {content_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_content(
        self,
        user_id: str = None,
        status: ContentStatus = None,
        content_type: ContentType = None,
        category: ContentCategory = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        List content with filtering and pagination
        
        Args:
            user_id: Filter by user
            status: Filter by status
            content_type: Filter by content type
            category: Filter by category
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict containing paginated content list
        """
        try:
            query = self.db.query(ContentPiece)
            
            # Apply filters
            if user_id:
                query = query.filter(ContentPiece.user_id == user_id)
            
            if status:
                query = query.filter(ContentPiece.status == status)
            
            if content_type:
                query = query.filter(ContentPiece.type == content_type.value)
            
            if category:
                query = query.filter(
                    ContentPiece.metadata.contains({"category": category.value})
                )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            content_list = query.offset(offset).limit(per_page).all()
            
            # Format results
            results = []
            for content in content_list:
                results.append({
                    "id": content.id,
                    "title": content.title,
                    "type": content.type,
                    "status": content.status.value,
                    "category": content.metadata.get("category") if content.metadata else None,
                    "created_at": content.created_at.isoformat(),
                    "updated_at": content.updated_at.isoformat() if content.updated_at else None
                })
            
            return {
                "success": True,
                "content": results,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": (total_count + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to list content: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def submit_for_approval(self, content_id: int, user_id: str) -> Dict[str, Any]:
        """
        Submit content for approval
        
        Args:
            content_id: ID of content to submit
            user_id: User submitting the content
            
        Returns:
            Dict containing submission result
        """
        try:
            content_piece = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content_piece:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            if content_piece.status != ContentStatus.DRAFT:
                return {
                    "success": False,
                    "error": "Only draft content can be submitted for approval"
                }
            
            # Change status to in review
            content_piece.status = ContentStatus.IN_REVIEW
            content_piece.updated_at = datetime.utcnow()
            
            # Add approval metadata
            if not content_piece.metadata:
                content_piece.metadata = {}
            content_piece.metadata["submitted_for_approval_at"] = datetime.utcnow().isoformat()
            content_piece.metadata["submitted_by"] = user_id
            
            self.db.commit()
            
            logger.info(f"Content {content_id} submitted for approval by user {user_id}")
            
            return {
                "success": True,
                "content_id": content_id,
                "status": "in_review",
                "message": "Content submitted for approval"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit content {content_id} for approval: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def approve_content(
        self,
        content_id: int,
        approver_id: str,
        approval_notes: str = None
    ) -> Dict[str, Any]:
        """
        Approve content for publishing
        
        Args:
            content_id: ID of content to approve
            approver_id: User approving the content
            approval_notes: Optional approval notes
            
        Returns:
            Dict containing approval result
        """
        try:
            content_piece = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content_piece:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            if content_piece.status != ContentStatus.IN_REVIEW:
                return {
                    "success": False,
                    "error": "Only content in review can be approved"
                }
            
            # Change status to approved
            content_piece.status = ContentStatus.APPROVED
            content_piece.updated_at = datetime.utcnow()
            
            # Add approval metadata
            if not content_piece.metadata:
                content_piece.metadata = {}
            content_piece.metadata["approved_at"] = datetime.utcnow().isoformat()
            content_piece.metadata["approved_by"] = approver_id
            if approval_notes:
                content_piece.metadata["approval_notes"] = approval_notes
            
            self.db.commit()
            
            logger.info(f"Content {content_id} approved by user {approver_id}")
            
            return {
                "success": True,
                "content_id": content_id,
                "status": "approved",
                "message": "Content approved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to approve content {content_id}: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_content(
        self,
        content: str,
        content_type: ContentType,
        platforms: List[PlatformType] = None
    ) -> Dict[str, Any]:
        """Validate content for all target platforms"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not content or len(content.strip()) == 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Content cannot be empty")
            return validation_result
        
        if platforms:
            for platform in platforms:
                platform_validation = self._validate_for_platform(content, platform)
                if not platform_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(platform_validation["errors"])
                if platform_validation["warnings"]:
                    validation_result["warnings"].extend(platform_validation["warnings"])
        
        return validation_result
    
    def _validate_for_platform(
        self,
        content: str,
        platform: PlatformType
    ) -> Dict[str, Any]:
        """Validate content for a specific platform"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        platform_limit = self.platform_limits.get(platform)
        if not platform_limit:
            validation_result["errors"].append(f"Unknown platform: {platform}")
            return validation_result
        
        max_length = platform_limit["max_length"]
        if len(content) > max_length:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Content exceeds {platform.value} limit: {len(content)} > {max_length} characters"
            )
        
        # Platform-specific validation rules
        if platform == PlatformType.TWITTER:
            # Check for valid hashtags
            hashtags = re.findall(r'#\w+', content)
            for hashtag in hashtags:
                if len(hashtag) > 50:  # Twitter hashtag limit
                    validation_result["warnings"].append(f"Hashtag too long: {hashtag}")
        
        elif platform == PlatformType.INSTAGRAM:
            # Instagram prefers shorter, punchy content
            if len(content) < 50:
                validation_result["warnings"].append("Instagram content might be too short for optimal engagement")
        
        return validation_result
    
    async def _adapt_content_for_platform(
        self,
        content: str,
        content_type: ContentType,
        platform: PlatformType,
        metadata: ContentMetadata
    ) -> PlatformContent:
        """Adapt content for a specific platform"""
        adapted_content = content
        
        # Platform-specific adaptations
        if platform == PlatformType.TWITTER:
            adapted_content = self._adapt_for_twitter(content, metadata)
        elif platform == PlatformType.FACEBOOK:
            adapted_content = self._adapt_for_facebook(content, metadata)
        elif platform == PlatformType.LINKEDIN:
            adapted_content = self._adapt_for_linkedin(content, metadata)
        elif platform == PlatformType.INSTAGRAM:
            adapted_content = self._adapt_for_instagram(content, metadata)
        
        # Extract hashtags and mentions
        hashtags = re.findall(r'#\w+', adapted_content)
        mentions = re.findall(r'@\w+', adapted_content)
        
        return PlatformContent(
            platform=platform,
            content=adapted_content,
            hashtags=hashtags,
            mentions=mentions,
            platform_specific_data=self._get_platform_specific_data(platform, content_type, metadata)
        )
    
    def _adapt_for_twitter(self, content: str, metadata: ContentMetadata) -> str:
        """Adapt content for Twitter"""
        adapted = content
        
        # Add hashtags if not present
        if metadata.tags and not re.search(r'#\w+', content):
            hashtags = ' '.join([f"#{tag}" for tag in metadata.tags[:3]])  # Max 3 hashtags
            adapted = f"{content}\n\n{hashtags}"
        
        # Ensure length limit
        if len(adapted) > 280:
            adapted = adapted[:277] + "..."
        
        return adapted
    
    def _adapt_for_facebook(self, content: str, metadata: ContentMetadata) -> str:
        """Adapt content for Facebook"""
        adapted = content
        
        # Facebook allows longer content, add more context
        if metadata.description and len(content) < 100:
            adapted = f"{content}\n\n{metadata.description}"
        
        # Add hashtags
        if metadata.tags:
            hashtags = ' '.join([f"#{tag}" for tag in metadata.tags[:5]])
            adapted = f"{adapted}\n\n{hashtags}"
        
        return adapted
    
    def _adapt_for_linkedin(self, content: str, metadata: ContentMetadata) -> str:
        """Adapt content for LinkedIn"""
        adapted = content
        
        # LinkedIn prefers professional tone
        if metadata.category == ContentCategory.PROFESSIONAL:
            adapted = f"Professional insight: {content}"
        
        # Add call to action
        if not re.search(r'(learn more|read more|discover|explore)', content.lower()):
            adapted = f"{adapted}\n\nWhat are your thoughts on this? Share your experience in the comments."
        
        return adapted
    
    def _adapt_for_instagram(self, content: str, metadata: ContentMetadata) -> str:
        """Adapt content for Instagram"""
        adapted = content
        
        # Instagram prefers visual language
        if not re.search(r'(📸|🎯|💡|🔥|✨)', content):
            adapted = f"💡 {content}"
        
        # Add relevant emojis based on category
        if metadata.category:
            emoji_map = {
                ContentCategory.MARKETING: "🎯",
                ContentCategory.EDUCATIONAL: "📚",
                ContentCategory.ENTERTAINMENT: "🎬",
                ContentCategory.NEWS: "📰",
                ContentCategory.PRODUCT: "🛍️",
                ContentCategory.SERVICE: "🔧"
            }
            emoji = emoji_map.get(metadata.category, "✨")
            adapted = f"{emoji} {adapted}"
        
        return adapted
    
    def _get_platform_specific_data(
        self,
        platform: PlatformType,
        content_type: ContentType,
        metadata: ContentMetadata
    ) -> Dict[str, Any]:
        """Get platform-specific data for content"""
        platform_data = {}
        
        if platform == PlatformType.TWITTER:
            platform_data = {
                "card_type": "summary" if len(metadata.description or "") > 100 else "summary_large_image",
                "conversation_id": None
            }
        
        elif platform == PlatformType.FACEBOOK:
            platform_data = {
                "feed_targeting": {
                    "age_min": 18,
                    "age_max": 65,
                    "genders": [1, 2]  # 1=male, 2=female
                }
            }
        
        elif platform == PlatformType.LINKEDIN:
            platform_data = {
                "visibility": "anyone",
                "distribution": {
                    "linkedInDistributionTarget": {
                        "visibleToGuest": True
                    }
                }
            }
        
        elif platform == PlatformType.INSTAGRAM:
            platform_data = {
                "caption": True,
                "location": None,
                "user_tags": []
            }
        
        return platform_data
    
    async def get_content_analytics(self, content_id: int) -> Dict[str, Any]:
        """Get analytics for a content piece across all platforms"""
        try:
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id
            ).all()
            
            analytics = {
                "content_id": content_id,
                "total_posts": len(social_posts),
                "platforms": {},
                "overall_metrics": {
                    "total_impressions": 0,
                    "total_engagements": 0,
                    "total_reach": 0
                }
            }
            
            for post in social_posts:
                platform = post.platform
                if platform not in analytics["platforms"]:
                    analytics["platforms"][platform] = {
                        "posts": 0,
                        "impressions": 0,
                        "engagements": 0,
                        "reach": 0
                    }
                
                analytics["platforms"][platform]["posts"] += 1
                
                if post.metrics:
                    metrics = post.metrics
                    analytics["platforms"][platform]["impressions"] += metrics.get("impressions", 0)
                    analytics["platforms"][platform]["engagements"] += metrics.get("engagements", 0)
                    analytics["platforms"][platform]["reach"] += metrics.get("reach", 0)
                    
                    analytics["overall_metrics"]["total_impressions"] += metrics.get("impressions", 0)
                    analytics["overall_metrics"]["total_engagements"] += metrics.get("engagements", 0)
                    analytics["overall_metrics"]["total_reach"] += metrics.get("reach", 0)
            
            return {
                "success": True,
                "analytics": analytics
            }
            
        except Exception as e:
            logger.error(f"Failed to get content analytics for {content_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }




