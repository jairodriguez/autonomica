"""
System-wide Orchestration Logic for OWL/CAMEL Multi-Agent System

This module implements the core orchestration layer that coordinates all agents,
tasks, resources, and workflows in the Autonomica platform. It provides:
- Advanced task scheduling and dependency management
- Multi-agent coordination and communication
- Resource allocation and conflict resolution
- Token usage monitoring and cost management
- Error recovery and system resilience
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

from .agent import Agent, TaskAllocationSystem
from .tasks import Task, TaskStatus, SubTask
from .communication import (
    CamelMessage, MessageHeader, MessageType,
    TaskAssignmentPayload, StatusUpdatePayload, ConflictDetectedPayload
)
from .monitoring import TaskMonitor
from .negotiation import NegotiationManager

logger = logging.getLogger(__name__)


class OrchestrationMode(str, Enum):
    """Defines different orchestration strategies."""
    SEQUENTIAL = "sequential"  # Execute tasks one by one
    PARALLEL = "parallel"     # Execute independent tasks simultaneously
    ADAPTIVE = "adaptive"     # Dynamically choose based on resources and complexity


class ResourceType(str, Enum):
    """Types of resources that can be managed."""
    AGENT = "agent"
    COMPUTATIONAL = "computational"
    MEMORY = "memory"
    TOKEN_BUDGET = "token_budget"
    EXTERNAL_API = "external_api"


@dataclass
class SystemResource:
    """Represents a system resource that can be allocated to agents."""
    id: str
    type: ResourceType
    capacity: int
    allocated: int = 0
    reserved_by: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> int:
        return self.capacity - self.allocated

    @property
    def utilization_rate(self) -> float:
        return self.allocated / self.capacity if self.capacity > 0 else 0.0


@dataclass
class WorkflowExecution:
    """Tracks the execution of a multi-agent workflow."""
    id: str = field(default_factory=lambda: f"workflow_{uuid.uuid4()}")
    name: str = ""
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    mode: OrchestrationMode = OrchestrationMode.ADAPTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_cost: float = 0.0
    participating_agents: Set[str] = field(default_factory=set)


class WorkforceOrchestrator:
    """
    Advanced orchestration system that coordinates the entire multi-agent workforce.
    
    This class serves as the central nervous system of the OWL platform, managing:
    - Task scheduling and dependency resolution
    - Agent coordination and load balancing
    - Resource allocation and conflict resolution
    - System monitoring and performance optimization
    - Error recovery and fault tolerance
    """

    def __init__(self, default_model: str = "gpt-4"):
        # Core components
        self.agents: Dict[str, Agent] = {}
        self.task_allocator = TaskAllocationSystem()
        self.task_monitor = TaskMonitor()
        self.negotiation_manager = NegotiationManager()
        
        # Orchestration state
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.task_dependency_graph: Dict[str, Set[str]] = {}
        self.agent_workloads: Dict[str, List[str]] = {}  # agent_id -> task_ids
        
        # Resource management
        self.system_resources: Dict[str, SystemResource] = {
            "token_budget": SystemResource(
                id="token_budget",
                type=ResourceType.TOKEN_BUDGET,
                capacity=1000000,  # 1M tokens default budget
                metadata={"cost_per_token": 0.00002}
            ),
            "memory_pool": SystemResource(
                id="memory_pool", 
                type=ResourceType.MEMORY,
                capacity=8192,  # 8GB memory pool
                metadata={"unit": "MB"}
            )
        }
        
        # Performance metrics
        self.total_tasks_processed: int = 0
        self.total_cost_incurred: float = 0.0
        self.average_task_completion_time: float = 0.0
        self.system_efficiency_score: float = 0.0
        
        # Configuration
        self.default_model = default_model
        self.max_concurrent_tasks = 10
        self.token_budget_threshold = 0.8  # Alert when 80% of budget used
        self.orchestration_tick_interval = 2.0  # seconds
        
        logger.info("WorkforceOrchestrator initialized with advanced coordination capabilities")

    # ================================
    # Agent Management
    # ================================

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestration system."""
        self.agents[agent.id] = agent
        self.agent_workloads[agent.id] = []
        
        # Register agent as a computational resource
        self.system_resources[f"agent_{agent.id}"] = SystemResource(
            id=f"agent_{agent.id}",
            type=ResourceType.AGENT,
            capacity=1,  # One agent can handle one primary task at a time
            metadata={
                "agent_type": agent.agent_type,
                "model": agent.brain.model,
                "capabilities": agent.tool_manager.available_tools
            }
        )
        
        logger.info(f"Agent {agent.name} ({agent.id}) registered with orchestrator")

    def get_agent_by_capabilities(self, required_capabilities: List[str]) -> Optional[Agent]:
        """Find the best agent based on required capabilities."""
        best_agent = None
        best_score = -1

        for agent in self.agents.values():
            if agent.status == "offline":
                continue
                
            # Calculate capability match score
            agent_tools = set(agent.tool_manager.available_tools)
            required_tools = set(required_capabilities)
            match_score = len(agent_tools.intersection(required_tools))
            
            # Add workload penalty
            workload_penalty = len(self.agent_workloads.get(agent.id, [])) * 0.5
            final_score = match_score - workload_penalty
            
            if final_score > best_score:
                best_score = final_score
                best_agent = agent

        return best_agent

    # ================================
    # Task Orchestration
    # ================================

    def create_workflow(self, name: str, tasks: List[Task], 
                       mode: OrchestrationMode = OrchestrationMode.ADAPTIVE) -> WorkflowExecution:
        """Create a new multi-task workflow with orchestration strategy."""
        workflow = WorkflowExecution(name=name, tasks=tasks, mode=mode)
        self.active_workflows[workflow.id] = workflow
        
        # Build dependency graph for this workflow
        for task in tasks:
            self.task_dependency_graph[task.id] = set(task.dependencies)
            self.task_monitor.register_task(task)
        
        logger.info(f"Workflow '{name}' created with {len(tasks)} tasks in {mode.value} mode")
        return workflow

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a complete workflow with advanced orchestration."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow.status = TaskStatus.IN_PROGRESS
        workflow.started_at = datetime.utcnow()
        
        logger.info(f"Starting workflow execution: {workflow.name}")
        
        try:
            if workflow.mode == OrchestrationMode.SEQUENTIAL:
                result = await self._execute_sequential_workflow(workflow)
            elif workflow.mode == OrchestrationMode.PARALLEL:
                result = await self._execute_parallel_workflow(workflow)
            else:  # ADAPTIVE
                result = await self._execute_adaptive_workflow(workflow)
            
            workflow.status = TaskStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            self.total_tasks_processed += len(workflow.tasks)
            
            logger.info(f"Workflow '{workflow.name}' completed successfully")
            return result
            
        except Exception as e:
            workflow.status = TaskStatus.FAILED
            logger.error(f"Workflow '{workflow.name}' failed: {str(e)}")
            await self._handle_workflow_failure(workflow, e)
            raise

    async def _execute_sequential_workflow(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute tasks one after another, respecting dependencies."""
        results = {}
        
        # Sort tasks by dependencies (topological sort)
        ordered_tasks = self._topological_sort(workflow.tasks)
        
        for task in ordered_tasks:
            # Check if all dependencies are satisfied
            if not self._are_dependencies_satisfied(task):
                continue
                
            # Allocate best agent for this task
            agent = await self._allocate_agent_for_task(task)
            if not agent:
                logger.warning(f"No suitable agent found for task {task.title}")
                continue
            
            # Execute task
            result = await self._execute_single_task(task, agent, workflow)
            results[task.id] = result
            
            # Update workflow progress
            workflow.participating_agents.add(agent.id)
        
        return {"workflow_id": workflow.id, "results": results}

    async def _execute_parallel_workflow(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute independent tasks in parallel for maximum efficiency."""
        # Group tasks by dependency level
        task_levels = self._group_tasks_by_dependency_level(workflow.tasks)
        results = {}
        
        for level, tasks in task_levels.items():
            logger.info(f"Executing dependency level {level} with {len(tasks)} tasks")
            
            # Execute all tasks at this level in parallel
            level_tasks = []
            for task in tasks:
                agent = await self._allocate_agent_for_task(task)
                if agent:
                    level_tasks.append(self._execute_single_task(task, agent, workflow))
                    workflow.participating_agents.add(agent.id)
            
            # Wait for all tasks at this level to complete
            if level_tasks:
                level_results = await asyncio.gather(*level_tasks, return_exceptions=True)
                for i, result in enumerate(level_results):
                    if not isinstance(result, Exception):
                        results[tasks[i].id] = result
        
        return {"workflow_id": workflow.id, "results": results}

    async def _execute_adaptive_workflow(self, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Intelligently choose between sequential and parallel based on system state."""
        # Analyze system capacity and task complexity
        available_agents = len([a for a in self.agents.values() if a.status != "offline"])
        independent_tasks = len([t for t in workflow.tasks if not t.dependencies])
        
        # Decision logic for adaptive execution
        if available_agents >= len(workflow.tasks) // 2 and independent_tasks > 1:
            logger.info("Adaptive mode: Choosing parallel execution")
            return await self._execute_parallel_workflow(workflow)
        else:
            logger.info("Adaptive mode: Choosing sequential execution")
            return await self._execute_sequential_workflow(workflow)

    async def _execute_single_task(self, task: Task, agent: Agent, workflow: WorkflowExecution) -> Dict[str, Any]:
        """Execute a single task with comprehensive monitoring and error handling."""
        start_time = datetime.utcnow()
        
        try:
            # Reserve resources
            await self._reserve_resources_for_task(task, agent)
            
            # Send task assignment
            header = MessageHeader(
                sender_id="ORCHESTRATOR",
                recipient_id=agent.id,
                message_type=MessageType.TASK_ASSIGNMENT
            )
            payload = TaskAssignmentPayload(task=task)
            message = CamelMessage(header=header, payload=payload)
            
            agent.mailbox.add_incoming(message)
            
            # Monitor task execution
            task.status = TaskStatus.IN_PROGRESS
            task.assigned_to = agent.id
            
            # Simulate task execution (in real implementation, this would be actual agent processing)
            await self._monitor_task_execution(task, agent)
            
            # Calculate execution metrics
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update cost tracking
            task_cost = self._calculate_task_cost(task, agent, execution_time)
            workflow.total_cost += task_cost
            self.total_cost_incurred += task_cost
            
            # Release resources
            await self._release_resources_for_task(task, agent)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = end_time
            
            return {
                "task_id": task.id,
                "status": "completed",
                "execution_time": execution_time,
                "cost": task_cost,
                "agent_id": agent.id
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            await self._handle_task_failure(task, agent, e)
            raise

    # ================================
    # Resource Management
    # ================================

    async def _reserve_resources_for_task(self, task: Task, agent: Agent) -> None:
        """Reserve necessary system resources for task execution."""
        # Reserve agent capacity
        agent_resource = self.system_resources.get(f"agent_{agent.id}")
        if agent_resource and agent_resource.available > 0:
            agent_resource.allocated += 1
            agent_resource.reserved_by.add(task.id)
        
        # Reserve token budget based on task complexity
        estimated_tokens = self._estimate_token_usage(task)
        token_resource = self.system_resources["token_budget"]
        if token_resource.available >= estimated_tokens:
            token_resource.allocated += estimated_tokens
            token_resource.reserved_by.add(task.id)
        else:
            logger.warning(f"Insufficient token budget for task {task.id}")

    async def _release_resources_for_task(self, task: Task, agent: Agent) -> None:
        """Release resources after task completion."""
        # Release agent
        agent_resource = self.system_resources.get(f"agent_{agent.id}")
        if agent_resource:
            agent_resource.allocated = max(0, agent_resource.allocated - 1)
            agent_resource.reserved_by.discard(task.id)
        
        # Release tokens (actual usage may be different from estimate)
        token_resource = self.system_resources["token_budget"]
        if task.id in token_resource.reserved_by:
            # Calculate actual token usage
            actual_tokens = agent.brain.total_input_tokens + agent.brain.total_output_tokens
            token_resource.allocated = max(0, token_resource.allocated - actual_tokens)
            token_resource.reserved_by.discard(task.id)

    # ================================
    # Monitoring and Analytics
    # ================================

    async def _monitor_task_execution(self, task: Task, agent: Agent) -> None:
        """Monitor task execution and handle any issues that arise."""
        max_wait_time = 300  # 5 minutes timeout
        check_interval = 5   # Check every 5 seconds
        
        start_time = datetime.utcnow()
        
        while task.status == TaskStatus.IN_PROGRESS:
            # Check for timeout
            if (datetime.utcnow() - start_time).total_seconds() > max_wait_time:
                raise TimeoutError(f"Task {task.id} timed out after {max_wait_time} seconds")
            
            # Process agent inbox to handle status updates
            await agent.process_inbox()
            
            # Check for conflicts or resource issues
            await self._check_for_conflicts(task, agent)
            
            await asyncio.sleep(check_interval)

    def _calculate_task_cost(self, task: Task, agent: Agent, execution_time: float) -> float:
        """Calculate the cost of executing a task."""
        # Base cost calculation using token usage
        input_tokens = agent.brain.total_input_tokens
        output_tokens = agent.brain.total_output_tokens
        
        # Cost per token (varies by model)
        model = agent.brain.model.lower()
        if "gpt-4" in model:
            input_cost = input_tokens * 0.00003
            output_cost = output_tokens * 0.00006
        elif "claude-3" in model:
            input_cost = input_tokens * 0.000015
            output_cost = output_tokens * 0.000075
        else:
            input_cost = input_tokens * 0.00001
            output_cost = output_tokens * 0.00002
        
        total_cost = input_cost + output_cost
        
        # Add time-based cost for agent utilization
        time_cost = execution_time * 0.001  # $0.001 per second
        
        return total_cost + time_cost

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics."""
        active_agents = len([a for a in self.agents.values() if a.status != "offline"])
        total_capacity = sum(r.capacity for r in self.system_resources.values() 
                           if r.type == ResourceType.AGENT)
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "active_workflows": len(self.active_workflows),
            "total_tasks_processed": self.total_tasks_processed,
            "total_cost_incurred": round(self.total_cost_incurred, 4),
            "average_completion_time": round(self.average_task_completion_time, 2),
            "system_efficiency": round(self.system_efficiency_score, 3),
            "resource_utilization": {
                name: {
                    "capacity": resource.capacity,
                    "allocated": resource.allocated,
                    "utilization_rate": round(resource.utilization_rate, 3)
                }
                for name, resource in self.system_resources.items()
            },
            "token_budget_remaining": self.system_resources["token_budget"].available,
            "token_budget_utilization": self.system_resources["token_budget"].utilization_rate
        }

    # ================================
    # Helper Methods
    # ================================

    def _topological_sort(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by dependencies using topological sort algorithm."""
        # Create a map of task IDs to task objects
        task_map = {task.id: task for task in tasks}
        
        # Build adjacency list and in-degree count
        graph = {}
        in_degree = {}
        
        for task in tasks:
            graph[task.id] = task.dependencies.copy()
            in_degree[task.id] = len(task.dependencies)
        
        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []
        
        while queue:
            current_id = queue.pop(0)
            sorted_tasks.append(task_map[current_id])
            
            # Update in-degrees of dependent tasks
            for task_id, deps in graph.items():
                if current_id in deps:
                    deps.remove(current_id)
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)
        
        return sorted_tasks

    def _group_tasks_by_dependency_level(self, tasks: List[Task]) -> Dict[int, List[Task]]:
        """Group tasks by their dependency level for parallel execution."""
        levels = {}
        task_map = {task.id: task for task in tasks}
        
        def get_level(task_id: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            if task_id in visited:
                return 0  # Circular dependency, treat as level 0
            
            visited.add(task_id)
            task = task_map.get(task_id)
            
            if not task or not task.dependencies:
                return 0
            
            max_dep_level = max(get_level(dep_id, visited.copy()) 
                              for dep_id in task.dependencies)
            return max_dep_level + 1
        
        for task in tasks:
            level = get_level(task.id)
            if level not in levels:
                levels[level] = []
            levels[level].append(task)
        
        return levels

    def _are_dependencies_satisfied(self, task: Task) -> bool:
        """Check if all task dependencies have been completed."""
        for dep_id in task.dependencies:
            dep_task = self.task_monitor.task_registry.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    async def _allocate_agent_for_task(self, task: Task) -> Optional[Agent]:
        """Allocate the best available agent for a specific task."""
        return await self.task_allocator.allocate_task(self.agents, task)

    def _estimate_token_usage(self, task: Task) -> int:
        """Estimate token usage for a task based on complexity."""
        base_tokens = 1000  # Base token cost
        
        # Adjust based on task description length
        description_tokens = len(task.description.split()) * 1.3
        
        # Adjust based on required tools
        tool_complexity = len(task.required_tools) * 500
        
        # Adjust based on subtasks
        subtask_complexity = len(task.subtasks) * 300
        
        return int(base_tokens + description_tokens + tool_complexity + subtask_complexity)

    async def _check_for_conflicts(self, task: Task, agent: Agent) -> None:
        """Check for resource conflicts and initiate resolution if needed."""
        # Check if multiple agents are trying to use the same resources
        agent_resource = self.system_resources.get(f"agent_{agent.id}")
        if agent_resource and len(agent_resource.reserved_by) > 1:
            conflicting_tasks = list(agent_resource.reserved_by)
            if len(conflicting_tasks) > 1:
                logger.warning(f"Resource conflict detected for agent {agent.id}")
                await self._initiate_conflict_resolution(agent.id, conflicting_tasks)

    async def _initiate_conflict_resolution(self, resource_id: str, conflicting_task_ids: List[str]) -> None:
        """Initiate conflict resolution process."""
        # Use the negotiation manager to resolve conflicts
        negotiation_state = self.negotiation_manager.start_negotiation(
            resource_id=resource_id,
            initiating_agent_id="ORCHESTRATOR",
            involved_agent_ids=conflicting_task_ids
        )
        
        logger.info(f"Started conflict resolution {negotiation_state.negotiation_id} for resource {resource_id}")

    async def _handle_task_failure(self, task: Task, agent: Agent, error: Exception) -> None:
        """Handle task failure with recovery strategies."""
        logger.error(f"Task {task.id} failed on agent {agent.id}: {str(error)}")
        
        # Release resources
        await self._release_resources_for_task(task, agent)
        
        # Try to reassign to another agent
        alternative_agent = await self._allocate_agent_for_task(task)
        if alternative_agent and alternative_agent.id != agent.id:
            logger.info(f"Reassigning failed task {task.id} to agent {alternative_agent.id}")
            task.status = TaskStatus.PENDING
            # Could implement retry logic here

    async def _handle_workflow_failure(self, workflow: WorkflowExecution, error: Exception) -> None:
        """Handle workflow failure with comprehensive cleanup."""
        logger.error(f"Workflow {workflow.name} failed: {str(error)}")
        
        # Clean up any pending tasks
        for task in workflow.tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                task.status = TaskStatus.FAILED
                # Release any reserved resources
                for agent_id in workflow.participating_agents:
                    agent = self.agents.get(agent_id)
                    if agent:
                        await self._release_resources_for_task(task, agent)

    # ================================
    # Main Orchestration Loop
    # ================================

    async def start_orchestration(self) -> None:
        """Start the main orchestration loop."""
        logger.info("Starting system-wide orchestration loop")
        
        while True:
            try:
                # Process all active workflows
                for workflow_id in list(self.active_workflows.keys()):
                    workflow = self.active_workflows[workflow_id]
                    
                    if workflow.status == TaskStatus.PENDING:
                        # Start workflow execution
                        asyncio.create_task(self.execute_workflow(workflow_id))
                    
                # Monitor system health
                await self._monitor_system_health()
                
                # Clean up completed workflows
                await self._cleanup_completed_workflows()
                
                # Wait before next iteration
                await asyncio.sleep(self.orchestration_tick_interval)
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {str(e)}")
                await asyncio.sleep(self.orchestration_tick_interval)

    async def _monitor_system_health(self) -> None:
        """Monitor overall system health and performance."""
        # Check token budget
        token_resource = self.system_resources["token_budget"]
        if token_resource.utilization_rate > self.token_budget_threshold:
            logger.warning(f"Token budget utilization at {token_resource.utilization_rate:.2%}")
        
        # Check agent health
        for agent in self.agents.values():
            if len(self.agent_workloads.get(agent.id, [])) > 5:
                logger.warning(f"Agent {agent.name} is overloaded with {len(self.agent_workloads[agent.id])} tasks")

    async def _cleanup_completed_workflows(self) -> None:
        """Clean up completed workflows to free memory."""
        completed_workflows = [
            wf_id for wf_id, workflow in self.active_workflows.items()
            if workflow.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            and workflow.completed_at
            and (datetime.utcnow() - workflow.completed_at) > timedelta(hours=1)
        ]
        
        for wf_id in completed_workflows:
            del self.active_workflows[wf_id]
            logger.debug(f"Cleaned up completed workflow {wf_id}")