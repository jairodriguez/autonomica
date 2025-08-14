"""
Autonomica API - Main FastAPI Application
OWL (Optimized Workflow Language) powered multi-agent marketing system
"""

import os
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
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

# --- SEO Research and Analysis Endpoints ---

@app.post("/api/seo/analyze")
async def analyze_keyword(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Perform comprehensive SEO analysis for a target keyword"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Perform analysis
        analysis = await seo_service.analyze_keyword(
            keyword=request.get("keyword"),
            domain=request.get("domain")
        )
        
        return {
            "success": True,
            "analysis": analysis.dict(),
            "processing_time_ms": 0  # Placeholder
        }
        
    except Exception as e:
        logger.error(f"Error during SEO analysis for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }

@app.post("/api/seo/research")
async def research_keywords(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Research related keywords and identify opportunities"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Get related keywords
        related_keywords = await seo_service.semrush_client.get_related_keywords(
            request.get("seed_keyword"), 
            request.get("max_related", 50)
        )
        
        # Get data for each related keyword (limit to top 20 for performance)
        keyword_records = []
        total_volume = 0
        difficulties = []
        cpcs = []
        
        for keyword in related_keywords[:20]:
            try:
                record = await seo_service.semrush_client.get_keyword_data(keyword)
                if record.search_volume and record.difficulty and record.cpc:
                    # Apply filters if provided
                    min_volume = request.get("min_volume")
                    max_difficulty = request.get("max_difficulty")
                    
                    if (min_volume is None or record.search_volume >= min_volume) and \
                       (max_difficulty is None or record.difficulty <= max_difficulty):
                        keyword_records.append(record.dict())
                        total_volume += record.search_volume
                        difficulties.append(record.difficulty)
                        cpcs.append(record.cpc)
            except Exception as e:
                logger.warning(f"Could not get data for keyword {keyword}: {str(e)}")
                continue
        
        # Calculate averages
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
        avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0
        
        # Identify opportunities
        opportunities = []
        for record in keyword_records:
            if record.get("search_volume") and record.get("difficulty") and record.get("cpc"):
                if record["search_volume"] > 5000 and record["difficulty"] < 40:
                    opportunities.append(f"High volume ({record['search_volume']}) with low difficulty ({record['difficulty']}): {record['keyword']}")
                if record["cpc"] > 2.0:
                    opportunities.append(f"High CPC (${record['cpc']:.2f}): {record['keyword']}")
        
        return {
            "success": True,
            "seed_keyword": request.get("seed_keyword"),
            "related_keywords": keyword_records,
            "total_volume": total_volume,
            "avg_difficulty": avg_difficulty,
            "avg_cpc": avg_cpc,
            "opportunities": opportunities
        }
        
    except Exception as e:
        logger.error(f"Error during keyword research for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "seed_keyword": request.get("seed_keyword"),
            "related_keywords": [],
            "total_volume": 0,
            "avg_difficulty": 0,
            "avg_cpc": 0,
            "opportunities": [],
            "error": f"Research failed: {str(e)}"
        }

@app.post("/api/seo/serp")
async def research_serp(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Research search engine results page (SERP) for a keyword"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Get SERP results
        serp_results = await seo_service.scraper.scrape_serp(
            request.get("keyword"), 
            request.get("num_results", 10)
        )
        
        # Analyze SERP features
        featured_snippets = sum(1 for r in serp_results if r.featured_snippet)
        paa_questions = sum(1 for r in serp_results if r.paa_questions)
        
        # Competition analysis
        competition_analysis = {
            "total_results": len(serp_results),
            "featured_snippets": featured_snippets,
            "paa_questions": paa_questions,
            "top_domains": [r.url.split('/')[2] for r in serp_results[:5] if r.url],
            "avg_title_length": sum(len(r.title) for r in serp_results) / len(serp_results) if serp_results else 0
        }
        
        return {
            "success": True,
            "keyword": request.get("keyword"),
            "serp_results": [r.dict() for r in serp_results],
            "featured_snippets": featured_snippets,
            "paa_questions": paa_questions,
            "competition_analysis": competition_analysis
        }
        
    except Exception as e:
        logger.error(f"Error during SERP research for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "keyword": request.get("keyword"),
            "serp_results": [],
            "featured_snippets": 0,
            "paa_questions": 0,
            "competition_analysis": {},
            "error": f"SERP research failed: {str(e)}"
        }

@app.post("/api/seo/cluster")
async def cluster_keywords(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Cluster keywords based on semantic similarity"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Perform keyword clustering
        clusters = await seo_service._cluster_keywords(request.get("keywords", []))
        
        # Calculate clustering quality (simplified metric)
        total_keywords = len(request.get("keywords", []))
        clustering_quality = len(clusters) / max(1, total_keywords // 5)  # Normalize by expected cluster count
        
        return {
            "success": True,
            "clusters": [c.dict() for c in clusters],
            "total_keywords": total_keywords,
            "clustering_quality": min(clustering_quality, 1.0)
        }
        
    except Exception as e:
        logger.error(f"Error during keyword clustering for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "clusters": [],
            "total_keywords": len(request.get("keywords", [])),
            "clustering_quality": 0.0,
            "error": f"Clustering failed: {str(e)}"
        }

@app.post("/api/seo/opportunities")
async def find_opportunities(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Find SEO opportunities based on keyword criteria"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        opportunities = []
        total_volume = 0
        difficulties = []
        cpcs = []
        
        # Analyze each keyword for opportunities
        for keyword in request.get("keywords", []):
            try:
                record = await seo_service.semrush_client.get_keyword_data(keyword)
                if record.search_volume and record.difficulty and record.cpc:
                    min_volume = request.get("min_volume", 1000)
                    max_difficulty = request.get("max_difficulty", 50)
                    min_cpc = request.get("min_cpc", 1.0)
                    
                    if (record.search_volume >= min_volume and 
                        record.difficulty <= max_difficulty and 
                        record.cpc >= min_cpc):
                        
                        opportunity = {
                            "keyword": keyword,
                            "search_volume": record.search_volume,
                            "difficulty": record.difficulty,
                            "cpc": record.cpc,
                            "score": (record.search_volume / 1000) * (1 - record.difficulty / 100) * record.cpc
                        }
                        opportunities.append(opportunity)
                        
                        total_volume += record.search_volume
                        difficulties.append(record.difficulty)
                        cpcs.append(record.cpc)
                        
            except Exception as e:
                logger.warning(f"Could not analyze keyword {keyword}: {str(e)}")
                continue
        
        # Sort opportunities by score
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        
        # Calculate averages
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
        avg_cpc = sum(cpcs) / len(cpcs) if cpcs else 0
        
        # Generate recommendations
        recommendations = []
        if opportunities:
            if avg_difficulty < 30:
                recommendations.append("Low competition keywords detected - great opportunity for quick wins")
            if avg_cpc > 3.0:
                recommendations.append("High CPC keywords found - strong commercial potential")
            if len(opportunities) > 10:
                recommendations.append("Multiple opportunities available - consider content cluster strategy")
        
        return {
            "success": True,
            "opportunities": opportunities,
            "total_volume": total_volume,
            "avg_difficulty": avg_difficulty,
            "avg_cpc": avg_cpc,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Error during opportunity analysis for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "opportunities": [],
            "total_volume": 0,
            "avg_difficulty": 0,
            "avg_cpc": 0,
            "recommendations": [],
            "error": f"Opportunity analysis failed: {str(e)}"
        }

@app.get("/api/seo/health")
async def seo_service_health(
    current_user: ClerkUser = Depends(get_current_user)
):
    """Check SEO service health and configuration"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            return {
                "status": "unhealthy",
                "service": "SEO Research Service",
                "semrush_api": "not_configured",
                "web_scraper": "not_configured",
                "openai_api": "not_configured" if not openai_api_key else "configured",
                "user_id": current_user.user_id,
                "error": "SEMrush API key not configured"
            }
        
        # Create SEO service and test connectivity
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Test SEMrush API connectivity
        semrush_status = await seo_service.semrush_client.test_connection()
        
        # Test Web Scraper connectivity
        scraper_status = await seo_service.scraper.test_connection()
        
        # Get API quota information
        quota_info = await seo_service.semrush_client.get_api_quota_info()
        
        # Determine overall health
        overall_healthy = (
            semrush_status.get("status") == "connected" and 
            scraper_status.get("status") == "connected"
        )
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "service": "SEO Research Service",
            "semrush_api": semrush_status,
            "web_scraper": scraper_status,
            "openai_api": "configured" if openai_api_key else "not_configured",
            "quota_info": quota_info,
            "user_id": current_user.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking SEO service health: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "SEO Research Service",
            "error": f"Health check failed: {str(e)}"
        }

@app.post("/api/seo/scrape")
async def scrape_website(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Scrape a website for comprehensive SEO analysis"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Validate request
        url = request.get("url")
        if not url:
            raise HTTPException(
                status_code=400,
                detail="URL is required"
            )
        
        respect_robots = request.get("respect_robots", True)
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Scrape the website
        result = await seo_service.scraper.scrape_website(url, respect_robots)
        
        if result.get("error"):
            return {
                "success": False,
                "url": url,
                "error": result["error"]
            }
        
        return {
            "success": True,
            "url": url,
            "scraped_at": result.get("scraped_at"),
            "seo_data": {
                "title": result.get("title"),
                "meta_description": result.get("meta_description"),
                "meta_keywords": result.get("meta_keywords"),
                "canonical_url": result.get("canonical_url"),
                "robots": result.get("robots"),
                "language": result.get("language"),
                "charset": result.get("charset"),
                "content_analysis": result.get("content_analysis"),
                "links_analysis": result.get("links_analysis"),
                "images_analysis": result.get("images_analysis"),
                "social_tags": result.get("social_tags"),
                "structured_data": result.get("structured_data")
            }
        }
        
    except Exception as e:
        logger.error(f"Error scraping website for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "url": request.get("url", ""),
            "error": f"Scraping failed: {str(e)}"
        }

@app.post("/api/seo/scrape-multiple")
async def scrape_multiple_websites(
    request: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Scrape multiple websites for batch SEO analysis"""
    try:
        from app.services.seo_service import create_seo_service
        
        # Get configuration
        semrush_api_key = os.getenv("SEMRUSH_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not semrush_api_key:
            raise HTTPException(
                status_code=500,
                detail="SEMrush API key not configured. Please set SEMRUSH_API_KEY environment variable."
            )
        
        # Validate request
        urls = request.get("urls", [])
        if not urls or not isinstance(urls, list):
            raise HTTPException(
                status_code=400,
                detail="URLs list is required and must be an array"
            )
        
        if len(urls) > 50:  # Limit to prevent abuse
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 URLs allowed per request"
            )
        
        respect_robots = request.get("respect_robots", True)
        
        # Create SEO service
        seo_service = create_seo_service(
            semrush_api_key=semrush_api_key,
            openai_api_key=openai_api_key
        )
        
        # Scrape multiple websites
        results = await seo_service.scraper.scrape_multiple_urls(urls, respect_robots)
        
        # Count successes and failures
        successful = sum(1 for r in results if r.get("status") != "failed")
        failed = len(results) - successful
        
        return {
            "success": True,
            "total_urls": len(urls),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error scraping multiple websites for user {current_user.user_id}: {str(e)}")
        return {
            "success": False,
            "total_urls": len(request.get("urls", [])),
            "error": f"Batch scraping failed: {str(e)}"
        }

# SEO Research and Analysis Routes
@app.post("/api/seo/dashboard")
async def get_seo_dashboard():
    """Get comprehensive SEO dashboard data"""
    try:
        # This would typically fetch data from database/cache
        # For now, return sample dashboard data
        dashboard_data = {
            "overview": {
                "total_keywords_tracked": 150,
                "average_seo_score": 72.5,
                "top_performing_keywords": 25,
                "keywords_needing_attention": 18,
                "recent_improvements": 12
            },
            "performance_metrics": {
                "organic_traffic": {
                    "current": 15420,
                    "previous": 14200,
                    "change_percent": 8.6
                },
                "keyword_rankings": {
                    "top_3": 45,
                    "top_10": 89,
                    "top_100": 142
                },
                "click_through_rate": {
                    "current": 3.2,
                    "previous": 2.8,
                    "change_percent": 14.3
                }
            },
            "recent_activities": [
                {
                    "type": "keyword_improvement",
                    "description": "Improved ranking for 'digital marketing' from #8 to #3",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "impact": "high"
                },
                {
                    "type": "content_update",
                    "description": "Updated meta descriptions for 15 pages",
                    "timestamp": "2024-01-14T15:45:00Z",
                    "impact": "medium"
                }
            ],
            "quick_actions": [
                "Analyze new keyword opportunities",
                "Review technical SEO issues",
                "Generate content recommendations",
                "Check competitor analysis"
            ]
        }
        
        return {"success": True, "data": dashboard_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/reports/generate")
async def generate_seo_report(request: dict):
    """Generate comprehensive SEO report"""
    try:
        report_type = request.get("type", "comprehensive")
        date_range = request.get("date_range", "last_30_days")
        include_recommendations = request.get("include_recommendations", True)
        
        # Sample report data
        report_data = {
            "report_id": f"seo_report_{int(time.time())}",
            "type": report_type,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_pages_analyzed": 45,
                "average_seo_score": 74.2,
                "improvements_made": 23,
                "issues_found": 12
            },
            "detailed_analysis": {
                "on_page_seo": {
                    "score": 78.5,
                    "strengths": ["Optimized titles", "Good meta descriptions"],
                    "weaknesses": ["Missing alt text", "Poor internal linking"],
                    "recommendations": [
                        "Add alt text to all images",
                        "Improve internal linking structure"
                    ]
                },
                "technical_seo": {
                    "score": 82.1,
                    "strengths": ["Fast loading", "Mobile friendly"],
                    "weaknesses": ["Missing schema markup"],
                    "recommendations": [
                        "Implement structured data markup"
                    ]
                },
                "content_quality": {
                    "score": 71.3,
                    "strengths": ["Comprehensive content", "Good readability"],
                    "weaknesses": ["Outdated information", "Low engagement"],
                    "recommendations": [
                        "Update outdated content",
                        "Add interactive elements"
                    ]
                }
            },
            "keyword_performance": {
                "top_performers": [
                    {"keyword": "digital marketing", "position": 3, "traffic": 1200},
                    {"keyword": "seo tips", "position": 5, "traffic": 850},
                    {"keyword": "content marketing", "position": 7, "traffic": 650}
                ],
                "opportunities": [
                    {"keyword": "local seo", "current_position": 15, "potential_traffic": 400},
                    {"keyword": "ecommerce seo", "current_position": 22, "potential_traffic": 300}
                ]
            },
            "competitor_analysis": {
                "top_competitors": [
                    {"domain": "competitor1.com", "overlap_score": 0.85, "strength": "high"},
                    {"domain": "competitor2.com", "overlap_score": 0.72, "strength": "medium"}
                ],
                "content_gaps": [
                    "Video content for product demos",
                    "Comprehensive comparison guides"
                ]
            }
        }
        
        if include_recommendations:
            report_data["action_plan"] = {
                "immediate_actions": [
                    "Fix critical technical issues",
                    "Update meta descriptions",
                    "Add missing alt text"
                ],
                "short_term_goals": [
                    "Improve average SEO score to 80+",
                    "Rank in top 10 for 5 target keywords",
                    "Increase organic traffic by 15%"
                ],
                "long_term_strategy": [
                    "Develop comprehensive content calendar",
                    "Implement advanced analytics tracking",
                    "Build quality backlink profile"
                ]
            }
        
        return {"success": True, "data": report_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/keywords/track")
async def track_keyword(keyword_request: dict):
    """Track a new keyword for monitoring"""
    try:
        keyword = keyword_request.get("keyword")
        target_url = keyword_request.get("target_url")
        priority = keyword_request.get("priority", "medium")
        
        if not keyword:
            return {"success": False, "error": "Keyword is required"}
        
        # Sample tracking data
        tracking_data = {
            "keyword_id": f"kw_{int(time.time())}",
            "keyword": keyword,
            "target_url": target_url,
            "priority": priority,
            "added_at": datetime.now().isoformat(),
            "current_position": None,
            "best_position": None,
            "search_volume": None,
            "difficulty": None,
            "status": "tracking"
        }
        
        return {"success": True, "data": tracking_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/seo/keywords/tracking")
async def get_tracked_keywords():
    """Get all tracked keywords"""
    try:
        # Sample tracked keywords data
        tracked_keywords = [
            {
                "keyword_id": "kw_1",
                "keyword": "digital marketing",
                "target_url": "/digital-marketing-guide",
                "priority": "high",
                "added_at": "2024-01-01T00:00:00Z",
                "current_position": 3,
                "best_position": 3,
                "search_volume": 12000,
                "difficulty": 65,
                "status": "tracking",
                "trend": "improving"
            },
            {
                "keyword_id": "kw_2",
                "keyword": "seo optimization",
                "target_url": "/seo-optimization",
                "priority": "medium",
                "added_at": "2024-01-05T00:00:00Z",
                "current_position": 12,
                "best_position": 8,
                "search_volume": 8000,
                "difficulty": 75,
                "status": "tracking",
                "trend": "stable"
            }
        ]
        
        return {"success": True, "data": tracked_keywords}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/content/analyze")
async def analyze_content(content_request: dict):
    """Analyze content for SEO optimization"""
    try:
        content = content_request.get("content")
        target_keyword = content_request.get("target_keyword")
        content_type = content_request.get("content_type", "article")
        
        if not content or not target_keyword:
            return {"success": False, "error": "Content and target keyword are required"}
        
        # Sample content analysis
        analysis_result = {
            "content_id": f"content_{int(time.time())}",
            "target_keyword": target_keyword,
            "content_type": content_type,
            "analyzed_at": datetime.now().isoformat(),
            "overall_score": 78.5,
            "word_count": len(content.split()),
            "keyword_density": 2.1,
            "readability_score": 85.2,
            "seo_analysis": {
                "title_optimization": {
                    "score": 85,
                    "issues": ["Title could be more compelling"],
                    "suggestions": ["Add power words", "Include target keyword"]
                },
                "heading_structure": {
                    "score": 90,
                    "issues": [],
                    "suggestions": ["Structure looks good"]
                },
                "keyword_usage": {
                    "score": 75,
                    "issues": ["Keyword could be used more naturally"],
                    "suggestions": ["Include LSI keywords", "Use keyword variations"]
                },
                "content_quality": {
                    "score": 80,
                    "issues": ["Some sentences are too long"],
                    "suggestions": ["Break up long sentences", "Add more examples"]
                }
            },
            "recommendations": [
                "Optimize title for better click-through rate",
                "Include more related keywords naturally",
                "Add internal links to relevant pages",
                "Improve content structure with better headings"
            ]
        }
        
        return {"success": True, "data": analysis_result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/competitors/analyze")
async def analyze_competitors(competitor_request: dict):
    """Analyze competitor websites and strategies"""
    try:
        competitors = competitor_request.get("competitors", [])
        analysis_depth = competitor_request.get("depth", "comprehensive")
        
        if not competitors:
            return {"success": False, "error": "At least one competitor is required"}
        
        # Sample competitor analysis
        analysis_result = {
            "analysis_id": f"comp_{int(time.time())}",
            "analyzed_at": datetime.now().isoformat(),
            "depth": analysis_depth,
            "competitors": []
        }
        
        for competitor in competitors:
            comp_analysis = {
                "domain": competitor,
                "overall_score": 82.5,
                "strength_level": "high",
                "key_metrics": {
                    "domain_authority": 85,
                    "organic_traffic": 45000,
                    "ranking_keywords": 1200,
                    "backlinks": 15000
                },
                "top_keywords": [
                    {"keyword": "digital marketing", "position": 2, "traffic": 2000},
                    {"keyword": "seo services", "position": 1, "traffic": 1800}
                ],
                "content_strategy": {
                    "content_frequency": "weekly",
                    "content_types": ["blog posts", "infographics", "videos"],
                    "average_length": 1500
                },
                "technical_analysis": {
                    "page_speed": "fast",
                    "mobile_friendly": True,
                    "ssl_secure": True,
                    "structured_data": True
                },
                "opportunities": [
                    "Content gaps in local SEO",
                    "Missing video content",
                    "Limited social media presence"
                ]
            }
            analysis_result["competitors"].append(comp_analysis)
        
        # Overall insights
        analysis_result["insights"] = {
            "market_position": "competitive",
            "strengths": ["Strong content strategy", "Good technical foundation"],
            "weaknesses": ["Limited local presence", "Social media gaps"],
            "recommendations": [
                "Focus on local SEO opportunities",
                "Develop video content strategy",
                "Improve social media engagement"
            ]
        }
        
        return {"success": True, "data": analysis_result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/backlinks/analyze")
async def analyze_backlinks(backlink_request: dict):
    """Analyze backlink profile and opportunities"""
    try:
        domain = backlink_request.get("domain")
        analysis_type = backlink_request.get("type", "overview")
        
        if not domain:
            return {"success": False, "error": "Domain is required"}
        
        # Sample backlink analysis
        analysis_result = {
            "domain": domain,
            "analysis_id": f"backlink_{int(time.time())}",
            "analyzed_at": datetime.now().isoformat(),
            "overview": {
                "total_backlinks": 1250,
                "unique_domains": 180,
                "domain_authority": 72,
                "spam_score": 2.1
            },
            "quality_metrics": {
                "high_quality_backlinks": 890,
                "medium_quality_backlinks": 280,
                "low_quality_backlinks": 80,
                "quality_score": 85.2
            },
            "top_referring_domains": [
                {
                    "domain": "authority-site1.com",
                    "domain_authority": 95,
                    "backlinks": 15,
                    "anchor_text": "digital marketing guide"
                },
                {
                    "domain": "industry-blog.com",
                    "domain_authority": 88,
                    "backlinks": 8,
                    "anchor_text": "seo tips"
                }
            ],
            "anchor_text_analysis": {
                "most_common_anchors": [
                    {"text": "digital marketing", "count": 45, "percentage": 12.5},
                    {"text": "seo services", "count": 32, "percentage": 8.9},
                    {"text": "marketing tips", "count": 28, "percentage": 7.8}
                ],
                "branded_anchors": 35,
                "generic_anchors": 180,
                "exact_match_anchors": 25
            },
            "opportunities": [
                {
                    "type": "broken_link_building",
                    "description": "Find broken links on competitor sites",
                    "potential_impact": "high",
                    "effort_required": "medium"
                },
                {
                    "type": "content_outreach",
                    "description": "Create linkable content for industry publications",
                    "potential_impact": "high",
                    "effort_required": "high"
                },
                {
                    "type": "local_citations",
                    "description": "Build local business directory listings",
                    "potential_impact": "medium",
                    "effort_required": "low"
                }
            ],
            "risks": [
                {
                    "type": "toxic_backlinks",
                    "description": "15 potentially toxic backlinks detected",
                    "severity": "medium",
                    "recommendation": "Disavow toxic backlinks"
                }
            ]
        }
        
        return {"success": True, "data": analysis_result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/rankings/track")
async def track_rankings(ranking_request: dict):
    """Track keyword rankings over time"""
    try:
        keywords = ranking_request.get("keywords", [])
        search_engine = ranking_request.get("search_engine", "google")
        location = ranking_request.get("location", "US")
        
        if not keywords:
            return {"success": False, "error": "At least one keyword is required"}
        
        # Sample ranking tracking data
        tracking_result = {
            "tracking_id": f"rankings_{int(time.time())}",
            "search_engine": search_engine,
            "location": location,
            "tracked_at": datetime.now().isoformat(),
            "keywords": []
        }
        
        for keyword in keywords:
            keyword_data = {
                "keyword": keyword,
                "current_position": 5,  # This would be fetched from actual data
                "previous_position": 7,
                "change": 2,
                "search_volume": 8000,
                "competition": "medium",
                "trend": "improving"
            }
            tracking_result["keywords"].append(keyword_data)
        
        return {"success": True, "data": tracking_result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/seo/rankings/history")
async def get_ranking_history(keyword: str = None, days: int = 30):
    """Get historical ranking data for keywords"""
    try:
        # Sample historical data
        history_data = {
            "keyword": keyword or "digital marketing",
            "search_engine": "google",
            "location": "US",
            "period_days": days,
            "data_points": []
        }
        
        # Generate sample historical data
        base_position = 5
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            position = base_position + (i % 3) - 1  # Vary position slightly
            history_data["data_points"].append({
                "date": date,
                "position": position,
                "change": position - base_position
            })
        
        return {"success": True, "data": history_data}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/seo/alerts/setup")
async def setup_seo_alerts(alert_request: dict):
    """Setup SEO monitoring alerts"""
    try:
        alert_type = alert_request.get("type")
        conditions = alert_request.get("conditions", {})
        notification_method = alert_request.get("notification_method", "email")
        
        if not alert_type:
            return {"success": False, "error": "Alert type is required"}
        
        # Sample alert setup
        alert_config = {
            "alert_id": f"alert_{int(time.time())}",
            "type": alert_type,
            "conditions": conditions,
            "notification_method": notification_method,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "last_triggered": None
        }
        
        return {"success": True, "data": alert_config}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/seo/alerts/list")
async def list_seo_alerts():
    """List all configured SEO alerts"""
    try:
        # Sample alerts
        alerts = [
            {
                "alert_id": "alert_1",
                "type": "ranking_drop",
                "conditions": {"drop_threshold": 5, "keywords": ["digital marketing"]},
                "notification_method": "email",
                "created_at": "2024-01-01T00:00:00Z",
                "status": "active",
                "last_triggered": None
            },
            {
                "alert_id": "alert_2",
                "type": "technical_issue",
                "conditions": {"issue_types": ["page_speed", "mobile_friendly"]},
                "notification_method": "slack",
                "created_at": "2024-01-05T00:00:00Z",
                "status": "active",
                "last_triggered": "2024-01-10T15:30:00Z"
            }
        ]
        
        return {"success": True, "data": alerts}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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