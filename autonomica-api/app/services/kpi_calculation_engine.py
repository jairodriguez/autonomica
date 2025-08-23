"""
KPI Calculation Engine
Processes analytics data to calculate key performance indicators,
growth metrics, target achievement, and performance benchmarks.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import defaultdict
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.schema import SocialPost, ContentPiece, ContentStatus
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class KPIType(Enum):
    """Types of KPIs that can be calculated"""
    GROWTH = "growth"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    COMPETITIVE = "competitive"
    ROI = "roi"
    TIME_SAVINGS = "time_savings"

class MetricCategory(Enum):
    """Categories of metrics for KPI calculation"""
    SOCIAL_MEDIA = "social_media"
    SEO = "seo"
    CONTENT = "content"
    USER_BEHAVIOR = "user_behavior"
    SYSTEM = "system"
    BUSINESS = "business"
    AUTOMATION = "automation"

class TargetStatus(Enum):
    """Status of KPI targets"""
    ON_TARGET = "on_target"
    BELOW_TARGET = "below_target"
    ABOVE_TARGET = "above_target"
    CRITICAL = "critical"
    EXCEEDING = "exceeding"

@dataclass
class KPITarget:
    """KPI target definition"""
    kpi_id: str
    name: str
    description: str
    target_value: float
    current_value: float
    unit: str
    period: str  # daily, weekly, monthly, quarterly, yearly
    status: TargetStatus
    trend: float  # percentage change
    last_updated: datetime
    metadata: Dict[str, Any] = None

@dataclass
class KPICalculation:
    """KPI calculation result"""
    kpi_id: str
    name: str
    value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # increasing, decreasing, stable
    status: TargetStatus
    target: float
    unit: str
    calculated_at: datetime
    data_points: int
    confidence_score: float
    metadata: Dict[str, Any] = None

@dataclass
class GrowthMetrics:
    """Growth-related metrics"""
    period: str
    start_date: datetime
    end_date: datetime
    impressions_growth: float
    clicks_growth: float
    engagement_growth: float
    conversion_growth: float
    overall_growth_score: float
    target_achievement: float
    status: TargetStatus

@dataclass
class AdvancedKPIMetrics:
    """Advanced KPI metrics with additional insights"""
    kpi_id: str
    name: str
    value: float
    target: float
    unit: str
    period: str
    status: TargetStatus
    trend_direction: str
    change_percentage: float
    velocity: float  # Rate of change over time
    momentum: float  # Acceleration of change
    volatility: float  # Stability of the metric
    seasonality: float  # Seasonal pattern strength
    forecast: float  # Predicted next period value
    confidence_interval: tuple  # (lower, upper) bounds
    calculated_at: datetime
    metadata: Dict[str, Any] = None

class KPICalculationEngine:
    """
    Enhanced KPI calculation engine for analytics data
    
    Features:
    - Growth metric calculations
    - Target achievement tracking
    - Performance benchmarking
    - Trend analysis and forecasting
    - Multi-period comparisons
    - Confidence scoring
    - Advanced statistical analysis
    - ROI calculations
    - Time savings optimization
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Enhanced KPI targets from PRD requirements
        self.kpi_targets = {
            "impressions_growth": {
                "target": 25.0,  # 25% growth target from PRD
                "unit": "percentage",
                "period": "monthly",
                "description": "Monthly growth in search impressions",
                "category": KPIType.GROWTH,
                "weight": 0.25
            },
            "engagement_rate": {
                "target": 5.0,  # 5% engagement rate target
                "unit": "percentage",
                "period": "monthly",
                "description": "Monthly engagement rate across platforms",
                "category": KPIType.ENGAGEMENT,
                "weight": 0.20
            },
            "conversion_rate": {
                "target": 3.0,  # 3% conversion rate target
                "unit": "percentage",
                "period": "monthly",
                "description": "Monthly conversion rate from content",
                "category": KPIType.CONVERSION,
                "weight": 0.20
            },
            "content_quality": {
                "target": 85.0,  # 85% quality score target
                "unit": "score",
                "period": "monthly",
                "description": "Monthly content quality score",
                "category": KPIType.QUALITY,
                "weight": 0.15
            },
            "time_savings": {
                "target": 40.0,  # 40% time savings target
                "unit": "percentage",
                "period": "monthly",
                "description": "Monthly time savings from automation",
                "category": KPIType.TIME_SAVINGS,
                "weight": 0.10
            },
            "roi": {
                "target": 300.0,  # 300% ROI target
                "unit": "percentage",
                "period": "monthly",
                "description": "Monthly return on investment",
                "category": KPIType.ROI,
                "weight": 0.10
            }
        }
        
        # Calculation periods with enhanced configuration
        self.calculation_periods = {
            "daily": {"days": 1, "comparison_days": 7, "min_data_points": 3},
            "weekly": {"days": 7, "comparison_days": 28, "min_data_points": 4},
            "monthly": {"days": 30, "comparison_days": 90, "min_data_points": 3},
            "quarterly": {"days": 90, "comparison_days": 270, "min_data_points": 4},
            "yearly": {"days": 365, "comparison_days": 730, "min_data_points": 12}
        }
        
        # Statistical analysis configuration
        self.statistical_config = {
            "trend_analysis_window": 7,  # days for trend calculation
            "seasonality_periods": 12,    # months for seasonal analysis
            "forecast_horizon": 3,        # periods to forecast
            "confidence_level": 0.95,     # 95% confidence interval
            "min_volatility_threshold": 0.1,  # minimum volatility to consider
            "momentum_calculation_window": 5   # days for momentum calculation
        }
    
    async def calculate_growth_metrics(
        self,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> GrowthMetrics:
        """
        Calculate comprehensive growth metrics
        
        Args:
            period: Calculation period (daily, weekly, monthly, quarterly, yearly)
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            GrowthMetrics object with calculated growth data
        """
        try:
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            comparison_start = end_date - timedelta(days=period_config["comparison_days"])
            
            # Get current period metrics
            current_metrics = await self._get_period_metrics(start_date, end_date, user_id)
            
            # Get comparison period metrics
            comparison_metrics = await self._get_period_metrics(comparison_start, start_date, user_id)
            
            # Calculate growth percentages
            impressions_growth = self._calculate_growth_percentage(
                current_metrics.get("impressions", 0),
                comparison_metrics.get("impressions", 0)
            )
            
            clicks_growth = self._calculate_growth_percentage(
                current_metrics.get("clicks", 0),
                comparison_metrics.get("clicks", 0)
            )
            
            engagement_growth = self._calculate_growth_percentage(
                current_metrics.get("engagement", 0),
                comparison_metrics.get("engagement", 0)
            )
            
            conversion_growth = self._calculate_growth_percentage(
                current_metrics.get("conversions", 0),
                comparison_metrics.get("conversions", 0)
            )
            
            # Calculate overall growth score (weighted average)
            overall_growth_score = self._calculate_weighted_growth_score(
                impressions_growth, clicks_growth, engagement_growth, conversion_growth
            )
            
            # Calculate target achievement
            target_achievement = self._calculate_target_achievement(overall_growth_score)
            
            # Determine status
            status = self._determine_target_status(target_achievement)
            
            return GrowthMetrics(
                period=period,
                start_date=start_date,
                end_date=end_date,
                impressions_growth=impressions_growth,
                clicks_growth=clicks_growth,
                engagement_growth=engagement_growth,
                conversion_growth=conversion_growth,
                overall_growth_score=overall_growth_score,
                target_achievement=target_achievement,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
            raise
    
    async def calculate_kpi(
        self,
        kpi_name: str,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> KPICalculation:
        """
        Calculate a specific KPI
        
        Args:
            kpi_name: Name of the KPI to calculate
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            KPICalculation object with calculated KPI data
        """
        try:
            if kpi_name not in self.kpi_targets:
                raise ValueError(f"Unknown KPI: {kpi_name}")
            
            target_config = self.kpi_targets[kpi_name]
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            comparison_start = end_date - timedelta(days=period_config["comparison_days"])
            
            # Get current and previous period values
            current_value = await self._get_kpi_value(kpi_name, start_date, end_date, user_id)
            previous_value = await self._get_kpi_value(kpi_name, comparison_start, start_date, user_id)
            
            # Calculate change percentage
            change_percentage = self._calculate_growth_percentage(current_value, previous_value)
            
            # Determine trend direction
            trend_direction = self._determine_trend_direction(change_percentage)
            
            # Determine status
            status = self._determine_kpi_status(current_value, target_config["target"])
            
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(kpi_name, current_value, user_id)
            
            # Get data points count
            data_points = await self._get_data_points_count(kpi_name, start_date, end_date, user_id)
            
            return KPICalculation(
                kpi_id=kpi_name,
                name=target_config["description"],
                value=current_value,
                previous_value=previous_value,
                change_percentage=change_percentage,
                trend_direction=trend_direction,
                status=status,
                target=target_config["target"],
                unit=target_config["unit"],
                calculated_at=datetime.utcnow(),
                data_points=data_points,
                confidence_score=confidence_score,
                metadata={
                    "period": period,
                    "target_config": target_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating KPI {kpi_name}: {e}")
            raise
    
    async def calculate_all_kpis(
        self,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> List[KPICalculation]:
        """
        Calculate all available KPIs
        
        Args:
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            List of KPICalculation objects
        """
        try:
            kpi_calculations = []
            
            for kpi_name in self.kpi_targets.keys():
                try:
                    kpi_calculation = await self.calculate_kpi(kpi_name, period, user_id)
                    kpi_calculations.append(kpi_calculation)
                except Exception as e:
                    logger.warning(f"Failed to calculate KPI {kpi_name}: {e}")
                    continue
            
            return kpi_calculations
            
        except Exception as e:
            logger.error(f"Error calculating all KPIs: {e}")
            raise
    
    async def get_kpi_targets(self) -> Dict[str, KPITarget]:
        """
        Get current KPI targets with current values
        
        Returns:
            Dict of KPI targets with current status
        """
        try:
            kpi_targets = {}
            
            for kpi_name, target_config in self.kpi_targets.items():
                # Calculate current value
                current_value = await self._get_kpi_value(kpi_name, None, None)
                
                # Calculate trend (monthly comparison)
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                comparison_start = end_date - timedelta(days=60)
                
                current_period = await self._get_kpi_value(kpi_name, start_date, end_date)
                previous_period = await self._get_kpi_value(kpi_name, comparison_start, start_date)
                
                trend = self._calculate_growth_percentage(current_period, previous_period)
                
                # Determine status
                status = self._determine_kpi_status(current_value, target_config["target"])
                
                kpi_targets[kpi_name] = KPITarget(
                    kpi_id=kpi_name,
                    name=target_config["description"],
                    target_value=target_config["target"],
                    current_value=current_value,
                    unit=target_config["unit"],
                    period=target_config["period"],
                    status=status,
                    trend=trend,
                    last_updated=datetime.utcnow(),
                    metadata=target_config
                )
            
            return kpi_targets
            
        except Exception as e:
            logger.error(f"Error getting KPI targets: {e}")
            raise
    
    async def calculate_advanced_kpi(
        self,
        kpi_name: str,
        period: str = "monthly",
        user_id: Optional[str] = None,
        include_forecast: bool = True
    ) -> AdvancedKPIMetrics:
        """
        Calculate advanced KPI with statistical analysis
        
        Args:
            kpi_name: Name of the KPI to calculate
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            include_forecast: Whether to include forecasting
            
        Returns:
            AdvancedKPIMetrics object with comprehensive analysis
        """
        try:
            if kpi_name not in self.kpi_targets:
                raise ValueError(f"Unknown KPI: {kpi_name}")
            
            target_config = self.kpi_targets[kpi_name]
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            comparison_start = end_date - timedelta(days=period_config["comparison_days"])
            
            # Get historical data for advanced analysis
            historical_data = await self._get_historical_kpi_data(
                kpi_name, start_date, end_date, user_id
            )
            
            if len(historical_data) < period_config["min_data_points"]:
                logger.warning(f"Insufficient data points for {kpi_name}: {len(historical_data)} < {period_config['min_data_points']}")
                return await self._create_basic_advanced_kpi(kpi_name, target_config, period, user_id)
            
            # Calculate current and previous values
            current_value = historical_data[-1] if historical_data else 0.0
            previous_value = historical_data[-2] if len(historical_data) > 1 else 0.0
            
            # Calculate advanced metrics
            change_percentage = self._calculate_growth_percentage(current_value, previous_value)
            trend_direction = self._determine_trend_direction(change_percentage)
            status = self._determine_kpi_status(current_value, target_config["target"])
            
            # Statistical analysis
            velocity = self._calculate_velocity(historical_data, period_config["days"])
            momentum = self._calculate_momentum(historical_data, self.statistical_config["momentum_calculation_window"])
            volatility = self._calculate_volatility(historical_data)
            seasonality = self._calculate_seasonality(historical_data)
            
            # Forecasting
            forecast = 0.0
            confidence_interval = (0.0, 0.0)
            if include_forecast and len(historical_data) >= 6:
                forecast = self._forecast_next_period(historical_data, self.statistical_config["forecast_horizon"])
                confidence_interval = self._calculate_confidence_interval(
                    historical_data, self.statistical_config["confidence_level"]
                )
            
            return AdvancedKPIMetrics(
                kpi_id=kpi_name,
                name=target_config["description"],
                value=current_value,
                target=target_config["target"],
                unit=target_config["unit"],
                period=period,
                status=status,
                trend_direction=trend_direction,
                change_percentage=change_percentage,
                velocity=velocity,
                momentum=momentum,
                volatility=volatility,
                seasonality=seasonality,
                forecast=forecast,
                confidence_interval=confidence_interval,
                calculated_at=datetime.utcnow(),
                metadata={
                    "period": period,
                    "target_config": target_config,
                    "data_points": len(historical_data),
                    "statistical_config": self.statistical_config
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating advanced KPI {kpi_name}: {e}")
            raise
    
    async def calculate_roi_metrics(
        self,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate ROI-related metrics
        
        Args:
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            Dict of ROI metrics
        """
        try:
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            
            # Get cost and revenue data
            costs = await self._get_period_costs(start_date, end_date, user_id)
            revenue = await self._get_period_revenue(start_date, end_date, user_id)
            
            # Calculate ROI metrics
            total_cost = sum(costs.values())
            total_revenue = sum(revenue.values())
            
            if total_cost == 0:
                roi_percentage = 0.0
                profit_margin = 0.0
                cost_per_acquisition = 0.0
            else:
                roi_percentage = ((total_revenue - total_cost) / total_cost) * 100
                profit_margin = ((total_revenue - total_cost) / total_revenue) * 100 if total_revenue > 0 else 0.0
                cost_per_acquisition = total_cost / max(1, len([v for v in revenue.values() if v > 0]))
            
            return {
                "roi_percentage": round(roi_percentage, 2),
                "profit_margin": round(profit_margin, 2),
                "cost_per_acquisition": round(cost_per_acquisition, 2),
                "total_cost": round(total_cost, 2),
                "total_revenue": round(total_revenue, 2),
                "net_profit": round(total_revenue - total_cost, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI metrics: {e}")
            return {}
    
    async def calculate_time_savings_metrics(
        self,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate time savings and efficiency metrics
        
        Args:
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            Dict of time savings metrics
        """
        try:
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            
            # Get time tracking data
            manual_time = await self._get_period_manual_time(start_date, end_date, user_id)
            automated_time = await self._get_period_automated_time(start_date, end_date, user_id)
            
            total_manual_time = sum(manual_time.values())
            total_automated_time = sum(automated_time.values())
            
            if total_manual_time == 0:
                time_savings_percentage = 0.0
                efficiency_gain = 0.0
            else:
                time_savings_percentage = ((total_manual_time - total_automated_time) / total_manual_time) * 100
                efficiency_gain = (total_manual_time / total_automated_time) if total_automated_time > 0 else 0.0
            
            return {
                "time_savings_percentage": round(time_savings_percentage, 2),
                "efficiency_gain": round(efficiency_gain, 2),
                "manual_time_hours": round(total_manual_time / 3600, 2),  # Convert to hours
                "automated_time_hours": round(total_automated_time / 3600, 2),
                "saved_time_hours": round((total_manual_time - total_automated_time) / 3600, 2),
                "automation_rate": round((total_automated_time / (total_manual_time + total_automated_time)) * 100, 2) if (total_manual_time + total_automated_time) > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating time savings metrics: {e}")
            return {}
    
    async def calculate_competitive_metrics(
        self,
        period: str = "monthly",
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate competitive analysis metrics
        
        Args:
            period: Calculation period
            user_id: Optional user ID for user-specific metrics
            
        Returns:
            Dict of competitive metrics
        """
        try:
            period_config = self.calculation_periods.get(period, self.calculation_periods["monthly"])
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_config["days"])
            
            # Get competitive data (this would integrate with competitor analysis services)
            # For now, return placeholder values
            return {
                "market_share": 15.5,  # Placeholder: 15.5% market share
                "competitive_position": 3.2,  # Placeholder: 3.2 out of 5 competitive position
                "brand_awareness": 42.8,  # Placeholder: 42.8% brand awareness
                "customer_satisfaction": 4.1,  # Placeholder: 4.1 out of 5 satisfaction
                "innovation_score": 78.5,  # Placeholder: 78.5% innovation score
                "competitive_advantage": 65.2  # Placeholder: 65.2% competitive advantage
            }
            
        except Exception as e:
            logger.error(f"Error calculating competitive metrics: {e}")
            return {}
    
    async def _get_period_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get metrics for a specific time period"""
        try:
            metrics = {}
            
            # Get social media metrics
            social_metrics = await self._get_social_media_metrics(start_date, end_date, user_id)
            metrics.update(social_metrics)
            
            # Get content metrics
            content_metrics = await self._get_content_metrics(start_date, end_date, user_id)
            metrics.update(content_metrics)
            
            # Get SEO metrics
            seo_metrics = await self._get_seo_metrics(start_date, end_date, user_id)
            metrics.update(seo_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting period metrics: {e}")
            return {}
    
    async def _get_social_media_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get social media metrics for a time period"""
        try:
            query = self.db.query(SocialPost).filter(
                and_(
                    SocialPost.created_at >= start_date,
                    SocialPost.created_at <= end_date
                )
            )
            
            if user_id:
                query = query.filter(SocialPost.user_id == user_id)
            
            posts = query.all()
            
            total_impressions = 0
            total_engagement = 0
            total_reach = 0
            total_clicks = 0
            
            for post in posts:
                if post.metrics:
                    metrics = post.metrics
                    total_impressions += metrics.get("impressions", 0)
                    total_engagement += metrics.get("engagements", 0)
                    total_reach += metrics.get("reach", 0)
                    total_clicks += metrics.get("clicks", 0)
            
            return {
                "impressions": total_impressions,
                "engagement": total_engagement,
                "reach": total_reach,
                "clicks": total_clicks,
                "posts": len(posts)
            }
            
        except Exception as e:
            logger.error(f"Error getting social media metrics: {e}")
            return {}
    
    async def _get_content_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get content metrics for a time period"""
        try:
            query = self.db.query(ContentPiece).filter(
                and_(
                    ContentPiece.created_at >= start_date,
                    ContentPiece.created_at <= end_date
                )
            )
            
            if user_id:
                query = query.filter(ContentPiece.user_id == user_id)
            
            content_pieces = query.all()
            
            total_views = 0
            total_conversions = 0
            total_quality_score = 0
            content_count = len(content_pieces)
            
            for content in content_pieces:
                # This would integrate with content analytics service
                # For now, we'll use placeholder values
                total_views += 100  # Placeholder
                total_conversions += 5   # Placeholder
                total_quality_score += 85  # Placeholder
            
            avg_quality_score = total_quality_score / content_count if content_count > 0 else 0
            conversion_rate = (total_conversions / total_views * 100) if total_views > 0 else 0
            
            return {
                "views": total_views,
                "conversions": total_conversions,
                "conversion_rate": conversion_rate,
                "quality_score": avg_quality_score,
                "content_count": content_count
            }
            
        except Exception as e:
            logger.error(f"Error getting content metrics: {e}")
            return {}
    
    async def _get_seo_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get SEO metrics for a time period"""
        try:
            # This would integrate with Google Search Console and SEMrush
            # For now, we'll return placeholder values
            return {
                "search_impressions": 1000,  # Placeholder
                "search_clicks": 100,        # Placeholder
                "avg_position": 15.5,        # Placeholder
                "ctr": 10.0                  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"Error getting SEO metrics: {e}")
            return {}
    
    async def _get_kpi_value(
        self,
        kpi_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> float:
        """Get the current value for a specific KPI"""
        try:
            if kpi_name == "impressions_growth":
                # Calculate impressions growth
                if start_date and end_date:
                    current_metrics = await self._get_period_metrics(start_date, end_date, user_id)
                    return current_metrics.get("impressions", 0)
                else:
                    # Get current month impressions
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                    current_metrics = await self._get_period_metrics(start_date, end_date, user_id)
                    return current_metrics.get("impressions", 0)
            
            elif kpi_name == "engagement_rate":
                # Calculate engagement rate
                if start_date and end_date:
                    current_metrics = await self._get_period_metrics(start_date, end_date, user_id)
                    impressions = current_metrics.get("impressions", 0)
                    engagement = current_metrics.get("engagement", 0)
                    return (engagement / impressions * 100) if impressions > 0 else 0
                else:
                    # Get current month engagement rate
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                    current_metrics = await self._get_period_metrics(start_date, end_date, user_id)
                    impressions = current_metrics.get("impressions", 0)
                    engagement = current_metrics.get("engagement", 0)
                    return (engagement / impressions * 100) if impressions > 0 else 0
            
            elif kpi_name == "conversion_rate":
                # Get conversion rate from content metrics
                if start_date and end_date:
                    content_metrics = await self._get_content_metrics(start_date, end_date, user_id)
                    return content_metrics.get("conversion_rate", 0)
                else:
                    # Get current month conversion rate
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                    content_metrics = await self._get_content_metrics(start_date, end_date, user_id)
                    return content_metrics.get("conversion_rate", 0)
            
            elif kpi_name == "content_quality":
                # Get content quality score
                if start_date and end_date:
                    content_metrics = await self._get_content_metrics(start_date, end_date, user_id)
                    return content_metrics.get("quality_score", 0)
                else:
                    # Get current month quality score
                    end_date = datetime.utcnow()
                    start_date = end_date - timedelta(days=30)
                    content_metrics = await self._get_content_metrics(start_date, end_date, user_id)
                    return content_metrics.get("quality_score", 0)
            
            elif kpi_name == "time_savings":
                # Calculate time savings (this would integrate with workflow analytics)
                # For now, return a placeholder value
                return 35.0  # Placeholder: 35% time savings
            
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error getting KPI value for {kpi_name}: {e}")
            return 0.0
    
    async def _get_data_points_count(
        self,
        kpi_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> int:
        """Get the count of data points used for KPI calculation"""
        try:
            if start_date and end_date:
                # Count data points in the specified period
                if kpi_name in ["impressions_growth", "engagement_rate"]:
                    query = self.db.query(SocialPost).filter(
                        and_(
                            SocialPost.created_at >= start_date,
                            SocialPost.created_at <= end_date
                        )
                    )
                    if user_id:
                        query = query.filter(SocialPost.user_id == user_id)
                    return query.count()
                
                elif kpi_name in ["conversion_rate", "content_quality"]:
                    query = self.db.query(ContentPiece).filter(
                        and_(
                            ContentPiece.created_at >= start_date,
                            ContentPiece.created_at <= end_date
                        )
                    )
                    if user_id:
                        query = query.filter(ContentPiece.user_id == user_id)
                    return query.count()
                
                else:
                    return 0
            else:
                # Return total count for all time
                if kpi_name in ["impressions_growth", "engagement_rate"]:
                    query = self.db.query(SocialPost)
                    if user_id:
                        query = query.filter(SocialPost.user_id == user_id)
                    return query.count()
                
                elif kpi_name in ["conversion_rate", "content_quality"]:
                    query = self.db.query(ContentPiece)
                    if user_id:
                        query = query.filter(ContentPiece.user_id == user_id)
                    return query.count()
                
                else:
                    return 0
                    
        except Exception as e:
            logger.error(f"Error getting data points count for {kpi_name}: {e}")
            return 0
    
    async def _calculate_confidence_score(
        self,
        kpi_name: str,
        current_value: float,
        user_id: Optional[str] = None
    ) -> float:
        """Calculate confidence score for KPI calculation"""
        try:
            # Get data points count
            data_points = await self._get_data_points_count(kpi_name, user_id=user_id)
            
            # Base confidence on data availability
            if data_points == 0:
                return 0.0
            elif data_points < 10:
                return 0.3
            elif data_points < 50:
                return 0.6
            elif data_points < 100:
                return 0.8
            else:
                return 0.95
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _calculate_growth_percentage(self, current: float, previous: float) -> float:
        """Calculate growth percentage between two values"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        
        return ((current - previous) / previous) * 100
    
    def _calculate_weighted_growth_score(
        self,
        impressions_growth: float,
        clicks_growth: float,
        engagement_growth: float,
        conversion_growth: float
    ) -> float:
        """Calculate weighted growth score"""
        # Weights for different metrics
        weights = {
            "impressions": 0.3,    # 30% weight
            "clicks": 0.25,        # 25% weight
            "engagement": 0.25,    # 25% weight
            "conversion": 0.2      # 20% weight
        }
        
        weighted_score = (
            impressions_growth * weights["impressions"] +
            clicks_growth * weights["clicks"] +
            engagement_growth * weights["engagement"] +
            conversion_growth * weights["conversion"]
        )
        
        return round(weighted_score, 2)
    
    def _calculate_target_achievement(self, growth_score: float) -> float:
        """Calculate target achievement percentage"""
        target = 25.0  # 25% growth target from PRD
        achievement = (growth_score / target) * 100
        return min(achievement, 100.0)  # Cap at 100%
    
    def _determine_target_status(self, target_achievement: float) -> TargetStatus:
        """Determine target status based on achievement percentage"""
        if target_achievement >= 100:
            return TargetStatus.ABOVE_TARGET
        elif target_achievement >= 80:
            return TargetStatus.ON_TARGET
        elif target_achievement >= 50:
            return TargetStatus.BELOW_TARGET
        else:
            return TargetStatus.CRITICAL
    
    def _determine_kpi_status(self, current_value: float, target_value: float) -> TargetStatus:
        """Determine KPI status based on current vs target values"""
        if current_value >= target_value:
            return TargetStatus.ON_TARGET
        elif current_value >= target_value * 0.8:
            return TargetStatus.BELOW_TARGET
        elif current_value >= target_value * 0.5:
            return TargetStatus.BELOW_TARGET
        else:
            return TargetStatus.CRITICAL
    
    def _determine_trend_direction(self, change_percentage: float) -> str:
        """Determine trend direction based on change percentage"""
        if change_percentage > 5:
            return "increasing"
        elif change_percentage < -5:
            return "decreasing"
        else:
            return "stable"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the KPI calculation engine"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "kpi_targets": len(self.kpi_targets),
                "calculation_periods": len(self.calculation_periods),
                "database_connection": "healthy",
                "redis_connection": "healthy"
            }
            
            # Test database connection
            try:
                self.db.execute("SELECT 1")
                health_status["database_connection"] = "healthy"
            except Exception as e:
                health_status["database_connection"] = "unhealthy"
                health_status["status"] = "degraded"
                health_status["database_error"] = str(e)
            
            # Test Redis connection
            try:
                await self.redis_service.health_check()
                health_status["redis_connection"] = "healthy"
            except Exception as e:
                health_status["redis_connection"] = "unhealthy"
                health_status["status"] = "degraded"
                health_status["redis_error"] = str(e)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in KPI calculation engine health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _get_historical_kpi_data(
        self,
        kpi_name: str,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> List[float]:
        """Get historical KPI data for statistical analysis"""
        try:
            # This would retrieve historical data from the database or cache
            # For now, generate sample data for demonstration
            days_diff = (end_date - start_date).days
            data_points = []
            
            for i in range(days_diff):
                # Generate realistic sample data with some variation
                base_value = 100.0  # Base value for demonstration
                variation = math.sin(i * 0.1) * 20  # Sinusoidal variation
                noise = (hash(f"{kpi_name}_{i}") % 100 - 50) * 0.1  # Random noise
                value = max(0, base_value + variation + noise)
                data_points.append(value)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error getting historical KPI data: {e}")
            return []
    
    async def _create_basic_advanced_kpi(
        self,
        kpi_name: str,
        target_config: Dict[str, Any],
        period: str,
        user_id: Optional[str] = None
    ) -> AdvancedKPIMetrics:
        """Create basic advanced KPI when insufficient data is available"""
        current_value = await self._get_kpi_value(kpi_name, None, None, user_id)
        status = self._determine_kpi_status(current_value, target_config["target"])
        
        return AdvancedKPIMetrics(
            kpi_id=kpi_name,
            name=target_config["description"],
            value=current_value,
            target=target_config["target"],
            unit=target_config["unit"],
            period=period,
            status=status,
            trend_direction="stable",
            change_percentage=0.0,
            velocity=0.0,
            momentum=0.0,
            volatility=0.0,
            seasonality=0.0,
            forecast=current_value,
            confidence_interval=(current_value * 0.8, current_value * 1.2),
            calculated_at=datetime.utcnow(),
            metadata={
                "period": period,
                "target_config": target_config,
                "data_points": 0,
                "insufficient_data": True
            }
        )
    
    def _calculate_velocity(self, data: List[float], period_days: int) -> float:
        """Calculate the rate of change over time"""
        if len(data) < 2:
            return 0.0
        
        # Linear regression slope as velocity
        n = len(data)
        x_values = list(range(n))
        y_values = data
        
        # Calculate slope (velocity)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope * (period_days / n)  # Normalize to period
    
    def _calculate_momentum(self, data: List[float], window: int) -> float:
        """Calculate the acceleration of change (momentum)"""
        if len(data) < window + 1:
            return 0.0
        
        # Calculate velocity over two consecutive windows
        recent_data = data[-window:]
        previous_data = data[-2*window:-window] if len(data) >= 2*window else data[:-window]
        
        recent_velocity = self._calculate_velocity(recent_data, window)
        previous_velocity = self._calculate_velocity(previous_data, window)
        
        return recent_velocity - previous_velocity
    
    def _calculate_volatility(self, data: List[float]) -> float:
        """Calculate the stability/volatility of the metric"""
        if len(data) < 2:
            return 0.0
        
        mean = statistics.mean(data)
        variance = statistics.variance(data, mean)
        return math.sqrt(variance) / mean if mean != 0 else 0.0
    
    def _calculate_seasonality(self, data: List[float]) -> float:
        """Calculate the strength of seasonal patterns"""
        if len(data) < 12:  # Need at least 12 data points for seasonal analysis
            return 0.0
        
        # Simple seasonal strength calculation using autocorrelation
        seasonal_strength = 0.0
        for lag in [1, 2, 3, 6, 12]:  # Common seasonal lags
            if lag < len(data):
                correlation = self._calculate_autocorrelation(data, lag)
                seasonal_strength += abs(correlation)
        
        return seasonal_strength / 5  # Average of seasonal correlations
    
    def _calculate_autocorrelation(self, data: List[float], lag: int) -> float:
        """Calculate autocorrelation at a given lag"""
        if len(data) <= lag:
            return 0.0
        
        mean = statistics.mean(data)
        variance = statistics.variance(data, mean)
        
        if variance == 0:
            return 0.0
        
        autocorr = 0.0
        for i in range(len(data) - lag):
            autocorr += (data[i] - mean) * (data[i + lag] - mean)
        
        return autocorr / ((len(data) - lag) * variance)
    
    def _forecast_next_period(self, data: List[float], horizon: int) -> float:
        """Forecast the next period value using simple moving average with trend"""
        if len(data) < 3:
            return data[-1] if data else 0.0
        
        # Simple exponential smoothing with trend
        alpha = 0.3  # Smoothing factor
        beta = 0.1   # Trend factor
        
        # Initialize
        s = data[0]
        b = data[1] - data[0] if len(data) > 1 else 0
        
        # Apply exponential smoothing
        for i in range(1, len(data)):
            s_prev = s
            s = alpha * data[i] + (1 - alpha) * (s + b)
            b = beta * (s - s_prev) + (1 - beta) * b
        
        # Forecast
        forecast = s + b * horizon
        return max(0, forecast)  # Ensure non-negative
    
    def _calculate_confidence_interval(
        self,
        data: List[float],
        confidence_level: float
    ) -> tuple:
        """Calculate confidence interval for the forecast"""
        if len(data) < 2:
            return (0.0, 0.0)
        
        # Calculate standard error
        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)
        standard_error = std_dev / math.sqrt(len(data))
        
        # Z-score for confidence level (simplified)
        z_score = 1.96 if confidence_level == 0.95 else 1.645  # 95% or 90%
        
        margin_of_error = z_score * standard_error
        
        return (mean - margin_of_error, mean + margin_of_error)
    
    async def _get_period_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get costs for a time period"""
        # This would integrate with cost tracking services
        # For now, return placeholder values
        return {
            "advertising": 500.0,
            "content_creation": 300.0,
            "tools_subscriptions": 150.0,
            "labor": 800.0
        }
    
    async def _get_period_revenue(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get revenue for a time period"""
        # This would integrate with revenue tracking services
        # For now, return placeholder values
        return {
            "product_sales": 2500.0,
            "subscriptions": 800.0,
            "consulting": 1200.0,
            "affiliate": 300.0
        }
    
    async def _get_period_manual_time(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get manual time spent for a time period"""
        # This would integrate with time tracking services
        # For now, return placeholder values (in seconds)
        return {
            "content_creation": 7200,  # 2 hours
            "social_media": 3600,      # 1 hour
            "seo_analysis": 5400,      # 1.5 hours
            "reporting": 1800          # 0.5 hours
        }
    
    async def _get_period_automated_time(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[str] = None
    ) -> Dict[str, float]:
        """Get automated time for a time period"""
        # This would integrate with automation tracking services
        # For now, return placeholder values (in seconds)
        return {
            "content_creation": 1800,  # 0.5 hours
            "social_media": 900,       # 0.25 hours
            "seo_analysis": 2700,      # 0.75 hours
            "reporting": 900           # 0.25 hours
        }

class KPICalculationService:
    """
    Comprehensive KPI calculation service that integrates with Vercel KV storage
    and provides business intelligence features
    
    Features:
    - Real-time KPI calculation and caching
    - Business intelligence insights
    - Performance benchmarking
    - Goal tracking and alerts
    - Custom KPI definitions
    - Multi-tenant support
    """
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService, vercel_kv_service=None):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        self.kpi_engine = KPICalculationEngine(db, redis_service, cache_service)
        
        # Business intelligence configuration
        self.bi_config = {
            "performance_benchmarks": {
                "excellent": 0.9,    # 90%+ performance
                "good": 0.7,         # 70-89% performance
                "average": 0.5,      # 50-69% performance
                "below_average": 0.3, # 30-49% performance
                "poor": 0.0          # <30% performance
            },
            "alert_thresholds": {
                "critical": 0.3,     # Alert when below 30%
                "warning": 0.6,      # Warning when below 60%
                "info": 0.8          # Info when below 80%
            },
            "trend_analysis": {
                "positive_threshold": 0.05,   # 5% increase
                "negative_threshold": -0.05,  # 5% decrease
                "stable_threshold": 0.02      # 2% variation
            }
        }
    
    async def calculate_comprehensive_kpis(
        self,
        user_id: str,
        period: str = "monthly",
        include_advanced: bool = True,
        include_forecasts: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive KPIs for a user
        
        Args:
            user_id: User ID for multi-tenant support
            period: Calculation period
            include_advanced: Include advanced statistical analysis
            include_forecasts: Include forecasting
            
        Returns:
            Comprehensive KPI report
        """
        try:
            # Check cache first
            cache_key = f"kpi_comprehensive:{user_id}:{period}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                return cached_result
            
            # Calculate all KPIs
            kpi_results = {}
            
            # Basic KPIs
            basic_kpis = await self.kpi_engine.calculate_all_kpis(period, user_id)
            kpi_results["basic"] = [asdict(kpi) for kpi in basic_kpis]
            
            # Advanced KPIs
            if include_advanced:
                advanced_kpis = {}
                for kpi_name in self.kpi_engine.kpi_targets.keys():
                    try:
                        advanced_kpi = await self.kpi_engine.calculate_advanced_kpi(
                            kpi_name, period, user_id, include_forecasts
                        )
                        advanced_kpis[kpi_name] = asdict(advanced_kpi)
                    except Exception as e:
                        logger.warning(f"Failed to calculate advanced KPI {kpi_name}: {e}")
                        continue
                kpi_results["advanced"] = advanced_kpis
            
            # Business metrics
            roi_metrics = await self.kpi_engine.calculate_roi_metrics(period, user_id)
            time_savings_metrics = await self.kpi_engine.calculate_time_savings_metrics(period, user_id)
            competitive_metrics = await self.kpi_engine.calculate_competitive_metrics(period, user_id)
            
            kpi_results["business"] = {
                "roi": roi_metrics,
                "time_savings": time_savings_metrics,
                "competitive": competitive_metrics
            }
            
            # Business intelligence insights
            bi_insights = await self._generate_business_intelligence(kpi_results, user_id)
            kpi_results["insights"] = bi_insights
            
            # Performance summary
            performance_summary = await self._calculate_performance_summary(kpi_results)
            kpi_results["performance_summary"] = performance_summary
            
            # Store in Vercel KV if available
            if self.vercel_kv_service:
                await self.vercel_kv_service.store_analytics_data(
                    user_id=user_id,
                    data_type="kpi_comprehensive",
                    source_id=f"comprehensive_{period}",
                    metric_name="comprehensive_kpis",
                    metric_value=json.dumps(kpi_results),
                    metadata={
                        "period": period,
                        "include_advanced": include_advanced,
                        "include_forecasts": include_forecasts,
                        "calculated_at": datetime.utcnow().isoformat()
                    }
                )
            
            # Cache the result
            await self.cache_service.set(cache_key, kpi_results, ttl=3600)  # 1 hour cache
            
            return kpi_results
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive KPIs: {e}")
            raise
    
    async def _generate_business_intelligence(
        self,
        kpi_results: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Generate business intelligence insights from KPI data"""
        try:
            insights = {
                "performance_analysis": {},
                "trend_analysis": {},
                "recommendations": [],
                "alerts": [],
                "opportunities": [],
                "risks": []
            }
            
            # Performance analysis
            if "basic" in kpi_results:
                for kpi in kpi_results["basic"]:
                    kpi_name = kpi["kpi_id"]
                    current_value = kpi["value"]
                    target_value = kpi["target"]
                    status = kpi["status"]
                    
                    # Performance score
                    if target_value > 0:
                        performance_score = min(current_value / target_value, 2.0)  # Cap at 200%
                    else:
                        performance_score = 0.0
                    
                    insights["performance_analysis"][kpi_name] = {
                        "score": round(performance_score, 3),
                        "level": self._get_performance_level(performance_score),
                        "gap": round(target_value - current_value, 2),
                        "gap_percentage": round(((target_value - current_value) / target_value) * 100, 2) if target_value > 0 else 0
                    }
                    
                    # Generate alerts
                    if performance_score < self.bi_config["alert_thresholds"]["critical"]:
                        insights["alerts"].append({
                            "level": "critical",
                            "kpi": kpi_name,
                            "message": f"{kpi_name} is critically below target ({performance_score:.1%} of target)",
                            "current_value": current_value,
                            "target_value": target_value
                        })
                    elif performance_score < self.bi_config["alert_thresholds"]["warning"]:
                        insights["alerts"].append({
                            "level": "warning",
                            "kpi": kpi_name,
                            "message": f"{kpi_name} is below target ({performance_score:.1%} of target)",
                            "current_value": current_value,
                            "target_value": target_value
                        })
            
            # Trend analysis
            if "advanced" in kpi_results:
                for kpi_name, advanced_kpi in kpi_results["advanced"].items():
                    trend_direction = advanced_kpi.get("trend_direction", "stable")
                    change_percentage = advanced_kpi.get("change_percentage", 0)
                    momentum = advanced_kpi.get("momentum", 0)
                    
                    insights["trend_analysis"][kpi_name] = {
                        "direction": trend_direction,
                        "change_percentage": change_percentage,
                        "momentum": momentum,
                        "strength": self._get_trend_strength(change_percentage, momentum)
                    }
            
            # Generate recommendations
            insights["recommendations"] = await self._generate_recommendations(kpi_results, insights)
            
            # Identify opportunities and risks
            insights["opportunities"] = await self._identify_opportunities(kpi_results, insights)
            insights["risks"] = await self._identify_risks(kpi_results, insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating business intelligence: {e}")
            return {}
    
    async def _calculate_performance_summary(
        self,
        kpi_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall performance summary"""
        try:
            summary = {
                "overall_score": 0.0,
                "performance_distribution": {},
                "top_performers": [],
                "improvement_areas": [],
                "status_summary": {}
            }
            
            if "basic" in kpi_results:
                total_score = 0.0
                kpi_count = len(kpi_results["basic"])
                
                for kpi in kpi_results["basic"]:
                    current_value = kpi["value"]
                    target_value = kpi["target"]
                    
                    if target_value > 0:
                        score = min(current_value / target_value, 2.0)
                    else:
                        score = 0.0
                    
                    total_score += score
                
                summary["overall_score"] = round(total_score / kpi_count, 3) if kpi_count > 0 else 0.0
                
                # Performance distribution
                performance_levels = ["excellent", "good", "average", "below_average", "poor"]
                for level in performance_levels:
                    summary["performance_distribution"][level] = 0
                
                for kpi in kpi_results["basic"]:
                    current_value = kpi["value"]
                    target_value = kpi["target"]
                    
                    if target_value > 0:
                        score = min(current_value / target_value, 2.0)
                    else:
                        score = 0.0
                    
                    level = self._get_performance_level(score)
                    summary["performance_distribution"][level] += 1
                
                # Top performers and improvement areas
                for kpi in kpi_results["basic"]:
                    current_value = kpi["value"]
                    target_value = kpi["target"]
                    
                    if target_value > 0:
                        score = min(current_value / target_value, 2.0)
                    else:
                        score = 0.0
                    
                    if score >= 1.0:  # Meeting or exceeding target
                        summary["top_performers"].append({
                            "kpi": kpi["kpi_id"],
                            "score": round(score, 3),
                            "value": current_value,
                            "target": target_value
                        })
                    elif score < 0.8:  # Below 80% of target
                        summary["improvement_areas"].append({
                            "kpi": kpi["kpi_id"],
                            "score": round(score, 3),
                            "value": current_value,
                            "target": target_value,
                            "gap": round(target_value - current_value, 2)
                        })
                
                # Sort by performance
                summary["top_performers"].sort(key=lambda x: x["score"], reverse=True)
                summary["improvement_areas"].sort(key=lambda x: x["score"])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating performance summary: {e}")
            return {}
    
    async def _generate_recommendations(
        self,
        kpi_results: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on KPI analysis"""
        try:
            recommendations = []
            
            # Performance-based recommendations
            if "performance_analysis" in insights:
                for kpi_name, analysis in insights["performance_analysis"].items():
                    score = analysis["score"]
                    gap = analysis["gap"]
                    
                    if score < 0.5:  # Below 50% of target
                        recommendations.append({
                            "priority": "high",
                            "category": "performance",
                            "kpi": kpi_name,
                            "title": f"Immediate attention needed for {kpi_name}",
                            "description": f"Current performance is {score:.1%} of target. Focus on closing the {gap:.2f} gap.",
                            "action_items": [
                                "Review current strategies and tactics",
                                "Identify root causes of underperformance",
                                "Develop action plan with specific milestones",
                                "Increase monitoring frequency"
                            ]
                        })
                    elif score < 0.8:  # Below 80% of target
                        recommendations.append({
                            "priority": "medium",
                            "category": "performance",
                            "kpi": kpi_name,
                            "title": f"Improve {kpi_name} performance",
                            "description": f"Current performance is {score:.1%} of target. Opportunity for improvement.",
                            "action_items": [
                                "Analyze performance trends",
                                "Identify optimization opportunities",
                                "Implement incremental improvements",
                                "Monitor progress closely"
                            ]
                        })
            
            # Trend-based recommendations
            if "trend_analysis" in insights:
                for kpi_name, analysis in insights["trend_analysis"].items():
                    direction = analysis["direction"]
                    momentum = analysis["momentum"]
                    
                    if direction == "decreasing" and momentum < 0:
                        recommendations.append({
                            "priority": "high",
                            "category": "trend",
                            "kpi": kpi_name,
                            "title": f"Address declining {kpi_name} trend",
                            "description": f"{kpi_name} is trending downward with negative momentum.",
                            "action_items": [
                                "Investigate causes of decline",
                                "Implement corrective measures",
                                "Increase monitoring and reporting",
                                "Consider strategy adjustments"
                            ]
                        })
                    elif direction == "increasing" and momentum > 0:
                        recommendations.append({
                            "priority": "low",
                            "category": "trend",
                            "kpi": kpi_name,
                            "title": f"Leverage {kpi_name} momentum",
                            "description": f"{kpi_name} is trending upward with positive momentum.",
                            "action_items": [
                                "Identify success factors",
                                "Scale successful strategies",
                                "Document best practices",
                                "Share learnings across teams"
                            ]
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def _identify_opportunities(
        self,
        kpi_results: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify business opportunities from KPI analysis"""
        try:
            opportunities = []
            
            # High-performing KPIs
            if "performance_analysis" in insights:
                for kpi_name, analysis in insights["performance_analysis"].items():
                    score = analysis["score"]
                    
                    if score >= 1.2:  # Exceeding target by 20%+
                        opportunities.append({
                            "type": "performance_excellence",
                            "kpi": kpi_name,
                            "title": f"Leverage {kpi_name} excellence",
                            "description": f"{kpi_name} is exceeding target by {(score - 1.0) * 100:.1f}%",
                            "potential_impact": "high",
                            "action_items": [
                                "Analyze success factors",
                                "Scale successful strategies",
                                "Set higher targets",
                                "Share best practices"
                            ]
                        })
            
            # Positive trends
            if "trend_analysis" in insights:
                for kpi_name, analysis in insights["trend_analysis"].items():
                    direction = analysis["direction"]
                    momentum = analysis["momentum"]
                    
                    if direction == "increasing" and momentum > 0:
                        opportunities.append({
                            "type": "positive_momentum",
                            "kpi": kpi_name,
                            "title": f"Capitalize on {kpi_name} momentum",
                            "description": f"{kpi_name} shows strong positive momentum",
                            "potential_impact": "medium",
                            "action_items": [
                                "Accelerate successful initiatives",
                                "Allocate additional resources",
                                "Set stretch goals",
                                "Monitor for sustainability"
                            ]
                        })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying opportunities: {e}")
            return []
    
    async def _identify_risks(
        self,
        kpi_results: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify business risks from KPI analysis"""
        try:
            risks = []
            
            # Critical performance issues
            if "performance_analysis" in insights:
                for kpi_name, analysis in insights["performance_analysis"].items():
                    score = analysis["score"]
                    
                    if score < 0.3:  # Below 30% of target
                        risks.append({
                            "level": "critical",
                            "category": "performance",
                            "kpi": kpi_name,
                            "title": f"Critical risk: {kpi_name} severely underperforming",
                            "description": f"{kpi_name} is at {score:.1%} of target, indicating critical issues",
                            "potential_impact": "high",
                            "mitigation_actions": [
                                "Immediate intervention required",
                                "Escalate to senior management",
                                "Develop emergency response plan",
                                "Increase monitoring to daily"
                            ]
                        })
                    elif score < 0.6:  # Below 60% of target
                        risks.append({
                            "level": "high",
                            "category": "performance",
                            "kpi": kpi_name,
                            "title": f"High risk: {kpi_name} underperforming",
                            "description": f"{kpi_name} is at {score:.1%} of target, requiring attention",
                            "potential_impact": "medium",
                            "mitigation_actions": [
                                "Develop improvement plan",
                                "Allocate additional resources",
                                "Increase monitoring frequency",
                                "Set weekly progress reviews"
                            ]
                        })
            
            # Negative trends
            if "trend_analysis" in insights:
                for kpi_name, analysis in insights["trend_analysis"].items():
                    direction = analysis["direction"]
                    momentum = analysis["momentum"]
                    
                    if direction == "decreasing" and momentum < 0:
                        risks.append({
                            "level": "medium",
                            "category": "trend",
                            "kpi": kpi_name,
                            "title": f"Trend risk: {kpi_name} declining",
                            "description": f"{kpi_name} shows negative momentum and declining trend",
                            "potential_impact": "medium",
                            "mitigation_actions": [
                                "Investigate root causes",
                                "Implement corrective measures",
                                "Monitor trend closely",
                                "Prepare contingency plans"
                            ]
                        })
            
            return risks
            
        except Exception as e:
            logger.error(f"Error identifying risks: {e}")
            return []
    
    def _get_performance_level(self, score: float) -> str:
        """Get performance level based on score"""
        if score >= self.bi_config["performance_benchmarks"]["excellent"]:
            return "excellent"
        elif score >= self.bi_config["performance_benchmarks"]["good"]:
            return "good"
        elif score >= self.bi_config["performance_benchmarks"]["average"]:
            return "average"
        elif score >= self.bi_config["performance_benchmarks"]["below_average"]:
            return "below_average"
        else:
            return "poor"
    
    def _get_trend_strength(self, change_percentage: float, momentum: float) -> str:
        """Get trend strength based on change and momentum"""
        abs_change = abs(change_percentage)
        abs_momentum = abs(momentum)
        
        if abs_change > 20 or abs_momentum > 10:
            return "strong"
        elif abs_change > 10 or abs_momentum > 5:
            return "moderate"
        elif abs_change > 5 or abs_momentum > 2:
            return "weak"
        else:
            return "stable"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the KPI calculation service"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "KPICalculationService",
                "components": {}
            }
            
            # Check KPI engine
            try:
                engine_health = await self.kpi_engine.health_check()
                health_status["components"]["kpi_engine"] = engine_health
            except Exception as e:
                health_status["components"]["kpi_engine"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            # Check Vercel KV service
            if self.vercel_kv_service:
                try:
                    kv_health = await self.vercel_kv_service.health_check()
                    health_status["components"]["vercel_kv"] = kv_health
                except Exception as e:
                    health_status["components"]["vercel_kv"] = {"status": "unhealthy", "error": str(e)}
                    health_status["status"] = "degraded"
            
            # Check cache service
            try:
                await self.cache_service.set("health_check", "test", ttl=60)
                health_status["components"]["cache"] = {"status": "healthy"}
            except Exception as e:
                health_status["components"]["cache"] = {"status": "unhealthy", "error": str(e)}
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in KPI calculation service health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
