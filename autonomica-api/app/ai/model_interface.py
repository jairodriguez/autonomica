"""
Unified AI Model Interface and Registry System

This module provides a unified interface for interacting with different AI models
and providers, enabling seamless switching between OpenAI, Anthropic, Google AI,
OpenRouter, and Ollama.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


@dataclass
class TokenUsage:
    """Token usage tracking for cost optimization."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float = 0.0


@dataclass
class ModelCapabilities:
    """Define capabilities of different AI models."""
    max_tokens: int
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool
    cost_per_1k_tokens: float
    performance_score: float  # 1-10 scale


@dataclass
class ModelConfig:
    """Configuration for AI models."""
    name: str
    provider: ModelProvider
    model_id: str
    capabilities: ModelCapabilities
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_local: bool = False


class AIModelInterface(ABC):
    """Abstract base class for all AI model implementations."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = config.name
        self.provider = config.provider
        
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        """Generate streaming text completion."""
        pass
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings (optional for models that support it)."""
        raise NotImplementedError("Embeddings not supported by this model")
    
    async def health_check(self) -> bool:
        """Check if the model is available and healthy."""
        try:
            response = await self.generate("Test", max_tokens=1)
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False


class ModelRegistry:
    """Registry for managing AI model instances."""
    
    _models: Dict[str, AIModelInterface] = {}
    _configs: Dict[str, ModelConfig] = {}
    
    @classmethod
    def register_config(cls, config: ModelConfig):
        """Register a model configuration."""
        cls._configs[config.name] = config
        logger.info(f"Registered model config: {config.name}")
    
    @classmethod
    def create_model(cls, name: str, **kwargs) -> AIModelInterface:
        """Create a model instance by name."""
        if name not in cls._configs:
            raise ValueError(f"Unknown model: {name}")
        
        config = cls._configs[name]
        
        # Import the appropriate model class based on provider
        if config.provider == ModelProvider.OPENAI:
            from .providers.openai_model import OpenAIModel
            return OpenAIModel(config, **kwargs)
        elif config.provider == ModelProvider.ANTHROPIC:
            from .providers.anthropic_model import AnthropicModel
            return AnthropicModel(config, **kwargs)
        elif config.provider == ModelProvider.GOOGLE:
            from .providers.google_model import GoogleModel
            return GoogleModel(config, **kwargs)
        elif config.provider == ModelProvider.OPENROUTER:
            from .providers.openrouter_model import OpenRouterModel
            return OpenRouterModel(config, **kwargs)
        elif config.provider == ModelProvider.OLLAMA:
            from .providers.ollama_model import OllamaModel
            return OllamaModel(config, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    @classmethod
    def get_model(cls, name: str) -> AIModelInterface:
        """Get or create a model instance."""
        if name not in cls._models:
            cls._models[name] = cls.create_model(name)
        return cls._models[name]
    
    @classmethod
    def list_models(cls) -> List[str]:
        """List all registered model names."""
        return list(cls._configs.keys())
    
    @classmethod
    def get_models_by_provider(cls, provider: ModelProvider) -> List[str]:
        """Get all model names for a specific provider."""
        return [
            name for name, config in cls._configs.items() 
            if config.provider == provider
        ]
    
    @classmethod
    def clear_cache(cls):
        """Clear the model instance cache."""
        cls._models.clear()


class TokenTracker:
    """Track token usage across all models for cost optimization."""
    
    _usage: Dict[str, TokenUsage] = {}
    _budgets: Dict[str, int] = {}
    
    @classmethod
    def update_usage(cls, model_name: str, usage: TokenUsage):
        """Update token usage for a model."""
        if model_name not in cls._usage:
            cls._usage[model_name] = TokenUsage(0, 0, 0, 0.0)
        
        current = cls._usage[model_name]
        current.prompt_tokens += usage.prompt_tokens
        current.completion_tokens += usage.completion_tokens
        current.total_tokens += usage.total_tokens
        current.estimated_cost += usage.estimated_cost
    
    @classmethod
    def get_usage(cls, model_name: str) -> TokenUsage:
        """Get token usage for a model."""
        return cls._usage.get(model_name, TokenUsage(0, 0, 0, 0.0))
    
    @classmethod
    def set_budget(cls, model_name: str, max_tokens: int):
        """Set token budget for a model."""
        cls._budgets[model_name] = max_tokens
    
    @classmethod
    def check_budget(cls, model_name: str) -> bool:
        """Check if model is within budget."""
        if model_name not in cls._budgets:
            return True
        
        usage = cls.get_usage(model_name)
        return usage.total_tokens < cls._budgets[model_name]
    
    @classmethod
    def get_total_cost(cls) -> float:
        """Get total estimated cost across all models."""
        return sum(usage.estimated_cost for usage in cls._usage.values())


class ModelSelector:
    """Intelligent model selection based on task requirements."""
    
    @staticmethod
    def select_for_task(
        task_type: str,
        content_length: int = 0,
        budget_priority: bool = False,
        performance_priority: bool = False,
        local_preference: bool = False
    ) -> str:
        """Select the best model for a specific task."""
        
        available_models = ModelRegistry.list_models()
        if not available_models:
            raise ValueError("No models registered")
        
        # Filter models based on requirements
        candidates = []
        for model_name in available_models:
            config = ModelRegistry._configs[model_name]
            
            # Check budget
            if not TokenTracker.check_budget(model_name):
                continue
            
            # Local preference
            if local_preference and not config.is_local:
                continue
            
            # Content length check
            if content_length > config.capabilities.max_tokens:
                continue
            
            candidates.append((model_name, config))
        
        if not candidates:
            # Fallback to any available model
            return available_models[0]
        
        # Score models based on criteria
        def score_model(model_name: str, config: ModelConfig) -> float:
            score = config.capabilities.performance_score
            
            if budget_priority:
                # Lower cost = higher score
                score += (1.0 / max(config.capabilities.cost_per_1k_tokens, 0.001)) * 0.1
            
            if performance_priority:
                score += config.capabilities.performance_score * 0.5
            
            if local_preference and config.is_local:
                score += 2.0
            
            return score
        
        # Select highest scoring model
        best_model = max(candidates, key=lambda x: score_model(x[0], x[1]))
        return best_model[0]


# Initialize default model configurations
def initialize_default_models():
    """Initialize default model configurations with latest cost-effective options."""
    
    # **2024-2025 Latest Models - High Performance, Cost-Effective**
    
    # OpenAI models - Latest and most cost-effective
    ModelRegistry.register_config(ModelConfig(
        name="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o-mini",
        capabilities=ModelCapabilities(
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.00015,  # Incredibly cheap for GPT-4 level
            performance_score=9.5
        )
    ))
    
    ModelRegistry.register_config(ModelConfig(
        name="gpt-4o",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        capabilities=ModelCapabilities(
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.005,  # Much cheaper than GPT-4
            performance_score=9.8
        )
    ))
    
    # Anthropic models - Latest Claude versions
    ModelRegistry.register_config(ModelConfig(
        name="claude-3-5-sonnet",
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-5-sonnet",
        capabilities=ModelCapabilities(
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.003,  # Much cheaper than before!
            performance_score=9.8
        )
    ))
    
    ModelRegistry.register_config(ModelConfig(
        name="claude-3-haiku",
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-haiku",
        capabilities=ModelCapabilities(
            max_tokens=200000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.00025,  # Extremely cost-effective
            performance_score=9.2
        )
    ))
    
    # **Open Source Powerhouses - Excellent Performance/Cost Ratio**
    
    # LLaMA 3.1 8B (Meta) - Newest LLaMA, excellent performance
    ModelRegistry.register_config(ModelConfig(
        name="llama-3-1-8b",
        provider=ModelProvider.OPENROUTER,
        model_id="meta-llama/llama-3.1-8b-instruct",
        capabilities=ModelCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            cost_per_1k_tokens=0.0002,  # Extremely cheap
            performance_score=8.8
        )
    ))
    
    # Mixtral 8x22B (Mistral) - Latest Mixtral, excellent reasoning
    ModelRegistry.register_config(ModelConfig(
        name="mixtral-8x22b",
        provider=ModelProvider.OPENROUTER,
        model_id="mistralai/mixtral-8x22b-instruct",
        capabilities=ModelCapabilities(
            max_tokens=65536,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            cost_per_1k_tokens=0.0004,  # Great value for 22B model
            performance_score=9.1
        )
    ))
    
    # **Ultra-Cost-Effective Options - High Volume Tasks**
    
    # Gemma 2 27B (Google) - Excellent performance/cost ratio
    ModelRegistry.register_config(ModelConfig(
        name="gemma-2-27b",
        provider=ModelProvider.OPENROUTER,
        model_id="google/gemma-2-27b-it",
        capabilities=ModelCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            cost_per_1k_tokens=0.0001,  # Extremely cheap
            performance_score=8.5
        )
    ))
    
    # **Ollama models (local) - Zero cost, privacy-focused**
    ModelRegistry.register_config(ModelConfig(
        name="ollama-llama3-1-8b",
        provider=ModelProvider.OLLAMA,
        model_id="llama3.1:8b",
        capabilities=ModelCapabilities(
            max_tokens=8192,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            cost_per_1k_tokens=0.0,  # Local = free
            performance_score=8.5
        ),
        is_local=True
    ))
    
    ModelRegistry.register_config(ModelConfig(
        name="ollama-mixtral-8x7b",
        provider=ModelProvider.OLLAMA,
        model_id="mixtral:8x7b",
        capabilities=ModelCapabilities(
            max_tokens=32768,
            supports_streaming=True,
            supports_functions=False,
            supports_vision=False,
            cost_per_1k_tokens=0.0,
            performance_score=8.0
        ),
        is_local=True
    ))
    
    # **Legacy Models - Still Good, Higher Cost (for comparison)**
    ModelRegistry.register_config(ModelConfig(
        name="gpt-4-turbo",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4-turbo",
        capabilities=ModelCapabilities(
            max_tokens=128000,
            supports_streaming=True,
            supports_functions=True,
            supports_vision=True,
            cost_per_1k_tokens=0.01,  # Higher cost but top performance
            performance_score=9.9
        )
    ))


# Initialize on import
initialize_default_models()
