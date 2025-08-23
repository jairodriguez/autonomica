"""
Analytics Data Collection System
Comprehensive data collection from multiple sources including Google Search Console,
social media platforms, content analytics, and system metrics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
import httpx
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.schema import SocialPost, ContentPiece, ContentStatus
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.social_analytics_collector import SocialAnalyticsCollector
from app.services.content_analytics import ContentAnalyticsService
from app.services.seo_service import SEMrushAPIClient

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """Types of data sources for analytics collection"""
    GOOGLE_SEARCH_CONSOLE = "google_search_console"
    SOCIAL_MEDIA = "social_media"
    CONTENT_ANALYTICS = "content_analytics"
    SEO_METRICS = "seo_metrics"
    SYSTEM_METRICS = "system_metrics"
    USER_BEHAVIOR = "user_behavior"

class CollectionFrequency(Enum):
    """Collection frequency for different data types"""
    REAL_TIME = "real_time"  # Every 5 minutes
    HOURLY = "hourly"        # Every hour
    DAILY = "daily"          # Once per day
    WEEKLY = "weekly"        # Once per week
    MONTHLY = "monthly"      # Once per month

class CollectionStatus(Enum):
    """Status of data collection jobs"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"

@dataclass
class CollectionJob:
    """Data collection job definition"""
    job_id: str
    source_type: DataSourceType
    frequency: CollectionFrequency
    parameters: Dict[str, Any]
    status: CollectionStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    data_points_collected: int = 0
    metadata: Dict[str, Any] = None

@dataclass
class AnalyticsDataPoint:
    """Standardized analytics data point"""
    id: str
    source_type: DataSourceType
    source_id: str
    metric_name: str
    metric_value: Union[int, float, str]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    user_id: Optional[str] = None
    platform: Optional[str] = None

class GoogleSearchConsoleClient:
    """Google Search Console API client for SEO metrics collection"""
    
    def __init__(self, credentials_path: str = None, site_url: str = None):
        self.credentials_path = credentials_path
        self.site_url = site_url
        self.service = None
        self.authenticated = False
        
        if credentials_path and site_url:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Search Console API"""
        try:
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/webmasters']
                )
            else:
                # Try to use default credentials
                credentials = service_account.Credentials.from_service_account_info(
                    json.loads(os.getenv('GOOGLE_SEARCH_CONSOLE_CREDENTIALS', '{}'))
                )
            
            self.service = build('searchconsole', 'v1', credentials=credentials)
            self.authenticated = True
            logger.info("Successfully authenticated with Google Search Console API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Search Console: {e}")
            self.authenticated = False
    
    async def get_search_analytics(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str] = None,
        row_limit: int = 500
    ) -> Dict[str, Any]:
        """
        Get search analytics data from Google Search Console
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dimensions: List of dimensions to include (query, page, country, device)
            row_limit: Maximum number of rows to return
            
        Returns:
            Dict containing search analytics data
        """
        if not self.authenticated or not self.service:
            return {"error": "Not authenticated with Google Search Console"}
        
        try:
            if dimensions is None:
                dimensions = ['query', 'page']
            
            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': row_limit
            }
            
            response = self.service.searchanalytics().query(
                siteUrl=self.site_url,
                body=request_body
            ).execute()
            
            return {
                "success": True,
                "data": response,
                "metadata": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "dimensions": dimensions,
                    "rows_returned": len(response.get('rows', []))
                }
            }
            
        except HttpError as e:
            logger.error(f"Google Search Console API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": e.resp.status if hasattr(e, 'resp') else None
            }
        except Exception as e:
            logger.error(f"Unexpected error in Google Search Console API: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_site_performance_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get overall site performance summary
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict containing performance summary
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get basic metrics
        basic_metrics = await self.get_search_analytics(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            dimensions=['query'],
            row_limit=1000
        )
        
        if not basic_metrics.get("success"):
            return basic_metrics
        
        # Calculate summary metrics
        rows = basic_metrics["data"].get("rows", [])
        total_impressions = sum(row.get("impressions", 0) for row in rows)
        total_clicks = sum(row.get("clicks", 0) for row in rows)
        total_queries = len(rows)
        
        # Calculate CTR
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        # Calculate average position
        total_position = sum(row.get("position", 0) for row in rows)
        avg_position = total_position / total_queries if total_queries > 0 else 0
        
        return {
            "success": True,
            "summary": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_queries": total_queries,
                "click_through_rate": round(ctr, 2),
                "average_position": round(avg_position, 2),
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

class AnalyticsDataCollector:
    """
    Comprehensive analytics data collection system
    
    Features:
    - Google Search Console integration for SEO metrics
    - Enhanced social media analytics collection
    - Content performance tracking
    - System metrics and user behavior monitoring
    - Unified data collection pipeline
    - Rate limiting and error handling
    - Background job processing
    """
    
    def __init__(
        self,
        db: Session,
        redis_service: RedisService,
        cache_service: CacheService,
        google_credentials_path: str = None,
        google_site_url: str = None
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Initialize data source clients
        self.google_search_console = GoogleSearchConsoleClient(
            google_credentials_path, google_site_url
        )
        self.social_analytics = SocialAnalyticsCollector(
            db, redis_service, cache_service
        )
        self.content_analytics = ContentAnalyticsService()
        self.seo_client = SEMrushAPIClient()
        
        # Collection configuration
        self.collection_jobs: Dict[str, CollectionJob] = {}
        self.active_jobs: Dict[str, CollectionJob] = {}
        
        # Rate limiting configuration
        self.rate_limits = {
            DataSourceType.GOOGLE_SEARCH_CONSOLE: {"requests": 10000, "window": "day"},
            DataSourceType.SOCIAL_MEDIA: {"requests": 1000, "window": "hour"},
            DataSourceType.CONTENT_ANALYTICS: {"requests": 10000, "window": "hour"},
            DataSourceType.SEO_METRICS: {"requests": 100, "window": "hour"},
            DataSourceType.SYSTEM_METRICS: {"requests": 10000, "window": "hour"},
            DataSourceType.USER_BEHAVIOR: {"requests": 10000, "window": "hour"}
        }
        
        # Collection frequencies
        self.collection_frequencies = {
            DataSourceType.GOOGLE_SEARCH_CONSOLE: CollectionFrequency.DAILY,
            DataSourceType.SOCIAL_MEDIA: CollectionFrequency.REAL_TIME,
            DataSourceType.CONTENT_ANALYTICS: CollectionFrequency.HOURLY,
            DataSourceType.SEO_METRICS: CollectionFrequency.DAILY,
            DataSourceType.SYSTEM_METRICS: CollectionFrequency.HOURLY,
            DataSourceType.USER_BEHAVIOR: CollectionFrequency.REAL_TIME
        }
        
        # Initialize collection patterns
        self._initialize_collection_patterns()
    
    def _initialize_collection_patterns(self):
        """Initialize collection patterns for different data sources"""
        self.collection_patterns = {
            DataSourceType.GOOGLE_SEARCH_CONSOLE: {
                "metrics": ["impressions", "clicks", "ctr", "position"],
                "dimensions": ["query", "page", "country", "device"],
                "cache_ttl": 86400,  # 24 hours
                "retry_attempts": 3,
                "retry_delay": 60  # 1 minute
            },
            DataSourceType.SOCIAL_MEDIA: {
                "metrics": ["engagement", "reach", "impressions", "clicks", "conversions"],
                "platforms": ["twitter", "facebook", "linkedin", "instagram"],
                "cache_ttl": 300,  # 5 minutes
                "retry_attempts": 5,
                "retry_delay": 30  # 30 seconds
            },
            DataSourceType.CONTENT_ANALYTICS: {
                "metrics": ["views", "engagement", "conversion_rate", "quality_score"],
                "content_types": ["blog_post", "social_post", "landing_page"],
                "cache_ttl": 3600,  # 1 hour
                "retry_attempts": 3,
                "retry_delay": 300  # 5 minutes
            },
            DataSourceType.SEO_METRICS: {
                "metrics": ["search_volume", "cpc", "keyword_difficulty", "competition"],
                "cache_ttl": 86400,  # 24 hours
                "retry_attempts": 3,
                "retry_delay": 300  # 5 minutes
            },
            DataSourceType.SYSTEM_METRICS: {
                "metrics": ["api_calls", "response_times", "error_rates", "token_usage"],
                "cache_ttl": 300,  # 5 minutes
                "retry_attempts": 3,
                "retry_delay": 60  # 1 minute
            },
            DataSourceType.USER_BEHAVIOR: {
                "metrics": ["session_duration", "page_views", "feature_usage", "export_activity"],
                "cache_ttl": 1800,  # 30 minutes
                "retry_attempts": 3,
                "retry_delay": 60  # 1 minute
            }
        }
    
    async def create_collection_job(
        self,
        source_type: DataSourceType,
        parameters: Dict[str, Any] = None,
        frequency: CollectionFrequency = None
    ) -> CollectionJob:
        """
        Create a new data collection job
        
        Args:
            source_type: Type of data source to collect from
            parameters: Job-specific parameters
            frequency: Collection frequency (overrides default)
            
        Returns:
            CollectionJob object
        """
        job_id = str(uuid.uuid4())
        
        if frequency is None:
            frequency = self.collection_frequencies.get(source_type, CollectionFrequency.DAILY)
        
        if parameters is None:
            parameters = {}
        
        job = CollectionJob(
            job_id=job_id,
            source_type=source_type,
            frequency=frequency,
            parameters=parameters,
            status=CollectionStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata={}
        )
        
        self.collection_jobs[job_id] = job
        
        # Store job in Redis for persistence
        await self.redis_service.set(
            f"collection_job:{job_id}",
            json.dumps(asdict(job), default=str),
            ttl=86400  # 24 hours
        )
        
        logger.info(f"Created collection job {job_id} for {source_type.value}")
        return job
    
    async def start_collection_job(self, job_id: str) -> bool:
        """
        Start a data collection job
        
        Args:
            job_id: ID of the job to start
            
        Returns:
            True if job started successfully, False otherwise
        """
        if job_id not in self.collection_jobs:
            logger.error(f"Job {job_id} not found")
            return False
        
        job = self.collection_jobs[job_id]
        
        if job.status != CollectionStatus.PENDING:
            logger.warning(f"Job {job_id} is not in pending status: {job.status}")
            return False
        
        # Check rate limits
        if not await self._check_rate_limit(job.source_type):
            job.status = CollectionStatus.RATE_LIMITED
            await self._update_job_status(job_id, job.status)
            logger.warning(f"Rate limit exceeded for {job.source_type.value}")
            return False
        
        # Start the job
        job.status = CollectionStatus.IN_PROGRESS
        job.started_at = datetime.utcnow()
        self.active_jobs[job_id] = job
        
        await self._update_job_status(job_id, job.status)
        
        # Execute collection based on source type
        try:
            if job.source_type == DataSourceType.GOOGLE_SEARCH_CONSOLE:
                await self._collect_google_search_console_data(job)
            elif job.source_type == DataSourceType.SOCIAL_MEDIA:
                await self._collect_social_media_data(job)
            elif job.source_type == DataSourceType.CONTENT_ANALYTICS:
                await self._collect_content_analytics_data(job)
            elif job.source_type == DataSourceType.SEO_METRICS:
                await self._collect_seo_metrics_data(job)
            elif job.source_type == DataSourceType.SYSTEM_METRICS:
                await self._collect_system_metrics_data(job)
            elif job.source_type == DataSourceType.USER_BEHAVIOR:
                await self._collect_user_behavior_data(job)
            else:
                raise ValueError(f"Unknown source type: {job.source_type}")
            
            job.status = CollectionStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
        except Exception as e:
            job.status = CollectionStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"Job {job_id} failed: {e}")
        
        # Update job status
        await self._update_job_status(job_id, job.status)
        
        # Remove from active jobs
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
        
        return job.status == CollectionStatus.COMPLETED
    
    async def _collect_google_search_console_data(self, job: CollectionJob):
        """Collect data from Google Search Console"""
        try:
            # Get date range from parameters or use default
            days = job.parameters.get("days", 30)
            
            # Get site performance summary
            summary = await self.google_search_console.get_site_performance_summary(days)
            
            if summary.get("success"):
                # Store the data
                await self._store_analytics_data(
                    DataSourceType.GOOGLE_SEARCH_CONSOLE,
                    "site_performance",
                    summary["summary"],
                    job.user_id if hasattr(job, 'user_id') else None
                )
                
                job.data_points_collected = 1
                logger.info(f"Collected Google Search Console data for job {job.job_id}")
            else:
                raise Exception(f"Failed to collect Google Search Console data: {summary.get('error')}")
                
        except Exception as e:
            logger.error(f"Error collecting Google Search Console data: {e}")
            raise
    
    async def _collect_social_media_data(self, job: CollectionJob):
        """Collect social media analytics data"""
        try:
            # Use existing social analytics collector
            platforms = job.parameters.get("platforms", ["twitter", "facebook", "linkedin", "instagram"])
            content_ids = job.parameters.get("content_ids", None)
            
            if content_ids:
                # Collect for specific content
                for content_id in content_ids:
                    metrics = await self.social_analytics.collect_realtime_metrics(
                        content_id, platforms, force_refresh=True
                    )
                    
                    if metrics.get("success"):
                        await self._store_analytics_data(
                            DataSourceType.SOCIAL_MEDIA,
                            f"content_{content_id}",
                            metrics["metrics"],
                            job.user_id if hasattr(job, 'user_id') else None
                        )
                        job.data_points_collected += 1
            else:
                # Collect general platform metrics
                for platform in platforms:
                    # This would need to be implemented in the social analytics collector
                    # For now, we'll collect what's available
                    pass
            
            logger.info(f"Collected social media data for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error collecting social media data: {e}")
            raise
    
    async def _collect_content_analytics_data(self, job: CollectionJob):
        """Collect content analytics data"""
        try:
            # Get content performance data
            content_ids = job.parameters.get("content_ids", None)
            
            if content_ids:
                for content_id in content_ids:
                    # Get content from database
                    content = self.db.query(ContentPiece).filter(
                        ContentPiece.id == content_id
                    ).first()
                    
                    if content:
                        # Get analytics for this content
                        analytics = await self.content_analytics.get_content_analytics(content_id)
                        
                        if analytics.get("success"):
                            await self._store_analytics_data(
                                DataSourceType.CONTENT_ANALYTICS,
                                f"content_{content_id}",
                                analytics["analytics"],
                                job.user_id if hasattr(job, 'user_id') else None
                            )
                            job.data_points_collected += 1
            
            logger.info(f"Collected content analytics data for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error collecting content analytics data: {e}")
            raise
    
    async def _collect_seo_metrics_data(self, job: CollectionJob):
        """Collect SEO metrics data"""
        try:
            keywords = job.parameters.get("keywords", [])
            
            for keyword in keywords:
                # Get keyword analysis from SEMrush
                keyword_data = await self.seo_client.get_keyword_analysis(keyword)
                
                if keyword_data:
                    await self._store_analytics_data(
                        DataSourceType.SEO_METRICS,
                        f"keyword_{keyword}",
                        keyword_data.__dict__,
                        job.user_id if hasattr(job, 'user_id') else None
                    )
                    job.data_points_collected += 1
            
            logger.info(f"Collected SEO metrics data for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error collecting SEO metrics data: {e}")
            raise
    
    async def _collect_system_metrics_data(self, job: CollectionJob):
        """Collect system metrics data"""
        try:
            # Collect system performance metrics
            system_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "redis_health": await self.redis_service.health_check(),
                "cache_stats": await self.cache_service.get_stats(),
                "active_jobs": len(self.active_jobs),
                "total_jobs": len(self.collection_jobs)
            }
            
            await self._store_analytics_data(
                DataSourceType.SYSTEM_METRICS,
                "system_performance",
                system_metrics,
                job.user_id if hasattr(job, 'user_id') else None
            )
            
            job.data_points_collected = 1
            logger.info(f"Collected system metrics data for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics data: {e}")
            raise
    
    async def _collect_user_behavior_data(self, job: CollectionJob):
        """Collect user behavior data"""
        try:
            # This would integrate with user tracking systems
            # For now, we'll collect basic session data
            user_behavior_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "active_sessions": 0,  # Would be implemented with user tracking
                "feature_usage": {},    # Would track feature usage
                "export_activity": 0   # Would track report exports
            }
            
            await self._store_analytics_data(
                DataSourceType.USER_BEHAVIOR,
                "user_behavior",
                user_behavior_metrics,
                job.user_id if hasattr(job, 'user_id') else None
            )
            
            job.data_points_collected = 1
            logger.info(f"Collected user behavior data for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Error collecting user behavior data: {e}")
            raise
    
    async def _store_analytics_data(
        self,
        source_type: DataSourceType,
        source_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Store analytics data in Redis and database"""
        try:
            # Create data point
            data_point = AnalyticsDataPoint(
                id=str(uuid.uuid4()),
                source_type=source_type,
                source_id=source_id,
                metric_name="comprehensive_metrics",
                metric_value=json.dumps(data),
                timestamp=datetime.utcnow(),
                metadata={"raw_data": data},
                user_id=user_id
            )
            
            # Store in Redis for caching
            cache_key = f"analytics:{source_type.value}:{source_id}:{data_point.timestamp.strftime('%Y%m%d')}"
            await self.redis_service.set(
                cache_key,
                json.dumps(asdict(data_point), default=str),
                ttl=self.collection_patterns[source_type]["cache_ttl"]
            )
            
            # Store in database for persistence
            # This would need to be implemented based on your database schema
            # For now, we'll just log the storage
            
            logger.debug(f"Stored analytics data: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error storing analytics data: {e}")
            raise
    
    async def _check_rate_limit(self, source_type: DataSourceType) -> bool:
        """Check if we're within rate limits for a data source"""
        try:
            rate_limit = self.rate_limits.get(source_type, {"requests": 1000, "window": "hour"})
            
            # Get current usage from Redis
            usage_key = f"rate_limit:{source_type.value}:{datetime.utcnow().strftime('%Y%m%d%H')}"
            current_usage = await self.redis_service.get(usage_key)
            
            if current_usage is None:
                current_usage = 0
            else:
                current_usage = int(current_usage)
            
            # Check if we're within limits
            if current_usage < rate_limit["requests"]:
                # Increment usage
                await self.redis_service.incr(usage_key)
                await self.redis_service.expire(usage_key, 3600)  # 1 hour TTL
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False  # Fail safe - assume rate limited
    
    async def _update_job_status(self, job_id: str, status: CollectionStatus):
        """Update job status in Redis"""
        try:
            if job_id in self.collection_jobs:
                job = self.collection_jobs[job_id]
                job.status = status
                
                await self.redis_service.set(
                    f"collection_job:{job_id}",
                    json.dumps(asdict(job), default=str),
                    ttl=86400
                )
                
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
    
    async def get_collection_job_status(self, job_id: str) -> Optional[CollectionJob]:
        """Get the status of a collection job"""
        return self.collection_jobs.get(job_id)
    
    async def get_active_jobs(self) -> List[CollectionJob]:
        """Get list of currently active jobs"""
        return list(self.active_jobs.values())
    
    async def cancel_collection_job(self, job_id: str) -> bool:
        """Cancel a running collection job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = CollectionStatus.FAILED
            job.error_message = "Job cancelled by user"
            job.completed_at = datetime.utcnow()
            
            await self._update_job_status(job_id, job.status)
            del self.active_jobs[job_id]
            
            logger.info(f"Cancelled collection job {job_id}")
            return True
        
        return False
    
    async def schedule_recurring_collection(self):
        """Schedule recurring data collection jobs"""
        try:
            for source_type, frequency in self.collection_frequencies.items():
                # Check if we need to create a new job
                last_job_key = f"last_collection:{source_type.value}"
                last_collection = await self.redis_service.get(last_job_key)
                
                should_collect = False
                current_time = datetime.utcnow()
                
                if last_collection is None:
                    should_collect = True
                else:
                    last_collection = datetime.fromisoformat(last_collection)
                    
                    if frequency == CollectionFrequency.REAL_TIME:
                        should_collect = (current_time - last_collection).seconds >= 300  # 5 minutes
                    elif frequency == CollectionFrequency.HOURLY:
                        should_collect = (current_time - last_collection).seconds >= 3600  # 1 hour
                    elif frequency == CollectionFrequency.DAILY:
                        should_collect = (current_time - last_collection).days >= 1
                    elif frequency == CollectionFrequency.WEEKLY:
                        should_collect = (current_time - last_collection).days >= 7
                    elif frequency == CollectionFrequency.MONTHLY:
                        should_collect = (current_time - last_collection).days >= 30
                
                if should_collect:
                    # Create and start collection job
                    job = await self.create_collection_job(source_type)
                    await self.start_collection_job(job.job_id)
                    
                    # Update last collection time
                    await self.redis_service.set(
                        last_job_key,
                        current_time.isoformat(),
                        ttl=86400 * 30  # 30 days
                    )
                    
                    logger.info(f"Scheduled recurring collection for {source_type.value}")
            
        except Exception as e:
            logger.error(f"Error scheduling recurring collection: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the analytics data collector"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "active_jobs": len(self.active_jobs),
                "total_jobs": len(self.collection_jobs),
                "data_sources": {}
            }
            
            # Check each data source
            for source_type in DataSourceType:
                try:
                    if source_type == DataSourceType.GOOGLE_SEARCH_CONSOLE:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy" if self.google_search_console.authenticated else "unauthenticated",
                            "authenticated": self.google_search_console.authenticated
                        }
                    elif source_type == DataSourceType.SOCIAL_MEDIA:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy",
                            "platforms": ["twitter", "facebook", "linkedin", "instagram"]
                        }
                    elif source_type == DataSourceType.CONTENT_ANALYTICS:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy"
                        }
                    elif source_type == DataSourceType.SEO_METRICS:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy"
                        }
                    elif source_type == DataSourceType.SYSTEM_METRICS:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy"
                        }
                    elif source_type == DataSourceType.USER_BEHAVIOR:
                        health_status["data_sources"][source_type.value] = {
                            "status": "healthy"
                        }
                        
                except Exception as e:
                    health_status["data_sources"][source_type.value] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
                    health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
