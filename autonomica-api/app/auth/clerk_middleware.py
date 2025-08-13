"""
Clerk Authentication Middleware for FastAPI
"""

import os
from typing import Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from loguru import logger

from app.core.config import settings

# Initialize Clerk client. Different versions accept different args; fallback to env-based init.
try:
    clerk_client = Clerk(secret_key=settings.CLERK_SECRET_KEY)
except TypeError:
    try:
        clerk_client = Clerk(api_key=settings.CLERK_SECRET_KEY)
    except TypeError:
        clerk_client = Clerk()
security = HTTPBearer()

class ClerkUser:
    """Represents a validated and authenticated Clerk user"""
    def __init__(self, user_id: str, claims: Dict[str, Any]):
        self.user_id = user_id
        self.claims = claims
        # You can add more properties here based on your needs, e.g., email
        self.email = claims.get("email", "")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "claims": self.claims,
            "email": self.email
        }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> ClerkUser:
    """
    FastAPI dependency to verify the Clerk JWT and return the user.
    This function now correctly and securely verifies the token.
    """
    token = credentials.credentials
    try:
        # Verify the token using the Clerk client's JWKS
        # This is the secure way to validate the token.
        payload = clerk_client.verify_token(token)
        
        # Check if the session is active
        session_id = payload.get("sid")
        if not session_id:
            logger.warning("Token verification failed: No session ID (sid) in token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing session information."
            )
            
        session = clerk_client.sessions.get_session(session_id)
        if session.status != "active":
            logger.warning(f"Authentication failed for user {session.user_id}: Session status is '{session.status}'.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User session is not active. Status: {session.status}"
            )

        logger.info(f"Successfully authenticated user {session.user_id} with session {session_id}.")
        return ClerkUser(user_id=session.user_id, claims=payload)

    except Exception as e:
        # This will catch expired tokens, invalid signatures, etc.
        logger.error(f"Clerk token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}"
        )

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