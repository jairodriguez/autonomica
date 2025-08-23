from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from app.services.analytics_service import AnalyticsService
from app.services.analytics_auth_service import AnalyticsAuthService, require_permission, require_access_level
from app.services.data_privacy_service import DataCategory, DataRight
from app.core.dependencies import get_db, get_redis_service, get_cache_service, get_vercel_kv_service
from app.core.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Dependency to get analytics service
async def get_analytics_service(
    db=Depends(get_db),
    redis_service=Depends(get_redis_service),
    cache_service=Depends(get_cache_service),
    vercel_kv_service=Depends(get_vercel_kv_service)
) -> AnalyticsService:
    return AnalyticsService(db, redis_service, cache_service, vercel_kv_service)


# Dependency to get auth service
async def get_auth_service(
    db=Depends(get_db),
    redis_service=Depends(get_redis_service),
    cache_service=Depends(get_cache_service),
    vercel_kv_service=Depends(get_vercel_kv_service)
) -> AnalyticsAuthService:
    return AnalyticsAuthService(db, redis_service, cache_service, vercel_kv_service)


# Data Collection Endpoints
@router.post("/collect/start")
async def start_data_collection(
    data_sources: List[str] = Body(..., description="List of data sources to collect from"),
    collection_frequency: str = Body("daily", description="Collection frequency"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Start data collection for specified sources"""
    
    try:
        result = await analytics_service.start_data_collection(
            user_id=current_user,
            data_sources=data_sources,
            collection_frequency=collection_frequency
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collect/status")
async def get_collection_status(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get status of data collection jobs"""
    
    try:
        # Get active collection jobs
        active_jobs = await analytics_service.data_collector.get_active_collection_jobs()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "active_jobs": active_jobs,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# KPI Endpoints
@router.get("/kpis")
async def get_kpis(
    date_range: Optional[str] = Query(None, description="Date range in format 'start_date,end_date'"),
    include_advanced: bool = Query(True, description="Include advanced KPI metrics"),
    include_business_intelligence: bool = Query(True, description="Include business intelligence insights"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive KPI data"""
    
    try:
        # Parse date range if provided
        parsed_date_range = None
        if date_range:
            start_date, end_date = date_range.split(",")
            parsed_date_range = {
                "start_date": start_date,
                "end_date": end_date
            }
        
        result = await analytics_service.get_comprehensive_kpis(
            user_id=current_user,
            date_range=parsed_date_range,
            include_advanced=include_advanced,
            include_business_intelligence=include_business_intelligence
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis/{kpi_type}")
async def get_specific_kpi(
    kpi_type: str = Path(..., description="Type of KPI to retrieve"),
    date_range: Optional[str] = Query(None, description="Date range in format 'start_date,end_date'"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get specific KPI data by type"""
    
    try:
        # Parse date range if provided
        parsed_date_range = None
        if date_range:
            start_date, end_date = date_range.split(",")
            parsed_date_range = {
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Get KPI data from the service
        kpi_data = await analytics_service.kpi_service.calculate_comprehensive_kpis(
            user_id=current_user,
            date_range=parsed_date_range,
            include_advanced=True,
            include_business_intelligence=True
        )
        
        # Filter by KPI type
        if kpi_type in kpi_data:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "kpi_type": kpi_type,
                    "data": kpi_data[kpi_type],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"KPI type '{kpi_type}' not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Endpoints
@router.get("/dashboards")
async def get_dashboards(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get available dashboards for the user"""
    
    try:
        dashboards = await analytics_service.dashboard_service.get_dashboard_config(
            user_id=current_user
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "dashboards": dashboards,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard_data(
    dashboard_id: str = Path(..., description="ID of the dashboard to retrieve"),
    date_range: Optional[str] = Query(None, description="Date range in format 'start_date,end_date'"),
    filters: Optional[str] = Query(None, description="JSON string of filters to apply"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get data for a specific dashboard"""
    
    try:
        # Parse date range if provided
        parsed_date_range = None
        if date_range:
            start_date, end_date = date_range.split(",")
            parsed_date_range = {
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Parse filters if provided
        parsed_filters = None
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid filters JSON")
        
        result = await analytics_service.get_dashboard_data(
            user_id=current_user,
            dashboard_id=dashboard_id,
            date_range=parsed_date_range,
            filters=parsed_filters
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dashboards")
async def create_custom_dashboard(
    dashboard_config: Dict[str, Any] = Body(..., description="Dashboard configuration"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a custom dashboard"""
    
    try:
        dashboard = await analytics_service.dashboard_service.create_custom_dashboard(
            user_id=current_user,
            config=dashboard_config
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "dashboard": dashboard,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Report Endpoints
@router.get("/reports/templates")
async def get_report_templates(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get available report templates"""
    
    try:
        templates = await analytics_service.report_service.get_report_templates()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "templates": [template.__dict__ for template in templates],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(
    template_id: str = Body(..., description="ID of the report template"),
    report_type: str = Body(..., description="Type of report to generate"),
    date_range: Dict[str, str] = Body(..., description="Date range for the report"),
    export_formats: Optional[List[str]] = Body(["json"], description="Export formats"),
    filters: Optional[Dict[str, Any]] = Body(None, description="Filters to apply"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Generate a report"""
    
    try:
        result = await analytics_service.generate_report(
            user_id=current_user,
            template_id=template_id,
            report_type=report_type,
            date_range=date_range,
            export_formats=export_formats,
            filters=filters
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/schedule")
async def schedule_report(
    template_id: str = Body(..., description="ID of the report template"),
    name: str = Body(..., description="Name of the scheduled report"),
    description: str = Body(..., description="Description of the scheduled report"),
    cron_expression: str = Body(..., description="Cron expression for scheduling"),
    timezone: str = Body("UTC", description="Timezone for scheduling"),
    delivery_methods: Optional[List[str]] = Body(["storage"], description="Delivery methods"),
    export_formats: Optional[List[str]] = Body(["json"], description="Export formats"),
    filters: Optional[Dict[str, Any]] = Body(None, description="Filters to apply"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Schedule a recurring report"""
    
    try:
        result = await analytics_service.schedule_report(
            user_id=current_user,
            template_id=template_id,
            name=name,
            description=description,
            cron_expression=cron_expression,
            timezone=timezone,
            delivery_methods=delivery_methods,
            export_formats=export_formats,
            filters=filters
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=201,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/schedules")
async def get_scheduled_reports(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get scheduled reports for the user"""
    
    try:
        schedules = await analytics_service.scheduler_service.get_schedules(
            user_id=current_user
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "schedules": [schedule.__dict__ for schedule in schedules],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Privacy and GDPR Endpoints
@router.post("/privacy/consent")
async def record_consent(
    data_category: str = Body(..., description="Category of data for consent"),
    consent_given: bool = Body(..., description="Whether consent is given"),
    consent_version: str = Body(..., description="Version of the consent"),
    legal_basis: str = Body(..., description="Legal basis for processing"),
    purpose: str = Body(..., description="Purpose of data processing"),
    expires_at: Optional[str] = Body(None, description="Expiration date for consent"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Record user consent for data processing"""
    
    try:
        # Parse expiration date if provided
        parsed_expires_at = None
        if expires_at:
            parsed_expires_at = datetime.fromisoformat(expires_at)
        
        # Get data category enum
        try:
            data_category_enum = DataCategory(data_category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid data category: {data_category}")
        
        consent = await analytics_service.privacy_service.record_data_processing_consent(
            user_id=current_user,
            data_category=data_category_enum,
            consent_given=consent_given,
            consent_version=consent_version,
            legal_basis=legal_basis,
            purpose=purpose,
            expires_at=parsed_expires_at
        )
        
        if consent:
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "consent": consent.__dict__,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to record consent")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/consent/revoke")
async def revoke_consent(
    data_category: str = Body(..., description="Category of data to revoke consent for"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Revoke user consent for data processing"""
    
    try:
        # Get data category enum
        try:
            data_category_enum = DataCategory(data_category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid data category: {data_category}")
        
        success = await analytics_service.privacy_service.revoke_consent(
            user_id=current_user,
            data_category=data_category_enum
        )
        
        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"Consent revoked for {data_category}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to revoke consent")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/dsr")
async def create_data_subject_request(
    request_type: str = Body(..., description="Type of data subject request"),
    description: str = Body(..., description="Description of the request"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Create a data subject request (GDPR)"""
    
    try:
        result = await analytics_service.process_data_subject_request(
            user_id=current_user,
            request_type=request_type,
            description=description
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=201,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy/dsr")
async def get_data_subject_requests(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get data subject requests for the user"""
    
    try:
        dsrs = await analytics_service.privacy_service.get_privacy_audit_logs(
            admin_user_id=current_user,
            action="create_dsr",
            limit=100
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "dsrs": [dsr.__dict__ for dsr in dsrs],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Status and Health Endpoints
@router.get("/status")
async def get_system_status(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get comprehensive system status"""
    
    try:
        status = await analytics_service.get_system_status()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "status": status.__dict__,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_analytics_metrics(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overall analytics system metrics"""
    
    try:
        metrics = await analytics_service.get_analytics_metrics(current_user)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "metrics": metrics.__dict__,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Check system health"""
    
    try:
        health = await analytics_service.health_check()
        
        return JSONResponse(
            status_code=200,
            content=health
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Admin-only Endpoints
@router.post("/admin/cleanup")
async def cleanup_expired_data(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: AnalyticsAuthService = Depends(get_auth_service)
):
    """Clean up expired data based on retention policies (admin only)"""
    
    try:
        # Check if user has admin permissions
        if not await auth_service.check_permission(current_user, "manage_users"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = await analytics_service.cleanup_expired_data(current_user)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/process-scheduled-reports")
async def process_scheduled_reports(
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: AnalyticsAuthService = Depends(get_auth_service)
):
    """Process all due scheduled reports (admin only)"""
    
    try:
        # Check if user has admin permissions
        if not await auth_service.check_permission(current_user, "manage_schedules"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = await analytics_service.process_scheduled_reports()
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content=result
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    data_category: Optional[str] = Query(None, description="Filter by data category"),
    start_date: Optional[str] = Query(None, description="Start date for filtering"),
    end_date: Optional[str] = Query(None, description="End date for filtering"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    current_user: str = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: AnalyticsAuthService = Depends(get_auth_service)
):
    """Get privacy audit logs (admin only)"""
    
    try:
        # Check if user has admin permissions
        if not await auth_service.check_permission(current_user, "view_user_data"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date)
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date)
        
        # Parse data category if provided
        parsed_data_category = None
        if data_category:
            try:
                parsed_data_category = DataCategory(data_category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid data category: {data_category}")
        
        logs = await analytics_service.privacy_service.get_privacy_audit_logs(
            admin_user_id=current_user,
            user_id=user_id,
            action=action,
            data_category=parsed_data_category,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            limit=limit
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "logs": [log.__dict__ for log in logs],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




