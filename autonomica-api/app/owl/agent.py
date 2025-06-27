from __future__ import annotations
import uuid
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .communication import (
    CamelMessage, MessageHeader, MessageType,
    TaskAssignmentPayload, TaskDecompositionRequestPayload, TaskDecompositionResponsePayload,
    StatusUpdatePayload, FeedbackPayload,
    ConflictDetectedPayload, NegotiationRequestPayload, NegotiationResponsePayload, ResolutionFoundPayload
)
from .tasks import Task, SubTask, TaskStatus
from .negotiation import NegotiationManager

class Feedback(BaseModel):
    """Represents a piece of feedback received on a task."""
    task_id: str
    rating: float
    comments: Optional[str] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)

class AgentMemory(BaseModel):
    """Manages the agent's memory, including short-term conversation history and long-term knowledge."""
    short_term_memory: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_log: List[Feedback] = Field(default_factory=list)
    long_term_memory_id: Optional[str] = None  # Placeholder for a vector store connection

    def add_message(self, role: str, content: str):
        """Adds a message to the short-term memory."""
        self.short_term_memory.append({"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()})

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the most recent conversation history."""
        return self.short_term_memory[-limit:]

    def add_feedback(self, feedback: Feedback):
        """Adds a piece of feedback to the agent's memory."""
        self.feedback_log.append(feedback)
        # In a real system, this could trigger a fine-tuning process
        # or update a knowledge base.
        print(f"Feedback for task {feedback.task_id} (Rating: {feedback.rating}) added to memory.")

class AgentMailbox(BaseModel):
    """Handles incoming and outgoing messages for an agent."""
    incoming_messages: List[CamelMessage] = Field(default_factory=list)
    outgoing_messages: List[CamelMessage] = Field(default_factory=list)

    def add_incoming(self, message: CamelMessage):
        """Adds a message to the inbox."""
        self.incoming_messages.append(message)

    def add_outgoing(self, message: CamelMessage):
        """Adds a message to the outbox to be sent by the workforce."""
        self.outgoing_messages.append(message)

    def is_inbox_empty(self) -> bool:
        """Checks if the inbox is empty."""
        return not self.incoming_messages
        
    def get_incoming(self) -> CamelMessage:
        """Retrieves one message from the inbox."""
        return self.incoming_messages.pop(0)
        
    def get_pending_sends(self) -> List[CamelMessage]:
        """Retrieves all messages from the outbox and clears it."""
        messages = self.outgoing_messages.copy()
        self.outgoing_messages.clear()
        return messages

class ToolManager(BaseModel):
    """Manages the tools available to an agent and their execution."""
    available_tools: List[str] = Field(default_factory=list)
    tool_instances: Dict[str, Any] = Field(default_factory=dict)

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Executes a tool if it's available."""
        if tool_name not in self.available_tools:
            return f"Error: Tool '{tool_name}' is not available."
        # Placeholder for actual tool execution logic
        return f"Executed tool '{tool_name}' with args: {kwargs}"

class AgentBrain(BaseModel):
    """The core decision-making and reasoning engine for an agent."""
    model: str
    system_prompt: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0

    async def think(self, user_input: str) -> str:
        """Processes a simple text input and returns a response."""
        # This is a placeholder for a more complex reasoning loop
        print(f"Brain is thinking about: {user_input}")
        response = f"I have processed your input: '{user_input}'."
        return response

    async def decompose_task(self, task: Task) -> List[SubTask]:
        """Uses an LLM to decompose a complex task into a list of subtasks."""
        print(f"Brain is decomposing task: {task.title}")
        
        # In a real implementation, this would involve a complex prompt
        # and a call to an actual LLM service.
        prompt = f"""
        You are a task decomposition expert. Given the following complex task, break it down into a series of smaller, manageable subtasks.
        Return the subtasks as a JSON array of objects, where each object has a "title" and a "description".

        Task Title: {task.title}
        Task Description: {task.description}

        Example Response:
        [
            {{"title": "Subtask 1 Title", "description": "Description for subtask 1."}},
            {{"title": "Subtask 2 Title", "description": "Description for subtask 2."}}
        ]
        """
        
        # Simulate LLM response for now
        simulated_llm_response = json.dumps([
            {"title": f"Research for {task.title}", "description": "Gather all necessary information and context."},
            {"title": f"Draft initial version of {task.title}", "description": "Create the first draft based on research."},
            {"title": f"Review and edit for {task.title}", "description": "Proofread and refine the draft."},
            {"title": f"Finalize {task.title}", "description": "Prepare the final version for delivery."}
        ])
        
        try:
            subtask_data = json.loads(simulated_llm_response)
            subtasks = [SubTask(**data) for data in subtask_data]
            return subtasks
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing LLM response for task decomposition: {e}")
            return []

    async def _handle_negotiation_message(self, message: CamelMessage, agent_name: str) -> Optional[CamelMessage]:
        """Handles all negotiation-related messages."""
        # This is a placeholder for more complex negotiation logic.
        print(f"Brain of {agent_name} is handling negotiation message: {message.header.message_type.value}")

        if message.header.message_type == MessageType.NEGOTIATION_REQUEST:
            payload = NegotiationRequestPayload(**message.payload)
            print(f"Received negotiation request {payload.negotiation_id} for resource {payload.resource_id} with proposal: {payload.proposal}")

            # Simple strategy: always accept the proposal
            response_header = MessageHeader(
                sender_id=message.header.recipient_id,
                recipient_id=message.header.sender_id,
                message_type=MessageType.NEGOTIATION_RESPONSE
            )
            response_payload = NegotiationResponsePayload(
                negotiation_id=payload.negotiation_id,
                response="accept"
            )
            return CamelMessage(header=response_header, payload=response_payload)

        # Other negotiation messages can be handled here.
        return None

    async def think_on_message(self, message: CamelMessage, agent_name: str) -> Optional[CamelMessage]:
        """Processes an incoming CamelMessage and decides on a response or action."""
        print(f"Brain of {agent_name} is thinking about message: {message.header.message_type.value}")
        payload_data = message.payload

        if message.header.message_type == MessageType.TASK_ASSIGNMENT:
            task_payload = TaskAssignmentPayload(**payload_data)
            response_header = MessageHeader(
                sender_id=message.header.recipient_id,
                recipient_id=message.header.sender_id,
                message_type=MessageType.STATUS_UPDATE
            )
            response_payload = StatusUpdatePayload(
                task_id=task_payload.task.id,
                status=TaskStatus.IN_PROGRESS, # Acknowledged and starting
                details=f"Task '{task_payload.task.title}' acknowledged and started by {agent_name}."
            )
            return CamelMessage(header=response_header, payload=response_payload)

        elif message.header.message_type == MessageType.TASK_DECOMPOSITION_REQUEST:
            decomp_payload = TaskDecompositionRequestPayload(**payload_data)
            subtasks = await self.decompose_task(decomp_payload.task)
            
            response_header = MessageHeader(
                sender_id=message.header.recipient_id,
                recipient_id=message.header.sender_id,
                message_type=MessageType.TASK_DECOMPOSITION_RESPONSE
            )
            response_payload = TaskDecompositionResponsePayload(
                original_task_id=decomp_payload.task.id,
                subtasks=subtasks
            )
            return CamelMessage(header=response_header, payload=response_payload)
            
        elif message.header.message_type == MessageType.FEEDBACK:
            # The brain itself doesn't need to respond to feedback,
            # but it could trigger an internal reflection process here.
            feedback_payload = FeedbackPayload(**payload_data)
            print(f"Brain of {agent_name} noted feedback for task {feedback_payload.task_id}.")
            # The feedback will be formally logged by the Agent class.
            return None
        
        elif message.header.message_type in [
            MessageType.CONFLICT_DETECTED,
            MessageType.NEGOTIATION_REQUEST,
            MessageType.NEGOTIATION_RESPONSE,
            MessageType.RESOLUTION_FOUND
        ]:
            return await self._handle_negotiation_message(message, agent_name)
            
        return None

class Agent(BaseModel):
    """Represents a complete, modular agent in the OWL system."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    agent_type: str = Field(alias="type")
    brain: AgentBrain
    memory: AgentMemory = Field(default_factory=AgentMemory)
    tool_manager: ToolManager = Field(default_factory=ToolManager)
    mailbox: AgentMailbox = Field(default_factory=AgentMailbox)
    status: str = "idle"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    tasks_completed: int = 0

    class Config:
        populate_by_name = True
    
    def get_total_cost(self) -> float:
        return self.brain.total_cost

    def get_tasks_completed(self) -> int:
        return self.tasks_completed
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Returns a summary of the agent's operational costs."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type,
            "model": self.brain.model,
            "cost": round(self.get_total_cost(), 4),
            "input_tokens": self.brain.total_input_tokens,
            "output_tokens": self.brain.total_output_tokens,
            "tasks_completed": self.get_tasks_completed()
        }

    async def process_input(self, user_input: str) -> str:
        """High-level method to process external user input."""
        self.memory.add_message(role="user", content=user_input)
        response = await self.brain.think(user_input)
        self.memory.add_message(role="assistant", content=response)
        return response

    def send_message(self, message: CamelMessage):
        """Adds a message to the agent's outbox for the workforce to route."""
        self.mailbox.add_outgoing(message)
        print(f"Agent {self.name} queued message to {message.header.recipient_id}")

    def initiate_conflict_resolution(self, resource_id: str, conflicting_agent_ids: List[str]):
        """Starts a conflict resolution process by notifying involved agents."""
        print(f"Agent {self.name} is initiating conflict resolution for resource: {resource_id}")
        
        if not conflicting_agent_ids:
            return

        negotiation_manager = NegotiationManager()
        negotiation_state = negotiation_manager.start_negotiation(
            resource_id=resource_id,
            initiating_agent_id=self.id,
            involved_agent_ids=conflicting_agent_ids
        )
        
        # Send a negotiation request to the first conflicting agent
        target_agent_id = conflicting_agent_ids[0]
        
        header = MessageHeader(
            sender_id=self.id,
            recipient_id=target_agent_id,
            message_type=MessageType.NEGOTIATION_REQUEST
        )
        payload = NegotiationRequestPayload(
            negotiation_id=negotiation_state.negotiation_id,
            resource_id=resource_id,
            proposal=f"Agent {self.name} requests control of resource {resource_id}. Please stand down."
        )
        
        message = CamelMessage(header=header, payload=payload)
        self.send_message(message)

    async def process_inbox(self):
        """Processes all messages in the inbox."""
        while not self.mailbox.is_inbox_empty():
            message = self.mailbox.get_incoming()
            print(f"Agent {self.name} is processing message from {message.header.sender_id}")
            
            # If it's feedback, log it directly to memory
            if message.header.message_type == MessageType.FEEDBACK:
                feedback = Feedback(**message.payload)
                self.memory.add_feedback(feedback)
            
            # Let the brain decide what to do with the message
            response_message = await self.brain.think_on_message(message, self.name)
            
            if response_message:
                self.send_message(response_message)

# --- TEMPORARY WORKFORCE LOGIC - TO BE MOVED TO workforce.py ---

class TaskAllocationSystem:
    """Holds the logic for the task allocation system."""

    def _score_agent_for_task(self, agent: Agent, task: Task) -> float:
        """Calculates a suitability score for an agent to handle a specific task."""
        score = 0.0

        # 1. Capability Match
        task_keywords = set(task.title.lower().split() + task.description.lower().split())
        agent_capabilities = set(agent.brain.system_prompt.lower().split())
        capability_match = len(task_keywords.intersection(agent_capabilities))
        score += capability_match * 1.5

        # 2. Tool Match
        if task.required_tools:
            required = set(task.required_tools)
            available = set(agent.tool_manager.available_tools)
            if required.issubset(available):
                score += 10.0
            score += len(required.intersection(available)) * 2.0

        # 3. Workload Penalty
        if agent.status == "busy":
            score -= 5.0
            
        # 4. Model Quality Bonus
        if "gpt-4" in agent.brain.model.lower():
            score += 3.0
        elif "claude-3" in agent.brain.model.lower():
            score += 3.5

        return score

    async def allocate_task(self, agents: Dict[str, Agent], task: Task) -> Optional[Agent]:
        """Finds the best agent for a task and returns it."""
        if not agents:
            print("Warning: No agents available to allocate task.")
            return None

        best_agent = None
        highest_score = -1.0

        for agent in agents.values():
            if agent.status != "offline":
                score = self._score_agent_for_task(agent, task)
                if score > highest_score:
                    highest_score = score
                    best_agent = agent
        
        if best_agent:
            print(f"Best agent for task '{task.title}' is '{best_agent.name}' with score {highest_score:.2f}")
        else:
            print(f"Warning: Could not find a suitable agent for task '{task.title}'")

        return best_agent 