"""
Facebook Graph API Client Implementation
Handles Facebook page posting and metrics retrieval
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from .base_client import BaseSocialClient
from app.models.schema import ContentPiece

logger = logging.getLogger(__name__)

class FacebookClient(BaseSocialClient):
    """
    Facebook Graph API client for page posts
    
    Implements the BaseSocialClient interface with Facebook-specific functionality
    """
    
    def __init__(self):
        super().__init__("facebook")
        self.api_base_url = "https://graph.facebook.com/v18.0"
        self.access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.app_id = os.getenv("FACEBOOK_APP_ID")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET")
        
        # Facebook-specific limits
        self.max_post_length = 63206  # Facebook post character limit
        self.rate_limit_remaining = 200  # Default rate limit
        self.rate_limit_reset_time = None
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            params={"access_token": self.access_token} if self.access_token else {}
        )
    
    def _get_max_content_length(self) -> int:
        """Get maximum content length for Facebook"""
        return self.max_post_length
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with Facebook Graph API
        
        Args:
            credentials: Facebook API credentials
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Use provided credentials or environment variables
            access_token = credentials.get("access_token") or self.access_token
            page_id = credentials.get("page_id") or self.page_id
            
            if not access_token:
                self.logger.error("Facebook access token not provided")
                return False
            
            if not page_id:
                self.logger.error("Facebook page ID not provided")
                return False
            
            # Test authentication by getting page information
            response = await self.http_client.get(
                f"{self.api_base_url}/{page_id}",
                params={"fields": "id,name,access_token"}
            )
            
            if response.status_code == 200:
                page_data = response.json()
                self.is_authenticated = True
                self.page_id = page_id
                self.access_token = access_token
                
                # Update HTTP client with page access token
                self.http_client.params["access_token"] = access_token
                
                self.logger.info(f"Facebook authentication successful for page: {page_data.get('name', page_id)}")
                return True
            else:
                self.logger.error(f"Facebook authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Facebook authentication error: {e}")
            return False
    
    async def publish_content(self, content: ContentPiece, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish content to Facebook page
        
        Args:
            content: Content piece to publish
            schedule_data: Scheduling metadata
            
        Returns:
            Dict containing publishing result
        """
        try:
            # Validate content
            if not self._validate_content(content):
                return {
                    "success": False,
                    "error_message": "Content validation failed"
                }
            
            # Check authentication
            if not self.is_authenticated:
                return {
                    "success": False,
                    "error_message": "Not authenticated with Facebook"
                }
            
            # Check rate limits
            await self.wait_for_rate_limit()
            
            # Format content for Facebook
            post_text = self._format_content_for_platform(content)
            
            # Prepare post data
            post_data = {
                "message": post_text,
                "published": True  # Publish immediately
            }
            
            # Add scheduling if specified
            if schedule_data.get("scheduled_time"):
                scheduled_time = schedule_data["scheduled_time"]
                if isinstance(scheduled_time, str):
                    from datetime import datetime
                    scheduled_time = datetime.fromisoformat(scheduled_time)
                
                # Facebook expects Unix timestamp
                post_data["published"] = False
                post_data["scheduled_publish_time"] = int(scheduled_time.timestamp())
            
            # Post to Facebook page
            response = await self.http_client.post(
                f"{self.api_base_url}/{self.page_id}/feed",
                json=post_data
            )
            
            if response.status_code == 200:
                post_response = response.json()
                post_id = post_response["id"]
                
                # Update rate limit info from headers
                self._update_rate_limits_from_headers(response.headers)
                
                self.logger.info(f"Successfully posted to Facebook: {post_id}")
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "platform_post_id": post_id,
                    "metrics": {
                        "created_at": datetime.utcnow().isoformat(),
                        "text_length": len(post_text),
                        "page_id": self.page_id
                    }
                }
            else:
                error_msg = f"Failed to post to Facebook: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg
                }
                
        except Exception as e:
            return await self._handle_api_error(e, "publishing to Facebook")
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics for a published Facebook post
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            Dict containing post metrics
        """
        try:
            if not self.is_authenticated:
                return {"error": "Not authenticated with Facebook"}
            
            # Get post insights (metrics)
            response = await self.http_client.get(
                f"{self.api_base_url}/{post_id}/insights",
                params={
                    "metric": "post_impressions,post_engagements,post_reactions_by_type_total,post_clicks"
                }
            )
            
            if response.status_code == 200:
                insights_data = response.json()
                
                # Get post details
                post_response = await self.http_client.get(
                    f"{self.api_base_url}/{post_id}",
                    params={"fields": "message,created_time,shares,comments.summary(true),reactions.summary(true)"}
                )
                
                post_data = {}
                if post_response.status_code == 200:
                    post_data = post_response.json()
                
                # Compile metrics
                metrics = {
                    "post_id": post_id,
                    "message": post_data.get("message", ""),
                    "created_time": post_data.get("created_time"),
                    "insights": insights_data.get("data", []),
                    "shares": post_data.get("shares", {}).get("count", 0) if post_data.get("shares") else 0,
                    "comments": post_data.get("comments", {}).get("summary", {}).get("total_count", 0) if post_data.get("comments") else 0,
                    "reactions": post_data.get("reactions", {}).get("summary", {}).get("total_count", 0) if post_data.get("reactions") else 0,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                self.logger.info(f"Retrieved metrics for Facebook post {post_id}")
                return metrics
            else:
                error_msg = f"Failed to get Facebook post metrics: {response.status_code}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            return await self._handle_api_error(e, "retrieving Facebook post metrics")
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a published Facebook post
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            bool: True if deletion successful
        """
        try:
            if not self.is_authenticated:
                self.logger.error("Not authenticated with Facebook")
                return False
            
            response = await self.http_client.delete(f"{self.api_base_url}/{post_id}")
            
            if response.status_code == 200:
                self.logger.info(f"Successfully deleted Facebook post {post_id}")
                return True
            else:
                self.logger.error(f"Failed to delete Facebook post: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting Facebook post {post_id}: {e}")
            return False
    
    async def update_post(self, post_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing Facebook post
        
        Args:
            post_id: Facebook post ID
            updates: Dict containing new content
            
        Returns:
            bool: True if update successful
        """
        try:
            if not self.is_authenticated:
                self.logger.error("Not authenticated with Facebook")
                return False
            
            # Facebook allows updating post message
            if "message" in updates:
                update_data = {"message": updates["message"]}
                
                response = await self.http_client.post(
                    f"{self.api_base_url}/{post_id}",
                    json=update_data
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully updated Facebook post {post_id}")
                    return True
                else:
                    self.logger.error(f"Failed to update Facebook post: {response.status_code}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating Facebook post {post_id}: {e}")
            return False
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated page's profile information
        
        Returns:
            Dict containing page profile data
        """
        try:
            if not self.is_authenticated:
                return {"error": "Not authenticated with Facebook"}
            
            response = await self.http_client.get(
                f"{self.api_base_url}/{self.page_id}",
                params={
                    "fields": "id,name,username,fan_count,verification_status,profile_picture_url"
                }
            )
            
            if response.status_code == 200:
                page_data = response.json()
                
                profile = {
                    "id": page_data["id"],
                    "name": page_data["name"],
                    "username": page_data.get("username"),
                    "fan_count": page_data.get("fan_count"),
                    "verification_status": page_data.get("verification_status"),
                    "profile_picture_url": page_data.get("profile_picture_url"),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                return profile
            else:
                error_msg = f"Failed to get Facebook page profile: {response.status_code}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            return await self._handle_api_error(e, "retrieving Facebook page profile")
    
    def _format_content_for_platform(self, content: ContentPiece) -> str:
        """
        Format content specifically for Facebook
        
        Args:
            content: Raw content piece
            
        Returns:
            str: Content formatted for Facebook
        """
        post_text = content.content
        
        # Ensure content doesn't exceed Facebook's limit
        if len(post_text) > self.max_post_length:
            # Truncate and add ellipsis
            post_text = post_text[:self.max_post_length - 3] + "..."
        
        # Facebook-specific formatting could be added here
        # For example, ensuring proper hashtag formatting, etc.
        
        return post_text
    
    def _update_rate_limits_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit information from API response headers"""
        try:
            # Facebook doesn't provide standard rate limit headers
            # We'll use a conservative approach
            remaining = headers.get("x-fb-rev")
            if remaining:
                # Facebook revision header can indicate API usage
                pass
                
        except Exception as e:
            self.logger.warning(f"Failed to parse Facebook rate limit headers: {e}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()
