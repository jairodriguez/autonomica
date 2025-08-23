import asyncio
import json
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.vercel_kv_service import VercelKVService
from app.services.kpi_calculation_service import KPICalculationService
from app.models.user import User
from app.models.analytics import AnalyticsDataPoint


class ReportType(Enum):
    """Types of reports that can be generated"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"
    PERFORMANCE = "performance"
    GROWTH = "growth"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    ROI = "roi"
    TIME_SAVINGS = "time_savings"
    COMPETITIVE = "competitive"


class ReportFormat(Enum):
    """Supported report export formats"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"
    EXCEL = "xlsx"


class ReportStatus(Enum):
    """Status of report generation"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    DELIVERED = "delivered"


@dataclass
class ReportTemplate:
    """Configuration for report templates"""
    id: str
    name: str
    description: str
    report_type: ReportType
    sections: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression for scheduling
    recipients: List[str] = field(default_factory=list)
    export_formats: List[ReportFormat] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReportJob:
    """Report generation job configuration"""
    id: str
    user_id: str
    template_id: str
    report_type: ReportType
    date_range: Dict[str, str]
    filters: Dict[str, Any] = field(default_factory=dict)
    export_formats: List[ReportFormat] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    status: ReportStatus = ReportStatus.PENDING
    progress: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_paths: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReportData:
    """Report data structure"""
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    charts: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime
    date_range: Dict[str, str]


class ReportGenerationService:
    """Service for generating customizable analytics reports"""
    
    def __init__(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        cache_service: CacheService,
        vercel_kv_service: VercelKVService,
        kpi_service: KPICalculationService
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        self.kpi_service = kpi_service
        
        # Initialize default report templates
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default report templates"""
        self.default_templates = {
            "daily_overview": ReportTemplate(
                id="daily_overview",
                name="Daily Overview",
                description="Daily summary of key metrics and performance",
                report_type=ReportType.DAILY,
                sections=["summary", "metrics", "alerts", "trends"],
                charts=["line_chart", "metric_cards"],
                metrics=["impressions", "clicks", "engagement", "conversion"],
                export_formats=[ReportFormat.JSON, ReportFormat.CSV, ReportFormat.PDF],
                schedule="0 9 * * *"  # Daily at 9 AM
            ),
            "weekly_performance": ReportTemplate(
                id="weekly_performance",
                name="Weekly Performance",
                description="Weekly performance analysis with trends",
                report_type=ReportType.WEEKLY,
                sections=["summary", "performance", "growth", "insights"],
                charts=["line_chart", "bar_chart", "pie_chart"],
                metrics=["growth_rate", "performance_score", "roi", "time_savings"],
                export_formats=[ReportFormat.JSON, ReportFormat.CSV, ReportFormat.PDF],
                schedule="0 9 * * 1"  # Weekly on Monday at 9 AM
            ),
            "monthly_analytics": ReportTemplate(
                id="monthly_analytics",
                name="Monthly Analytics",
                description="Comprehensive monthly analytics report",
                report_type=ReportType.MONTHLY,
                sections=["summary", "analytics", "trends", "forecasts", "recommendations"],
                charts=["line_chart", "area_chart", "scatter_plot", "heatmap"],
                metrics=["all_kpis", "advanced_metrics", "competitive_analysis"],
                export_formats=[ReportFormat.JSON, ReportFormat.CSV, ReportFormat.PDF, ReportFormat.EXCEL],
                schedule="0 9 1 * *"  # Monthly on 1st at 9 AM
            )
        }
    
    async def create_report_job(
        self,
        user_id: str,
        template_id: str,
        report_type: ReportType,
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None,
        export_formats: Optional[List[ReportFormat]] = None,
        recipients: Optional[List[str]] = None
    ) -> ReportJob:
        """Create a new report generation job"""
        
        # Get template
        template = self.default_templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Create job
        job = ReportJob(
            id=f"report_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            user_id=user_id,
            template_id=template_id,
            report_type=report_type,
            date_range=date_range,
            filters=filters or {},
            export_formats=export_formats or [ReportFormat.JSON],
            recipients=recipients or []
        )
        
        # Store job in Vercel KV
        await self.vercel_kv_service.store_analytics_data(
            user_id=user_id,
            data_type="report_jobs",
            source_id=job.id,
            data=job.__dict__,
            ttl=86400  # 24 hours
        )
        
        return job
    
    async def generate_report(
        self,
        user_id: str,
        job_id: str,
        template_id: str,
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ) -> ReportData:
        """Generate report data based on template and filters"""
        
        # Update job status
        await self._update_job_status(job_id, user_id, ReportStatus.GENERATING, 10)
        
        try:
            # Get template
            template = self.default_templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Collect data based on template
            await self._update_job_status(job_id, user_id, ReportStatus.GENERATING, 30)
            
            # Get KPI data
            kpi_data = await self.kpi_service.calculate_comprehensive_kpis(
                user_id=user_id,
                date_range=date_range,
                filters=filters
            )
            
            await self._update_job_status(job_id, user_id, ReportStatus.GENERATING, 60)
            
            # Generate report sections
            report_data = await self._generate_report_sections(
                template, kpi_data, date_range, filters
            )
            
            await self._update_job_status(job_id, user_id, ReportStatus.GENERATING, 90)
            
            # Create final report data
            report = ReportData(
                summary=report_data.get("summary", {}),
                metrics=report_data.get("metrics", {}),
                charts=report_data.get("charts", []),
                tables=report_data.get("tables", []),
                insights=report_data.get("insights", []),
                recommendations=report_data.get("recommendations", []),
                generated_at=datetime.utcnow(),
                date_range=date_range
            )
            
            await self._update_job_status(job_id, user_id, ReportStatus.COMPLETED, 100)
            
            return report
            
        except Exception as e:
            await self._update_job_status(
                job_id, user_id, ReportStatus.FAILED, 0, str(e)
            )
            raise
    
    async def _generate_report_sections(
        self,
        template: ReportTemplate,
        kpi_data: Dict[str, Any],
        date_range: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate individual report sections based on template"""
        
        sections = {}
        
        # Summary section
        if "summary" in template.sections:
            sections["summary"] = await self._generate_summary_section(kpi_data, date_range)
        
        # Metrics section
        if "metrics" in template.sections:
            sections["metrics"] = await self._generate_metrics_section(template.metrics, kpi_data)
        
        # Performance section
        if "performance" in template.sections:
            sections["performance"] = await self._generate_performance_section(kpi_data)
        
        # Growth section
        if "growth" in template.sections:
            sections["growth"] = await self._generate_growth_section(kpi_data)
        
        # Insights section
        if "insights" in template.sections:
            sections["insights"] = await self._generate_insights_section(kpi_data)
        
        # Recommendations section
        if "recommendations" in template.sections:
            sections["recommendations"] = await self._generate_recommendations_section(kpi_data)
        
        # Charts section
        if template.charts:
            sections["charts"] = await self._generate_charts_section(template.charts, kpi_data)
        
        # Tables section
        sections["tables"] = await self._generate_tables_section(kpi_data)
        
        return sections
    
    async def _generate_summary_section(
        self,
        kpi_data: Dict[str, Any],
        date_range: Dict[str, str]
    ) -> Dict[str, Any]:
        """Generate summary section with key highlights"""
        
        performance_summary = kpi_data.get("performance_summary", {})
        
        return {
            "overall_score": performance_summary.get("overall_score", 0),
            "performance_level": performance_summary.get("performance_level", "unknown"),
            "top_performers": performance_summary.get("top_performers", []),
            "improvement_areas": performance_summary.get("improvement_areas", []),
            "date_range": date_range,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_metrics_section(
        self,
        requested_metrics: List[str],
        kpi_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metrics section with requested KPIs"""
        
        metrics = {}
        basic_kpis = kpi_data.get("basic_kpis", {})
        advanced_kpis = kpi_data.get("advanced_kpis", {})
        
        for metric in requested_metrics:
            if metric == "all_kpis":
                metrics.update(basic_kpis)
                metrics.update(advanced_kpis)
            elif metric in basic_kpis:
                metrics[metric] = basic_kpis[metric]
            elif metric in advanced_kpis:
                metrics[metric] = advanced_kpis[metric]
        
        return metrics
    
    async def _generate_performance_section(
        self,
        kpi_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate performance analysis section"""
        
        performance_summary = kpi_data.get("performance_summary", {})
        bi_insights = kpi_data.get("bi_insights", {})
        
        return {
            "performance_distribution": performance_summary.get("performance_distribution", {}),
            "top_performers": performance_summary.get("top_performers", []),
            "improvement_areas": performance_summary.get("improvement_areas", []),
            "alerts": bi_insights.get("alerts", []),
            "trends": bi_insights.get("trends", [])
        }
    
    async def _generate_growth_section(
        self,
        kpi_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate growth analysis section"""
        
        growth_metrics = kpi_data.get("growth_metrics", {})
        
        return {
            "overall_growth": growth_metrics.get("overall_growth", {}),
            "metric_growth": growth_metrics.get("metric_growth", {}),
            "target_achievement": growth_metrics.get("target_achievement", {}),
            "growth_velocity": growth_metrics.get("growth_velocity", {}),
            "momentum": growth_metrics.get("momentum", {})
        }
    
    async def _generate_insights_section(
        self,
        kpi_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate business intelligence insights"""
        
        bi_insights = kpi_data.get("bi_insights", {})
        
        return {
            "performance_analysis": bi_insights.get("performance_analysis", ""),
            "trend_analysis": bi_insights.get("trend_analysis", ""),
            "opportunities": bi_insights.get("opportunities", []),
            "risks": bi_insights.get("risks", [])
        }
    
    async def _generate_recommendations_section(
        self,
        kpi_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        
        bi_insights = kpi_data.get("bi_insights", {})
        
        return {
            "recommendations": bi_insights.get("recommendations", []),
            "priority": "high",  # Could be calculated based on impact
            "estimated_impact": "medium",  # Could be calculated
            "implementation_effort": "low"  # Could be calculated
        }
    
    async def _generate_charts_section(
        self,
        chart_types: List[str],
        kpi_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate chart data for visualization"""
        
        charts = []
        
        for chart_type in chart_types:
            if chart_type == "line_chart":
                charts.append(await self._generate_line_chart_data(kpi_data))
            elif chart_type == "bar_chart":
                charts.append(await self._generate_bar_chart_data(kpi_data))
            elif chart_type == "pie_chart":
                charts.append(await self._generate_pie_chart_data(kpi_data))
            elif chart_type == "metric_cards":
                charts.append(await self._generate_metric_cards_data(kpi_data))
        
        return charts
    
    async def _generate_line_chart_data(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate line chart data for trends"""
        
        return {
            "type": "line",
            "title": "Performance Trends",
            "data": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "datasets": [
                    {
                        "label": "Overall Score",
                        "data": [75, 78, 82, 85],
                        "borderColor": "#3B82F6",
                        "backgroundColor": "rgba(59, 130, 246, 0.1)"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {"beginAtZero": True, "max": 100}
                }
            }
        }
    
    async def _generate_bar_chart_data(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bar chart data for comparisons"""
        
        return {
            "type": "bar",
            "title": "KPI Performance",
            "data": {
                "labels": ["Impressions", "Engagement", "Conversion", "Quality"],
                "datasets": [
                    {
                        "label": "Current",
                        "data": [85, 78, 72, 88],
                        "backgroundColor": "#10B981"
                    },
                    {
                        "label": "Target",
                        "data": [75, 70, 65, 80],
                        "backgroundColor": "#F59E0B"
                    }
                ]
            }
        }
    
    async def _generate_pie_chart_data(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pie chart data for distribution"""
        
        return {
            "type": "pie",
            "title": "Performance Distribution",
            "data": {
                "labels": ["Excellent", "Good", "Average", "Below Average", "Poor"],
                "datasets": [
                    {
                        "data": [25, 35, 25, 10, 5],
                        "backgroundColor": [
                            "#10B981", "#3B82F6", "#F59E0B", "#EF4444", "#6B7280"
                        ]
                    }
                ]
            }
        }
    
    async def _generate_metric_cards_data(self, kpi_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metric cards data for key indicators"""
        
        basic_kpis = kpi_data.get("basic_kpis", {})
        
        return {
            "type": "metric_cards",
            "title": "Key Performance Indicators",
            "metrics": [
                {
                    "name": "Impressions Growth",
                    "value": basic_kpis.get("impressions_growth", {}).get("growth", 0),
                    "change": "+12%",
                    "status": "positive"
                },
                {
                    "name": "Engagement Rate",
                    "value": basic_kpis.get("engagement_rate", {}).get("current", 0),
                    "change": "+5%",
                    "status": "positive"
                },
                {
                    "name": "Conversion Rate",
                    "value": basic_kpis.get("conversion_rate", {}).get("current", 0),
                    "change": "+3%",
                    "status": "positive"
                }
            ]
        }
    
    async def _generate_tables_section(self, kpi_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate tables section with detailed data"""
        
        tables = []
        
        # KPI Summary Table
        basic_kpis = kpi_data.get("basic_kpis", {})
        kpi_table = {
            "title": "KPI Summary",
            "headers": ["Metric", "Current", "Previous", "Change", "Target", "Status"],
            "rows": []
        }
        
        for kpi_name, kpi_data in basic_kpis.items():
            if isinstance(kpi_data, dict):
                row = [
                    kpi_name.replace("_", " ").title(),
                    kpi_data.get("current", 0),
                    kpi_data.get("previous", 0),
                    f"{kpi_data.get('change', 0):.1f}%",
                    kpi_data.get("target", 0),
                    kpi_data.get("status", "unknown")
                ]
                kpi_table["rows"].append(row)
        
        tables.append(kpi_table)
        
        # Performance Summary Table
        performance_summary = kpi_data.get("performance_summary", {})
        perf_table = {
            "title": "Performance Summary",
            "headers": ["Category", "Score", "Level", "Trend"],
            "rows": [
                ["Overall Performance", performance_summary.get("overall_score", 0), 
                 performance_summary.get("performance_level", "unknown"), "↗️"],
                ["Top Performers", len(performance_summary.get("top_performers", [])), 
                 "Good", "↗️"],
                ["Improvement Areas", len(performance_summary.get("improvement_areas", [])), 
                 "Needs Attention", "↘️"]
            ]
        }
        
        tables.append(perf_table)
        
        return tables
    
    async def export_report(
        self,
        report_data: ReportData,
        export_format: ReportFormat,
        user_id: str
    ) -> Union[str, bytes]:
        """Export report data in specified format"""
        
        if export_format == ReportFormat.JSON:
            return await self._export_to_json(report_data)
        elif export_format == ReportFormat.CSV:
            return await self._export_to_csv(report_data)
        elif export_format == ReportFormat.PDF:
            return await self._export_to_pdf(report_data)
        elif export_format == ReportFormat.HTML:
            return await self._export_to_html(report_data)
        else:
            raise ValueError(f"Export format {export_format} not supported")
    
    async def _export_to_json(self, report_data: ReportData) -> str:
        """Export report to JSON format"""
        
        # Convert datetime objects to strings for JSON serialization
        export_data = {
            "summary": report_data.summary,
            "metrics": report_data.metrics,
            "charts": report_data.charts,
            "tables": report_data.tables,
            "insights": report_data.insights,
            "recommendations": report_data.recommendations,
            "generated_at": report_data.generated_at.isoformat(),
            "date_range": report_data.date_range
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    async def _export_to_csv(self, report_data: ReportData) -> str:
        """Export report to CSV format"""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write summary
        writer.writerow(["SUMMARY"])
        writer.writerow(["Metric", "Value"])
        for key, value in report_data.summary.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # Write metrics
        writer.writerow(["METRICS"])
        writer.writerow(["Metric", "Value"])
        for key, value in report_data.metrics.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # Write insights
        writer.writerow(["INSIGHTS"])
        for insight in report_data.insights:
            writer.writerow([insight])
        
        writer.writerow([])
        
        # Write recommendations
        writer.writerow(["RECOMMENDATIONS"])
        for rec in report_data.recommendations:
            writer.writerow([rec])
        
        return output.getvalue()
    
    async def _export_to_pdf(self, report_data: ReportData) -> bytes:
        """Export report to PDF format (placeholder implementation)"""
        
        # This is a placeholder - in production, you'd use a library like reportlab
        # or weasyprint to generate actual PDFs
        
        pdf_content = f"""
        ANALYTICS REPORT
        
        Generated: {report_data.generated_at}
        Date Range: {report_data.date_range.get('start', 'N/A')} to {report_data.date_range.get('end', 'N/A')}
        
        SUMMARY:
        {json.dumps(report_data.summary, indent=2)}
        
        INSIGHTS:
        {chr(10).join(report_data.insights)}
        
        RECOMMENDATIONS:
        {chr(10).join(report_data.recommendations)}
        """
        
        return pdf_content.encode('utf-8')
    
    async def _export_to_html(self, report_data: ReportData) -> str:
        """Export report to HTML format"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e9ecef; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Analytics Report</h1>
                <p>Generated: {report_data.generated_at}</p>
                <p>Date Range: {report_data.date_range.get('start', 'N/A')} to {report_data.date_range.get('end', 'N/A')}</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <div class="metrics">
                    {''.join([f'<div class="metric"><strong>{k}:</strong> {v}</div>' for k, v in report_data.summary.items()])}
                </div>
            </div>
            
            <div class="section">
                <h2>Insights</h2>
                <ul>
                    {''.join([f'<li>{insight}</li>' for insight in report_data.insights])}
                </ul>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in report_data.recommendations])}
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    async def _update_job_status(
        self,
        job_id: str,
        user_id: str,
        status: ReportStatus,
        progress: int,
        error_message: Optional[str] = None
    ):
        """Update job status and progress"""
        
        # Get current job
        job_data = await self.vercel_kv_service.get_analytics_data(
            user_id=user_id,
            data_type="report_jobs",
            source_id=job_id
        )
        
        if job_data:
            job = ReportJob(**job_data)
            job.status = status
            job.progress = progress
            
            if status == ReportStatus.GENERATING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status == ReportStatus.COMPLETED:
                job.completed_at = datetime.utcnow()
            elif status == ReportStatus.FAILED:
                job.error_message = error_message
            
            # Update job in storage
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="report_jobs",
                source_id=job_id,
                data=job.__dict__,
                ttl=86400
            )
    
    async def get_report_jobs(
        self,
        user_id: str,
        status: Optional[ReportStatus] = None
    ) -> List[ReportJob]:
        """Get report jobs for a user"""
        
        # Get all jobs for user
        jobs_data = await self.vercel_kv_service.get_analytics_data(
            user_id=user_id,
            data_type="report_jobs"
        )
        
        jobs = []
        for job_data in jobs_data:
            if isinstance(job_data, dict):
                job = ReportJob(**job_data)
                if status is None or job.status == status:
                    jobs.append(job)
        
        # Sort by creation date (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return jobs
    
    async def get_report_templates(self) -> List[ReportTemplate]:
        """Get available report templates"""
        
        return list(self.default_templates.values())
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        
        try:
            # Test Vercel KV connection
            kv_health = await self.vercel_kv_service.health_check()
            
            # Test KPI service
            kpi_health = await self.kpi_service.health_check()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "vercel_kv": kv_health,
                    "kpi_service": kpi_health
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




