"""
Agents API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.owl.workforce import AutonomicaWorkforce, Agent

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


class AgentListResponse(BaseModel):
    """Agent list response model"""
    agents: List[AgentResponse]
    total_count: int
    active_count: int


def get_workforce(request: Request) -> AutonomicaWorkforce:
    """Dependency to get workforce from app state"""
    if not hasattr(request.app.state, 'workforce') or not request.app.state.workforce:
        raise HTTPException(status_code=503, detail="OWL Workforce not initialized")
    return request.app.state.workforce


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """List all available agents with optional filtering"""
    
    agents = list(workforce.agents.values())
    
    # Apply filters
    if agent_type:
        agents = [a for a in agents if a.type == agent_type]
    
    if status:
        agents = [a for a in agents if a.status == status]
    
    # Convert to response format
    agent_responses = [
        AgentResponse(**agent.to_dict()) for agent in agents
    ]
    
    active_count = len([a for a in workforce.agents.values() if a.status not in ["offline", "error"]])
    
    return AgentListResponse(
        agents=agent_responses,
        total_count=len(workforce.agents),
        active_count=active_count
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get a specific agent by ID"""
    
    agent = await workforce.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return AgentResponse(**agent.to_dict())


@router.get("/agents/types/{agent_type}", response_model=AgentListResponse)
async def get_agents_by_type(
    agent_type: str,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all agents of a specific type"""
    
    agents = await workforce.get_agents_by_type(agent_type)
    
    agent_responses = [
        AgentResponse(**agent.to_dict()) for agent in agents
    ]
    
    return AgentListResponse(
        agents=agent_responses,
        total_count=len(agents),
        active_count=len([a for a in agents if a.status not in ["offline", "error"]])
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