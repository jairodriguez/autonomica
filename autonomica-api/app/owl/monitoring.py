from __future__ import annotations
from typing import Dict, Any
from .tasks import Task, TaskStatus

class TaskMonitor:
    """Holds the logic for monitoring task execution across the workforce."""
    
    def __init__(self):
        self.task_registry: Dict[str, Task] = {}

    def register_task(self, task: Task):
        """Adds a new task to the registry for monitoring."""
        if task.id not in self.task_registry:
            self.task_registry[task.id] = task
            print(f"Task '{task.title}' ({task.id}) registered for monitoring.")
        else:
            print(f"Warning: Task {task.id} is already registered.")

    def handle_status_update(self, payload: Dict[str, Any]):
        """Handles a status update payload from a message."""
        task_id = payload.get("task_id")
        if task_id in self.task_registry:
            task = self.task_registry[task_id]
            try:
                new_status = TaskStatus(payload.get("status"))
                task.update_status(new_status)
                print(f"Updated task {task.id} to status {new_status.value}. Details: {payload.get('details')}")
                
                # In a real system, this could trigger other workflows
                if new_status == TaskStatus.COMPLETED:
                    print(f"Task {task.id} completed. Checking for dependent tasks...")

            except ValueError:
                print(f"Error: Invalid status '{payload.get('status')}' for task {task_id}.")
        else:
            print(f"Warning: Received status update for unknown task {task_id}")

    def add_task(self, task: Task):
        """Alias for register_task to maintain backward compatibility."""
        self.register_task(task)

    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update a task's status directly."""
        if task_id in self.task_registry:
            task = self.task_registry[task_id]
            task.update_status(status)
        else:
            print(f"Warning: Tried to update status for unknown task {task_id}") 