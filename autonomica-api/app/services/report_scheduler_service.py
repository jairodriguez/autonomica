import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import croniter

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.vercel_kv_service import VercelKVService
from app.services.report_generation_service import ReportGenerationService, ReportType, ReportStatus
from app.models.user import User


class ScheduleStatus(Enum):
    """Status of scheduled reports"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class DeliveryMethod(Enum):
    """Methods for delivering reports"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    STORAGE = "storage"
    API = "api"


@dataclass
class ReportSchedule:
    """Configuration for scheduled report generation"""
    id: str
    user_id: str
    template_id: str
    name: str
    description: str
    cron_expression: str
    timezone: str = "UTC"
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    delivery_methods: List[DeliveryMethod] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    webhook_url: Optional[str] = None
    storage_path: Optional[str] = None
    export_formats: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0


@dataclass
class ScheduledReport:
    """A scheduled report instance"""
    schedule_id: str
    user_id: str
    template_id: str
    scheduled_time: datetime
    status: ReportStatus = ReportStatus.PENDING
    report_data: Optional[Dict[str, Any]] = None
    generated_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportSchedulerService:
    """Service for scheduling and managing automated report generation"""
    
    def __init__(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        cache_service: CacheService,
        vercel_kv_service: VercelKVService,
        report_service: ReportGenerationService
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        self.report_service = report_service
        
        # Initialize default schedules
        self._initialize_default_schedules()
    
    def _initialize_default_schedules(self):
        """Initialize default report schedules"""
        self.default_schedules = {
            "daily_overview": ReportSchedule(
                id="daily_overview_default",
                user_id="system",
                template_id="daily_overview",
                name="Daily Overview Report",
                description="Automated daily overview report",
                cron_expression="0 9 * * *",  # Daily at 9 AM
                timezone="UTC",
                delivery_methods=[DeliveryMethod.STORAGE],
                export_formats=["json", "pdf"],
                filters={}
            ),
            "weekly_performance": ReportSchedule(
                id="weekly_performance_default",
                user_id="system",
                template_id="weekly_performance",
                name="Weekly Performance Report",
                description="Automated weekly performance analysis",
                cron_expression="0 9 * * 1",  # Weekly on Monday at 9 AM
                timezone="UTC",
                delivery_methods=[DeliveryMethod.STORAGE, DeliveryMethod.EMAIL],
                export_formats=["json", "pdf", "csv"],
                filters={}
            ),
            "monthly_analytics": ReportSchedule(
                id="monthly_analytics_default",
                user_id="system",
                template_id="monthly_analytics",
                name="Monthly Analytics Report",
                description="Comprehensive monthly analytics report",
                cron_expression="0 9 1 * *",  # Monthly on 1st at 9 AM
                timezone="UTC",
                delivery_methods=[DeliveryMethod.STORAGE, DeliveryMethod.EMAIL],
                export_formats=["json", "pdf", "csv", "excel"],
                filters={}
            )
        }
    
    async def create_schedule(
        self,
        user_id: str,
        template_id: str,
        name: str,
        description: str,
        cron_expression: str,
        timezone: str = "UTC",
        delivery_methods: Optional[List[DeliveryMethod]] = None,
        recipients: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        storage_path: Optional[str] = None,
        export_formats: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> ReportSchedule:
        """Create a new report schedule"""
        
        # Validate cron expression
        try:
            croniter.croniter(cron_expression)
        except ValueError as e:
            raise ValueError(f"Invalid cron expression: {e}")
        
        # Create schedule
        schedule = ReportSchedule(
            id=f"schedule_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            user_id=user_id,
            template_id=template_id,
            name=name,
            description=description,
            cron_expression=cron_expression,
            timezone=timezone,
            delivery_methods=delivery_methods or [DeliveryMethod.STORAGE],
            recipients=recipients or [],
            webhook_url=webhook_url,
            storage_path=storage_path,
            export_formats=export_formats or ["json"],
            filters=filters or {}
        )
        
        # Calculate next run time
        schedule.next_run = self._calculate_next_run(schedule.cron_expression, schedule.timezone)
        
        # Store schedule in Vercel KV
        await self.vercel_kv_service.store_analytics_data(
            user_id=user_id,
            data_type="report_schedules",
            source_id=schedule.id,
            data=schedule.__dict__,
            ttl=0  # No expiration for schedules
        )
        
        return schedule
    
    async def update_schedule(
        self,
        user_id: str,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> ReportSchedule:
        """Update an existing report schedule"""
        
        # Get current schedule
        schedule_data = await self.vercel_kv_service.get_analytics_data(
            user_id=user_id,
            data_type="report_schedules",
            source_id=schedule_id
        )
        
        if not schedule_data:
            raise ValueError(f"Schedule {schedule_id} not found")
        
        schedule = ReportSchedule(**schedule_data)
        
        # Update fields
        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        # Recalculate next run if cron expression changed
        if "cron_expression" in updates:
            try:
                croniter.croniter(schedule.cron_expression)
                schedule.next_run = self._calculate_next_run(schedule.cron_expression, schedule.timezone)
            except ValueError as e:
                raise ValueError(f"Invalid cron expression: {e}")
        
        schedule.updated_at = datetime.utcnow()
        
        # Store updated schedule
        await self.vercel_kv_service.store_analytics_data(
            user_id=user_id,
            data_type="report_schedules",
            source_id=schedule_id,
            data=schedule.__dict__,
            ttl=0
        )
        
        return schedule
    
    async def delete_schedule(self, user_id: str, schedule_id: str) -> bool:
        """Delete a report schedule"""
        
        try:
            await self.vercel_kv_service.delete_analytics_data(
                user_id=user_id,
                data_type="report_schedules",
                source_id=schedule_id
            )
            return True
        except Exception:
            return False
    
    async def pause_schedule(self, user_id: str, schedule_id: str) -> ReportSchedule:
        """Pause a report schedule"""
        
        return await self.update_schedule(
            user_id=user_id,
            schedule_id=schedule_id,
            updates={"status": ScheduleStatus.PAUSED}
        )
    
    async def resume_schedule(self, user_id: str, schedule_id: str) -> ReportSchedule:
        """Resume a paused report schedule"""
        
        schedule = await self.update_schedule(
            user_id=user_id,
            schedule_id=schedule_id,
            updates={"status": ScheduleStatus.ACTIVE}
        )
        
        # Recalculate next run time
        schedule.next_run = self._calculate_next_run(schedule.cron_expression, schedule.timezone)
        
        await self.vercel_kv_service.store_analytics_data(
            user_id=user_id,
            data_type="report_schedules",
            source_id=schedule_id,
            data=schedule.__dict__,
            ttl=0
        )
        
        return schedule
    
    async def get_schedules(
        self,
        user_id: str,
        status: Optional[ScheduleStatus] = None
    ) -> List[ReportSchedule]:
        """Get report schedules for a user"""
        
        # Get all schedules for user
        schedules_data = await self.vercel_kv_service.get_analytics_data(
            user_id=user_id,
            data_type="report_schedules"
        )
        
        schedules = []
        for schedule_data in schedules_data:
            if isinstance(schedule_data, dict):
                schedule = ReportSchedule(**schedule_data)
                if status is None or schedule.status == status:
                    schedules.append(schedule)
        
        # Sort by next run time
        schedules.sort(key=lambda x: x.next_run or datetime.max)
        
        return schedules
    
    async def get_due_schedules(self) -> List[ReportSchedule]:
        """Get all schedules that are due to run"""
        
        now = datetime.utcnow()
        due_schedules = []
        
        # Get all active schedules from all users
        all_schedules_data = await self.vercel_kv_service.get_all_analytics_data(
            data_type="report_schedules"
        )
        
        for schedule_data in all_schedules_data:
            if isinstance(schedule_data, dict):
                schedule = ReportSchedule(**schedule_data)
                
                # Check if schedule is active and due to run
                if (schedule.status == ScheduleStatus.ACTIVE and 
                    schedule.next_run and 
                    schedule.next_run <= now):
                    due_schedules.append(schedule)
        
        return due_schedules
    
    async def process_due_schedules(self) -> List[Dict[str, Any]]:
        """Process all schedules that are due to run"""
        
        due_schedules = await self.get_due_schedules()
        results = []
        
        for schedule in due_schedules:
            try:
                result = await self._execute_schedule(schedule)
                results.append({
                    "schedule_id": schedule.id,
                    "user_id": schedule.user_id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "schedule_id": schedule.id,
                    "user_id": schedule.user_id,
                    "status": "error",
                    "error": str(e)
                })
                
                # Update schedule failure count
                schedule.failure_count += 1
                await self.vercel_kv_service.store_analytics_data(
                    user_id=schedule.user_id,
                    data_type="report_schedules",
                    source_id=schedule.id,
                    data=schedule.__dict__,
                    ttl=0
                )
        
        return results
    
    async def _execute_schedule(self, schedule: ReportSchedule) -> Dict[str, Any]:
        """Execute a single scheduled report"""
        
        # Create scheduled report instance
        scheduled_report = ScheduledReport(
            schedule_id=schedule.id,
            user_id=schedule.user_id,
            template_id=schedule.template_id,
            scheduled_time=schedule.next_run or datetime.utcnow()
        )
        
        # Calculate date range based on schedule type
        date_range = self._calculate_date_range(schedule)
        
        try:
            # Generate report
            report_data = await self.report_service.generate_report(
                user_id=schedule.user_id,
                job_id=scheduled_report.schedule_id,
                template_id=schedule.template_id,
                date_range=date_range,
                filters=schedule.filters
            )
            
            # Update scheduled report
            scheduled_report.report_data = report_data.__dict__
            scheduled_report.generated_at = datetime.utcnow()
            scheduled_report.status = ReportStatus.COMPLETED
            
            # Deliver report
            delivery_result = await self._deliver_report(schedule, report_data)
            
            # Update schedule
            schedule.last_run = datetime.utcnow()
            schedule.next_run = self._calculate_next_run(schedule.cron_expression, schedule.timezone)
            schedule.run_count += 1
            schedule.success_count += 1
            
            # Store updated schedule
            await self.vercel_kv_service.store_analytics_data(
                user_id=schedule.user_id,
                data_type="report_schedules",
                source_id=schedule.id,
                data=schedule.__dict__,
                ttl=0
            )
            
            # Store scheduled report
            await self.vercel_kv_service.store_analytics_data(
                user_id=schedule.user_id,
                data_type="scheduled_reports",
                source_id=f"{schedule.id}_{schedule.last_run.strftime('%Y%m%d_%H%M%S')}",
                data=scheduled_report.__dict__,
                ttl=2592000  # 30 days
            )
            
            return {
                "report_generated": True,
                "delivery_result": delivery_result,
                "next_run": schedule.next_run.isoformat()
            }
            
        except Exception as e:
            # Update scheduled report with error
            scheduled_report.status = ReportStatus.FAILED
            scheduled_report.error_message = str(e)
            
            # Store failed report
            await self.vercel_kv_service.store_analytics_data(
                user_id=schedule.user_id,
                data_type="scheduled_reports",
                source_id=f"{schedule.id}_{schedule.scheduled_time.strftime('%Y%m%d_%H%M%S')}",
                data=scheduled_report.__dict__,
                ttl=2592000
            )
            
            raise
    
    async def _deliver_report(
        self,
        schedule: ReportSchedule,
        report_data: Any
    ) -> Dict[str, Any]:
        """Deliver report using configured delivery methods"""
        
        delivery_results = {}
        
        for delivery_method in schedule.delivery_methods:
            try:
                if delivery_method == DeliveryMethod.STORAGE:
                    result = await self._deliver_to_storage(schedule, report_data)
                    delivery_results["storage"] = result
                
                elif delivery_method == DeliveryMethod.EMAIL:
                    result = await self._deliver_via_email(schedule, report_data)
                    delivery_results["email"] = result
                
                elif delivery_method == DeliveryMethod.WEBHOOK:
                    result = await self._deliver_via_webhook(schedule, report_data)
                    delivery_results["webhook"] = result
                
                elif delivery_method == DeliveryMethod.API:
                    result = await self._deliver_via_api(schedule, report_data)
                    delivery_results["api"] = result
                    
            except Exception as e:
                delivery_results[delivery_method.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return delivery_results
    
    async def _deliver_to_storage(
        self,
        schedule: ReportSchedule,
        report_data: Any
    ) -> Dict[str, Any]:
        """Deliver report to storage location"""
        
        # Generate exports for all formats
        exports = {}
        for export_format in schedule.export_formats:
            try:
                export_data = await self.report_service.export_report(
                    report_data=report_data,
                    export_format=export_format,
                    user_id=schedule.user_id
                )
                exports[export_format] = export_data
            except Exception as e:
                exports[export_format] = {"error": str(e)}
        
        # Store exports in Vercel KV
        storage_key = f"reports/{schedule.user_id}/{schedule.id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        await self.vercel_kv_service.store_analytics_data(
            user_id=schedule.user_id,
            data_type="report_exports",
            source_id=storage_key,
            data={
                "schedule_id": schedule.id,
                "exports": exports,
                "generated_at": datetime.utcnow().isoformat()
            },
            ttl=2592000  # 30 days
        )
        
        return {
            "status": "success",
            "storage_key": storage_key,
            "exports": list(exports.keys())
        }
    
    async def _deliver_via_email(
        self,
        schedule: ReportSchedule,
        report_data: Any
    ) -> Dict[str, Any]:
        """Deliver report via email (placeholder implementation)"""
        
        # This is a placeholder - in production, you'd integrate with an email service
        # like SendGrid, AWS SES, or similar
        
        return {
            "status": "success",
            "recipients": schedule.recipients,
            "message": "Report delivered via email (placeholder implementation)"
        }
    
    async def _deliver_via_webhook(
        self,
        schedule: ReportSchedule,
        report_data: Any
    ) -> Dict[str, Any]:
        """Deliver report via webhook (placeholder implementation)"""
        
        # This is a placeholder - in production, you'd make HTTP POST requests
        # to the configured webhook URL
        
        return {
            "status": "success",
            "webhook_url": schedule.webhook_url,
            "message": "Report delivered via webhook (placeholder implementation)"
        }
    
    async def _deliver_via_api(
        self,
        schedule: ReportSchedule,
        report_data: Any
    ) -> Dict[str, Any]:
        """Deliver report via API (placeholder implementation)"""
        
        # This is a placeholder - in production, you'd make API calls to
        # external services or internal endpoints
        
        return {
            "status": "success",
            "message": "Report delivered via API (placeholder implementation)"
        }
    
    def _calculate_next_run(self, cron_expression: str, timezone: str) -> datetime:
        """Calculate the next run time based on cron expression"""
        
        # For simplicity, using UTC timezone
        # In production, you'd use pytz or similar for proper timezone handling
        
        cron = croniter.croniter(cron_expression, datetime.utcnow())
        return cron.get_next(datetime)
    
    def _calculate_date_range(self, schedule: ReportSchedule) -> Dict[str, str]:
        """Calculate date range for the report based on schedule type"""
        
        now = datetime.utcnow()
        
        if schedule.template_id == "daily_overview":
            start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif schedule.template_id == "weekly_performance":
            start_date = (now - timedelta(weeks=1)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif schedule.template_id == "monthly_analytics":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:
            # Default to last 7 days
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        
        return {
            "start": start_date,
            "end": end_date
        }
    
    async def get_scheduled_reports(
        self,
        user_id: str,
        schedule_id: Optional[str] = None,
        status: Optional[ReportStatus] = None
    ) -> List[ScheduledReport]:
        """Get scheduled reports for a user"""
        
        # Get all scheduled reports for user
        reports_data = await self.vercel_kv_service.get_analytics_data(
            user_id=user_id,
            data_type="scheduled_reports"
        )
        
        reports = []
        for report_data in reports_data:
            if isinstance(report_data, dict):
                report = ScheduledReport(**report_data)
                
                # Apply filters
                if schedule_id and report.schedule_id != schedule_id:
                    continue
                if status and report.status != status:
                    continue
                
                reports.append(report)
        
        # Sort by scheduled time (newest first)
        reports.sort(key=lambda x: x.scheduled_time, reverse=True)
        
        return reports
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        
        try:
            # Test Vercel KV connection
            kv_health = await self.vercel_kv_service.health_check()
            
            # Test report service
            report_health = await self.report_service.health_check()
            
            # Get schedule statistics
            all_schedules = await self.vercel_kv_service.get_all_analytics_data(
                data_type="report_schedules"
            )
            
            active_schedules = sum(
                1 for s in all_schedules 
                if isinstance(s, dict) and s.get("status") == ScheduleStatus.ACTIVE.value
            )
            
            due_schedules = await self.get_due_schedules()
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "vercel_kv": kv_health,
                    "report_service": report_health
                },
                "schedules": {
                    "total": len(all_schedules),
                    "active": active_schedules,
                    "due": len(due_schedules)
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




