"""Workforce orchestrator.
Provides a lightweight singleton that allocates tasks, routes messages, and drives
all agents in an asynchronous loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent import TaskAllocationSystem
from .communication import (
    CamelMessage,
    MessageHeader,
    MessageType,
    TaskAssignmentPayload,
)
from .monitoring import TaskMonitor
from .negotiation import NegotiationManager
from .tasks import Task, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """Simple data class representing an AI agent in the workforce."""

    id: str
    name: str
    type: str
    status: str = "active"
    model: str | None = None
    system_prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class Workforce:
    """Central orchestration system for the multi-agent platform."""

    _instance: Optional["Workforce"] = None

    # ---------------------------------------------------------------------
    # Construction helpers (singleton pattern)
    # ---------------------------------------------------------------------
    def __new__(cls, *args, **kwargs) -> "Workforce":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, default_model: str) -> None:
        # Prevent re-initialisation in the singleton instance
        if getattr(self, "_initialised", False):
            return

        # Runtime state containers
        self.agents: Dict[str, Agent] = {
            "strategy": Agent(
                id="strategy-001",
                name="Strategy Specialist",
                type="Marketing Strategy",
                model=default_model,
                system_prompt=(
                    "You are a senior marketing strategist with 10+ years of "
                    "experience. Provide strategic marketing advice, campaign "
                    "planning, and business growth insights."
                ),
            ),
            "content": Agent(
                id="content-001",
                name="Content Creator",
                type="Content Marketing",
                model=default_model,
                system_prompt=(
                    "You are an expert content marketer and copywriter. Create "
                    "engaging content, blog posts, social media copy, and "
                    "marketing materials."
                ),
            ),
            "analytics": Agent(
                id="analytics-001",
                name="Analytics Expert",
                type="Data Analytics",
                model=default_model,
                system_prompt=(
                    "You are a marketing analytics expert. Analyze data, "
                    "provide insights on performance metrics, ROI, and "
                    "optimization recommendations."
                ),
            ),
        }
        self.task_queue: List[Task] = []
        self.task_allocator = TaskAllocationSystem()
        self.task_monitor = TaskMonitor()
        self.negotiation_manager = NegotiationManager()
        self._running: bool = False
        self._initialised = True
        logger.info("Workforce singleton initialised")

    # ------------------------------------------------------------------
    # Public registration helpers
    # ------------------------------------------------------------------
    def add_agent(self, agent: Agent) -> None:
        """Register an *existing* agent instance with the workforce."""
        self.agents[agent.id] = agent
        logger.info("Agent registered: %s (%s)", agent.name, agent.id)

    def add_task(self, task: Task) -> None:
        """Queue a task for allocation and execution."""
        self.task_queue.append(task)
        self.task_monitor.register_task(task)
        logger.info("Task queued: %s – %s", task.id, task.title)

    # ------------------------------------------------------------------
    # Internal operations
    # ------------------------------------------------------------------
    async def _allocate_tasks(self) -> None:
        """Allocate PENDING tasks to the best-suited available agent."""
        pending = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        for task in pending:
            agent = await self.task_allocator.allocate_task(self.agents, task)
            if agent is None:
                logger.debug("No agent currently available for task %s", task.id)
                continue

            # Send assignment message to agent
            header = MessageHeader(
                sender_id="WORKFORCE",
                recipient_id=agent.id,
                message_type=MessageType.TASK_ASSIGNMENT,
            )
            payload = TaskAssignmentPayload(task=task)
            agent.mailbox.add_incoming(CamelMessage(header=header, payload=payload))

            # Update local task state & monitoring
            task.status = TaskStatus.IN_PROGRESS
            task.assigned_to = agent.id  # field exists in Task model
            self.task_monitor.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            logger.info("Task %s assigned to agent %s", task.id, agent.name)

    async def _route_messages(self) -> None:
        """Deliver all pending outgoing messages to their recipients."""
        for agent in self.agents.values():
            for msg in agent.mailbox.get_pending_sends():
                recipient = self.agents.get(msg.header.recipient_id)
                if recipient:
                    recipient.mailbox.add_incoming(msg)
                    logger.debug(
                        "Message %s routed %s → %s",
                        msg.header.message_type.value,
                        msg.header.sender_id,
                        msg.header.recipient_id,
                    )
                else:
                    logger.warning("Unknown recipient %s for message %s", msg.header.recipient_id, msg.header.message_id)

    async def _process_inboxes(self) -> None:
        """Ask every agent to process its inbox."""
        await asyncio.gather(*(agent.process_inbox() for agent in self.agents.values()))

    # ------------------------------------------------------------------
    # Main loop control
    # ------------------------------------------------------------------
    async def run(self, tick: float = 1.0) -> None:
        """Continuously orchestrate agents and tasks until :py:meth:`stop` is called."""
        if self._running:
            return
        self._running = True
        logger.info("Workforce loop started")
        try:
            while self._running:
                await self._allocate_tasks()
                await self._route_messages()
                await self._process_inboxes()
                await asyncio.sleep(tick)
        finally:
            self._running = False
            logger.info("Workforce loop stopped")

    def stop(self) -> None:
        """Signal the running loop to exit after the current iteration."""
        self._running = False

    # ---------------------------------------------------------------------
    # Agent selection logic (iteration 1)
    # ---------------------------------------------------------------------
    def select_agent(self, messages: List["ChatMessage" | Any]) -> Agent:
        """Naively choose an agent based on keywords in the latest user message.

        `messages` should be the list of incoming chat messages (Pydantic
        ChatMessage objects or similar with `.content` attr).  This mirrors the
        previous hard-coded logic but now resides centrally.
        """
        if not messages:
            # Fallback to strategy agent if no content.
            return self.agents["strategy"]

        last_content = messages[-1].content.lower()
        if any(k in last_content for k in ("strategy", "plan", "goal", "campaign")):
            return self.agents["strategy"]
        if any(k in last_content for k in ("content", "blog", "social", "copy")):
            return self.agents["content"]
        if any(k in last_content for k in ("analytics", "data", "metrics", "performance")):
            return self.agents["analytics"]
        # Default
        return self.agents["strategy"]

    # ------------------------------------------------------------------
    # Placeholder orchestration (will expand in future iterations)
    # ------------------------------------------------------------------
    async def run_agents(self, messages: List["ChatMessage" | Any], user_id: str | None = None, session_id: str = "default") -> Dict[str, Any]:
        """Route a chat request through the workforce.

        Current minimal implementation performs three things:
        1. Chooses the most suitable *single* agent via ``select_agent``.
        2. Stores / retrieves conversation history in Redis (if configured).
        3. Returns a payload containing the agent and the compiled message
           history ready for an LLM call.

        A future iteration will
        • coordinate *multiple* agents asynchronously,
        • track token/cost usage,
        • and aggregate their responses.
        """

        import os, json  # local import to avoid unused warnings when redis not set

        agent = self.select_agent(messages)

        # ------------------------------------------------------------------
        # Conversation memory (optional Redis persistence)
        # ------------------------------------------------------------------
        history: List[Dict[str, Any]]

        redis_url = os.getenv("REDIS_URL") or os.getenv("KV_REST_API_URL")
        if redis_url and user_id:
            try:
                import redis  # type: ignore

                redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

                key = f"chat:{user_id}:{session_id}"

                # Append new messages to the conversation history (store as JSON)
                for m in messages:
                    redis_client.rpush(key, json.dumps(m if isinstance(m, dict) else m.dict()))

                # Trim to last 100 messages to keep memory bounded
                redis_client.ltrim(key, -100, -1)

                # Retrieve complete (trimmed) history for context
                history_json = redis_client.lrange(key, 0, -1)
                history = [json.loads(item) for item in history_json]

            except Exception:  # noqa: BLE001 – optional feature, fallback gracefully
                logger.exception("Redis conversation store unavailable – falling back to local history only")
                history = [m.dict() if hasattr(m, "dict") else m for m in messages]
        else:
            # No Redis configured – just use provided messages as context
            history = [m.dict() if hasattr(m, "dict") else m for m in messages]

        return {
            "agent": agent,
            "history": history,
        }


# -----------------------------------------------------------------
# Back-compat shim for legacy FastAPI boot code
# -----------------------------------------------------------------
class AutonomicaWorkforce(Workforce):  # noqa: N801 - keep legacy name
    """Thin wrapper exposing the old interface expected by app.main."""

    # FastAPI startup expects coroutine initialise/shutdown
    async def initialize(self) -> None:
        logger.info("AutonomicaWorkforce.initialize() – no-op (new Workforce auto-initialises)")

    async def shutdown(self) -> None:
        logger.info("AutonomicaWorkforce.shutdown() – stopping workforce loop")
        self.stop()

    # Legacy status fields referenced by /api/status endpoint
    version: str = "0.1.0"
    active_workflows: list = []  # placeholder

    class _Stats:  # simple struct
        total_tasks_processed: int = 0
        uptime_seconds: int = 0

    stats = _Stats()

    class _RedisMock:
        def ping(self) -> bool:  # noqa: D401
            return False

    redis_client = _RedisMock()
    vector_store = None
