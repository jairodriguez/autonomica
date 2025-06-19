"""
OWL (Optimized Workflow Language) Workforce Implementation
Simplified version for initial testing
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from loguru import logger

@dataclass 
class Agent:
    """Simplified agent for initial testing"""
    id: str
    name: str
    type: str
    custom_prompt: str
    capabilities: List[str]
    model: str
    tools: List[str] = field(default_factory=list)
    status: str = "idle"
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    last_active: datetime = field(default_factory=datetime.utcnow)
    
    # Cost tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    tasks_completed: int = 0
    
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
            "last_active": self.last_active.isoformat(),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": round(self.total_cost, 4),
            "tasks_completed": self.tasks_completed,
        }
    
    async def execute_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task - simplified version"""
        try:
            self.status = "busy"
            self.last_active = datetime.utcnow()
            
            user_message = task_spec.get("inputs", {}).get("user_message", "")
            
            # Simple response for now
            response = f"Hello! I'm {self.name}, the CEO of Autonomica. I've received your request: '{user_message}'. I'll coordinate with my team to help you with this task."
            
            self.tasks_completed += 1
            self.status = "idle"
            
            return {
                "response": response,
                "agent_name": self.name,
                "model_used": self.model,
                "task_completed": True
            }
            
        except Exception as e:
            self.status = "error"
            logger.error(f"Task execution failed for {self.name}: {e}")
            raise

class AutonomicaWorkforce:
    """Simplified workforce management system"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        
    async def initialize(self):
        """Initialize workforce with CEO agent"""
        logger.info("Initializing Autonomica Workforce...")
        
        # Create a CEO agent
        ceo_agent = Agent(
            id=str(uuid.uuid4()),
            name="CEO",
            type="ceo",
            custom_prompt="You are the CEO of Autonomica, an AI-powered marketing agency. You coordinate tasks and provide strategic leadership.",
            capabilities=["leadership", "coordination", "delegation"],
            model="gpt-4o-mini",
            tools=["search", "document_processing"],
            created_by="system"
        )
        
        self.agents[ceo_agent.id] = ceo_agent
        logger.info(f"Workforce initialized with CEO agent: {ceo_agent.id}")
        
        return ceo_agent
    
    def get_ceo_agent(self) -> Optional[Agent]:
        """Get the CEO agent"""
        for agent in self.agents.values():
            if agent.type == "ceo":
                return agent
        return None
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents"""
        return list(self.agents.values())
    
    async def delegate_task(self, task_spec: Dict[str, Any]) -> Dict[str, Any]:
        """CEO delegates task"""
        ceo = self.get_ceo_agent()
        if not ceo:
            raise ValueError("No CEO agent available for delegation")
        
        return await ceo.execute_task(task_spec)

# Global workforce instance
_workforce_instance = None

async def get_workforce() -> AutonomicaWorkforce:
    """Get or create workforce instance"""
    global _workforce_instance
    if _workforce_instance is None:
        _workforce_instance = AutonomicaWorkforce()
        await _workforce_instance.initialize()
    return _workforce_instance 