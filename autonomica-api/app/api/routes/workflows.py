"""
Workflows API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.owl.workforce import AutonomicaWorkforce

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
    agent_type: Optional[str] = None  # Specific agent to use, or let system choose


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    agent_used: str
    agent_id: str
    capabilities_applied: List[str]
    metadata: Optional[Dict[str, Any]] = None


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


def get_workforce(request: Request) -> AutonomicaWorkforce:
    """Dependency to get workforce from app state"""
    if not hasattr(request.app.state, 'workforce') or not request.app.state.workforce:
        raise HTTPException(status_code=503, detail="OWL Workforce not initialized")
    return request.app.state.workforce


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


@router.post("/workflows/chat", response_model=ChatResponse)
async def chat_with_agents(
    chat_request: ChatRequest,
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Chat with Autonomica marketing agents"""
    
    try:
        # Determine the best agent for the request
        if chat_request.agent_type:
            # Use specific agent if requested
            agent = workforce.get_agent_by_type(chat_request.agent_type)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent type '{chat_request.agent_type}' not found")
        else:
            # Let the system choose the best agent based on the message
            agent = workforce.route_message_to_agent(chat_request.message)
        
        # Create a simple task for the agent
        task_spec = {
            "name": "Chat Response",
            "description": f"Respond to user message: {chat_request.message[:100]}...",
            "inputs": {
                "user_message": chat_request.message,
                "conversation_context": chat_request.context
            },
            "agent_type": agent.type,
            "priority": "high"
        }
        
        # Execute the task
        result = await agent.execute_task(task_spec)
        
        # Update agent status
        agent.tasks_completed += 1
        agent.last_active = agent.created_at  # Update timestamp
        
        return ChatResponse(
            response=result.get("response", "I'm here to help with your marketing needs!"),
            agent_used=agent.name,
            agent_id=agent.id,
            capabilities_applied=agent.capabilities,
            metadata={
                "task_duration": result.get("duration", 0),
                "confidence": result.get("confidence", 0.9),
                "suggestions": result.get("suggestions", [])
            }
        )
        
    except Exception as e:
        # Fallback response if agent execution fails
        return ChatResponse(
            response=f"I'm Autonomica, your AI marketing assistant. I can help you with content creation, SEO optimization, social media management, campaign planning, and data analysis. How can I assist you today?",
            agent_used="System Fallback",
            agent_id="system",
            capabilities_applied=["general_assistance"],
            metadata={"error": str(e), "fallback": True}
        ) 