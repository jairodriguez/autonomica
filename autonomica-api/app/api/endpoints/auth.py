from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.services.auth_service import AuthService
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.models.schema import User, UserRole, Permission, UserPermission
from app.auth.permission_decorator import (
    require_authenticated, require_admin, require_manager_or_admin,
    require_user_management, require_authenticated
)

router = APIRouter(prefix="/auth", tags=["Authentication & Authorization"])

# Pydantic models for request/response
class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserCreateRequest(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "creator"

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class RoleUpdateRequest(BaseModel):
    role: str

class PermissionGrantRequest(BaseModel):
    user_id: int
    permission: str
    expires_at: Optional[datetime] = None

class PermissionRevokeRequest(BaseModel):
    user_id: int
    permission: str

class UserPermissionsResponse(BaseModel):
    user_id: int
    permissions: List[str]
    role: str

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

@router.get("/me", response_model=UserResponse)
@require_authenticated()
async def get_current_user_info(
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information."""
    return current_user

@router.get("/me/permissions", response_model=UserPermissionsResponse)
@require_authenticated()
async def get_current_user_permissions(
    current_user: User = Depends(),
    db: Session = Depends(get_db)
):
    """Get current user's permissions."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    permissions = await auth_service.get_user_permissions(current_user.id)
    permission_names = [p.value for p in permissions]
    
    return UserPermissionsResponse(
        user_id=current_user.id,
        permissions=permission_names,
        role=current_user.role.value if current_user.role else "none"
    )

@router.get("/users", response_model=UserListResponse)
@require_user_management()
async def list_users(
    page: int = 1,
    per_page: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """List users with pagination and filtering."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    # Build query
    query = db.query(User)
    
    if role:
        try:
            user_role = UserRole(role)
            query = query.filter(User.role == user_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}"
            )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/users/{user_id}", response_model=UserResponse)
@require_user_management()
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Get user by ID."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/users/{user_id}/role")
@require_admin()
async def update_user_role(
    user_id: int,
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Update user role (admin only)."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    try:
        new_role = UserRole(request.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {request.role}"
        )
    
    updated_user = await auth_service.update_user_role(
        user_id, new_role, current_user.id
    )
    
    return {"message": f"User role updated to {new_role.value}", "user": updated_user}

@router.post("/users/{user_id}/permissions")
@require_admin()
async def grant_permission(
    user_id: int,
    request: PermissionGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Grant a permission to a user (admin only)."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {request.permission}"
        )
    
    user_permission = await auth_service.grant_permission(
        user_id, permission, current_user.id, request.expires_at
    )
    
    return {"message": f"Permission {permission.value} granted to user {user_id}"}

@router.delete("/users/{user_id}/permissions")
@require_admin()
async def revoke_permission(
    user_id: int,
    request: PermissionRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Revoke a permission from a user (admin only)."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    try:
        permission = Permission(request.permission)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid permission: {request.permission}"
        )
    
    revoked = await auth_service.revoke_permission(
        user_id, permission, current_user.id
    )
    
    if revoked:
        return {"message": f"Permission {permission.value} revoked from user {user_id}"}
    else:
        return {"message": f"Permission {permission.value} was not found for user {user_id}"}

@router.put("/users/{user_id}/deactivate")
@require_manager_or_admin()
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Deactivate a user account."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    # Prevent self-deactivation
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    deactivated_user = await auth_service.deactivate_user(user_id, current_user.id)
    
    return {"message": f"User {deactivated_user.email} deactivated"}

@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
@require_user_management()
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends()
):
    """Get user's permissions."""
    redis_service = RedisService()
    cache_service = CacheService(redis_service)
    auth_service = AuthService(db, redis_service, cache_service)
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permissions = await auth_service.get_user_permissions(user_id)
    permission_names = [p.value for p in permissions]
    
    return UserPermissionsResponse(
        user_id=user_id,
        permissions=permission_names,
        role=user.role.value if user.role else "none"
    )

@router.get("/roles")
async def get_available_roles():
    """Get all available user roles."""
    roles = [{"value": role.value, "name": role.name} for role in UserRole]
    return {"roles": roles}

@router.get("/permissions")
async def get_available_permissions():
    """Get all available permissions."""
    permissions = [{"value": perm.value, "name": perm.name} for perm in Permission]
    return {"permissions": permissions}

@router.get("/health")
async def auth_health_check():
    """Health check for authentication service."""
    return {"status": "healthy", "service": "authentication"}




