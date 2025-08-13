"""
OpenAI Model Provider

Provides integration with OpenAI's API including GPT-4, GPT-3.5-turbo, and other models.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx

from ..model_interface import AIModelInterface, ModelConfig, TokenUsage


logger = logging.getLogger(__name__)


class OpenAIModel(AIModelInterface):
    """OpenAI model implementation."""
    
    def __init__(self, config: ModelConfig, api_key: Optional[str] = None):
        super().__init__(config)
        self.api_key = api_key or config.api_key
        self.base_url = config.base_url or "https://api.openai.com/v1"
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
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
        """Generate text completion using OpenAI."""
        
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
                    "id": result.get("id")
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_stream(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text completion using OpenAI."""
        
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
                                        "created": chunk.get("created")
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
            logger.error(f"OpenAI streaming failed: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI."""
        payload = {
            "model": "text-embedding-ada-002",  # Default embedding model
            "input": text
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embeddings",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            return result["data"][0]["embedding"]
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    def _calculate_cost(self, usage_data: Dict[str, Any]) -> float:
        """Calculate estimated cost based on token usage."""
        prompt_tokens = usage_data.get("prompt_tokens", 0)
        completion_tokens = usage_data.get("completion_tokens", 0)
        
        # Use the cost per 1k tokens from model capabilities
        cost_per_1k = self.config.capabilities.cost_per_1k_tokens
        
        # Some models have different pricing for input vs output tokens
        if self.config.model_id.startswith("gpt-4"):
            # GPT-4 has different pricing for input/output
            input_cost = (prompt_tokens / 1000) * 0.03
            output_cost = (completion_tokens / 1000) * 0.06
            return input_cost + output_cost
        else:
            # Use flat rate for other models
            total_tokens = prompt_tokens + completion_tokens
            return (total_tokens / 1000) * cost_per_1k
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Simple test request
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return False
