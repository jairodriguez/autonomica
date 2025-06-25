"""
Agents API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.owl.workforce import AutonomicaWorkforce, Agent
from app.auth.clerk_middleware import get_current_user, ClerkUser

router = APIRouter()


class AgentResponse(BaseModel):
    """Agent response model"""
    id: str
    name: str
    type: str
    capabilities: List[str]
    status: str
    created_at: str
    last_active: str
    tasks_completed: int
    user_id: Optional[str] = None


class AgentListResponse(BaseModel):
    """Agent list response model"""
    agents: List[AgentResponse]
    total_count: int
    active_count: int


class CreateAgentRequest(BaseModel):
    """Request model for creating a new agent"""
    name: str
    agent_type: str
    custom_prompt: str
    model: str
    tools: List[str]
    capabilities: List[str]


class CreateAgentFromTemplateRequest(BaseModel):
    """Request model for creating agent from template"""
    template_type: str
    custom_name: Optional[str] = None
    custom_prompt: Optional[str] = None
    custom_model: Optional[str] = None
    custom_tools: Optional[List[str]] = None


def get_workforce(request: Request) -> AutonomicaWorkforce:
    """Dependency to get workforce from app state"""
    if not hasattr(request.app.state, 'workforce') or not request.app.state.workforce:
        raise HTTPException(status_code=503, detail="OWL Workforce not initialized")
    return request.app.state.workforce


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """List all available agents for the authenticated user with optional filtering"""
    
    # Filter agents by user_id to show only user's own agents
    user_agents = [
        agent for agent in workforce.agents.values() 
        if agent.user_id == current_user.user_id
    ]
    
    # Apply additional filters
    if agent_type:
        user_agents = [a for a in user_agents if a.type == agent_type]
    
    if status:
        user_agents = [a for a in user_agents if a.status == status]
    
    # Convert to response format
    agent_responses = [
        AgentResponse(**agent.to_dict()) for agent in user_agents
    ]
    
    # Count active agents for this user only
    active_count = len([a for a in user_agents if a.status not in ["offline", "error"]])
    
    return AgentListResponse(
        agents=agent_responses,
        total_count=len(user_agents),
        active_count=active_count
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get a specific agent by ID (user can only access their own agents)"""
    
    agent = workforce.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Check if the agent belongs to the authenticated user
    if agent.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own agents")
    
    return AgentResponse(**agent.to_dict())


@router.get("/agents/types/{agent_type}", response_model=AgentListResponse)
async def get_agents_by_type(
    agent_type: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all agents of a specific type for the authenticated user"""
    
    agents = workforce.get_agents_by_type(agent_type)
    
    # Filter to only include user's own agents
    user_agents = [a for a in agents if a.user_id == current_user.user_id]
    
    agent_responses = [
        AgentResponse(**agent.to_dict()) for agent in user_agents
    ]
    
    return AgentListResponse(
        agents=agent_responses,
        total_count=len(user_agents),
        active_count=len([a for a in user_agents if a.status not in ["offline", "error"]])
    )


@router.get("/agents/capabilities")
async def get_agent_capabilities(
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all available agent capabilities"""
    
    capabilities = set()
    agent_types = set()
    
    for agent in workforce.agents.values():
        agent_types.add(agent.type)
        capabilities.update(agent.capabilities)
    
    return {
        "agent_types": sorted(list(agent_types)),
        "capabilities": sorted(list(capabilities)),
        "total_agents": len(workforce.agents)
    }


@router.post("/agents", response_model=AgentResponse)
async def create_agent(
    request: CreateAgentRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a new custom agent"""
    
    try:
        agent = await workforce.create_custom_agent(
            name=request.name,
            agent_type=request.agent_type,
            custom_prompt=request.custom_prompt,
            model=request.model,
            tools=request.tools,
            capabilities=request.capabilities,
            created_by=current_user.user_id,
            user_id=current_user.user_id
        )
        
        return AgentResponse(**agent.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create agent: {str(e)}")


@router.post("/agents/from-template", response_model=AgentResponse)
async def create_agent_from_template(
    request: CreateAgentFromTemplateRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a new agent from a template"""
    
    try:
        agent = await workforce.create_agent_from_template(
            template_type=request.template_type,
            custom_name=request.custom_name,
            custom_prompt=request.custom_prompt,
            custom_model=request.custom_model,
            custom_tools=request.custom_tools,
            created_by=current_user.user_id,
            user_id=current_user.user_id
        )
        
        return AgentResponse(**agent.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@router.get("/agents/templates")
async def get_agent_templates(
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all available agent templates"""
    
    return workforce.get_available_templates()