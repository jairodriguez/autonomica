"""
Clerk Authentication Middleware for FastAPI
"""

import os
import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from loguru import logger

# Initialize Clerk client
clerk_client = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))
security = HTTPBearer()

class ClerkUser:
    """Represents an authenticated Clerk user"""
    def __init__(self, user_id: str, email: str, first_name: str = "", last_name: str = ""):
        self.user_id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name
        }

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials) -> ClerkUser:
    """
    Verify Clerk session token and return user information
    """
    try:
        token = credentials.credentials
        
        # Verify the JWT token with Clerk
        # First, decode without verification to get the session ID
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        session_id = unverified_payload.get("sid")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no session ID found"
            )
        
        # Verify the session with Clerk
        try:
            session = clerk_client.sessions.verify_session(
                session_id=session_id,
                token=token
            )
            
            if not session or session.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session is not active"
                )
            
            # Get user information
            user = clerk_client.users.get_user(user_id=session.user_id)
            
            return ClerkUser(
                user_id=user.id,
                email=user.email_addresses[0].email_address if user.email_addresses else "",
                first_name=user.first_name or "",
                last_name=user.last_name or ""
            )
            
        except Exception as e:
            logger.error(f"Clerk session verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )
            
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> ClerkUser:
    """
    FastAPI dependency to get the current authenticated user
    """
    return await verify_clerk_token(credentials)

def require_auth(request: Request) -> ClerkUser:
    """
    Synchronous dependency to require authentication
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    # This is a simplified sync version - in practice, use get_current_user
    # for async routes
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use get_current_user dependency for async routes"
    ) 