"""
Social Media Publishing Service
Core service for managing social media publishing operations across multiple platforms
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import uuid

from sqlalchemy.orm import Session
from celery import Celery

from app.models.schema import SocialPost, ContentPiece, ContentStatus
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.social_scheduler import ContentType, PlatformType, SocialMediaScheduler

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    """Supported social media platforms"""
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"

class PostStatus(Enum):
    """Post status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PublishingErrorType(Enum):
    """Types of publishing errors"""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    CONTENT_VALIDATION = "content_validation"
    NETWORK = "network"
    PLATFORM_UNAVAILABLE = "platform_unavailable"

@dataclass
class PostingSchedule:
    """Data structure for posting schedule"""
    platform: PlatformType
    content_id: int
    scheduled_time: datetime
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class PublishingResult:
    """Result of publishing operation"""
    success: bool
    post_id: Optional[str] = None
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[PublishingErrorType] = None
    metrics: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None
    platform_response: Optional[Dict[str, Any]] = None

@dataclass
class PublishingJob:
    """Publishing job for coordination"""
    job_id: str
    content_id: int
    platforms: List[PlatformType]
    priority: int
    scheduled_time: Optional[datetime] = None
    status: str = "pending"
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, PublishingResult] = None
    errors: List[str] = None

class SocialMediaPublisher:
    """
    Enhanced social media publishing service that orchestrates:
    - Content scheduling and optimization
    - Multi-platform publishing with coordination
    - Real-time status monitoring
    - Analytics collection
    - Error handling and retries
    - Cross-platform publishing management
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService, scheduler: SocialMediaScheduler):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.scheduler = scheduler
        self.platform_clients = {}
        self.scheduling_queue = "social_publishing_queue"
        self.analytics_queue = "social_analytics_queue"
        self.publishing_jobs_queue = "publishing_jobs_queue"
        self.status_updates_queue = "status_updates_queue"
        
        # Publishing coordination
        self.active_jobs: Dict[str, PublishingJob] = {}
        self.publishing_locks: Dict[str, asyncio.Lock] = {}
        
        # Initialize platform clients
        self._initialize_platform_clients()
    
    def _initialize_platform_clients(self):
        """Initialize platform-specific API clients"""
        try:
            from .social_clients.twitter_client import TwitterClient
            from .social_clients.facebook_client import FacebookClient
            from .social_clients.linkedin_client import LinkedInClient
            from .social_clients.instagram_client import InstagramClient
            
            self.platform_clients = {
                PlatformType.TWITTER: TwitterClient(),
                PlatformType.FACEBOOK: FacebookClient(),
                PlatformType.LINKEDIN: LinkedInClient(),
                PlatformType.INSTAGRAM: InstagramClient()
            }
            logger.info("Platform clients initialized successfully")
        except ImportError as e:
            logger.warning(f"Some platform clients could not be initialized: {e}")
    
    async def publish_content_immediately(
        self,
        content_id: int,
        platforms: List[PlatformType],
        priority: int = 1,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Publish content immediately to specified platforms
        
        Args:
            content_id: ID of the content piece to publish
            platforms: Target social media platforms
            priority: Publishing priority
            user_id: User requesting the publish
            
        Returns:
            Dict containing publishing job information
        """
        try:
            # Validate content exists and is approved
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id,
                ContentPiece.status == ContentStatus.APPROVED
            ).first()
            
            if not content:
                return {
                    "success": False,
                    "error": "Content not found or not approved"
                }
            
            # Create publishing job
            job_id = str(uuid.uuid4())
            publishing_job = PublishingJob(
                job_id=job_id,
                content_id=content_id,
                platforms=platforms,
                priority=priority,
                scheduled_time=datetime.utcnow(),
                status="pending",
                created_at=datetime.utcnow(),
                results={},
                errors=[]
            )
            
            # Store job in memory and Redis
            self.active_jobs[job_id] = publishing_job
            await self._store_publishing_job(publishing_job)
            
            # Start publishing process
            asyncio.create_task(self._execute_publishing_job(publishing_job))
            
            logger.info(f"Started immediate publishing job {job_id} for content {content_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "publishing",
                "platforms": [p.value for p in platforms],
                "message": f"Publishing started for {len(platforms)} platform(s)"
            }
            
        except Exception as e:
            logger.error(f"Failed to start immediate publishing: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def publish_content_scheduled(
        self,
        content_id: int,
        platforms: List[PlatformType],
        scheduled_time: datetime,
        priority: int = 1,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Schedule content for publishing at a specific time
        
        Args:
            content_id: ID of the content piece to publish
            platforms: Target social media platforms
            scheduled_time: When to publish the content
            priority: Publishing priority
            user_id: User scheduling the publish
            
        Returns:
            Dict containing scheduling result
        """
        try:
            # Validate content exists and is approved
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id,
                ContentPiece.status == ContentStatus.APPROVED
            ).first()
            
            if not content:
                return {
                    "success": False,
                    "error": "Content not found or not approved"
                }
            
            # Create publishing job for scheduling
            job_id = str(uuid.uuid4())
            publishing_job = PublishingJob(
                job_id=job_id,
                content_id=content_id,
                platforms=platforms,
                priority=priority,
                scheduled_time=scheduled_time,
                status="scheduled",
                created_at=datetime.utcnow(),
                results={},
                errors=[]
            )
            
            # Store job for scheduling
            await self._store_publishing_job(publishing_job)
            
            # Add to scheduling queue
            for platform in platforms:
                schedule = PostingSchedule(
                    platform=platform,
                    content_id=content_id,
                    scheduled_time=scheduled_time,
                    priority=priority
                )
                await self._add_to_scheduling_queue(schedule, job_id)
            
            # Update database status
            for platform in platforms:
                social_post = SocialPost(
                    platform=platform.value,
                    content_id=content_id,
                    status=ContentStatus.DRAFT,
                    publish_date=scheduled_time
                )
                self.db.add(social_post)
            
            self.db.commit()
            
            logger.info(f"Scheduled publishing job {job_id} for content {content_id} at {scheduled_time}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "scheduled",
                "scheduled_time": scheduled_time.isoformat(),
                "platforms": [p.value for p in platforms]
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule publishing: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_publishing_job(self, publishing_job: PublishingJob):
        """Execute a publishing job across all platforms"""
        try:
            publishing_job.status = "publishing"
            publishing_job.started_at = datetime.utcnow()
            await self._update_publishing_job(publishing_job)
            
            # Get content
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == publishing_job.content_id
            ).first()
            
            if not content:
                publishing_job.errors.append("Content not found")
                publishing_job.status = "failed"
                await self._update_publishing_job(publishing_job)
                return
            
            # Publish to each platform concurrently
            publishing_tasks = []
            for platform in publishing_job.platforms:
                task = asyncio.create_task(
                    self._publish_to_platform(publishing_job, platform, content)
                )
                publishing_tasks.append(task)
            
            # Wait for all publishing tasks to complete
            results = await asyncio.gather(*publishing_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                platform = publishing_job.platforms[i]
                if isinstance(result, Exception):
                    publishing_job.results[platform.value] = PublishingResult(
                        success=False,
                        error_message=str(result),
                        error_type=PublishingErrorType.API_ERROR
                    )
                    publishing_job.errors.append(f"{platform.value}: {str(result)}")
                else:
                    publishing_job.results[platform.value] = result
            
            # Determine overall job status
            successful_publishes = sum(1 for r in publishing_job.results.values() if r.success)
            if successful_publishes == len(publishing_job.platforms):
                publishing_job.status = "completed"
            elif successful_publishes > 0:
                publishing_job.status = "partially_completed"
            else:
                publishing_job.status = "failed"
            
            publishing_job.completed_at = datetime.utcnow()
            await self._update_publishing_job(publishing_job)
            
            # Send status update
            await self._send_status_update(publishing_job)
            
            logger.info(f"Completed publishing job {publishing_job.job_id} with status: {publishing_job.status}")
            
        except Exception as e:
            logger.error(f"Failed to execute publishing job {publishing_job.job_id}: {e}")
            publishing_job.status = "failed"
            publishing_job.errors.append(str(e))
            publishing_job.completed_at = datetime.utcnow()
            await self._update_publishing_job(publishing_job)
    
    async def _publish_to_platform(
        self,
        publishing_job: PublishingJob,
        platform: PlatformType,
        content: ContentPiece
    ) -> PublishingResult:
        """Publish content to a specific platform"""
        try:
            # Get platform client
            client = self.platform_clients.get(platform)
            if not client:
                return PublishingResult(
                    success=False,
                    error_message=f"No client available for platform {platform.value}",
                    error_type=PublishingErrorType.PLATFORM_UNAVAILABLE
                )
            
            # Check if client is authenticated
            if not client.is_authenticated:
                # Try to authenticate with stored credentials
                from .social_credentials import SocialCredentialsManager
                cred_manager = SocialCredentialsManager()
                credentials = cred_manager.retrieve_encrypted_credentials(platform.value)
                
                if credentials:
                    auth_success = await client.authenticate(credentials)
                    if not auth_success:
                        return PublishingResult(
                            success=False,
                            error_message=f"Authentication failed for {platform.value}",
                            error_type=PublishingErrorType.AUTHENTICATION
                        )
                else:
                    return PublishingResult(
                        success=False,
                        error_message=f"No credentials available for {platform.value}",
                        error_type=PublishingErrorType.AUTHENTICATION
                    )
            
            # Prepare content for platform
            schedule_data = {
                "scheduled_time": publishing_job.scheduled_time,
                "priority": publishing_job.priority
            }
            
            # Publish content
            result = await client.publish_content(content, schedule_data)
            
            if result.get("success"):
                # Update database
                social_post = self.db.query(SocialPost).filter(
                    SocialPost.content_id == publishing_job.content_id,
                    SocialPost.platform == platform.value
                ).first()
                
                if social_post:
                    social_post.status = ContentStatus.PUBLISHED
                    social_post.metrics = result.get("metrics", {})
                    self.db.commit()
                
                return PublishingResult(
                    success=True,
                    post_id=result.get("post_id"),
                    platform_post_id=result.get("platform_post_id"),
                    metrics=result.get("metrics"),
                    published_at=datetime.utcnow(),
                    platform_response=result
                )
            else:
                return PublishingResult(
                    success=False,
                    error_message=result.get("error_message", "Unknown publishing error"),
                    error_type=PublishingErrorType.API_ERROR,
                    platform_response=result
                )
                
        except Exception as e:
            logger.error(f"Failed to publish to {platform.value}: {e}")
            return PublishingResult(
                success=False,
                error_message=str(e),
                error_type=PublishingErrorType.API_ERROR
            )
    
    async def get_publishing_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of a publishing job"""
        try:
            # Check memory first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            else:
                # Try to retrieve from Redis
                job_data = await self.redis_service.get(f"publishing_job:{job_id}")
                if job_data:
                    job = PublishingJob(**json.loads(job_data))
                else:
                    return {
                        "success": False,
                        "error": "Publishing job not found"
                    }
            
            return {
                "success": True,
                "job": {
                    "job_id": job.job_id,
                    "content_id": job.content_id,
                    "platforms": [p.value for p in job.platforms],
                    "priority": job.priority,
                    "status": job.status,
                    "scheduled_time": job.scheduled_time.isoformat() if job.scheduled_time else None,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "results": {
                        platform: result.__dict__ for platform, result in job.results.items()
                    },
                    "errors": job.errors
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get publishing status for job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_publishing_job(self, job_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel a publishing job"""
        try:
            # Check memory first
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
            else:
                # Try to retrieve from Redis
                job_data = await self.redis_service.get(f"publishing_job:{job_id}")
                if job_data:
                    job = PublishingJob(**json.loads(job_data))
                else:
                    return {
                        "success": False,
                        "error": "Publishing job not found"
                    }
            
            # Check if job can be cancelled
            if job.status in ["completed", "failed"]:
                return {
                    "success": False,
                    "error": "Cannot cancel completed or failed job"
                }
            
            # Cancel the job
            job.status = "cancelled"
            job.completed_at = datetime.utcnow()
            job.errors.append(f"Cancelled by user {user_id}")
            
            # Update job status
            await self._update_publishing_job(job)
            
            # Cancel any scheduled posts
            for platform in job.platforms:
                await self.cancel_scheduled_post(job.content_id, platform)
            
            # Send status update
            await self._send_status_update(job)
            
            logger.info(f"Cancelled publishing job {job_id} by user {user_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "cancelled",
                "message": "Publishing job cancelled successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel publishing job {job_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _store_publishing_job(self, publishing_job: PublishingJob):
        """Store publishing job in Redis"""
        try:
            job_data = json.dumps(publishing_job.__dict__, default=str)
            await self.redis_service.set(
                f"publishing_job:{publishing_job.job_id}",
                job_data,
                ex=3600  # Expire in 1 hour
            )
        except Exception as e:
            logger.error(f"Failed to store publishing job: {e}")
    
    async def _update_publishing_job(self, publishing_job: PublishingJob):
        """Update publishing job in Redis"""
        try:
            await self._store_publishing_job(publishing_job)
        except Exception as e:
            logger.error(f"Failed to update publishing job: {e}")
    
    async def _send_status_update(self, publishing_job: PublishingJob):
        """Send status update to monitoring queue"""
        try:
            status_update = {
                "job_id": publishing_job.job_id,
                "status": publishing_job.status,
                "timestamp": datetime.utcnow().isoformat(),
                "results": {
                    platform: {
                        "success": result.success,
                        "error_message": result.error_message,
                        "error_type": result.error_type.value if result.error_type else None
                    }
                    for platform, result in publishing_job.results.items()
                }
            }
            
            await self.redis_service.lpush(
                self.status_updates_queue,
                json.dumps(status_update)
            )
            
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
    
    async def _add_to_scheduling_queue(self, schedule: PostingSchedule, job_id: str):
        """Add a posting schedule to the Redis queue with job ID"""
        try:
            schedule_data = {
                "platform": schedule.platform.value,
                "content_id": schedule.content_id,
                "scheduled_time": schedule.scheduled_time.isoformat(),
                "priority": schedule.priority,
                "retry_count": schedule.retry_count,
                "max_retries": schedule.max_retries,
                "job_id": job_id
            }
            
            # Use priority queue for scheduling
            await self.redis_service.zadd(
                self.scheduling_queue,
                schedule.scheduled_time.timestamp(),
                json.dumps(schedule_data)
            )
            
            logger.debug(f"Added to scheduling queue: {schedule_data}")
            
        except Exception as e:
            logger.error(f"Failed to add to scheduling queue: {e}")
            raise
    
    async def process_scheduled_posts(self):
        """Process all scheduled posts that are due for publishing"""
        try:
            current_time = datetime.utcnow()
            
            # Get all posts due for publishing
            due_posts = await self.redis_service.zrangebyscore(
                self.scheduling_queue,
                0,
                current_time.timestamp()
            )
            
            for post_data in due_posts:
                try:
                    schedule_data = json.loads(post_data)
                    job_id = schedule_data.get("job_id")
                    
                    # Retrieve publishing job
                    if job_id:
                        job_data = await self.redis_service.get(f"publishing_job:{job_id}")
                        if job_data:
                            publishing_job = PublishingJob(**json.loads(job_data))
                            
                            # Execute the job
                            asyncio.create_task(self._execute_publishing_job(publishing_job))
                        else:
                            logger.warning(f"Publishing job {job_id} not found, processing as legacy post")
                            await self._publish_scheduled_post(schedule_data)
                    else:
                        # Legacy post processing
                        await self._publish_scheduled_post(schedule_data)
                    
                    # Remove from scheduling queue
                    await self.redis_service.zrem(self.scheduling_queue, post_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process scheduled post {post_data}: {e}")
                    # Keep in queue for retry if within retry limits
                    await self._handle_publishing_failure(post_data, e)
            
        except Exception as e:
            logger.error(f"Failed to process scheduled posts: {e}")
    
    async def _publish_scheduled_post(self, schedule_data: Dict[str, Any]):
        """Publish a scheduled post to the target platform (legacy method)"""
        try:
            platform = PlatformType(schedule_data["platform"])
            content_id = schedule_data["content_id"]
            
            # Get platform client
            client = self.platform_clients.get(platform)
            if not client:
                raise ValueError(f"No client available for platform {platform}")
            
            # Get content
            content = self.db.query(ContentPiece).filter(
                ContentPiece.id == content_id
            ).first()
            
            if not content:
                raise ValueError(f"Content {content_id} not found")
            
            # Update status to publishing
            social_post = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id,
                SocialPost.platform == platform.value
            ).first()
            
            if social_post:
                social_post.status = ContentStatus.IN_REVIEW  # Using existing enum
                self.db.commit()
            
            # Publish to platform
            result = await client.publish_content(content, schedule_data)
            
            # Handle result
            if result.get("success"):
                await self._handle_publishing_success(schedule_data, result)
            else:
                await self._handle_publishing_failure(schedule_data, result.get("error_message", "Unknown error"))
                
        except Exception as e:
            logger.error(f"Failed to publish scheduled post: {e}")
            await self._handle_publishing_failure(schedule_data, str(e))
    
    async def _handle_publishing_success(self, schedule_data: Dict[str, Any], result: Dict[str, Any]):
        """Handle successful publishing"""
        try:
            # Update database
            social_post = self.db.query(SocialPost).filter(
                SocialPost.content_id == schedule_data["content_id"],
                SocialPost.platform == schedule_data["platform"]
            ).first()
            
            if social_post:
                social_post.status = ContentStatus.PUBLISHED
                social_post.metrics = result.get("metrics", {})
                self.db.commit()
            
            # Add to analytics queue for metrics collection
            await self._add_to_analytics_queue(schedule_data, result)
            
            logger.info(f"Successfully published post {schedule_data['content_id']} to {schedule_data['platform']}")
            
        except Exception as e:
            logger.error(f"Failed to handle publishing success: {e}")
    
    async def _handle_publishing_failure(self, schedule_data: Dict[str, Any], error: str):
        """Handle publishing failure with retry logic"""
        try:
            retry_count = schedule_data.get("retry_count", 0)
            max_retries = schedule_data.get("max_retries", 3)
            
            if retry_count < max_retries:
                # Increment retry count and reschedule
                schedule_data["retry_count"] = retry_count + 1
                
                # Exponential backoff: wait 2^retry_count minutes
                backoff_minutes = 2 ** retry_count
                new_time = datetime.utcnow() + timedelta(minutes=backoff_minutes)
                
                # Reschedule with new time
                await self.redis_service.zadd(
                    self.scheduling_queue,
                    new_time.timestamp(),
                    json.dumps(schedule_data)
                )
                
                logger.info(f"Rescheduled post {schedule_data['content_id']} for retry {retry_count + 1}")
                
            else:
                # Max retries exceeded, mark as failed
                social_post = self.db.query(SocialPost).filter(
                    SocialPost.content_id == schedule_data["content_id"],
                    SocialPost.platform == schedule_data["platform"]
                ).first()
                
                if social_post:
                    social_post.status = ContentStatus.REJECTED  # Using existing enum
                    self.db.commit()
                
                logger.error(f"Post {schedule_data['content_id']} failed after {max_retries} retries")
                
        except Exception as e:
            logger.error(f"Failed to handle publishing failure: {e}")
    
    async def _add_to_analytics_queue(self, schedule_data: Dict[str, Any], result: Dict[str, Any]):
        """Add published post to analytics collection queue"""
        try:
            analytics_data = {
                "platform": schedule_data["platform"],
                "content_id": schedule_data["content_id"],
                "platform_post_id": result.get("platform_post_id"),
                "publish_time": datetime.utcnow().isoformat(),
                "metrics": result.get("metrics", {})
            }
            
            await self.redis_service.lpush(
                self.analytics_queue,
                json.dumps(analytics_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to add to analytics queue: {e}")
    
    async def get_publishing_status(self, content_id: int) -> Dict[str, Any]:
        """Get the publishing status for a specific content piece"""
        try:
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id
            ).all()
            
            status = {}
            for post in social_posts:
                status[post.platform] = {
                    "status": post.status.value,
                    "publish_date": post.publish_date.isoformat() if post.publish_date else None,
                    "metrics": post.metrics or {}
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get publishing status: {e}")
            return {}
    
    async def cancel_scheduled_post(self, content_id: int, platform: PlatformType) -> bool:
        """Cancel a scheduled post"""
        try:
            # Remove from scheduling queue
            queue_items = await self.redis_service.zrange(self.scheduling_queue, 0, -1)
            
            for item in queue_items:
                try:
                    schedule_data = json.loads(item)
                    if (schedule_data["content_id"] == content_id and 
                        schedule_data["platform"] == platform.value):
                        
                        await self.redis_service.zrem(self.scheduling_queue, item)
                        break
                        
                except json.JSONDecodeError:
                    continue
            
            # Update database status
            social_post = self.db.query(SocialPost).filter(
                SocialPost.content_id == content_id,
                SocialPost.platform == platform.value
            ).first()
            
            if social_post:
                social_post.status = ContentStatus.CANCELLED
                self.db.commit()
            
            logger.info(f"Cancelled scheduled post {content_id} for {platform.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel scheduled post: {e}")
            return False
    
    async def get_publishing_queue_status(self) -> Dict[str, Any]:
        """Get the current status of the publishing queue"""
        try:
            queue_size = await self.redis_service.zcard(self.scheduling_queue)
            
            # Get next few scheduled posts
            next_posts = await self.redis_service.zrange(
                self.scheduling_queue, 0, 4, withscores=True
            )
            
            upcoming = []
            for post_data, score in next_posts:
                try:
                    schedule_data = json.loads(post_data)
                    upcoming.append({
                        "content_id": schedule_data["content_id"],
                        "platform": schedule_data["platform"],
                        "scheduled_time": datetime.fromtimestamp(score).isoformat(),
                        "priority": schedule_data.get("priority", 1),
                        "job_id": schedule_data.get("job_id")
                    })
                except json.JSONDecodeError:
                    continue
            
            return {
                "queue_size": queue_size,
                "upcoming_posts": upcoming
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"queue_size": 0, "upcoming_posts": []}
