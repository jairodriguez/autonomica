#!/usr/bin/env python3
"""
Simple FastAPI server with real OpenAI integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from openai import OpenAI

app = FastAPI(title="Simple Autonomica API", version="1.0.0")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    context: list = []
    agent_type: str = "ceo_agent"
    agent_name: str = "CEO Agent"

class ChatResponse(BaseModel):
    message: str
    agent_name: str
    agent_type: str
    metadata: dict = {}

@app.get("/")
async def root():
    return {
        "name": "Simple Autonomica API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy", "message": "Simple server is running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with real OpenAI integration"""
    
    try:
        # Create agent-specific system prompts
        agent_prompts = {
            "ceo_agent": """You are a CEO Agent in the Autonomica AI management system. You are a strategic leader who:
            - Provides high-level business guidance and vision
            - Delegates tasks to other AI agents effectively  
            - Makes strategic decisions for the organization
            - Communicates with clarity and authority
            - Focuses on business outcomes and growth
            
            Respond as a CEO would, offering strategic insights and leadership guidance.""",
            
            "marketing_strategist": """You are a Marketing Strategist Agent in the Autonomica AI management system. You are an expert in:
            - Developing comprehensive marketing strategies
            - Brand positioning and messaging
            - Customer segmentation and targeting
            - Campaign planning and execution
            - Market research and competitive analysis
            - ROI optimization and performance metrics
            
            Respond with marketing expertise, providing actionable insights for brand growth and customer engagement.""",
            
            "content_creator": """You are a Content Creator Agent in the Autonomica AI management system. You specialize in:
            - Content strategy and planning
            - Writing engaging blog posts, articles, and copy
            - Social media content creation
            - Video and multimedia content planning
            - SEO-optimized content
            - Maintaining consistent brand voice
            
            Respond creatively with practical content ideas, writing tips, and content strategy recommendations.""",
            
            "seo_specialist": """You are an SEO Specialist Agent in the Autonomica AI management system. You are an expert in:
            - Keyword research and analysis
            - On-page and technical SEO optimization
            - Link building strategies
            - SEO audits and recommendations
            - Performance tracking and reporting
            - Algorithm updates and best practices
            
            Respond with technical SEO expertise and specific, actionable recommendations for improving search rankings."""
        }
        
        # Get the appropriate system prompt for the agent type
        system_prompt = agent_prompts.get(request.agent_type.lower(), agent_prompts["ceo_agent"])
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the faster, cheaper model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return ChatResponse(
            message=ai_response,
            agent_name=request.agent_name,
            agent_type=request.agent_type, 
            metadata={
                "status": "completed",
                "tools_used": [],
                "model": "gpt-4o-mini",
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

@app.get("/api/agents")
async def list_agents():
    """Mock agents endpoint"""
    return {
        "agents": [
            {
                "id": "ceo-001",
                "name": "CEO Agent",
                "type": "ceo_agent",
                "capabilities": ["delegation", "strategy", "coordination"],
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "last_active": "2024-01-01T00:00:00Z",
                "tasks_completed": 0
            }
        ],
        "total_count": 1,
        "active_count": 1
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Autonomica API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False) 