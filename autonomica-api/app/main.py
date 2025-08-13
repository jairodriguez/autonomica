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
from fastapi import FastAPI, HTTPException, Depends, Request, Query
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