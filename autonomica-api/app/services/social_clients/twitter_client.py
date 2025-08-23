"""
Twitter API Client Implementation
Handles Twitter v2 API integration for posting tweets and retrieving metrics
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from .base_client import BaseSocialClient
from app.models.schema import ContentPiece

logger = logging.getLogger(__name__)

class TwitterClient(BaseSocialClient):
    """
    Twitter API v2 client for posting tweets and retrieving metrics
    
    Implements the BaseSocialClient interface with Twitter-specific functionality
    """
    
    def __init__(self):
        super().__init__("twitter")
        self.api_base_url = "https://api.twitter.com/2"
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        # Twitter-specific limits
        self.max_tweet_length = 280
        self.rate_limit_remaining = 300  # Default rate limit
        self.rate_limit_reset_time = None
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.bearer_token}" if self.bearer_token else "",
                "Content-Type": "application/json"
            }
        )
    
    def _get_max_content_length(self) -> int:
        """Get maximum content length for Twitter"""
        return self.max_tweet_length
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with Twitter API
        
        Args:
            credentials: Twitter API credentials
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Use provided credentials or environment variables
            bearer_token = credentials.get("bearer_token") or self.bearer_token
            api_key = credentials.get("api_key") or self.api_key
            api_secret = credentials.get("api_secret") or self.api_secret
            
            if not bearer_token:
                self.logger.error("Twitter bearer token not provided")
                return False
            
            # Test authentication by making a simple API call
            response = await self.http_client.get(f"{self.api_base_url}/users/me")
            
            if response.status_code == 200:
                self.is_authenticated = True
                self.logger.info("Twitter authentication successful")
                return True
            else:
                self.logger.error(f"Twitter authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Twitter authentication error: {e}")
            return False
    
    async def publish_content(self, content: ContentPiece, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish content as a tweet
        
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
                    "error_message": "Not authenticated with Twitter"
                }
            
            # Check rate limits
            await self.wait_for_rate_limit()
            
            # Format content for Twitter
            tweet_text = self._format_content_for_platform(content)
            
            # Post tweet
            tweet_data = {"text": tweet_text}
            
            response = await self.http_client.post(
                f"{self.api_base_url}/tweets",
                json=tweet_data
            )
            
            if response.status_code == 201:
                tweet_response = response.json()
                tweet_id = tweet_response["data"]["id"]
                
                # Update rate limit info from headers
                self._update_rate_limits_from_headers(response.headers)
                
                self.logger.info(f"Successfully posted tweet: {tweet_id}")
                
                return {
                    "success": True,
                    "post_id": tweet_id,
                    "platform_post_id": tweet_id,
                    "metrics": {
                        "created_at": datetime.utcnow().isoformat(),
                        "text_length": len(tweet_text)
                    }
                }
            else:
                error_msg = f"Failed to post tweet: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error_message": error_msg
                }
                
        except Exception as e:
            return await self._handle_api_error(e, "publishing tweet")
    
    async def get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics for a published tweet
        
        Args:
            post_id: Twitter tweet ID
            
        Returns:
            Dict containing tweet metrics
        """
        try:
            if not self.is_authenticated:
                return {"error": "Not authenticated with Twitter"}
            
            # Get tweet metrics
            response = await self.http_client.get(
                f"{self.api_base_url}/tweets/{post_id}",
                params={
                    "tweet.fields": "public_metrics,created_at,text",
                    "expansions": "author_id"
                }
            )
            
            if response.status_code == 200:
                tweet_data = response.json()
                tweet = tweet_data["data"]
                
                metrics = {
                    "tweet_id": post_id,
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at"),
                    "public_metrics": tweet.get("public_metrics", {}),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                self.logger.info(f"Retrieved metrics for tweet {post_id}")
                return metrics
            else:
                error_msg = f"Failed to get tweet metrics: {response.status_code}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            return await self._handle_api_error(e, "retrieving tweet metrics")
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a published tweet
        
        Args:
            post_id: Twitter tweet ID
            
        Returns:
            bool: True if deletion successful
        """
        try:
            if not self.is_authenticated:
                self.logger.error("Not authenticated with Twitter")
                return False
            
            response = await self.http_client.delete(f"{self.api_base_url}/tweets/{post_id}")
            
            if response.status_code == 200:
                self.logger.info(f"Successfully deleted tweet {post_id}")
                return True
            else:
                self.logger.error(f"Failed to delete tweet: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting tweet {post_id}: {e}")
            return False
    
    async def update_post(self, post_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing tweet (Twitter doesn't support editing, so this reposts)
        
        Args:
            post_id: Twitter tweet ID
            updates: Dict containing new content
            
        Returns:
            bool: True if update successful
        """
        try:
            # Twitter doesn't support editing tweets, so we delete and repost
            if "text" in updates:
                # Delete the old tweet
                if await self.delete_post(post_id):
                    # Create a new tweet with updated content
                    new_content = ContentPiece(
                        content=updates["text"],
                        type="tweet"
                    )
                    
                    result = await self.publish_content(new_content, {})
                    return result["success"]
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating tweet {post_id}: {e}")
            return False
    
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the authenticated user's profile information
        
        Returns:
            Dict containing user profile data
        """
        try:
            if not self.is_authenticated:
                return {"error": "Not authenticated with Twitter"}
            
            response = await self.http_client.get(
                f"{self.api_base_url}/users/me",
                params={"user.fields": "id,name,username,profile_image_url,verified"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user = user_data["data"]
                
                profile = {
                    "id": user["id"],
                    "name": user["name"],
                    "username": user["username"],
                    "profile_image_url": user.get("profile_image_url"),
                    "verified": user.get("verified", False),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                return profile
            else:
                error_msg = f"Failed to get user profile: {response.status_code}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
        except Exception as e:
            return await self._handle_api_error(e, "retrieving user profile")
    
    def _format_content_for_platform(self, content: ContentPiece) -> str:
        """
        Format content specifically for Twitter
        
        Args:
            content: Raw content piece
            
        Returns:
            str: Content formatted for Twitter
        """
        tweet_text = content.content
        
        # Ensure content doesn't exceed Twitter's limit
        if len(tweet_text) > self.max_tweet_length:
            # Truncate and add ellipsis
            tweet_text = tweet_text[:self.max_tweet_length - 3] + "..."
        
        # Twitter-specific formatting could be added here
        # For example, ensuring proper hashtag formatting, etc.
        
        return tweet_text
    
    def _update_rate_limits_from_headers(self, headers: Dict[str, str]) -> None:
        """Update rate limit information from API response headers"""
        try:
            remaining = headers.get("x-rate-limit-remaining")
            reset_time = headers.get("x-rate-limit-reset")
            
            if remaining:
                self.rate_limit_remaining = int(remaining)
            
            if reset_time:
                # Twitter provides reset time as Unix timestamp
                self.rate_limit_reset_time = datetime.fromtimestamp(int(reset_time))
                
        except Exception as e:
            self.logger.warning(f"Failed to parse rate limit headers: {e}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()




