"""
Autonomica OWL API - Production Version
Real AI integration with environment-based configuration
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import logging

# Workforce orchestrator
from app.owl.workforce import Workforce

# Environment Configuration
class Config:
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Frontend URLs (for CORS)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")
    PRODUCTION_FRONTEND_URL = os.getenv("PRODUCTION_FRONTEND_URL", "https://your-app.vercel.app")
    
    # AI Provider Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, anthropic, or mock
    AI_MODEL = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    
    # Performance Settings
    RESPONSE_DELAY = float(os.getenv("RESPONSE_DELAY", "0.1"))  # Seconds between words
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

config = Config()

# Pydantic Models
class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    agentContext: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    response: str

# FastAPI App Setup
app = FastAPI(
    title="Autonomica OWL API",
    description="Production Multi-agent Marketing Automation Platform",
    version="1.0.0"
)

# CORS Configuration for Production
allowed_origins = [
    config.FRONTEND_URL,
    config.PRODUCTION_FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:3001",
]

# Add environment-specific origins
if os.getenv("VERCEL_URL"):
    allowed_origins.append(f"https://{os.getenv('VERCEL_URL')}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.routes.seo import router as seo_router
from app.api.routes.seo_pipeline import router as seo_pipeline_router
from app.api.routes.keyword_suggestions import router as keyword_suggestions_router
app.include_router(seo_router)
app.include_router(seo_pipeline_router)
app.include_router(keyword_suggestions_router)

# Instantiate central Workforce orchestrator
workforce = Workforce(config.AI_MODEL)

# AI Integration
async def call_openai_api(messages: List[Dict], system_prompt: str) -> str:
    """Call OpenAI API for real AI responses"""
    if not config.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + messages,
                    "max_tokens": config.MAX_TOKENS,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {response.status_code}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=500, detail="AI service timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

async def call_anthropic_api(messages: List[Dict], system_prompt: str) -> str:
    """Call Anthropic Claude API for real AI responses"""
    if not config.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Anthropic API key not configured")
    
    # Convert OpenAI format to Anthropic format
    anthropic_messages = []
    for msg in messages:
        if msg["role"] != "system":
            anthropic_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": config.ANTHROPIC_API_KEY,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": config.MAX_TOKENS,
                    "system": system_prompt,
                    "messages": anthropic_messages
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Anthropic API error: {response.status_code}")
            
            data = response.json()
            return data["content"][0]["text"]
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=500, detail="AI service timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

async def generate_ai_response(messages: List[ChatMessage], agent_context: Optional[Dict[str, Any]] = None) -> str:
    """Generate real AI responses based on provider configuration"""
    
    # Delegate to Workforce to obtain agent + full conversation history
    # (Redis-backed if configured).
    # TODO: pass real user_id when auth middleware wired.
    orchestration = await workforce.run_agents(messages)
    agent = orchestration["agent"]
    history = orchestration["history"]

    # Convert history into OpenAI/Anthropic compatible message list
    openai_messages = [
        {
            "role": m.get("role", "user") if m.get("role") != "system" else "assistant",
            "content": m.get("content", "")
        }
        for m in history
        if m.get("role") in ["user", "assistant"]
    ]
    
    # Call appropriate AI provider
    if config.AI_PROVIDER == "openai":
        return await call_openai_api(openai_messages, agent.system_prompt)
    elif config.AI_PROVIDER == "anthropic":
        return await call_anthropic_api(openai_messages, agent.system_prompt)
    else:
        # Mock responses for development/testing
        return f"[MOCK RESPONSE] I'm a {agent.name} agent. In production, this would be a real AI response using {config.AI_PROVIDER}."

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Autonomica OWL API",
        "version": "1.0.0",
        "description": "Production Multi-agent Marketing Automation Platform",
        "owl_framework": "production-active",
        "ai_provider": config.AI_PROVIDER,
        "agents_available": len(workforce.agents),
        "environment": "production" if config.AI_PROVIDER != "mock" else "development",
        "endpoints": {
            "health": "/api/health",
            "agents": "/api/agents", 
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "owl_framework": "production-active",
        "ai_provider": config.AI_PROVIDER,
        "agents_online": len(workforce.agents),
        "environment": "production" if config.AI_PROVIDER != "mock" else "development"
    }

@app.get("/api/agents")
async def get_agents():
    """Get all available agents"""
    return {
        "agents": [a.__dict__ for a in workforce.agents.values()],
        "total": len(workforce.agents),
        "active": len([a for a in workforce.agents.values() if a.status == "active"]),
        "ai_provider": config.AI_PROVIDER
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle chat interactions with real AI agents"""
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    try:
        # Generate AI response
        response_text = await generate_ai_response(request.messages, request.agentContext)
        
        # Create streaming response for better UX
        async def stream_response():
            words = response_text.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": f"msg_{datetime.now().timestamp()}",
                    "role": "assistant", 
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "timestamp": datetime.now().isoformat(),
                    "agent": "production-owl-agent",
                    "ai_provider": config.AI_PROVIDER
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(config.RESPONSE_DELAY)  # Configurable typing speed
            
            # End of stream
            yield f"data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("🦉 Starting Autonomica OWL API (Production)...")
    print(f"🤖 AI Provider: {config.AI_PROVIDER}")
    print(f"🌐 Frontend URL: {config.FRONTEND_URL}")
    print("⚡ Ready for production deployment")
    
    uvicorn.run(
        "main_api:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,  # Disable reload in production
        log_level="info"
    ) 