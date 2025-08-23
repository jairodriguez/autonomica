from functools import wraps
from typing import List, Optional, Union
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.models.schema import Permission, User
from app.services.auth_service import AuthService
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

def require_permissions(
    permissions: Union[Permission, List[Permission]],
    require_all: bool = True,
    allow_roles: Optional[List[str]] = None
):
    """
    Decorator to require specific permissions for API endpoints.
    
    Args:
        permissions: Single permission or list of permissions required
        require_all: If True, user must have ALL permissions. If False, user must have ANY permission.
        allow_roles: Optional list of role names that bypass permission checks (e.g., ['admin'])
    """
    if isinstance(permissions, Permission):
        permissions = [permissions]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies from function signature
            db = None
            current_user = None
            
            # Extract dependencies from kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, ClerkUser):
                    current_user = value
            
            # If dependencies not found in kwargs, try to get them
            if not db:
                db = next(get_db())
            if not current_user:
                current_user = await get_current_user(db)
            
            # Initialize services
            redis_service = RedisService()
            cache_service = CacheService(redis_service)
            auth_service = AuthService(db, redis_service, cache_service)
            
            # Get or create user from Clerk data
            user = await auth_service.get_or_create_user(current_user)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated or account inactive"
                )
            
            # Check if user has bypass role
            if allow_roles and user.role and user.role.value in allow_roles:
                return await func(*args, **kwargs)
            
            # Check permissions
            if require_all:
                has_access = await auth_service.has_all_permissions(user.id, permissions)
            else:
                has_access = await auth_service.has_any_permission(user.id, permissions)
            
            if not has_access:
                permission_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {', '.join(permission_names)}"
                )
            
            # Add user to kwargs for the function to use
            kwargs['current_user'] = user
            kwargs['user_id'] = user.id
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_role(role: str):
    """
    Decorator to require a specific user role for API endpoints.
    
    Args:
        role: Role name required (e.g., 'admin', 'manager')
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies from function signature
            db = None
            current_user = None
            
            # Extract dependencies from kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, ClerkUser):
                    current_user = value
            
            # If dependencies not found in kwargs, try to get them
            if not db:
                db = next(get_db())
            if not current_user:
                current_user = await get_current_user(db)
            
            # Initialize services
            redis_service = RedisService()
            cache_service = CacheService(redis_service)
            auth_service = AuthService(db, redis_service, cache_service)
            
            # Get or create user from Clerk data
            user = await auth_service.get_or_create_user(current_user)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated or account inactive"
                )
            
            # Check role
            if not user.role or user.role.value != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required. Current role: {user.role.value if user.role else 'None'}"
                )
            
            # Add user to kwargs for the function to use
            kwargs['current_user'] = user
            kwargs['user_id'] = user.id
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_any_role(roles: List[str]):
    """
    Decorator to require any of the specified roles for API endpoints.
    
    Args:
        roles: List of role names, user must have at least one
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies from function signature
            db = None
            current_user = None
            
            # Extract dependencies from kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, ClerkUser):
                    current_user = value
            
            # If dependencies not found in kwargs, try to get them
            if not db:
                db = next(get_db())
            if not current_user:
                current_user = await get_current_user(db)
            
            # Initialize services
            redis_service = RedisService()
            cache_service = CacheService(redis_service)
            auth_service = AuthService(db, redis_service, cache_service)
            
            # Get or create user from Clerk data
            user = await auth_service.get_or_create_user(current_user)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated or account inactive"
                )
            
            # Check if user has any of the required roles
            if not user.role or user.role.value not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {', '.join(roles)}. Current role: {user.role.value if user.role else 'None'}"
                )
            
            # Add user to kwargs for the function to use
            kwargs['current_user'] = user
            kwargs['user_id'] = user.id
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_authenticated():
    """
    Decorator to require only authentication (no specific permissions).
    Useful for endpoints that just need a valid user.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies from function signature
            db = None
            current_user = None
            
            # Extract dependencies from kwargs
            for key, value in kwargs.items():
                if isinstance(value, Session):
                    db = value
                elif isinstance(value, ClerkUser):
                    current_user = value
            
            # If dependencies not found in kwargs, try to get them
            if not db:
                db = next(get_db())
            if not current_user:
                current_user = await get_current_user(db)
            
            # Initialize services
            redis_service = RedisService()
            cache_service = CacheService(redis_service)
            auth_service = AuthService(db, redis_service, cache_service)
            
            # Get or create user from Clerk data
            user = await auth_service.get_or_create_user(current_user)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not authenticated or account inactive"
                )
            
            # Add user to kwargs for the function to use
            kwargs['current_user'] = user
            kwargs['user_id'] = user.id
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Convenience decorators for common permission patterns
def require_content_management():
    """Require content management permissions."""
    return require_permissions([
        Permission.CREATE_CONTENT,
        Permission.EDIT_CONTENT,
        Permission.DELETE_CONTENT
    ], require_all=False)

def require_publishing():
    """Require publishing permissions."""
    return require_permissions([
        Permission.PUBLISH_CONTENT,
        Permission.SCHEDULE_POSTS,
        Permission.PUBLISH_POSTS
    ], require_all=False)

def require_analytics():
    """Require analytics viewing permissions."""
    return require_permissions([Permission.VIEW_ANALYTICS])

def require_user_management():
    """Require user management permissions."""
    return require_permissions([
        Permission.MANAGE_USERS,
        Permission.ASSIGN_ROLES,
        Permission.VIEW_USERS
    ], require_all=False)

def require_admin():
    """Require admin role."""
    return require_role('admin')

def require_manager_or_admin():
    """Require manager or admin role."""
    return require_any_role(['manager', 'admin'])

def require_editor_or_higher():
    """Require editor role or higher."""
    return require_any_role(['editor', 'manager', 'admin'])

def require_creator_or_higher():
    """Require creator role or higher."""
    return require_any_role(['creator', 'editor', 'manager', 'admin'])




