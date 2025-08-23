"""
API endpoints package
"""
from .analytics import router as analytics_router
from .auth import router as auth_router

__all__ = ["analytics_router", "auth_router"]
