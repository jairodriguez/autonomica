"""
Autonomica API - Main FastAPI Application
OWL (Optimized Workflow Language) powered multi-agent marketing system
"""

import os
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

from app.core.config import settings, validate_settings
from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.owl.workforce import Workforce
from loguru import logger

# Initial settings validation
try:
    validate_settings()
    logger.info("Configuration validated successfully.")
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    # Exit if essential configuration is missing
    exit(1)

# Pydantic Models
class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    agentContext: Dict[str, Any] = {}

# Lifespan manager for the application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management for initializing and shutting down the Workforce."""
    logger.info("🚀 Starting Autonomica API with OWL Framework")
    
    # Initialize Workforce with settings
    workforce = Workforce(
        default_model=getattr(settings, 'AI_MODEL', "gpt-4-turbo"),
        redis_url=settings.REDIS_URL
    )
    await workforce.initialize()
    
    # Store workforce in app state
    app.state.workforce = workforce
    
    logger.success("✅ OWL Workforce initialized and available.")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🔄 Shutting down OWL Workforce...")
    await app.state.workforce.shutdown()
    logger.info("✅ OWL Workforce shutdown complete.")

# FastAPI App Setup
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified and Secured Multi-agent Marketing Automation Platform",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from app.api.routes import health, agents, agent_management, tasks, workflows

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(agent_management.router, prefix="/api", tags=["agent-management"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(workflows.router, prefix="/api", tags=["workflows"])

# Static Files Configuration
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Health and Info Endpoints ---

@app.get("/")
async def root(request: Request):
    """Root endpoint with API information"""
    workforce = request.app.state.workforce
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "description": "Unified and Secured Multi-agent Marketing Automation Platform",
        "owl_framework": "production-active",
        "ai_provider": os.getenv("AI_PROVIDER", "not-set"),
        "agents_available": len(workforce.agents) if workforce else 0,
        "endpoints": {
            "health": "/api/health",
            "agents": "/api/agents",
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/agents")
async def get_agents(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get all available agents (authenticated endpoint)"""
    logger.info(f"User {current_user.user_id} requesting agent list.")
    workforce = request.app.state.workforce
    # NOTE: In a true multi-tenant system, this should filter agents belonging to the user.
    # The current agent implementation is global. This is a design flaw that should be addressed.
    return {
        "agents": [a.__dict__ for a in workforce.agents.values()] if workforce else [],
        "total": len(workforce.agents) if workforce else 0,
    }

@app.get("/api/ai/models")
async def get_ai_models(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get available AI models and their status"""
    logger.info(f"User {current_user.user_id} requesting AI model status.")
    workforce = request.app.state.workforce
    
    try:
        ai_status = await workforce.get_ai_status()
        return {
            "success": True,
            "data": ai_status
        }
    except Exception as e:
        logger.error(f"Failed to get AI model status: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {}
        }

@app.post("/api/ai/ollama/install")
async def install_ollama_model(
    model_request: dict,
    request: Request,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Install an Ollama model"""
    logger.info(f"User {current_user.user_id} requesting Ollama model installation.")
    workforce = request.app.state.workforce
    
    model_name = model_request.get("model_name")
    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")
    
    try:
        from .ai.ai_manager import ai_manager
        success = await ai_manager.install_ollama_model(model_name)
        
        return {
            "success": success,
            "model_name": model_name,
            "message": f"Model {model_name} {'installed successfully' if success else 'installation failed'}"
        }
    except Exception as e:
        logger.error(f"Failed to install Ollama model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/ollama/models")
async def list_ollama_models(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """List available Ollama models"""
    logger.info(f"User {current_user.user_id} requesting Ollama model list.")
    
    try:
        from .ai.ai_manager import ai_manager
        models = await ai_manager.list_ollama_models()
        
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {e}")
        return {
            "success": False,
            "error": str(e),
            "models": []
        }

@app.get("/api/ai/ollama/status")
async def get_ollama_status(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get Ollama service status and model statistics"""
    logger.info(f"User {current_user.user_id} requesting Ollama status.")
    
    try:
        from .ai.ai_manager import ai_manager
        status = await ai_manager.get_ollama_status()
        
        return {
            "success": True,
            "total_models": status.get("total_models", 0),
            "active_models": status.get("active_models", 0),
            "total_size": status.get("total_size", "0 GB"),
            "service_status": status.get("service_status", "unknown")
        }
    except Exception as e:
        logger.error(f"Failed to get Ollama status: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_models": 0,
            "active_models": 0,
            "total_size": "0 GB",
            "service_status": "error"
        }

@app.get("/api/ai/ollama/health")
async def check_ollama_health(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Check Ollama service health"""
    logger.info(f"User {current_user.user_id} requesting Ollama health check.")
    
    try:
        from .ai.ai_manager import ai_manager
        healthy = await ai_manager.check_ollama_health()
        
        return {
            "success": True,
            "healthy": healthy
        }
    except Exception as e:
        logger.error(f"Failed to check Ollama health: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/metrics")
async def get_ollama_metrics(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get Ollama performance metrics"""
    logger.info(f"User {current_user.user_id} requesting Ollama metrics.")
    
    try:
        from .ai.ai_manager import ai_manager
        metrics = await ai_manager.get_ollama_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        logger.error(f"Failed to get Ollama metrics: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": {}
        }

@app.get("/api/ai/ollama/recommendations")
async def get_ollama_recommendations(
    task_type: str = Query(..., description="Type of task for model recommendation"),
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get model recommendations based on task type"""
    logger.info(f"User {current_user.user_id} requesting model recommendations for {task_type}.")
    
    try:
        from .ai.ai_manager import ai_manager
        recommendations = await ai_manager.get_model_recommendations(task_type)
        
        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Failed to get model recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }

@app.delete("/api/ai/ollama/remove")
async def remove_ollama_model(
    model_request: dict,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Remove an Ollama model"""
    logger.info(f"User {current_user.user_id} requesting Ollama model removal.")
    
    model_name = model_request.get("model_name")
    if not model_name:
        raise HTTPException(status_code=400, detail="model_name is required")
    
    try:
        from .ai.ai_manager import ai_manager
        success = await ai_manager.remove_ollama_model(model_name)
        
        return {
            "success": success,
            "model_name": model_name,
            "message": f"Model {model_name} {'removed successfully' if success else 'removal failed'}"
        }
    except Exception as e:
        logger.error(f"Failed to remove Ollama model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ollama-dashboard")
async def serve_ollama_dashboard(request: Request):
    """Serve the Ollama management dashboard"""
    from fastapi.responses import FileResponse
    import os
    
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "ollama_dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/ollama-performance-dashboard")
async def serve_ollama_performance_dashboard(request: Request):
    """Serve the Ollama performance dashboard"""
    try:
        with open("ollama-performance-dashboard.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dashboard file not found")

# --- Secure Chat Endpoint ---

@app.post("/api/chat")
async def chat_endpoint(chat_req: ChatRequest, fastapi_request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """
    Handle chat interactions with real AI agents.
    This endpoint is protected and requires a valid Clerk token.
    """
    logger.info(f"Chat request received for user: {current_user.user_id}")
    workforce = fastapi_request.app.state.workforce

    if not chat_req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    try:
        chat_history = [msg.dict() for msg in chat_req.messages]
        orchestration = await workforce.run_agents(
            chat_history, 
            user_id=current_user.user_id
        )
        
        agent = orchestration.get("agent")
        response_text = orchestration.get("response", "No response generated.")

        async def stream_response():
            words = response_text.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": f"msg_{datetime.now().timestamp()}",
                    "role": "assistant",
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent.name if agent else "unified-owl-agent",
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)

            yield f"data: [DONE]\n\n"

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Content-Type-Options": "nosniff"
            }
        )

    except Exception as e:
        logger.error(f"Chat processing error for user {current_user.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

@app.get("/api/ai/ollama/performance/summary")
async def get_ollama_performance_summary(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get comprehensive Ollama performance summary"""
    logger.info(f"User {current_user.user_id} requesting Ollama performance summary.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        summary = await ollama_performance_monitor.get_ollama_performance_summary()
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get Ollama performance summary: {e}")
        return {
            "success": False,
            "error": str(e),
            "summary": {}
        }

@app.get("/api/ai/ollama/performance/metrics/{model_name}")
async def get_ollama_model_performance(
    model_name: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get performance metrics for a specific Ollama model"""
    logger.info(f"User {current_user.user_id} requesting performance metrics for model {model_name}.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        metrics = ollama_performance_monitor.get_model_performance(model_name)
        
        if metrics:
            return {
                "success": True,
                "metrics": {
                    "model_name": metrics.model_name,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "avg_response_time_ms": metrics.avg_response_time_ms,
                    "success_rate": metrics.success_rate,
                    "performance_score": metrics.performance_score,
                    "last_used": metrics.last_used.isoformat() if metrics.last_used else None
                }
            }
        else:
            return {
                "success": False,
                "error": f"No performance data found for model {model_name}",
                "metrics": None
            }
            
    except Exception as e:
        logger.error(f"Failed to get performance metrics for model {model_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": None
        }

@app.get("/api/ai/ollama/performance/alerts")
async def get_ollama_performance_alerts(
    severity: Optional[str] = Query(None, description="Filter alerts by severity (low, medium, high, critical)"),
    limit: int = Query(50, description="Maximum number of alerts to return"),
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get Ollama performance alerts"""
    logger.info(f"User {current_user.user_id} requesting Ollama performance alerts.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        # Get recent alerts
        recent_alerts = list(ollama_performance_monitor.performance_alerts)[-limit:]
        
        # Filter by severity if specified
        if severity:
            recent_alerts = [a for a in recent_alerts if a.severity == severity]
        
        alerts_data = [
            {
                "timestamp": alert.timestamp.isoformat(),
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "model_name": alert.model_name,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "recommendation": alert.recommendation
            }
            for alert in recent_alerts
        ]
        
        return {
            "success": True,
            "alerts": alerts_data,
            "total_alerts": len(alerts_data),
            "severity_filter": severity
        }
        
    except Exception as e:
        logger.error(f"Failed to get Ollama performance alerts: {e}")
        return {
            "success": False,
            "error": str(e),
            "alerts": []
        }

@app.get("/api/ai/ollama/performance/system")
async def get_ollama_system_metrics(
    hours: int = Query(24, description="Number of hours of system metrics to return"),
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get Ollama system metrics"""
    logger.info(f"User {current_user.user_id} requesting Ollama system metrics.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        # Get system metrics for the specified time period
        system_metrics = ollama_performance_monitor.get_resource_history(hours)
        
        metrics_data = [
            {
                "timestamp": metric.timestamp.isoformat(),
                "cpu_usage_percent": metric.cpu_percent,
                "memory_usage_percent": metric.memory_percent,
                "memory_available_gb": metric.memory_available_gb,
                "disk_usage_percent": metric.disk_usage_percent
            }
            for metric in system_metrics
        ]
        
        return {
            "success": True,
            "metrics": metrics_data,
            "total_metrics": len(metrics_data),
            "time_period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get Ollama system metrics: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": []
        }

@app.post("/api/ai/ollama/performance/export")
async def export_ollama_metrics(
    export_request: dict,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Export Ollama performance metrics"""
    logger.info(f"User {current_user.user_id} requesting Ollama metrics export.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        format_type = export_request.get("format", "json")
        filepath = export_request.get("filepath")
        
        if format_type not in ["json", "csv"]:
            raise ValueError("Export format must be 'json' or 'csv'")
        
        exported_file = await ollama_performance_monitor.export_ollama_metrics(format_type, filepath)
        
        return {
            "success": True,
            "exported_file": exported_file,
            "format": format_type,
            "message": f"Metrics exported successfully to {exported_file}"
        }
        
    except Exception as e:
        logger.error(f"Failed to export Ollama metrics: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/ollama/performance/cleanup")
async def cleanup_ollama_metrics(
    cleanup_request: dict,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Clean up old Ollama performance metrics"""
    logger.info(f"User {current_user.user_id} requesting Ollama metrics cleanup.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        days_to_keep = cleanup_request.get("days_to_keep", 30)
        
        if not isinstance(days_to_keep, int) or days_to_keep < 1:
            raise ValueError("days_to_keep must be a positive integer")
        
        await ollama_performance_monitor.cleanup_old_metrics(days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleaned up metrics older than {days_to_keep} days",
            "days_to_keep": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup Ollama metrics: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/ollama/performance/monitoring/start")
async def start_ollama_performance_monitoring(
    monitoring_request: dict,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Start Ollama performance monitoring"""
    logger.info(f"User {current_user.user_id} starting Ollama performance monitoring.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        interval = monitoring_request.get("interval", 5.0)
        
        if not isinstance(interval, (int, float)) or interval < 1.0:
            raise ValueError("interval must be a number >= 1.0")
        
        await ollama_performance_monitor.start_ollama_monitoring(interval)
        
        return {
            "success": True,
            "message": f"Ollama performance monitoring started with {interval}s interval",
            "monitoring_active": ollama_performance_monitor.is_monitoring,
            "interval_seconds": interval
        }
        
    except Exception as e:
        logger.error(f"Failed to start Ollama performance monitoring: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/ollama/performance/monitoring/stop")
async def stop_ollama_performance_monitoring(
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Stop Ollama performance monitoring"""
    logger.info(f"User {current_user.user_id} stopping Ollama performance monitoring.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        await ollama_performance_monitor.stop_monitoring()
        
        return {
            "success": True,
            "message": "Ollama performance monitoring stopped",
            "monitoring_active": ollama_performance_monitor.is_monitoring
        }
        
    except Exception as e:
        logger.error(f"Failed to stop Ollama performance monitoring: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/performance/status")
async def get_ollama_performance_monitoring_status(
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get Ollama performance monitoring status"""
    logger.info(f"User {current_user.user_id} requesting Ollama performance monitoring status.")
    
    try:
        from .ai.ollama_performance_monitor import ollama_performance_monitor
        
        status = {
            "monitoring_active": ollama_performance_monitor.is_monitoring,
            "monitoring_interval": ollama_performance_monitor.monitoring_interval,
            "gpu_available": ollama_performance_monitor.gpu_available,
            "total_ollama_metrics": len(ollama_performance_monitor.ollama_metrics),
            "total_system_metrics": len(ollama_performance_monitor.system_metrics),
            "total_alerts": len(ollama_performance_monitor.performance_alerts),
            "storage_path": str(ollama_performance_monitor.storage_path)
        }
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get Ollama performance monitoring status: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": {}
        }

# --- Ollama Extended Model Library Endpoints ---

@app.get("/api/ai/ollama/models/library")
async def get_model_library(request: Request, current_user: ClerkUser = Depends(get_current_user)):
    """Get comprehensive model library information"""
    logger.info(f"User {current_user.user_id} requesting model library information.")
    
    try:
        from .ai.ollama_model_library import ollama_model_library
        categories = await ollama_model_library.get_model_categories()
        
        return {
            "success": True,
            "categories": {cat.value: models for cat, models in categories.items()}
        }
    except Exception as e:
        logger.error(f"Failed to get model library: {e}")
        return {
            "success": False,
            "error": str(e),
            "categories": {}
        }

@app.get("/api/ai/ollama/models/search")
async def search_models(
    query: str,
    category: Optional[str] = None,
    size: Optional[str] = None,
    min_performance: Optional[float] = None,
    max_parameters: Optional[int] = None,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Search models with filters"""
    logger.info(f"User {current_user.user_id} searching models with query: {query}")
    
    try:
        from .ai.ollama_model_library import ollama_model_library
        
        filters = {}
        if category:
            filters["category"] = category
        if size:
            filters["size"] = size
        if min_performance:
            filters["min_performance"] = min_performance
        if max_parameters:
            filters["max_parameters"] = max_parameters
        
        results = await ollama_model_library.search_models(query, filters)
        
        return {
            "success": True,
            "query": query,
            "filters": filters,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Failed to search models: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }

@app.get("/api/ai/ollama/models/recommendations")
async def get_model_recommendations(
    task_type: str,
    preferred_size: Optional[str] = None,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get model recommendations for a specific task"""
    logger.info(f"User {current_user.user_id} requesting model recommendations for task: {task_type}")
    
    try:
        from .ai.ollama_model_library import ollama_model_library
        
        # Mock system info for now - in production, this would come from actual system monitoring
        system_info = {
            "available_memory_gb": 16.0,
            "gpu_available": True,
            "gpu_memory_gb": 8.0,
            "high_performance_cpu": True
        }
        
        preferences = {}
        if preferred_size:
            preferences["preferred_size"] = preferred_size
        
        recommendations = await ollama_model_library.get_model_recommendations(task_type, system_info, preferences)
        
        return {
            "success": True,
            "task_type": task_type,
            "system_info": system_info,
            "preferences": preferences,
            "recommendations": [
                {
                    "model_name": rec.model_name,
                    "confidence_score": rec.confidence_score,
                    "reasoning": rec.reasoning,
                    "expected_performance": rec.expected_performance,
                    "alternatives": rec.alternatives,
                    "trade_offs": rec.trade_offs
                }
                for rec in recommendations
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get model recommendations: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        }

@app.get("/api/ai/ollama/models/compatibility/{model_name}")
async def check_model_compatibility(
    model_name: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Check model compatibility with current system"""
    logger.info(f"User {current_user.user_id} checking compatibility for model: {model_name}")
    
    try:
        from .ai.ollama_model_library import ollama_model_library
        
        # Mock system info for now
        system_info = {
            "available_memory_gb": 16.0,
            "gpu_available": True,
            "gpu_memory_gb": 8.0,
            "high_performance_cpu": True
        }
        
        compatibility = await ollama_model_library.check_model_compatibility(model_name, system_info)
        
        return {
            "success": True,
            "model_name": model_name,
            "compatibility": {
                "compatibility_score": compatibility.compatibility_score,
                "hardware_compatibility": compatibility.hardware_compatibility,
                "warnings": compatibility.warnings,
                "recommendations": compatibility.recommendations,
                "performance_estimate": compatibility.performance_estimate
            }
        }
    except Exception as e:
        logger.error(f"Failed to check model compatibility: {e}")
        return {
            "success": False,
            "error": str(e),
            "compatibility": {}
        }

@app.get("/api/ai/ollama/models/compare")
async def compare_models(
    models: str,  # Comma-separated model names
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Compare multiple models side by side"""
    logger.info(f"User {current_user.user_id} comparing models: {models}")
    
    try:
        from .ai.ollama_model_library import ollama_model_library
        
        model_names = [name.strip() for name in models.split(",")]
        comparison = await ollama_model_library.get_model_comparison(model_names)
        
        return {
            "success": True,
            "models": comparison["models"],
            "comparison_table": comparison["comparison_table"],
            "recommendations": comparison["recommendations"]
        }
    except Exception as e:
        logger.error(f"Failed to compare models: {e}")
        return {
            "success": False,
            "error": str(e),
            "comparison": {}
        }

# --- Ollama Fine-Tuning Endpoints ---

@app.post("/api/ai/ollama/fine-tuning/create")
async def create_fine_tuning_job(
    request: Request,
    current_user: ClerkUser = Depends(get_current_user),
    base_model: str = Form(...),
    target_model_name: str = Form(...),
    training_data_path: str = Form(...),
    data_type: str = Form(...),
    hyperparameters: str = Form("balanced"),  # JSON string or preset name
    target_capabilities: Optional[str] = Form(None)  # JSON string
):
    """Create a new fine-tuning job"""
    logger.info(f"User {current_user.user_id} creating fine-tuning job for {target_model_name}")
    
    try:
        from .ai.ollama_fine_tuning import ollama_fine_tuning_manager, TrainingData
        
        # Parse hyperparameters
        if hyperparameters in ["efficient", "balanced", "high_quality", "custom"]:
            hyperparam_preset = hyperparameters
        else:
            try:
                hyperparam_preset = json.loads(hyperparameters)
            except json.JSONDecodeError:
                hyperparam_preset = "balanced"
        
        # Parse target capabilities
        capabilities = set()
        if target_capabilities:
            try:
                cap_list = json.loads(target_capabilities)
                from .ai.ollama_model_library import ModelCapability
                capabilities = {ModelCapability(cap) for cap in cap_list}
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Create training data
        training_data = TrainingData(
            data_path=training_data_path,
            data_type=data_type
        )
        
        # Create fine-tuning job
        job = await ollama_fine_tuning_manager.create_fine_tuning_job(
            base_model=base_model,
            target_model_name=target_model_name,
            training_data=training_data,
            hyperparameters=hyperparam_preset,
            target_capabilities=capabilities
        )
        
        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status.value,
            "message": f"Fine-tuning job created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create fine-tuning job: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/ollama/fine-tuning/start/{job_id}")
async def start_fine_tuning(
    job_id: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Start a fine-tuning job"""
    logger.info(f"User {current_user.user_id} starting fine-tuning job {job_id}")
    
    try:
        from .ai.ollama_fine_tuning import ollama_fine_tuning_manager
        
        success = await ollama_fine_tuning_manager.start_training(job_id)
        
        return {
            "success": success,
            "job_id": job_id,
            "message": "Fine-tuning job started successfully" if success else "Failed to start fine-tuning job"
        }
    except Exception as e:
        logger.error(f"Failed to start fine-tuning job {job_id}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/fine-tuning/status/{job_id}")
async def get_fine_tuning_status(
    job_id: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get fine-tuning job status"""
    logger.info(f"User {current_user.user_id} checking fine-tuning job {job_id}")
    
    try:
        from .ai.ollama_fine_tuning import ollama_fine_tuning_manager
        
        job = await ollama_fine_tuning_manager.get_training_status(job_id)
        
        if job:
            return {
                "success": True,
                "job": {
                    "job_id": job.job_id,
                    "base_model": job.base_model,
                    "target_model_name": job.target_model_name,
                    "status": job.status.value,
                    "current_phase": job.current_phase.value,
                    "progress": job.progress,
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None,
                    "error_message": job.error_message,
                    "logs": job.logs[-10:]  # Last 10 log entries
                }
            }
        else:
            return {
                "success": False,
                "error": "Job not found"
            }
    except Exception as e:
        logger.error(f"Failed to get fine-tuning status: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/fine-tuning/jobs")
async def list_fine_tuning_jobs(
    status: Optional[str] = None,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """List fine-tuning jobs"""
    logger.info(f"User {current_user.user_id} listing fine-tuning jobs")
    
    try:
        from .ai.ollama_fine_tuning import ollama_fine_tuning_manager, TrainingStatus
        
        status_filter = None
        if status:
            try:
                status_filter = TrainingStatus(status)
            except ValueError:
                pass
        
        jobs = await ollama_fine_tuning_manager.list_training_jobs(status_filter)
        
        return {
            "success": True,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "base_model": job.base_model,
                    "target_model_name": job.target_model_name,
                    "status": job.status.value,
                    "current_phase": job.current_phase.value,
                    "progress": job.progress,
                    "start_time": job.start_time.isoformat() if job.start_time else None,
                    "end_time": job.end_time.isoformat() if job.end_time else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list fine-tuning jobs: {e}")
        return {
            "success": False,
            "error": str(e),
            "jobs": []
        }

# --- Ollama Parameter Optimization Endpoints ---

@app.post("/api/ai/ollama/optimization/create")
async def create_optimization_session(
    request: Request,
    current_user: ClerkUser = Depends(get_current_user),
    model_name: str = Form(...),
    objective: str = Form(...),
    strategy: str = Form("bayesian_optimization"),
    model_type: str = Form("general")
):
    """Create a new parameter optimization session"""
    logger.info(f"User {current_user.user_id} creating optimization session for {model_name}")
    
    try:
        from .ai.ollama_parameter_optimizer import (
            ollama_parameter_optimizer, 
            OptimizationObjective, 
            OptimizationStrategy
        )
        
        # Parse enums
        try:
            opt_objective = OptimizationObjective(objective)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid objective: {objective}. Valid options: {[obj.value for obj in OptimizationObjective]}"
            }
        
        try:
            opt_strategy = OptimizationStrategy(strategy)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid strategy: {strategy}. Valid options: {[strat.value for strat in OptimizationStrategy]}"
            }
        
        # Create optimization session
        session = await ollama_parameter_optimizer.create_optimization_session(
            model_name=model_name,
            objective=opt_objective,
            strategy=opt_strategy,
            model_type=model_type
        )
        
        return {
            "success": True,
            "session_id": session.session_id,
            "model_name": session.model_name,
            "objective": session.config.objective.value,
            "strategy": session.config.strategy.value,
            "message": "Optimization session created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create optimization session: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/ai/ollama/optimization/start/{session_id}")
async def start_optimization(
    session_id: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Start parameter optimization"""
    logger.info(f"User {current_user.user_id} starting optimization session {session_id}")
    
    try:
        from .ai.ollama_parameter_optimizer import ollama_parameter_optimizer
        
        success = await ollama_parameter_optimizer.start_optimization(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Optimization started successfully" if success else "Failed to start optimization"
        }
    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/optimization/status/{session_id}")
async def get_optimization_status(
    session_id: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get optimization session status"""
    logger.info(f"User {current_user.user_id} checking optimization session {session_id}")
    
    try:
        from .ai.ollama_parameter_optimizer import ollama_parameter_optimizer
        
        session = await ollama_parameter_optimizer.get_optimization_status(session_id)
        
        if session:
            return {
                "success": True,
                "session": {
                    "session_id": session.session_id,
                    "model_name": session.model_name,
                    "status": session.status,
                    "objective": session.config.objective.value,
                    "strategy": session.config.strategy.value,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "current_iteration": session.current_iteration,
                    "best_result": {
                        "overall_score": session.best_result.overall_score,
                        "parameters": session.best_result.parameters
                    } if session.best_result else None
                }
            }
        else:
            return {
                "success": False,
                "error": "Session not found"
            }
    except Exception as e:
        logger.error(f"Failed to get optimization status: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/ai/ollama/optimization/sessions")
async def list_optimization_sessions(
    status: Optional[str] = None,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """List optimization sessions"""
    logger.info(f"User {current_user.user_id} listing optimization sessions")
    
    try:
        from .ai.ollama_parameter_optimizer import ollama_parameter_optimizer
        
        sessions = await ollama_parameter_optimizer.list_optimization_sessions(status)
        
        return {
            "success": True,
            "sessions": [
                {
                    "session_id": session.session_id,
                    "model_name": session.model_name,
                    "status": session.status,
                    "objective": session.config.objective.value,
                    "strategy": session.config.strategy.value,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat() if session.end_time else None,
                    "current_iteration": session.current_iteration
                }
                for session in sessions
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list optimization sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "jobs": []
        }

@app.get("/api/ai/ollama/optimization/best-parameters/{session_id}")
async def get_best_parameters(
    session_id: str,
    request: Request = None,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get best parameters from optimization session"""
    logger.info(f"User {current_user.user_id} getting best parameters for session {session_id}")
    
    try:
        from .ai.ollama_parameter_optimizer import ollama_parameter_optimizer
        
        best_params = await ollama_parameter_optimizer.get_best_parameters(session_id)
        
        if best_params:
            return {
                "success": True,
                "session_id": session_id,
                "best_parameters": best_params
            }
        else:
            return {
                "success": False,
                "error": "No best parameters found"
            }
    except Exception as e:
        logger.error(f"Failed to get best parameters: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# --- Main execution ---

if __name__ == "__main__":
    import uvicorn

    logger.info("🦉 Starting Autonomica Unified API...")
    logger.info(f"⚙️ Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"🛡️ CORS Origins: {settings.ALLOWED_ORIGINS}")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    ) 