"""
AI Manager

Central manager for AI model operations, integrating with the multi-agent system.
Provides failover, load balancing, and intelligent model selection.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta

from .model_interface import (
    AIModelInterface, ModelRegistry, ModelSelector, TokenTracker,
    ModelProvider, ModelConfig, TokenUsage
)
from .providers.ollama_model import OllamaManager, ensure_ollama_model
from .providers.openrouter_model import get_openrouter_model_configs


logger = logging.getLogger(__name__)


@dataclass
class ModelHealth:
    """Track model health status."""
    model_name: str
    is_healthy: bool
    last_check: datetime
    failure_count: int = 0
    avg_response_time: float = 0.0


class ModelFallbackChain:
    """Implements fallback chain for model reliability."""
    
    def __init__(self, primary_model: str, fallback_models: List[str]):
        self.primary_model = primary_model
        self.fallback_models = fallback_models
        self.health_tracker: Dict[str, ModelHealth] = {}
    
    async def execute(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute request with fallback support."""
        
        models_to_try = [self.primary_model] + self.fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                # Check model health first
                if not await self._is_model_healthy(model_name):
                    logger.warning(f"Skipping unhealthy model: {model_name}")
                    continue
                
                # Check budget
                if not TokenTracker.check_budget(model_name):
                    logger.warning(f"Model {model_name} over budget, skipping")
                    continue
                
                start_time = datetime.now()
                model = ModelRegistry.get_model(model_name)
                result = await model.generate(prompt, max_tokens, temperature, **kwargs)
                
                # Update health tracking
                response_time = (datetime.now() - start_time).total_seconds()
                await self._update_model_health(model_name, True, response_time)
                
                # Track token usage
                if "usage" in result:
                    TokenTracker.update_usage(model_name, result["usage"])
                
                logger.info(f"Successfully generated response using {model_name}")
                return result
                
            except Exception as e:
                last_error = e
                await self._update_model_health(model_name, False)
                logger.warning(f"Model {model_name} failed: {str(e)}")
                continue
        
        raise Exception(f"All models in fallback chain failed. Last error: {last_error}")
    
    async def execute_stream(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming request with fallback support."""
        
        models_to_try = [self.primary_model] + self.fallback_models
        last_error = None
        
        for model_name in models_to_try:
            try:
                # Check model health and budget
                if not await self._is_model_healthy(model_name):
                    continue
                
                if not TokenTracker.check_budget(model_name):
                    continue
                
                model = ModelRegistry.get_model(model_name)
                async for chunk in model.generate_stream(prompt, max_tokens, temperature, **kwargs):
                    yield chunk
                
                # Update health on successful completion
                await self._update_model_health(model_name, True)
                return
                
            except Exception as e:
                last_error = e
                await self._update_model_health(model_name, False)
                logger.warning(f"Streaming model {model_name} failed: {str(e)}")
                continue
        
        raise Exception(f"All streaming models in fallback chain failed. Last error: {last_error}")
    
    async def _is_model_healthy(self, model_name: str) -> bool:
        """Check if a model is healthy."""
        if model_name not in self.health_tracker:
            return True  # Assume healthy if not tracked yet
        
        health = self.health_tracker[model_name]
        
        # If recently checked and healthy, return cached result
        if (datetime.now() - health.last_check) < timedelta(minutes=5) and health.is_healthy:
            return True
        
        # If failure count is too high, consider unhealthy
        if health.failure_count >= 3:
            return False
        
        return health.is_healthy
    
    async def _update_model_health(self, model_name: str, success: bool, response_time: float = 0.0):
        """Update model health tracking."""
        if model_name not in self.health_tracker:
            self.health_tracker[model_name] = ModelHealth(
                model_name=model_name,
                is_healthy=True,
                last_check=datetime.now(),
                failure_count=0,
                avg_response_time=0.0
            )
        
        health = self.health_tracker[model_name]
        health.last_check = datetime.now()
        
        if success:
            health.is_healthy = True
            health.failure_count = max(0, health.failure_count - 1)  # Decrease failure count on success
            if response_time > 0:
                # Update average response time (simple moving average)
                health.avg_response_time = (health.avg_response_time + response_time) / 2
        else:
            health.failure_count += 1
            if health.failure_count >= 3:
                health.is_healthy = False


class AIManager:
    """Central AI manager for the multi-agent system."""
    
    def __init__(self):
        self.fallback_chains: Dict[str, ModelFallbackChain] = {}
        self.ollama_manager = OllamaManager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the AI manager."""
        if self._initialized:
            return
        
        try:
            # Register additional model configurations
            await self._register_additional_models()
            
            # Setup default fallback chains
            await self._setup_fallback_chains()
            
            # Check Ollama availability
            await self._check_ollama_setup()
            
            self._initialized = True
            logger.info("AI Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Manager: {e}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        task_type: str = "general",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        prefer_local: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using intelligent model selection."""
        
        if not self._initialized:
            await self.initialize()
        
        # Select appropriate model based on task type and preferences
        model_name = ModelSelector.select_for_task(
            task_type=task_type,
            content_length=len(prompt),
            local_preference=prefer_local
        )
        
        # Get fallback chain for this task type
        chain = await self._get_fallback_chain(task_type, model_name)
        
        # Execute with fallback support
        return await chain.execute(prompt, max_tokens, temperature, **kwargs)
    
    async def generate_stream(
        self,
        prompt: str,
        task_type: str = "general",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        prefer_local: bool = False,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response."""
        
        if not self._initialized:
            await self.initialize()
        
        model_name = ModelSelector.select_for_task(
            task_type=task_type,
            content_length=len(prompt),
            local_preference=prefer_local
        )
        
        chain = await self._get_fallback_chain(task_type, model_name)
        
        async for chunk in chain.execute_stream(prompt, max_tokens, temperature, **kwargs):
            yield chunk
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models by provider."""
        result = {}
        
        for provider in ModelProvider:
            models = ModelRegistry.get_models_by_provider(provider)
            if models:
                result[provider.value] = models
        
        return result
    
    async def get_model_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered models."""
        status = {}
        
        for model_name in ModelRegistry.list_models():
            try:
                model = ModelRegistry.get_model(model_name)
                is_healthy = await model.health_check()
                usage = TokenTracker.get_usage(model_name)
                
                status[model_name] = {
                    "healthy": is_healthy,
                    "provider": model.provider.value,
                    "usage": {
                        "total_tokens": usage.total_tokens,
                        "estimated_cost": usage.estimated_cost
                    }
                }
            except Exception as e:
                status[model_name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        return status
    
    async def install_ollama_model(self, model_name: str) -> bool:
        """Install an Ollama model."""
        return await self.ollama_manager.pull_model(model_name)
    
    async def list_ollama_models(self) -> List[Dict[str, Any]]:
        """List available Ollama models."""
        return await self.ollama_manager.list_available_models()
    
    async def _register_additional_models(self):
        """Register additional model configurations."""
        
        # Register OpenRouter models
        for config in get_openrouter_model_configs():
            ModelRegistry.register_config(config)
        
        # Check and register available Ollama models
        if await self.ollama_manager.is_running():
            available_models = await self.ollama_manager.list_available_models()
            for model_info in available_models:
                model_name = model_info["name"]
                # Register if not already configured
                if f"ollama-{model_name}" not in ModelRegistry.list_models():
                    from .model_interface import ModelCapabilities
                    config = ModelConfig(
                        name=f"ollama-{model_name}",
                        provider=ModelProvider.OLLAMA,
                        model_id=model_name,
                        capabilities=ModelCapabilities(
                            max_tokens=4096,  # Default
                            supports_streaming=True,
                            supports_functions=False,
                            supports_vision=False,
                            cost_per_1k_tokens=0.0,
                            performance_score=6.0
                        ),
                        is_local=True
                    )
                    ModelRegistry.register_config(config)
    
    async def _setup_fallback_chains(self):
        """Setup default fallback chains for different task types."""
        
        # Content generation chain: prefer quality models
        self.fallback_chains["content_generation"] = ModelFallbackChain(
            primary_model="gpt-4",
            fallback_models=["claude-3-sonnet", "openrouter-gpt-4", "gpt-3.5-turbo", "ollama-llama2"]
        )
        
        # Code generation chain: prefer code-focused models
        self.fallback_chains["code_generation"] = ModelFallbackChain(
            primary_model="gpt-4",
            fallback_models=["openrouter-claude-3-sonnet", "gpt-3.5-turbo", "ollama-mistral"]
        )
        
        # Analysis chain: balance of performance and cost
        self.fallback_chains["analysis"] = ModelFallbackChain(
            primary_model="claude-3-sonnet",
            fallback_models=["gpt-4", "openrouter-mixtral-8x7b", "gpt-3.5-turbo", "ollama-llama2"]
        )
        
        # General/default chain: cost-effective options
        self.fallback_chains["general"] = ModelFallbackChain(
            primary_model="gpt-3.5-turbo",
            fallback_models=["openrouter-gemini-pro", "ollama-llama2", "ollama-mistral"]
        )
    
    async def _get_fallback_chain(self, task_type: str, preferred_model: str) -> ModelFallbackChain:
        """Get or create fallback chain for task type."""
        
        if task_type in self.fallback_chains:
            return self.fallback_chains[task_type]
        
        # Create dynamic chain with preferred model as primary
        available_models = ModelRegistry.list_models()
        fallback_models = [m for m in available_models if m != preferred_model][:3]  # Limit to 3 fallbacks
        
        return ModelFallbackChain(
            primary_model=preferred_model,
            fallback_models=fallback_models
        )
    
    async def _check_ollama_setup(self):
        """Check and setup Ollama if available."""
        
        if not await self.ollama_manager.is_running():
            logger.info("Ollama not running - local models not available")
            return
        
        # Check if we have any Ollama models
        available_models = await self.ollama_manager.list_available_models()
        if not available_models:
            logger.info("No Ollama models found - attempting to install recommended model")
            
            # Try to install a basic model
            success = await ensure_ollama_model("llama2")
            if success:
                logger.info("Successfully installed llama2 model")
            else:
                logger.warning("Failed to install default Ollama model")

    async def get_ollama_status(self) -> Dict[str, Any]:
        """Get Ollama service status and model statistics."""
        try:
            models = await self.list_ollama_models()
            total_size = sum(m.get("size", 0) for m in models)
            
            return {
                "total_models": len(models),
                "active_models": len([m for m in models if m.get("status") == "ready"]),
                "total_size": f"{total_size / (1024**3):.2f} GB",
                "service_status": "online" if models else "offline"
            }
        except Exception as e:
            logger.error(f"Failed to get Ollama status: {e}")
            return {
                "total_models": 0,
                "active_models": 0,
                "total_size": "0 GB",
                "service_status": "error"
            }

    async def check_ollama_health(self) -> bool:
        """Check if Ollama service is healthy."""
        try:
            return await self.ollama_manager.is_running()
        except Exception as e:
            logger.error(f"Failed to check Ollama health: {e}")
            return False

    async def get_ollama_metrics(self) -> Dict[str, Any]:
        """Get Ollama performance metrics."""
        try:
            # This would typically come from a metrics collection system
            # For now, return mock data
            return {
                "avg_response_time": 1500,  # ms
                "requests_per_minute": 12,
                "error_rate": 2.5,  # percentage
                "memory_usage": "2.1 GB",
                "cpu_usage": "15%",
                "gpu_usage": "0%"
            }
        except Exception as e:
            logger.error(f"Failed to get Ollama metrics: {e}")
            return {}

    async def get_model_recommendations(self, task_type: str) -> List[Dict[str, Any]]:
        """Get model recommendations based on task type."""
        try:
            recommendations = []
            
            if task_type == "coding":
                recommendations = [
                    {"name": "codellama:7b", "score": 9.2, "reason": "Excellent for code generation and debugging"},
                    {"name": "llama3.1:8b", "score": 8.8, "reason": "Strong general coding capabilities"},
                    {"name": "mixtral:8x7b", "score": 8.5, "reason": "Good for complex reasoning tasks"}
                ]
            elif task_type == "content":
                recommendations = [
                    {"name": "llama3.1:8b", "score": 9.0, "reason": "Excellent for creative writing and content generation"},
                    {"name": "mixtral:8x7b", "score": 8.8, "reason": "Strong for structured content creation"},
                    {"name": "gemma:2b", "score": 8.2, "reason": "Fast and efficient for simple content tasks"}
                ]
            elif task_type == "analysis":
                recommendations = [
                    {"name": "mixtral:8x7b", "score": 9.1, "reason": "Excellent reasoning and analysis capabilities"},
                    {"name": "llama3.1:8b", "score": 8.9, "reason": "Strong analytical thinking"},
                    {"name": "phi-2", "score": 8.0, "reason": "Good for mathematical and logical tasks"}
                ]
            else:  # general
                recommendations = [
                    {"name": "llama3.1:8b", "score": 9.0, "reason": "Best overall performance and versatility"},
                    {"name": "mixtral:8x7b", "score": 8.8, "reason": "Excellent for complex multi-step tasks"},
                    {"name": "gemma:2b", "score": 8.0, "reason": "Fast and efficient for simple content tasks"}
                ]
            
            return recommendations
        except Exception as e:
            logger.error(f"Failed to get model recommendations: {e}")
            return []

    async def remove_ollama_model(self, model_name: str) -> bool:
        """Remove an Ollama model."""
        try:
            return await self.ollama_manager.remove_model(model_name)
        except Exception as e:
            logger.error(f"Failed to remove Ollama model '{model_name}': {e}")
            return False

# Global AI manager instance
ai_manager = AIManager()
