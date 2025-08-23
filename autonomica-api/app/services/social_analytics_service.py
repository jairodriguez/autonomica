"""
Social Analytics Service
Main service that orchestrates analytics collection and processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json
import uuid

from sqlalchemy.orm import Session

from app.services.social_analytics_collector import SocialAnalyticsCollector
from app.services.analytics_data_processor import AnalyticsDataProcessor
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class SocialAnalyticsService:
    """
    Main social analytics service that orchestrates:
    - Analytics data collection from social platforms
    - Data processing and insight generation
    - Automated collection scheduling
    - Performance monitoring and reporting
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Initialize sub-services
        self.collector = SocialAnalyticsCollector(db, redis_service, cache_service)
        self.processor = AnalyticsDataProcessor(db, redis_service, cache_service)
        
        # Service configuration
        self.auto_collection_enabled = True
        self.collection_interval = 300  # 5 minutes
        self.insight_generation_interval = 3600  # 1 hour
        self.data_retention_days = 90
        
        # Service state
        self.is_running = False
        self.collection_task = None
        self.insight_task = None
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the analytics service"""
        try:
            logger.info("Initializing Social Analytics Service")
            
            # Start background tasks if auto-collection is enabled
            if self.auto_collection_enabled:
                self.start_background_tasks()
            
            logger.info("Social Analytics Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Social Analytics Service: {e}")
    
    async def start_background_tasks(self):
        """Start background collection and processing tasks"""
        try:
            if not self.is_running:
                self.is_running = True
                
                # Start metrics collection task
                self.collection_task = asyncio.create_task(self._run_metrics_collection_loop())
                
                # Start insight generation task
                self.insight_task = asyncio.create_task(self._run_insight_generation_loop())
                
                logger.info("Background analytics tasks started")
            else:
                logger.info("Background tasks already running")
                
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
            self.is_running = False
    
    async def stop_background_tasks(self):
        """Stop background collection and processing tasks"""
        try:
            if self.is_running:
                self.is_running = False
                
                # Cancel tasks
                if self.collection_task:
                    self.collection_task.cancel()
                    try:
                        await self.collection_task
                    except asyncio.CancelledError:
                        pass
                
                if self.insight_task:
                    self.insight_task.cancel()
                    try:
                        await self.insight_task
                    except asyncio.CancelledError:
                        pass
                
                logger.info("Background analytics tasks stopped")
            else:
                logger.info("Background tasks not running")
                
        except Exception as e:
            logger.error(f"Failed to stop background tasks: {e}")
    
    async def _run_metrics_collection_loop(self):
        """Background loop for collecting metrics from social platforms"""
        try:
            while self.is_running:
                try:
                    # Get content that needs metrics collection
                    content_to_collect = await self._get_content_for_collection()
                    
                    for content_id in content_to_collect:
                        try:
                            # Start real-time metrics collection
                            result = await self.collector.collect_realtime_metrics(content_id)
                            
                            if result["success"]:
                                logger.info(f"Started metrics collection for content {content_id}")
                            else:
                                logger.warning(f"Failed to start metrics collection for content {content_id}: {result.get('error')}")
                                
                        except Exception as e:
                            logger.error(f"Error collecting metrics for content {content_id}: {e}")
                    
                    # Wait for next collection cycle
                    await asyncio.sleep(self.collection_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in metrics collection loop: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
                    
        except Exception as e:
            logger.error(f"Metrics collection loop failed: {e}")
        finally:
            logger.info("Metrics collection loop stopped")
    
    async def _run_insight_generation_loop(self):
        """Background loop for generating insights from collected data"""
        try:
            while self.is_running:
                try:
                    # Get content that needs insight generation
                    content_for_insights = await self._get_content_for_insights()
                    
                    for content_id in content_for_insights:
                        try:
                            # Generate insights
                            result = await self.processor.process_content_analytics(
                                content_id,
                                analysis_period="7d",
                                include_insights=True,
                                include_recommendations=True
                            )
                            
                            if result["success"]:
                                logger.info(f"Generated insights for content {content_id}")
                            else:
                                logger.warning(f"Failed to generate insights for content {content_id}: {result.get('error')}")
                                
                        except Exception as e:
                            logger.error(f"Error generating insights for content {content_id}: {e}")
                    
                    # Wait for next insight generation cycle
                    await asyncio.sleep(self.insight_generation_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in insight generation loop: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
                    
        except Exception as e:
            logger.error(f"Insight generation loop failed: {e}")
        finally:
            logger.info("Insight generation loop stopped")
    
    async def _get_content_for_collection(self) -> List[int]:
        """Get content IDs that need metrics collection"""
        try:
            # Get published content that hasn't been collected recently
            from app.models.schema import ContentPiece, SocialPost, ContentStatus
            
            # Find content with published social posts
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.status == ContentStatus.PUBLISHED
            ).all()
            
            content_ids = set()
            current_time = datetime.utcnow()
            
            for post in social_posts:
                metrics = post.metrics or {}
                last_collected = metrics.get("last_collected")
                
                # Check if metrics need collection
                needs_collection = False
                
                if not last_collected:
                    needs_collection = True
                else:
                    try:
                        last_collected_time = datetime.fromisoformat(last_collected)
                        hours_since_collection = (current_time - last_collected_time).total_seconds() / 3600
                        
                        # Collect metrics if older than 6 hours
                        if hours_since_collection > 6:
                            needs_collection = True
                    except:
                        needs_collection = True
                
                if needs_collection:
                    content_ids.add(post.content_id)
            
            return list(content_ids)
            
        except Exception as e:
            logger.error(f"Failed to get content for collection: {e}")
            return []
    
    async def _get_content_for_insights(self) -> List[int]:
        """Get content IDs that need insight generation"""
        try:
            # Get content that has metrics but no recent insights
            from app.models.schema import ContentPiece, SocialPost, ContentStatus
            
            # Find content with published social posts and metrics
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.status == ContentStatus.PUBLISHED,
                SocialPost.metrics.isnot(None)
            ).all()
            
            content_ids = set()
            current_time = datetime.utcnow()
            
            for post in social_posts:
                metrics = post.metrics or {}
                last_collected = metrics.get("last_collected")
                
                # Check if insights need generation
                needs_insights = False
                
                if last_collected:
                    try:
                        last_collected_time = datetime.fromisoformat(last_collected)
                        hours_since_collection = (current_time - last_collected_time).total_seconds() / 3600
                        
                        # Generate insights if metrics are fresh (less than 24 hours old)
                        if hours_since_collection < 24:
                            needs_insights = True
                    except:
                        needs_insights = False
                
                if needs_insights:
                    content_ids.add(post.content_id)
            
            return list(content_ids)
            
        except Exception as e:
            logger.error(f"Failed to get content for insights: {e}")
            return []
    
    async def collect_metrics_for_content(
        self,
        content_id: int,
        platforms: List[str] = None,
        collection_type: str = "realtime",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Collect metrics for specific content
        
        Args:
            content_id: ID of the content piece
            platforms: Specific platforms to collect from (None for all)
            collection_type: Type of collection ("realtime" or "historical")
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            Dict containing collection results
        """
        try:
            if collection_type == "realtime":
                return await self.collector.collect_realtime_metrics(
                    content_id, platforms, force_refresh
                )
            elif collection_type == "historical":
                # For historical collection, we need date range
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=7)  # Default to 7 days
                
                return await self.collector.collect_historical_metrics(
                    content_id, start_date, end_date, platforms
                )
            else:
                return {
                    "success": False,
                    "error": f"Invalid collection type: {collection_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to collect metrics for content {content_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_analytics_for_content(
        self,
        content_id: int,
        analysis_period: str = "7d",
        include_insights: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for specific content
        
        Args:
            content_id: ID of the content piece
            analysis_period: Analysis period (e.g., "7d", "30d", "90d")
            include_insights: Whether to include insights
            include_recommendations: Whether to include recommendations
            
        Returns:
            Dict containing analytics data
        """
        try:
            return await self.processor.process_content_analytics(
                content_id,
                analysis_period,
                include_insights,
                include_recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to get analytics for content {content_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_collection_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a metrics collection job"""
        try:
            return await self.collector.get_collection_status(job_id)
        except Exception as e:
            logger.error(f"Failed to get collection status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_analytics_summary(self, content_id: int) -> Dict[str, Any]:
        """Get a summary of analytics data for content"""
        try:
            return await self.collector.get_analytics_summary(content_id)
        except Exception as e:
            logger.error(f"Failed to get analytics summary: {e}")
            return {"error": str(e)}
    
    async def get_insights_summary(self, content_id: int) -> Dict[str, Any]:
        """Get a summary of insights for content"""
        try:
            return await self.processor.get_insights_summary(content_id)
        except Exception as e:
            logger.error(f"Failed to get insights summary: {e}")
            return {"error": str(e)}
    
    async def get_platform_performance_comparison(
        self,
        content_ids: List[int],
        platforms: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare performance across multiple content pieces and platforms
        
        Args:
            content_ids: List of content IDs to compare
            platforms: Specific platforms to include (None for all)
            
        Returns:
            Dict containing comparison data
        """
        try:
            comparison_data = {
                "content_comparison": {},
                "platform_comparison": {},
                "overall_summary": {
                    "total_content": len(content_ids),
                    "total_platforms": 0,
                    "avg_performance_score": 0,
                    "best_performing_content": None,
                    "best_performing_platform": None
                }
            }
            
            platform_performance = defaultdict(list)
            content_performance = {}
            
            # Collect analytics for each content piece
            for content_id in content_ids:
                analytics = await self.get_analytics_for_content(
                    content_id,
                    analysis_period="7d",
                    include_insights=False,
                    include_recommendations=False
                )
                
                if analytics["success"]:
                    report = analytics["report"]
                    content_performance[content_id] = report["overall_score"]
                    
                    # Aggregate platform performance
                    for platform, data in report["platform_performance"].items():
                        if platforms is None or platform in platforms:
                            indicators = data.get("performance_indicators", {})
                            if "performance_score" in indicators:
                                platform_performance[platform].append(indicators["performance_score"])
            
            # Calculate platform averages
            for platform, scores in platform_performance.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    comparison_data["platform_comparison"][platform] = {
                        "average_score": round(avg_score, 2),
                        "content_count": len(scores),
                        "scores": scores
                    }
            
            # Calculate content comparison
            for content_id, score in content_performance.items():
                comparison_data["content_comparison"][content_id] = {
                    "performance_score": score,
                    "rank": len([s for s in content_performance.values() if s > score]) + 1
                }
            
            # Calculate overall summary
            if content_performance:
                comparison_data["overall_summary"]["avg_performance_score"] = round(
                    sum(content_performance.values()) / len(content_performance), 2
                )
                
                best_content = max(content_performance, key=content_performance.get)
                comparison_data["overall_summary"]["best_performing_content"] = {
                    "content_id": best_content,
                    "score": content_performance[best_content]
                }
            
            if platform_performance:
                comparison_data["overall_summary"]["total_platforms"] = len(platform_performance)
                
                # Find best performing platform
                platform_averages = {}
                for platform, scores in platform_performance.items():
                    platform_averages[platform] = sum(scores) / len(scores)
                
                best_platform = max(platform_averages, key=platform_averages.get)
                comparison_data["overall_summary"]["best_performing_platform"] = {
                    "platform": best_platform,
                    "average_score": round(platform_averages[best_platform], 2)
                }
            
            return {
                "success": True,
                "comparison": comparison_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get platform performance comparison: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_analytics_dashboard_data(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get data for the analytics dashboard
        
        Args:
            user_id: Optional user ID for user-specific data
            
        Returns:
            Dict containing dashboard data
        """
        try:
            from app.models.schema import ContentPiece, SocialPost, ContentStatus
            
            # Get overall statistics
            total_content = self.db.query(ContentPiece).count()
            published_content = self.db.query(ContentPiece).filter(
                ContentPiece.status == ContentStatus.PUBLISHED
            ).count()
            
            total_social_posts = self.db.query(SocialPost).filter(
                SocialPost.status == ContentStatus.PUBLISHED
            ).count()
            
            # Get recent analytics activity
            recent_collection_jobs = await self._get_recent_collection_jobs(5)
            recent_insights = await self._get_recent_insights(5)
            
            # Get platform distribution
            platform_distribution = await self._get_platform_distribution()
            
            dashboard_data = {
                "overview": {
                    "total_content": total_content,
                    "published_content": published_content,
                    "total_social_posts": total_social_posts,
                    "active_platforms": len(platform_distribution)
                },
                "recent_activity": {
                    "collection_jobs": recent_collection_jobs,
                    "insights": recent_insights
                },
                "platform_distribution": platform_distribution,
                "service_status": {
                    "auto_collection_enabled": self.auto_collection_enabled,
                    "background_tasks_running": self.is_running,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
            return {
                "success": True,
                "dashboard_data": dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_recent_collection_jobs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent collection jobs"""
        try:
            # This would typically query a jobs table
            # For now, return placeholder data
            return [
                {
                    "id": f"job_{i}",
                    "content_id": 100 + i,
                    "status": "completed",
                    "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                    "platforms": ["twitter", "facebook"]
                }
                for i in range(limit)
            ]
        except Exception as e:
            logger.error(f"Failed to get recent collection jobs: {e}")
            return []
    
    async def _get_recent_insights(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent insights"""
        try:
            # This would typically query an insights table
            # For now, return placeholder data
            return [
                {
                    "id": f"insight_{i}",
                    "content_id": 100 + i,
                    "type": "performance",
                    "title": f"Sample Insight {i+1}",
                    "confidence": 0.8 + (i * 0.05),
                    "created_at": (datetime.utcnow() - timedelta(hours=i*2)).isoformat()
                }
                for i in range(limit)
            ]
        except Exception as e:
            logger.error(f"Failed to get recent insights: {e}")
            return []
    
    async def _get_platform_distribution(self) -> Dict[str, int]:
        """Get distribution of content across platforms"""
        try:
            from app.models.schema import SocialPost, ContentStatus
            
            platform_counts = {}
            social_posts = self.db.query(SocialPost).filter(
                SocialPost.status == ContentStatus.PUBLISHED
            ).all()
            
            for post in social_posts:
                platform = post.platform
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
            
            return platform_counts
            
        except Exception as e:
            logger.error(f"Failed to get platform distribution: {e}")
            return {}
    
    async def cleanup_old_data(self, max_age_days: int = None) -> Dict[str, Any]:
        """
        Clean up old analytics data
        
        Args:
            max_age_days: Maximum age of data to keep (uses service default if None)
            
        Returns:
            Dict containing cleanup results
        """
        try:
            max_age = max_age_days or self.data_retention_days
            cutoff_date = datetime.utcnow() - timedelta(days=max_age)
            
            cleanup_results = {
                "old_collection_jobs": 0,
                "old_insights": 0,
                "old_cache_data": 0,
                "total_cleaned": 0
            }
            
            # Clean up old collection jobs
            cleanup_results["old_collection_jobs"] = await self.collector.cleanup_old_jobs(
                max_age_hours=max_age * 24
            )
            
            # Clean up old cache data
            # This would typically involve cleaning up old Redis keys and cache entries
            cleanup_results["old_cache_data"] = 0  # Placeholder
            
            # Calculate total
            cleanup_results["total_cleaned"] = sum([
                cleanup_results["old_collection_jobs"],
                cleanup_results["old_insights"],
                cleanup_results["old_cache_data"]
            ])
            
            logger.info(f"Cleaned up {cleanup_results['total_cleaned']} old analytics data items")
            
            return {
                "success": True,
                "cleanup_results": cleanup_results
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get the health status of the analytics service"""
        try:
            health_status = {
                "service": "Social Analytics Service",
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "collector": "operational",
                    "processor": "operational",
                    "background_tasks": "operational" if self.is_running else "stopped"
                },
                "configuration": {
                    "auto_collection_enabled": self.auto_collection_enabled,
                    "collection_interval": self.collection_interval,
                    "insight_generation_interval": self.insight_generation_interval,
                    "data_retention_days": self.data_retention_days
                },
                "metrics": {
                    "active_collection_jobs": len(self.collector.active_collection_jobs),
                    "background_tasks_running": self.is_running
                }
            }
            
            # Check Redis connection
            try:
                redis_health = await self.redis_service.health_check()
                health_status["components"]["redis"] = redis_health["status"]
            except Exception as e:
                health_status["components"]["redis"] = "error"
                health_status["status"] = "degraded"
            
            # Check cache service
            try:
                cache_stats = await self.cache_service.get_cache_stats()
                health_status["components"]["cache"] = "operational"
                health_status["metrics"]["cache_entries"] = cache_stats.get("memory_cache_size", 0)
            except Exception as e:
                health_status["components"]["cache"] = "error"
                health_status["status"] = "degraded"
            
            # Determine overall status
            if any(status == "error" for status in health_status["components"].values()):
                health_status["status"] = "degraded"
            elif any(status == "stopped" for status in health_status["components"].values()):
                health_status["status"] = "warning"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get service health: {e}")
            return {
                "service": "Social Analytics Service",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }




