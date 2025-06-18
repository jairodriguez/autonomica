"""
Autonomica API - Main FastAPI Application
OWL (Optimized Workflow Language) powered multi-agent marketing system
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from loguru import logger

from app.api.routes import agents, tasks, health, workflows
from app.core.config import settings
from app.owl.workforce import AutonomicaWorkforce
from app.core.exceptions import setup_exception_handlers

# Load environment variables
load_dotenv()

# Global workforce instance
workforce: AutonomicaWorkforce = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with OWL Workforce initialization"""
    global workforce
    
    logger.info("🚀 Starting Autonomica API with OWL Framework")
    
    try:
        # Initialize OWL Workforce
        logger.info("🦉 Initializing OWL Workforce...")
        workforce = AutonomicaWorkforce()
        await workforce.initialize()
        
        # Store workforce in app state
        app.state.workforce = workforce
        
        logger.success("✅ OWL Workforce initialized successfully")
        logger.info(f"🎯 Available agents: {len(workforce.agents)}")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize OWL Workforce: {e}")
        raise
    
    finally:
        # Cleanup
        if workforce:
            logger.info("🔄 Shutting down OWL Workforce...")
            await workforce.shutdown()
            logger.info("✅ OWL Workforce shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Autonomica API",
    description="OWL-powered multi-agent marketing automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(workflows.router, prefix="/api", tags=["workflows"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Autonomica API",
        "version": "1.0.0",
        "description": "OWL-powered multi-agent marketing automation platform",
        "owl_framework": "active",
        "agents_available": len(app.state.workforce.agents) if hasattr(app.state, 'workforce') else 0,
        "endpoints": {
            "health": "/api/health",
            "agents": "/api/agents",
            "tasks": "/api/tasks", 
            "workflows": "/api/workflows",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status including OWL Workforce information"""
    if not hasattr(app.state, 'workforce') or not app.state.workforce:
        raise HTTPException(status_code=503, detail="OWL Workforce not initialized")
    
    workforce = app.state.workforce
    
    return {
        "status": "healthy",
        "owl_framework": {
            "status": "active",
            "version": workforce.version,
            "agents_count": len(workforce.agents),
            "active_workflows": len(workforce.active_workflows),
            "total_tasks_processed": workforce.stats.total_tasks_processed,
            "uptime_seconds": workforce.stats.uptime_seconds
        },
        "services": {
            "redis": "connected" if workforce.redis_client.ping() else "disconnected",
            "vector_store": "active" if workforce.vector_store else "inactive",
            "task_queue": "active"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Autonomica API server...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    ) 