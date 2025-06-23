"""
Health check endpoints for Autonomica API
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import os
import sys
from app.core.config import settings
from app.services.redis_service import get_redis_service, RedisService

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime: float
    python_version: str
    services: Dict[str, str]


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response model"""
    system_info: Dict[str, Any]
    configuration: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    
    # Calculate uptime (simplified - in real app you'd track start time)
    uptime = 0.0
    
    # Check service statuses
    services = {
        "api": "healthy",
        "database": "not_configured",
        "redis": "not_configured",
        "owl_framework": "initializing"
    }
    
    # Try to check Redis connection using our Redis service
    try:
        from app.services.redis_service import redis_service
        redis_health = await redis_service.health_check()
        services["redis"] = redis_health["status"]
    except Exception:
        services["redis"] = "unhealthy"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.API_VERSION,
        environment=os.getenv("ENVIRONMENT", "development"),
        uptime=uptime,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        services=services
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check with system information"""
    
    # Get basic health info
    basic_health = await health_check()
    
    # System information
    system_info = {
        "platform": sys.platform,
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
        "environment_variables": {
            "OPENAI_API_KEY": "***" if settings.OPENAI_API_KEY else "not_set",
            "ANTHROPIC_API_KEY": "***" if settings.ANTHROPIC_API_KEY else "not_set",
            "REDIS_URL": settings.REDIS_URL,
            "DEBUG": settings.DEBUG
        }
    }
    
    # Configuration info (non-sensitive)
    configuration = {
        "max_agents": settings.MAX_AGENTS,
        "agent_timeout": settings.AGENT_TIMEOUT_SECONDS,
        "owl_max_workflows": settings.OWL_MAX_CONCURRENT_WORKFLOWS,
        "vector_dimension": settings.VECTOR_DIMENSION,
        "rate_limit": settings.RATE_LIMIT_PER_MINUTE,
        "cors_origins": len(settings.ALLOWED_ORIGINS)
    }
    
    return DetailedHealthResponse(
        **basic_health.dict(),
        system_info=system_info,
        configuration=configuration
    )


@router.get("/health/readiness")
async def readiness_check():
    """Kubernetes-style readiness probe"""
    
    # Check if essential services are ready
    ready = True
    issues = []
    
    # Check if we have at least one AI provider configured
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        ready = False
        issues.append("No AI provider API key configured")
    
    # Check Redis connection using our Redis service
    try:
        from app.services.redis_service import redis_service
        redis_health = await redis_service.health_check()
        if redis_health["status"] != "healthy":
            ready = False
            issues.append(f"Redis unhealthy: {redis_health.get('error', 'Unknown error')}")
    except Exception as e:
        ready = False
        issues.append(f"Redis connection failed: {str(e)}")
    
    if not ready:
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "issues": issues
            }
        )
    
    return {
        "ready": True,
        "timestamp": datetime.utcnow()
    }


@router.get("/health/liveness")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    
    # Basic check to ensure the application is alive
    return {
        "alive": True,
        "timestamp": datetime.utcnow(),
        "pid": os.getpid()
    }


@router.get("/health/redis")
async def redis_health_check(redis_service: RedisService = Depends(get_redis_service)):
    """Detailed Redis health check"""
    
    health_status = await redis_service.health_check()
    
    # Add additional Redis-specific information
    health_status.update({
        "backend_type": "Vercel KV" if redis_service.is_vercel_kv else "Traditional Redis",
        "supports_user_scoping": True,
        "supports_task_queue": True,
        "supports_rate_limiting": True
    })
    
    if health_status["status"] != "healthy":
        raise HTTPException(
            status_code=503,
            detail=health_status
        )
    
    return health_status 