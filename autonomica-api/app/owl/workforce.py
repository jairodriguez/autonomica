"""Workforce orchestrator.
Provides a lightweight singleton that allocates tasks, routes messages, and drives
all agents in an asynchronous loop. Now integrated with advanced orchestration capabilities.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent import TaskAllocationSystem, Agent as FullAgent
from .communication import (
    CamelMessage,
    MessageHeader,
    MessageType,
    TaskAssignmentPayload,
)
from .monitoring import TaskMonitor
from .negotiation import NegotiationManager
from .tasks import Task, TaskStatus
from .orchestration import WorkforceOrchestrator, OrchestrationMode, WorkflowExecution
from ..ai.ai_manager import ai_manager

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

    def __init__(self, default_model: str, redis_url: Optional[str] = None):
        self.orchestrator = WorkforceOrchestrator(default_model)
        self.default_model = default_model
        self.redis_url = redis_url
        self.agents: Dict[str, Agent] = {}
        self._create_simple_agents()
        self._create_full_agents_from_simple()
        
        self.task_queue: List[Task] = []
        self.task_allocator = TaskAllocationSystem()
        self.task_monitor = TaskMonitor()
        self.negotiation_manager = NegotiationManager()
        self._running: bool = False
        logger.info("Workforce initialized with advanced orchestration capabilities")

    def _create_simple_agents(self):
        """Creates the default set of simple agents."""
        simple_agents = {
            "strategy": Agent(
                id="strategy-001",
                name="Strategy Specialist",
                type="Marketing Strategy",
                model=self.default_model,
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
                model=self.default_model,
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
                model=self.default_model,
                system_prompt=(
                    "You are a marketing analytics expert. Analyze data, "
                    "provide insights on performance metrics, ROI, and "
                    "optimization recommendations."
                ),
            ),
        }
        self.agents = simple_agents

    def _create_full_agents_from_simple(self) -> None:
        """Create full agent instances for orchestration from simple agent definitions."""
        from .agent import Agent as FullAgent, AgentBrain, ToolManager
        
        for agent_id, simple_agent in self.agents.items():
            brain = AgentBrain(
                model=simple_agent.model or self.default_model,
                system_prompt=simple_agent.system_prompt
            )
            
            tool_manager = ToolManager()
            if "strategy" in simple_agent.type.lower():
                tool_manager.available_tools = ["market_research", "competitor_analysis", "campaign_planner"]
            elif "content" in simple_agent.type.lower():
                tool_manager.available_tools = ["content_writer", "social_media_scheduler", "seo_optimizer"]
            elif "analytics" in simple_agent.type.lower():
                tool_manager.available_tools = ["data_analyzer", "performance_tracker", "roi_calculator"]
            
            full_agent = FullAgent(
                id=simple_agent.id,
                name=simple_agent.name,
                agent_type=simple_agent.type,
                brain=brain,
                tool_manager=tool_manager
            )
            
            self.orchestrator.register_agent(full_agent)

    async def initialize(self):
        """Initializes asynchronous resources."""
        # Initialize the AI manager first
        await ai_manager.initialize()
        logger.info("AI Manager initialized with multi-model support")
        
        # Run orchestration loop in the background to avoid blocking app startup
        asyncio.create_task(self.orchestrator.start_orchestration())
        logger.info("Workforce initialized and orchestrator started (background loop).")

    async def shutdown(self):
        """Shuts down asynchronous resources."""
        self.stop()
        logger.info("Workforce shutdown.")

    def add_agent(self, agent: Agent) -> None:
        """Register an *existing* agent instance with the workforce."""
        self.agents[agent.id] = agent
        logger.info("Agent registered: %s (%s)", agent.name, agent.id)

    def add_task(self, task: Task) -> None:
        """Queue a task for allocation and execution."""
        self.task_queue.append(task)
        self.task_monitor.register_task(task)
        logger.info("Task queued: %s – %s", task.id, task.title)

    async def _allocate_tasks(self) -> None:
        """Allocate PENDING tasks to the best-suited available agent."""
        pending = [t for t in self.task_queue if t.status == TaskStatus.PENDING]
        for task in pending:
            agent = await self.task_allocator.allocate_task(self.agents, task)
            if agent is None:
                logger.debug("No agent currently available for task %s", task.id)
                continue

            header = MessageHeader(
                sender_id="WORKFORCE",
                recipient_id=agent.id,
                message_type=MessageType.TASK_ASSIGNMENT,
            )
            payload = TaskAssignmentPayload(task=task)
            # This assumes agent has a mailbox attribute. The Agent class here doesn't.
            # This points to a discrepancy between Agent and FullAgent that needs resolving.
            # For now, we assume we're dealing with FullAgent instances that have mailboxes.
            if hasattr(agent, 'mailbox'):
                agent.mailbox.add_incoming(CamelMessage(header=header, payload=payload))

            task.status = TaskStatus.IN_PROGRESS
            task.assigned_to = agent.id
            self.task_monitor.update_task_status(task.id, TaskStatus.IN_PROGRESS)
            logger.info("Task %s assigned to agent %s", task.id, agent.name)

    async def run(self, tick: float = 1.0) -> None:
        """Continuously orchestrate agents and tasks until stop is called."""
        if self._running:
            return
        self._running = True
        logger.info("Workforce loop started")
        try:
            while self._running:
                await self._allocate_tasks()
                # Assuming _route_messages and _process_inboxes are part of a deeper agent model
                # not present in this simplified view.
                await asyncio.sleep(tick)
        finally:
            self._running = False
            logger.info("Workforce loop stopped")

    def stop(self) -> None:
        """Signal the running loop to exit after the current iteration."""
        self._running = False

    def select_agents(self, messages: List[Dict[str, Any]]) -> List[Agent]:
        """Select appropriate agents based on message content."""
        if not messages:
            return []
        
        latest_message = messages[-1].get('content', '').lower()
        selected = []
        
        # Simple keyword-based selection
        if any(keyword in latest_message for keyword in ['seo', 'research', 'keywords', 'competitor', 'analysis']):
            selected.append(self.agents.get('strategy'))
        if any(keyword in latest_message for keyword in ['content', 'blog', 'write', 'copy', 'social media']):
            selected.append(self.agents.get('content'))
        if any(keyword in latest_message for keyword in ['analytics', 'data', 'metrics', 'performance', 'roi']):
            selected.append(self.agents.get('analytics'))
        
        # Default fallback - select strategy agent
        if not selected:
            selected.append(self.agents.get('strategy'))
        
        return [agent for agent in selected if agent is not None]

    async def run_agents(self, messages: List[Dict[str, Any]], user_id: str | None = None, session_id: str = "default") -> Dict[str, Any]:
        if not messages:
            raise ValueError("Cannot run agents with an empty message list.")

        latest_message = messages[-1]['content']
        task = Task(
            title="Process User Chat Request",
            description=latest_message,
            required_tools=self._extract_required_tools(latest_message)
        )

        workflow = self.orchestrator.create_workflow(
            name=f"Chat Request - {session_id}",
            tasks=[task],
            mode=OrchestrationMode.ADAPTIVE
        )
        
        workflow_result = await self.orchestrator.execute_workflow(workflow.id)

        primary_agent_id = next(iter(workflow.participating_agents), None)
        if primary_agent_id:
            agent = self.orchestrator.agents.get(primary_agent_id)
        else:
            agent = self.orchestrator.get_agent_by_capabilities([])

        history = await self._manage_conversation_history(messages, user_id, session_id)

        # Produce a concrete response using the selected agent's brain as a fallback
        final_response = "Default response if none generated."
        try:
            latest_message = messages[-1]['content']
            if agent and hasattr(agent, 'brain'):
                final_response = await agent.brain.think(latest_message)
        except Exception as _:
            pass

        return {
            "agent": agent,
            "history": history,
            "response": final_response,
            "workflow_result": workflow_result,
            "metadata": {
                "model_used": getattr(agent, 'model', self.default_model) if agent else self.default_model,
                "timestamp": asyncio.get_event_loop().time(),
                "session_id": session_id,
                "user_id": user_id,
            }
        }
    
    async def generate_ai_response(
        self,
        prompt: str,
        task_type: str = "general",
        agent_context: Optional[str] = None,
        prefer_local: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate AI response using the multi-model AI manager."""
        try:
            # Enhance prompt with agent context if provided
            enhanced_prompt = prompt
            if agent_context:
                enhanced_prompt = f"Context: {agent_context}\n\nUser Query: {prompt}"
            
            # Use AI manager for intelligent model selection and generation
            response = await ai_manager.generate_response(
                prompt=enhanced_prompt,
                task_type=task_type,
                prefer_local=prefer_local,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.get("content", ""),
                "model_used": response.get("model", "unknown"),
                "usage": response.get("usage", {}),
                "metadata": response.get("metadata", {})
            }
        
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {
                "content": "I apologize, but I'm having trouble generating a response right now. Please try again.",
                "model_used": "fallback",
                "error": str(e)
            }
    
    async def generate_streaming_response(
        self,
        prompt: str,
        task_type: str = "general",
        agent_context: Optional[str] = None,
        prefer_local: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """Generate streaming AI response using the multi-model AI manager."""
        try:
            # Enhance prompt with agent context if provided
            enhanced_prompt = prompt
            if agent_context:
                enhanced_prompt = f"Context: {agent_context}\n\nUser Query: {prompt}"
            
            # Use AI manager for streaming generation
            async for chunk in ai_manager.generate_stream(
                prompt=enhanced_prompt,
                task_type=task_type,
                prefer_local=prefer_local,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                yield chunk
        
        except Exception as e:
            logger.error(f"Streaming AI response generation failed: {e}")
            yield {
                "content": "I apologize, but I'm having trouble generating a response right now.",
                "done": True,
                "error": str(e)
            }
    
    async def get_ai_status(self) -> Dict[str, Any]:
        """Get status of all AI models and providers."""
        try:
            model_status = await ai_manager.get_model_status()
            available_models = await ai_manager.get_available_models()
            
            return {
                "available_models": available_models,
                "model_status": model_status,
                "initialized": ai_manager._initialized
            }
        except Exception as e:
            logger.error(f"Failed to get AI status: {e}")
            return {
                "error": str(e),
                "available_models": {},
                "model_status": {},
                "initialized": False
            }

    def _extract_required_tools(self, content: str) -> List[str]:
        """Extract required tools from message content using simple keywords."""
        content = content.lower()
        tools = []
        if any(k in content for k in ["research", "analyze", "plan"]):
            tools.append("market_research")
        if any(k in content for k in ["write", "create", "post"]):
            tools.append("content_writer")
        if any(k in content for k in ["data", "metrics", "performance"]):
            tools.append("data_analyzer")
        return tools

    async def _manage_conversation_history(self, messages: List[Dict[str, Any]], user_id: str | None, session_id: str) -> List[Dict[str, Any]]:
        """Store and retrieve conversation history from Redis if available."""
        import json
        
        history: List[Dict[str, Any]]

        if self.redis_url and user_id:
            try:
                import redis.asyncio as redis
                redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
                key = f"chat:{user_id}:{session_id}"

                # Use a pipeline for efficiency
                pipe = redis_client.pipeline()
                for m in messages:
                    pipe.rpush(key, json.dumps(m))
                pipe.ltrim(key, -100, -1)
                await pipe.execute()

                history_json = await redis_client.lrange(key, 0, -1)
                history = [json.loads(item) for item in history_json]
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}), falling back to local history.")
                history = messages
        else:
            history = messages
            
        return history
