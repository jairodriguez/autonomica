"""
Content Analytics and Reporting Module

This module provides comprehensive analytics and reporting capabilities for
tracking content performance, engagement metrics, and generating insights.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, Counter

from content_types_simple import ContentType, ContentFormat
from content_versioning import get_versioning_system, ContentVersion, VersionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be tracked"""
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    BUSINESS = "business"


class EngagementMetric(str, Enum):
    """Specific engagement metrics"""
    VIEWS = "views"
    LIKES = "likes"
    SHARES = "shares"
    COMMENTS = "comments"
    CLICKS = "clicks"
    CONVERSIONS = "conversions"
    BOUNCE_RATE = "bounce_rate"
    TIME_ON_PAGE = "time_on_page"


class PerformanceMetric(str, Enum):
    """Specific performance metrics"""
    LOAD_TIME = "load_time"
    SEO_SCORE = "seo_score"
    READABILITY_SCORE = "readability_score"
    QUALITY_SCORE = "quality_score"
    APPROVAL_RATE = "approval_rate"
    REVISION_COUNT = "revision_count"


@dataclass
class ContentMetric:
    """Represents a single metric measurement"""
    metric_id: str
    content_id: str
    version_id: str
    metric_type: MetricType
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetric':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ContentPerformance:
    """Aggregated performance data for content"""
    content_id: str
    version_id: str
    content_type: ContentType
    total_views: int = 0
    total_likes: int = 0
    total_shares: int = 0
    total_comments: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    avg_time_on_page: float = 0.0
    bounce_rate: float = 0.0
    engagement_rate: float = 0.0
    conversion_rate: float = 0.0
    quality_score: float = 0.0
    seo_score: float = 0.0
    readability_score: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentPerformance':
        """Create from dictionary"""
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""
    report_id: str
    report_type: str
    generated_at: datetime
    time_period: str
    summary: str
    metrics: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    charts_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalyticsReport':
        """Create from dictionary"""
        data['generated_at'] = datetime.fromisoformat(data['generated_at'])
        return cls(**data)


class ContentAnalytics:
    """Main analytics engine for content performance tracking"""
    
    def __init__(self):
        self.metrics: Dict[str, ContentMetric] = {}
        self.performance: Dict[str, ContentPerformance] = {}
        self.versioning_system = get_versioning_system()
        
    def track_metric(self, 
                    content_id: str,
                    version_id: str,
                    metric_type: MetricType,
                    metric_name: str,
                    value: float,
                    unit: str = "",
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Track a new metric measurement"""
        
        metric_id = str(uuid.uuid4())
        metric = ContentMetric(
            metric_id=metric_id,
            content_id=content_id,
            version_id=version_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )
        
        self.metrics[metric_id] = metric
        
        # Update aggregated performance data
        self._update_performance_data(content_id, version_id, metric)
        
        logger.info(f"Tracked metric {metric_name} for content {content_id}: {value} {unit}")
        return metric_id
    
    def _update_performance_data(self, content_id: str, version_id: str, metric: ContentMetric) -> None:
        """Update aggregated performance data based on new metric"""
        
        if content_id not in self.performance:
            # Get content type from versioning system
            version = self.versioning_system.versions.get(version_id)
            content_type = version.content_type if version else ContentType.BLOG_POST
            
            self.performance[content_id] = ContentPerformance(
                content_id=content_id,
                version_id=version_id,
                content_type=content_type
            )
        
        performance = self.performance[content_id]
        performance.last_updated = datetime.now(timezone.utc)
        
        # Update specific metrics based on type
        if metric.metric_type == MetricType.ENGAGEMENT:
            if metric.metric_name == EngagementMetric.VIEWS.value:
                performance.total_views = int(metric.value)
            elif metric.metric_name == EngagementMetric.LIKES.value:
                performance.total_likes = int(metric.value)
            elif metric.metric_name == EngagementMetric.SHARES.value:
                performance.total_shares = int(metric.value)
            elif metric.metric_name == EngagementMetric.COMMENTS.value:
                performance.total_comments = int(metric.value)
            elif metric.metric_name == EngagementMetric.CLICKS.value:
                performance.total_clicks = int(metric.value)
            elif metric.metric_name == EngagementMetric.CONVERSIONS.value:
                performance.total_conversions = int(metric.value)
            elif metric.metric_name == EngagementMetric.TIME_ON_PAGE.value:
                performance.avg_time_on_page = metric.value
            elif metric.metric_name == EngagementMetric.BOUNCE_RATE.value:
                performance.bounce_rate = metric.value
        
        elif metric.metric_type == MetricType.QUALITY:
            if metric.metric_name == PerformanceMetric.QUALITY_SCORE.value:
                performance.quality_score = metric.value
            elif metric.metric_name == PerformanceMetric.SEO_SCORE.value:
                performance.seo_score = metric.value
            elif metric.metric_name == PerformanceMetric.READABILITY_SCORE.value:
                performance.readability_score = metric.value
        
        # Calculate derived metrics
        self._calculate_derived_metrics(performance)
    
    def _calculate_derived_metrics(self, performance: ContentPerformance) -> None:
        """Calculate derived metrics from raw data"""
        
        # Engagement rate (likes + shares + comments) / views
        if performance.total_views > 0:
            performance.engagement_rate = (
                (performance.total_likes + performance.total_shares + performance.total_comments) 
                / performance.total_views * 100
            )
        
        # Conversion rate
        if performance.total_clicks > 0:
            performance.conversion_rate = (performance.total_conversions / performance.total_clicks) * 100
    
    def get_content_performance(self, content_id: str) -> Optional[ContentPerformance]:
        """Get performance data for specific content"""
        return self.performance.get(content_id)
    
    def get_metrics_for_content(self, content_id: str, 
                               metric_type: Optional[MetricType] = None,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[ContentMetric]:
        """Get metrics for specific content with optional filtering"""
        
        metrics = []
        for metric in self.metrics.values():
            if metric.content_id != content_id:
                continue
            
            if metric_type and metric.metric_type != metric_type:
                continue
            
            if start_date and metric.timestamp < start_date:
                continue
            
            if end_date and metric.timestamp > end_date:
                continue
            
            metrics.append(metric)
        
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def get_performance_summary(self, time_period: str = "30d") -> Dict[str, Any]:
        """Get performance summary across all content"""
        
        # Calculate time range
        end_date = datetime.now(timezone.utc)
        if time_period == "7d":
            start_date = end_date - timedelta(days=7)
        elif time_period == "30d":
            start_date = end_date - timedelta(days=30)
        elif time_period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 30 days
        
        # Filter metrics by time range
        recent_metrics = [
            m for m in self.metrics.values() 
            if start_date <= m.timestamp <= end_date
        ]
        
        # Aggregate data
        summary = {
            "time_period": time_period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_content": len(self.performance),
            "total_metrics": len(recent_metrics),
            "engagement_metrics": {},
            "performance_metrics": {},
            "top_performing_content": [],
            "content_type_distribution": {},
            "trends": {}
        }
        
        # Engagement metrics
        engagement_metrics = [m for m in recent_metrics if m.metric_type == MetricType.ENGAGEMENT]
        for metric in engagement_metrics:
            if metric.metric_name not in summary["engagement_metrics"]:
                summary["engagement_metrics"][metric.metric_name] = 0
            summary["engagement_metrics"][metric.metric_name] += metric.value
        
        # Performance metrics
        performance_metrics = [m for m in recent_metrics if m.metric_type == MetricType.PERFORMANCE]
        for metric in performance_metrics:
            if metric.metric_name not in summary["performance_metrics"]:
                summary["performance_metrics"][metric.metric_name] = []
            summary["performance_metrics"][metric.metric_name].append(metric.value)
        
        # Calculate averages for performance metrics
        for metric_name, values in summary["performance_metrics"].items():
            if values:
                summary["performance_metrics"][metric_name] = sum(values) / len(values)
        
        # Top performing content
        content_scores = []
        for content_id, perf in self.performance.items():
            score = (perf.engagement_rate * 0.4 + 
                    perf.quality_score * 0.3 + 
                    perf.seo_score * 0.3)
            content_scores.append((content_id, score, perf))
        
        content_scores.sort(key=lambda x: x[1], reverse=True)
        summary["top_performing_content"] = [
            {
                "content_id": content_id,
                "score": score,
                "content_type": perf.content_type.value,
                "engagement_rate": perf.engagement_rate,
                "quality_score": perf.quality_score
            }
            for content_id, score, perf in content_scores[:10]
        ]
        
        # Content type distribution
        type_counts = Counter(perf.content_type.value for perf in self.performance.values())
        summary["content_type_distribution"] = dict(type_counts)
        
        return summary
    
    def generate_content_report(self, content_id: str, 
                               include_metrics: bool = True,
                               include_trends: bool = True) -> AnalyticsReport:
        """Generate a comprehensive report for specific content"""
        
        performance = self.get_content_performance(content_id)
        if not performance:
            raise ValueError(f"No performance data found for content {content_id}")
        
        # Get metrics for this content
        metrics = self.get_metrics_for_content(content_id)
        
        # Generate insights
        insights = self._generate_content_insights(performance, metrics)
        
        # Generate recommendations
        recommendations = self._generate_content_recommendations(performance, metrics)
        
        # Prepare metrics data
        metrics_data = {
            "overview": {
                "content_type": performance.content_type.value,
                "total_views": performance.total_views,
                "engagement_rate": performance.engagement_rate,
                "quality_score": performance.quality_score,
                "seo_score": performance.seo_score
            },
            "engagement": {
                "likes": performance.total_likes,
                "shares": performance.total_shares,
                "comments": performance.total_comments,
                "clicks": performance.total_clicks,
                "conversions": performance.total_conversions
            },
            "performance": {
                "bounce_rate": performance.bounce_rate,
                "avg_time_on_page": performance.avg_time_on_page,
                "conversion_rate": performance.conversion_rate
            }
        }
        
        if include_metrics:
            metrics_data["detailed_metrics"] = [
                {
                    "metric_name": m.metric_name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                    "metadata": m.metadata
                }
                for m in metrics
            ]
        
        # Generate charts data
        charts_data = None
        if include_trends:
            charts_data = self._generate_charts_data(content_id, metrics)
        
        report = AnalyticsReport(
            report_id=str(uuid.uuid4()),
            report_type="content_performance",
            generated_at=datetime.now(timezone.utc),
            time_period="all_time",
            summary=f"Performance report for {performance.content_type.value} content",
            metrics=metrics_data,
            insights=insights,
            recommendations=recommendations,
            charts_data=charts_data
        )
        
        return report
    
    def generate_system_report(self, time_period: str = "30d") -> AnalyticsReport:
        """Generate a system-wide analytics report"""
        
        summary_data = self.get_performance_summary(time_period)
        
        # Generate insights
        insights = self._generate_system_insights(summary_data)
        
        # Generate recommendations
        recommendations = self._generate_system_recommendations(summary_data)
        
        report = AnalyticsReport(
            report_id=str(uuid.uuid4()),
            report_type="system_analytics",
            generated_at=datetime.now(timezone.utc),
            time_period=time_period,
            summary=f"System analytics report for {time_period}",
            metrics=summary_data,
            insights=insights,
            recommendations=recommendations
        )
        
        return report
    
    def _generate_content_insights(self, performance: ContentPerformance, 
                                  metrics: List[ContentMetric]) -> List[str]:
        """Generate insights for specific content"""
        
        insights = []
        
        # Engagement insights
        if performance.engagement_rate > 5.0:
            insights.append("Content has high engagement rate, indicating strong audience connection")
        elif performance.engagement_rate < 1.0:
            insights.append("Low engagement rate suggests content may need optimization")
        
        if performance.total_shares > performance.total_likes:
            insights.append("High share-to-like ratio indicates content has viral potential")
        
        # Quality insights
        if performance.quality_score > 80:
            insights.append("Content quality is excellent, maintaining high standards")
        elif performance.quality_score < 50:
            insights.append("Content quality needs improvement to meet standards")
        
        # Performance insights
        if performance.bounce_rate > 70:
            insights.append("High bounce rate suggests content may not meet user expectations")
        
        if performance.conversion_rate > 5:
            insights.append("Strong conversion rate indicates effective call-to-action")
        
        return insights
    
    def _generate_content_recommendations(self, performance: ContentPerformance,
                                        metrics: List[ContentMetric]) -> List[str]:
        """Generate recommendations for specific content"""
        
        recommendations = []
        
        # Engagement recommendations
        if performance.engagement_rate < 2.0:
            recommendations.append("Add more interactive elements to increase engagement")
            recommendations.append("Include compelling visuals and multimedia content")
        
        if performance.total_shares < performance.total_likes * 0.1:
            recommendations.append("Optimize content for social sharing with shareable quotes")
            recommendations.append("Add social sharing buttons and incentives")
        
        # Quality recommendations
        if performance.quality_score < 70:
            recommendations.append("Review and improve content quality based on feedback")
            recommendations.append("Implement quality check workflow before publishing")
        
        # Performance recommendations
        if performance.bounce_rate > 60:
            recommendations.append("Improve content introduction to capture reader attention")
            recommendations.append("Ensure content delivers on headline promises")
        
        if performance.conversion_rate < 2:
            recommendations.append("Strengthen call-to-action elements")
            recommendations.append("Test different conversion strategies")
        
        return recommendations
    
    def _generate_system_insights(self, summary_data: Dict[str, Any]) -> List[str]:
        """Generate system-wide insights"""
        
        insights = []
        
        # Content performance insights
        if summary_data["total_content"] > 0:
            avg_engagement = (
                summary_data["engagement_metrics"].get("likes", 0) +
                summary_data["engagement_metrics"].get("shares", 0) +
                summary_data["engagement_metrics"].get("comments", 0)
            ) / summary_data["total_content"]
            
            if avg_engagement > 10:
                insights.append("Overall content performance is strong with high engagement")
            elif avg_engagement < 3:
                insights.append("Content engagement is below target, review content strategy")
        
        # Content type insights
        if summary_data["content_type_distribution"]:
            top_type = max(summary_data["content_type_distribution"].items(), key=lambda x: x[1])
            insights.append(f"Most popular content type is {top_type[0]} ({top_type[1]} pieces)")
        
        return insights
    
    def _generate_system_recommendations(self, summary_data: Dict[str, Any]) -> List[str]:
        """Generate system-wide recommendations"""
        
        recommendations = []
        
        # Content strategy recommendations
        if summary_data["total_content"] < 10:
            recommendations.append("Increase content production to build audience")
        
        if len(summary_data["content_type_distribution"]) < 3:
            recommendations.append("Diversify content types to reach different audience segments")
        
        # Performance recommendations
        if summary_data["engagement_metrics"].get("shares", 0) < summary_data["engagement_metrics"].get("likes", 0) * 0.2:
            recommendations.append("Focus on creating more shareable content")
        
        return recommendations
    
    def _generate_charts_data(self, content_id: str, metrics: List[ContentMetric]) -> Dict[str, Any]:
        """Generate data for charts and visualizations"""
        
        charts_data = {
            "engagement_timeline": [],
            "metric_distribution": {},
            "performance_trends": []
        }
        
        # Engagement timeline
        engagement_metrics = [m for m in metrics if m.metric_type == MetricType.ENGAGEMENT]
        for metric in engagement_metrics:
            charts_data["engagement_timeline"].append({
                "date": metric.timestamp.strftime("%Y-%m-%d"),
                "metric": metric.metric_name,
                "value": metric.value
            })
        
        # Metric distribution
        metric_counts = Counter(m.metric_name for m in metrics)
        charts_data["metric_distribution"] = dict(metric_counts)
        
        # Performance trends (last 7 days)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        daily_metrics = defaultdict(list)
        for metric in metrics:
            if start_date <= metric.timestamp <= end_date:
                date_key = metric.timestamp.strftime("%Y-%m-%d")
                daily_metrics[date_key].append(metric.value)
        
        for date, values in daily_metrics.items():
            charts_data["performance_trends"].append({
                "date": date,
                "avg_value": sum(values) / len(values),
                "total_metrics": len(values)
            })
        
        return charts_data
    
    def export_analytics_data(self, content_id: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export analytics data for external analysis"""
        
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "metrics": [],
            "performance": {},
            "summary": {}
        }
        
        # Export metrics
        for metric in self.metrics.values():
            if content_id and metric.content_id != content_id:
                continue
            
            if start_date and metric.timestamp < start_date:
                continue
            
            if end_date and metric.timestamp > end_date:
                continue
            
            export_data["metrics"].append(metric.to_dict())
        
        # Export performance data
        if content_id:
            if content_id in self.performance:
                export_data["performance"][content_id] = self.performance[content_id].to_dict()
        else:
            for cid, perf in self.performance.items():
                export_data["performance"][cid] = perf.to_dict()
        
        # Export summary
        export_data["summary"] = self.get_performance_summary()
        
        return export_data


# Global analytics instance
_analytics = None

def get_analytics() -> ContentAnalytics:
    """Get the global analytics instance"""
    global _analytics
    if _analytics is None:
        _analytics = ContentAnalytics()
    return _analytics