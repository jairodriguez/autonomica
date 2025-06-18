"""
Custom exception handlers for Autonomica API
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from loguru import logger
import traceback
from typing import Any, Dict


class AutonomicaException(Exception):
    """Base exception for Autonomica API"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        self.message = message
        self.error_code = error_code or "AUTONOMICA_ERROR"
        self.status_code = status_code
        super().__init__(self.message)


class AgentException(AutonomicaException):
    """Exception raised when agent operations fail"""
    
    def __init__(self, message: str, agent_id: str = None):
        self.agent_id = agent_id
        super().__init__(message, "AGENT_ERROR", 422)


class WorkflowException(AutonomicaException):
    """Exception raised when workflow operations fail"""
    
    def __init__(self, message: str, workflow_id: str = None):
        self.workflow_id = workflow_id
        super().__init__(message, "WORKFLOW_ERROR", 422)


class OWLException(AutonomicaException):
    """Exception raised when OWL framework operations fail"""
    
    def __init__(self, message: str):
        super().__init__(message, "OWL_ERROR", 503)


async def autonomica_exception_handler(request: Request, exc: AutonomicaException):
    """Handle custom Autonomica exceptions"""
    logger.error(f"Autonomica Exception: {exc.message} (Code: {exc.error_code})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "type": "autonomica_error"
            }
        }
    )


async def agent_exception_handler(request: Request, exc: AgentException):
    """Handle agent-specific exceptions"""
    logger.error(f"Agent Exception: {exc.message} (Agent ID: {exc.agent_id})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "type": "agent_error",
                "agent_id": exc.agent_id
            }
        }
    )


async def workflow_exception_handler(request: Request, exc: WorkflowException):
    """Handle workflow-specific exceptions"""
    logger.error(f"Workflow Exception: {exc.message} (Workflow ID: {exc.workflow_id})")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "type": "workflow_error",
                "workflow_id": exc.workflow_id
            }
        }
    )


async def owl_exception_handler(request: Request, exc: OWLException):
    """Handle OWL framework exceptions"""
    logger.error(f"OWL Exception: {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "type": "owl_error"
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "code": f"HTTP_{exc.status_code}",
                "type": "http_error"
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation exceptions"""
    logger.warning(f"Validation Exception: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Request validation failed",
                "code": "VALIDATION_ERROR", 
                "type": "validation_error",
                "details": exc.errors()
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled Exception: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "type": "server_error"
            }
        }
    )


def setup_exception_handlers(app: FastAPI):
    """Setup all exception handlers for the FastAPI app"""
    
    # Custom exception handlers
    app.add_exception_handler(AutonomicaException, autonomica_exception_handler)
    app.add_exception_handler(AgentException, agent_exception_handler)
    app.add_exception_handler(WorkflowException, workflow_exception_handler)
    app.add_exception_handler(OWLException, owl_exception_handler)
    
    # Standard exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Exception handlers configured") 