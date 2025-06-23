"""
OWL (Optimized Workflow Language) Workforce Implementation
Dynamic agent management system with cost tracking and tool integration
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json
from loguru import logger

# CAMEL Framework imports for tool-enabled agents
from camel.models import ModelFactory
from camel.toolkits import (
    SearchToolkit,
    CodeExecutionToolkit,
    MathToolkit,
    RetrievalToolkit,
    WeatherToolkit,
    DalleToolkit,
    TwitterToolkit,
    SlackToolkit,
    LinkedInToolkit,
    GoogleMapsToolkit,
    GithubToolkit,
)
from camel.types import ModelPlatformType, ModelType
from camel.societies import RolePlaying
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.configs import ChatGPTConfig

# LangChain integration
from .langchain_integration import get_nlp_engine, LangChainExecution

# Model pricing per 1K tokens (input/output)
MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015, "provider": "openai"},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006, "provider": "openai"},
    "gpt-4": {"input": 0.03, "output": 0.06, "provider": "openai"},
    "gpt-3.5-turbo": {"input": 0.001, "output": 0.002, "provider": "openai"},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015, "provider": "anthropic"},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125, "provider": "anthropic"},
    "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079, "provider": "groq"},
    "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008, "provider": "groq"},
}

@dataclass
class AgentTemplate:
    """Template for creating new agents"""
    name: str
    type: str
    base_prompt: str
    capabilities: List[str]
    recommended_tools: List[str]
    recommended_model: str
    description: str

@dataclass
class TaskExecution:
    """Track individual task executions and costs"""
    id: str
    agent_id: str
    task_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    status: str = "running"  # running, completed, failed
    result: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowTask:
    """Individual task within a workflow"""
    id: str
    title: str
    description: str
    agent_type: Optional[str] = None
    agent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    status: str = "pending"  # pending, assigned, running, completed, failed
    priority: int = 5  # 1-10, higher is more important
    estimated_duration: Optional[int] = None  # minutes
    execution_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Workflow:
    """Multi-agent workflow orchestration"""
    id: str
    title: str
    description: str
    user_id: str
    tasks: List[WorkflowTask] = field(default_factory=list)
    status: str = "created"  # created, planning, running, completed, failed, cancelled
    orchestration_strategy: str = "optimal"  # optimal, parallel, sequential, custom
    max_parallel_tasks: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_cost: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OrchestrationPlan:
    """Execution plan for a workflow"""
    workflow_id: str
    execution_order: List[List[str]]  # List of parallel execution groups
    agent_assignments: Dict[str, str]  # task_id -> agent_id
    estimated_duration: int  # total minutes
    estimated_cost: float
    resource_requirements: Dict[str, int]  # agent_type -> count
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass 
class Agent:
    """Dynamic tool-enabled agent with cost tracking"""
    id: str
    name: str
    type: str
    custom_prompt: str
    capabilities: List[str]
    model: str
    tools: List[str] = field(default_factory=list)
    status: str = "idle"  # idle, busy, error, offline
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    user_id: Optional[str] = None  # Clerk user ID
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    # Cost tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    tasks_completed: int = 0
    
    # CAMEL agent instance
    camel_agent: Optional[ChatAgent] = None
    toolkit_instances: List[Any] = field(default_factory=list)
    
    # LangChain NLP capabilities
    nlp_enabled: bool = False
    nlp_capabilities: List[str] = field(default_factory=list)  # Available NLP capabilities
    nlp_executions: List[LangChainExecution] = field(default_factory=list)  # NLP execution history
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "custom_prompt": self.custom_prompt,
            "capabilities": self.capabilities,
            "model": self.model,
            "tools": self.tools,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "user_id": self.user_id,
            "last_active": self.last_active.isoformat(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "tasks_completed": self.tasks_completed,
            "nlp_enabled": self.nlp_enabled,
            "nlp_capabilities": self.nlp_capabilities,
            "nlp_executions_count": len(self.nlp_executions)
        }
    
    async def initialize_camel_agent(self):
        """Initialize CAMEL agent with tools"""
        try:
            # Determine model platform and type
            model_platform = ModelPlatformType.OPENAI
            model_type = ModelType.GPT_4O_MINI
            
            if "claude" in self.model.lower():
                model_platform = ModelPlatformType.ANTHROPIC
                model_type = ModelType.CLAUDE_3_5_SONNET
            elif "gpt-4o" in self.model.lower():
                model_type = ModelType.GPT_4O
            elif "gpt-4" in self.model.lower():
                model_type = ModelType.GPT_4
            elif "groq" in self.model.lower() or "llama" in self.model.lower():
                model_platform = ModelPlatformType.GROQ
                model_type = ModelType.LLAMA_3_1_70B_VERSATILE
            
            # Create model with configuration
            model_config_dict = {
                "temperature": 0.7,
                "max_tokens": 1000,
            }
            
            model = ModelFactory.create(
                model_platform=model_platform,
                model_type=model_type,
                model_config_dict=model_config_dict,
            )
            
            # Initialize toolkits based on agent tools
            toolkits = []
            for tool_name in self.tools:
                if tool_name == "search":
                    toolkits.append(SearchToolkit())
                elif tool_name == "code_execution":
                    toolkits.append(CodeExecutionToolkit())
                elif tool_name == "math":
                    toolkits.append(MathToolkit())
                elif tool_name == "retrieval":
                    toolkits.append(RetrievalToolkit())
                elif tool_name == "weather":
                    toolkits.append(WeatherToolkit())
                elif tool_name == "dalle":
                    toolkits.append(DalleToolkit())
                elif tool_name == "twitter":
                    toolkits.append(TwitterToolkit())
                elif tool_name == "slack":
                    toolkits.append(SlackToolkit())
                elif tool_name == "linkedin":
                    toolkits.append(LinkedInToolkit())
                elif tool_name == "maps":
                    toolkits.append(GoogleMapsToolkit())
                elif tool_name == "github":
                    toolkits.append(GithubToolkit())
            
            self.toolkit_instances = toolkits
            
            # Create CAMEL agent
            self.camel_agent = ChatAgent(
                system_message=BaseMessage.make_assistant_message(
                    role_name=self.name,
                    content=self.custom_prompt
                ),
                model=model,
                tools=toolkits
            )
            
            logger.info(f"Initialized CAMEL agent for {self.name} with {len(toolkits)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize CAMEL agent for {self.name}: {e}")
            raise
    
    async def execute_task(self, task_spec: Dict[str, Any]) -> TaskExecution:
        """Execute a task using CAMEL agent with full tool capabilities"""
        execution = TaskExecution(
            id=str(uuid.uuid4()),
            agent_id=self.id,
            task_type=task_spec.get("task_type", "general"),
            start_time=datetime.utcnow()
        )
        
        try:
            self.status = "busy"
            self.last_active = datetime.utcnow()
            
            # Initialize CAMEL agent if not already done
            if not self.camel_agent:
                await self.initialize_camel_agent()
            
            # Create task message
            user_message = task_spec.get("inputs", {}).get("user_message", "")
            task_message = BaseMessage.make_user_message(
                role_name="User",
                content=f"Task: {user_message}\n\nPlease execute this task using your available tools and provide comprehensive results."
            )
            
            # Execute task with CAMEL agent
            response = self.camel_agent.step(task_message)
            
            # Calculate costs (approximate token counting)
            input_tokens = len(user_message.split()) * 1.3  # Rough approximation
            output_tokens = len(response.content.split()) * 1.3  # Rough approximation
            
            model_pricing = MODEL_PRICING.get(self.model, {"input": 0.001, "output": 0.002})
            cost = (input_tokens * model_pricing["input"] / 1000) + (output_tokens * model_pricing["output"] / 1000)
            
            # Update agent statistics
            self.total_input_tokens += int(input_tokens)
            self.total_output_tokens += int(output_tokens)
            self.total_cost += cost
            self.tasks_completed += 1
            
            # Update execution record
            execution.end_time = datetime.utcnow()
            execution.input_tokens = int(input_tokens)
            execution.output_tokens = int(output_tokens)
            execution.cost = cost
            execution.status = "completed"
            execution.result = {
                "response": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "agent_name": self.name,
                "model_used": self.model
            }
            
            self.status = "idle"
            
            return execution
            
        except Exception as e:
            execution.end_time = datetime.utcnow()
            execution.status = "failed"
            execution.result = {"error": str(e)}
            self.status = "error"
            logger.error(f"Task execution failed for {self.name}: {e}")
            raise

    async def enable_nlp_capabilities(self, capabilities: Optional[List[str]] = None):
        """Enable LangChain NLP capabilities for this agent"""
        try:
            nlp_engine = await get_nlp_engine()
            
            # If no specific capabilities requested, enable all available
            if capabilities is None:
                available_capabilities = nlp_engine.get_capabilities()
                self.nlp_capabilities = list(available_capabilities.keys())
            else:
                # Validate requested capabilities
                available_capabilities = nlp_engine.get_capabilities()
                valid_capabilities = []
                for cap in capabilities:
                    if cap in available_capabilities:
                        valid_capabilities.append(cap)
                    else:
                        logger.warning(f"Unknown NLP capability: {cap}")
                self.nlp_capabilities = valid_capabilities
            
            self.nlp_enabled = True
            logger.info(f"Enabled {len(self.nlp_capabilities)} NLP capabilities for agent {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to enable NLP capabilities for agent {self.name}: {e}")
            self.nlp_enabled = False
    
    async def execute_nlp_task(self, task_type: str, **kwargs) -> Optional[LangChainExecution]:
        """Execute an NLP task using LangChain"""
        if not self.nlp_enabled:
            logger.warning(f"NLP not enabled for agent {self.name}")
            return None
            
        if task_type not in self.nlp_capabilities:
            logger.warning(f"NLP capability '{task_type}' not available for agent {self.name}")
            return None
        
        try:
            nlp_engine = await get_nlp_engine()
            
            # Execute the appropriate NLP task
            if task_type == "text_summarization":
                execution = await nlp_engine.summarize_text(
                    text=kwargs.get("text", ""),
                    agent_id=self.id,
                    max_length=kwargs.get("max_length", 150),
                    style=kwargs.get("style", "concise")
                )
            elif task_type == "sentiment_analysis":
                execution = await nlp_engine.analyze_sentiment(
                    text=kwargs.get("text", ""),
                    agent_id=self.id
                )
            elif task_type == "language_translation":
                execution = await nlp_engine.translate_text(
                    text=kwargs.get("text", ""),
                    target_language=kwargs.get("target_language", "english"),
                    agent_id=self.id,
                    source_language=kwargs.get("source_language", "auto")
                )
            else:
                logger.warning(f"NLP task type '{task_type}' not yet implemented")
                return None
            
            # Track the execution
            self.nlp_executions.append(execution)
            self.total_cost += execution.cost
            
            logger.info(f"Agent {self.name} completed NLP task '{task_type}' (cost: ${execution.cost:.4f})")
            return execution
            
        except Exception as e:
            logger.error(f"NLP task '{task_type}' failed for agent {self.name}: {e}")
            return None
    
    def get_nlp_summary(self) -> Dict[str, Any]:
        """Get summary of NLP usage for this agent"""
        if not self.nlp_enabled:
            return {"nlp_enabled": False}
        
        total_nlp_cost = sum(exec.cost for exec in self.nlp_executions)
        total_nlp_tokens = sum(exec.tokens_used for exec in self.nlp_executions)
        
        capability_usage = {}
        for exec in self.nlp_executions:
            cap = exec.capability
            if cap not in capability_usage:
                capability_usage[cap] = {"count": 0, "cost": 0.0, "avg_time": 0.0}
            capability_usage[cap]["count"] += 1
            capability_usage[cap]["cost"] += exec.cost
            capability_usage[cap]["avg_time"] += exec.execution_time
        
        # Calculate averages
        for cap_stats in capability_usage.values():
            if cap_stats["count"] > 0:
                cap_stats["avg_time"] = cap_stats["avg_time"] / cap_stats["count"]
                cap_stats["cost"] = round(cap_stats["cost"], 4)
                cap_stats["avg_time"] = round(cap_stats["avg_time"], 2)
        
        return {
            "nlp_enabled": True,
            "available_capabilities": self.nlp_capabilities,
            "total_nlp_executions": len(self.nlp_executions),
            "total_nlp_cost": round(total_nlp_cost, 4),
            "total_nlp_tokens": total_nlp_tokens,
            "capability_usage": capability_usage
        }

# Predefined agent templates
AGENT_TEMPLATES = {
    "ceo": AgentTemplate(
        name="CEO",
        type="ceo",
        base_prompt="""You are the CEO of Autonomica, an AI-powered marketing agency. Your role is to:
1. Coordinate and delegate tasks to specialist agents
2. Make strategic decisions about resource allocation
3. Ensure all tasks align with business objectives
4. Provide high-level oversight and quality control
5. Interface with clients and stakeholders

You have access to tools for research, document processing, and team coordination. When given a task, analyze it and either handle it directly or delegate to appropriate specialist agents.""",
        capabilities=["strategic_leadership", "team_coordination", "delegation", "client_relations"],
        recommended_tools=["search", "document_processing", "excel"],
        recommended_model="gpt-4o",
        description="Executive leader responsible for strategic oversight and team coordination"
    ),
    
    "content_writer": AgentTemplate(
        name="Content Writer",
        type="content_writer", 
        base_prompt="""You are a professional content writer specializing in creating engaging, high-quality content. Your expertise includes:
1. Blog posts and articles
2. Marketing copy and sales materials
3. Social media content
4. Technical documentation
5. Creative storytelling

Use your tools to research topics, analyze competitor content, and create compelling, well-researched content that resonates with target audiences.""",
        capabilities=["blog_writing", "copywriting", "content_strategy", "storytelling"],
        recommended_tools=["search", "browser", "document_processing", "file_write"],
        recommended_model="gpt-4o",
        description="Expert content creator for blogs, marketing materials, and engaging copy"
    ),
    
    "seo_analyst": AgentTemplate(
        name="SEO Analyst",
        type="seo_analyst",
        base_prompt="""You are an SEO specialist focused on improving search engine visibility and organic traffic. Your expertise includes:
1. Keyword research and analysis
2. On-page and technical SEO optimization
3. Competitor analysis
4. Content optimization for search engines
5. SEO performance tracking and reporting

Use your tools to conduct thorough SEO audits, research keywords, analyze competitors, and provide actionable SEO recommendations.""",
        capabilities=["keyword_research", "seo_audit", "competitor_analysis", "technical_seo"],
        recommended_tools=["search", "browser", "excel", "document_processing"],
        recommended_model="gpt-4o-mini",
        description="SEO expert for search optimization and organic traffic growth"
    ),
    
    "social_media_manager": AgentTemplate(
        name="Social Media Manager",
        type="social_media_manager",
        base_prompt="""You are a social media marketing expert responsible for building brand presence across social platforms. Your expertise includes:
1. Social media strategy development
2. Content calendar planning and scheduling
3. Community engagement and management
4. Social media advertising campaigns
5. Performance analytics and reporting

Use your tools to research trending topics, analyze competitor social presence, and create comprehensive social media strategies.""",
        capabilities=["social_strategy", "content_scheduling", "community_management", "social_advertising"],
        recommended_tools=["search", "browser", "excel", "document_processing"],
        recommended_model="gpt-4o-mini",
        description="Social media expert for brand building and audience engagement"
    ),
    
    "data_analyst": AgentTemplate(
        name="Data Analyst", 
        type="data_analyst",
        base_prompt="""You are a marketing data analyst focused on extracting insights from data to drive business decisions. Your expertise includes:
1. Marketing performance analysis
2. Customer behavior analytics
3. Campaign ROI measurement
4. Data visualization and reporting
5. Predictive analytics for marketing

Use your tools to process data files, create visualizations, and provide actionable insights based on marketing metrics and KPIs.""",
        capabilities=["data_analysis", "reporting", "visualization", "predictive_analytics"],
        recommended_tools=["excel", "code_execution", "document_processing", "file_write"],
        recommended_model="gpt-4o-mini",
        description="Data expert for marketing analytics and performance insights"
    )
}

class AutonomicaWorkforce:
    """Dynamic workforce management system with cost tracking"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.agent_templates = AGENT_TEMPLATES
        self.task_executions: List[TaskExecution] = []
        self.workflows: Dict[str, Workflow] = {}
        self.orchestration_plans: Dict[str, OrchestrationPlan] = {}
        self.total_cost: float = 0.0
        
    async def initialize(self):
        """Initialize workforce with CEO agent"""
        logger.info("Initializing Autonomica Workforce...")
        
        # Always create a CEO agent first
        ceo_agent = await self.create_agent_from_template(
            template_type="ceo",
            custom_name="CEO",
            created_by="system"
        )
        
        logger.info(f"Workforce initialized with CEO agent: {ceo_agent.id}")
        
    async def create_agent_from_template(
        self, 
        template_type: str, 
        custom_name: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        custom_model: Optional[str] = None,
        custom_tools: Optional[List[str]] = None,
        created_by: str = "user",
        user_id: Optional[str] = None
    ) -> Agent:
        """Create a new agent from a template with customizations"""
        
        if template_type not in self.agent_templates:
            raise ValueError(f"Template {template_type} not found")
        
        template = self.agent_templates[template_type]
        
        agent = Agent(
            id=str(uuid.uuid4()),
            name=custom_name or template.name,
            type=template.type,
            custom_prompt=custom_prompt or template.base_prompt,
            capabilities=template.capabilities.copy(),
            model=custom_model or template.recommended_model,
            tools=custom_tools or template.recommended_tools.copy(),
            created_by=created_by,
            user_id=user_id
        )
        
        # Initialize the CAMEL agent
        await agent.initialize_camel_agent()
        
        self.agents[agent.id] = agent
        logger.info(f"Created agent: {agent.name} ({agent.type}) with model {agent.model}")
        
        return agent
    
    async def create_custom_agent(
        self,
        name: str,
        agent_type: str,
        custom_prompt: str,
        model: str,
        tools: List[str],
        capabilities: List[str],
        created_by: str = "user",
        user_id: Optional[str] = None
    ) -> Agent:
        """Create a completely custom agent"""
        
        agent = Agent(
            id=str(uuid.uuid4()),
            name=name,
            type=agent_type,
            custom_prompt=custom_prompt,
            capabilities=capabilities,
            model=model,
            tools=tools,
            created_by=created_by,
            user_id=user_id
        )
        
        await agent.initialize_camel_agent()
        self.agents[agent.id] = agent
        
        logger.info(f"Created custom agent: {name} with model {model}")
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.type == agent_type]
    
    def get_ceo_agent(self) -> Optional[Agent]:
        """Get the CEO agent"""
        ceo_agents = self.get_agents_by_type("ceo")
        return ceo_agents[0] if ceo_agents else None
    
    async def delegate_task(self, task_spec: Dict[str, Any]) -> TaskExecution:
        """CEO delegates task to appropriate agent"""
        ceo = self.get_ceo_agent()
        if not ceo:
            raise ValueError("No CEO agent available for delegation")
        
        # CEO analyzes task and determines best agent
        user_message = task_spec.get("inputs", {}).get("user_message", "")
        
        # For now, route through CEO - in future, CEO could intelligently delegate
        return await ceo.execute_task(task_spec)
    
    async def assign_task_to_agent(
        self, 
        agent_id: str, 
        task_id: str, 
        task_description: str, 
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Assign a specific task to a specific agent and return execution ID"""
        
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if agent.status not in ["idle", "ready"]:
            logger.warning(f"Agent {agent.name} is {agent.status}, task may be queued")
        
        try:
            # Prepare task specification for OWL execution
            task_spec = {
                "task_id": task_id,
                "task_type": task_metadata.get("priority", "medium") if task_metadata else "medium",
                "inputs": {
                    "user_message": task_description,
                    "metadata": task_metadata or {}
                }
            }
            
            # Execute task with the specific agent
            execution = await agent.execute_task(task_spec)
            
            # Track the execution
            self.task_executions.append(execution)
            self.total_cost += execution.cost
            
            logger.info(f"Task {task_id} assigned to agent {agent.name} (cost: ${execution.cost:.4f})")
            
            return execution.id  # Return execution ID for tracking
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_id} to agent {agent.name}: {e}")
            raise
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost breakdown"""
        summary = {
            "total_cost": round(sum(agent.total_cost for agent in self.agents.values()), 4),
            "total_input_tokens": sum(agent.total_input_tokens for agent in self.agents.values()),
            "total_output_tokens": sum(agent.total_output_tokens for agent in self.agents.values()),
            "total_tasks": sum(agent.tasks_completed for agent in self.agents.values()),
            "agents": []
        }
        
        for agent in self.agents.values():
            agent_cost = {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type,
                "model": agent.model,
                "cost": round(agent.total_cost, 4),
                "input_tokens": agent.total_input_tokens,
                "output_tokens": agent.total_output_tokens,
                "tasks_completed": agent.tasks_completed,
                "created_by": agent.created_by
            }
            summary["agents"].append(agent_cost)
        
        return summary
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available agent templates"""
        return {
            template_type: {
                "name": template.name,
                "type": template.type,
                "description": template.description,
                "capabilities": template.capabilities,
                "recommended_tools": template.recommended_tools,
                "recommended_model": template.recommended_model
            }
            for template_type, template in self.agent_templates.items()
        }
    
    def get_model_pricing(self) -> Dict[str, Dict[str, Any]]:
        """Get current model pricing information"""
        return MODEL_PRICING.copy()

    # Agent Orchestration Logic for Task 2.8
    
    async def create_workflow(
        self,
        title: str,
        description: str,
        user_id: str,
        workflow_tasks: List[Dict[str, Any]],
        orchestration_strategy: str = "optimal",
        max_parallel_tasks: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """Create a new multi-agent workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        # Convert task definitions to WorkflowTask objects
        tasks = []
        for i, task_def in enumerate(workflow_tasks):
            task = WorkflowTask(
                id=f"{workflow_id}-task-{i+1}",
                title=task_def.get("title", f"Task {i+1}"),
                description=task_def.get("description", ""),
                agent_type=task_def.get("agent_type"),
                dependencies=task_def.get("dependencies", []),
                priority=task_def.get("priority", 5),
                estimated_duration=task_def.get("estimated_duration")
            )
            tasks.append(task)
        
        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=description,
            user_id=user_id,
            tasks=tasks,
            orchestration_strategy=orchestration_strategy,
            max_parallel_tasks=max_parallel_tasks,
            metadata=metadata or {}
        )
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow '{title}' with {len(tasks)} tasks for user {user_id}")
        
        return workflow
    
    async def create_orchestration_plan(self, workflow_id: str) -> OrchestrationPlan:
        """Create an optimal execution plan for a workflow"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Get user's available agents
        user_agents = [a for a in self.agents.values() if a.user_id == workflow.user_id]
        
        if not user_agents:
            raise ValueError(f"No agents available for user {workflow.user_id}")
        
        # Analyze task dependencies and create execution groups
        execution_order = self._plan_execution_order(workflow.tasks, workflow.max_parallel_tasks)
        
        # Assign optimal agents to tasks
        agent_assignments = await self._assign_agents_to_tasks(workflow.tasks, user_agents)
        
        # Calculate estimates
        estimated_duration, estimated_cost = self._calculate_workflow_estimates(
            workflow.tasks, agent_assignments
        )
        
        # Calculate resource requirements
        resource_requirements = self._calculate_resource_requirements(workflow.tasks)
        
        plan = OrchestrationPlan(
            workflow_id=workflow_id,
            execution_order=execution_order,
            agent_assignments=agent_assignments,
            estimated_duration=estimated_duration,
            estimated_cost=estimated_cost,
            resource_requirements=resource_requirements
        )
        
        self.orchestration_plans[workflow_id] = plan
        workflow.status = "planning"
        
        logger.info(f"Created orchestration plan for workflow {workflow_id}: "
                   f"{estimated_duration}min, ${estimated_cost:.2f}")
        
        return plan
    
    def _plan_execution_order(self, tasks: List[WorkflowTask], max_parallel: int) -> List[List[str]]:
        """Plan optimal execution order respecting dependencies"""
        
        execution_groups = []
        completed_tasks = set()
        remaining_tasks = {task.id: task for task in tasks}
        
        while remaining_tasks:
            # Find tasks with no pending dependencies
            ready_tasks = []
            for task_id, task in remaining_tasks.items():
                if all(dep in completed_tasks for dep in task.dependencies):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # Circular dependency or other issue
                logger.warning(f"No ready tasks found. Remaining: {list(remaining_tasks.keys())}")
                break
            
            # Sort by priority and take up to max_parallel
            ready_tasks.sort(key=lambda tid: remaining_tasks[tid].priority, reverse=True)
            
            # Create execution group
            group = ready_tasks[:max_parallel]
            execution_groups.append(group)
            
            # Mark as scheduled
            for task_id in group:
                completed_tasks.add(task_id)
                del remaining_tasks[task_id]
        
        return execution_groups
    
    async def _assign_agents_to_tasks(
        self, 
        tasks: List[WorkflowTask], 
        available_agents: List[Agent]
    ) -> Dict[str, str]:
        """Assign optimal agents to workflow tasks"""
        
        assignments = {}
        agent_workload = {agent.id: 0 for agent in available_agents}
        
        # Sort tasks by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            best_agent = None
            best_score = -1
            
            # Find best agent for this task
            for agent in available_agents:
                score = self._calculate_agent_task_score(agent, task)
                
                # Prefer less loaded agents
                load_penalty = agent_workload[agent.id] * 0.1
                adjusted_score = score - load_penalty
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent
            
            if best_agent:
                assignments[task.id] = best_agent.id
                agent_workload[best_agent.id] += task.estimated_duration or 10
                task.agent_id = best_agent.id
                task.agent_type = best_agent.type
        
        return assignments
    
    def _calculate_agent_task_score(self, agent: Agent, task: WorkflowTask) -> float:
        """Calculate how well an agent matches a task"""
        
        score = 0.0
        
        # Type match bonus
        if task.agent_type and agent.type == task.agent_type:
            score += 10.0
        
        # Capability match
        task_keywords = task.description.lower().split()
        capability_matches = sum(1 for cap in agent.capabilities 
                               if any(keyword in cap.lower() for keyword in task_keywords))
        score += capability_matches * 2.0
        
        # Performance history bonus
        if agent.tasks_completed > 0:
            success_rate = min(agent.tasks_completed / max(agent.tasks_completed + 1, 1), 1.0)
            score += success_rate * 3.0
        
        # Model quality bonus (higher for better models)
        if "gpt-4" in agent.model.lower():
            score += 2.0
        elif "claude" in agent.model.lower():
            score += 2.5
        
        # Availability bonus
        if agent.status == "idle":
            score += 5.0
        elif agent.status == "busy":
            score -= 2.0
        
        return score
    
    def _calculate_workflow_estimates(
        self, 
        tasks: List[WorkflowTask], 
        assignments: Dict[str, str]
    ) -> Tuple[int, float]:
        """Calculate estimated duration and cost for workflow"""
        
        total_duration = 0
        total_cost = 0.0
        
        for task in tasks:
            # Estimate duration
            duration = task.estimated_duration or 10  # default 10 minutes
            total_duration = max(total_duration, duration)  # Assuming parallel execution
            
            # Estimate cost
            if task.agent_id and task.agent_id in [a.id for a in self.agents.values()]:
                agent = self.agents[task.agent_id]
                model_pricing = MODEL_PRICING.get(agent.model, {"input": 0.001, "output": 0.002})
                
                # Rough cost estimate: 500 input + 300 output tokens per task
                estimated_cost = (500 * model_pricing["input"] + 300 * model_pricing["output"]) / 1000
                total_cost += estimated_cost
        
        return total_duration, total_cost
    
    def _calculate_resource_requirements(self, tasks: List[WorkflowTask]) -> Dict[str, int]:
        """Calculate required agent types and counts"""
        
        requirements = {}
        for task in tasks:
            if task.agent_type:
                requirements[task.agent_type] = requirements.get(task.agent_type, 0) + 1
            else:
                requirements["general"] = requirements.get("general", 0) + 1
        
        return requirements
    
    async def execute_workflow(self, workflow_id: str) -> bool:
        """Execute a workflow using the orchestration plan"""
        
        workflow = self.workflows.get(workflow_id)
        plan = self.orchestration_plans.get(workflow_id)
        
        if not workflow or not plan:
            raise ValueError(f"Workflow {workflow_id} or its plan not found")
        
        workflow.status = "running"
        workflow.started_at = datetime.utcnow()
        
        logger.info(f"Starting execution of workflow '{workflow.title}'")
        
        try:
            for group_index, task_group in enumerate(plan.execution_order):
                logger.info(f"Executing group {group_index + 1}: {len(task_group)} tasks")
                
                # Execute tasks in parallel within the group
                group_tasks = []
                for task_id in task_group:
                    task = next(t for t in workflow.tasks if t.id == task_id)
                    if task.agent_id:
                        group_tasks.append(self._execute_workflow_task(task, workflow_id))
                
                # Wait for all tasks in group to complete
                if group_tasks:
                    await asyncio.gather(*group_tasks, return_exceptions=True)
            
            # Check if all tasks completed successfully
            failed_tasks = [t for t in workflow.tasks if t.status == "failed"]
            
            if failed_tasks:
                workflow.status = "failed"
                logger.error(f"Workflow {workflow_id} failed: {len(failed_tasks)} tasks failed")
                return False
            else:
                workflow.status = "completed"
                workflow.completed_at = datetime.utcnow()
                logger.info(f"Workflow '{workflow.title}' completed successfully")
                return True
                
        except Exception as e:
            workflow.status = "failed"
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            return False
    
    async def _execute_workflow_task(self, task: WorkflowTask, workflow_id: str) -> bool:
        """Execute a single task within a workflow"""
        
        try:
            task.status = "running"
            task.started_at = datetime.utcnow()
            
            agent = self.agents.get(task.agent_id)
            if not agent:
                raise ValueError(f"Agent {task.agent_id} not found")
            
            # Prepare task spec with workflow context
            task_spec = {
                "task_id": task.id,
                "workflow_id": workflow_id,
                "task_type": "workflow_task",
                "inputs": {
                    "user_message": f"Workflow Task: {task.title}\n\nDescription: {task.description}",
                    "metadata": {
                        "workflow_id": workflow_id,
                        "task_id": task.id,
                        "priority": task.priority
                    }
                }
            }
            
            # Execute the task
            execution = await agent.execute_task(task_spec)
            
            # Update task status
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.execution_id = execution.id
            task.result = execution.result
            
            # Track execution
            self.task_executions.append(execution)
            self.workflows[workflow_id].total_cost += execution.cost
            
            logger.info(f"Workflow task {task.id} completed (cost: ${execution.cost:.4f})")
            return True
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.result = {"error": str(e)}
            logger.error(f"Workflow task {task.id} failed: {e}")
            return False
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive status of a workflow"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Calculate progress
        total_tasks = len(workflow.tasks)
        completed_tasks = len([t for t in workflow.tasks if t.status == "completed"])
        failed_tasks = len([t for t in workflow.tasks if t.status == "failed"])
        running_tasks = len([t for t in workflow.tasks if t.status == "running"])
        
        progress = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            "workflow_id": workflow.id,
            "title": workflow.title,
            "status": workflow.status,
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "total_cost": round(workflow.total_cost, 4),
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "agent_id": task.agent_id,
                    "agent_name": self.agents[task.agent_id].name if task.agent_id and task.agent_id in self.agents else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in workflow.tasks
            ]
        }
    
    def get_user_workflows(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a specific user"""
        
        user_workflows = [wf for wf in self.workflows.values() if wf.user_id == user_id]
        
        return [
            {
                "id": wf.id,
                "title": wf.title,
                "description": wf.description,
                "status": wf.status,
                "task_count": len(wf.tasks),
                "total_cost": round(wf.total_cost, 4),
                "created_at": wf.created_at.isoformat(),
                "completed_at": wf.completed_at.isoformat() if wf.completed_at else None
            }
            for wf in user_workflows
        ]

    # LangChain NLP Integration Methods for Task 2.9
    
    async def enable_agent_nlp(self, agent_id: str, capabilities: Optional[List[str]] = None) -> bool:
        """Enable LangChain NLP capabilities for a specific agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return False
        
        try:
            await agent.enable_nlp_capabilities(capabilities)
            logger.info(f"Enabled NLP capabilities for agent {agent.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable NLP for agent {agent.name}: {e}")
            return False
    
    async def bulk_enable_nlp(
        self, 
        user_id: Optional[str] = None, 
        agent_types: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Enable NLP capabilities for multiple agents"""
        
        # Filter agents based on criteria
        target_agents = []
        for agent in self.agents.values():
            if user_id and agent.user_id != user_id:
                continue
            if agent_types and agent.type not in agent_types:
                continue
            target_agents.append(agent)
        
        results = {
            "total_agents": len(target_agents),
            "enabled_successfully": 0,
            "failed": 0,
            "agent_results": []
        }
        
        for agent in target_agents:
            try:
                await agent.enable_nlp_capabilities(capabilities)
                results["enabled_successfully"] += 1
                results["agent_results"].append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "status": "success",
                    "nlp_capabilities": agent.nlp_capabilities
                })
            except Exception as e:
                results["failed"] += 1
                results["agent_results"].append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"Bulk NLP enablement: {results['enabled_successfully']}/{results['total_agents']} agents")
        return results
    
    async def execute_nlp_workflow(
        self, 
        workflow_tasks: List[Dict[str, Any]], 
        user_id: str
    ) -> Dict[str, Any]:
        """Execute a workflow of NLP tasks across multiple agents"""
        
        workflow_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        results = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "total_tasks": len(workflow_tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_cost": 0.0,
            "task_results": [],
            "start_time": start_time.isoformat()
        }
        
        # Get user's NLP-enabled agents
        nlp_agents = [
            agent for agent in self.agents.values()
            if agent.user_id == user_id and agent.nlp_enabled
        ]
        
        if not nlp_agents:
            results["error"] = "No NLP-enabled agents found for user"
            return results
        
        # Execute NLP tasks
        for i, task in enumerate(workflow_tasks):
            task_type = task.get("type")
            task_data = task.get("data", {})
            
            # Select best agent for this task type
            best_agent = None
            for agent in nlp_agents:
                if task_type in agent.nlp_capabilities:
                    best_agent = agent
                    break
            
            if not best_agent:
                results["failed_tasks"] += 1
                results["task_results"].append({
                    "task_index": i,
                    "task_type": task_type,
                    "status": "failed",
                    "error": f"No agent available for task type: {task_type}"
                })
                continue
            
            try:
                execution = await best_agent.execute_nlp_task(task_type, **task_data)
                
                if execution and execution.status == "success":
                    results["completed_tasks"] += 1
                    results["total_cost"] += execution.cost
                    results["task_results"].append({
                        "task_index": i,
                        "task_type": task_type,
                        "agent_id": best_agent.id,
                        "agent_name": best_agent.name,
                        "status": "success",
                        "execution_id": execution.id,
                        "cost": execution.cost,
                        "execution_time": execution.execution_time,
                        "output_summary": str(execution.output_data)[:200] + "..." if len(str(execution.output_data)) > 200 else str(execution.output_data)
                    })
                else:
                    results["failed_tasks"] += 1
                    results["task_results"].append({
                        "task_index": i,
                        "task_type": task_type,
                        "status": "failed",
                        "error": execution.error_message if execution else "Unknown error"
                    })
                    
            except Exception as e:
                results["failed_tasks"] += 1
                results["task_results"].append({
                    "task_index": i,
                    "task_type": task_type,
                    "status": "failed",
                    "error": str(e)
                })
        
        results["end_time"] = datetime.utcnow().isoformat()
        results["total_cost"] = round(results["total_cost"], 4)
        
        logger.info(f"NLP workflow {workflow_id} completed: {results['completed_tasks']}/{results['total_tasks']} tasks")
        return results
    
    def get_nlp_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive NLP usage analytics"""
        
        # Filter agents based on user
        agents = [a for a in self.agents.values() if not user_id or a.user_id == user_id]
        nlp_agents = [a for a in agents if a.nlp_enabled]
        
        if not nlp_agents:
            return {
                "total_agents": len(agents),
                "nlp_enabled_agents": 0,
                "analytics": {}
            }
        
        # Aggregate statistics
        total_nlp_executions = sum(len(agent.nlp_executions) for agent in nlp_agents)
        total_nlp_cost = sum(sum(exec.cost for exec in agent.nlp_executions) for agent in nlp_agents)
        total_nlp_tokens = sum(sum(exec.tokens_used for exec in agent.nlp_executions) for agent in nlp_agents)
        
        # Capability usage across all agents
        capability_stats = {}
        for agent in nlp_agents:
            for exec in agent.nlp_executions:
                cap = exec.capability
                if cap not in capability_stats:
                    capability_stats[cap] = {
                        "total_executions": 0,
                        "total_cost": 0.0,
                        "total_tokens": 0,
                        "avg_execution_time": 0.0,
                        "success_rate": 0.0
                    }
                
                capability_stats[cap]["total_executions"] += 1
                capability_stats[cap]["total_cost"] += exec.cost
                capability_stats[cap]["total_tokens"] += exec.tokens_used
                capability_stats[cap]["avg_execution_time"] += exec.execution_time
                
                if exec.status == "success":
                    capability_stats[cap]["success_rate"] += 1
        
        # Calculate averages and success rates
        for cap, stats in capability_stats.items():
            if stats["total_executions"] > 0:
                stats["avg_execution_time"] /= stats["total_executions"]
                stats["success_rate"] = (stats["success_rate"] / stats["total_executions"]) * 100
                stats["total_cost"] = round(stats["total_cost"], 4)
                stats["avg_execution_time"] = round(stats["avg_execution_time"], 2)
                stats["success_rate"] = round(stats["success_rate"], 1)
        
        # Agent performance breakdown
        agent_performance = []
        for agent in nlp_agents:
            agent_summary = agent.get_nlp_summary()
            agent_performance.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "agent_type": agent.type,
                **agent_summary
            })
        
        return {
            "user_id": user_id,
            "total_agents": len(agents),
            "nlp_enabled_agents": len(nlp_agents),
            "total_nlp_executions": total_nlp_executions,
            "total_nlp_cost": round(total_nlp_cost, 4),
            "total_nlp_tokens": total_nlp_tokens,
            "capability_analytics": capability_stats,
            "agent_performance": agent_performance,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def get_available_nlp_capabilities(self) -> Dict[str, Any]:
        """Get all available LangChain NLP capabilities"""
        try:
            nlp_engine = await get_nlp_engine()
            capabilities = nlp_engine.get_capabilities()
            
            return {
                "total_capabilities": len(capabilities),
                "capabilities": {
                    cap_name: {
                        "name": cap.name,
                        "description": cap.description,
                        "input_type": cap.input_type,
                        "output_type": cap.output_type,
                        "required_tools": cap.required_tools
                    }
                    for cap_name, cap in capabilities.items()
                }
            }
        except Exception as e:
            logger.error(f"Failed to get NLP capabilities: {e}")
            return {"error": str(e)}

    async def shutdown(self):
        """Cleanup resources during shutdown"""
        logger.info("🔄 Shutting down Autonomica Workforce...")
        # Cleanup any resources, close connections, etc.
        # For now, just log the shutdown
        for agent in self.agents.values():
            agent.status = "offline"
        logger.info("✅ Workforce shutdown complete")

# Global workforce instance
_workforce_instance = None


async def get_workforce() -> AutonomicaWorkforce:
    """Get or create workforce instance"""
    global _workforce_instance
    if _workforce_instance is None:
        _workforce_instance = AutonomicaWorkforce()
        await _workforce_instance.initialize()
    return _workforce_instance 