"""
Analytics API Endpoints
Provides data access for the analytics dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.services.social_analytics_service import SocialAnalyticsService
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.auth import get_current_user
from app.models.schema import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Initialize services
def get_analytics_service(db: Session = Depends(get_db)) -> SocialAnalyticsService:
    """Get analytics service instance"""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    return SocialAnalyticsService(db, redis_service, cache_service)

@router.get("/dashboard")
async def get_dashboard_data(
    user_id: Optional[str] = Query(None, description="User ID for user-specific data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard data including:
    - Overview statistics
    - Recent activity
    - Platform distribution
    - Service status
    """
    try:
        analytics_service = get_analytics_service(db)
        dashboard_data = await analytics_service.get_analytics_dashboard_data(user_id)
        
        if dashboard_data["success"]:
            return {
                "success": True,
                "data": dashboard_data["dashboard_data"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get dashboard data: {dashboard_data.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )

@router.get("/content/{content_id}")
async def get_content_analytics(
    content_id: int,
    analysis_period: str = Query("7d", description="Analysis period (e.g., 7d, 30d, 90d)"),
    include_insights: bool = Query(True, description="Include generated insights"),
    include_recommendations: bool = Query(True, description="Include recommendations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics for specific content piece
    """
    try:
        analytics_service = get_analytics_service(db)
        analytics_data = await analytics_service.get_analytics_for_content(
            content_id,
            analysis_period,
            include_insights,
            include_recommendations
        )
        
        if analytics_data["success"]:
            return {
                "success": True,
                "data": analytics_data["report"],
                "content_id": content_id,
                "analysis_period": analysis_period,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Content analytics not found: {analytics_data.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving content analytics: {str(e)}"
        )

@router.get("/content/{content_id}/summary")
async def get_content_summary(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics summary for specific content piece
    """
    try:
        analytics_service = get_analytics_service(db)
        summary_data = await analytics_service.get_analytics_summary(content_id)
        
        if "error" not in summary_data:
            return {
                "success": True,
                "data": summary_data,
                "content_id": content_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Content summary not found: {summary_data.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving content summary: {str(e)}"
        )

@router.get("/content/{content_id}/insights")
async def get_content_insights(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get insights for specific content piece
    """
    try:
        analytics_service = get_analytics_service(db)
        insights_data = await analytics_service.get_insights_summary(content_id)
        
        if "error" not in insights_data:
            return {
                "success": True,
                "data": insights_data,
                "content_id": content_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Content insights not found: {insights_data.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving content insights: {str(e)}"
        )

@router.post("/content/{content_id}/collect-metrics")
async def collect_content_metrics(
    content_id: int,
    platforms: Optional[List[str]] = Query(None, description="Specific platforms to collect from"),
    collection_type: str = Query("realtime", description="Collection type: realtime or historical"),
    force_refresh: bool = Query(False, description="Force refresh even if cached data exists"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start metrics collection for specific content
    """
    try:
        analytics_service = get_analytics_service(db)
        
        # Start collection in background
        collection_result = await analytics_service.collect_metrics_for_content(
            content_id,
            platforms,
            collection_type,
            force_refresh
        )
        
        if collection_result["success"]:
            return {
                "success": True,
                "message": "Metrics collection started successfully",
                "job_id": collection_result.get("job_id"),
                "status": collection_result.get("status"),
                "platforms": collection_result.get("platforms"),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to start metrics collection: {collection_result.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting metrics collection: {str(e)}"
        )

@router.get("/collection-job/{job_id}")
async def get_collection_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a metrics collection job
    """
    try:
        analytics_service = get_analytics_service(db)
        job_status = await analytics_service.get_collection_status(job_id)
        
        if job_status["success"]:
            return {
                "success": True,
                "data": job_status["job"],
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Collection job not found: {job_status.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving job status: {str(e)}"
        )

@router.get("/comparison")
async def get_performance_comparison(
    content_ids: str = Query(..., description="Comma-separated list of content IDs"),
    platforms: Optional[str] = Query(None, description="Comma-separated list of platforms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare performance across multiple content pieces and platforms
    """
    try:
        # Parse content IDs
        try:
            content_id_list = [int(cid.strip()) for cid in content_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid content ID format. Use comma-separated integers."
            )
        
        # Parse platforms if provided
        platform_list = None
        if platforms:
            platform_list = [p.strip() for p in platforms.split(",")]
        
        analytics_service = get_analytics_service(db)
        comparison_data = await analytics_service.get_platform_performance_comparison(
            content_id_list,
            platform_list
        )
        
        if comparison_data["success"]:
            return {
                "success": True,
                "data": comparison_data["comparison"],
                "content_ids": content_id_list,
                "platforms": platform_list,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate comparison: {comparison_data.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating performance comparison: {str(e)}"
        )

@router.get("/trends")
async def get_trend_analysis(
    content_id: Optional[int] = Query(None, description="Content ID for specific content trends"),
    platform: Optional[str] = Query(None, description="Specific platform for trends"),
    metric: str = Query("engagement_rate", description="Metric to analyze (engagement_rate, reach, impressions)"),
    period: str = Query("30d", description="Analysis period (7d, 30d, 90d)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get trend analysis for metrics over time
    """
    try:
        # This would typically involve historical data analysis
        # For now, return placeholder trend data structure
        
        # Calculate date range
        end_date = datetime.utcnow()
        if period.endswith("d"):
            days = int(period[:-1])
            start_date = end_date - timedelta(days=days)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Generate sample trend data
        trend_data = {
            "metric": metric,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trend_direction": "increasing",
            "trend_strength": "moderate",
            "data_points": [],
            "summary": {
                "average_value": 0,
                "peak_value": 0,
                "lowest_value": 0,
                "change_percentage": 0
            }
        }
        
        # Generate sample data points
        current_date = start_date
        base_value = 100
        while current_date <= end_date:
            # Simulate trend with some variation
            import random
            variation = random.uniform(0.8, 1.2)
            value = base_value * variation
            
            trend_data["data_points"].append({
                "date": current_date.strftime("%Y-%m-%d"),
                "value": round(value, 2)
            })
            
            base_value = value * 1.05  # Slight upward trend
            current_date += timedelta(days=1)
        
        # Calculate summary statistics
        values = [point["value"] for point in trend_data["data_points"]]
        if values:
            trend_data["summary"]["average_value"] = round(sum(values) / len(values), 2)
            trend_data["summary"]["peak_value"] = max(values)
            trend_data["summary"]["lowest_value"] = min(values)
            
            if len(values) > 1:
                change = ((values[-1] - values[0]) / values[0]) * 100
                trend_data["summary"]["change_percentage"] = round(change, 2)
                
                if change > 10:
                    trend_data["trend_direction"] = "increasing"
                    trend_data["trend_strength"] = "strong"
                elif change > 5:
                    trend_data["trend_direction"] = "increasing"
                    trend_data["trend_strength"] = "moderate"
                elif change < -10:
                    trend_data["trend_direction"] = "decreasing"
                    trend_data["trend_strength"] = "strong"
                elif change < -5:
                    trend_data["trend_direction"] = "decreasing"
                    trend_data["trend_strength"] = "moderate"
                else:
                    trend_data["trend_direction"] = "stable"
                    trend_data["trend_strength"] = "weak"
        
        return {
            "success": True,
            "data": trend_data,
            "content_id": content_id,
            "platform": platform,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating trend analysis: {str(e)}"
        )

@router.get("/export")
async def export_analytics_data(
    content_ids: str = Query(..., description="Comma-separated list of content IDs"),
    format: str = Query("json", description="Export format (json, csv, excel)"),
    include_insights: bool = Query(True, description="Include insights in export"),
    include_recommendations: bool = Query(True, description="Include recommendations in export"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export analytics data in various formats
    """
    try:
        # Parse content IDs
        try:
            content_id_list = [int(cid.strip()) for cid in content_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid content ID format. Use comma-separated integers."
            )
        
        analytics_service = get_analytics_service(db)
        
        # Collect analytics data for each content piece
        export_data = {
            "export_info": {
                "format": format,
                "content_count": len(content_id_list),
                "exported_at": datetime.utcnow().isoformat(),
                "user_id": str(current_user.id)
            },
            "content_analytics": []
        }
        
        for content_id in content_id_list:
            try:
                analytics_data = await analytics_service.get_analytics_for_content(
                    content_id,
                    "30d",  # Use 30-day period for export
                    include_insights,
                    include_recommendations
                )
                
                if analytics_data["success"]:
                    export_data["content_analytics"].append({
                        "content_id": content_id,
                        "analytics": analytics_data["report"]
                    })
                else:
                    export_data["content_analytics"].append({
                        "content_id": content_id,
                        "error": analytics_data.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                export_data["content_analytics"].append({
                    "content_id": content_id,
                    "error": str(e)
                })
        
        # Return data in requested format
        if format.lower() == "json":
            return {
                "success": True,
                "data": export_data,
                "format": "json",
                "timestamp": datetime.utcnow().isoformat()
            }
        elif format.lower() == "csv":
            # For CSV format, we'd need to flatten the data structure
            # This is a simplified CSV representation
            csv_data = "Content ID,Platform,Performance Score,Engagement Rate,Reach,Impressions\n"
            
            for content_item in export_data["content_analytics"]:
                if "analytics" in content_item:
                    analytics = content_item["analytics"]
                    for platform, data in analytics.get("platform_performance", {}).items():
                        indicators = data.get("performance_indicators", {})
                        metrics = data.get("raw_metrics", {})
                        
                        csv_data += f"{content_item['content_id']},{platform},"
                        csv_data += f"{indicators.get('performance_score', 0)},"
                        csv_data += f"{indicators.get('engagement_rate', 0)},"
                        csv_data += f"{metrics.get('reach_count', 0)},"
                        csv_data += f"{metrics.get('impression_count', 0)}\n"
            
            return {
                "success": True,
                "data": csv_data,
                "format": "csv",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format: {format}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting analytics data: {str(e)}"
        )

@router.get("/health")
async def get_analytics_service_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get health status of the analytics service
    """
    try:
        analytics_service = get_analytics_service(db)
        health_status = await analytics_service.get_service_health()
        
        return {
            "success": True,
            "data": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving service health: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_analytics_data(
    max_age_days: int = Query(90, description="Maximum age of data to keep in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old analytics data
    """
    try:
        analytics_service = get_analytics_service(db)
        cleanup_result = await analytics_service.cleanup_old_data(max_age_days)
        
        if cleanup_result["success"]:
            return {
                "success": True,
                "message": "Data cleanup completed successfully",
                "data": cleanup_result["cleanup_results"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cleanup data: {cleanup_result.get('error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during data cleanup: {str(e)}"
        )




