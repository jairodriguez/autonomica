"""
SEO Data Processing Pipeline API Routes
Provides endpoints for executing comprehensive SEO analysis pipelines
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.seo_data_pipeline import (
    create_seo_data_pipeline, 
    SEODataPipeline, 
    KeywordResearchRequest,
    PipelineResult,
    PipelineStatus
)

# Initialize router
router = APIRouter(prefix="/api/seo/pipeline", tags=["SEO Pipeline"])

# Pydantic models for request/response
class PipelineExecuteRequest(BaseModel):
    """Request to execute an SEO analysis pipeline"""
    primary_keywords: List[str] = Field(..., description="List of primary keywords to analyze", min_items=1, max_items=100)
    competitor_domains: List[str] = Field(..., description="List of competitor domains to analyze", min_items=1, max_items=50)
    target_database: str = Field(default="us", description="Target database for keyword research (us, uk, ca, etc.)")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth: basic, comprehensive, or deep")
    include_competitors: bool = Field(default=True, description="Whether to include competitor analysis")
    include_clustering: bool = Field(default=True, description="Whether to include keyword clustering")
    include_opportunity_analysis: bool = Field(default=True, description="Whether to include opportunity analysis")
    max_keywords_per_analysis: int = Field(default=100, description="Maximum keywords to analyze", ge=1, le=1000)
    max_competitors_per_domain: int = Field(default=20, description="Maximum competitors to analyze per domain", ge=1, le=100)

class PipelineStatusResponse(BaseModel):
    """Response for pipeline status check"""
    pipeline_id: str
    status: str
    current_stage: Optional[str] = None
    stages_completed: List[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    progress_percentage: float
    estimated_time_remaining: Optional[str] = None
    errors: List[str] = None

class PipelineListResponse(BaseModel):
    """Response for listing pipelines"""
    active_pipelines: List[PipelineStatusResponse]
    completed_pipelines: List[PipelineStatusResponse]
    total_count: int

class PipelineInsightsResponse(BaseModel):
    """Response for pipeline insights"""
    pipeline_id: str
    summary: Dict[str, Any]
    key_findings: List[Dict[str, Any]]
    recommendations: List[str]
    opportunities: List[Dict[str, Any]]
    risks: List[str]

# Global pipeline instance (in production, this would be managed by a service layer)
_pipeline_instance: Optional[SEODataPipeline] = None

async def get_pipeline_instance() -> SEODataPipeline:
    """Get or create the global pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = await create_seo_data_pipeline()
    return _pipeline_instance

@router.post("/execute", response_model=Dict[str, Any])
async def execute_pipeline(
    request: PipelineExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Execute a comprehensive SEO analysis pipeline
    
    This endpoint initiates a complete SEO analysis including:
    - Keyword research and analysis
    - Competitor analysis
    - Keyword clustering
    - Opportunity identification
    - Comprehensive insights generation
    """
    try:
        # Convert request to internal format
        pipeline_request = KeywordResearchRequest(
            primary_keywords=request.primary_keywords,
            competitor_domains=request.competitor_domains,
            target_database=request.target_database,
            analysis_depth=request.analysis_depth,
            include_competitors=request.include_competitors,
            include_clustering=request.include_clustering,
            include_opportunity_analysis=request.include_opportunity_analysis,
            max_keywords_per_analysis=request.max_keywords_per_analysis,
            max_competitors_per_domain=request.max_competitors_per_domain
        )
        
        # Execute pipeline in background
        pipeline_result = await pipeline.execute_pipeline(pipeline_request)
        
        return {
            "pipeline_id": pipeline_result.pipeline_id,
            "status": pipeline_result.status.value,
            "message": "Pipeline execution started successfully",
            "estimated_completion_time": "5-10 minutes depending on analysis depth",
            "stages_to_execute": [
                "keyword_research",
                "competitor_analysis" if request.include_competitors else None,
                "keyword_clustering" if request.include_clustering else None,
                "keyword_analysis" if request.include_opportunity_analysis else None,
                "insights_generation",
                "report_generation"
            ],
            "monitor_url": f"/api/seo/pipeline/status/{pipeline_result.pipeline_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute pipeline: {str(e)}"
        )

@router.get("/status/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    pipeline_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Get the current status of a pipeline execution
    """
    try:
        pipeline_result = await pipeline.get_pipeline_status(pipeline_id)
        
        if not pipeline_result:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        # Calculate progress percentage
        total_stages = 6  # Total possible stages
        completed_stages = len(pipeline_result.stages_completed)
        progress_percentage = (completed_stages / total_stages) * 100
        
        # Estimate time remaining
        estimated_time_remaining = None
        if pipeline_result.status == PipelineStatus.IN_PROGRESS and pipeline_result.start_time:
            elapsed_time = datetime.now() - pipeline_result.start_time
            if completed_stages > 0:
                avg_time_per_stage = elapsed_time / completed_stages
                remaining_stages = total_stages - completed_stages
                estimated_remaining = avg_time_per_stage * remaining_stages
                estimated_time_remaining = str(estimated_remaining).split('.')[0]  # Remove microseconds
        
        return PipelineStatusResponse(
            pipeline_id=pipeline_result.pipeline_id,
            status=pipeline_result.status.value,
            current_stage=pipeline_result.current_stage.value if pipeline_result.current_stage else None,
            stages_completed=[stage.value for stage in pipeline_result.stages_completed],
            start_time=pipeline_result.start_time,
            end_time=pipeline_result.end_time,
            progress_percentage=round(progress_percentage, 1),
            estimated_time_remaining=estimated_time_remaining,
            errors=pipeline_result.errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline status: {str(e)}"
        )

@router.get("/list", response_model=PipelineListResponse)
async def list_pipelines(
    status: Optional[str] = Query(None, description="Filter by status (active, completed, failed)"),
    limit: int = Query(20, description="Maximum number of pipelines to return", ge=1, le=100),
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    List all pipelines with optional status filtering
    """
    try:
        # Get pipeline statistics
        stats = pipeline.get_pipeline_statistics()
        
        # For now, return basic information
        # In a full implementation, this would query a database
        active_pipelines = []
        completed_pipelines = []
        
        # Add active pipelines
        for pipeline_id, pipeline_result in pipeline.active_pipelines.items():
            active_pipelines.append(PipelineStatusResponse(
                pipeline_id=pipeline_id,
                status=pipeline_result.status.value,
                current_stage=pipeline_result.current_stage.value if pipeline_result.current_stage else None,
                stages_completed=[stage.value for stage in pipeline_result.stages_completed],
                start_time=pipeline_result.start_time,
                end_time=pipeline_result.end_time,
                progress_percentage=0.0,  # Would calculate based on current stage
                estimated_time_remaining=None,
                errors=pipeline_result.errors
            ))
        
        # Add completed pipelines from cache
        for pipeline_id, pipeline_result in pipeline.pipeline_cache.items():
            if pipeline_result.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
                completed_pipelines.append(PipelineStatusResponse(
                    pipeline_id=pipeline_id,
                    status=pipeline_result.status.value,
                    current_stage=None,
                    stages_completed=[stage.value for stage in pipeline_result.stages_completed],
                    start_time=pipeline_result.start_time,
                    end_time=pipeline_result.end_time,
                    progress_percentage=100.0,
                    estimated_time_remaining=None,
                    errors=pipeline_result.errors
                ))
        
        # Apply status filter
        if status:
            if status.lower() == "active":
                completed_pipelines = []
            elif status.lower() == "completed":
                active_pipelines = []
            elif status.lower() == "failed":
                active_pipelines = []
                completed_pipelines = [p for p in completed_pipelines if p.status == "failed"]
        
        # Apply limit
        active_pipelines = active_pipelines[:limit]
        completed_pipelines = completed_pipelines[:limit]
        
        return PipelineListResponse(
            active_pipelines=active_pipelines,
            completed_pipelines=completed_pipelines,
            total_count=len(active_pipelines) + len(completed_pipelines)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list pipelines: {str(e)}"
        )

@router.get("/insights/{pipeline_id}", response_model=PipelineInsightsResponse)
async def get_pipeline_insights(
    pipeline_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Get insights and analysis results from a completed pipeline
    """
    try:
        pipeline_result = await pipeline.get_pipeline_status(pipeline_id)
        
        if not pipeline_result:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        if pipeline_result.status != PipelineStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline {pipeline_id} is not completed. Current status: {pipeline_result.status.value}"
            )
        
        # Extract insights from pipeline results
        insights = pipeline_result.results.get("insights", {})
        
        return PipelineInsightsResponse(
            pipeline_id=pipeline_id,
            summary=insights.get("summary", {}),
            key_findings=insights.get("key_findings", []),
            recommendations=insights.get("recommendations", []),
            opportunities=insights.get("opportunities", []),
            risks=insights.get("risks", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline insights: {str(e)}"
        )

@router.get("/report/{pipeline_id}")
async def get_pipeline_report(
    pipeline_id: str,
    format: str = Query("json", description="Report format: json, html, or pdf"),
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Get the complete report from a completed pipeline
    """
    try:
        pipeline_result = await pipeline.get_pipeline_status(pipeline_id)
        
        if not pipeline_result:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found"
            )
        
        if pipeline_result.status != PipelineStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Pipeline {pipeline_id} is not completed. Current status: {pipeline_result.status.value}"
            )
        
        # Get the comprehensive report
        report = pipeline_result.results.get("report", {})
        
        if format.lower() == "json":
            return report
        elif format.lower() == "html":
            # Convert to HTML format (simplified)
            html_content = f"""
            <html>
            <head><title>SEO Pipeline Report - {pipeline_id}</title></head>
            <body>
                <h1>SEO Analysis Pipeline Report</h1>
                <h2>Pipeline ID: {pipeline_id}</h2>
                <h3>Executive Summary</h3>
                <p>Status: {report.get('executive_summary', {}).get('status', 'Unknown')}</p>
                <p>Execution Date: {report.get('executive_summary', {}).get('execution_date', 'Unknown')}</p>
                <p>Stages Completed: {report.get('executive_summary', {}).get('stages_completed', 0)}</p>
                
                <h3>Key Insights</h3>
                <ul>
                    {''.join([f'<li>{finding.get("description", "No description")}</li>' for finding in report.get('insights', {}).get('key_findings', [])])}
                </ul>
                
                <h3>Recommendations</h3>
                <ul>
                    {''.join([f'<li>{rec}</li>' for rec in report.get('insights', {}).get('recommendations', [])])}
                </ul>
            </body>
            </html>
            """
            return {"html": html_content}
        elif format.lower() == "pdf":
            # For PDF, we would need additional libraries like reportlab or weasyprint
            raise HTTPException(
                status_code=400,
                detail="PDF format not yet implemented"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {format}. Supported formats: json, html, pdf"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline report: {str(e)}"
        )

@router.delete("/cancel/{pipeline_id}")
async def cancel_pipeline(
    pipeline_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Cancel a running pipeline
    """
    try:
        success = await pipeline.cancel_pipeline(pipeline_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Pipeline {pipeline_id} not found or not running"
            )
        
        return {
            "message": f"Pipeline {pipeline_id} cancelled successfully",
            "pipeline_id": pipeline_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel pipeline: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_expired_pipelines(
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Clean up expired pipeline cache entries
    """
    try:
        await pipeline.cleanup_expired_cache()
        
        return {
            "message": "Pipeline cache cleanup completed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup expired pipelines: {str(e)}"
        )

@router.get("/statistics")
async def get_pipeline_statistics(
    current_user: ClerkUser = Depends(get_current_user),
    pipeline: SEODataPipeline = Depends(get_pipeline_instance)
):
    """
    Get pipeline execution statistics
    """
    try:
        stats = pipeline.get_pipeline_statistics()
        
        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline statistics: {str(e)}"
        )
