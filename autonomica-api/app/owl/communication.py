from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Import the new Task model
from .tasks import Task, SubTask, TaskStatus

class MessageType(str, Enum):
    """Defines the types of messages agents can send to each other."""
    TASK_ASSIGNMENT = "TASK_ASSIGNMENT"
    TASK_DECOMPOSITION_REQUEST = "TASK_DECOMPOSITION_REQUEST"
    TASK_DECOMPOSITION_RESPONSE = "TASK_DECOMPOSITION_RESPONSE"
    STATUS_UPDATE = "STATUS_UPDATE"
    FEEDBACK = "FEEDBACK"
    DATA_REQUEST = "DATA_REQUEST"
    DATA_RESPONSE = "DATA_RESPONSE"
    GENERAL_QUERY = "GENERAL_QUERY"
    ERROR_INFO = "ERROR_INFO"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    NEGOTIATION_REQUEST = "NEGOTIATION_REQUEST"
    NEGOTIATION_RESPONSE = "NEGOTIATION_RESPONSE"
    RESOLUTION_FOUND = "RESOLUTION_FOUND"

class MessageHeader(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_id: str
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BasePayload(BaseModel):
    """Base model for all message payloads to ensure consistency."""
    pass

class TaskAssignmentPayload(BasePayload):
    """Payload for assigning a new task to an agent."""
    task: Task

class TaskDecompositionRequestPayload(BasePayload):
    """Payload to request the decomposition of a complex task."""
    task: Task

class TaskDecompositionResponsePayload(BasePayload):
    """Payload that returns the result of a task decomposition."""
    original_task_id: str
    subtasks: List[SubTask]

class FeedbackPayload(BasePayload):
    """Payload for providing feedback on a completed task."""
    task_id: str
    rating: float = Field(..., ge=0.0, le=5.0, description="A rating from 0.0 to 5.0 for the task performance.")
    comments: Optional[str] = None

class StatusUpdatePayload(BasePayload):
    """Payload for providing a status update on a task."""
    task_id: str
    status: TaskStatus
    details: Optional[str] = None
    subtask_id: Optional[str] = None # Optional: for subtask-specific updates
    
class DataRequestPayload(BasePayload):
    """Payload for requesting data or analysis from another agent."""
    source_task_id: str # The task that requires this data

class DataResponsePayload(BasePayload):
    """Payload for sending data in response to a DataRequest."""
    request_id: str # The ID of the original DataRequest message
    data: Dict[str, Any]

class ConflictDetectedPayload(BasePayload):
    """Payload to signal that a conflict over a resource has been detected."""
    resource_id: str
    conflicting_agent_ids: List[str]
    details: Optional[str] = None

class NegotiationRequestPayload(BasePayload):
    """Payload to initiate or respond to a negotiation for a resource."""
    negotiation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    resource_id: str
    proposal: str # e.g., "release_lock", "wait", "share_resource"

class NegotiationResponsePayload(BasePayload):
    """Payload for an agent's response in a negotiation."""
    negotiation_id: str
    response: str # "accept", "reject", "counter-proposal"
    counter_proposal: Optional[str] = None

class ResolutionFoundPayload(BasePayload):
    """Payload to broadcast the final resolution of a negotiation."""
    negotiation_id: str
    resource_id: str
    resolution: str # Describes the agreed-upon action

class CamelMessage(BaseModel):
    header: MessageHeader
    payload: BasePayload