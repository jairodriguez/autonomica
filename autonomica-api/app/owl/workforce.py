"""Workforce orchestrator.
Provides a lightweight singleton that allocates tasks, routes messages, and drives
all agents in an asynchronous loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

from .agent import Agent, TaskAllocationSystem
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


class Workforce:
    """Central orchestration system for the multi-agent platform."""

    _instance: Optional["Workforce"] = None

    # ---------------------------------------------------------------------
    # Construction helpers (singleton pattern)
    # ---------------------------------------------------------------------
    def __new__(cls) -> "Workforce":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # Prevent re-initialisation in the singleton instance
        if getattr(self, "_initialised", False):
            return

        # Runtime state containers
        self.agents: Dict[str, Agent] = {}
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
