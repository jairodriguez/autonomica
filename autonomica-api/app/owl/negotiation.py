from __future__ import annotations
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from .communication import CamelMessage

class NegotiationState(BaseModel):
    """Tracks the state of a single negotiation process."""
    negotiation_id: str
    resource_id: str
    initiating_agent_id: str
    involved_agent_ids: List[str]
    history: List[CamelMessage] = []
    status: str = "open"  # "open", "resolved", "failed"
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NegotiationManager:
    """A singleton class to manage all conflict negotiations."""
    _instance = None
    _negotiations: Dict[str, NegotiationState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NegotiationManager, cls).__new__(cls)
            cls._negotiations = {}
        return cls._instance

    def start_negotiation(self, resource_id: str, initiating_agent_id: str, involved_agent_ids: List[str]) -> NegotiationState:
        """Starts a new negotiation process."""
        negotiation_id = str(uuid.uuid4())
        state = NegotiationState(
            negotiation_id=negotiation_id,
            resource_id=resource_id,
            initiating_agent_id=initiating_agent_id,
            involved_agent_ids=involved_agent_ids
        )
        self._negotiations[negotiation_id] = state
        return state

    def add_message_to_history(self, negotiation_id: str, message: CamelMessage):
        """Adds a message to the negotiation's history."""
        if negotiation_id in self._negotiations:
            self._negotiations[negotiation_id].history.append(message)
            self._negotiations[negotiation_id].updated_at = datetime.utcnow()
        else:
            # Handle error: negotiation not found
            pass

    def get_negotiation(self, negotiation_id: str) -> Optional[NegotiationState]:
        """Retrieves the current state of a negotiation."""
        return self._negotiations.get(negotiation_id)

    def resolve_negotiation(self, negotiation_id: str, resolution: str):
        """Marks a negotiation as resolved."""
        if negotiation_id in self._negotiations:
            self._negotiations[negotiation_id].status = "resolved"
            self._negotiations[negotiation_id].resolution = resolution
            self._negotiations[negotiation_id].updated_at = datetime.utcnow()

    def fail_negotiation(self, negotiation_id: str):
        """Marks a negotiation as failed."""
        if negotiation_id in self._negotiations:
            self._negotiations[negotiation_id].status = "failed"
            self._negotiations[negotiation_id].updated_at = datetime.utcnow() 