import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path

from .content_analytics import ContentAnalyticsService, ReportType, AnalyticsReport
from .content_types import ContentType, Platform

logger = logging.getLogger(__name__)

class ScheduleType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"

class ReportStatus(str, Enum):
    SCHEDULED = "scheduled"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    DELIVERED = "delivered"

@dataclass
class ReportSchedule:
    schedule_id: str
    name: str
    description: str
    schedule_type: ScheduleType
    report_type: ReportType
    recipients: List[str]
    format: ReportFormat
    include_recommendations: bool = True
    custom_interval_days: Optional[int] = None
    last_generated: Optional[datetime] = None
    next_generation: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

@dataclass
class ReportDelivery:
    delivery_id: str
    report_id: str
    schedule_id: str
    delivery_method: str
    recipient: str
    status: ReportStatus
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class ContentReportingService:
    def __init__(self, analytics_service: ContentAnalyticsService):
        self.analytics_service = analytics_service
        self.schedules: Dict[str, ReportSchedule] = {}
        self.deliveries: List[ReportDelivery] = []
        self.reports_directory = Path("reports")
        self._initialize_service()
        
    def _initialize_service(self):
        """Initialize the reporting service with default configurations"""
        # Create reports directory
        self.reports_directory.mkdir(exist_ok=True)
        
        # Create default schedules
        self._create_default_schedules()
        
        logger.info("Content reporting service initialized")

    def _create_default_schedules(self):
        """Create default reporting schedules"""
        default_schedules = [
            {
                "schedule_id": "daily_summary",
                "name": "Daily Content Summary",
                "description": "Daily overview of content performance and engagement",
                "schedule_type": ScheduleType.DAILY,
                "report_type": ReportType.DAILY,
                "recipients": ["content-team@company.com"],
                "format": ReportFormat.HTML,
                "include_recommendations": True
            },
            {
                "schedule_id": "weekly_analysis",
                "name": "Weekly Content Analysis",
                "description": "Weekly deep dive into content performance trends",
                "schedule_type": ScheduleType.WEEKLY,
                "report_type": ReportType.WEEKLY,
                "recipients": ["content-team@company.com", "marketing@company.com"],
                "format": ReportFormat.PDF,
                "include_recommendations": True
            },
            {
                "schedule_id": "monthly_executive",
                "name": "Monthly Executive Summary",
                "description": "Monthly high-level content performance overview",
                "schedule_type": ScheduleType.MONTHLY,
                "report_type": ReportType.MONTHLY,
                "recipients": ["executives@company.com"],
                "format": ReportFormat.PDF,
                "include_recommendations": False
            }
        ]
        
        for schedule_data in default_schedules:
            schedule = ReportSchedule(
                schedule_id=schedule_data["schedule_id"],
                name=schedule_data["name"],
                description=schedule_data["description"],
                schedule_type=schedule_data["schedule_type"],
                report_type=schedule_data["report_type"],
                recipients=schedule_data["recipients"],
                format=schedule_data["format"],
                include_recommendations=schedule_data["include_recommendations"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.schedules[schedule.schedule_id] = schedule
            self._calculate_next_generation(schedule)

    def _calculate_next_generation(self, schedule: ReportSchedule):
        """Calculate when the next report should be generated"""
        now = datetime.now()
        
        if schedule.last_generated is None:
            # First generation - start immediately
            schedule.next_generation = now
            return
        
        if schedule.schedule_type == ScheduleType.DAILY:
            schedule.next_generation = schedule.last_generated + timedelta(days=1)
        elif schedule.schedule_type == ScheduleType.WEEKLY:
            schedule.next_generation = schedule.last_generated + timedelta(weeks=1)
        elif schedule.schedule_type == ScheduleType.MONTHLY:
            schedule.next_generation = schedule.last_generated + timedelta(days=30)
        elif schedule.schedule_type == ScheduleType.QUARTERLY:
            schedule.next_generation = schedule.last_generated + timedelta(days=90)
        elif schedule.schedule_type == ScheduleType.YEARLY:
            schedule.next_generation = schedule.last_generated + timedelta(days=365)
        elif schedule.schedule_type == ScheduleType.CUSTOM and schedule.custom_interval_days:
            schedule.next_generation = schedule.last_generated + timedelta(days=schedule.custom_interval_days)
        
        # Ensure next generation is in the future
        while schedule.next_generation <= now:
            if schedule.schedule_type == ScheduleType.DAILY:
                schedule.next_generation += timedelta(days=1)
            elif schedule.schedule_type == ScheduleType.WEEKLY:
                schedule.next_generation += timedelta(weeks=1)
            elif schedule.schedule_type == ScheduleType.MONTHLY:
                schedule.next_generation += timedelta(days=30)
            elif schedule.schedule_type == ScheduleType.QUARTERLY:
                schedule.next_generation += timedelta(days=90)
            elif schedule.schedule_type == ScheduleType.YEARLY:
                schedule.next_generation += timedelta(days=365)
            elif schedule.schedule_type == ScheduleType.CUSTOM and schedule.custom_interval_days:
                schedule.next_generation += timedelta(days=schedule.custom_interval_days)

    async def create_schedule(self, name: str, description: str, schedule_type: ScheduleType,
                            report_type: ReportType, recipients: List[str], format: ReportFormat,
                            include_recommendations: bool = True, custom_interval_days: Optional[int] = None) -> ReportSchedule:
        """Create a new report schedule"""
        try:
            schedule_id = f"schedule_{schedule_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            schedule = ReportSchedule(
                schedule_id=schedule_id,
                name=name,
                description=description,
                schedule_type=schedule_type,
                report_type=report_type,
                recipients=recipients,
                format=format,
                include_recommendations=include_recommendations,
                custom_interval_days=custom_interval_days,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self._calculate_next_generation(schedule)
            self.schedules[schedule_id] = schedule
            
            logger.info(f"Created report schedule: {schedule_id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating report schedule: {e}")
            raise

    async def update_schedule(self, schedule_id: str, **kwargs) -> bool:
        """Update an existing report schedule"""
        try:
            if schedule_id not in self.schedules:
                raise ValueError(f"Schedule {schedule_id} not found")
            
            schedule = self.schedules[schedule_id]
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            schedule.updated_at = datetime.now()
            
            # Recalculate next generation if schedule type changed
            if 'schedule_type' in kwargs or 'custom_interval_days' in kwargs:
                self._calculate_next_generation(schedule)
            
            logger.info(f"Updated report schedule: {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating report schedule: {e}")
            return False

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a report schedule"""
        try:
            if schedule_id not in self.schedules:
                return False
            
            del self.schedules[schedule_id]
            logger.info(f"Deleted report schedule: {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting report schedule: {e}")
            return False

    async def get_schedules(self, active_only: bool = True) -> List[ReportSchedule]:
        """Get all report schedules"""
        schedules = list(self.schedules.values())
        
        if active_only:
            schedules = [s for s in schedules if s.is_active]
        
        return sorted(schedules, key=lambda x: x.next_generation or datetime.max)

    async def generate_scheduled_reports(self) -> List[str]:
        """Generate reports for all due schedules"""
        try:
            generated_reports = []
            now = datetime.now()
            
            for schedule in self.schedules.values():
                if not schedule.is_active:
                    continue
                
                if schedule.next_generation and schedule.next_generation <= now:
                    try:
                        report = await self._generate_scheduled_report(schedule)
                        if report:
                            generated_reports.append(report.report_id)
                            
                            # Update schedule
                            schedule.last_generated = now
                            self._calculate_next_generation(schedule)
                            
                            # Deliver report
                            await self._deliver_report(report, schedule)
                            
                    except Exception as e:
                        logger.error(f"Error generating scheduled report for {schedule.schedule_id}: {e}")
                        # Mark delivery as failed
                        await self._record_delivery_failure(schedule.schedule_id, str(e))
            
            return generated_reports
            
        except Exception as e:
            logger.error(f"Error generating scheduled reports: {e}")
            return []

    async def _generate_scheduled_report(self, schedule: ReportSchedule) -> Optional[AnalyticsReport]:
        """Generate a report for a specific schedule"""
        try:
            # Calculate date range based on schedule type
            end_date = datetime.now()
            
            if schedule.schedule_type == ScheduleType.DAILY:
                start_date = end_date - timedelta(days=1)
            elif schedule.schedule_type == ScheduleType.WEEKLY:
                start_date = end_date - timedelta(weeks=1)
            elif schedule.schedule_type == ScheduleType.MONTHLY:
                start_date = end_date - timedelta(days=30)
            elif schedule.schedule_type == ScheduleType.QUARTERLY:
                start_date = end_date - timedelta(days=90)
            elif schedule.schedule_type == ScheduleType.YEARLY:
                start_date = end_date - timedelta(days=365)
            elif schedule.schedule_type == ScheduleType.CUSTOM and schedule.custom_interval_days:
                start_date = end_date - timedelta(days=schedule.custom_interval_days)
            else:
                start_date = end_date - timedelta(days=1)
            
            # Generate report using analytics service
            report = await self.analytics_service.generate_report(
                report_type=schedule.report_type,
                start_date=start_date,
                end_date=end_date,
                include_recommendations=schedule.include_recommendations
            )
            
            # Save report to file system
            await self._save_report_to_file(report, schedule.format)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating scheduled report: {e}")
            return None

    async def _save_report_to_file(self, report: AnalyticsReport, format: ReportFormat):
        """Save report to file system"""
        try:
            # Create format-specific directory
            format_dir = self.reports_directory / format.value
            format_dir.mkdir(exist_ok=True)
            
            # Generate filename
            filename = f"{report.report_id}_{report.generated_at.strftime('%Y%m%d_%H%M%S')}.{format.value}"
            filepath = format_dir / filename
            
            # Save based on format
            if format == ReportFormat.JSON:
                with open(filepath, 'w') as f:
                    json.dump(asdict(report), f, default=str, indent=2)
            elif format == ReportFormat.CSV:
                csv_content = await self._convert_report_to_csv(report)
                with open(filepath, 'w') as f:
                    f.write(csv_content)
            elif format == ReportFormat.HTML:
                html_content = await self._convert_report_to_html(report)
                with open(filepath, 'w') as f:
                    f.write(html_content)
            else:
                # For other formats, save as JSON for now
                with open(filepath, 'w') as f:
                    json.dump(asdict(report), f, default=str, indent=2)
            
            logger.info(f"Saved report to file: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving report to file: {e}")
            raise

    async def _convert_report_to_csv(self, report: AnalyticsReport) -> str:
        """Convert report to CSV format"""
        csv_lines = []
        
        # Header
        csv_lines.append("Report ID,Report Type,Start Date,End Date,Generated At")
        csv_lines.append(f"{report.report_id},{report.report_type},{report.start_date.date()},{report.end_date.date()},{report.generated_at}")
        csv_lines.append("")
        
        # Metrics Summary
        csv_lines.append("Metrics Summary")
        csv_lines.append("Metric,Value")
        for key, value in report.metrics_summary.items():
            if isinstance(value, (dict, list)):
                csv_lines.append(f"{key},Complex Data")
            else:
                csv_lines.append(f"{key},{value}")
        csv_lines.append("")
        
        # Top Performing Content
        csv_lines.append("Top Performing Content")
        csv_lines.append("Content ID,Title,Content Type,Platform,Performance Score")
        for content in report.top_performing_content[:10]:  # Top 10
            csv_lines.append(f"{content.content_id},{content.title},{content.content_type},{content.platform},{content.performance_score}")
        csv_lines.append("")
        
        # Recommendations
        csv_lines.append("Recommendations")
        for i, rec in enumerate(report.recommendations, 1):
            csv_lines.append(f"{i},{rec}")
        
        return "\n".join(csv_lines)

    async def _convert_report_to_html(self, report: AnalyticsReport) -> str:
        """Convert report to HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Content Analytics Report - {report.report_type}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .recommendation {{ background-color: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Content Analytics Report</h1>
                <p><strong>Report Type:</strong> {report.report_type}</p>
                <p><strong>Date Range:</strong> {report.start_date.date()} to {report.end_date.date()}</p>
                <p><strong>Generated:</strong> {report.generated_at}</p>
            </div>
            
            <div class="section">
                <h2>Metrics Summary</h2>
                <div class="metric">
                    <strong>Total Content:</strong> {report.metrics_summary.get('total_content', 0)}
                </div>
                <div class="metric">
                    <strong>Average Performance:</strong> {report.metrics_summary.get('average_performance', 0)}
                </div>
            </div>
            
            <div class="section">
                <h2>Top Performing Content</h2>
                <table>
                    <tr>
                        <th>Content ID</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Platform</th>
                        <th>Performance Score</th>
                    </tr>
        """
        
        for content in report.top_performing_content[:10]:
            html_content += f"""
                    <tr>
                        <td>{content.content_id}</td>
                        <td>{content.title}</td>
                        <td>{content.content_type}</td>
                        <td>{content.platform}</td>
                        <td>{content.performance_score}</td>
                    </tr>
            """
        
        html_content += """
                </table>
            </div>
            
            <div class="section">
                <h2>Recommendations</h2>
        """
        
        for rec in report.recommendations:
            html_content += f'<div class="recommendation">{rec}</div>'
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return html_content

    async def _deliver_report(self, report: AnalyticsReport, schedule: ReportSchedule):
        """Deliver report to all recipients"""
        try:
            for recipient in schedule.recipients:
                delivery = ReportDelivery(
                    delivery_id=f"delivery_{report.report_id}_{recipient}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    report_id=report.report_id,
                    schedule_id=schedule.schedule_id,
                    delivery_method="file",  # Default to file delivery
                    recipient=recipient,
                    status=ReportStatus.COMPLETED,
                    delivered_at=datetime.now(),
                    metadata={"format": schedule.format.value}
                )
                
                self.deliveries.append(delivery)
                
                # Try to deliver via appropriate method
                if schedule.format == ReportFormat.HTML:
                    await self._deliver_via_file(report, recipient, schedule)
                else:
                    await self._deliver_via_file(report, recipient, schedule)
                
                delivery.status = ReportStatus.DELIVERED
                
        except Exception as e:
            logger.error(f"Error delivering report: {e}")
            await self._record_delivery_failure(schedule.schedule_id, str(e))

    async def _deliver_via_file(self, report: AnalyticsReport, recipient: str, schedule: ReportSchedule):
        """Deliver report via file system"""
        # For now, just log the delivery
        logger.info(f"Report {report.report_id} delivered to {recipient} via file system")

    async def _record_delivery_failure(self, schedule_id: str, error_message: str):
        """Record a delivery failure"""
        delivery = ReportDelivery(
            delivery_id=f"failed_delivery_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            report_id="",
            schedule_id=schedule_id,
            delivery_method="unknown",
            recipient="",
            status=ReportStatus.FAILED,
            error_message=error_message,
            metadata={}
        )
        
        self.deliveries.append(delivery)

    async def get_delivery_history(self, schedule_id: Optional[str] = None, 
                                 status: Optional[ReportStatus] = None) -> List[ReportDelivery]:
        """Get delivery history"""
        deliveries = self.deliveries
        
        if schedule_id:
            deliveries = [d for d in deliveries if d.schedule_id == schedule_id]
        
        if status:
            deliveries = [d for d in deliveries if d.status == status]
        
        return sorted(deliveries, key=lambda x: x.delivered_at or datetime.min, reverse=True)

    async def start_scheduler(self):
        """Start the automated report scheduler"""
        try:
            logger.info("Starting automated report scheduler")
            
            while True:
                # Generate scheduled reports
                generated = await self.generate_scheduled_reports()
                if generated:
                    logger.info(f"Generated {len(generated)} scheduled reports")
                
                # Wait for next check (every hour)
                await asyncio.sleep(3600)
                
        except Exception as e:
            logger.error(f"Error in report scheduler: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check reporting service health"""
        try:
            active_schedules = len([s for s in self.schedules.values() if s.is_active])
            total_deliveries = len(self.deliveries)
            successful_deliveries = len([d for d in self.deliveries if d.status == ReportStatus.DELIVERED])
            
            return {
                "status": "healthy",
                "active_schedules": active_schedules,
                "total_schedules": len(self.schedules),
                "total_deliveries": total_deliveries,
                "successful_deliveries": successful_deliveries,
                "delivery_success_rate": successful_deliveries / total_deliveries if total_deliveries > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
