"""
Ollama Model Implementation

Provides Ollama model integration with performance monitoring and enhanced metrics collection.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass

import httpx

from ..model_interface import AIModelInterface, ModelConfig, TokenUsage
from ..ollama_performance_monitor import ollama_performance_monitor

logger = logging.getLogger(__name__)

@dataclass
class OllamaModelConfig(ModelConfig):
    """Configuration for Ollama models."""
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    seed: Optional[int] = None
    num_ctx: Optional[int] = None
    num_gpu: Optional[int] = None
    num_thread: Optional[int] = None
    stop: Optional[List[str]] = None

class OllamaModel(AIModelInterface):
    """Ollama model implementation with performance monitoring."""
    
    def __init__(self, config: OllamaModelConfig):
        super().__init__(config)
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = config.base_url
        
        # Performance monitoring integration
        self.performance_monitor = ollama_performance_monitor
        
        logger.info(f"OllamaModel initialized for {config.model_id} at {config.base_url}")

    async def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Ollama with performance monitoring."""
        start_time = time.time()
        error = None
        
        try:
            # Prepare payload with Ollama-specific options
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": kwargs.get("top_p", self.config.top_p),
                    "top_k": kwargs.get("top_k", self.config.top_k),
                    "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                    "seed": kwargs.get("seed", self.config.seed),
                    "num_ctx": kwargs.get("num_ctx", self.config.num_ctx),
                    "num_gpu": kwargs.get("num_gpu", self.config.num_gpu),
                    "num_thread": kwargs.get("num_thread", self.config.num_thread),
                    "stop": kwargs.get("stop", self.config.stop)
                }
            }
            
            # Add any additional options
            payload["options"].update(kwargs)
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract token usage (Ollama provides eval_count and prompt_eval_count)
            usage = TokenUsage(
                prompt_tokens=result.get("prompt_eval_count", 0),
                completion_tokens=result.get("eval_count", 0),
                total_tokens=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                estimated_cost=0.0  # Local models are free
            )
            
            # Collect performance metrics
            await self.performance_monitor.collect_ollama_metrics(
                self.config.model_id, result, start_time, error
            )
            
            return {
                "content": result.get("response", ""),
                "model": self.config.model_id,
                "usage": usage,
                "metadata": {
                    "eval_duration": result.get("eval_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_duration": result.get("prompt_eval_duration"),
                    "total_duration": result.get("total_duration"),
                }
            }
            
        except Exception as e:
            error = str(e)
            logger.error(f"Ollama generation failed: {e}")
            
            # Collect error metrics
            await self.performance_monitor.collect_ollama_metrics(
                self.config.model_id, {}, start_time, error
            )
            
            raise

    async def generate_stream(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text using Ollama with performance monitoring."""
        start_time = time.time()
        error = None
        accumulated_response = ""
        total_tokens = 0
        
        try:
            # Prepare payload for streaming
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "top_p": kwargs.get("top_p", self.config.top_p),
                    "top_k": kwargs.get("top_k", self.config.top_k),
                    "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                    "seed": kwargs.get("seed", self.config.seed),
                    "num_ctx": kwargs.get("num_ctx", self.config.num_ctx),
                    "num_gpu": kwargs.get("num_gpu", self.config.num_gpu),
                    "num_thread": kwargs.get("num_thread", self.config.num_thread),
                    "stop": kwargs.get("stop", self.config.stop)
                }
            }
            
            # Add any additional options
            payload["options"].update(kwargs)
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            
                            # Extract response text
                            if "response" in chunk:
                                accumulated_response += chunk["response"]
                                total_tokens += 1
                            
                            # Check if generation is complete
                            if chunk.get("done", False):
                                # Final chunk contains complete metrics
                                final_metrics = {
                                    "response": accumulated_response,
                                    "eval_count": chunk.get("eval_count", total_tokens),
                                    "prompt_eval_count": chunk.get("prompt_eval_count", 0),
                                    "eval_duration": chunk.get("eval_duration"),
                                    "load_duration": chunk.get("load_duration"),
                                    "prompt_eval_duration": chunk.get("prompt_eval_duration"),
                                    "total_duration": chunk.get("total_duration"),
                                    "temperature": temperature,
                                    "top_p": kwargs.get("top_p", self.config.top_p)
                                }
                                
                                # Collect final performance metrics
                                await self.performance_monitor.collect_ollama_metrics(
                                    self.config.model_id, final_metrics, start_time, error
                                )
                                break
                            
                            # Yield streaming chunk
                            yield {
                                "content": chunk.get("response", ""),
                                "model": self.config.model_id,
                                "done": chunk.get("done", False),
                                "metadata": {
                                    "eval_duration": chunk.get("eval_duration"),
                                    "load_duration": chunk.get("load_duration"),
                                    "prompt_eval_duration": chunk.get("prompt_eval_duration"),
                                    "total_duration": chunk.get("total_duration"),
                                }
                            }
                            
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            error = str(e)
            logger.error(f"Ollama streaming generation failed: {e}")
            
            # Collect error metrics
            await self.performance_monitor.collect_ollama_metrics(
                self.config.model_id, {}, start_time, error
            )
            
            raise

    async def health_check(self) -> bool:
        """Check if the Ollama service is healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed information about the model."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/show", 
                params={"name": self.config.model_id}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
        return None

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this model."""
        try:
            model_performance = self.performance_monitor.get_model_performance(self.config.model_id)
            if model_performance:
                return {
                    "model_name": model_performance.model_name,
                    "total_requests": model_performance.total_requests,
                    "successful_requests": model_performance.successful_requests,
                    "failed_requests": model_performance.failed_requests,
                    "avg_response_time_ms": model_performance.avg_response_time_ms,
                    "success_rate": model_performance.success_rate,
                    "performance_score": model_performance.performance_score,
                    "last_used": model_performance.last_used.isoformat() if model_performance.last_used else None
                }
            else:
                return {"model_name": self.config.model_id, "no_data": True}
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info(f"OllamaModel {self.config.model_id} cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up OllamaModel: {e}")

class OllamaManager:
    """Manager for Ollama operations like model installation and management."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for model operations
        
        # Performance monitoring integration
        self.performance_monitor = ollama_performance_monitor
        
        logger.info(f"OllamaManager initialized for {base_url}")

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List all models installed in Ollama."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            # Enhance model information with performance data
            enhanced_models = []
            for model in models:
                model_name = model["name"]
                performance_data = await self.performance_monitor.get_model_performance(model_name)
                
                enhanced_model = {
                    **model,
                    "performance": performance_data.to_dict() if performance_data else None,
                    "health_status": await self._check_model_health(model_name)
                }
                enhanced_models.append(enhanced_model)
            
            return enhanced_models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model to Ollama."""
        try:
            payload = {"name": model_name}
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            status = chunk.get("status", "")
                            logger.info(f"Pull progress: {status}")
                            
                            if "error" in chunk:
                                logger.error(f"Pull error: {chunk['error']}")
                                return False
                                
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"Successfully pulled model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            payload = {"name": model_name}
            response = await self.client.delete(f"{self.base_url}/api/delete", json=payload)
            response.raise_for_status()
            
            logger.info(f"Successfully deleted model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/show", 
                params={"name": model_name}
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {e}")
        return None

    async def _check_model_health(self, model_name: str) -> str:
        """Check the health status of a specific model."""
        try:
            # Try to get model info to see if it's accessible
            info = await self.get_model_info(model_name)
            if info:
                return "healthy"
            else:
                return "unavailable"
        except Exception:
            return "error"

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including performance metrics."""
        try:
            # Get basic Ollama status
            status = {
                "service_healthy": await self._check_service_health(),
                "models_count": len(await self.list_available_models()),
                "performance_summary": await self.performance_monitor.get_ollama_performance_summary()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    async def is_running(self) -> bool:
        """Check if Ollama service is running and accessible."""
        return await self._check_service_health()

    async def _check_service_health(self) -> bool:
        """Check if the Ollama service is running and healthy."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("OllamaManager cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up OllamaManager: {e}")

# Utility function to ensure Ollama model is available
async def ensure_ollama_model(model_name: str, base_url: str = "http://localhost:11434") -> bool:
    """Ensure that a specific Ollama model is available, pulling it if necessary."""
    try:
        manager = OllamaManager(base_url)
        
        # Check if model exists
        models = await manager.list_available_models()
        model_names = [m["name"] for m in models]
        
        if model_name in model_names:
            logger.info(f"Model {model_name} is already available")
            await manager.cleanup()
            return True
        
        # Pull the model
        logger.info(f"Pulling model {model_name}...")
        success = await manager.pull_model(model_name)
        
        await manager.cleanup()
        return success
        
    except Exception as e:
        logger.error(f"Failed to ensure Ollama model {model_name}: {e}")
        return False


async def get_recommended_ollama_models() -> List[str]:
    """Get a list of recommended Ollama models for different use cases."""
    return [
        "llama2",           # General purpose, good balance
        "llama2:13b",       # Better performance, more resources
        "mistral",          # Fast and efficient
        "codellama",        # Code generation
        "llama2-uncensored", # Less restricted responses
        "neural-chat",      # Conversation optimized
        "starling-lm",      # Instruction following
    ]
