"""
Analytics Data Processor
Processes collected analytics data and provides insights and reporting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import statistics
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.schema import SocialPost, ContentPiece, ContentStatus
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class InsightType(Enum):
    """Types of insights that can be generated"""
    PERFORMANCE = "performance"
    ENGAGEMENT = "engagement"
    REACH = "reach"
    TREND = "trend"
    COMPARISON = "comparison"
    OPTIMIZATION = "optimization"
    ANOMALY = "anomaly"

class MetricCategory(Enum):
    """Categories of metrics"""
    ENGAGEMENT = "engagement"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    CONVERSIONS = "conversions"
    GROWTH = "growth"

@dataclass
class AnalyticsInsight:
    """Individual analytics insight"""
    id: str
    insight_type: InsightType
    metric_category: MetricCategory
    title: str
    description: str
    value: Union[int, float, str]
    previous_value: Optional[Union[int, float, str]] = None
    change_percentage: Optional[float] = None
    confidence: float = 0.0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    content_id: int
    report_period: str
    generated_at: datetime
    overall_score: float
    platform_performance: Dict[str, Dict[str, Any]]
    insights: List[AnalyticsInsight]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]

class AnalyticsDataProcessor:
    """
    Processes collected analytics data and generates insights
    
    Features:
    - Performance analysis and scoring
    - Trend detection and analysis
    - Cross-platform comparison
    - Optimization recommendations
    - Anomaly detection
    - Automated reporting
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Processing configuration
        self.insight_confidence_threshold = 0.7
        self.trend_analysis_window = 7  # days
        self.performance_weights = {
            "engagement_rate": 0.3,
            "reach": 0.25,
            "impressions": 0.2,
            "growth": 0.15,
            "consistency": 0.1
        }
        
        # Initialize processing patterns
        self._initialize_processing_patterns()
    
    def _initialize_processing_patterns(self):
        """Initialize processing patterns for different types of analysis"""
        self.processing_patterns = {
            "performance_scoring": {
                "excellent_threshold": 0.8,
                "good_threshold": 0.6,
                "average_threshold": 0.4,
                "poor_threshold": 0.2
            },
            "trend_analysis": {
                "positive_threshold": 0.1,  # 10% increase
                "negative_threshold": -0.1,  # 10% decrease
                "stable_threshold": 0.05     # 5% variation
            },
            "anomaly_detection": {
                "std_dev_threshold": 2.0,  # 2 standard deviations
                "min_data_points": 5
            }
        }
    
    async def process_content_analytics(
        self,
        content_id: int,
        analysis_period: str = "7d",
        include_insights: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """
        Process analytics data for specific content
        
        Args:
            content_id: ID of the content piece
            analysis_period: Analysis period (e.g., "7d", "30d", "90d")
            include_insights: Whether to generate insights
            include_recommendations: Whether to generate recommendations
            
        Returns:
            Dict containing processed analytics data
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
            
            # Calculate analysis period
            end_date = datetime.utcnow()
            start_date = self._calculate_start_date(analysis_period, end_date)
            
            # Process analytics data
            processed_data = await self._process_content_data(
                content, social_posts, start_date, end_date
            )
            
            # Generate insights if requested
            insights = []
            if include_insights:
                insights = await self._generate_content_insights(
                    content, social_posts, processed_data, start_date, end_date
                )
            
            # Generate recommendations if requested
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_recommendations(
                    content, social_posts, processed_data, insights
                )
            
            # Calculate overall performance score
            performance_score = self._calculate_performance_score(processed_data)
            
            # Create performance report
            report = PerformanceReport(
                content_id=content_id,
                report_period=analysis_period,
                generated_at=datetime.utcnow(),
                overall_score=performance_score,
                platform_performance=processed_data["platform_performance"],
                insights=insights,
                recommendations=recommendations,
                metrics_summary=processed_data["metrics_summary"]
            )
            
            # Cache the report
            cache_key = f"analytics_report:{content_id}:{analysis_period}"
            await self.cache_service.set(cache_key, json.dumps(asdict(report)), 3600)  # 1 hour TTL
            
            logger.info(f"Generated analytics report for content {content_id}")
            
            return {
                "success": True,
                "report": asdict(report)
            }
            
        except Exception as e:
            logger.error(f"Failed to process content analytics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_content_data(
        self,
        content: ContentPiece,
        social_posts: List[SocialPost],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Process raw content data into structured analytics"""
        try:
            processed_data = {
                "platform_performance": {},
                "metrics_summary": {
                    "total_posts": len(social_posts),
                    "platforms": list(set(post.platform for post in social_posts)),
                    "analysis_period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "days": (end_date - start_date).days
                    }
                }
            }
            
            # Process each platform's data
            for post in social_posts:
                platform = post.platform
                metrics = post.metrics or {}
                
                # Extract and process metrics
                platform_metrics = self._extract_platform_metrics(metrics)
                
                # Calculate performance indicators
                performance_indicators = self._calculate_performance_indicators(platform_metrics)
                
                # Store processed data
                processed_data["platform_performance"][platform] = {
                    "post_id": post.id,
                    "platform_post_id": metrics.get("platform_post_id", ""),
                    "publish_date": post.publish_date.isoformat() if post.publish_date else None,
                    "last_collected": metrics.get("last_collected"),
                    "raw_metrics": platform_metrics,
                    "performance_indicators": performance_indicators,
                    "data_quality": self._assess_data_quality(platform_metrics)
                }
            
            # Calculate cross-platform metrics
            processed_data["metrics_summary"].update(
                self._calculate_cross_platform_metrics(processed_data["platform_performance"])
            )
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Failed to process content data: {e}")
            raise
    
    def _extract_platform_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize platform metrics"""
        try:
            extracted = {}
            
            # Extract core metrics
            core_metrics = metrics.get("metrics", {})
            for key, value in core_metrics.items():
                if isinstance(value, (int, float)) and value >= 0:
                    extracted[key] = value
            
            # Extract metadata
            extracted["last_collected"] = metrics.get("last_collected")
            extracted["collection_job_id"] = metrics.get("collection_job_id")
            
            return extracted
            
        except Exception as e:
            logger.error(f"Failed to extract platform metrics: {e}")
            return {}
    
    def _calculate_performance_indicators(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance indicators from raw metrics"""
        try:
            indicators = {}
            
            # Engagement rate
            if "engagement_rate" in metrics:
                indicators["engagement_rate"] = metrics["engagement_rate"]
            elif "like_count" in metrics and "impression_count" in metrics:
                total_engagement = sum([
                    metrics.get("like_count", 0),
                    metrics.get("comment_count", 0),
                    metrics.get("share_count", 0),
                    metrics.get("retweet_count", 0)
                ])
                if metrics["impression_count"] > 0:
                    indicators["engagement_rate"] = (total_engagement / metrics["impression_count"]) * 100
                else:
                    indicators["engagement_rate"] = 0
            
            # Reach efficiency
            if "reach_count" in metrics and "impression_count" in metrics:
                if metrics["impression_count"] > 0:
                    indicators["reach_efficiency"] = (metrics["reach_count"] / metrics["impression_count"]) * 100
                else:
                    indicators["reach_efficiency"] = 0
            
            # Content performance score (0-100)
            score_components = []
            
            # Engagement component (40%)
            if "engagement_rate" in indicators:
                engagement_score = min(indicators["engagement_rate"] * 2, 40)  # Max 40 points
                score_components.append(engagement_score)
            
            # Reach component (30%)
            if "reach_count" in metrics:
                reach_score = min(metrics["reach_count"] / 1000, 30)  # Max 30 points
                score_components.append(reach_score)
            
            # Impressions component (20%)
            if "impression_count" in metrics:
                impression_score = min(metrics["impression_count"] / 10000, 20)  # Max 20 points
                score_components.append(impression_score)
            
            # Consistency component (10%)
            consistency_score = 10 if len(metrics) >= 5 else len(metrics) * 2  # Max 10 points
            score_components.append(consistency_score)
            
            indicators["performance_score"] = sum(score_components)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate performance indicators: {e}")
            return {"performance_score": 0}
    
    def _assess_data_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of collected metrics data"""
        try:
            quality_score = 0
            issues = []
            
            # Check data completeness
            required_metrics = ["like_count", "impression_count"]
            available_metrics = [k for k in required_metrics if k in metrics]
            completeness = len(available_metrics) / len(required_metrics)
            
            if completeness < 0.5:
                issues.append("Incomplete metrics data")
            elif completeness < 0.8:
                issues.append("Partially complete metrics data")
            
            # Check data freshness
            if "last_collected" in metrics:
                try:
                    last_collected = datetime.fromisoformat(metrics["last_collected"])
                    age_hours = (datetime.utcnow() - last_collected).total_seconds() / 3600
                    
                    if age_hours > 24:
                        issues.append("Data is more than 24 hours old")
                    elif age_hours > 6:
                        issues.append("Data is more than 6 hours old")
                    
                    freshness_score = max(0, 100 - (age_hours * 2))  # Decrease score with age
                except:
                    issues.append("Invalid timestamp format")
                    freshness_score = 0
            else:
                issues.append("No collection timestamp")
                freshness_score = 0
            
            # Calculate overall quality score
            quality_score = (completeness * 60) + (freshness_score * 0.4)
            
            return {
                "score": round(quality_score, 2),
                "completeness": round(completeness * 100, 2),
                "freshness_score": round(freshness_score, 2),
                "issues": issues,
                "grade": "A" if quality_score >= 90 else "B" if quality_score >= 80 else "C" if quality_score >= 70 else "D" if quality_score >= 60 else "F"
            }
            
        except Exception as e:
            logger.error(f"Failed to assess data quality: {e}")
            return {"score": 0, "grade": "F", "issues": ["Data quality assessment failed"]}
    
    def _calculate_cross_platform_metrics(self, platform_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics across all platforms"""
        try:
            cross_platform = {
                "total_engagement": 0,
                "total_reach": 0,
                "total_impressions": 0,
                "avg_engagement_rate": 0,
                "platform_count": len(platform_performance),
                "best_performing_platform": None,
                "worst_performing_platform": None
            }
            
            platform_scores = []
            
            for platform, data in platform_performance.items():
                metrics = data.get("raw_metrics", {})
                indicators = data.get("performance_indicators", {})
                
                # Aggregate metrics
                cross_platform["total_engagement"] += metrics.get("like_count", 0) + metrics.get("comment_count", 0) + metrics.get("share_count", 0)
                cross_platform["total_reach"] += metrics.get("reach_count", 0)
                cross_platform["total_impressions"] += metrics.get("impression_count", 0)
                
                # Track platform scores
                if "performance_score" in indicators:
                    platform_scores.append((platform, indicators["performance_score"]))
            
            # Calculate averages
            if platform_scores:
                cross_platform["avg_engagement_rate"] = sum(
                    data.get("performance_indicators", {}).get("engagement_rate", 0)
                    for data in platform_performance.values()
                ) / len(platform_scores)
                
                # Find best and worst performing platforms
                platform_scores.sort(key=lambda x: x[1], reverse=True)
                cross_platform["best_performing_platform"] = platform_scores[0][0]
                cross_platform["worst_performing_platform"] = platform_scores[-1][0]
            
            return cross_platform
            
        except Exception as e:
            logger.error(f"Failed to calculate cross-platform metrics: {e}")
            return {}
    
    async def _generate_content_insights(
        self,
        content: ContentPiece,
        social_posts: List[SocialPost],
        processed_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[AnalyticsInsight]:
        """Generate insights from processed analytics data"""
        try:
            insights = []
            
            # Performance insights
            performance_insights = self._generate_performance_insights(processed_data)
            insights.extend(performance_insights)
            
            # Engagement insights
            engagement_insights = self._generate_engagement_insights(processed_data)
            insights.extend(engagement_insights)
            
            # Trend insights
            trend_insights = await self._generate_trend_insights(content.id, start_date, end_date)
            insights.extend(trend_insights)
            
            # Comparison insights
            comparison_insights = self._generate_comparison_insights(processed_data)
            insights.extend(comparison_insights)
            
            # Optimization insights
            optimization_insights = self._generate_optimization_insights(processed_data)
            insights.extend(optimization_insights)
            
            # Filter insights by confidence
            filtered_insights = [
                insight for insight in insights 
                if insight.confidence >= self.insight_confidence_threshold
            ]
            
            # Sort by confidence and value
            filtered_insights.sort(key=lambda x: (x.confidence, x.value if isinstance(x.value, (int, float)) else 0), reverse=True)
            
            return filtered_insights[:10]  # Return top 10 insights
            
        except Exception as e:
            logger.error(f"Failed to generate content insights: {e}")
            return []
    
    def _generate_performance_insights(self, processed_data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Generate performance-related insights"""
        insights = []
        
        try:
            platform_performance = processed_data["platform_performance"]
            metrics_summary = processed_data["metrics_summary"]
            
            # Overall performance insight
            if "avg_engagement_rate" in metrics_summary:
                engagement_rate = metrics_summary["avg_engagement_rate"]
                
                if engagement_rate > 5.0:
                    insights.append(AnalyticsInsight(
                        id=f"perf_high_engagement_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.PERFORMANCE,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title="High Engagement Performance",
                        description=f"Content achieved an above-average engagement rate of {engagement_rate:.2f}%",
                        value=engagement_rate,
                        confidence=0.85,
                        timestamp=datetime.utcnow(),
                        metadata={"threshold": 5.0, "category": "above_average"}
                    ))
                elif engagement_rate < 1.0:
                    insights.append(AnalyticsInsight(
                        id=f"perf_low_engagement_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.PERFORMANCE,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title="Low Engagement Performance",
                        description=f"Content has below-average engagement rate of {engagement_rate:.2f}%",
                        value=engagement_rate,
                        confidence=0.80,
                        timestamp=datetime.utcnow(),
                        metadata={"threshold": 1.0, "category": "below_average"}
                    ))
            
            # Platform performance insights
            for platform, data in platform_performance.items():
                indicators = data.get("performance_indicators", {})
                
                if "performance_score" in indicators:
                    score = indicators["performance_score"]
                    
                    if score >= 80:
                        insights.append(AnalyticsInsight(
                            id=f"perf_excellent_{platform}_{datetime.utcnow().timestamp()}",
                            insight_type=InsightType.PERFORMANCE,
                            metric_category=MetricCategory.ENGAGEMENT,
                            title=f"Excellent Performance on {platform.title()}",
                            description=f"Content performed exceptionally well on {platform} with a score of {score:.1f}/100",
                            value=score,
                            confidence=0.90,
                            timestamp=datetime.utcnow(),
                            metadata={"platform": platform, "threshold": 80}
                        ))
            
        except Exception as e:
            logger.error(f"Failed to generate performance insights: {e}")
        
        return insights
    
    def _generate_engagement_insights(self, processed_data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Generate engagement-related insights"""
        insights = []
        
        try:
            platform_performance = processed_data["platform_performance"]
            
            # Find platform with highest engagement
            platform_engagement = {}
            for platform, data in platform_performance.items():
                indicators = data.get("performance_indicators", {})
                if "engagement_rate" in indicators:
                    platform_engagement[platform] = indicators["engagement_rate"]
            
            if platform_engagement:
                best_platform = max(platform_engagement, key=platform_engagement.get)
                best_rate = platform_engagement[best_platform]
                
                insights.append(AnalyticsInsight(
                    id=f"engage_best_platform_{datetime.utcnow().timestamp()}",
                    insight_type=InsightType.ENGAGEMENT,
                    metric_category=MetricCategory.ENGAGEMENT,
                    title=f"Best Engagement on {best_platform.title()}",
                    description=f"{best_platform.title()} achieved the highest engagement rate at {best_rate:.2f}%",
                    value=best_rate,
                    confidence=0.85,
                    timestamp=datetime.utcnow(),
                    metadata={"best_platform": best_platform, "all_rates": platform_engagement}
                ))
            
            # Engagement consistency across platforms
            if len(platform_engagement) > 1:
                rates = list(platform_engagement.values())
                variance = statistics.variance(rates) if len(rates) > 1 else 0
                
                if variance < 1.0:  # Low variance = consistent performance
                    insights.append(AnalyticsInsight(
                        id=f"engage_consistent_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.ENGAGEMENT,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title="Consistent Engagement Across Platforms",
                        description="Content maintains consistent engagement performance across all platforms",
                        value=round(statistics.mean(rates), 2),
                        confidence=0.80,
                        timestamp=datetime.utcnow(),
                        metadata={"variance": variance, "consistency": "high"}
                    ))
                elif variance > 5.0:  # High variance = inconsistent performance
                    insights.append(AnalyticsInsight(
                        id=f"engage_inconsistent_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.ENGAGEMENT,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title="Inconsistent Engagement Across Platforms",
                        description="Content shows significant engagement variation across platforms",
                        value=round(statistics.mean(rates), 2),
                        confidence=0.75,
                        timestamp=datetime.utcnow(),
                        metadata={"variance": variance, "consistency": "low"}
                    ))
            
        except Exception as e:
            logger.error(f"Failed to generate engagement insights: {e}")
        
        return insights
    
    async def _generate_trend_insights(
        self,
        content_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[AnalyticsInsight]:
        """Generate trend-related insights"""
        insights = []
        
        try:
            # This would typically analyze historical data over time
            # For now, we'll generate placeholder insights
            
            insights.append(AnalyticsInsight(
                id=f"trend_placeholder_{datetime.utcnow().timestamp()}",
                insight_type=InsightType.TREND,
                metric_category=MetricCategory.GROWTH,
                title="Trend Analysis Available",
                description="Historical trend analysis can be performed with sufficient data collection",
                value="trend_analysis",
                confidence=0.60,
                timestamp=datetime.utcnow(),
                metadata={"data_requirements": "historical_data", "analysis_window": "7+ days"}
            ))
            
        except Exception as e:
            logger.error(f"Failed to generate trend insights: {e}")
        
        return insights
    
    def _generate_comparison_insights(self, processed_data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Generate comparison-related insights"""
        insights = []
        
        try:
            platform_performance = processed_data["platform_performance"]
            
            if len(platform_performance) > 1:
                # Compare platforms
                platform_scores = []
                for platform, data in platform_performance.items():
                    indicators = data.get("performance_indicators", {})
                    if "performance_score" in indicators:
                        platform_scores.append((platform, indicators["performance_score"]))
                
                if platform_scores:
                    platform_scores.sort(key=lambda x: x[1], reverse=True)
                    best_platform, best_score = platform_scores[0]
                    worst_platform, worst_score = platform_scores[-1]
                    
                    score_difference = best_score - worst_score
                    
                    if score_difference > 30:
                        insights.append(AnalyticsInsight(
                            id=f"comp_significant_difference_{datetime.utcnow().timestamp()}",
                            insight_type=InsightType.COMPARISON,
                            metric_category=MetricCategory.ENGAGEMENT,
                            title="Significant Platform Performance Gap",
                            description=f"Performance varies significantly between {best_platform.title()} ({best_score:.1f}) and {worst_platform.title()} ({worst_score:.1f})",
                            value=score_difference,
                            confidence=0.85,
                            timestamp=datetime.utcnow(),
                            metadata={"best_platform": best_platform, "worst_platform": worst_platform, "gap": score_difference}
                        ))
            
        except Exception as e:
            logger.error(f"Failed to generate comparison insights: {e}")
        
        return insights
    
    def _generate_optimization_insights(self, processed_data: Dict[str, Any]) -> List[AnalyticsInsight]:
        """Generate optimization-related insights"""
        insights = []
        
        try:
            platform_performance = processed_data["platform_performance"]
            metrics_summary = processed_data["metrics_summary"]
            
            # Data quality insights
            for platform, data in platform_performance.items():
                data_quality = data.get("data_quality", {})
                
                if data_quality.get("score", 0) < 70:
                    insights.append(AnalyticsInsight(
                        id=f"opt_data_quality_{platform}_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.OPTIMIZATION,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title=f"Improve Data Quality on {platform.title()}",
                        description=f"Data quality score of {data_quality.get('score', 0)} indicates room for improvement",
                        value=data_quality.get("score", 0),
                        confidence=0.80,
                        timestamp=datetime.utcnow(),
                        metadata={"platform": platform, "issues": data_quality.get("issues", [])}
                    ))
            
            # Cross-platform optimization
            if metrics_summary.get("platform_count", 0) > 1:
                best_platform = metrics_summary.get("best_performing_platform")
                worst_platform = metrics_summary.get("worst_performing_platform")
                
                if best_platform and worst_platform:
                    insights.append(AnalyticsInsight(
                        id=f"opt_cross_platform_{datetime.utcnow().timestamp()}",
                        insight_type=InsightType.OPTIMIZATION,
                        metric_category=MetricCategory.ENGAGEMENT,
                        title="Cross-Platform Optimization Opportunity",
                        description=f"Learn from {best_platform.title()}'s success to improve {worst_platform.title()} performance",
                        value="optimization_opportunity",
                        confidence=0.75,
                        timestamp=datetime.utcnow(),
                        metadata={"best_platform": best_platform, "worst_platform": worst_platform}
                    ))
            
        except Exception as e:
            logger.error(f"Failed to generate optimization insights: {e}")
        
        return insights
    
    async def _generate_recommendations(
        self,
        content: ContentPiece,
        social_posts: List[SocialPost],
        processed_data: Dict[str, Any],
        insights: List[AnalyticsInsight]
    ) -> List[str]:
        """Generate actionable recommendations based on insights"""
        try:
            recommendations = []
            
            # Data quality recommendations
            for platform, data in processed_data["platform_performance"].items():
                data_quality = data.get("data_quality", {})
                if data_quality.get("score", 0) < 70:
                    recommendations.append(f"Improve data collection frequency for {platform.title()} to get more accurate insights")
            
            # Performance recommendations
            overall_score = self._calculate_performance_score(processed_data)
            if overall_score < 50:
                recommendations.append("Content performance is below average. Consider optimizing content format and timing")
            elif overall_score < 70:
                recommendations.append("Content performance is moderate. Focus on improving engagement and reach")
            
            # Platform-specific recommendations
            platform_performance = processed_data["platform_performance"]
            for platform, data in platform_performance.items():
                indicators = data.get("performance_indicators", {})
                
                if "engagement_rate" in indicators:
                    engagement_rate = indicators["engagement_rate"]
                    if engagement_rate < 1.0:
                        recommendations.append(f"Low engagement on {platform.title()}. Consider testing different content formats")
                    elif engagement_rate > 5.0:
                        recommendations.append(f"High engagement on {platform.title()}. Replicate successful strategies on other platforms")
            
            # Cross-platform recommendations
            if len(platform_performance) > 1:
                best_platform = processed_data["metrics_summary"].get("best_performing_platform")
                if best_platform:
                    recommendations.append(f"Study successful strategies from {best_platform.title()} and apply them to underperforming platforms")
            
            # Content optimization recommendations
            if content.type == "blog_post":
                recommendations.append("Blog posts typically perform well on LinkedIn. Consider cross-posting content there")
            elif content.type == "tweet":
                recommendations.append("Tweets work best on Twitter. Consider adapting content for other platforms")
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations at this time"]
    
    def _calculate_performance_score(self, processed_data: Dict[str, Any]) -> float:
        """Calculate overall performance score for content"""
        try:
            platform_performance = processed_data["platform_performance"]
            
            if not platform_performance:
                return 0.0
            
            # Calculate weighted score based on platform performance
            total_score = 0
            total_weight = 0
            
            for platform, data in platform_performance.items():
                indicators = data.get("performance_indicators", {})
                
                # Platform weight (equal distribution for now)
                platform_weight = 1.0 / len(platform_performance)
                
                # Performance score
                performance_score = indicators.get("performance_score", 0)
                
                # Data quality bonus/penalty
                data_quality = data.get("data_quality", {})
                quality_bonus = (data_quality.get("score", 50) - 50) / 100  # -0.5 to 0.5
                
                # Adjusted score
                adjusted_score = performance_score + (quality_bonus * 10)
                adjusted_score = max(0, min(100, adjusted_score))  # Clamp to 0-100
                
                total_score += adjusted_score * platform_weight
                total_weight += platform_weight
            
            if total_weight > 0:
                return round(total_score / total_weight, 2)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate performance score: {e}")
            return 0.0
    
    def _calculate_start_date(self, analysis_period: str, end_date: datetime) -> datetime:
        """Calculate start date based on analysis period"""
        try:
            if analysis_period.endswith("d"):
                days = int(analysis_period[:-1])
                return end_date - timedelta(days=days)
            elif analysis_period.endswith("w"):
                weeks = int(analysis_period[:-1])
                return end_date - timedelta(weeks=weeks)
            elif analysis_period.endswith("m"):
                months = int(analysis_period[:-1])
                # Approximate month calculation
                return end_date - timedelta(days=months * 30)
            else:
                # Default to 7 days
                return end_date - timedelta(days=7)
                
        except Exception as e:
            logger.error(f"Failed to calculate start date: {e}")
            return end_date - timedelta(days=7)
    
    async def get_insights_summary(self, content_id: int) -> Dict[str, Any]:
        """Get a summary of insights for content"""
        try:
            # Get cached insights if available
            cache_key = f"insights_summary:{content_id}"
            cached_summary = await self.cache_service.get(cache_key)
            
            if cached_summary:
                return json.loads(cached_summary)
            
            # Generate fresh summary
            summary = await self.process_content_analytics(
                content_id, 
                analysis_period="7d",
                include_insights=True,
                include_recommendations=True
            )
            
            if summary["success"]:
                # Cache the summary
                await self.cache_service.set(cache_key, json.dumps(summary), 1800)  # 30 minutes TTL
                return summary
            else:
                return {"error": summary.get("error", "Failed to generate insights")}
                
        except Exception as e:
            logger.error(f"Failed to get insights summary: {e}")
            return {"error": str(e)}




