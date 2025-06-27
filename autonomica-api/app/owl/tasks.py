from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class TaskStatus(str, Enum):
    """Defines the lifecycle status of a task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"

class SubTask(BaseModel):
    """Represents a smaller, executable part of a larger task."""
    id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4()}")
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    """A comprehensive representation of a task to be executed by an agent or a team of agents."""
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4()}")
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    
    dependencies: List[str] = Field(default_factory=list, description="List of task IDs that must be completed first.")
    subtasks: List[SubTask] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list, description="List of tools required to complete the task.")
    
    assigned_to: Optional[str] = Field(default=None, description="The ID of the agent or agent type this task is assigned to.")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible field for additional task-related data.")
    result: Optional[Dict[str, Any]] = None

    def update_status(self, new_status: TaskStatus):
        """Updates the task's status and timestamps."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.completed_at = datetime.utcnow()

    def add_subtask(self, title: str, description: Optional[str] = None) -> SubTask:
        """Adds a new subtask to this task."""
        subtask = SubTask(title=title, description=description)
        self.subtasks.append(subtask)
        return subtask 