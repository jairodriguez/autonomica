import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.vercel_kv_service import VercelKVService
from app.services.analytics_data_collector import AnalyticsDataCollector
from app.services.kpi_calculation_service import KPICalculationService
from app.services.kpi_dashboard_service import KPIDashboardService
from app.services.report_generation_service import ReportGenerationService
from app.services.report_scheduler_service import ReportSchedulerService
from app.services.analytics_auth_service import AnalyticsAuthService
from app.services.data_privacy_service import DataPrivacyService


@dataclass
class AnalyticsSystemStatus:
    """Status of the analytics system components"""
    data_collector: Dict[str, Any]
    kpi_service: Dict[str, Any]
    dashboard_service: Dict[str, Any]
    report_service: Dict[str, Any]
    scheduler_service: Dict[str, Any]
    auth_service: Dict[str, Any]
    privacy_service: Dict[str, Any]
    vercel_kv: Dict[str, Any]
    overall_status: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AnalyticsMetrics:
    """Overall analytics metrics"""
    total_data_points: int
    total_users: int
    active_collections: int
    scheduled_reports: int
    pending_dsrs: int
    data_retention_compliance: float
    system_performance: Dict[str, Any]


class AnalyticsService:
    """Main service for orchestrating the analytics system"""
    
    def __init__(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        cache_service: CacheService,
        vercel_kv_service: VercelKVService
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        
        # Initialize all analytics services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all analytics service components"""
        
        # Initialize authentication service first
        self.auth_service = AnalyticsAuthService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service
        )
        
        # Initialize data privacy service
        self.privacy_service = DataPrivacyService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service,
            auth_service=self.auth_service
        )
        
        # Initialize data collection service
        self.data_collector = AnalyticsDataCollector(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service
        )
        
        # Initialize KPI calculation service
        self.kpi_service = KPICalculationService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service
        )
        
        # Initialize dashboard service
        self.dashboard_service = KPIDashboardService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service,
            kpi_service=self.kpi_service
        )
        
        # Initialize report generation service
        self.report_service = ReportGenerationService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service,
            kpi_service=self.kpi_service
        )
        
        # Initialize report scheduler service
        self.scheduler_service = ReportSchedulerService(
            db=self.db,
            redis_service=self.redis_service,
            cache_service=self.cache_service,
            vercel_kv_service=self.vercel_kv_service,
            report_service=self.report_service
        )
    
    async def start_data_collection(
        self,
        user_id: str,
        data_sources: List[str],
        collection_frequency: str = "daily"
    ) -> Dict[str, Any]:
        """Start data collection for specified sources"""
        
        try:
            # Check if user has permission to start data collection
            if not await self.auth_service.check_permission(user_id, "view_analytics"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to start data collection"
                }
            
            # Start collection jobs
            collection_results = {}
            for source in data_sources:
                try:
                    result = await self.data_collector.start_collection_job(
                        user_id=user_id,
                        source_type=source,
                        frequency=collection_frequency
                    )
                    collection_results[source] = result
                except Exception as e:
                    collection_results[source] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Log the collection start
            await self.privacy_service._log_privacy_audit(
                user_id=user_id,
                action="start_data_collection",
                data_category=self.privacy_service.DataCategory.ANALYTICS,
                legal_basis="legitimate_interest",
                additional_info={
                    "data_sources": data_sources,
                    "frequency": collection_frequency,
                    "results": collection_results
                }
            )
            
            return {
                "success": True,
                "collection_results": collection_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_comprehensive_kpis(
        self,
        user_id: str,
        date_range: Optional[Dict[str, str]] = None,
        include_advanced: bool = True,
        include_business_intelligence: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive KPI data for a user"""
        
        try:
            # Check if user has permission to view analytics
            if not await self.auth_service.check_permission(user_id, "view_analytics"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to view analytics"
                }
            
            # Get KPI data
            kpi_data = await self.kpi_service.calculate_comprehensive_kpis(
                user_id=user_id,
                date_range=date_range,
                include_advanced=include_advanced,
                include_business_intelligence=include_business_intelligence
            )
            
            # Log KPI access
            await self.privacy_service._log_privacy_audit(
                user_id=user_id,
                action="access_kpis",
                data_category=self.privacy_service.DataCategory.ANALYTICS,
                legal_basis="legitimate_interest",
                additional_info={
                    "date_range": date_range,
                    "include_advanced": include_advanced,
                    "include_business_intelligence": include_business_intelligence
                }
            )
            
            return {
                "success": True,
                "kpi_data": kpi_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_dashboard_data(
        self,
        user_id: str,
        dashboard_id: str,
        date_range: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get dashboard data for a specific dashboard"""
        
        try:
            # Check if user has permission to view dashboards
            if not await self.auth_service.check_permission(user_id, "view_dashboards"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to view dashboards"
                }
            
            # Get dashboard data
            dashboard_data = await self.dashboard_service.get_dashboard_data(
                user_id=user_id,
                dashboard_id=dashboard_id,
                date_range=date_range,
                filters=filters
            )
            
            # Log dashboard access
            await self.privacy_service._log_privacy_audit(
                user_id=user_id,
                action="access_dashboard",
                data_category=self.privacy_service.DataCategory.ANALYTICS,
                legal_basis="legitimate_interest",
                additional_info={
                    "dashboard_id": dashboard_id,
                    "date_range": date_range,
                    "filters": filters
                }
            )
            
            return {
                "success": True,
                "dashboard_data": dashboard_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_report(
        self,
        user_id: str,
        template_id: str,
        report_type: str,
        date_range: Dict[str, str],
        export_formats: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a report for a user"""
        
        try:
            # Check if user has permission to generate reports
            if not await self.auth_service.check_permission(user_id, "view_reports"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to generate reports"
                }
            
            # Create report job
            report_job = await self.report_service.create_report_job(
                user_id=user_id,
                template_id=template_id,
                report_type=report_type,
                date_range=date_range,
                export_formats=export_formats or ["json"],
                filters=filters
            )
            
            # Generate report
            report_data = await self.report_service.generate_report(
                user_id=user_id,
                job_id=report_job.id,
                template_id=template_id,
                date_range=date_range,
                filters=filters
            )
            
            # Export report in requested formats
            export_results = {}
            for export_format in (export_formats or ["json"]):
                try:
                    export_result = await self.report_service.export_report(
                        report_data=report_data,
                        export_format=export_format,
                        user_id=user_id
                    )
                    export_results[export_format] = export_result
                except Exception as e:
                    export_results[export_format] = {
                        "success": False,
                        "error": str(e)
                    }
            
            # Log report generation
            await self.privacy_service._log_privacy_audit(
                user_id=user_id,
                action="generate_report",
                data_category=self.privacy_service.DataCategory.ANALYTICS,
                legal_basis="legitimate_interest",
                additional_info={
                    "template_id": template_id,
                    "report_type": report_type,
                    "export_formats": export_formats,
                    "filters": filters
                }
            )
            
            return {
                "success": True,
                "report_job": report_job,
                "report_data": report_data,
                "export_results": export_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def schedule_report(
        self,
        user_id: str,
        template_id: str,
        name: str,
        description: str,
        cron_expression: str,
        timezone: str = "UTC",
        delivery_methods: Optional[List[str]] = None,
        export_formats: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Schedule a recurring report"""
        
        try:
            # Check if user has permission to schedule reports
            if not await self.auth_service.check_permission(user_id, "schedule_reports"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to schedule reports"
                }
            
            # Create report schedule
            schedule = await self.scheduler_service.create_schedule(
                user_id=user_id,
                template_id=template_id,
                name=name,
                description=description,
                cron_expression=cron_expression,
                timezone=timezone,
                delivery_methods=delivery_methods or ["storage"],
                export_formats=export_formats or ["json"],
                filters=filters
            )
            
            # Log schedule creation
            await self.privacy_service._log_privacy_audit(
                user_id=user_id,
                action="schedule_report",
                data_category=self.privacy_service.DataCategory.ANALYTICS,
                legal_basis="legitimate_interest",
                additional_info={
                    "template_id": template_id,
                    "cron_expression": cron_expression,
                    "delivery_methods": delivery_methods,
                    "export_formats": export_formats
                }
            )
            
            return {
                "success": True,
                "schedule": schedule,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_data_subject_request(
        self,
        user_id: str,
        request_type: str,
        description: str
    ) -> Dict[str, Any]:
        """Process a data subject request (GDPR)"""
        
        try:
            # Create DSR
            dsr = await self.privacy_service.create_data_subject_request(
                user_id=user_id,
                request_type=request_type,
                description=description
            )
            
            if not dsr:
                return {
                    "success": False,
                    "error": "Failed to create data subject request"
                }
            
            # Execute the data right if it's a supported type
            if request_type in ["access", "erasure", "portability"]:
                execution_result = await self.privacy_service.execute_data_right(
                    user_id=user_id,
                    data_right=request_type
                )
                
                return {
                    "success": True,
                    "dsr": dsr,
                    "execution_result": execution_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": True,
                    "dsr": dsr,
                    "message": f"Data subject request created. {request_type} requests are processed manually by administrators.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_system_status(self) -> AnalyticsSystemStatus:
        """Get comprehensive system status"""
        
        try:
            # Get health status for all services
            data_collector_status = await self.data_collector.health_check()
            kpi_service_status = await self.kpi_service.health_check()
            dashboard_status = await self.dashboard_service.health_check()
            report_service_status = await self.report_service.health_check()
            scheduler_status = await self.scheduler_service.health_check()
            auth_status = await self.auth_service.health_check()
            privacy_status = await self.privacy_service.health_check()
            vercel_kv_status = await self.vercel_kv_service.health_check()
            
            # Determine overall status
            all_statuses = [
                data_collector_status.get("status"),
                kpi_service_status.get("status"),
                dashboard_status.get("status"),
                report_service_status.get("status"),
                scheduler_status.get("status"),
                auth_status.get("status"),
                privacy_status.get("status"),
                vercel_kv_status.get("status")
            ]
            
            if all(status == "healthy" for status in all_statuses if status):
                overall_status = "healthy"
            elif any(status == "unhealthy" for status in all_statuses if status):
                overall_status = "unhealthy"
            else:
                overall_status = "degraded"
            
            return AnalyticsSystemStatus(
                data_collector=data_collector_status,
                kpi_service=kpi_service_status,
                dashboard_service=dashboard_status,
                report_service=report_service_status,
                scheduler_service=scheduler_status,
                auth_service=auth_status,
                privacy_service=privacy_status,
                vercel_kv=vercel_kv_status,
                overall_status=overall_status
            )
            
        except Exception as e:
            return AnalyticsSystemStatus(
                data_collector={"error": str(e)},
                kpi_service={"error": str(e)},
                dashboard_service={"error": str(e)},
                report_service={"error": str(e)},
                scheduler_service={"error": str(e)},
                auth_service={"error": str(e)},
                privacy_service={"error": str(e)},
                vercel_kv={"error": str(e)},
                overall_status="error"
            )
    
    async def get_analytics_metrics(self, user_id: str) -> AnalyticsMetrics:
        """Get overall analytics system metrics"""
        
        try:
            # Check if user has permission to view system metrics
            if not await self.auth_service.check_permission(user_id, "view_analytics"):
                return AnalyticsMetrics(
                    total_data_points=0,
                    total_users=0,
                    active_collections=0,
                    scheduled_reports=0,
                    pending_dsrs=0,
                    data_retention_compliance=0.0,
                    system_performance={"error": "Insufficient permissions"}
                )
            
            # Get metrics from various services
            total_data_points = len(await self.vercel_kv_service.get_all_analytics_data("analytics"))
            total_users = len(await self.vercel_kv_service.get_all_analytics_data("user_permissions"))
            active_collections = len(await self.data_collector.get_active_collection_jobs())
            scheduled_reports = len(await self.scheduler_service.get_schedules(user_id))
            pending_dsrs = len(await self.privacy_service.get_privacy_audit_logs(
                admin_user_id=user_id,
                action="create_dsr",
                limit=1000
            ))
            
            # Calculate data retention compliance
            retention_rules = await self.privacy_service.get_all_retention_rules()
            compliance_score = 0.0
            if retention_rules:
                compliance_score = sum(1 for rule in retention_rules if rule.is_active) / len(retention_rules)
            
            # Get system performance metrics
            system_status = await self.get_system_status()
            system_performance = {
                "overall_status": system_status.overall_status,
                "service_health": {
                    "data_collector": system_status.data_collector.get("status"),
                    "kpi_service": system_status.kpi_service.get("status"),
                    "dashboard_service": system_status.dashboard_service.get("status"),
                    "report_service": system_status.report_service.get("status"),
                    "scheduler_service": system_status.scheduler_service.get("status"),
                    "auth_service": system_status.auth_service.get("status"),
                    "privacy_service": system_status.privacy_service.get("status"),
                    "vercel_kv": system_status.vercel_kv.get("status")
                }
            }
            
            return AnalyticsMetrics(
                total_data_points=total_data_points,
                total_users=total_users,
                active_collections=active_collections,
                scheduled_reports=scheduled_reports,
                pending_dsrs=pending_dsrs,
                data_retention_compliance=compliance_score,
                system_performance=system_performance
            )
            
        except Exception as e:
            return AnalyticsMetrics(
                total_data_points=0,
                total_users=0,
                active_collections=0,
                scheduled_reports=0,
                pending_dsrs=0,
                data_retention_compliance=0.0,
                system_performance={"error": str(e)}
            )
    
    async def cleanup_expired_data(self, admin_user_id: str) -> Dict[str, Any]:
        """Clean up expired data based on retention policies"""
        
        try:
            # Check if admin user has permission to manage privacy
            if not await self.auth_service.check_permission(admin_user_id, "manage_users"):
                return {
                    "success": False,
                    "error": "Insufficient permissions to cleanup expired data"
                }
            
            # Execute cleanup
            cleanup_result = await self.privacy_service.cleanup_expired_data()
            
            return {
                "success": True,
                "cleanup_result": cleanup_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_scheduled_reports(self) -> Dict[str, Any]:
        """Process all due scheduled reports"""
        
        try:
            # Get due schedules
            due_schedules = await self.scheduler_service.get_due_schedules()
            
            if not due_schedules:
                return {
                    "success": True,
                    "message": "No scheduled reports due",
                    "processed_count": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Process due schedules
            results = await self.scheduler_service.process_due_schedules()
            
            return {
                "success": True,
                "processed_count": len(results),
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check overall system health"""
        
        try:
            system_status = await self.get_system_status()
            
            return {
                "status": system_status.overall_status,
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "data_collector": system_status.data_collector.get("status"),
                    "kpi_service": system_status.kpi_service.get("status"),
                    "dashboard_service": system_status.dashboard_service.get("status"),
                    "report_service": system_status.report_service.get("status"),
                    "scheduler_service": system_status.scheduler_service.get("status"),
                    "auth_service": system_status.auth_service.get("status"),
                    "privacy_service": system_status.privacy_service.get("status"),
                    "vercel_kv": system_status.vercel_kv.get("status")
                },
                "overall_status": system_status.overall_status
            }
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }




