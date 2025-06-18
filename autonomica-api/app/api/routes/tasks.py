"""
Tasks API routes for Autonomica OWL Framework
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

router = APIRouter()


class TaskRequest(BaseModel):
    """Task creation request model"""
    title: str
    description: str
    agent_type: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Task response model"""
    id: str
    title: str
    description: str
    status: str
    agent_type: Optional[str]
    priority: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]]


class TaskListResponse(BaseModel):
    """Task list response model"""
    tasks: List[TaskResponse]
    total_count: int
    pending_count: int
    completed_count: int


# In-memory task storage for demo (would use database in production)
tasks_storage: Dict[str, Dict[str, Any]] = {}


@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest):
    """Create a new task"""
    
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    task = {
        "id": task_id,
        "title": task_request.title,
        "description": task_request.description,
        "status": "pending",
        "agent_type": task_request.agent_type,
        "priority": task_request.priority,
        "created_at": now,
        "updated_at": now,
        "metadata": task_request.metadata or {}
    }
    
    tasks_storage[task_id] = task
    
    return TaskResponse(**task)


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = None,
    agent_type: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List tasks with optional filtering"""
    
    tasks = list(tasks_storage.values())
    
    # Apply filters
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    if agent_type:
        tasks = [t for t in tasks if t["agent_type"] == agent_type]
    
    if priority:
        tasks = [t for t in tasks if t["priority"] == priority]
    
    # Apply pagination
    total_count = len(tasks)
    tasks = tasks[offset:offset + limit]
    
    # Count statuses
    all_tasks = list(tasks_storage.values())
    pending_count = len([t for t in all_tasks if t["status"] == "pending"])
    completed_count = len([t for t in all_tasks if t["status"] == "completed"])
    
    task_responses = [TaskResponse(**task) for task in tasks]
    
    return TaskListResponse(
        tasks=task_responses,
        total_count=total_count,
        pending_count=pending_count,
        completed_count=completed_count
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID"""
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return TaskResponse(**task)


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """Update task status"""
    
    if status not in ["pending", "in_progress", "completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    task = tasks_storage.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task["status"] = status
    task["updated_at"] = datetime.utcnow().isoformat()
    
    return {"message": f"Task {task_id} status updated to {status}"}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    del tasks_storage[task_id]
    
    return {"message": f"Task {task_id} deleted successfully"}


@router.get("/tasks/stats")
async def get_task_stats():
    """Get task statistics"""
    
    all_tasks = list(tasks_storage.values())
    
    stats = {
        "total_tasks": len(all_tasks),
        "by_status": {},
        "by_priority": {},
        "by_agent_type": {}
    }
    
    for task in all_tasks:
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