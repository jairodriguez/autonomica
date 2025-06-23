"""
Tasks API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.auth.clerk_middleware import get_current_user, ClerkUser
from app.owl.workforce import AutonomicaWorkforce

router = APIRouter()


class TaskRequest(BaseModel):
    """Task creation request model"""
    title: str
    description: str
    agent_id: Optional[str] = None  # Specific agent to assign the task to
    agent_type: Optional[str] = None  # Type of agent if no specific agent
    priority: str = "medium"  # low, medium, high
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Task response model"""
    id: str
    title: str
    description: str
    status: str
    agent_id: Optional[str]
    agent_type: Optional[str]
    priority: str
    created_at: str
    updated_at: str
    user_id: str  # Associated user
    metadata: Optional[Dict[str, Any]]


class TaskListResponse(BaseModel):
    """Task list response model"""
    tasks: List[TaskResponse]
    total_count: int
    pending_count: int
    completed_count: int


class TaskStatusResponse(BaseModel):
    """Enhanced task status response with execution details"""
    id: str
    title: str
    description: str
    status: str
    agent_id: Optional[str]
    agent_name: Optional[str]
    agent_type: Optional[str]
    priority: str
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    user_id: str
    metadata: Optional[Dict[str, Any]]
    
    # OWL execution details
    execution_id: Optional[str] = None
    execution_status: Optional[str] = None  # running, completed, failed
    execution_progress: Optional[float] = None  # 0.0 to 1.0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    execution_cost: Optional[float] = None
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BatchStatusRequest(BaseModel):
    """Request model for batch status checking"""
    task_ids: List[str]


class BatchStatusResponse(BaseModel):
    """Response model for batch status checking"""
    tasks: List[TaskStatusResponse]
    summary: Dict[str, int]  # Status counts


class AgentTasksResponse(BaseModel):
    """Response for agent-specific task status"""
    agent_id: str
    agent_name: str
    agent_type: str
    tasks: List[TaskStatusResponse]
    total_tasks: int
    task_summary: Dict[str, int]  # status -> count


class WorkflowTaskRequest(BaseModel):
    """Individual task within a workflow"""
    title: str
    description: str
    agent_type: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)  # Task titles or indices this depends on
    priority: int = 5  # 1-10
    estimated_duration: Optional[int] = None  # minutes


class WorkflowRequest(BaseModel):
    """Request to create a multi-agent workflow"""
    title: str
    description: str
    tasks: List[WorkflowTaskRequest]
    orchestration_strategy: str = "optimal"  # optimal, parallel, sequential
    max_parallel_tasks: int = 3
    metadata: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Response for workflow creation or status"""
    id: str
    title: str
    description: str
    status: str
    progress: float  # 0.0 to 1.0
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    total_cost: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None
    estimated_cost: Optional[float] = None


def get_workforce(request: Request) -> AutonomicaWorkforce:
    """Dependency to get workforce from app state"""
    if not hasattr(request.app.state, 'workforce') or not request.app.state.workforce:
        raise HTTPException(status_code=503, detail="OWL Workforce not initialized")
    return request.app.state.workforce


# In-memory task storage for demo (would use database in production)
# Structure: {task_id: task_data}
tasks_storage: Dict[str, Dict[str, Any]] = {}


async def get_enhanced_task_status(
    task: Dict[str, Any], 
    workforce: AutonomicaWorkforce
) -> TaskStatusResponse:
    """Get enhanced task status with OWL execution details"""
    
    # Get agent details if assigned
    agent_name = None
    agent_status = None
    execution_details = {}
    
    if task.get("agent_id"):
        agent = workforce.get_agent(task["agent_id"])
        if agent:
            agent_name = agent.name
            agent_status = agent.status
            
            # Look for execution details in workforce task executions
            for execution in workforce.task_executions:
                if execution.agent_id == agent.id and str(execution.id) == task.get("execution_id"):
                    execution_details = {
                        "execution_id": execution.id,
                        "execution_status": execution.status,
                        "execution_progress": 1.0 if execution.status == "completed" else (0.5 if execution.status == "running" else 0.0),
                        "input_tokens": execution.input_tokens,
                        "output_tokens": execution.output_tokens,
                        "execution_cost": execution.cost,
                        "execution_result": execution.result,
                        "error_message": execution.result.get("error") if execution.result and "error" in execution.result else None
                    }
                    break
    
    return TaskStatusResponse(
        id=task["id"],
        title=task["title"],
        description=task["description"],
        status=task["status"],
        agent_id=task.get("agent_id"),
        agent_name=agent_name,
        agent_type=task.get("agent_type"),
        priority=task["priority"],
        created_at=task["created_at"],
        updated_at=task["updated_at"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        user_id=task["user_id"],
        metadata=task.get("metadata"),
        **execution_details
    )


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: TaskRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a new task and associate it with the authenticated user"""
    
    # Validate agent assignment
    assigned_agent = None
    if task_request.agent_id:
        # Verify the specific agent exists and belongs to the user
        agent = workforce.get_agent(task_request.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {task_request.agent_id} not found")
        
        # Check if the agent belongs to the authenticated user
        if agent.user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied: You can only assign tasks to your own agents")
        
        assigned_agent = agent
        
    elif task_request.agent_type:
        # Find available agents of the specified type belonging to the user
        user_agents = workforce.get_agents_by_type(task_request.agent_type)
        user_agents = [a for a in user_agents if a.user_id == current_user.user_id]
        
        if not user_agents:
            raise HTTPException(
                status_code=404, 
                detail=f"No agents of type '{task_request.agent_type}' found for user"
            )
        
        # Assign to the first available agent of this type
        assigned_agent = user_agents[0]
    
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    task = {
        "id": task_id,
        "title": task_request.title,
        "description": task_request.description,
        "status": "pending",
        "agent_id": assigned_agent.id if assigned_agent else None,
        "agent_type": assigned_agent.type if assigned_agent else task_request.agent_type,
        "priority": task_request.priority,
        "created_at": now,
        "updated_at": now,
        "user_id": current_user.user_id,  # Associate with authenticated user
        "metadata": task_request.metadata or {}
    }
    
    tasks_storage[task_id] = task
    
    # If an agent is assigned, queue the task with OWL framework
    if assigned_agent:
        try:
            # Queue the task for execution by the assigned agent
            execution_id = await workforce.assign_task_to_agent(
                agent_id=assigned_agent.id,
                task_id=task_id,
                task_description=task_request.description,
                task_metadata=task.copy()
            )
            task["status"] = "queued"
            task["execution_id"] = execution_id
            task["started_at"] = datetime.utcnow().isoformat()
            task["updated_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            # If assignment fails, keep task as pending for manual assignment later
            print(f"Warning: Failed to assign task to agent {assigned_agent.id}: {e}")
    
    return TaskResponse(**task)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: ClerkUser = Depends(get_current_user)
):
    """List tasks for the authenticated user with optional filtering"""
    
    # Filter tasks to only show user's own tasks
    user_tasks = [
        task for task in tasks_storage.values() 
        if task["user_id"] == current_user.user_id
    ]
    
    # Apply additional filters
    if status:
        user_tasks = [t for t in user_tasks if t["status"] == status]
    
    if agent_type:
        user_tasks = [t for t in user_tasks if t["agent_type"] == agent_type]
    
    if priority:
        user_tasks = [t for t in user_tasks if t["priority"] == priority]
    
    # Apply pagination
    total_count = len(user_tasks)
    user_tasks = user_tasks[offset:offset + limit]
    
    # Count statuses for user's tasks only
    all_user_tasks = [
        task for task in tasks_storage.values() 
        if task["user_id"] == current_user.user_id
    ]
    pending_count = len([t for t in all_user_tasks if t["status"] == "pending"])
    completed_count = len([t for t in all_user_tasks if t["status"] == "completed"])
    
    task_responses = [TaskResponse(**task) for task in user_tasks]
    
    return TaskListResponse(
        tasks=task_responses,
        total_count=total_count,
        pending_count=pending_count,
        completed_count=completed_count
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Get a specific task by ID (user can only access their own tasks)"""
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Check if the task belongs to the authenticated user
    if task["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own tasks")
    
    return TaskResponse(**task)


@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str, 
    status: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Update task status (user can only update their own tasks)"""
    
    if status not in ["pending", "queued", "in_progress", "completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Check if the task belongs to the authenticated user
    if task["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only update your own tasks")
    
    # Update task status
    old_status = task["status"]
    task["status"] = status
    task["updated_at"] = datetime.utcnow().isoformat()
    
    # If task is being assigned to an agent and has an agent_id, notify OWL framework
    if status == "queued" and task.get("agent_id") and old_status != "queued":
        try:
            await workforce.assign_task_to_agent(
                agent_id=task["agent_id"],
                task_id=task_id,
                task_description=task["description"],
                task_metadata=task.copy()
            )
        except Exception as e:
            # If assignment fails, revert status
            task["status"] = old_status
            raise HTTPException(status_code=500, detail=f"Failed to assign task to agent: {e}")
    
    return {"message": f"Task {task_id} status updated to {status}"}


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: ClerkUser = Depends(get_current_user)
):
    """Delete a task (user can only delete their own tasks)"""
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Check if the task belongs to the authenticated user
    if task["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only delete your own tasks")
    
    del tasks_storage[task_id]
    
    return {"message": f"Task {task_id} deleted successfully"}


@router.get("/tasks/stats")
async def get_task_stats(current_user: ClerkUser = Depends(get_current_user)):
    """Get task statistics for the authenticated user"""
    
    # Filter to user's tasks only
    user_tasks = [
        task for task in tasks_storage.values() 
        if task["user_id"] == current_user.user_id
    ]
    
    stats = {
        "total_tasks": len(user_tasks),
        "by_status": {},
        "by_priority": {},
        "by_agent_type": {}
    }
    
    for task in user_tasks:
        # Count by status
        status = task["status"]
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Count by priority
        priority = task["priority"]
        stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        # Count by agent type
        agent_type = task.get("agent_type", "unassigned")
        stats["by_agent_type"][agent_type] = stats["by_agent_type"].get(agent_type, 0) + 1
    
    return stats


# Enhanced Task Status Endpoints for Task 2.7

@router.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get enhanced status of a specific task with OWL execution details"""
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # Check if the task belongs to the authenticated user
    if task["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own tasks")
    
    return await get_enhanced_task_status(task, workforce)


@router.post("/tasks/status/batch", response_model=BatchStatusResponse)
async def get_batch_task_status(
    request: BatchStatusRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get status of multiple tasks in a single request"""
    
    if len(request.task_ids) > 50:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 50 tasks per batch request")
    
    task_statuses = []
    status_summary = {}
    
    for task_id in request.task_ids:
        task = tasks_storage.get(task_id)
        
        if not task:
            continue  # Skip non-existent tasks
        
        # Check if the task belongs to the authenticated user
        if task["user_id"] != current_user.user_id:
            continue  # Skip tasks that don't belong to user
        
        task_status = await get_enhanced_task_status(task, workforce)
        task_statuses.append(task_status)
        
        # Count statuses for summary
        status = task_status.status
        status_summary[status] = status_summary.get(status, 0) + 1
    
    return BatchStatusResponse(
        tasks=task_statuses,
        summary=status_summary
    )


@router.get("/tasks/agent/{agent_id}/status", response_model=AgentTasksResponse)
async def get_agent_task_status(
    agent_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all tasks assigned to a specific agent with their status"""
    
    # Verify the agent exists and belongs to the user
    agent = workforce.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    if agent.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: You can only access your own agents")
    
    # Find all tasks assigned to this agent
    agent_tasks = [
        task for task in tasks_storage.values()
        if task.get("agent_id") == agent_id and task["user_id"] == current_user.user_id
    ]
    
    # Get enhanced status for each task
    task_statuses = []
    for task in agent_tasks:
        task_status = await get_enhanced_task_status(task, workforce)
        task_statuses.append(task_status)
    
    # Count active (non-completed) tasks
    active_tasks = len([t for t in task_statuses if t.status not in ["completed", "failed", "cancelled"]])
    
    return AgentTasksResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        agent_type=agent.type,
        tasks=task_statuses,
        total_tasks=len(task_statuses),
        task_summary={t.status: 1 for t in task_statuses}
    )


@router.get("/tasks/status/live")
async def get_live_task_status(
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get live status summary of all user tasks with real-time execution info"""
    
    # Get all user tasks
    user_tasks = [
        task for task in tasks_storage.values() 
        if task["user_id"] == current_user.user_id
    ]
    
    # Organize by status with execution details
    live_status = {
        "total_tasks": len(user_tasks),
        "active_executions": 0,
        "by_status": {},
        "by_agent": {},
        "execution_summary": {
            "total_cost": 0.0,
            "total_tokens": 0,
            "running_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0
        }
    }
    
    for task in user_tasks:
        status = task["status"]
        
        # Count by status
        live_status["by_status"][status] = live_status["by_status"].get(status, 0) + 1
        
        # Count by agent
        if task.get("agent_id"):
            agent = workforce.get_agent(task["agent_id"])
            if agent:
                agent_key = f"{agent.name} ({agent.type})"
                if agent_key not in live_status["by_agent"]:
                    live_status["by_agent"][agent_key] = {
                        "total": 0,
                        "active": 0,
                        "completed": 0
                    }
                
                live_status["by_agent"][agent_key]["total"] += 1
                
                if status in ["queued", "in_progress"]:
                    live_status["by_agent"][agent_key]["active"] += 1
                    live_status["active_executions"] += 1
                elif status == "completed":
                    live_status["by_agent"][agent_key]["completed"] += 1
        
        # Add execution summary from OWL
        for execution in workforce.task_executions:
            if execution.agent_id == task.get("agent_id"):
                live_status["execution_summary"]["total_cost"] += execution.cost
                live_status["execution_summary"]["total_tokens"] += execution.input_tokens + execution.output_tokens
                
                if execution.status == "running":
                    live_status["execution_summary"]["running_tasks"] += 1
                elif execution.status == "completed":
                    live_status["execution_summary"]["completed_tasks"] += 1
                elif execution.status == "failed":
                    live_status["execution_summary"]["failed_tasks"] += 1
    
    # Round cost for display
    live_status["execution_summary"]["total_cost"] = round(live_status["execution_summary"]["total_cost"], 4)
    
    return live_status


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(
    workflow_request: WorkflowRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Create a new multi-agent workflow"""
    
    try:
        # Convert API request to workflow tasks format
        workflow_tasks = []
        for i, task_req in enumerate(workflow_request.tasks):
            # Convert dependencies from titles/indices to actual task IDs (simplified)
            task_dependencies = []
            for dep in task_req.dependencies:
                if dep.isdigit():
                    # Dependency is an index
                    dep_index = int(dep) - 1
                    if 0 <= dep_index < len(workflow_request.tasks):
                        task_dependencies.append(f"task-{dep_index + 1}")
                else:
                    # Dependency is a title - find matching task (simplified)
                    for j, other_task in enumerate(workflow_request.tasks):
                        if other_task.title == dep:
                            task_dependencies.append(f"task-{j + 1}")
                            break
            
            workflow_tasks.append({
                "title": task_req.title,
                "description": task_req.description,
                "agent_type": task_req.agent_type,
                "dependencies": task_dependencies,
                "priority": task_req.priority,
                "estimated_duration": task_req.estimated_duration
            })
        
        # Create workflow using OWL framework
        workflow = await workforce.create_workflow(
            title=workflow_request.title,
            description=workflow_request.description,
            user_id=current_user.user_id,
            workflow_tasks=workflow_tasks,
            orchestration_strategy=workflow_request.orchestration_strategy,
            max_parallel_tasks=workflow_request.max_parallel_tasks,
            metadata=workflow_request.metadata
        )
        
        # Create orchestration plan
        plan = await workforce.create_orchestration_plan(workflow.id)
        
        return WorkflowResponse(
            id=workflow.id,
            title=workflow.title,
            description=workflow.description,
            status=workflow.status,
            progress=0.0,
            total_tasks=len(workflow.tasks),
            completed_tasks=0,
            failed_tasks=0,
            running_tasks=0,
            total_cost=0.0,
            created_at=workflow.created_at.isoformat(),
            estimated_duration=plan.estimated_duration,
            estimated_cost=plan.estimated_cost
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create workflow: {str(e)}")


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get status of a specific workflow"""
    
    try:
        # Get workflow status from OWL framework
        status = workforce.get_workflow_status(workflow_id)
        
        # Verify user has access to this workflow
        workflow = workforce.workflows.get(workflow_id)
        if not workflow or workflow.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return WorkflowResponse(
            id=status["workflow_id"],
            title=status["title"],
            description=workflow.description,
            status=status["status"],
            progress=status["progress"],
            total_tasks=status["total_tasks"],
            completed_tasks=status["completed_tasks"],
            failed_tasks=status["failed_tasks"],
            running_tasks=status["running_tasks"],
            total_cost=status["total_cost"],
            created_at=status["created_at"],
            started_at=status.get("started_at"),
            completed_at=status.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflow status: {str(e)}")


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Start execution of a workflow"""
    
    try:
        # Verify user has access to this workflow
        workflow = workforce.workflows.get(workflow_id)
        if not workflow or workflow.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status not in ["created", "planning", "failed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot execute workflow in status '{workflow.status}'"
            )
        
        # Execute workflow
        success = await workforce.execute_workflow(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "execution_started": success,
            "message": "Workflow execution started successfully" if success else "Workflow execution failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing workflow: {str(e)}")


@router.get("/workflows")
async def list_user_workflows(
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """List all workflows for the authenticated user"""
    
    try:
        workflows = workforce.get_user_workflows(current_user.user_id)
        return {
            "workflows": workflows,
            "total_count": len(workflows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflows: {str(e)}")


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Cancel a running workflow"""
    
    try:
        # Verify user has access to this workflow
        workflow = workforce.workflows.get(workflow_id)
        if not workflow or workflow.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status not in ["running", "pending", "planning"]:
            raise HTTPException(status_code=400, detail=f"Cannot cancel workflow with status: {workflow.status}")
        
        # Cancel the workflow
        workflow.status = "cancelled"
        workflow.completed_at = datetime.utcnow()
        
        # Cancel any running tasks
        for task in workflow.tasks:
            if task.status == "running":
                task.status = "cancelled"
                task.completed_at = datetime.utcnow()
        
        return {"message": "Workflow cancelled successfully", "workflow_id": workflow_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling workflow: {str(e)}")


@router.post("/workflows/{workflow_id}/tasks", response_model=TaskResponse)
async def add_task_to_workflow(
    workflow_id: str,
    task_request: TaskRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Add a new task to an existing workflow"""
    
    # Implementation of task addition to workflow logic
    # This is a placeholder and should be replaced with the actual implementation
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    task = {
        "id": task_id,
        "title": task_request.title,
        "description": task_request.description,
        "status": "pending",
        "agent_id": None,
        "agent_type": task_request.agent_type,
        "priority": task_request.priority,
        "created_at": now,
        "updated_at": now,
        "user_id": current_user.user_id,
        "metadata": task_request.metadata or {}
    }
    
    tasks_storage[task_id] = task
    
    # If an agent is assigned, queue the task with OWL framework
    if task_request.agent_type:
        # Find available agents of the specified type belonging to the user
        user_agents = workforce.get_agents_by_type(task_request.agent_type)
        user_agents = [a for a in user_agents if a.user_id == current_user.user_id]
        
        if not user_agents:
            raise HTTPException(
                status_code=404, 
                detail=f"No agents of type '{task_request.agent_type}' found for user"
            )
        
        # Assign to the first available agent of this type
        task["agent_id"] = user_agents[0].id
    
    return TaskResponse(**task)


# LangChain NLP Endpoints for Task 2.9

class NLPTaskRequest(BaseModel):
    """Request for executing an NLP task"""
    task_type: str  # text_summarization, sentiment_analysis, etc.
    agent_id: Optional[str] = None  # Specific agent or auto-select
    text: str
    parameters: Optional[Dict[str, Any]] = {}  # Task-specific parameters


class NLPWorkflowRequest(BaseModel):
    """Request for executing multiple NLP tasks"""
    tasks: List[Dict[str, Any]]  # List of NLP tasks with type and data
    sequential: bool = False  # Execute sequentially vs parallel


class EnableNLPRequest(BaseModel):
    """Request to enable NLP capabilities for agents"""
    agent_ids: Optional[List[str]] = None  # Specific agents or all user agents
    capabilities: Optional[List[str]] = None  # Specific capabilities or all available


@router.get("/nlp/capabilities")
async def get_nlp_capabilities(
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get all available LangChain NLP capabilities"""
    
    try:
        capabilities = await workforce.get_available_nlp_capabilities()
        return capabilities
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving NLP capabilities: {str(e)}")


@router.post("/nlp/enable")
async def enable_nlp_capabilities(
    request: EnableNLPRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Enable LangChain NLP capabilities for user's agents"""
    
    try:
        if request.agent_ids:
            # Enable for specific agents
            results = {"agent_results": []}
            for agent_id in request.agent_ids:
                agent = workforce.get_agent(agent_id)
                if not agent or agent.user_id != current_user.user_id:
                    results["agent_results"].append({
                        "agent_id": agent_id,
                        "status": "failed",
                        "error": "Agent not found or access denied"
                    })
                    continue
                
                success = await workforce.enable_agent_nlp(agent_id, request.capabilities)
                results["agent_results"].append({
                    "agent_id": agent_id,
                    "agent_name": agent.name,
                    "status": "success" if success else "failed",
                    "nlp_capabilities": agent.nlp_capabilities if success else []
                })
            
            return results
        else:
            # Enable for all user agents
            results = await workforce.bulk_enable_nlp(
                user_id=current_user.user_id,
                capabilities=request.capabilities
            )
            return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling NLP capabilities: {str(e)}")


@router.post("/nlp/execute")
async def execute_nlp_task(
    request: NLPTaskRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Execute a single NLP task"""
    
    try:
        # Find appropriate agent
        if request.agent_id:
            agent = workforce.get_agent(request.agent_id)
            if not agent or agent.user_id != current_user.user_id:
                raise HTTPException(status_code=404, detail="Agent not found or access denied")
            if not agent.nlp_enabled:
                raise HTTPException(status_code=400, detail="Agent does not have NLP capabilities enabled")
            if request.task_type not in agent.nlp_capabilities:
                raise HTTPException(status_code=400, detail=f"Agent does not support task type: {request.task_type}")
        else:
            # Auto-select agent
            user_agents = [a for a in workforce.agents.values() if a.user_id == current_user.user_id and a.nlp_enabled]
            capable_agents = [a for a in user_agents if request.task_type in a.nlp_capabilities]
            
            if not capable_agents:
                raise HTTPException(status_code=400, detail=f"No agents available for task type: {request.task_type}")
            
            agent = capable_agents[0]  # Select first available agent
        
        # Prepare task parameters
        task_params = {"text": request.text, **request.parameters}
        
        # Execute the NLP task
        execution = await agent.execute_nlp_task(request.task_type, **task_params)
        
        if not execution:
            raise HTTPException(status_code=500, detail="Failed to execute NLP task")
        
        return {
            "execution_id": execution.id,
            "agent_id": agent.id,
            "agent_name": agent.name,
            "task_type": execution.capability,
            "status": execution.status,
            "input_data": execution.input_data,
            "output_data": execution.output_data,
            "tokens_used": execution.tokens_used,
            "cost": execution.cost,
            "execution_time": execution.execution_time,
            "created_at": execution.created_at.isoformat(),
            "error_message": execution.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing NLP task: {str(e)}")


@router.post("/nlp/workflow")
async def execute_nlp_workflow(
    request: NLPWorkflowRequest,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Execute a workflow of multiple NLP tasks"""
    
    try:
        results = await workforce.execute_nlp_workflow(
            workflow_tasks=request.tasks,
            user_id=current_user.user_id
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing NLP workflow: {str(e)}")


@router.get("/nlp/analytics")
async def get_nlp_analytics(
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get comprehensive NLP usage analytics for the user"""
    
    try:
        analytics = workforce.get_nlp_analytics(user_id=current_user.user_id)
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving NLP analytics: {str(e)}")


@router.get("/agents/{agent_id}/nlp")
async def get_agent_nlp_status(
    agent_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get NLP status and capabilities for a specific agent"""
    
    try:
        agent = workforce.get_agent(agent_id)
        if not agent or agent.user_id != current_user.user_id:
            raise HTTPException(status_code=404, detail="Agent not found or access denied")
        
        nlp_summary = agent.get_nlp_summary()
        
        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "agent_type": agent.type,
            **nlp_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agent NLP status: {str(e)}")


@router.get("/nlp/executions/{execution_id}")
async def get_nlp_execution_details(
    execution_id: str,
    current_user: ClerkUser = Depends(get_current_user),
    workforce: AutonomicaWorkforce = Depends(get_workforce)
):
    """Get detailed information about a specific NLP execution"""
    
    try:
        # Find the execution across all user's agents
        for agent in workforce.agents.values():
            if agent.user_id != current_user.user_id:
                continue
            
            for execution in agent.nlp_executions:
                if execution.id == execution_id:
                    return {
                        "execution_id": execution.id,
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "capability": execution.capability,
                        "input_data": execution.input_data,
                        "output_data": execution.output_data,
                        "tokens_used": execution.tokens_used,
                        "cost": execution.cost,
                        "execution_time": execution.execution_time,
                        "status": execution.status,
                        "error_message": execution.error_message,
                        "created_at": execution.created_at.isoformat()
                    }
        
        raise HTTPException(status_code=404, detail="NLP execution not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving NLP execution details: {str(e)}") 