from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.schema import User, UserRole, Permission, UserPermission, SocialAccount
from app.auth.clerk_middleware import ClerkUser
from app.services.redis_service import RedisService
from app.services.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication, authorization, and user management."""
    
    def __init__(self, db: Session, redis_service: RedisService, cache_service: CacheService):
        self.db = db
        self.redis_service = redis_service
        self.cache_service = cache_service
        
        # Cache keys
        self.USER_CACHE_PREFIX = "user:"
        self.PERMISSIONS_CACHE_PREFIX = "permissions:"
        self.ROLE_CACHE_PREFIX = "role:"
        
        # Cache TTL (in seconds)
        self.USER_CACHE_TTL = 3600  # 1 hour
        self.PERMISSIONS_CACHE_TTL = 1800  # 30 minutes
        self.ROLE_CACHE_TTL = 7200  # 2 hours

    async def get_or_create_user(self, clerk_user: ClerkUser) -> User:
        """Get existing user or create new one from Clerk user data."""
        try:
            # Try to get from cache first
            cache_key = f"{self.USER_CACHE_PREFIX}{clerk_user.clerk_id}"
            cached_user = await self.cache_service.get(cache_key)
            if cached_user:
                return User(**cached_user)
            
            # Check database
            user = self.db.query(User).filter(User.clerk_id == clerk_user.clerk_id).first()
            
            if user:
                # Update last login and sync data
                user.last_login = datetime.utcnow()
                user.email = clerk_user.email
                user.first_name = clerk_user.first_name
                user.last_name = clerk_user.last_name
                user.is_verified = clerk_user.is_verified
                
                self.db.commit()
                
                # Cache the updated user
                await self.cache_service.set(
                    cache_key, 
                    self._user_to_dict(user), 
                    self.USER_CACHE_TTL
                )
                
                return user
            else:
                # Create new user
                user = User(
                    clerk_id=clerk_user.clerk_id,
                    email=clerk_user.email,
                    first_name=clerk_user.first_name,
                    last_name=clerk_user.last_name,
                    role=UserRole.CREATOR,  # Default role
                    is_verified=clerk_user.is_verified,
                    is_active=True,
                    last_login=datetime.utcnow()
                )
                
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                
                # Grant default permissions based on role
                await self._grant_default_permissions(user)
                
                # Cache the new user
                await self.cache_service.set(
                    cache_key, 
                    self._user_to_dict(user), 
                    self.USER_CACHE_TTL
                )
                
                logger.info(f"Created new user: {user.email} with role {user.role}")
                return user
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get or create user"
            )

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with caching."""
        try:
            cache_key = f"{self.USER_CACHE_PREFIX}{user_id}"
            cached_user = await self.cache_service.get(cache_key)
            
            if cached_user:
                return User(**cached_user)
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                await self.cache_service.set(
                    cache_key, 
                    self._user_to_dict(user), 
                    self.USER_CACHE_TTL
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {str(e)}")
            return None

    async def get_user_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        """Get user by Clerk ID with caching."""
        try:
            cache_key = f"{self.USER_CACHE_PREFIX}{clerk_id}"
            cached_user = await self.cache_service.get(cache_key)
            
            if cached_user:
                return User(**cached_user)
            
            user = self.db.query(User).filter(User.clerk_id == clerk_id).first()
            if user:
                await self.cache_service.set(
                    cache_key, 
                    self._user_to_dict(user), 
                    self.USER_CACHE_TTL
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Error in get_user_by_clerk_id: {str(e)}")
            return None

    async def update_user_role(self, user_id: int, new_role: UserRole, updated_by: int) -> User:
        """Update user role and adjust permissions accordingly."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Check if updater has permission
            if not await self.has_permission(updated_by, Permission.ASSIGN_ROLES):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to assign roles"
                )
            
            old_role = user.role
            user.role = new_role
            user.updated_at = datetime.utcnow()
            
            # Remove old role-specific permissions
            await self._remove_role_permissions(user_id, old_role)
            
            # Grant new role-specific permissions
            await self._grant_role_permissions(user_id, new_role)
            
            self.db.commit()
            
            # Clear user cache
            await self._clear_user_cache(user)
            
            logger.info(f"Updated user {user.email} role from {old_role} to {new_role}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_user_role: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user role"
            )

    async def grant_permission(self, user_id: int, permission: Permission, granted_by: int, expires_at: Optional[datetime] = None) -> UserPermission:
        """Grant a specific permission to a user."""
        try:
            # Check if granter has permission
            if not await self.has_permission(granted_by, Permission.ASSIGN_ROLES):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to grant permissions"
                )
            
            # Check if permission already exists
            existing = self.db.query(UserPermission).filter(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission == permission
                )
            ).first()
            
            if existing:
                # Update existing permission
                existing.expires_at = expires_at
                existing.granted_at = datetime.utcnow()
                existing.granted_by = granted_by
                user_permission = existing
            else:
                # Create new permission
                user_permission = UserPermission(
                    user_id=user_id,
                    permission=permission,
                    granted_by=granted_by,
                    expires_at=expires_at
                )
                self.db.add(user_permission)
            
            self.db.commit()
            
            # Clear permissions cache
            await self._clear_permissions_cache(user_id)
            
            logger.info(f"Granted permission {permission} to user {user_id}")
            return user_permission
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in grant_permission: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to grant permission"
            )

    async def revoke_permission(self, user_id: int, permission: Permission, revoked_by: int) -> bool:
        """Revoke a specific permission from a user."""
        try:
            # Check if revoker has permission
            if not await self.has_permission(revoked_by, Permission.ASSIGN_ROLES):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to revoke permissions"
                )
            
            user_permission = self.db.query(UserPermission).filter(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission == permission
                )
            ).first()
            
            if user_permission:
                self.db.delete(user_permission)
                self.db.commit()
                
                # Clear permissions cache
                await self._clear_permissions_cache(user_id)
                
                logger.info(f"Revoked permission {permission} from user {user_id}")
                return True
            
            return False
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in revoke_permission: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke permission"
            )

    async def has_permission(self, user_id: int, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        try:
            # Check cache first
            cache_key = f"{self.PERMISSIONS_CACHE_PREFIX}{user_id}:{permission.value}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                return False
            
            # Check role-based permissions first
            role_permissions = await self._get_role_permissions(user.role)
            if permission in role_permissions:
                await self.cache_service.set(cache_key, True, self.PERMISSIONS_CACHE_TTL)
                return True
            
            # Check explicit user permissions
            user_permission = self.db.query(UserPermission).filter(
                and_(
                    UserPermission.user_id == user_id,
                    UserPermission.permission == permission,
                    or_(
                        UserPermission.expires_at.is_(None),
                        UserPermission.expires_at > datetime.utcnow()
                    )
                )
            ).first()
            
            has_perm = user_permission is not None
            await self.cache_service.set(cache_key, has_perm, self.PERMISSIONS_CACHE_TTL)
            
            return has_perm
            
        except Exception as e:
            logger.error(f"Error in has_permission: {str(e)}")
            return False

    async def has_any_permission(self, user_id: int, permissions: List[Permission]) -> bool:
        """Check if a user has any of the specified permissions."""
        for permission in permissions:
            if await self.has_permission(user_id, permission):
                return True
        return False

    async def has_all_permissions(self, user_id: int, permissions: List[Permission]) -> bool:
        """Check if a user has all of the specified permissions."""
        for permission in permissions:
            if not await self.has_permission(user_id, permission):
                return False
        return True

    async def get_user_permissions(self, user_id: int) -> List[Permission]:
        """Get all permissions for a user (role-based + explicit)."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user or not user.is_active:
                return []
            
            permissions = set()
            
            # Add role-based permissions
            role_permissions = await self._get_role_permissions(user.role)
            permissions.update(role_permissions)
            
            # Add explicit user permissions
            user_permissions = self.db.query(UserPermission).filter(
                and_(
                    UserPermission.user_id == user_id,
                    or_(
                        UserPermission.expires_at.is_(None),
                        UserPermission.expires_at > datetime.utcnow()
                    )
                )
            ).all()
            
            for up in user_permissions:
                permissions.add(up.permission)
            
            return list(permissions)
            
        except Exception as e:
            logger.error(f"Error in get_user_permissions: {str(e)}")
            return []

    async def deactivate_user(self, user_id: int, deactivated_by: int) -> User:
        """Deactivate a user account."""
        try:
            if not await self.has_permission(deactivated_by, Permission.MANAGE_USERS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to deactivate users"
                )
            
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Clear user cache
            await self._clear_user_cache(user)
            
            logger.info(f"Deactivated user: {user.email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in deactivate_user: {str(e)}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate user"
            )

    async def get_users_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """Get users by role with pagination."""
        try:
            users = self.db.query(User).filter(
                and_(
                    User.role == role,
                    User.is_active == True
                )
            ).offset(offset).limit(limit).all()
            
            return users
            
        except Exception as e:
            logger.error(f"Error in get_users_by_role: {str(e)}")
            return []

    async def get_user_social_accounts(self, user_id: int) -> List[SocialAccount]:
        """Get all social media accounts for a user."""
        try:
            accounts = self.db.query(SocialAccount).filter(
                and_(
                    SocialAccount.user_id == user_id,
                    SocialAccount.is_active == True
                )
            ).all()
            
            return accounts
            
        except Exception as e:
            logger.error(f"Error in get_user_social_accounts: {str(e)}")
            return []

    async def _grant_default_permissions(self, user: User) -> None:
        """Grant default permissions based on user role."""
        try:
            role_permissions = await self._get_role_permissions(user.role)
            
            for permission in role_permissions:
                user_permission = UserPermission(
                    user_id=user.id,
                    permission=permission,
                    granted_by=None  # System-granted
                )
                self.db.add(user_permission)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in _grant_default_permissions: {str(e)}")
            self.db.rollback()

    async def _grant_role_permissions(self, user_id: int, role: UserRole) -> None:
        """Grant permissions specific to a role."""
        try:
            role_permissions = await self._get_role_permissions(role)
            
            for permission in role_permissions:
                user_permission = UserPermission(
                    user_id=user_id,
                    permission=permission,
                    granted_by=None  # System-granted
                )
                self.db.add(user_permission)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in _grant_role_permissions: {str(e)}")
            self.db.rollback()

    async def _remove_role_permissions(self, user_id: int, role: UserRole) -> None:
        """Remove permissions specific to a role."""
        try:
            role_permissions = await self._get_role_permissions(role)
            
            for permission in role_permissions:
                self.db.query(UserPermission).filter(
                    and_(
                        UserPermission.user_id == user_id,
                        UserPermission.permission == permission,
                        UserPermission.granted_by.is_(None)  # Only system-granted
                    )
                ).delete()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in _remove_role_permissions: {str(e)}")
            self.db.rollback()

    async def _get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Get permissions associated with a specific role."""
        role_permissions = {
            UserRole.ADMIN: [
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT, Permission.DELETE_CONTENT,
                Permission.PUBLISH_CONTENT, Permission.APPROVE_CONTENT, Permission.MANAGE_SOCIAL_ACCOUNTS,
                Permission.SCHEDULE_POSTS, Permission.PUBLISH_POSTS, Permission.VIEW_ANALYTICS,
                Permission.MANAGE_ANALYTICS, Permission.MANAGE_USERS, Permission.ASSIGN_ROLES,
                Permission.VIEW_USERS, Permission.MANAGE_SETTINGS, Permission.VIEW_LOGS,
                Permission.MANAGE_INTEGRATIONS
            ],
            UserRole.MANAGER: [
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT, Permission.DELETE_CONTENT,
                Permission.PUBLISH_CONTENT, Permission.APPROVE_CONTENT, Permission.MANAGE_SOCIAL_ACCOUNTS,
                Permission.SCHEDULE_POSTS, Permission.PUBLISH_POSTS, Permission.VIEW_ANALYTICS,
                Permission.MANAGE_ANALYTICS, Permission.VIEW_USERS
            ],
            UserRole.EDITOR: [
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT, Permission.PUBLISH_CONTENT,
                Permission.SCHEDULE_POSTS, Permission.PUBLISH_POSTS, Permission.VIEW_ANALYTICS
            ],
            UserRole.CREATOR: [
                Permission.CREATE_CONTENT, Permission.EDIT_CONTENT, Permission.SCHEDULE_POSTS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.VIEWER: [
                Permission.VIEW_ANALYTICS
            ]
        }
        
        return role_permissions.get(role, [])

    async def _clear_user_cache(self, user: User) -> None:
        """Clear all cache entries for a user."""
        try:
            # Clear user cache
            await self.cache_service.delete(f"{self.USER_CACHE_PREFIX}{user.id}")
            await self.cache_service.delete(f"{self.USER_CACHE_PREFIX}{user.clerk_id}")
            
            # Clear permissions cache
            await self._clear_permissions_cache(user.id)
            
        except Exception as e:
            logger.error(f"Error in _clear_user_cache: {str(e)}")

    async def _clear_permissions_cache(self, user_id: int) -> None:
        """Clear permissions cache for a user."""
        try:
            # Get all permissions to clear their cache
            permissions = await self.get_user_permissions(user_id)
            for permission in permissions:
                cache_key = f"{self.PERMISSIONS_CACHE_PREFIX}{user_id}:{permission.value}"
                await self.cache_service.delete(cache_key)
                
        except Exception as e:
            logger.error(f"Error in _clear_permissions_cache: {str(e)}")

    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User model to dictionary for caching."""
        return {
            'id': user.id,
            'clerk_id': user.clerk_id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role.value if user.role else None,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }




