import logging
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

from .content_types import ContentType, Platform, ContentFormat

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    REACH = "reach"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    WORKFLOW = "workflow"

class EngagementMetric(str, Enum):
    VIEWS = "views"
    LIKES = "likes"
    SHARES = "shares"
    COMMENTS = "comments"
    CLICKS = "clicks"
    TIME_SPENT = "time_spent"
    BOUNCE_RATE = "bounce_rate"

class ConversionMetric(str, Enum):
    SIGNUPS = "signups"
    PURCHASES = "purchases"
    DOWNLOADS = "downloads"
    SUBSCRIPTIONS = "subscriptions"
    LEAD_GENERATION = "lead_generation"

class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

@dataclass
class ContentMetric:
    content_id: str
    metric_type: MetricType
    metric_name: str
    value: float
    timestamp: datetime
    platform: Optional[Platform] = None
    audience_segment: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class ContentPerformance:
    content_id: str
    title: str
    content_type: ContentType
    platform: Platform
    total_views: int
    total_engagement: int
    conversion_rate: float
    quality_score: float
    performance_score: float
    created_at: datetime
    published_at: Optional[datetime] = None
    last_updated: datetime = None

@dataclass
class AnalyticsReport:
    report_id: str
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    generated_at: datetime
    metrics_summary: Dict[str, Any]
    top_performing_content: List[ContentPerformance]
    platform_breakdown: Dict[Platform, Dict[str, Any]]
    content_type_analysis: Dict[ContentType, Dict[str, Any]]
    trends: Dict[str, List[Dict[str, Any]]]
    recommendations: List[str]

@dataclass
class WorkflowAnalytics:
    total_content: int
    content_by_stage: Dict[str, int]
    average_review_time: float
    approval_rate: float
    content_velocity: float
    bottlenecks: List[str]
    efficiency_score: float

class ContentAnalyticsService:
    def __init__(self):
        self.metrics: List[ContentMetric] = []
        self.performance_data: Dict[str, ContentPerformance] = {}
        self.reports: List[AnalyticsReport] = []
        self.analytics_config = self._initialize_analytics_config()
        
    def _initialize_analytics_config(self) -> Dict[str, Any]:
        """Initialize analytics configuration and thresholds"""
        return {
            "engagement_thresholds": {
                "high": 0.8,
                "medium": 0.5,
                "low": 0.2
            },
            "conversion_thresholds": {
                "high": 0.1,
                "medium": 0.05,
                "low": 0.01
            },
            "quality_thresholds": {
                "excellent": 0.9,
                "good": 0.7,
                "fair": 0.5,
                "poor": 0.3
            },
            "reporting_intervals": {
                "daily": timedelta(days=1),
                "weekly": timedelta(weeks=1),
                "monthly": timedelta(days=30),
                "quarterly": timedelta(days=90),
                "yearly": timedelta(days=365)
            }
        }

    async def track_metric(self, content_id: str, metric_type: MetricType, 
                          metric_name: str, value: float, platform: Optional[Platform] = None,
                          audience_segment: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Track a new metric for content"""
        try:
            metric = ContentMetric(
                content_id=content_id,
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                timestamp=datetime.now(),
                platform=platform,
                audience_segment=audience_segment,
                metadata=metadata or {}
            )
            
            self.metrics.append(metric)
            await self._update_performance_data(content_id, metric)
            
            logger.info(f"Tracked metric {metric_name}={value} for content {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking metric: {e}")
            return False

    async def _update_performance_data(self, content_id: str, metric: ContentMetric):
        """Update performance data when new metrics are tracked"""
        if content_id not in self.performance_data:
            # Initialize performance data if it doesn't exist
            self.performance_data[content_id] = ContentPerformance(
                content_id=content_id,
                title="Unknown",
                content_type=ContentType.BLOG_POST,  # Default
                platform=Platform.WEBSITE,  # Default
                total_views=0,
                total_engagement=0,
                conversion_rate=0.0,
                quality_score=0.0,
                performance_score=0.0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
        
        performance = self.performance_data[content_id]
        
        # Update metrics based on type
        if metric.metric_type == MetricType.ENGAGEMENT:
            if metric.metric_name == EngagementMetric.VIEWS:
                performance.total_views += int(metric.value)
            elif metric.metric_name in [EngagementMetric.LIKES, EngagementMetric.SHARES, EngagementMetric.COMMENTS]:
                performance.total_engagement += int(metric.value)
        
        elif metric.metric_type == MetricType.CONVERSION:
            # Update conversion rate
            if performance.total_views > 0:
                performance.conversion_rate = metric.value / performance.total_views
        
        elif metric.metric_type == MetricType.QUALITY:
            performance.quality_score = metric.value
        
        performance.last_updated = datetime.now()
        
        # Recalculate performance score
        performance.performance_score = self._calculate_performance_score(performance)

    def _calculate_performance_score(self, performance: ContentPerformance) -> float:
        """Calculate overall performance score based on multiple metrics"""
        # Weighted scoring system
        weights = {
            "engagement": 0.3,
            "conversion": 0.3,
            "quality": 0.2,
            "reach": 0.2
        }
        
        # Normalize metrics to 0-1 scale
        engagement_score = min(performance.total_engagement / max(performance.total_views, 1), 1.0)
        conversion_score = min(performance.conversion_rate * 100, 1.0)  # Convert to percentage
        quality_score = performance.quality_score
        reach_score = min(performance.total_views / 1000, 1.0)  # Normalize to 1000 views
        
        # Calculate weighted score
        total_score = (
            engagement_score * weights["engagement"] +
            conversion_score * weights["conversion"] +
            quality_score * weights["quality"] +
            reach_score * weights["reach"]
        )
        
        return round(total_score, 3)

    async def get_content_performance(self, content_id: str) -> Optional[ContentPerformance]:
        """Get performance data for specific content"""
        return self.performance_data.get(content_id)

    async def get_performance_summary(self, content_ids: Optional[List[str]] = None, 
                                    platform: Optional[Platform] = None,
                                    content_type: Optional[ContentType] = None,
                                    date_from: Optional[datetime] = None,
                                    date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get performance summary for content"""
        try:
            # Filter performance data
            filtered_data = list(self.performance_data.values())
            
            if content_ids:
                filtered_data = [p for p in filtered_data if p.content_id in content_ids]
            
            if platform:
                filtered_data = [p for p in filtered_data if p.platform == platform]
            
            if content_type:
                filtered_data = [p for p in filtered_data if p.content_type == content_type]
            
            if date_from:
                filtered_data = [p for p in filtered_data if p.created_at >= date_from]
            
            if date_to:
                filtered_data = [p for p in filtered_data if p.created_at <= date_to]
            
            if not filtered_data:
                return {
                    "total_content": 0,
                    "average_performance": 0.0,
                    "top_performers": [],
                    "platform_breakdown": {},
                    "content_type_breakdown": {}
                }
            
            # Calculate summary statistics
            total_content = len(filtered_data)
            performance_scores = [p.performance_score for p in filtered_data]
            average_performance = statistics.mean(performance_scores) if performance_scores else 0.0
            
            # Top performers
            top_performers = sorted(filtered_data, key=lambda x: x.performance_score, reverse=True)[:10]
            
            # Platform breakdown
            platform_breakdown = defaultdict(lambda: {"count": 0, "avg_performance": 0.0})
            for p in filtered_data:
                platform_breakdown[p.platform]["count"] += 1
                platform_breakdown[p.platform]["avg_performance"] += p.performance_score
            
            for platform in platform_breakdown:
                count = platform_breakdown[platform]["count"]
                platform_breakdown[platform]["avg_performance"] /= count
            
            # Content type breakdown
            content_type_breakdown = defaultdict(lambda: {"count": 0, "avg_performance": 0.0})
            for p in filtered_data:
                content_type_breakdown[p.content_type]["count"] += 1
                content_type_breakdown[p.content_type]["avg_performance"] += p.performance_score
            
            for content_type in content_type_breakdown:
                count = content_type_breakdown[content_type]["count"]
                content_type_breakdown[content_type]["avg_performance"] /= count
            
            return {
                "total_content": total_content,
                "average_performance": round(average_performance, 3),
                "top_performers": [asdict(p) for p in top_performers],
                "platform_breakdown": dict(platform_breakdown),
                "content_type_breakdown": dict(content_type_breakdown),
                "date_range": {
                    "from": date_from.isoformat() if date_from else None,
                    "to": date_to.isoformat() if date_to else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    async def generate_report(self, report_type: ReportType, start_date: datetime, 
                            end_date: datetime, include_recommendations: bool = True) -> AnalyticsReport:
        """Generate comprehensive analytics report"""
        try:
            report_id = f"report_{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
            # Get performance summary for the date range
            performance_summary = await self.get_performance_summary(
                date_from=start_date,
                date_to=end_date
            )
            
            # Get top performing content
            top_performing_content = await self._get_top_performing_content(start_date, end_date)
            
            # Platform breakdown
            platform_breakdown = await self._analyze_platform_performance(start_date, end_date)
            
            # Content type analysis
            content_type_analysis = await self._analyze_content_type_performance(start_date, end_date)
            
            # Trend analysis
            trends = await self._analyze_trends(start_date, end_date)
            
            # Generate recommendations
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_recommendations(performance_summary, trends)
            
            report = AnalyticsReport(
                report_id=report_id,
                report_type=report_type,
                start_date=start_date,
                end_date=end_date,
                generated_at=datetime.now(),
                metrics_summary=performance_summary,
                top_performing_content=top_performing_content,
                platform_breakdown=platform_breakdown,
                content_type_analysis=content_type_analysis,
                trends=trends,
                recommendations=recommendations
            )
            
            self.reports.append(report)
            logger.info(f"Generated report {report_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    async def _get_top_performing_content(self, start_date: datetime, end_date: datetime) -> List[ContentPerformance]:
        """Get top performing content for a date range"""
        filtered_data = [
            p for p in self.performance_data.values()
            if start_date <= p.created_at <= end_date
        ]
        
        # Sort by performance score and return top 20
        return sorted(filtered_data, key=lambda x: x.performance_score, reverse=True)[:20]

    async def _analyze_platform_performance(self, start_date: datetime, end_date: datetime) -> Dict[Platform, Dict[str, Any]]:
        """Analyze performance by platform"""
        platform_data = defaultdict(lambda: {
            "total_content": 0,
            "total_views": 0,
            "total_engagement": 0,
            "avg_performance": 0.0,
            "best_content_type": None
        })
        
        filtered_data = [
            p for p in self.performance_data.values()
            if start_date <= p.created_at <= end_date
        ]
        
        for performance in filtered_data:
            platform = performance.platform
            platform_data[platform]["total_content"] += 1
            platform_data[platform]["total_views"] += performance.total_views
            platform_data[platform]["total_engagement"] += performance.total_engagement
            platform_data[platform]["avg_performance"] += performance.performance_score
        
        # Calculate averages and find best content types
        for platform in platform_data:
            count = platform_data[platform]["total_content"]
            if count > 0:
                platform_data[platform]["avg_performance"] /= count
                
                # Find best performing content type for this platform
                platform_content = [p for p in filtered_data if p.platform == platform]
                if platform_content:
                    content_type_performance = defaultdict(list)
                    for p in platform_content:
                        content_type_performance[p.content_type].append(p.performance_score)
                    
                    best_content_type = max(content_type_performance.items(), 
                                         key=lambda x: statistics.mean(x[1]))[0]
                    platform_data[platform]["best_content_type"] = best_content_type
        
        return dict(platform_data)

    async def _analyze_content_type_performance(self, start_date: datetime, end_date: datetime) -> Dict[ContentType, Dict[str, Any]]:
        """Analyze performance by content type"""
        content_type_data = defaultdict(lambda: {
            "total_content": 0,
            "total_views": 0,
            "total_engagement": 0,
            "avg_performance": 0.0,
            "best_platform": None,
            "engagement_rate": 0.0,
            "conversion_rate": 0.0
        })
        
        filtered_data = [
            p for p in self.performance_data.values()
            if start_date <= p.created_at <= end_date
        ]
        
        for performance in filtered_data:
            content_type = performance.content_type
            content_type_data[content_type]["total_content"] += 1
            content_type_data[content_type]["total_views"] += performance.total_views
            content_type_data[content_type]["total_engagement"] += performance.total_engagement
            content_type_data[content_type]["avg_performance"] += performance.performance_score
        
        # Calculate averages and metrics
        for content_type in content_type_data:
            count = content_type_data[content_type]["total_content"]
            if count > 0:
                content_type_data[content_type]["avg_performance"] /= count
                
                # Calculate engagement rate
                total_views = content_type_data[content_type]["total_views"]
                if total_views > 0:
                    content_type_data[content_type]["engagement_rate"] = (
                        content_type_data[content_type]["total_engagement"] / total_views
                    )
                
                # Find best platform for this content type
                content_type_performance = [p for p in filtered_data if p.content_type == content_type]
                if content_type_performance:
                    platform_performance = defaultdict(list)
                    for p in content_type_performance:
                        platform_performance[p.platform].append(p.performance_score)
                    
                    best_platform = max(platform_performance.items(), 
                                     key=lambda x: statistics.mean(x[1]))[0]
                    content_type_data[content_type]["best_platform"] = best_platform
        
        return dict(content_type_data)

    async def _analyze_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze trends over time"""
        trends = {
            "performance_trend": [],
            "engagement_trend": [],
            "content_volume_trend": [],
            "platform_trend": []
        }
        
        # Group metrics by date
        date_metrics = defaultdict(lambda: {
            "performance_scores": [],
            "engagement_scores": [],
            "content_count": 0,
            "platforms": set()
        })
        
        filtered_metrics = [
            m for m in self.metrics
            if start_date <= m.timestamp <= end_date
        ]
        
        for metric in filtered_metrics:
            date_key = metric.timestamp.date()
            date_metrics[date_key]["content_count"] += 1
            
            if metric.metric_type == MetricType.PERFORMANCE:
                date_metrics[date_key]["performance_scores"].append(metric.value)
            
            if metric.metric_type == MetricType.ENGAGEMENT:
                date_metrics[date_key]["engagement_scores"].append(metric.value)
            
            if metric.platform:
                date_metrics[date_key]["platforms"].add(metric.platform)
        
        # Convert to sorted lists
        sorted_dates = sorted(date_metrics.keys())
        
        for date in sorted_dates:
            data = date_metrics[date]
            
            # Performance trend
            if data["performance_scores"]:
                trends["performance_trend"].append({
                    "date": date.isoformat(),
                    "value": statistics.mean(data["performance_scores"])
                })
            
            # Engagement trend
            if data["engagement_scores"]:
                trends["engagement_trend"].append({
                    "date": date.isoformat(),
                    "value": statistics.mean(data["engagement_scores"])
                })
            
            # Content volume trend
            trends["content_volume_trend"].append({
                "date": date.isoformat(),
                "value": data["content_count"]
            })
            
            # Platform trend
            trends["platform_trend"].append({
                "date": date.isoformat(),
                "value": len(data["platforms"])
            })
        
        return trends

    async def _generate_recommendations(self, performance_summary: Dict[str, Any], 
                                     trends: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        # Performance-based recommendations
        if performance_summary.get("average_performance", 0) < 0.5:
            recommendations.append("Overall content performance is below target. Consider reviewing content quality and engagement strategies.")
        
        # Platform-specific recommendations
        platform_breakdown = performance_summary.get("platform_breakdown", {})
        for platform, data in platform_breakdown.items():
            if data.get("avg_performance", 0) < 0.4:
                recommendations.append(f"Performance on {platform.value} is low. Optimize content specifically for this platform.")
        
        # Content type recommendations
        content_type_breakdown = performance_summary.get("content_type_breakdown", {})
        best_type = max(content_type_breakdown.items(), key=lambda x: x[1].get("avg_performance", 0))[0]
        recommendations.append(f"Focus on creating more {best_type.value} content as it performs best.")
        
        # Trend-based recommendations
        if trends.get("performance_trend"):
            recent_performance = trends["performance_trend"][-3:]  # Last 3 data points
            if len(recent_performance) >= 2:
                first_avg = statistics.mean([p["value"] for p in recent_performance[:2]])
                last_avg = statistics.mean([p["value"] for p in recent_performance[-2:]])
                
                if last_avg < first_avg * 0.9:  # 10% decline
                    recommendations.append("Performance trend is declining. Review recent content strategy and quality.")
                elif last_avg > first_avg * 1.1:  # 10% improvement
                    recommendations.append("Performance trend is improving. Continue current successful strategies.")
        
        # Engagement recommendations
        if trends.get("engagement_trend"):
            recent_engagement = trends["engagement_trend"][-3:]
            if len(recent_engagement) >= 2:
                avg_engagement = statistics.mean([e["value"] for e in recent_engagement])
                if avg_engagement < 0.3:
                    recommendations.append("Low engagement rates detected. Consider improving content interactivity and call-to-actions.")
        
        return recommendations[:5]  # Limit to top 5 recommendations

    async def get_workflow_analytics(self, date_from: Optional[datetime] = None, 
                                   date_to: Optional[datetime] = None) -> WorkflowAnalytics:
        """Get workflow analytics for content management"""
        try:
            # This would typically integrate with the lifecycle manager
            # For now, return mock data
            return WorkflowAnalytics(
                total_content=len(self.performance_data),
                content_by_stage={
                    "draft": 5,
                    "in_review": 3,
                    "approved": 8,
                    "published": 14
                },
                average_review_time=2.5,  # days
                approval_rate=0.85,
                content_velocity=12.0,  # content per week
                bottlenecks=["content review", "quality checks"],
                efficiency_score=0.78
            )
        except Exception as e:
            logger.error(f"Error getting workflow analytics: {e}")
            return WorkflowAnalytics(
                total_content=0,
                content_by_stage={},
                average_review_time=0.0,
                approval_rate=0.0,
                content_velocity=0.0,
                bottlenecks=[],
                efficiency_score=0.0
            )

    async def export_report(self, report_id: str, format: str = "json") -> Union[str, bytes]:
        """Export report in specified format"""
        try:
            report = next((r for r in self.reports if r.report_id == report_id), None)
            if not report:
                raise ValueError(f"Report {report_id} not found")
            
            if format.lower() == "json":
                return json.dumps(asdict(report), default=str, indent=2)
            elif format.lower() == "csv":
                # Simple CSV export for key metrics
                csv_lines = ["Metric,Value"]
                csv_lines.append(f"Total Content,{report.metrics_summary.get('total_content', 0)}")
                csv_lines.append(f"Average Performance,{report.metrics_summary.get('average_performance', 0)}")
                csv_lines.append(f"Report Type,{report.report_type}")
                csv_lines.append(f"Date Range,{report.start_date.date()} to {report.end_date.date()}")
                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check analytics service health"""
        try:
            return {
                "status": "healthy",
                "total_metrics": len(self.metrics),
                "total_performance_records": len(self.performance_data),
                "total_reports": len(self.reports),
                "last_metric_tracked": self.metrics[-1].timestamp.isoformat() if self.metrics else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }




