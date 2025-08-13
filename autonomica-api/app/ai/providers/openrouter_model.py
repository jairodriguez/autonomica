"""
OpenRouter Model Provider

Provides integration with OpenRouter which gives access to multiple AI models
through a single API including Claude, GPT, Gemini, Llama, Mistral, and more.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx

from ..model_interface import AIModelInterface, ModelConfig, TokenUsage


logger = logging.getLogger(__name__)


class OpenRouterModel(AIModelInterface):
    """OpenRouter model implementation for accessing multiple AI providers."""
    
    def __init__(self, config: ModelConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self.api_key = api_key or config.api_key
        self.base_url = config.base_url or "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://autonomica.app",  # Your app URL
                "X-Title": "Autonomica Multi-Agent System"
            },
            timeout=30.0
        )
    
    async def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text completion using OpenRouter."""
        
        payload = {
            "model": self.config.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        # Add any additional parameters
        payload.update(kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract usage information
            usage_data = result.get("usage", {})
            usage = TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
                estimated_cost=self._calculate_cost(usage_data)
            )
            
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result.get("model", self.config.model_id),
                "usage": usage,
                "metadata": {
                    "finish_reason": result["choices"][0].get("finish_reason"),
                    "created": result.get("created"),
                    "id": result.get("id"),
                    "provider": self._extract_provider_from_model()
                }
            }
            
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {e}")
            raise
    
    async def generate_stream(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text completion using OpenRouter."""
        
        payload = {
            "model": self.config.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            
                            if "content" in delta:
                                yield {
                                    "content": delta["content"],
                                    "done": False,
                                    "model": chunk.get("model", self.config.model_id),
                                    "metadata": {
                                        "id": chunk.get("id"),
                                        "created": chunk.get("created"),
                                        "provider": self._extract_provider_from_model()
                                    }
                                }
                        except json.JSONDecodeError:
                            continue
                
                # Signal completion
                yield {
                    "content": "",
                    "done": True,
                    "model": self.config.model_id
                }
                
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            raise
    
    def _extract_provider_from_model(self) -> str:
        """Extract the actual provider from OpenRouter model ID."""
        # OpenRouter models are typically in format: provider/model
        # e.g., "anthropic/claude-2", "openai/gpt-4", "meta-llama/llama-2-70b-chat"
        if "/" in self.config.model_id:
            return self.config.model_id.split("/")[0]
        return "unknown"
    
    def _calculate_cost(self, usage_data: Dict[str, Any]) -> float:
        """Calculate estimated cost based on token usage."""
        # OpenRouter provides actual cost information when available
        if "cost" in usage_data:
            return float(usage_data["cost"])
        
        # Fallback to estimated cost
        total_tokens = usage_data.get("total_tokens", 0)
        return (total_tokens / 1000) * self.config.capabilities.cost_per_1k_tokens
    
    async def health_check(self) -> bool:
        """Check if OpenRouter API is accessible."""
        try:
            # Check models endpoint
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"OpenRouter health check failed: {e}")
            return False
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter."""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to get OpenRouter models: {e}")
            return []


# Common OpenRouter model configurations
def get_openrouter_model_configs() -> List[ModelConfig]:
    """Get pre-configured OpenRouter model configurations with latest cost-effective options."""
    from ..model_interface import ModelConfig, ModelProvider, ModelCapabilities
    
    return [
        # **2024-2025 Latest Models - High Performance, Cost-Effective**
        
        # Claude 3.5 Sonnet (Anthropic) - Best overall performance/cost ratio
        ModelConfig(
            name="openrouter-claude-3-5-sonnet",
            provider=ModelProvider.OPENROUTER,
            model_id="anthropic/claude-3-5-sonnet",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                cost_per_1k_tokens=0.003,  # Much cheaper than before!
                performance_score=9.8
            )
        ),
        
        # Claude 3 Haiku (Anthropic) - Fast and efficient
        ModelConfig(
            name="openrouter-claude-3-haiku",
            provider=ModelProvider.OPENROUTER,
            model_id="anthropic/claude-3-haiku",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                cost_per_1k_tokens=0.00025,  # Extremely cost-effective
                performance_score=9.2
            )
        ),
        
        # GPT-4o Mini (OpenAI) - Latest GPT model, very cost-effective
        ModelConfig(
            name="openrouter-gpt-4o-mini",
            provider=ModelProvider.OPENROUTER,
            model_id="openai/gpt-4o-mini",
            capabilities=ModelCapabilities(
                max_tokens=128000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                cost_per_1k_tokens=0.00015,  # Incredibly cheap for GPT-4 level
                performance_score=9.5
            )
        ),
        
        # **Open Source Powerhouses - Excellent Performance/Cost Ratio**
        
        # LLaMA 3.1 8B (Meta) - Newest LLaMA, excellent performance
        ModelConfig(
            name="openrouter-llama-3-1-8b",
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
        ),
        
        # LLaMA 3.1 70B (Meta) - High performance, reasonable cost
        ModelConfig(
            name="openrouter-llama-3-1-70b",
            provider=ModelProvider.OPENROUTER,
            model_id="meta-llama/llama-3.1-70b-instruct",
            capabilities=ModelCapabilities(
                max_tokens=8192,
                supports_streaming=True,
                supports_functions=False,
                supports_vision=False,
                cost_per_1k_tokens=0.0007,  # Very cost-effective for 70B model
                performance_score=9.3
            )
        ),
        
        # Mixtral 8x22B (Mistral) - Latest Mixtral, excellent reasoning
        ModelConfig(
            name="openrouter-mixtral-8x22b",
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
        ),
        
        # **Specialized Models - Task-Specific Excellence**
        
        # CodeLlama 3.1 34B (Meta) - Best coding performance
        ModelConfig(
            name="openrouter-codellama-3-1-34b",
            provider=ModelProvider.OPENROUTER,
            model_id="meta-llama/codellama-3.1-34b-instruct",
            capabilities=ModelCapabilities(
                max_tokens=16384,
                supports_streaming=True,
                supports_functions=False,
                supports_vision=False,
                cost_per_1k_tokens=0.0005,  # Excellent for coding tasks
                performance_score=9.4
            )
        ),
        
        # Phi-3.5 14B (Microsoft) - Fast, efficient, great reasoning
        ModelConfig(
            name="openrouter-phi-3-5-14b",
            provider=ModelProvider.OPENROUTER,
            model_id="microsoft/phi-3.5-14b-instruct",
            capabilities=ModelCapabilities(
                max_tokens=16384,
                supports_streaming=True,
                supports_functions=False,
                supports_vision=False,
                cost_per_1k_tokens=0.0003,  # Very cost-effective
                performance_score=8.9
            )
        ),
        
        # **Ultra-Cost-Effective Options - High Volume Tasks**
        
        # Gemma 2 27B (Google) - Excellent performance/cost ratio
        ModelConfig(
            name="openrouter-gemma-2-27b",
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
        ),
        
        # Qwen2.5 32B (Alibaba) - Strong performance, very cheap
        ModelConfig(
            name="openrouter-qwen2-5-32b",
            provider=ModelProvider.OPENROUTER,
            model_id="qwen/qwen2.5-32b-instruct",
            capabilities=ModelCapabilities(
                max_tokens=32768,
                supports_streaming=True,
                supports_functions=False,
                supports_vision=False,
                cost_per_1k_tokens=0.00015,  # Incredibly cheap
                performance_score=8.7
            )
        ),
        
        # **Legacy Models - Still Good, Higher Cost**
        
        # GPT-4 Turbo (OpenAI) - When you need the absolute best
        ModelConfig(
            name="openrouter-gpt-4-turbo",
            provider=ModelProvider.OPENROUTER,
            model_id="openai/gpt-4-turbo",
            capabilities=ModelCapabilities(
                max_tokens=128000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                cost_per_1k_tokens=0.01,  # Higher cost but top performance
                performance_score=9.9
            )
        ),
        
        # Claude 3 Opus (Anthropic) - Maximum performance
        ModelConfig(
            name="openrouter-claude-3-opus",
            provider=ModelProvider.OPENROUTER,
            model_id="anthropic/claude-3-opus",
            capabilities=ModelCapabilities(
                max_tokens=200000,
                supports_streaming=True,
                supports_functions=True,
                supports_vision=True,
                cost_per_1k_tokens=0.015,  # Premium pricing
                performance_score=10.0
            )
        )
    ]
