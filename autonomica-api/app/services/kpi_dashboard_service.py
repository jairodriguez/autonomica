"""
KPI Dashboard Service
Provides interactive dashboards to visualize key metrics and KPIs
with real-time data updates and user-friendly interfaces.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio

from sqlalchemy.orm import Session

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.kpi_calculation_engine import KPICalculationEngine, KPICalculationService
from app.services.vercel_kv_service import VercelKVService

logger = logging.getLogger(__name__)

class DashboardType(Enum):
    """Types of dashboards available"""
    OVERVIEW = "overview"
    PERFORMANCE = "performance"
    GROWTH = "growth"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    ROI = "roi"
    TIME_SAVINGS = "time_savings"
    COMPETITIVE = "competitive"
    CUSTOM = "custom"

class ChartType(Enum):
    """Types of charts available for visualization"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DONUT = "donut"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    METRIC_CARD = "metric_card"
    TABLE = "table"
    HEATMAP = "heatmap"

class DashboardLayout(Enum):
    """Dashboard layout configurations"""
    GRID = "grid"
    FLEXIBLE = "flexible"
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"

@dataclass
class DashboardWidget:
    """Dashboard widget definition"""
    id: str
    title: str
    description: str
    chart_type: ChartType
    data_source: str
    refresh_interval: int  # seconds
    size: Dict[str, int]  # width, height
    position: Dict[str, int]  # x, y coordinates
    config: Dict[str, Any]  # chart-specific configuration
    filters: List[str]  # available filters
    drill_down: bool  # whether drill-down is enabled

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    dashboard_id: str
    name: str
    description: str
    dashboard_type: DashboardType
    layout: DashboardLayout
    widgets: List[DashboardWidget]
    refresh_interval: int  # seconds
    theme: str  # light, dark, auto
    custom_css: Optional[str] = None
    permissions: List[str] = None  # user roles that can access

@dataclass
class DashboardData:
    """Dashboard data response"""
    dashboard_id: str
    timestamp: datetime
    widgets_data: Dict[str, Any]
    summary_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    last_updated: datetime
    refresh_in: int  # seconds until next refresh

class KPIDashboardService:
    """
    KPI Dashboard Service for creating interactive visualizations
    
    Features:
    - Real-time KPI dashboards
    - Interactive charts and graphs
    - Customizable widget layouts
    - Real-time data updates
    - Multi-tenant support
    - Responsive design
    - Export capabilities
    """
    
    def __init__(
        self,
        db: Session,
        redis_service: RedisService,
        cache_service: CacheService,
        kpi_service: KPICalculationService,
        vercel_kv_service: Optional[VercelKVService] = None
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.kpi_service = kpi_service
        self.vercel_kv_service = vercel_kv_service
        
        # Default dashboard configurations
        self.default_dashboards = self._initialize_default_dashboards()
        
        # Chart configuration templates
        self.chart_configs = self._initialize_chart_configs()
        
        # Dashboard refresh intervals
        self.refresh_intervals = {
            "real_time": 30,      # 30 seconds
            "near_real_time": 300, # 5 minutes
            "hourly": 3600,       # 1 hour
            "daily": 86400        # 24 hours
        }
    
    def _initialize_default_dashboards(self) -> Dict[str, DashboardConfig]:
        """Initialize default dashboard configurations"""
        dashboards = {}
        
        # Overview Dashboard
        overview_widgets = [
            DashboardWidget(
                id="overview_metrics",
                title="Key Performance Overview",
                description="High-level KPI summary",
                chart_type=ChartType.METRIC_CARD,
                data_source="kpi_overview",
                refresh_interval=300,
                size={"width": 12, "height": 2},
                position={"x": 0, "y": 0},
                config={"metrics": ["impressions_growth", "engagement_rate", "conversion_rate", "time_savings"]},
                filters=["period", "platform"],
                drill_down=True
            ),
            DashboardWidget(
                id="growth_trends",
                title="Growth Trends",
                description="Performance trends over time",
                chart_type=ChartType.LINE,
                data_source="growth_metrics",
                refresh_interval=300,
                size={"width": 8, "height": 4},
                position={"x": 0, "y": 2},
                config={"y_axis": "percentage", "show_targets": True, "smooth_lines": True},
                filters=["period", "metric_type"],
                drill_down=True
            ),
            DashboardWidget(
                id="performance_distribution",
                title="Performance Distribution",
                description="KPI performance breakdown",
                chart_type=ChartType.DONUT,
                data_source="performance_summary",
                refresh_interval=300,
                size={"width": 4, "height": 4},
                position={"x": 8, "y": 2},
                config={"show_percentages": True, "color_scheme": "performance"},
                filters=["period"],
                drill_down=False
            ),
            DashboardWidget(
                id="top_performers",
                title="Top Performing KPIs",
                description="Best performing metrics",
                chart_type=ChartType.BAR,
                data_source="top_performers",
                refresh_interval=300,
                size={"width": 6, "height": 3},
                position={"x": 0, "y": 6},
                config={"orientation": "horizontal", "show_values": True},
                filters=["period", "metric_type"],
                drill_down=True
            ),
            DashboardWidget(
                id="improvement_areas",
                title="Areas for Improvement",
                description="KPIs below target",
                chart_type=ChartType.BAR,
                data_source="improvement_areas",
                refresh_interval=300,
                size={"width": 6, "height": 3},
                position={"x": 6, "y": 6},
                config={"orientation": "horizontal", "show_values": True, "color_scheme": "warning"},
                filters=["period", "metric_type"],
                drill_down=True
            )
        ]
        
        dashboards["overview"] = DashboardConfig(
            dashboard_id="overview",
            name="Performance Overview",
            description="High-level view of all key performance indicators",
            dashboard_type=DashboardType.OVERVIEW,
            layout=DashboardLayout.GRID,
            widgets=overview_widgets,
            refresh_interval=300,
            theme="auto",
            permissions=["user", "admin"]
        )
        
        # Performance Dashboard
        performance_widgets = [
            DashboardWidget(
                id="performance_metrics",
                title="Performance Metrics",
                description="Detailed performance breakdown",
                chart_type=ChartType.GAUGE,
                data_source="performance_metrics",
                refresh_interval=300,
                size={"width": 4, "height": 3},
                position={"x": 0, "y": 0},
                config={"min_value": 0, "max_value": 100, "thresholds": [30, 60, 80]},
                filters=["period", "metric_type"],
                drill_down=False
            ),
            DashboardWidget(
                id="performance_trends",
                title="Performance Trends",
                description="Performance over time",
                chart_type=ChartType.AREA,
                data_source="performance_trends",
                refresh_interval=300,
                size={"width": 8, "height": 3},
                position={"x": 4, "y": 0},
                config={"stacked": False, "show_targets": True},
                filters=["period", "metric_type"],
                drill_down=True
            ),
            DashboardWidget(
                id="performance_comparison",
                title="Performance Comparison",
                description="Compare different periods",
                chart_type=ChartType.BAR,
                data_source="performance_comparison",
                refresh_interval=300,
                size={"width": 12, "height": 4},
                position={"x": 0, "y": 3},
                config={"grouped": True, "show_percentages": True},
                filters=["period", "comparison_period"],
                drill_down=True
            )
        ]
        
        dashboards["performance"] = DashboardConfig(
            dashboard_id="performance",
            name="Performance Analysis",
            description="Detailed performance analysis and trends",
            dashboard_type=DashboardType.PERFORMANCE,
            layout=DashboardLayout.GRID,
            widgets=performance_widgets,
            refresh_interval=300,
            theme="auto",
            permissions=["user", "admin"]
        )
        
        # Growth Dashboard
        growth_widgets = [
            DashboardWidget(
                id="growth_overview",
                title="Growth Overview",
                description="Growth metrics summary",
                chart_type=ChartType.METRIC_CARD,
                data_source="growth_overview",
                refresh_interval=300,
                size={"width": 12, "height": 2},
                position={"x": 0, "y": 0},
                config={"metrics": ["overall_growth", "impressions_growth", "engagement_growth", "conversion_growth"]},
                filters=["period"],
                drill_down=True
            ),
            DashboardWidget(
                id="growth_velocity",
                title="Growth Velocity",
                description="Rate of change over time",
                chart_type=ChartType.LINE,
                data_source="growth_velocity",
                refresh_interval=300,
                size={"width": 6, "height": 4},
                position={"x": 0, "y": 2},
                config={"y_axis": "velocity", "show_momentum": True},
                filters=["period", "metric_type"],
                drill_down=True
            ),
            DashboardWidget(
                id="growth_momentum",
                title="Growth Momentum",
                description="Acceleration of growth",
                chart_type=ChartType.SCATTER,
                data_source="growth_momentum",
                refresh_interval=300,
                size={"width": 6, "height": 4},
                position={"x": 6, "y": 2},
                config={"x_axis": "velocity", "y_axis": "momentum", "show_quadrants": True},
                filters=["period", "metric_type"],
                drill_down=True
            )
        ]
        
        dashboards["growth"] = DashboardConfig(
            dashboard_id="growth",
            name="Growth Analysis",
            description="Growth metrics and trends analysis",
            dashboard_type=DashboardType.GROWTH,
            layout=DashboardLayout.GRID,
            widgets=growth_widgets,
            refresh_interval=300,
            theme="auto",
            permissions=["user", "admin"]
        )
        
        return dashboards
    
    def _initialize_chart_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize chart configuration templates"""
        return {
            "line": {
                "default_options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {
                        "x": {"type": "time", "time": {"unit": "day"}},
                        "y": {"beginAtZero": True}
                    },
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"mode": "index", "intersect": False}
                    }
                },
                "color_schemes": {
                    "default": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"],
                    "performance": ["#10B981", "#F59E0B", "#EF4444", "#6B7280"],
                    "growth": ["#3B82F6", "#8B5CF6", "#06B6D4", "#10B981"]
                }
            },
            "bar": {
                "default_options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {
                        "x": {"beginAtZero": True},
                        "y": {"beginAtZero": True}
                    },
                    "plugins": {
                        "legend": {"display": True},
                        "tooltip": {"mode": "index", "intersect": False}
                    }
                },
                "color_schemes": {
                    "default": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"],
                    "performance": ["#10B981", "#F59E0B", "#EF4444", "#6B7280"],
                    "warning": ["#F59E0B", "#EF4444", "#6B7280", "#3B82F6"]
                }
            },
            "pie": {
                "default_options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {"position": "bottom"},
                        "tooltip": {"callbacks": {"label": "function(context) { return context.label + ': ' + context.parsed + '%'; }"}}
                    }
                },
                "color_schemes": {
                    "default": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6"],
                    "performance": ["#10B981", "#F59E0B", "#EF4444", "#6B7280", "#3B82F6"]
                }
            },
            "gauge": {
                "default_options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {"display": False},
                        "tooltip": {"enabled": True}
                    }
                },
                "color_schemes": {
                    "default": ["#EF4444", "#F59E0B", "#10B981"],
                    "performance": ["#EF4444", "#F59E0B", "#10B981", "#3B82F6"]
                }
            },
            "metric_card": {
                "default_options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "plugins": {
                        "legend": {"display": False},
                        "tooltip": {"enabled": False}
                    }
                },
                "color_schemes": {
                    "default": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"],
                    "performance": ["#10B981", "#F59E0B", "#EF4444", "#6B7280"]
                }
            }
        }
    
    async def get_dashboard_config(
        self,
        dashboard_type: str,
        user_id: Optional[str] = None
    ) -> DashboardConfig:
        """
        Get dashboard configuration
        
        Args:
            dashboard_type: Type of dashboard to retrieve
            user_id: Optional user ID for customization
            
        Returns:
            Dashboard configuration
        """
        try:
            if dashboard_type in self.default_dashboards:
                return self.default_dashboards[dashboard_type]
            else:
                raise ValueError(f"Unknown dashboard type: {dashboard_type}")
                
        except Exception as e:
            logger.error(f"Error getting dashboard config: {e}")
            raise
    
    async def get_dashboard_data(
        self,
        dashboard_type: str,
        user_id: str,
        period: str = "monthly",
        filters: Optional[Dict[str, Any]] = None
    ) -> DashboardData:
        """
        Get dashboard data for visualization
        
        Args:
            dashboard_type: Type of dashboard
            user_id: User ID for data retrieval
            period: Time period for data
            filters: Optional filters to apply
            
        Returns:
            Dashboard data with widget information
        """
        try:
            # Get dashboard configuration
            dashboard_config = await self.get_dashboard_config(dashboard_type, user_id)
            
            # Get comprehensive KPI data
            kpi_data = await self.kpi_service.calculate_comprehensive_kpis(
                user_id, period, include_advanced=True, include_forecasts=True
            )
            
            # Process widget data
            widgets_data = {}
            for widget in dashboard_config.widgets:
                widget_data = await self._process_widget_data(
                    widget, kpi_data, user_id, period, filters
                )
                widgets_data[widget.id] = widget_data
            
            # Generate summary metrics
            summary_metrics = await self._generate_summary_metrics(kpi_data)
            
            # Generate alerts
            alerts = kpi_data.get("insights", {}).get("alerts", [])
            
            # Calculate refresh timing
            refresh_in = dashboard_config.refresh_interval
            
            return DashboardData(
                dashboard_id=dashboard_config.dashboard_id,
                timestamp=datetime.utcnow(),
                widgets_data=widgets_data,
                summary_metrics=summary_metrics,
                alerts=alerts,
                last_updated=datetime.utcnow(),
                refresh_in=refresh_in
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise
    
    async def _process_widget_data(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        user_id: str,
        period: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process data for a specific widget"""
        try:
            data_source = widget.data_source
            chart_type = widget.chart_type
            
            if data_source == "kpi_overview":
                return await self._process_kpi_overview_widget(widget, kpi_data, filters)
            elif data_source == "growth_metrics":
                return await self._process_growth_metrics_widget(widget, kpi_data, filters)
            elif data_source == "performance_summary":
                return await self._process_performance_summary_widget(widget, kpi_data, filters)
            elif data_source == "top_performers":
                return await self._process_top_performers_widget(widget, kpi_data, filters)
            elif data_source == "improvement_areas":
                return await self._process_improvement_areas_widget(widget, kpi_data, filters)
            elif data_source == "performance_metrics":
                return await self._process_performance_metrics_widget(widget, kpi_data, filters)
            elif data_source == "performance_trends":
                return await self._process_performance_trends_widget(widget, kpi_data, filters)
            elif data_source == "performance_comparison":
                return await self._process_performance_comparison_widget(widget, kpi_data, filters)
            elif data_source == "growth_overview":
                return await self._process_growth_overview_widget(widget, kpi_data, filters)
            elif data_source == "growth_velocity":
                return await self._process_growth_velocity_widget(widget, kpi_data, filters)
            elif data_source == "growth_momentum":
                return await self._process_growth_momentum_widget(widget, kpi_data, filters)
            else:
                return {"error": f"Unknown data source: {data_source}"}
                
        except Exception as e:
            logger.error(f"Error processing widget data: {e}")
            return {"error": str(e)}
    
    async def _process_kpi_overview_widget(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process KPI overview widget data"""
        try:
            metrics = widget.config.get("metrics", [])
            basic_kpis = kpi_data.get("basic", [])
            
            widget_data = {
                "chart_type": widget.chart_type.value,
                "title": widget.title,
                "description": widget.description,
                "data": []
            }
            
            for metric in metrics:
                kpi = next((k for k in basic_kpis if k["kpi_id"] == metric), None)
                if kpi:
                    widget_data["data"].append({
                        "label": kpi["name"],
                        "value": kpi["value"],
                        "target": kpi["target"],
                        "unit": kpi["unit"],
                        "status": kpi["status"].value,
                        "change_percentage": kpi["change_percentage"],
                        "trend_direction": kpi["trend_direction"]
                    })
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error processing KPI overview widget: {e}")
            return {"error": str(e)}
    
    async def _process_growth_metrics_widget(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process growth metrics widget data"""
        try:
            advanced_kpis = kpi_data.get("advanced", {})
            
            widget_data = {
                "chart_type": widget.chart_type.value,
                "title": widget.title,
                "description": widget.description,
                "data": {
                    "labels": [],
                    "datasets": []
                }
            }
            
            # Generate sample time series data for demonstration
            # In production, this would come from historical data
            time_labels = []
            growth_data = []
            target_data = []
            
            for i in range(30):  # Last 30 days
                date = datetime.utcnow() - timedelta(days=30-i)
                time_labels.append(date.strftime("%Y-%m-%d"))
                
                # Generate realistic growth data
                base_growth = 15.0  # Base growth rate
                variation = (hash(f"growth_{i}") % 100 - 50) * 0.1  # Random variation
                growth_data.append(max(0, base_growth + variation))
                target_data.append(25.0)  # 25% target from PRD
            
            widget_data["data"]["labels"] = time_labels
            widget_data["data"]["datasets"] = [
                {
                    "label": "Growth Rate",
                    "data": growth_data,
                    "borderColor": "#3B82F6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4
                },
                {
                    "label": "Target",
                    "data": target_data,
                    "borderColor": "#EF4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    "borderDash": [5, 5],
                    "tension": 0
                }
            ]
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error processing growth metrics widget: {e}")
            return {"error": str(e)}
    
    async def _process_performance_summary_widget(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process performance summary widget data"""
        try:
            performance_summary = kpi_data.get("performance_summary", {})
            distribution = performance_summary.get("performance_distribution", {})
            
            widget_data = {
                "chart_type": widget.chart_type.value,
                "title": widget.title,
                "description": widget.description,
                "data": {
                    "labels": [],
                    "datasets": [{
                        "data": [],
                        "backgroundColor": [],
                        "borderColor": []
                    }]
                }
            }
            
            # Map performance levels to colors
            color_mapping = {
                "excellent": "#10B981",
                "good": "#3B82F6",
                "average": "#F59E0B",
                "below_average": "#EF4444",
                "poor": "#6B7280"
            }
            
            for level, count in distribution.items():
                if count > 0:
                    widget_data["data"]["labels"].append(level.title())
                    widget_data["data"]["datasets"][0]["data"].append(count)
                    widget_data["data"]["datasets"][0]["backgroundColor"].append(color_mapping.get(level, "#6B7280"))
                    widget_data["data"]["datasets"][0]["borderColor"].append(color_mapping.get(level, "#6B7280"))
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error processing performance summary widget: {e}")
            return {"error": str(e)}
    
    async def _process_top_performers_widget(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process top performers widget data"""
        try:
            performance_summary = kpi_data.get("performance_summary", {})
            top_performers = performance_summary.get("top_performers", [])
            
            widget_data = {
                "chart_type": widget.chart_type.value,
                "title": widget.title,
                "description": widget.description,
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Performance Score",
                        "data": [],
                        "backgroundColor": "#10B981",
                        "borderColor": "#10B981"
                    }]
                }
            }
            
            for performer in top_performers[:5]:  # Top 5 performers
                widget_data["data"]["labels"].append(performer["kpi"].replace("_", " ").title())
                widget_data["data"]["datasets"][0]["data"].append(performer["score"])
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error processing top performers widget: {e}")
            return {"error": str(e)}
    
    async def _process_improvement_areas_widget(
        self,
        widget: DashboardWidget,
        kpi_data: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process improvement areas widget data"""
        try:
            performance_summary = kpi_data.get("performance_summary", {})
            improvement_areas = performance_summary.get("improvement_areas", [])
            
            widget_data = {
                "chart_type": widget.chart_type.value,
                "title": widget.title,
                "description": widget.description,
                "data": {
                    "labels": [],
                    "datasets": [{
                        "label": "Performance Score",
                        "data": [],
                        "backgroundColor": "#F59E0B",
                        "borderColor": "#F59E0B"
                    }]
                }
            }
            
            for area in improvement_areas[:5]:  # Top 5 improvement areas
                widget_data["data"]["labels"].append(area["kpi"].replace("_", " ").title())
                widget_data["data"]["datasets"][0]["data"].append(area["score"])
            
            return widget_data
            
        except Exception as e:
            logger.error(f"Error processing improvement areas widget: {e}")
            return {"error": str(e)}
    
    async def _generate_summary_metrics(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary metrics for dashboard"""
        try:
            performance_summary = kpi_data.get("performance_summary", {})
            insights = kpi_data.get("insights", {})
            
            return {
                "overall_score": performance_summary.get("overall_score", 0.0),
                "total_kpis": len(kpi_data.get("basic", [])),
                "on_target_kpis": len(performance_summary.get("top_performers", [])),
                "below_target_kpis": len(performance_summary.get("improvement_areas", [])),
                "alerts_count": len(insights.get("alerts", [])),
                "recommendations_count": len(insights.get("recommendations", [])),
                "opportunities_count": len(insights.get("opportunities", [])),
                "risks_count": len(insights.get("risks", []))
            }
            
        except Exception as e:
            logger.error(f"Error generating summary metrics: {e}")
            return {}
    
    async def create_custom_dashboard(
        self,
        user_id: str,
        name: str,
        description: str,
        widgets: List[Dict[str, Any]],
        layout: str = "grid",
        theme: str = "auto"
    ) -> DashboardConfig:
        """
        Create a custom dashboard for a user
        
        Args:
            user_id: User ID for the custom dashboard
            name: Dashboard name
            description: Dashboard description
            widgets: List of widget configurations
            layout: Dashboard layout
            theme: Dashboard theme
            
        Returns:
            Custom dashboard configuration
        """
        try:
            # Convert widget configurations to DashboardWidget objects
            dashboard_widgets = []
            for i, widget_config in enumerate(widgets):
                widget = DashboardWidget(
                    id=widget_config.get("id", f"custom_widget_{i}"),
                    title=widget_config.get("title", "Custom Widget"),
                    description=widget_config.get("description", ""),
                    chart_type=ChartType(widget_config.get("chart_type", "metric_card")),
                    data_source=widget_config.get("data_source", "custom"),
                    refresh_interval=widget_config.get("refresh_interval", 300),
                    size=widget_config.get("size", {"width": 6, "height": 3}),
                    position=widget_config.get("position", {"x": (i % 2) * 6, "y": (i // 2) * 3}),
                    config=widget_config.get("config", {}),
                    filters=widget_config.get("filters", []),
                    drill_down=widget_config.get("drill_down", False)
                )
                dashboard_widgets.append(widget)
            
            custom_dashboard = DashboardConfig(
                dashboard_id=f"custom_{user_id}_{int(datetime.utcnow().timestamp())}",
                name=name,
                description=description,
                dashboard_type=DashboardType.CUSTOM,
                layout=DashboardLayout(layout),
                widgets=dashboard_widgets,
                refresh_interval=300,
                theme=theme,
                permissions=[user_id]
            )
            
            # Store custom dashboard configuration
            if self.vercel_kv_service:
                await self.vercel_kv_service.store_analytics_data(
                    user_id=user_id,
                    data_type="dashboard_config",
                    source_id="custom_dashboards",
                    metric_name=custom_dashboard.dashboard_id,
                    metric_value=json.dumps(asdict(custom_dashboard)),
                    metadata={
                        "created_at": datetime.utcnow().isoformat(),
                        "dashboard_type": "custom"
                    }
                )
            
            return custom_dashboard
            
        except Exception as e:
            logger.error(f"Error creating custom dashboard: {e}")
            raise
    
    async def export_dashboard_data(
        self,
        dashboard_type: str,
        user_id: str,
        period: str = "monthly",
        format: str = "json",
        filters: Optional[Dict[str, Any]] = None
    ) -> Union[str, bytes]:
        """
        Export dashboard data in various formats
        
        Args:
            dashboard_type: Type of dashboard
            user_id: User ID for data retrieval
            period: Time period for data
            format: Export format (json, csv, pdf)
            filters: Optional filters to apply
            
        Returns:
            Exported data in requested format
        """
        try:
            dashboard_data = await self.get_dashboard_data(
                dashboard_type, user_id, period, filters
            )
            
            if format.lower() == "json":
                return json.dumps(asdict(dashboard_data), indent=2, default=str)
            elif format.lower() == "csv":
                return await self._export_to_csv(dashboard_data)
            elif format.lower() == "pdf":
                return await self._export_to_pdf(dashboard_data)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting dashboard data: {e}")
            raise
    
    async def _export_to_csv(self, dashboard_data: DashboardData) -> str:
        """Export dashboard data to CSV format"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Dashboard", "Timestamp", "Widget", "Data"])
            
            # Write data
            for widget_id, widget_data in dashboard_data.widgets_data.items():
                if "error" not in widget_data:
                    writer.writerow([
                        dashboard_data.dashboard_id,
                        dashboard_data.timestamp.isoformat(),
                        widget_id,
                        json.dumps(widget_data, default=str)
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return f"Error: {str(e)}"
    
    async def _export_to_pdf(self, dashboard_data: DashboardData) -> bytes:
        """Export dashboard data to PDF format"""
        try:
            # This would integrate with a PDF generation library
            # For now, return a placeholder
            return b"PDF export not yet implemented"
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return b"Error: PDF export failed"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the KPI dashboard service"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "KPIDashboardService",
                "components": {}
            }
            
            # Check KPI service
            try:
                kpi_health = await self.kpi_service.health_check()
                health_status["components"]["kpi_service"] = kpi_health
            except Exception as e:
                health_status["components"]["kpi_service"] = {"status": "unhealthy", "error": str(e)}
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
            logger.error(f"Error in KPI dashboard service health check: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




