"""
Agent Management API routes for Autonomica
Dynamic agent creation, cost tracking, and team management
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from loguru import logger

router = APIRouter()

# Model pricing per 1K tokens (input/output) in USD
MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015, "provider": "openai", "speed": "fast"},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "provider": "openai", "speed": "very_fast"},
    "gpt-4": {"input": 0.03, "output": 0.06, "provider": "openai", "speed": "slow"},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002, "provider": "openai", "speed": "fast"},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015, "provider": "anthropic", "speed": "fast"},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125, "provider": "anthropic", "speed": "very_fast"},
    "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079, "provider": "groq", "speed": "very_fast"},
    "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008, "provider": "groq", "speed": "ultra_fast"},
}

# Agent templates for quick creation
AGENT_TEMPLATES = {
    "ceo": {
        "name": "CEO",
        "description": "Executive leader responsible for strategic oversight and team coordination",
        "base_prompt": """You are the CEO of Autonomica, an AI-powered marketing agency. Your role is to:
1. Coordinate and delegate tasks to specialist agents
2. Make strategic decisions about resource allocation  
3. Ensure all tasks align with business objectives
4. Provide high-level oversight and quality control
5. Interface with clients and stakeholders

You have access to tools for research, document processing, and team coordination. When given a task, analyze it and either handle it directly or delegate to appropriate specialist agents.""",
        "capabilities": ["strategic_leadership", "team_coordination", "delegation", "client_relations"],
        "recommended_tools": ["search", "document_processing", "excel"],
        "recommended_model": "gpt-4o",
        "category": "leadership"
    },
    
    "content_writer": {
        "name": "Content Writer",
        "description": "Expert content creator for blogs, marketing materials, and engaging copy",
        "base_prompt": """You are a professional content writer specializing in creating engaging, high-quality content. Your expertise includes:
1. Blog posts and articles
2. Marketing copy and sales materials
3. Social media content
4. Technical documentation
5. Creative storytelling

Use your tools to research topics, analyze competitor content, and create compelling, well-researched content that resonates with target audiences.""",
        "capabilities": ["blog_writing", "copywriting", "content_strategy", "storytelling"],
        "recommended_tools": ["search", "browser", "document_processing", "file_write"],
        "recommended_model": "gpt-4o",
        "category": "creative"
    },
    
    "seo_analyst": {
        "name": "SEO Analyst",
        "description": "SEO expert for search optimization and organic traffic growth",
        "base_prompt": """You are an SEO specialist focused on improving search engine visibility and organic traffic. Your expertise includes:
1. Keyword research and analysis
2. On-page and technical SEO optimization
3. Competitor analysis
4. Content optimization for search engines
5. SEO performance tracking and reporting

Use your tools to conduct thorough SEO audits, research keywords, analyze competitors, and provide actionable SEO recommendations.""",
        "capabilities": ["keyword_research", "seo_audit", "competitor_analysis", "technical_seo"],
        "recommended_tools": ["search", "browser", "excel", "document_processing"],
        "recommended_model": "gpt-4o-mini",
        "category": "technical"
    },
    
    "social_media_manager": {
        "name": "Social Media Manager", 
        "description": "Social media expert for brand building and audience engagement",
        "base_prompt": """You are a social media marketing expert responsible for building brand presence across social platforms. Your expertise includes:
1. Social media strategy development
2. Content calendar planning and scheduling
3. Community engagement and management
4. Social media advertising campaigns
5. Performance analytics and reporting

Use your tools to research trending topics, analyze competitor social presence, and create comprehensive social media strategies.""",
        "capabilities": ["social_strategy", "content_scheduling", "community_management", "social_advertising"],
        "recommended_tools": ["search", "browser", "excel", "document_processing"],
        "recommended_model": "gpt-4o-mini",
        "category": "marketing"
    },
    
    "data_analyst": {
        "name": "Data Analyst",
        "description": "Data expert for marketing analytics and performance insights",
        "base_prompt": """You are a marketing data analyst focused on extracting insights from data to drive business decisions. Your expertise includes:
1. Marketing performance analysis
2. Customer behavior analytics
3. Campaign ROI measurement
4. Data visualization and reporting
5. Predictive analytics for marketing

Use your tools to process data files, create visualizations, and provide actionable insights based on marketing metrics and KPIs.""",
        "capabilities": ["data_analysis", "reporting", "visualization", "predictive_analytics"],
        "recommended_tools": ["excel", "code_execution", "document_processing", "file_write"],
        "recommended_model": "gpt-4o-mini",
        "category": "analytics"
    },
    
    "customer_success": {
        "name": "Customer Success Manager",
        "description": "Customer relationship and satisfaction expert",
        "base_prompt": """You are a customer success manager dedicated to ensuring client satisfaction and retention. Your expertise includes:
1. Customer onboarding and training
2. Relationship management and communication
3. Issue resolution and support
4. Customer feedback analysis
5. Retention strategy development

Use your tools to analyze customer data, track satisfaction metrics, and develop strategies to improve customer experience.""",
        "capabilities": ["customer_relations", "support", "retention", "communication"],
        "recommended_tools": ["search", "document_processing", "excel"],
        "recommended_model": "gpt-4o-mini",
        "category": "support"
    }
}

# Available tools for agents
AVAILABLE_TOOLS = {
    "search": {"name": "Web Search", "description": "Search the web for information"},
    "browser": {"name": "Web Browser", "description": "Browse and interact with websites"},
    "code_execution": {"name": "Code Execution", "description": "Execute Python code and scripts"},
    "file_write": {"name": "File Operations", "description": "Create, read, and modify files"},
    "document_processing": {"name": "Document Processing", "description": "Process PDFs, docs, and other documents"},
    "excel": {"name": "Excel/Spreadsheet", "description": "Work with spreadsheets and data analysis"},
    "email": {"name": "Email", "description": "Send and manage emails"},
    "calendar": {"name": "Calendar", "description": "Schedule and manage calendar events"}
}

# Request/Response models
class CreateAgentRequest(BaseModel):
    name: str
    agent_type: str
    custom_prompt: str
    model: str
    tools: List[str]
    capabilities: List[str] = []
    description: Optional[str] = None

class CreateTeamRequest(BaseModel):
    team_name: str
    description: Optional[str] = None
    agents: List[CreateAgentRequest]

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = None
    custom_prompt: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None

class AgentResponse(BaseModel):
    id: str
    name: str
    type: str
    model: str
    tools: List[str]
    status: str
    created_at: str
    cost_info: Dict[str, Any]
    description: Optional[str] = None

# In-memory storage (in production, use a proper database)
agents_db = {}
teams_db = {}

@router.get("/models/pricing")
async def get_model_pricing():
    """Get current model pricing and performance information"""
    return {
        "pricing": MODEL_PRICING,
        "currency": "USD",
        "unit": "per_1k_tokens",
        "last_updated": datetime.utcnow().isoformat(),
        "note": "Prices may vary based on actual provider rates"
    }

@router.get("/templates")
async def get_agent_templates():
    """Get all available agent templates"""
    return {
        "templates": AGENT_TEMPLATES,
        "categories": list(set(template["category"] for template in AGENT_TEMPLATES.values())),
        "available_tools": AVAILABLE_TOOLS,
        "available_models": list(MODEL_PRICING.keys())
    }

@router.get("/tools")
async def get_available_tools():
    """Get all available tools for agents"""
    return {
        "tools": AVAILABLE_TOOLS,
        "total_count": len(AVAILABLE_TOOLS)
    }

@router.post("/agents", response_model=AgentResponse)
async def create_agent(request: CreateAgentRequest):
    """Create a new custom agent"""
    try:
        # Validate model
        if request.model not in MODEL_PRICING:
            raise HTTPException(status_code=400, detail=f"Model {request.model} not supported")
        
        # Validate tools
        invalid_tools = [tool for tool in request.tools if tool not in AVAILABLE_TOOLS]
        if invalid_tools:
            raise HTTPException(status_code=400, detail=f"Invalid tools: {invalid_tools}")
        
        # Create agent
        agent_id = str(uuid.uuid4())
        agent = {
            "id": agent_id,
            "name": request.name,
            "type": request.agent_type,
            "custom_prompt": request.custom_prompt,
            "model": request.model,
            "tools": request.tools,
            "capabilities": request.capabilities,
            "description": request.description,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "user",
            "last_active": datetime.utcnow().isoformat(),
            "cost_info": {
                "total_cost": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "tasks_completed": 0
            }
        }
        
        agents_db[agent_id] = agent
        
        logger.info(f"Created agent: {request.name} ({request.agent_type}) with model {request.model}")
        
        return AgentResponse(**agent)
        
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")

@router.post("/agents/from-template", response_model=AgentResponse)
async def create_agent_from_template(
    template_type: str,
    custom_name: Optional[str] = None,
    custom_model: Optional[str] = None,
    custom_tools: Optional[List[str]] = None
):
    """Create an agent from a predefined template"""
    try:
        if template_type not in AGENT_TEMPLATES:
            raise HTTPException(status_code=400, detail=f"Template {template_type} not found")
        
        template = AGENT_TEMPLATES[template_type]
        
        request = CreateAgentRequest(
            name=custom_name or template["name"],
            agent_type=template_type,
            custom_prompt=template["base_prompt"],
            model=custom_model or template["recommended_model"],
            tools=custom_tools or template["recommended_tools"],
            capabilities=template["capabilities"],
            description=template["description"]
        )
        
        return await create_agent(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template agent creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template agent creation failed: {str(e)}")

@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(status: Optional[str] = None, agent_type: Optional[str] = None):
    """List all agents with optional filtering"""
    try:
        agents = list(agents_db.values())
        
        if status:
            agents = [agent for agent in agents if agent["status"] == status]
        
        if agent_type:
            agents = [agent for agent in agents if agent["type"] == agent_type]
        
        return [AgentResponse(**agent) for agent in agents]
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a specific agent by ID"""
    try:
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AgentResponse(**agents_db[agent_id])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@router.put("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, request: UpdateAgentRequest):
    """Update an existing agent"""
    try:
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db[agent_id]
        
        # Update fields if provided
        if request.name is not None:
            agent["name"] = request.name
        if request.custom_prompt is not None:
            agent["custom_prompt"] = request.custom_prompt
        if request.model is not None:
            if request.model not in MODEL_PRICING:
                raise HTTPException(status_code=400, detail=f"Model {request.model} not supported")
            agent["model"] = request.model
        if request.tools is not None:
            invalid_tools = [tool for tool in request.tools if tool not in AVAILABLE_TOOLS]
            if invalid_tools:
                raise HTTPException(status_code=400, detail=f"Invalid tools: {invalid_tools}")
            agent["tools"] = request.tools
        if request.capabilities is not None:
            agent["capabilities"] = request.capabilities
        
        agent["last_active"] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated agent: {agent_id}")
        
        return AgentResponse(**agent)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        if agent_id not in agents_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = agents_db.pop(agent_id)
        
        logger.info(f"Deleted agent: {agent['name']} ({agent_id})")
        
        return {"message": f"Agent {agent['name']} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@router.post("/teams")
async def create_team(request: CreateTeamRequest):
    """Create a team of agents"""
    try:
        team_id = str(uuid.uuid4())
        created_agents = []
        
        # Create all agents in the team
        for agent_request in request.agents:
            agent_response = await create_agent(agent_request)
            created_agents.append(agent_response.dict())
        
        team = {
            "id": team_id,
            "name": request.team_name,
            "description": request.description,
            "agents": created_agents,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        teams_db[team_id] = team
        
        logger.info(f"Created team: {request.team_name} with {len(created_agents)} agents")
        
        return {
            "team_id": team_id,
            "team_name": request.team_name,
            "agents_created": len(created_agents),
            "team": team
        }
        
    except Exception as e:
        logger.error(f"Team creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Team creation failed: {str(e)}")

@router.get("/teams")
async def list_teams():
    """List all teams"""
    try:
        return {
            "teams": list(teams_db.values()),
            "total_count": len(teams_db)
        }
        
    except Exception as e:
        logger.error(f"Failed to list teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")

@router.get("/teams/{team_id}")
async def get_team(team_id: str):
    """Get a specific team by ID"""
    try:
        if team_id not in teams_db:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return teams_db[team_id]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}")

@router.get("/costs/summary")
async def get_cost_summary():
    """Get comprehensive cost breakdown across all agents"""
    try:
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        total_tasks = 0
        
        agent_costs = []
        
        for agent in agents_db.values():
            cost_info = agent["cost_info"]
            total_cost += cost_info["total_cost"]
            total_input_tokens += cost_info["total_input_tokens"]
            total_output_tokens += cost_info["total_output_tokens"]
            total_tasks += cost_info["tasks_completed"]
            
            agent_costs.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "agent_type": agent["type"],
                "model": agent["model"],
                "cost": cost_info["total_cost"],
                "input_tokens": cost_info["total_input_tokens"],
                "output_tokens": cost_info["total_output_tokens"],
                "tasks_completed": cost_info["tasks_completed"]
            })
        
        # Sort by cost descending
        agent_costs.sort(key=lambda x: x["cost"], reverse=True)
        
        return {
            "summary": {
                "total_cost": round(total_cost, 4),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tasks": total_tasks,
                "active_agents": len(agents_db),
                "active_teams": len(teams_db)
            },
            "agent_breakdown": agent_costs,
            "currency": "USD",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")

@router.get("/costs/estimate")
async def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
):
    """Estimate cost for a given model and token usage"""
    try:
        if model not in MODEL_PRICING:
            raise HTTPException(status_code=400, detail=f"Model {model} not supported")
        
        pricing = MODEL_PRICING[model]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "costs": {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6)
            },
            "pricing_info": pricing,
            "currency": "USD"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to estimate cost: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to estimate cost: {str(e)}")

@router.get("/stats")
async def get_system_stats():
    """Get overall system statistics"""
    try:
        agents = list(agents_db.values())
        teams = list(teams_db.values())
        
        # Agent statistics
        agent_types = {}
        models_used = {}
        tools_used = {}
        
        for agent in agents:
            # Count agent types
            agent_type = agent["type"]
            agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            # Count models
            model = agent["model"]
            models_used[model] = models_used.get(model, 0) + 1
            
            # Count tools
            for tool in agent["tools"]:
                tools_used[tool] = tools_used.get(tool, 0) + 1
        
        return {
            "agents": {
                "total": len(agents),
                "by_type": agent_types,
                "by_model": models_used,
                "tools_usage": tools_used
            },
            "teams": {
                "total": len(teams),
                "average_team_size": sum(len(team["agents"]) for team in teams) / len(teams) if teams else 0
            },
            "system": {
                "available_models": len(MODEL_PRICING),
                "available_tools": len(AVAILABLE_TOOLS),
                "available_templates": len(AGENT_TEMPLATES)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system stats: {str(e)}") 