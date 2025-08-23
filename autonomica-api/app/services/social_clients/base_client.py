"""
Base Social Media Client Interface
Abstract base class defining the interface for all social media platform clients
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.models.schema import ContentPiece

logger = logging.getLogger(__name__)

class BaseSocialClient(ABC):
    """
    Abstract base class for social media platform clients
    
    All platform-specific clients must implement these methods to ensure
    consistent interface across different social media platforms.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.is_authenticated = False
        self.rate_limit_remaining = 0
        self.rate_limit_reset_time = None
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the social media platform
        
        Args:
            credentials: Platform-specific authentication credentials
            
        Returns:
            bool: True if authentication successful
        """
        pass
    
    @abstractmethod
    async def publish_content(self, content: ContentPiece, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish content to the social media platform
        
        Args:
            content: Content piece to publish
            schedule_data: Scheduling and publishing metadata
            
        Returns:
            Dict containing publishing result with keys:
            - success: bool
            - post_id: str (platform-specific post ID)
            - error_message: str (if failed)
            - metrics: Dict (initial metrics if available)
        """
        pass
    
    @abstractmethod
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics for a published post
        
        Args:
            post_id: Platform-specific post ID
            
        Returns:
            Dict containing post metrics (likes, shares, comments, etc.)
        """
        pass
    
    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a published post
        
        Args:
            post_id: Platform-specific post ID
            
        Returns:
            bool: True if deletion successful
        """
        pass
    
    @abstractmethod
    async def update_post(self, post_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing post
        
        Args:
            post_id: Platform-specific post ID
            updates: Dict containing fields to update
            
        Returns:
            bool: True if update successful
        """
        pass
    
    @abstractmethod
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated user's profile information
        
        Returns:
            Dict containing user profile data
        """
        pass
    
    async def check_rate_limits(self) -> Dict[str, Any]:
        """
        Check current rate limit status
        
        Returns:
            Dict containing rate limit information
        """
        return {
            "remaining": self.rate_limit_remaining,
            "reset_time": self.rate_limit_reset_time,
            "is_limited": self.rate_limit_remaining <= 0
        }
    
    async def wait_for_rate_limit(self) -> None:
        """Wait if rate limit is exceeded"""
        if self.rate_limit_remaining <= 0 and self.rate_limit_reset_time:
            import asyncio
            wait_time = (self.rate_limit_reset_time - datetime.utcnow()).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit exceeded, waiting {wait_time} seconds")
                await asyncio.sleep(wait_time)
    
    def _validate_content(self, content: ContentPiece) -> bool:
        """
        Validate content before publishing
        
        Args:
            content: Content piece to validate
            
        Returns:
            bool: True if content is valid for this platform
        """
        if not content.content or len(content.content.strip()) == 0:
            self.logger.error("Content is empty")
            return False
        
        # Platform-specific content length validation
        max_length = self._get_max_content_length()
        if len(content.content) > max_length:
            self.logger.error(f"Content exceeds maximum length ({max_length} characters)")
            return False
        
        return True
    
    def _get_max_content_length(self) -> int:
        """Get maximum content length for this platform"""
        # Default to Twitter's limit, override in platform-specific implementations
        return 280
    
    def _format_content_for_platform(self, content: ContentPiece) -> str:
        """
        Format content for the specific platform
        
        Args:
            content: Raw content piece
            
        Returns:
            str: Formatted content ready for publishing
        """
        # Base implementation - just return the content
        # Platform-specific clients can override this for custom formatting
        return content.content
    
    async def _handle_api_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle API errors consistently across all clients
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            
        Returns:
            Dict containing error information
        """
        error_msg = str(error)
        self.logger.error(f"API error during {operation}: {error_msg}")
        
        # Check if it's a rate limit error
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            self.rate_limit_remaining = 0
            # Set reset time to 15 minutes from now (typical rate limit window)
            from datetime import timedelta
            self.rate_limit_reset_time = datetime.utcnow() + timedelta(minutes=15)
        
        return {
            "success": False,
            "error_message": error_msg,
            "error_type": type(error).__name__,
            "operation": operation
        }
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """
        Extract hashtags from content
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of hashtags found in the content
        """
        import re
        hashtag_pattern = r'#\w+'
        return re.findall(hashtag_pattern, content)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """
        Extract mentions from content
        
        Args:
            content: Text content to analyze
            
        Returns:
            List of mentions found in the content
        """
        import re
        mention_pattern = r'@\w+'
        return re.findall(mention_pattern, content)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the client
        
        Returns:
            Dict containing health status information
        """
        try:
            profile = await self.get_user_profile()
            return {
                "status": "healthy",
                "platform": self.platform_name,
                "authenticated": self.is_authenticated,
                "profile_accessible": bool(profile),
                "rate_limit_status": await self.check_rate_limits()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "platform": self.platform_name,
                "authenticated": self.is_authenticated,
                "error": str(e),
                "rate_limit_status": await self.check_rate_limits()
            }




