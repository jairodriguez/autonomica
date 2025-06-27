# 🔐 Clerk Authentication Integration Guide

This guide covers the complete Clerk authentication implementation in Autonomica, including both frontend (Next.js) and backend (FastAPI) integration.

## Overview

Autonomica uses [Clerk](https://clerk.com) for user authentication, providing secure JWT-based authentication between the Next.js frontend and FastAPI backend. The system ensures that all API operations are tied to authenticated users.

## Architecture

```
Frontend (Next.js)     →     Backend (FastAPI)
┌─────────────────┐    JWT   ┌─────────────────┐
│ Clerk Auth      │  ──────→ │ Clerk Middleware│
│ - Sign In/Up    │          │ - Token Verify  │
│ - User Session  │          │ - User Context  │
│ - JWT Tokens    │          │ - Route Guard   │
└─────────────────┘          └─────────────────┘
```

## Prerequisites

1. **Clerk Account**: Create an account at [clerk.com](https://clerk.com)
2. **Clerk Application**: Set up a new application in your Clerk dashboard
3. **API Keys**: Obtain both publishable and secret keys from Clerk

## Frontend Setup (Next.js)

### 1. Environment Configuration

Create `.env.local` in the frontend directory:

```env
# Frontend Environment Variables
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
CLERK_SECRET_KEY=sk_test_your_secret_key_here
```

### 2. Clerk Dashboard Configuration

Configure these URLs in your Clerk dashboard:

- **Sign-in URL**: `http://localhost:3000/sign-in`
- **Sign-up URL**: `http://localhost:3000/sign-up`
- **After sign-in URL**: `http://localhost:3000/projects`
- **After sign-up URL**: `http://localhost:3000/projects`

### 3. Authentication Components

#### Layout with ClerkProvider
```typescript
// src/app/layout.tsx
import { ClerkProvider } from '@clerk/nextjs'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  )
}
```

#### Protected Route Middleware
```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isProtectedRoute = createRouteMatcher(['/projects(.*)'])

export default clerkMiddleware((auth, req) => {
  if (isProtectedRoute(req)) auth().protect()
})

export const config = {
  matcher: [
    '/((?!.*\\..*|_next).*)',
    '/',
    '/(api|trpc)(.*)'
  ],
}
```

#### Authentication Pages
```typescript
// src/app/sign-in/[[...rest]]/page.tsx
import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <SignIn 
        appearance={{
          baseTheme: 'dark',
          variables: { colorPrimary: '#3b82f6' }
        }}
      />
    </div>
  )
}
```

### 4. Getting User Session Token

For authenticated API calls, get the session token:

```typescript
// In a React component
import { useAuth } from '@clerk/nextjs'

function MyComponent() {
  const { getToken } = useAuth()
  
  const makeAuthenticatedRequest = async () => {
    const token = await getToken()
    
    const response = await fetch('/api/agents', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    return response.json()
  }
}
```

## Backend Setup (FastAPI)

### 1. Environment Configuration

Add to your `.env` file in the backend directory:

```env
# Backend Environment Variables
CLERK_SECRET_KEY=sk_test_your_secret_key_here
```

### 2. Dependencies

The backend uses these packages:
```bash
pip install clerk-backend-api pyjwt fastapi
```

### 3. Clerk Middleware Implementation

```python
# app/auth/clerk_middleware.py
import os
import jwt
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk

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
    """Verify Clerk session token and return user information"""
    try:
        token = credentials.credentials
        
        # Decode JWT to get session ID
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        session_id = unverified_payload.get("sid")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no session ID found"
            )
        
        # Verify session with Clerk
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> ClerkUser:
    """FastAPI dependency to get the current authenticated user"""
    return await verify_clerk_token(credentials)
```

### 4. Protected API Routes

Example of protecting API routes with Clerk authentication:

```python
# app/api/routes/agents.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.clerk_middleware import get_current_user, ClerkUser

router = APIRouter()

@router.get("/agents")
async def list_agents(
    current_user: ClerkUser = Depends(get_current_user)
):
    """List agents for the authenticated user"""
    # Access user information: current_user.user_id, current_user.email
    user_agents = get_user_agents(current_user.user_id)
    return {"agents": user_agents}

@router.post("/agents")
async def create_agent(
    agent_data: dict,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Create a new agent for the authenticated user"""
    agent = create_new_agent(
        data=agent_data,
        user_id=current_user.user_id
    )
    return {"agent": agent}
```

## API Request Examples

### 1. Frontend Making Authenticated Requests

```typescript
// Frontend API utility
import { useAuth } from '@clerk/nextjs'

export const useApiClient = () => {
  const { getToken } = useAuth()
  
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const token = await getToken()
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`)
    }
    
    return response.json()
  }
  
  return { apiCall }
}

// Usage in component
function AgentsList() {
  const { apiCall } = useApiClient()
  
  const fetchAgents = async () => {
    try {
      const data = await apiCall('/api/agents')
      setAgents(data.agents)
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    }
  }
  
  useEffect(() => {
    fetchAgents()
  }, [])
}
```

### 2. Direct API Calls with curl

```bash
# Get session token from Clerk (in browser dev tools)
TOKEN="your_jwt_token_here"

# List user's agents
curl -X GET "http://localhost:8000/api/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Create new agent
curl -X POST "http://localhost:8000/api/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Custom Agent",
    "agent_type": "custom",
    "custom_prompt": "You are a helpful assistant",
    "model": "gpt-4",
    "tools": ["web_search"],
    "capabilities": ["analysis", "research"]
  }'
```

### 3. Response Examples

**Successful Authentication:**
```json
{
  "agents": [
    {
      "id": "agent_123",
      "name": "CEO Agent",
      "type": "ceo_agent",
      "user_id": "user_clerk_123",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 1,
  "active_count": 1
}
```

**Authentication Failure:**
```json
{
  "detail": "Authentication failed"
}
```

## Authentication Flow

### 1. User Sign-In Process
1. User visits `/sign-in` page
2. Clerk handles authentication (email/password, social login, etc.)
3. Upon success, user is redirected to `/projects`
4. Clerk sets session cookies and provides JWT tokens

### 2. API Request Process
1. Frontend gets JWT token using `getToken()` from `useAuth()`
2. Token is included in `Authorization: Bearer <token>` header
3. Backend middleware extracts and verifies the token with Clerk
4. Clerk confirms session is active and returns user information
5. Request proceeds with user context available

### 3. Token Validation Process
1. Extract JWT token from Authorization header
2. Decode token to get session ID (without verification)
3. Call Clerk API to verify session and token
4. Retrieve user information from Clerk
5. Return user context for use in protected routes

## Security Considerations

### 1. Token Handling
- Tokens are automatically handled by Clerk's frontend SDK
- Tokens are short-lived and automatically refreshed
- Never store tokens in localStorage or sessionStorage
- Always use HTTPS in production

### 2. Route Protection
- Frontend: Use Clerk middleware to protect routes
- Backend: Use `get_current_user` dependency on protected endpoints
- Validate user access to resources (e.g., user can only access their own agents)

### 3. Environment Variables
- Keep `CLERK_SECRET_KEY` secure and never commit to version control
- Use different Clerk applications for development and production
- Rotate keys periodically

## Error Handling

### Common Error Scenarios

**1. Missing Authorization Header**
```json
{
  "detail": "Missing or invalid authorization header"
}
```

**2. Invalid/Expired Token**
```json
{
  "detail": "Session is not active"
}
```

**3. Access Denied**
```json
{
  "detail": "Access denied: You can only access your own agents"
}
```

### Error Handling in Frontend
```typescript
const handleApiError = (error: any) => {
  if (error.status === 401) {
    // Redirect to sign-in or refresh token
    window.location.href = '/sign-in'
  } else if (error.status === 403) {
    // Show access denied message
    setError('Access denied')
  } else {
    // Handle other errors
    setError('An unexpected error occurred')
  }
}
```

## Testing Authentication

### 1. Frontend Testing
```bash
# Start frontend development server
cd autonomica-frontend
npm run dev

# Visit http://localhost:3000
# Test sign-in/sign-up flows
# Verify protection of /projects route
```

### 2. Backend Testing
```bash
# Start backend server
cd autonomica-api
source venv/bin/activate
python simple_server.py

# Test with authenticated requests using browser dev tools
# Get JWT token from Application -> Cookies or using getToken()
```

### 3. Integration Testing
```typescript
// Test authenticated API calls
import { test, expect } from '@playwright/test'

test('authenticated user can access agents', async ({ page }) => {
  // Sign in user
  await page.goto('/sign-in')
  await page.fill('[name="identifier"]', 'user@example.com')
  await page.fill('[name="password"]', 'password')
  await page.click('[type="submit"]')
  
  // Navigate to projects
  await page.goto('/projects')
  
  // Verify authenticated API calls work
  const response = await page.waitForResponse('**/api/agents')
  expect(response.status()).toBe(200)
})
```

## Troubleshooting

### 1. "Invalid publishable key" Error
- Verify key format starts with `pk_test_` or `pk_live_`
- Check environment variable spelling
- Restart development server after adding env vars

### 2. Backend Authentication Fails
- Verify `CLERK_SECRET_KEY` is set correctly
- Check Clerk dashboard for API key validity
- Ensure token is being sent with correct format

### 3. CORS Issues
- Add frontend URL to `ALLOWED_ORIGINS` in backend
- Verify Clerk dashboard URLs match your setup
- Check browser network tab for CORS errors

### 4. Session Not Active
- Check if user is actually signed in
- Verify token hasn't expired
- Ensure Clerk session settings allow your use case

## Migration from Other Auth Systems

If migrating from another authentication system:

1. **Export User Data**: Export existing user data
2. **Import to Clerk**: Use Clerk's user import APIs
3. **Update API Routes**: Replace auth middleware with Clerk implementation
4. **Update Frontend**: Replace auth components with Clerk components
5. **Test Thoroughly**: Verify all authentication flows work correctly

## Production Deployment

### 1. Environment Setup
```env
# Production environment variables
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_your_live_key
CLERK_SECRET_KEY=sk_live_your_live_secret_key
```

### 2. Clerk Dashboard Configuration
- Create production application in Clerk
- Configure production URLs
- Set up production API keys
- Configure webhooks for user events (if needed)

### 3. Security Checklist
- [ ] Use HTTPS for all endpoints
- [ ] Set secure cookie settings
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring for auth failures
- [ ] Configure session timeout appropriately

## Support and Resources

- **Clerk Documentation**: [https://clerk.com/docs](https://clerk.com/docs)
- **Clerk Next.js Guide**: [https://clerk.com/docs/quickstarts/nextjs](https://clerk.com/docs/quickstarts/nextjs)
- **FastAPI Security**: [https://fastapi.tiangolo.com/tutorial/security/](https://fastapi.tiangolo.com/tutorial/security/)
- **Autonomica Frontend Setup**: See `autonomica-frontend/CLERK_SETUP.md`

---

**Implementation Status**: ✅ Complete - Authentication system is fully implemented and operational 