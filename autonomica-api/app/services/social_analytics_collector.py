"""
Social Analytics Collection System
Collects and stores analytics data from various social media platforms
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.schema import SocialPost, ContentPiece, ContentStatus
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.social_clients import (
    TwitterClient, FacebookClient, LinkedInClient, InstagramClient
)

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of social media metrics"""
    ENGAGEMENT = "engagement"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    SENTIMENT = "sentiment"
    DEMOGRAPHICS = "demographics"
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"

class AnalyticsStatus(Enum):
    """Status of analytics collection"""
    PENDING = "pending"
    COLLECTING = "collecting"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class PlatformMetrics:
    """Metrics data for a specific platform"""
    platform: str
    post_id: str
    platform_post_id: str
    collected_at: datetime
    metrics: Dict[str, Any]
    raw_data: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class AnalyticsCollectionJob:
    """Analytics collection job"""
    job_id: str
    content_id: int
    platforms: List[str]
    collection_type: str  # "realtime", "historical", "scheduled"
    status: AnalyticsStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, PlatformMetrics] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class AnalyticsDataPoint:
    """Individual analytics data point"""
    id: str
    platform: str
    post_id: str
    metric_type: MetricType
    metric_name: str
    metric_value: Union[int, float, str]
    timestamp: datetime
    metadata: Dict[str, Any] = None

class SocialAnalyticsCollector:
    """
    Comprehensive analytics collection system for social media platforms
    
    Features:
    - Real-time and historical metrics collection
    - Multi-platform data aggregation
    - Engagement, reach, and conversion tracking
    - Automated collection scheduling
    - Data validation and quality checks
    - Performance optimization with caching
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Platform clients
        self.platform_clients = {
            "twitter": TwitterClient(),
            "facebook": FacebookClient(),
            "linkedin": LinkedInClient(),
            "instagram": InstagramClient()
        }
        
        # Analytics queues
        self.analytics_queue = "social_analytics_queue"
        self.collection_jobs_queue = "analytics_collection_jobs"
        self.metrics_cache_queue = "metrics_cache_queue"
        
        # Collection jobs tracking
        self.active_collection_jobs: Dict[str, AnalyticsCollectionJob] = {}
        
        # Metrics cache configuration
        self.metrics_cache_ttl = 3600  # 1 hour
        self.collection_interval = 300  # 5 minutes for real-time metrics
        
        # Initialize collection patterns
        self._initialize_collection_patterns()
    
    def _initialize_collection_patterns(self):
        """Initialize collection patterns for different platforms"""
        self.collection_patterns = {
            "twitter": {
                "realtime_metrics": ["likes", "retweets", "replies", "quote_tweets", "impressions"],
                "historical_metrics": ["engagement_rate", "reach", "follower_growth"],
                "collection_interval": 300,  # 5 minutes
                "rate_limit": 300,  # 300 requests per 15 minutes
                "max_historical_days": 30
            },
            "facebook": {
                "realtime_metrics": ["likes", "shares", "comments", "reach", "impressions"],
                "historical_metrics": ["engagement_rate", "page_views", "follower_growth"],
                "collection_interval": 600,  # 10 minutes
                "rate_limit": 200,  # 200 requests per hour
                "max_historical_days": 30
            },
            "linkedin": {
                "realtime_metrics": ["likes", "comments", "shares", "impressions"],
                "historical_metrics": ["engagement_rate", "reach", "follower_growth"],
                "collection_interval": 900,  # 15 minutes
                "rate_limit": 100,  # 100 requests per hour
                "max_historical_days": 30
            },
            "instagram": {
                "realtime_metrics": ["likes", "comments", "saves", "reach", "impressions"],
                "historical_metrics": ["engagement_rate", "follower_growth", "story_views"],
                "collection_interval": 600,  # 10 minutes
                "rate_limit": 200, # 200 requests per hour
                "max_historical_days": 30
            }
        }
    
    async def collect_realtime_metrics(
        self,
        content_id: int,
        platforms: List[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Collect real-time metrics for published content
        
        Args:
            content_id: ID of the content piece
            platforms: Specific platforms to collect from (None for all)
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            Dict containing collection results
        """
        try:
            # Get content and social posts
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id,
                SocialPost.status == ContentStatus.PUBLISHED
            ).all()
            
            if not social_posts:
                return {
                    "success": False,
                    "error": "No published social posts found for this content"
                }
            
            # Filter platforms if specified
            if platforms:
                social_posts = [post for post in social_posts if post.platform in platforms]
            
            # Create collection job
            job_id = str(uuid.uuid4())
            collection_job = AnalyticsCollectionJob(
                job_id=job_id,
                content_id=content_id,
                platforms=[post.platform for post in social_posts],
                collection_type="realtime",
                status=AnalyticsStatus.PENDING,
                created_at=datetime.utcnow(),
                results={},
                errors=[],
                metadata={
                    "content_title": content.title,
                    "content_type": content.type,
                    "force_refresh": force_refresh
                }
            )
            
            # Store job
            self.active_collection_jobs[job_id] = collection_job
            await self._store_collection_job(collection_job)
            
            # Start collection process
            asyncio.create_task(self._execute_collection_job(collection_job, social_posts))
            
            logger.info(f"Started real-time metrics collection job {job_id} for content {content_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "collecting",
                "platforms": [post.platform for post in social_posts],
                "message": f"Real-time metrics collection started for {len(social_posts)} platform(s)"
            }
            
        except Exception as e:
            logger.error(f"Failed to start real-time metrics collection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def collect_historical_metrics(
        self,
        content_id: int,
        start_date: datetime,
        end_date: datetime,
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Collect historical metrics for content over a date range
        
        Args:
            content_id: ID of the content piece
            start_date: Start date for historical collection
            end_date: End date for historical collection
            platforms: Specific platforms to collect from (None for all)
            
        Returns:
            Dict containing collection results
        """
        try:
            # Validate date range
            if start_date >= end_date:
                return {
                    "success": False,
                    "error": "Start date must be before end date"
                }
            
            if (end_date - start_date).days > 30:
                return {
                    "success": False,
                    "error": "Historical collection limited to 30 days"
                }
            
            # Get content and social posts
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content:
                return {
                    "success": False,
                    "error": "Content not found"
                }
            
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id,
                SocialPost.status == ContentStatus.PUBLISHED
            ).all()
            
            if not social_posts:
                return {
                    "success": False,
                    "error": "No published social posts found for this content"
                }
            
            # Filter platforms if specified
            if platforms:
                social_posts = [post for post in social_posts if post.platform in platforms]
            
            # Create collection job
            job_id = str(uuid.uuid4())
            collection_job = AnalyticsCollectionJob(
                job_id=job_id,
                content_id=content_id,
                platforms=[post.platform for post in social_posts],
                collection_type="historical",
                status=AnalyticsStatus.PENDING,
                created_at=datetime.utcnow(),
                results={},
                errors=[],
                metadata={
                    "content_title": content.title,
                    "content_type": content.type,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "date_range_days": (end_date - start_date).days
                }
            )
            
            # Store job
            self.active_collection_jobs[job_id] = collection_job
            await self._store_collection_job(collection_job)
            
            # Start collection process
            asyncio.create_task(self._execute_historical_collection_job(collection_job, social_posts, start_date, end_date))
            
            logger.info(f"Started historical metrics collection job {job_id} for content {content_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "collecting",
                "platforms": [post.platform for post in social_posts],
                "date_range": f"{start_date.date()} to {end_date.date()}",
                "message": f"Historical metrics collection started for {len(social_posts)} platform(s)"
            }
            
        except Exception as e:
            logger.error(f"Failed to start historical metrics collection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_collection_job(
        self,
        collection_job: AnalyticsCollectionJob,
        social_posts: List[SocialPost]
    ):
        """Execute a real-time metrics collection job"""
        try:
            collection_job.status = AnalyticsStatus.COLLECTING
            collection_job.started_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
            
            # Collect metrics from each platform concurrently
            collection_tasks = []
            for post in social_posts:
                task = asyncio.create_task(
                    self._collect_platform_metrics(collection_job, post)
                )
                collection_tasks.append(task)
            
            # Wait for all collection tasks to complete
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                post = social_posts[i]
                if isinstance(result, Exception):
                    collection_job.results[post.platform] = PlatformMetrics(
                        platform=post.platform,
                        post_id=post.id,
                        platform_post_id=post.metrics.get("platform_post_id", "") if post.metrics else "",
                        collected_at=datetime.utcnow(),
                        metrics={},
                        raw_data={},
                        error_message=str(result)
                    )
                    collection_job.errors.append(f"{post.platform}: {str(result)}")
                else:
                    collection_job.results[post.platform] = result
            
            # Determine overall job status
            successful_collections = sum(1 for r in collection_job.results.values() if not r.error_message)
            if successful_collections == len(social_posts):
                collection_job.status = AnalyticsStatus.COMPLETED
            elif successful_collections > 0:
                collection_job.status = AnalyticsStatus.PARTIAL
            else:
                collection_job.status = AnalyticsStatus.FAILED
            
            collection_job.completed_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
            
            # Store collected metrics
            await self._store_collected_metrics(collection_job)
            
            # Send to analytics queue for processing
            await self._send_to_analytics_queue(collection_job)
            
            logger.info(f"Completed collection job {collection_job.job_id} with status: {collection_job.status}")
            
        except Exception as e:
            logger.error(f"Failed to execute collection job {collection_job.job_id}: {e}")
            collection_job.status = AnalyticsStatus.FAILED
            collection_job.errors.append(str(e))
            collection_job.completed_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
    
    async def _execute_historical_collection_job(
        self,
        collection_job: AnalyticsCollectionJob,
        social_posts: List[SocialPost],
        start_date: datetime,
        end_date: datetime
    ):
        """Execute a historical metrics collection job"""
        try:
            collection_job.status = AnalyticsStatus.COLLECTING
            collection_job.started_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
            
            # Collect historical metrics from each platform
            collection_tasks = []
            for post in social_posts:
                task = asyncio.create_task(
                    self._collect_historical_platform_metrics(collection_job, post, start_date, end_date)
                )
                collection_tasks.append(task)
            
            # Wait for all collection tasks to complete
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process results (similar to real-time collection)
            for i, result in enumerate(results):
                post = social_posts[i]
                if isinstance(result, Exception):
                    collection_job.results[post.platform] = PlatformMetrics(
                        platform=post.platform,
                        post_id=post.id,
                        platform_post_id=post.metrics.get("platform_post_id", "") if post.metrics else "",
                        collected_at=datetime.utcnow(),
                        metrics={},
                        raw_data={},
                        error_message=str(result)
                    )
                    collection_job.errors.append(f"{post.platform}: {str(result)}")
                else:
                    collection_job.results[post.platform] = result
            
            # Determine overall job status
            successful_collections = sum(1 for r in collection_job.results.values() if not r.error_message)
            if successful_collections == len(social_posts):
                collection_job.status = AnalyticsStatus.COMPLETED
            elif successful_collections > 0:
                collection_job.status = AnalyticsStatus.PARTIAL
            else:
                collection_job.status = AnalyticsStatus.FAILED
            
            collection_job.completed_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
            
            # Store collected metrics
            await self._store_collected_metrics(collection_job)
            
            # Send to analytics queue for processing
            await self._send_to_analytics_queue(collection_job)
            
            logger.info(f"Completed historical collection job {collection_job.job_id} with status: {collection_job.status}")
            
        except Exception as e:
            logger.error(f"Failed to execute historical collection job {collection_job.job_id}: {e}")
            collection_job.status = AnalyticsStatus.FAILED
            collection_job.errors.append(str(e))
            collection_job.completed_at = datetime.utcnow()
            await self._update_collection_job(collection_job)
    
    async def _collect_platform_metrics(
        self,
        collection_job: AnalyticsCollectionJob,
        post: SocialPost
    ) -> PlatformMetrics:
        """Collect metrics from a specific platform"""
        try:
            platform = post.platform
            client = self.platform_clients.get(platform)
            
            if not client:
                raise ValueError(f"No client available for platform {platform}")
            
            # Check if we have cached metrics that are still fresh
            cache_key = f"metrics:{platform}:{post.id}:realtime"
            cached_metrics = await self.cache_service.get(cache_key)
            
            if cached_metrics and not collection_job.metadata.get("force_refresh", False):
                logger.info(f"Using cached metrics for {platform} post {post.id}")
                return PlatformMetrics(
                    platform=platform,
                    post_id=post.id,
                    platform_post_id=post.metrics.get("platform_post_id", "") if post.metrics else "",
                    collected_at=datetime.utcnow(),
                    metrics=cached_metrics["metrics"],
                    raw_data=cached_metrics["raw_data"]
                )
            
            # Collect fresh metrics from platform
            platform_post_id = post.metrics.get("platform_post_id", "") if post.metrics else ""
            
            if not platform_post_id:
                raise ValueError(f"No platform post ID available for {platform} post {post.id}")
            
            # Get metrics from platform
            metrics_result = await client.get_post_metrics(platform_post_id)
            
            if not metrics_result.get("success"):
                raise ValueError(f"Failed to get metrics from {platform}: {metrics_result.get('error_message', 'Unknown error')}")
            
            # Extract and normalize metrics
            raw_metrics = metrics_result.get("metrics", {})
            normalized_metrics = self._normalize_platform_metrics(platform, raw_metrics)
            
            # Create platform metrics object
            platform_metrics = PlatformMetrics(
                platform=platform,
                post_id=post.id,
                platform_post_id=platform_post_id,
                collected_at=datetime.utcnow(),
                metrics=normalized_metrics,
                raw_data=raw_metrics
            )
            
            # Cache the metrics
            cache_data = {
                "metrics": normalized_metrics,
                "raw_data": raw_metrics,
                "collected_at": datetime.utcnow().isoformat()
            }
            await self.cache_service.set(cache_key, cache_data, self.metrics_cache_ttl)
            
            return platform_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics from {post.platform}: {e}")
            raise
    
    async def _collect_historical_platform_metrics(
        self,
        collection_job: AnalyticsCollectionJob,
        post: SocialPost,
        start_date: datetime,
        end_date: datetime
    ) -> PlatformMetrics:
        """Collect historical metrics from a specific platform"""
        try:
            platform = post.platform
            client = self.platform_clients.get(platform)
            
            if not client:
                raise ValueError(f"No client available for platform {platform}")
            
            # Check if we have cached historical metrics
            cache_key = f"metrics:{platform}:{post.id}:historical:{start_date.date()}:{end_date.date()}"
            cached_metrics = await self.cache_service.get(cache_key)
            
            if cached_metrics:
                logger.info(f"Using cached historical metrics for {platform} post {post.id}")
                return PlatformMetrics(
                    platform=platform,
                    post_id=post.id,
                    platform_post_id=post.metrics.get("platform_post_id", "") if post.metrics else "",
                    collected_at=datetime.utcnow(),
                    metrics=cached_metrics["metrics"],
                    raw_data=cached_metrics["raw_data"]
                )
            
            # Collect historical metrics from platform
            platform_post_id = post.metrics.get("platform_post_id", "") if post.metrics else ""
            
            if not platform_post_id:
                raise ValueError(f"No platform post ID available for {platform} post {post.id}")
            
            # Get historical metrics from platform
            # Note: This would require platform-specific historical metrics endpoints
            # For now, we'll simulate historical collection
            historical_metrics = await self._simulate_historical_collection(platform, platform_post_id, start_date, end_date)
            
            # Create platform metrics object
            platform_metrics = PlatformMetrics(
                platform=platform,
                post_id=post.id,
                platform_post_id=platform_post_id,
                collected_at=datetime.utcnow(),
                metrics=historical_metrics,
                raw_data={"historical_data": True, "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}
            )
            
            # Cache the historical metrics
            cache_data = {
                "metrics": historical_metrics,
                "raw_data": platform_metrics.raw_data,
                "collected_at": datetime.utcnow().isoformat()
            }
            await self.cache_service.set(cache_key, cache_data, self.metrics_cache_ttl * 24)  # Longer TTL for historical data
            
            return platform_metrics
            
        except Exception as e:
            logger.error(f"Failed to collect historical metrics from {post.platform}: {e}")
            raise
    
    def _normalize_platform_metrics(self, platform: str, raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize metrics from different platforms to a standard format"""
        try:
            normalized = {}
            
            # Platform-specific metric mapping
            metric_mapping = {
                "twitter": {
                    "likes": "like_count",
                    "retweets": "retweet_count", 
                    "replies": "reply_count",
                    "impressions": "impression_count",
                    "engagement_rate": "engagement_rate"
                },
                "facebook": {
                    "likes": "like_count",
                    "shares": "share_count",
                    "comments": "comment_count",
                    "reach": "reach_count",
                    "impressions": "impression_count"
                },
                "linkedin": {
                    "likes": "like_count",
                    "comments": "comment_count",
                    "shares": "share_count",
                    "impressions": "impression_count"
                },
                "instagram": {
                    "likes": "like_count",
                    "comments": "comment_count",
                    "saves": "save_count",
                    "reach": "reach_count",
                    "impressions": "impression_count"
                }
            }
            
            mapping = metric_mapping.get(platform, {})
            
            # Map and normalize metrics
            for standard_name, platform_name in mapping.items():
                if platform_name in raw_metrics:
                    value = raw_metrics[platform_name]
                    if isinstance(value, (int, float)):
                        normalized[standard_name] = value
                    else:
                        try:
                            normalized[standard_name] = float(value)
                        except (ValueError, TypeError):
                            normalized[standard_name] = 0
            
            # Calculate engagement rate if not provided
            if "engagement_rate" not in normalized and "like_count" in normalized:
                total_engagement = sum([
                    normalized.get("like_count", 0),
                    normalized.get("comment_count", 0),
                    normalized.get("share_count", 0),
                    normalized.get("retweet_count", 0)
                ])
                
                if "impression_count" in normalized and normalized["impression_count"] > 0:
                    normalized["engagement_rate"] = (total_engagement / normalized["impression_count"]) * 100
                else:
                    normalized["engagement_rate"] = 0
            
            # Add platform-specific metadata
            normalized["platform"] = platform
            normalized["normalized_at"] = datetime.utcnow().isoformat()
            
            return normalized
            
        except Exception as e:
            logger.error(f"Failed to normalize metrics for {platform}: {e}")
            return {"error": str(e), "platform": platform}
    
    async def _simulate_historical_collection(
        self,
        platform: str,
        platform_post_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Simulate historical metrics collection (placeholder for actual implementation)"""
        try:
            # This is a placeholder implementation
            # In production, this would call platform-specific historical metrics APIs
            
            days_range = (end_date - start_date).days
            base_metrics = {
                "like_count": 100,
                "comment_count": 25,
                "share_count": 15,
                "impression_count": 5000,
                "reach_count": 3000
            }
            
            # Simulate daily variations
            historical_data = {}
            current_date = start_date
            
            while current_date <= end_date:
                date_key = current_date.strftime("%Y-%m-%d")
                daily_metrics = {}
                
                for metric, base_value in base_metrics.items():
                    # Add some random variation
                    import random
                    variation = random.uniform(0.8, 1.2)
                    daily_metrics[metric] = int(base_value * variation)
                
                # Calculate engagement rate
                total_engagement = sum([
                    daily_metrics.get("like_count", 0),
                    daily_metrics.get("comment_count", 0),
                    daily_metrics.get("share_count", 0)
                ])
                
                if daily_metrics.get("impression_count", 0) > 0:
                    daily_metrics["engagement_rate"] = round(
                        (total_engagement / daily_metrics["impression_count"]) * 100, 2
                    )
                else:
                    daily_metrics["engagement_rate"] = 0
                
                historical_data[date_key] = daily_metrics
                current_date += timedelta(days=1)
            
            return {
                "historical_data": historical_data,
                "summary": {
                    "total_likes": sum(data["like_count"] for data in historical_data.values()),
                    "total_comments": sum(data["comment_count"] for data in historical_data.values()),
                    "total_shares": sum(data["share_count"] for data in historical_data.values()),
                    "total_impressions": sum(data["impression_count"] for data in historical_data.values()),
                    "avg_engagement_rate": round(
                        sum(data["engagement_rate"] for data in historical_data.values()) / len(historical_data), 2
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to simulate historical collection for {platform}: {e}")
            return {"error": str(e)}
    
    async def _store_collected_metrics(self, collection_job: AnalyticsCollectionJob):
        """Store collected metrics in the database"""
        try:
            for platform, platform_metrics in collection_job.results.items():
                if platform_metrics.error_message:
                    continue
                
                # Update social post metrics
                social_post = self.db.query(SocialPost).filter(
                    SocialPost.content_id == collection_job.content_id,
                    SocialPost.platform == platform
                ).first()
                
                if social_post:
                    # Merge new metrics with existing ones
                    existing_metrics = social_post.metrics or {}
                    existing_metrics.update({
                        "last_collected": datetime.utcnow().isoformat(),
                        "collection_job_id": collection_job.job_id,
                        "metrics": platform_metrics.metrics,
                        "raw_data": platform_metrics.raw_data
                    })
                    
                    social_post.metrics = existing_metrics
                    self.db.commit()
                    
                    logger.info(f"Updated metrics for {platform} post {social_post.id}")
            
        except Exception as e:
            logger.error(f"Failed to store collected metrics: {e}")
            self.db.rollback()
    
    async def _send_to_analytics_queue(self, collection_job: AnalyticsCollectionJob):
        """Send collection results to analytics processing queue"""
        try:
            queue_data = {
                "job_id": collection_job.job_id,
                "content_id": collection_job.content_id,
                "collection_type": collection_job.collection_type,
                "status": collection_job.status.value,
                "platforms": list(collection_job.results.keys()),
                "completed_at": collection_job.completed_at.isoformat() if collection_job.completed_at else None,
                "results_summary": {
                    platform: {
                        "has_metrics": not metrics.error_message,
                        "metric_count": len(metrics.metrics) if metrics.metrics else 0,
                        "error": metrics.error_message
                    }
                    for platform, metrics in collection_job.results.items()
                }
            }
            
            await self.redis_service.lpush(
                self.analytics_queue,
                json.dumps(queue_data)
            )
            
            logger.info(f"Sent collection job {collection_job.job_id} to analytics queue")
            
        except Exception as e:
            logger.error(f"Failed to send to analytics queue: {e}")
    
    async def get_collection_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of an analytics collection job"""
        try:
            # Check memory first
            if job_id in self.active_collection_jobs:
                job = self.active_collection_jobs[job_id]
            else:
                # Try to retrieve from Redis
                job_data = await self.redis_service.get(f"analytics_job:{job_id}")
                if job_data:
                    job_data_dict = json.loads(job_data)
                    job = AnalyticsCollectionJob(**job_data_dict)
                else:
                    return {
                        "success": False,
                        "error": "Collection job not found"
                    }
            
            return {
                "success": True,
                "job": {
                    "job_id": job.job_id,
                    "content_id": job.content_id,
                    "platforms": job.platforms,
                    "collection_type": job.collection_type,
                    "status": job.status.value,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "results": {
                        platform: {
                            "has_metrics": not metrics.error_message,
                            "metric_count": len(metrics.metrics) if metrics.metrics else 0,
                            "error": metrics.error_message,
                            "collected_at": metrics.collected_at.isoformat()
                        }
                        for platform, metrics in job.results.items()
                    },
                    "errors": job.errors,
                    "metadata": job.metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection status for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_collection_job(self, collection_job: AnalyticsCollectionJob):
        """Store collection job in Redis"""
        try:
            job_data = json.dumps(asdict(collection_job), default=str)
            await self.redis_service.set(
                f"analytics_job:{collection_job.job_id}",
                job_data,
                ex=7200  # Expire in 2 hours
            )
        except Exception as e:
            logger.error(f"Failed to store collection job: {e}")
    
    async def _update_collection_job(self, collection_job: AnalyticsCollectionJob):
        """Update collection job in Redis"""
        try:
            await self._store_collection_job(collection_job)
        except Exception as e:
            logger.error(f"Failed to update collection job: {e}")
    
    async def get_analytics_summary(self, content_id: int) -> Dict[str, Any]:
        """Get a summary of analytics data for content"""
        try:
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id,
                SocialPost.status == ContentStatus.PUBLISHED
            ).all()
            
            summary = {
                "content_id": content_id,
                "total_posts": len(social_posts),
                "platforms": {},
                "overall_metrics": {
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_impressions": 0,
                    "total_reach": 0,
                    "avg_engagement_rate": 0
                }
            }
            
            for post in social_posts:
                platform = post.platform
                metrics = post.metrics or {}
                
                platform_metrics = {
                    "post_id": post.id,
                    "platform_post_id": metrics.get("platform_post_id", ""),
                    "publish_date": post.publish_date.isoformat() if post.publish_date else None,
                    "last_collected": metrics.get("last_collected"),
                    "metrics": metrics.get("metrics", {}),
                    "has_metrics": bool(metrics.get("metrics"))
                }
                
                summary["platforms"][platform] = platform_metrics
                
                # Aggregate overall metrics
                post_metrics = metrics.get("metrics", {})
                summary["overall_metrics"]["total_likes"] += post_metrics.get("like_count", 0)
                summary["overall_metrics"]["total_comments"] += post_metrics.get("comment_count", 0)
                summary["overall_metrics"]["total_shares"] += post_metrics.get("share_count", 0)
                summary["overall_metrics"]["total_impressions"] += post_metrics.get("impression_count", 0)
                summary["overall_metrics"]["total_reach"] += post_metrics.get("reach_count", 0)
            
            # Calculate average engagement rate
            if summary["overall_metrics"]["total_impressions"] > 0:
                total_engagement = (
                    summary["overall_metrics"]["total_likes"] +
                    summary["overall_metrics"]["total_comments"] +
                    summary["overall_metrics"]["total_shares"]
                )
                summary["overall_metrics"]["avg_engagement_rate"] = round(
                    (total_engagement / summary["overall_metrics"]["total_impressions"]) * 100, 2
                )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old collection jobs"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            jobs_to_remove = []
            
            for job_id, job in self.active_collection_jobs.items():
                if job.created_at < cutoff_time:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.active_collection_jobs[job_id]
            
            logger.info(f"Cleaned up {len(jobs_to_remove)} old collection jobs")
            return len(jobs_to_remove)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0




