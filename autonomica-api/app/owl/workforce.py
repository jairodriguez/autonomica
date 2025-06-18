"""
OWL (Optimized Workflow Language) Workforce Implementation
Core orchestration engine for multi-agent marketing automation
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import redis.asyncio as redis
import faiss
import numpy as np
from loguru import logger

from app.core.config import settings
from app.core.exceptions import OWLException, AgentException


@dataclass
class WorkforceStats:
    """Statistics for workforce performance tracking"""
    total_tasks_processed: int = 0
    total_workflows_executed: int = 0
    active_agents: int = 0
    uptime_seconds: float = 0
    average_task_duration: float = 0
    
    def update_uptime(self, start_time: float):
        self.uptime_seconds = time.time() - start_time


@dataclass 
class Agent:
    """OWL Agent representation"""
    id: str
    name: str
    type: str  # e.g., "content_writer", "seo_analyst", "social_media_manager"
    capabilities: List[str]
    status: str = "idle"  # idle, busy, error, offline
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    tasks_completed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name, 
            "type": self.type,
            "capabilities": self.capabilities,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "tasks_completed": self.tasks_completed
        }


@dataclass
class Workflow:
    """OWL Workflow representation"""
    id: str
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": self.tasks,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result
        }


class VectorMemory:
    """FAISS-based vector memory for agents"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.id_to_data = {}
        self.next_id = 0
    
    def add_memory(self, vector: np.ndarray, data: Dict[str, Any]) -> int:
        """Add a memory with vector representation"""
        memory_id = self.next_id
        self.index.add(vector.reshape(1, -1).astype('float32'))
        self.id_to_data[memory_id] = {
            **data,
            "timestamp": datetime.utcnow().isoformat(),
            "memory_id": memory_id
        }
        self.next_id += 1
        return memory_id
    
    def search_memories(self, query_vector: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memories"""
        if self.index.ntotal == 0:
            return []
        
        distances, indices = self.index.search(
            query_vector.reshape(1, -1).astype('float32'), 
            min(k, self.index.ntotal)
        )
        
        results = []
        for i, distance in zip(indices[0], distances[0]):
            if i >= 0 and i in self.id_to_data:
                memory = self.id_to_data[i].copy()
                memory["similarity_score"] = float(1.0 / (1.0 + distance))
                results.append(memory)
        
        return results


class AutonomicaWorkforce:
    """Main OWL Workforce orchestration engine"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.agents: Dict[str, Agent] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.vector_store: Optional[VectorMemory] = None
        self.stats = WorkforceStats()
        self.start_time = time.time()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the OWL Workforce"""
        try:
            logger.info("🦉 Initializing OWL Workforce...")
            
            # Initialize Redis connection
            await self._initialize_redis()
            
            # Initialize vector memory
            self._initialize_vector_store()
            
            # Create default marketing agents
            await self._create_default_agents()
            
            # Start background tasks
            asyncio.create_task(self._stats_updater())
            
            self._initialized = True
            logger.success(f"✅ OWL Workforce initialized with {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OWL Workforce: {e}")
            raise OWLException(f"Workforce initialization failed: {str(e)}")
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            await self.redis_client.ping()
            logger.info("✅ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            # Continue without Redis for development
            self.redis_client = None
    
    def _initialize_vector_store(self):
        """Initialize FAISS vector store"""
        try:
            self.vector_store = VectorMemory(dimension=settings.VECTOR_DIMENSION)
            logger.info(f"✅ Vector store initialized (dimension: {settings.VECTOR_DIMENSION})")
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            raise OWLException(f"Vector store initialization failed: {str(e)}")
    
    async def _create_default_agents(self):
        """Create default marketing agents"""
        default_agents = [
            {
                "name": "Content Writer",
                "type": "content_writer",
                "capabilities": ["blog_writing", "content_creation", "copywriting", "storytelling"]
            },
            {
                "name": "SEO Specialist", 
                "type": "seo_analyst",
                "capabilities": ["keyword_research", "seo_optimization", "content_analysis", "ranking_analysis"]
            },
            {
                "name": "Social Media Manager",
                "type": "social_media_manager", 
                "capabilities": ["social_posting", "content_scheduling", "engagement", "community_management"]
            },
            {
                "name": "Marketing Strategist",
                "type": "marketing_strategist",
                "capabilities": ["campaign_planning", "market_analysis", "strategy_development", "competitor_analysis"]
            },
            {
                "name": "Data Analyst",
                "type": "data_analyst",
                "capabilities": ["data_analysis", "reporting", "metrics_tracking", "performance_analysis"]
            }
        ]
        
        for agent_config in default_agents:
            agent = Agent(
                id=str(uuid.uuid4()),
                name=agent_config["name"],
                type=agent_config["type"],
                capabilities=agent_config["capabilities"]
            )
            self.agents[agent.id] = agent
            logger.info(f"✅ Created agent: {agent.name} ({agent.type})")
    
    async def create_workflow(self, workflow_spec: Dict[str, Any]) -> str:
        """Create and queue a new workflow"""
        if not self._initialized:
            raise OWLException("Workforce not initialized")
        
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            name=workflow_spec.get("name", f"Workflow-{workflow_id[:8]}"),
            description=workflow_spec.get("description", ""),
            tasks=workflow_spec.get("tasks", [])
        )
        
        self.active_workflows[workflow_id] = workflow
        
        # Queue workflow for execution
        asyncio.create_task(self._execute_workflow(workflow))
        
        logger.info(f"📋 Created workflow: {workflow.name} ({workflow_id})")
        return workflow_id
    
    async def _execute_workflow(self, workflow: Workflow):
        """Execute a workflow with multiple agents"""
        try:
            workflow.status = "running"
            workflow.started_at = datetime.utcnow()
            
            logger.info(f"🚀 Executing workflow: {workflow.name}")
            
            # Simulate workflow execution
            # In a real implementation, this would orchestrate actual agents
            await asyncio.sleep(2)  # Simulate processing time
            
            # Mark as completed
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            workflow.result = {
                "status": "success",
                "output": f"Workflow {workflow.name} completed successfully",
                "tasks_completed": len(workflow.tasks),
                "duration_seconds": (workflow.completed_at - workflow.started_at).total_seconds()
            }
            
            self.stats.total_workflows_executed += 1
            
            logger.success(f"✅ Workflow completed: {workflow.name}")
            
        except Exception as e:
            workflow.status = "failed"
            workflow.completed_at = datetime.utcnow()
            workflow.result = {"status": "error", "error": str(e)}
            logger.error(f"❌ Workflow failed: {workflow.name} - {e}")
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    async def get_agents_by_type(self, agent_type: str) -> List[Agent]:
        """Get all agents of a specific type"""
        return [agent for agent in self.agents.values() if agent.type == agent_type]
    
    def get_agent_by_type(self, agent_type: str) -> Optional[Agent]:
        """Get the first agent of a specific type"""
        agents = [agent for agent in self.agents.values() if agent.type == agent_type]
        return agents[0] if agents else None
    
    def route_message_to_agent(self, message: str) -> Agent:
        """Route message to the most appropriate agent based on content"""
        message_lower = message.lower()
        
        # Define keywords for each agent type
        agent_keywords = {
            "content_writer": ["content", "blog", "write", "article", "copy", "story", "text"],
            "seo_analyst": ["seo", "keyword", "search", "ranking", "optimize", "google"],
            "social_media_manager": ["social", "twitter", "facebook", "instagram", "post", "schedule"],
            "marketing_strategist": ["strategy", "campaign", "plan", "market", "competitor", "analysis"],
            "data_analyst": ["data", "analytics", "metrics", "report", "performance", "numbers"]
        }
        
        # Score each agent type based on keyword matches
        scores = {}
        for agent_type, keywords in agent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[agent_type] = score
        
        # Choose the agent type with the highest score
        if scores:
            best_agent_type = max(scores.keys(), key=lambda k: scores[k])
            agent = self.get_agent_by_type(best_agent_type)
            if agent:
                return agent
        
        # Default to content writer if no specific match
        return self.get_agent_by_type("content_writer") or list(self.agents.values())[0]
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        workflow = self.active_workflows.get(workflow_id)
        return workflow.to_dict() if workflow else None
    
    async def _stats_updater(self):
        """Background task to update statistics"""
        while True:
            try:
                self.stats.update_uptime(self.start_time)
                self.stats.active_agents = len([a for a in self.agents.values() if a.status != "offline"])
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Stats updater error: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """Gracefully shutdown the workforce"""
        logger.info("🔄 Shutting down OWL Workforce...")
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        # Mark all agents as offline
        for agent in self.agents.values():
            agent.status = "offline"
        
        logger.info("✅ OWL Workforce shutdown complete")
    
    def get_agent_by_type(self, agent_type: str) -> Optional[Agent]:
        """Get the first agent of a specific type"""
        agents = [agent for agent in self.agents.values() if agent.type == agent_type]
        return agents[0] if agents else None
    
    def route_message_to_agent(self, message: str) -> Agent:
        """Route message to the most appropriate agent based on content"""
        message_lower = message.lower()
        
        # Define keywords for each agent type
        agent_keywords = {
            "content_writer": ["content", "blog", "write", "article", "copy", "story", "text"],
            "seo_analyst": ["seo", "keyword", "search", "ranking", "optimize", "google"],
            "social_media_manager": ["social", "twitter", "facebook", "instagram", "post", "schedule"],
            "marketing_strategist": ["strategy", "campaign", "plan", "market", "competitor", "analysis"],
            "data_analyst": ["data", "analytics", "metrics", "report", "performance", "numbers"]
        }
        
        # Score each agent type based on keyword matches
        scores = {}
        for agent_type, keywords in agent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[agent_type] = score
        
        # Choose the agent type with the highest score
        if scores:
            best_agent_type = max(scores.keys(), key=lambda k: scores[k])
            agent = self.get_agent_by_type(best_agent_type)
            if agent:
                return agent
        
        # Default to content writer if no specific match
        return self.get_agent_by_type("content_writer") or list(self.agents.values())[0]


# Add execute_task method to Agent class
async def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task and return results"""
    try:
        self.status = "busy"
        self.last_active = datetime.utcnow()
        
        # Simulate task processing based on agent type
        user_message = task_spec.get("inputs", {}).get("user_message", "")
        
        # Generate response based on agent type and capabilities
        if self.type == "content_writer":
            response = f"As a Content Writer, I can help you create engaging content! For your request about '{user_message}', I'd recommend focusing on storytelling and clear messaging. I can assist with blog posts, articles, copywriting, and creative content that resonates with your audience."
        elif self.type == "seo_analyst":
            response = f"As an SEO Specialist, I'll help optimize your content for search engines! Regarding '{user_message}', I can perform keyword research, analyze your content for SEO best practices, and suggest improvements to boost your search rankings."
        elif self.type == "social_media_manager":
            response = f"As your Social Media Manager, I'll help you engage your audience across platforms! For '{user_message}', I can create social media strategies, schedule posts, manage community engagement, and optimize your social presence."
        elif self.type == "marketing_strategist":
            response = f"As a Marketing Strategist, I'll help you develop comprehensive marketing plans! Regarding '{user_message}', I can analyze your market, plan campaigns, study competitors, and create strategies that drive results."
        elif self.type == "data_analyst":
            response = f"As a Data Analyst, I'll help you make data-driven decisions! For '{user_message}', I can analyze your marketing metrics, create reports, track performance, and provide insights to optimize your campaigns."
        else:
            response = f"Hello! I'm here to help with your marketing needs. How can I assist you with '{user_message}'?"
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        self.status = "idle"
        
        return {
            "response": response,
            "duration": 0.5,
            "confidence": 0.95,
            "suggestions": [
                "Would you like me to create a detailed plan?",
                "I can provide specific examples if helpful",
                "Let me know if you need follow-up assistance"
            ]
        }
        
    except Exception as e:
        self.status = "error"
        return {
            "response": "I apologize, but I encountered an error processing your request. Please try again.",
            "error": str(e),
            "duration": 0,
            "confidence": 0.1
        }

# Monkey patch the execute_task method to the Agent class
Agent.execute_task = execute_task 