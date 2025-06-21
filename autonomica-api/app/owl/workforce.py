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