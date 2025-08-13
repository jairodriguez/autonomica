from __future__ import annotations
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from .communication import CamelMessage

logger = logging.getLogger(__name__)

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
    """
    Advanced negotiation manager for resource conflict resolution.
    
    Handles complex multi-agent negotiations with intelligent resolution strategies,
    priority-based allocation, and automated conflict detection.
    """
    _instance = None
    _negotiations: Dict[str, NegotiationState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NegotiationManager, cls).__new__(cls)
            cls._negotiations = {}
        return cls._instance

    def start_negotiation(self, resource_id: str, initiating_agent_id: str, involved_agent_ids: List[str]) -> NegotiationState:
        """Starts a new negotiation process with intelligent priority assessment."""
        negotiation_id = str(uuid.uuid4())
        state = NegotiationState(
            negotiation_id=negotiation_id,
            resource_id=resource_id,
            initiating_agent_id=initiating_agent_id,
            involved_agent_ids=involved_agent_ids
        )
        self._negotiations[negotiation_id] = state
        logger.info(f"Started negotiation {negotiation_id} for resource {resource_id}")
        
        # Attempt automated resolution first
        auto_resolution = self._attempt_automatic_resolution(state)
        if auto_resolution:
            self.resolve_negotiation(negotiation_id, auto_resolution)
            logger.info(f"Negotiation {negotiation_id} auto-resolved: {auto_resolution}")
        
        return state

    def _attempt_automatic_resolution(self, state: NegotiationState) -> Optional[str]:
        """Attempt to automatically resolve conflicts using predefined strategies."""
        resource_id = state.resource_id
        involved_agents = state.involved_agent_ids
        
        # Strategy 1: Resource sharing for compatible tasks
        if len(involved_agents) <= 2 and "agent_" in resource_id:
            return f"time_sharing:{','.join(involved_agents)}"
        
        # Strategy 2: Priority-based allocation for token budget
        if "token_budget" in resource_id:
            # Give priority to the initiating agent (first come, first served)
            return f"priority_allocation:{state.initiating_agent_id}"
        
        # Strategy 3: Load balancing for computational resources
        if "memory_pool" in resource_id or "computational" in resource_id:
            return f"load_balance:{','.join(involved_agents)}"
        
        return None

    def add_message_to_history(self, negotiation_id: str, message: CamelMessage):
        """Adds a message to the negotiation's history and checks for resolution."""
        if negotiation_id in self._negotiations:
            self._negotiations[negotiation_id].history.append(message)
            self._negotiations[negotiation_id].updated_at = datetime.utcnow()
            
            # Check if this message contains a resolution
            self._check_for_resolution(negotiation_id)
        else:
            logger.warning(f"Attempted to add message to unknown negotiation {negotiation_id}")

    def _check_for_resolution(self, negotiation_id: str):
        """Analyze negotiation history to detect if resolution has been reached."""
        negotiation = self._negotiations.get(negotiation_id)
        if not negotiation or negotiation.status != "open":
            return
        
        recent_messages = negotiation.history[-3:]  # Check last 3 messages
        
        # Look for acceptance patterns
        for message in recent_messages:
            payload = message.payload
            if hasattr(payload, 'response') and payload.response == "accept":
                # Found acceptance, resolve the negotiation
                resolution = f"negotiated_agreement:{message.header.sender_id}_accepts"
                self.resolve_negotiation(negotiation_id, resolution)
                return
        
        # Check for timeout (negotiations older than 5 minutes)
        if (datetime.utcnow() - negotiation.created_at).total_seconds() > 300:
            logger.warning(f"Negotiation {negotiation_id} timed out, applying default resolution")
            default_resolution = f"timeout_resolution:{negotiation.initiating_agent_id}"
            self.resolve_negotiation(negotiation_id, default_resolution)

    def get_negotiation(self, negotiation_id: str) -> Optional[NegotiationState]:
        """Retrieves the current state of a negotiation."""
        return self._negotiations.get(negotiation_id)

    def resolve_negotiation(self, negotiation_id: str, resolution: str):
        """Marks a negotiation as resolved with detailed resolution logging."""
        if negotiation_id in self._negotiations:
            negotiation = self._negotiations[negotiation_id]
            negotiation.status = "resolved"
            negotiation.resolution = resolution
            negotiation.updated_at = datetime.utcnow()
            
            logger.info(f"Negotiation {negotiation_id} resolved: {resolution}")
            logger.info(f"Resource {negotiation.resource_id} allocated according to resolution")
            
            # Cleanup old negotiations to prevent memory leaks
            self._cleanup_old_negotiations()

    def fail_negotiation(self, negotiation_id: str, reason: str = "unknown"):
        """Marks a negotiation as failed with reason logging."""
        if negotiation_id in self._negotiations:
            negotiation = self._negotiations[negotiation_id]
            negotiation.status = "failed"
            negotiation.updated_at = datetime.utcnow()
            
            logger.error(f"Negotiation {negotiation_id} failed: {reason}")
            logger.error(f"Resource {negotiation.resource_id} remains in conflict state")

    def _cleanup_old_negotiations(self):
        """Remove negotiations older than 1 hour to prevent memory buildup."""
        current_time = datetime.utcnow()
        old_negotiations = [
            neg_id for neg_id, negotiation in self._negotiations.items()
            if (current_time - negotiation.updated_at).total_seconds() > 3600
            and negotiation.status in ["resolved", "failed"]
        ]
        
        for neg_id in old_negotiations:
            del self._negotiations[neg_id]
            logger.debug(f"Cleaned up old negotiation {neg_id}")

    def get_active_negotiations(self) -> List[NegotiationState]:
        """Get all currently active negotiations."""
        return [
            negotiation for negotiation in self._negotiations.values()
            if negotiation.status == "open"
        ]

    def get_resource_conflicts(self, resource_id: str) -> List[NegotiationState]:
        """Get all negotiations related to a specific resource."""
        return [
            negotiation for negotiation in self._negotiations.values()
            if negotiation.resource_id == resource_id and negotiation.status == "open"
        ]

    def force_resolve_all_conflicts(self, resource_id: str, winning_agent_id: str):
        """Force resolution of all conflicts for a resource by declaring a winner."""
        conflicts = self.get_resource_conflicts(resource_id)
        
        for conflict in conflicts:
            resolution = f"force_resolution:{winning_agent_id}_wins"
            self.resolve_negotiation(conflict.negotiation_id, resolution)
            
        logger.info(f"Force resolved {len(conflicts)} conflicts for {resource_id}, winner: {winning_agent_id}")

    def get_negotiation_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics about the negotiation system."""
        total_negotiations = len(self._negotiations)
        active_negotiations = len(self.get_active_negotiations())
        resolved_negotiations = len([n for n in self._negotiations.values() if n.status == "resolved"])
        failed_negotiations = len([n for n in self._negotiations.values() if n.status == "failed"])
        
        return {
            "total_negotiations": total_negotiations,
            "active_negotiations": active_negotiations,
            "resolved_negotiations": resolved_negotiations,
            "failed_negotiations": failed_negotiations,
            "success_rate": resolved_negotiations / total_negotiations if total_negotiations > 0 else 0,
            "conflict_resources": list(set([n.resource_id for n in self.get_active_negotiations()]))
        } 