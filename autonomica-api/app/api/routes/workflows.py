"""
Workflows API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.owl.workforce import AutonomicaWorkforce
from datetime import datetime
from loguru import logger

router = APIRouter()


class WorkflowRequest(BaseModel):
    """Workflow creation request model"""
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    context: Optional[List[Dict[str, str]]] = []
    agent_type: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model with tool execution information"""
    response: str
    agent_name: str
    agent_id: str
    model_used: str
    tools_used: List[str] = []
    cost_info: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    task_completed: bool = True


class CreateAgentRequest(BaseModel):
    """Request to create a new agent"""
    name: str
    agent_type: str
    custom_prompt: str
    model: str
    tools: List[str]
    capabilities: List[str]


class CreateTeamRequest(BaseModel):
    """Request to create a team of agents"""
    team_name: str
    agents: List[CreateAgentRequest]
    description: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Workflow response model"""
    id: str
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    status: str
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    result: Optional[Dict[str, Any]]


class WorkflowListResponse(BaseModel):
    """Workflow list response model"""
    workflows: List[WorkflowResponse]
    total_count: int
    active_count: int
    completed_count: int


# Global workforce instance
_workforce = None

async def get_workforce():
    global _workforce
    if _workforce is None:
        _workforce = AutonomicaWorkforce()
        await _workforce.initialize()
    return _workforce


@router.post("/workflows", response_model=Dict[str, str])
async def create_workflow(
    workflow_request: WorkflowRequest,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create and execute a new workflow"""
    
    workflow_spec = {
        "name": workflow_request.name,
        "description": workflow_request.description,
        "tasks": workflow_request.tasks,
        "metadata": workflow_request.metadata or {}
    }
    
    workflow_id = await workforce.create_workflow(workflow_spec)
    
    return {
        "workflow_id": workflow_id,
        "message": f"Workflow '{workflow_request.name}' created and queued for execution"
    }


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[str] = None,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """List all workflows with optional status filtering"""
    
    workflows = list(workforce.active_workflows.values())
    
    # Apply status filter
    if status:
        workflows = [w for w in workflows if w.status == status]
    
    # Convert to response format
    workflow_responses = [
        WorkflowResponse(**workflow.to_dict()) for workflow in workflows
    ]
    
    # Count by status
    all_workflows = list(workforce.active_workflows.values())
    active_count = len([w for w in all_workflows if w.status in ["pending", "running"]])
    completed_count = len([w for w in all_workflows if w.status == "completed"])
    
    return WorkflowListResponse(
        workflows=workflow_responses,
        total_count=len(all_workflows),
        active_count=active_count,
        completed_count=completed_count
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get a specific workflow by ID"""
    
    workflow_data = await workforce.get_workflow_status(workflow_id)
    if not workflow_data:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return WorkflowResponse(**workflow_data)


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get workflow execution status and results"""
    
    workflow_data = await workforce.get_workflow_status(workflow_id)
    if not workflow_data:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return {
        "workflow_id": workflow_id,
        "status": workflow_data["status"],
        "progress": {
            "started_at": workflow_data.get("started_at"),
            "completed_at": workflow_data.get("completed_at"),
            "tasks_total": len(workflow_data.get("tasks", [])),
            "tasks_completed": workflow_data.get("result", {}).get("tasks_completed", 0) if workflow_data.get("result") else 0
        },
        "result": workflow_data.get("result")
    }


@router.post("/workflows/examples/{example_type}")
async def create_example_workflow(
    example_type: str,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create predefined example workflows for testing"""
    
    examples = {
        "content_generation": {
            "name": "Content Generation Pipeline",
            "description": "Generate blog content and repurpose for social media",
            "tasks": [
                {
                    "name": "Research Topic",
                    "agent_type": "data_analyst",
                    "inputs": {"topic": "AI in Marketing 2024"},
                    "outputs": {"research_data": "object"}
                },
                {
                    "name": "Write Blog Post",
                    "agent_type": "content_writer",
                    "inputs": {"research_data": "$.tasks[0].outputs.research_data"},
                    "outputs": {"blog_post": "text"}
                },
                {
                    "name": "Create Social Posts",
                    "agent_type": "social_media_manager",
                    "inputs": {"blog_post": "$.tasks[1].outputs.blog_post"},
                    "outputs": {"social_posts": "list"}
                }
            ]
        },
        "seo_analysis": {
            "name": "SEO Content Analysis",
            "description": "Analyze content for SEO optimization",
            "tasks": [
                {
                    "name": "Keyword Research",
                    "agent_type": "seo_analyst",
                    "inputs": {"topic": "Marketing Automation"},
                    "outputs": {"keywords": "list"}
                },
                {
                    "name": "Content Optimization",
                    "agent_type": "content_writer",
                    "inputs": {"keywords": "$.tasks[0].outputs.keywords"},
                    "outputs": {"optimized_content": "text"}
                }
            ]
        },
        "campaign_planning": {
            "name": "Marketing Campaign Planning",
            "description": "Plan and structure a marketing campaign",
            "tasks": [
                {
                    "name": "Market Analysis",
                    "agent_type": "marketing_strategist",
                    "inputs": {"product": "SaaS Tool", "target_audience": "SMB"},
                    "outputs": {"market_analysis": "object"}
                },
                {
                    "name": "Campaign Strategy",
                    "agent_type": "marketing_strategist",
                    "inputs": {"market_analysis": "$.tasks[0].outputs.market_analysis"},
                    "outputs": {"campaign_plan": "object"}
                },
                {
                    "name": "Content Calendar",
                    "agent_type": "social_media_manager",
                    "inputs": {"campaign_plan": "$.tasks[1].outputs.campaign_plan"},
                    "outputs": {"content_calendar": "object"}
                }
            ]
        }
    }
    
    if example_type not in examples:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown example type. Available: {', '.join(examples.keys())}"
        )
    
    workflow_spec = examples[example_type]
    workflow_id = await workforce.create_workflow(workflow_spec)
    
    return {
        "workflow_id": workflow_id,
        "message": f"Example workflow '{example_type}' created and queued for execution",
        "example_type": example_type
    }


@router.get("/workflows/examples")
async def list_example_workflows():
    """List available example workflow types"""
    
    return {
        "examples": [
            {
                "type": "content_generation",
                "name": "Content Generation Pipeline",
                "description": "Generate blog content and repurpose for social media"
            },
            {
                "type": "seo_analysis", 
                "name": "SEO Content Analysis",
                "description": "Analyze content for SEO optimization"
            },
            {
                "type": "campaign_planning",
                "name": "Marketing Campaign Planning", 
                "description": "Plan and structure a marketing campaign"
            }
        ]
    }


@router.post("/chat")
async def chat_with_agents(
    request: ChatRequest,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Chat with OWL agents using real tool-enabled task execution"""
    try:
        # Route message to CEO for delegation
        ceo = workforce.get_ceo_agent()
        if not ceo:
            raise HTTPException(status_code=500, detail="No CEO agent available")
        
        # Create task specification for execution
        task_spec = {
            "task_type": "chat_interaction",
            "inputs": {
                "user_message": request.message,
                "context": request.context
            },
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "web_interface"
            }
        }
        
        # Execute task through CEO
        start_time = datetime.utcnow()
        
        # Use the existing execute_task method from the backup
        result = await ceo.execute_task(task_spec)
        
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Create response
        response = ChatResponse(
            response=result.get("response", "Task completed successfully"),
            agent_name=ceo.name,
            agent_id=ceo.id,
            model_used=ceo.model if hasattr(ceo, 'model') else "gpt-4o-mini",
            tools_used=ceo.tools if hasattr(ceo, 'tools') else [],
            cost_info={
                "input_tokens": getattr(ceo, 'total_input_tokens', 0),
                "output_tokens": getattr(ceo, 'total_output_tokens', 0),
                "total_cost": getattr(ceo, 'total_cost', 0.0)
            },
            execution_time=execution_time,
            task_completed=True
        )
        
        logger.info(f"Task completed by {ceo.name} in {execution_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Chat execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@router.post("/agents/create")
async def create_agent(
    request: CreateAgentRequest,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a new custom agent"""
    try:
        # For now, create a basic agent structure
        agent_data = {
            "name": request.name,
            "type": request.agent_type,
            "custom_prompt": request.custom_prompt,
            "model": request.model,
            "tools": request.tools,
            "capabilities": request.capabilities
        }
        
        # This would integrate with the CAMEL framework when fully implemented
        logger.info(f"Agent creation requested: {request.name} ({request.agent_type})")
        
        return {
            "message": f"Agent '{request.name}' creation initiated",
            "agent_config": agent_data,
            "status": "pending_implementation"
        }
        
    except Exception as e:
        logger.error(f"Agent creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent creation failed: {str(e)}")


@router.post("/teams/create")
async def create_team(
    request: CreateTeamRequest,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a team of agents"""
    try:
        team_info = {
            "team_name": request.team_name,
            "description": request.description,
            "agents": [
                {
                    "name": agent.name,
                    "type": agent.agent_type,
                    "model": agent.model,
                    "tools": agent.tools
                }
                for agent in request.agents
            ],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Team creation requested: {request.team_name} with {len(request.agents)} agents")
        
        return {
            "message": f"Team '{request.team_name}' creation initiated",
            "team_info": team_info,
            "status": "pending_implementation"
        }
        
    except Exception as e:
        logger.error(f"Team creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Team creation failed: {str(e)}")


@router.get("/costs")
async def get_cost_summary(
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get comprehensive cost breakdown"""
    try:
        # Basic cost summary for now
        agents = workforce.get_all_agents() if hasattr(workforce, 'get_all_agents') else []
        
        cost_summary = {
            "total_cost": sum(getattr(agent, 'total_cost', 0.0) for agent in agents),
            "total_tasks": sum(getattr(agent, 'tasks_completed', 0) for agent in agents),
            "agent_count": len(agents),
            "agents": [
                {
                    "name": agent.name,
                    "type": getattr(agent, 'type', 'unknown'),
                    "cost": getattr(agent, 'total_cost', 0.0),
                    "tasks": getattr(agent, 'tasks_completed', 0)
                }
                for agent in agents
            ]
        }
        
        return cost_summary
        
    except Exception as e:
        logger.error(f"Cost summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cost summary failed: {str(e)}")


@router.get("/models/pricing")
async def get_model_pricing():
    """Get current model pricing information"""
    try:
        # Model pricing per 1K tokens (input/output)
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015, "provider": "openai"},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "provider": "openai"},
            "gpt-4": {"input": 0.03, "output": 0.06, "provider": "openai"},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002, "provider": "openai"},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015, "provider": "anthropic"},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125, "provider": "anthropic"},
            "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079, "provider": "groq"},
            "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008, "provider": "groq"},
        }
        
        return {
            "pricing": pricing,
            "currency": "USD",
            "unit": "per_1k_tokens",
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pricing retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pricing retrieval failed: {str(e)}")


@router.get("/templates")
async def get_agent_templates():
    """Get available agent templates"""
    try:
        templates = {
            "ceo": {
                "name": "CEO",
                "description": "Executive leader responsible for strategic oversight and team coordination",
                "capabilities": ["strategic_leadership", "team_coordination", "delegation", "client_relations"],
                "recommended_tools": ["search", "document_processing", "excel"],
                "recommended_model": "gpt-4o"
            },
            "content_writer": {
                "name": "Content Writer",
                "description": "Expert content creator for blogs, marketing materials, and engaging copy",
                "capabilities": ["blog_writing", "copywriting", "content_strategy", "storytelling"],
                "recommended_tools": ["search", "browser", "document_processing", "file_write"],
                "recommended_model": "gpt-4o"
            },
            "seo_analyst": {
                "name": "SEO Analyst", 
                "description": "SEO expert for search optimization and organic traffic growth",
                "capabilities": ["keyword_research", "seo_audit", "competitor_analysis", "technical_seo"],
                "recommended_tools": ["search", "browser", "excel", "document_processing"],
                "recommended_model": "gpt-4o-mini"
            },
            "social_media_manager": {
                "name": "Social Media Manager",
                "description": "Social media expert for brand building and audience engagement",
                "capabilities": ["social_strategy", "content_scheduling", "community_management", "social_advertising"],
                "recommended_tools": ["search", "browser", "excel", "document_processing"],
                "recommended_model": "gpt-4o-mini"
            },
            "data_analyst": {
                "name": "Data Analyst",
                "description": "Data expert for marketing analytics and performance insights",
                "capabilities": ["data_analysis", "reporting", "visualization", "predictive_analytics"],
                "recommended_tools": ["excel", "code_execution", "document_processing", "file_write"],
                "recommended_model": "gpt-4o-mini"
            }
        }
        
        return {
            "templates": templates,
            "available_tools": ["search", "browser", "code_execution", "file_write", "document_processing", "excel"],
            "available_models": list(pricing.keys()) if 'pricing' in locals() else ["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022"]
        }
        
    except Exception as e:
        logger.error(f"Template retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")


# Legacy endpoint for backward compatibility
@router.post("/workflows/chat")
async def legacy_chat(request: ChatRequest):
    """Legacy chat endpoint - redirects to new /chat endpoint"""
    return await chat_with_agents(request, await get_workforce()) 