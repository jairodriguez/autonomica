import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
from app.services.vercel_kv_service import VercelKVService
from app.models.user import User


class UserRole(Enum):
    """User roles for analytics access control"""
    VIEWER = "viewer"           # Can view analytics and reports
    ANALYST = "analyst"         # Can view and export analytics
    MANAGER = "manager"         # Can view, export, and schedule reports
    ADMIN = "admin"             # Full access to all features
    OWNER = "owner"             # Owner with full access and user management


class Permission(Enum):
    """Specific permissions for analytics features"""
    VIEW_DASHBOARDS = "view_dashboards"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"
    SCHEDULE_REPORTS = "schedule_reports"
    MANAGE_TEMPLATES = "manage_templates"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SCHEDULES = "manage_schedules"
    ACCESS_VERCEL_KV = "access_vercel_kv"
    VIEW_USER_DATA = "view_user_data"


class AccessLevel(Enum):
    """Access levels for data visibility"""
    OWN = "own"                 # User can only see their own data
    TEAM = "team"               # User can see team data
    ORGANIZATION = "organization"  # User can see organization data
    ALL = "all"                 # User can see all data


@dataclass
class UserPermissions:
    """User permissions configuration"""
    user_id: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    access_level: AccessLevel = AccessLevel.OWN
    team_id: Optional[str] = None
    organization_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class AccessToken:
    """Access token for analytics API"""
    token: str
    user_id: str
    permissions: List[Permission]
    access_level: AccessLevel
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    is_active: bool = True


@dataclass
class AuditLog:
    """Audit log entry for access control"""
    id: str
    user_id: str
    action: str
    resource: str
    resource_id: Optional[str] = None
    permissions_used: List[Permission] = field(default_factory=list)
    access_level: AccessLevel = AccessLevel.OWN
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


class AnalyticsAuthService:
    """Service for managing analytics authentication and access control"""
    
    def __init__(
        self,
        db: AsyncSession,
        redis_service: RedisService,
        cache_service: CacheService,
        vercel_kv_service: VercelKVService
    ):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        self.vercel_kv_service = vercel_kv_service
        
        # Initialize default role permissions
        self._initialize_role_permissions()
    
    def _initialize_role_permissions(self):
        """Initialize default permissions for each role"""
        self.role_permissions = {
            UserRole.VIEWER: [
                Permission.VIEW_DASHBOARDS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.ANALYST: [
                Permission.VIEW_DASHBOARDS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA
            ],
            UserRole.MANAGER: [
                Permission.VIEW_DASHBOARDS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.SCHEDULE_REPORTS,
                Permission.MANAGE_SCHEDULES
            ],
            UserRole.ADMIN: [
                Permission.VIEW_DASHBOARDS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.SCHEDULE_REPORTS,
                Permission.MANAGE_SCHEDULES,
                Permission.MANAGE_TEMPLATES,
                Permission.ACCESS_VERCEL_KV
            ],
            UserRole.OWNER: [
                Permission.VIEW_DASHBOARDS,
                Permission.VIEW_REPORTS,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.SCHEDULE_REPORTS,
                Permission.MANAGE_SCHEDULES,
                Permission.MANAGE_TEMPLATES,
                Permission.MANAGE_USERS,
                Permission.ACCESS_VERCEL_KV,
                Permission.VIEW_USER_DATA
            ]
        }
        
        # Default access levels for each role
        self.role_access_levels = {
            UserRole.VIEWER: AccessLevel.OWN,
            UserRole.ANALYST: AccessLevel.TEAM,
            UserRole.MANAGER: AccessLevel.TEAM,
            UserRole.ADMIN: AccessLevel.ORGANIZATION,
            UserRole.OWNER: AccessLevel.ALL
        }
    
    async def authenticate_user(self, clerk_user_id: str) -> Optional[UserPermissions]:
        """Authenticate user using Clerk and get permissions"""
        
        try:
            # Check cache first
            cache_key = f"user_permissions:{clerk_user_id}"
            cached_permissions = await self.cache_service.get(cache_key)
            
            if cached_permissions:
                return UserPermissions(**cached_permissions)
            
            # Get user from database
            user = await self._get_user_from_db(clerk_user_id)
            if not user:
                return None
            
            # Get or create user permissions
            user_permissions = await self._get_or_create_user_permissions(clerk_user_id, user)
            
            # Cache permissions
            await self.cache_service.set(
                cache_key,
                user_permissions.__dict__,
                ttl=3600  # 1 hour
            )
            
            return user_permissions
            
        except Exception as e:
            await self._log_audit_event(
                user_id=clerk_user_id,
                action="authentication_failed",
                resource="analytics_auth",
                success=False,
                error_message=str(e)
            )
            return None
    
    async def _get_user_from_db(self, clerk_user_id: str) -> Optional[User]:
        """Get user from database by Clerk user ID"""
        
        try:
            # Query user table
            result = await self.db.execute(
                select(User).where(User.clerk_user_id == clerk_user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                # Create user if not exists (integration with Clerk)
                user = await self._create_user_from_clerk(clerk_user_id)
            
            return user
            
        except Exception as e:
            # Log error and return None
            print(f"Error getting user from DB: {e}")
            return None
    
    async def _create_user_from_clerk(self, clerk_user_id: str) -> Optional[User]:
        """Create user in database from Clerk user data"""
        
        try:
            # This would typically integrate with Clerk API to get user details
            # For now, create a basic user record
            
            user = User(
                clerk_user_id=clerk_user_id,
                email=f"user_{clerk_user_id}@example.com",  # Placeholder
                username=f"user_{clerk_user_id}",
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            return user
            
        except Exception as e:
            print(f"Error creating user from Clerk: {e}")
            return None
    
    async def _get_or_create_user_permissions(
        self,
        clerk_user_id: str,
        user: User
    ) -> UserPermissions:
        """Get or create user permissions"""
        
        # Check Vercel KV for existing permissions
        permissions_data = await self.vercel_kv_service.get_analytics_data(
            user_id=clerk_user_id,
            data_type="user_permissions",
            source_id=clerk_user_id
        )
        
        if permissions_data:
            return UserPermissions(**permissions_data)
        
        # Create default permissions based on user role
        default_role = UserRole.VIEWER  # Default role for new users
        default_permissions = self.role_permissions[default_role]
        default_access_level = self.role_access_levels[default_role]
        
        user_permissions = UserPermissions(
            user_id=clerk_user_id,
            role=default_role,
            permissions=default_permissions,
            access_level=default_access_level,
            team_id=user.team_id if hasattr(user, 'team_id') else None,
            organization_id=user.organization_id if hasattr(user, 'organization_id') else None
        )
        
        # Store permissions in Vercel KV
        await self.vercel_kv_service.store_analytics_data(
            user_id=clerk_user_id,
            data_type="user_permissions",
            source_id=clerk_user_id,
            data=user_permissions.__dict__,
            ttl=0  # No expiration for user permissions
        )
        
        return user_permissions
    
    async def check_permission(
        self,
        user_id: str,
        permission: Permission,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has specific permission"""
        
        try:
            # Get user permissions
            user_permissions = await self.authenticate_user(user_id)
            if not user_permissions or not user_permissions.is_active:
                return False
            
            # Check if permission is granted
            if permission not in user_permissions.permissions:
                await self._log_audit_event(
                    user_id=user_id,
                    action="permission_denied",
                    resource=resource or "unknown",
                    resource_id=resource_id,
                    permissions_used=[permission],
                    success=False,
                    error_message="Permission not granted"
                )
                return False
            
            # Log successful permission check
            await self._log_audit_event(
                user_id=user_id,
                action="permission_granted",
                resource=resource or "unknown",
                resource_id=resource_id,
                permissions_used=[permission],
                success=True
            )
            
            return True
            
        except Exception as e:
            await self._log_audit_event(
                user_id=user_id,
                action="permission_check_error",
                resource=resource or "unknown",
                resource_id=resource_id,
                success=False,
                error_message=str(e)
            )
            return False
    
    async def check_access_level(
        self,
        user_id: str,
        required_level: AccessLevel,
        target_user_id: Optional[str] = None
    ) -> bool:
        """Check if user has required access level"""
        
        try:
            # Get user permissions
            user_permissions = await self.authenticate_user(user_id)
            if not user_permissions or not user_permissions.is_active:
                return False
            
            # Check access level hierarchy
            access_levels = [AccessLevel.OWN, AccessLevel.TEAM, AccessLevel.ORGANIZATION, AccessLevel.ALL]
            user_level_index = access_levels.index(user_permissions.access_level)
            required_level_index = access_levels.index(required_level)
            
            if user_level_index < required_level_index:
                await self._log_audit_event(
                    user_id=user_id,
                    action="access_level_denied",
                    resource="analytics_data",
                    resource_id=target_user_id,
                    access_level=user_permissions.access_level,
                    success=False,
                    error_message=f"Required level: {required_level}, User level: {user_permissions.access_level}"
                )
                return False
            
            # Check specific access rules
            if required_level == AccessLevel.OWN:
                if target_user_id and target_user_id != user_id:
                    return False
            elif required_level == AccessLevel.TEAM:
                if not await self._is_same_team(user_id, target_user_id):
                    return False
            elif required_level == AccessLevel.ORGANIZATION:
                if not await self._is_same_organization(user_id, target_user_id):
                    return False
            
            # Log successful access check
            await self._log_audit_event(
                user_id=user_id,
                action="access_level_granted",
                resource="analytics_data",
                resource_id=target_user_id,
                access_level=user_permissions.access_level,
                success=True
            )
            
            return True
            
        except Exception as e:
            await self._log_audit_event(
                user_id=user_id,
                action="access_level_check_error",
                resource="analytics_data",
                resource_id=target_user_id,
                success=False,
                error_message=str(e)
            )
            return False
    
    async def _is_same_team(self, user_id: str, target_user_id: Optional[str]) -> bool:
        """Check if users are in the same team"""
        
        if not target_user_id:
            return True
        
        try:
            # Get user permissions
            user_permissions = await self.authenticate_user(user_id)
            target_permissions = await self.authenticate_user(target_user_id)
            
            if not user_permissions or not target_permissions:
                return False
            
            return user_permissions.team_id == target_permissions.team_id
            
        except Exception:
            return False
    
    async def _is_same_organization(self, user_id: str, target_user_id: Optional[str]) -> bool:
        """Check if users are in the same organization"""
        
        if not target_user_id:
            return True
        
        try:
            # Get user permissions
            user_permissions = await self.authenticate_user(user_id)
            target_permissions = await self.authenticate_user(target_user_id)
            
            if not user_permissions or not target_permissions:
                return False
            
            return user_permissions.organization_id == target_permissions.organization_id
            
        except Exception:
            return False
    
    async def update_user_permissions(
        self,
        admin_user_id: str,
        target_user_id: str,
        role: UserRole,
        permissions: Optional[List[Permission]] = None,
        access_level: Optional[AccessLevel] = None,
        team_id: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> Optional[UserPermissions]:
        """Update user permissions (admin only)"""
        
        try:
            # Check if admin user has permission to manage users
            if not await self.check_permission(admin_user_id, Permission.MANAGE_USERS):
                return None
            
            # Get target user permissions
            target_permissions = await self.authenticate_user(target_user_id)
            if not target_permissions:
                return None
            
            # Update permissions
            target_permissions.role = role
            if permissions:
                target_permissions.permissions = permissions
            else:
                target_permissions.permissions = self.role_permissions[role]
            
            if access_level:
                target_permissions.access_level = access_level
            else:
                target_permissions.access_level = self.role_access_levels[role]
            
            if team_id:
                target_permissions.team_id = team_id
            if organization_id:
                target_permissions.organization_id = organization_id
            
            target_permissions.updated_at = datetime.utcnow()
            
            # Store updated permissions
            await self.vercel_kv_service.store_analytics_data(
                user_id=target_user_id,
                data_type="user_permissions",
                source_id=target_user_id,
                data=target_permissions.__dict__,
                ttl=0
            )
            
            # Clear cache
            cache_key = f"user_permissions:{target_user_id}"
            await self.cache_service.delete(cache_key)
            
            # Log the update
            await self._log_audit_event(
                user_id=admin_user_id,
                action="update_user_permissions",
                resource="user_permissions",
                resource_id=target_user_id,
                permissions_used=[Permission.MANAGE_USERS],
                success=True
            )
            
            return target_permissions
            
        except Exception as e:
            await self._log_audit_event(
                user_id=admin_user_id,
                action="update_user_permissions_error",
                resource="user_permissions",
                resource_id=target_user_id,
                success=False,
                error_message=str(e)
            )
            return None
    
    async def create_access_token(
        self,
        user_id: str,
        permissions: Optional[List[Permission]] = None,
        access_level: Optional[AccessLevel] = None,
        expires_in_hours: int = 24
    ) -> Optional[AccessToken]:
        """Create access token for analytics API"""
        
        try:
            # Get user permissions
            user_permissions = await self.authenticate_user(user_id)
            if not user_permissions or not user_permissions.is_active:
                return None
            
            # Use provided permissions or user's default permissions
            token_permissions = permissions or user_permissions.permissions
            token_access_level = access_level or user_permissions.access_level
            
            # Generate token
            import secrets
            token = secrets.token_urlsafe(32)
            
            access_token = AccessToken(
                token=token,
                user_id=user_id,
                permissions=token_permissions,
                access_level=token_access_level,
                expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )
            
            # Store token in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id=user_id,
                data_type="access_tokens",
                source_id=token,
                data=access_token.__dict__,
                ttl=expires_in_hours * 3600
            )
            
            # Log token creation
            await self._log_audit_event(
                user_id=user_id,
                action="create_access_token",
                resource="access_token",
                resource_id=token,
                success=True
            )
            
            return access_token
            
        except Exception as e:
            await self._log_audit_event(
                user_id=user_id,
                action="create_access_token_error",
                resource="access_token",
                success=False,
                error_message=str(e)
            )
            return None
    
    async def validate_access_token(self, token: str) -> Optional[AccessToken]:
        """Validate access token and return token data"""
        
        try:
            # Get token data from Vercel KV
            token_data = await self.vercel_kv_service.get_analytics_data(
                user_id="system",  # System-level lookup
                data_type="access_tokens",
                source_id=token
            )
            
            if not token_data:
                return None
            
            access_token = AccessToken(**token_data)
            
            # Check if token is expired
            if access_token.expires_at < datetime.utcnow():
                # Remove expired token
                await self.vercel_kv_service.delete_analytics_data(
                    user_id="system",
                    data_type="access_tokens",
                    source_id=token
                )
                return None
            
            # Check if token is active
            if not access_token.is_active:
                return None
            
            return access_token
            
        except Exception:
            return None
    
    async def revoke_access_token(self, admin_user_id: str, token: str) -> bool:
        """Revoke access token (admin only)"""
        
        try:
            # Check if admin user has permission to manage users
            if not await self.check_permission(admin_user_id, Permission.MANAGE_USERS):
                return False
            
            # Get token data
            token_data = await self.vercel_kv_service.get_analytics_data(
                user_id="system",
                data_type="access_tokens",
                source_id=token
            )
            
            if not token_data:
                return False
            
            # Mark token as inactive
            access_token = AccessToken(**token_data)
            access_token.is_active = False
            
            # Store updated token
            await self.vercel_kv_service.store_analytics_data(
                user_id="system",
                data_type="access_tokens",
                source_id=token,
                data=access_token.__dict__,
                ttl=3600  # 1 hour for revoked tokens
            )
            
            # Log token revocation
            await self._log_audit_event(
                user_id=admin_user_id,
                action="revoke_access_token",
                resource="access_token",
                resource_id=token,
                permissions_used=[Permission.MANAGE_USERS],
                success=True
            )
            
            return True
            
        except Exception as e:
            await self._log_audit_event(
                user_id=admin_user_id,
                action="revoke_access_token_error",
                resource="access_token",
                resource_id=token,
                success=False,
                error_message=str(e)
            )
            return False
    
    async def _log_audit_event(
        self,
        user_id: str,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        permissions_used: Optional[List[Permission]] = None,
        access_level: Optional[AccessLevel] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log audit event for access control"""
        
        try:
            audit_log = AuditLog(
                id=f"audit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                permissions_used=permissions_used or [],
                access_level=access_level or AccessLevel.OWN,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            # Store audit log in Vercel KV
            await self.vercel_kv_service.store_analytics_data(
                user_id="system",
                data_type="audit_logs",
                source_id=audit_log.id,
                data=audit_log.__dict__,
                ttl=31536000  # 1 year
            )
            
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Error logging audit event: {e}")
    
    async def get_audit_logs(
        self,
        admin_user_id: str,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs (admin only)"""
        
        try:
            # Check if admin user has permission to view user data
            if not await self.check_permission(admin_user_id, Permission.VIEW_USER_DATA):
                return []
            
            # Get all audit logs
            audit_logs_data = await self.vercel_kv_service.get_analytics_data(
                user_id="system",
                data_type="audit_logs"
            )
            
            audit_logs = []
            for log_data in audit_logs_data:
                if isinstance(log_data, dict):
                    audit_log = AuditLog(**log_data)
                    
                    # Apply filters
                    if user_id and audit_log.user_id != user_id:
                        continue
                    if action and audit_log.action != action:
                        continue
                    if resource and audit_log.resource != resource:
                        continue
                    if start_date and audit_log.timestamp < start_date:
                        continue
                    if end_date and audit_log.timestamp > end_date:
                        continue
                    
                    audit_logs.append(audit_log)
            
            # Sort by timestamp (newest first) and limit results
            audit_logs.sort(key=lambda x: x.timestamp, reverse=True)
            return audit_logs[:limit]
            
        except Exception as e:
            await self._log_audit_event(
                user_id=admin_user_id,
                action="get_audit_logs_error",
                resource="audit_logs",
                success=False,
                error_message=str(e)
            )
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        
        try:
            # Test Vercel KV connection
            kv_health = await self.vercel_kv_service.health_check()
            
            # Test cache service
            cache_health = await self.cache_service.health_check()
            
            # Get user statistics
            all_permissions = await self.vercel_kv_service.get_all_analytics_data(
                data_type="user_permissions"
            )
            
            active_users = sum(
                1 for p in all_permissions 
                if isinstance(p, dict) and p.get("is_active", False)
            )
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "vercel_kv": kv_health,
                    "cache": cache_health
                },
                "users": {
                    "total": len(all_permissions),
                    "active": active_users
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }


def require_permission(permission: Permission, resource: Optional[str] = None):
    """Decorator to require specific permission for function access"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, user_id: str, *args, **kwargs):
            if not await self.auth_service.check_permission(user_id, permission, resource):
                raise PermissionError(f"Permission {permission.value} required for {resource or 'this operation'}")
            return await func(self, user_id, *args, **kwargs)
        return wrapper
    return decorator


def require_access_level(access_level: AccessLevel):
    """Decorator to require specific access level for function access"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, user_id: str, *args, **kwargs):
            if not await self.auth_service.check_access_level(user_id, access_level):
                raise PermissionError(f"Access level {access_level.value} required for this operation")
            return await func(self, user_id, *args, **kwargs)
        return wrapper
    return decorator




