"""
Enhanced Ollama Model Implementation

Extends the base OllamaModel with configuration persistence integration,
automatically applying user preferences, parameter presets, and project configurations.
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
from ..ollama_config_manager import (
    ollama_config_manager, ConfigType, OllamaParameterPreset
)

logger = logging.getLogger(__name__)


@dataclass
class OllamaModelConfigEnhanced(ModelConfig):
    """Enhanced configuration for Ollama models with persistence support."""
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
    
    # Configuration integration
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    team_id: Optional[str] = None
    preset_name: Optional[str] = None
    auto_apply_presets: bool = True
    auto_apply_user_preferences: bool = True
    auto_apply_project_config: bool = True


class OllamaModelEnhanced(AIModelInterface):
    """Enhanced Ollama model with configuration persistence integration."""
    
    def __init__(self, config: OllamaModelConfigEnhanced):
        super().__init__(config)
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = config.base_url
        
        # Performance monitoring integration
        self.performance_monitor = ollama_performance_monitor
        
        # Configuration manager integration
        self.config_manager = ollama_config_manager
        
        # Configuration cache
        self._user_preferences = None
        self._project_config = None
        self._team_config = None
        self._active_preset = None
        
        logger.info(f"Enhanced OllamaModel initialized for {config.model_id} at {config.base_url}")

    async def _load_user_preferences(self) -> Optional[Dict[str, Any]]:
        """Load user preferences if user_id is configured."""
        if not self.config.user_id:
            return None
        
        try:
            preferences = self.config_manager.load_user_preferences(self.config.user_id)
            if preferences:
                self._user_preferences = preferences
                logger.debug(f"Loaded user preferences for {self.config.user_id}")
                return preferences
        except Exception as e:
            logger.warning(f"Failed to load user preferences: {e}")
        
        return None

    async def _load_project_config(self) -> Optional[Dict[str, Any]]:
        """Load project configuration if project_id is configured."""
        if not self.config.project_id:
            return None
        
        try:
            project_config = self.config_manager.load_project_config(self.config.project_id)
            if project_config:
                self._project_config = project_config
                logger.debug(f"Loaded project config for {self.config.project_id}")
                return project_config
        except Exception as e:
            logger.warning(f"Failed to load project config: {e}")
        
        return None

    async def _load_team_config(self) -> Optional[Dict[str, Any]]:
        """Load team configuration if team_id is configured."""
        if not self.config.team_id:
            return None
        
        try:
            team_config = self.config_manager.load_team_config(self.config.team_id)
            if team_config:
                self._team_config = team_config
                logger.debug(f"Loaded team config for {self.config.team_id}")
                return team_config
        except Exception as e:
            logger.warning(f"Failed to load team config: {e}")
        
        return None

    async def _load_parameter_preset(self, preset_name: str) -> Optional[OllamaParameterPreset]:
        """Load parameter preset by name."""
        try:
            preset = self.config_manager.load_parameter_preset(preset_name)
            if preset:
                self._active_preset = preset
                logger.debug(f"Loaded parameter preset: {preset_name}")
                return preset
        except Exception as e:
            logger.warning(f"Failed to load parameter preset {preset_name}: {e}")
        
        return None

    async def _get_optimal_parameters(
        self, 
        task_type: str, 
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Get optimal parameters by combining configuration sources."""
        optimal_params = {
            "temperature": temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "repeat_penalty": self.config.repeat_penalty,
            "seed": self.config.seed,
            "num_ctx": self.config.num_ctx,
            "num_gpu": self.config.num_gpu,
            "num_thread": self.config.num_thread,
            "stop": self.config.stop
        }
        
        # Override with any explicitly provided parameters
        optimal_params.update(kwargs)
        
        # Apply user preferences if available
        if self.config.auto_apply_user_preferences and self._user_preferences:
            # Get task-specific model preference
            task_model = self._user_preferences.preferred_models.get(task_type)
            if task_model and task_model != self.config.model_id:
                logger.info(f"User prefers {task_model} for {task_type} tasks")
            
            # Get task-specific parameter preset
            task_preset = self._user_preferences.parameter_presets.get(task_type)
            if task_preset and not self._active_preset:
                await self._load_parameter_preset(task_preset)
        
        # Apply project configuration if available
        if self.config.auto_apply_project_config and self._project_config:
            # Check project model constraints
            if self._project_config.model_constraints:
                logger.debug(f"Applying project model constraints: {self._project_config.model_constraints}")
            
            # Get project-specific parameter preset
            project_preset = self._project_config.parameter_presets.get(task_type)
            if project_preset and not self._active_preset:
                await self._load_parameter_preset(project_preset)
        
        # Apply team configuration if available
        if self.config.auto_apply_project_config and self._team_config:
            # Check team resource limits
            if self._team_config.resource_limits:
                logger.debug(f"Applying team resource limits: {self._team_config.resource_limits}")
            
            # Get team-shared parameter preset
            team_preset = self._team_config.shared_presets.get(task_type)
            if team_preset and not self._active_preset:
                self._active_preset = team_preset
                logger.debug(f"Applied team preset: {task_type}")
        
        # Apply active parameter preset if available
        if self._active_preset:
            optimal_params.update({
                "temperature": self._active_preset.temperature,
                "top_p": self._active_preset.top_p,
                "top_k": self._active_preset.top_k,
                "repeat_penalty": self._active_preset.repeat_penalty,
                "seed": self._active_preset.seed,
                "num_ctx": self._active_preset.num_ctx,
                "num_gpu": self._active_preset.num_gpu,
                "num_thread": self._active_preset.num_thread,
                "stop": self._active_preset.stop
            })
            
            # Increment usage count for the preset
            self._active_preset.usage_count += 1
            self.config_manager.save_parameter_preset(self._active_preset)
            
            logger.debug(f"Applied parameter preset: {self._active_preset.name}")
        
        return optimal_params

    async def _initialize_configurations(self):
        """Initialize all configuration sources."""
        if self.config.auto_apply_user_preferences:
            await self._load_user_preferences()
        
        if self.config.auto_apply_project_config:
            await self._load_project_config()
            await self._load_team_config()
        
        if self.config.preset_name:
            await self._load_parameter_preset(self.config.preset_name)

    async def generate(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        task_type: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Ollama with enhanced configuration integration."""
        start_time = time.time()
        error = None
        
        try:
            # Initialize configurations if not already done
            if not self._user_preferences and not self._project_config:
                await self._initialize_configurations()
            
            # Get optimal parameters based on configuration sources
            optimal_params = await self._get_optimal_parameters(task_type, temperature, **kwargs)
            
            # Prepare payload with optimized parameters
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "stream": False,
                "options": optimal_params
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract token usage
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
            
            # Log configuration usage for analytics
            await self._log_configuration_usage(task_type, optimal_params)
            
            return {
                "content": result.get("response", ""),
                "model": self.config.model_id,
                "usage": usage,
                "metadata": {
                    "eval_duration": result.get("eval_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_duration": result.get("prompt_eval_duration"),
                    "total_duration": result.get("total_duration"),
                    "applied_preset": self._active_preset.name if self._active_preset else None,
                    "configuration_sources": self._get_configuration_sources()
                }
            }
            
        except Exception as e:
            error = str(e)
            logger.error(f"Enhanced Ollama generation failed: {e}")
            
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
        task_type: str = "general",
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text using Ollama with enhanced configuration integration."""
        start_time = time.time()
        error = None
        accumulated_response = ""
        total_tokens = 0
        
        try:
            # Initialize configurations if not already done
            if not self._user_preferences and not self._project_config:
                await self._initialize_configurations()
            
            # Get optimal parameters based on configuration sources
            optimal_params = await self._get_optimal_parameters(task_type, temperature, **kwargs)
            
            # Prepare payload for streaming
            payload = {
                "model": self.config.model_id,
                "prompt": prompt,
                "stream": True,
                "options": optimal_params
            }
            
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
                                    "temperature": optimal_params["temperature"],
                                    "top_p": optimal_params["top_p"]
                                }
                                
                                # Collect final performance metrics
                                await self.performance_monitor.collect_ollama_metrics(
                                    self.config.model_id, final_metrics, start_time, error
                                )
                                
                                # Log configuration usage for analytics
                                await self._log_configuration_usage(task_type, optimal_params)
                                break
                            
                            # Yield streaming chunk
                            yield {
                                "content": chunk.get("response", ""),
                                "model": self.config.model_id,
                                "done": chunk.get("done", False),
                                "metadata": {
                                    "applied_preset": self._active_preset.name if self._active_preset else None,
                                    "configuration_sources": self._get_configuration_sources()
                                }
                            }
                            
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            error = str(e)
            logger.error(f"Enhanced Ollama streaming generation failed: {e}")
            
            # Collect error metrics
            await self.performance_monitor.collect_ollama_metrics(
                self.config.model_id, {}, start_time, error
            )
            
            raise

    async def _log_configuration_usage(self, task_type: str, parameters: Dict[str, Any]):
        """Log configuration usage for analytics and optimization."""
        try:
            # Track which configuration sources were used
            sources = self._get_configuration_sources()
            
            # Log to configuration manager for analytics
            if self.config.user_id:
                await self._update_user_usage_analytics(task_type, parameters, sources)
            
            # Log to performance monitor
            await self.performance_monitor.log_configuration_usage(
                self.config.model_id,
                task_type,
                parameters,
                sources
            )
            
        except Exception as e:
            logger.warning(f"Failed to log configuration usage: {e}")

    async def _update_user_usage_analytics(self, task_type: str, parameters: Dict[str, Any], sources: List[str]):
        """Update user usage analytics for optimization recommendations."""
        try:
            # This could be extended to track user behavior patterns
            # and suggest optimal configurations based on usage history
            logger.debug(f"Updated usage analytics for user {self.config.user_id}, task: {task_type}")
            
        except Exception as e:
            logger.warning(f"Failed to update user usage analytics: {e}")

    def _get_configuration_sources(self) -> List[str]:
        """Get list of configuration sources that were applied."""
        sources = []
        
        if self._user_preferences:
            sources.append("user_preferences")
        
        if self._project_config:
            sources.append("project_config")
        
        if self._team_config:
            sources.append("team_config")
        
        if self._active_preset:
            sources.append(f"parameter_preset:{self._active_preset.name}")
        
        return sources

    async def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of applied configurations."""
        return {
            "user_preferences": self._user_preferences is not None,
            "project_config": self._project_config is not None,
            "team_config": self._team_config is not None,
            "active_preset": self._active_preset.name if self._active_preset else None,
            "configuration_sources": self._get_configuration_sources(),
            "model_id": self.config.model_id,
            "base_url": self.base_url
        }

    async def apply_preset(self, preset_name: str) -> bool:
        """Apply a specific parameter preset."""
        try:
            preset = await self._load_parameter_preset(preset_name)
            return preset is not None
        except Exception as e:
            logger.error(f"Failed to apply preset {preset_name}: {e}")
            return False

    async def clear_preset(self):
        """Clear the currently applied parameter preset."""
        self._active_preset = None
        logger.debug("Cleared active parameter preset")

    async def get_available_presets(self) -> List[Dict[str, Any]]:
        """Get list of available parameter presets."""
        try:
            presets = self.config_manager.list_parameter_presets()
            return [
                {
                    "name": preset.name,
                    "description": preset.description,
                    "tags": preset.tags,
                    "usage_count": preset.usage_count,
                    "parameters": {
                        "temperature": preset.temperature,
                        "top_p": preset.top_p,
                        "top_k": preset.top_k,
                        "repeat_penalty": preset.repeat_penalty
                    }
                }
                for preset in presets
            ]
        except Exception as e:
            logger.error(f"Failed to get available presets: {e}")
            return []

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("Enhanced OllamaModel cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Enhanced OllamaModel: {e}")


# Factory function to create enhanced Ollama models
async def create_enhanced_ollama_model(
    model_id: str,
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    team_id: Optional[str] = None,
    preset_name: Optional[str] = None,
    base_url: str = "http://localhost:11434",
    **kwargs
) -> OllamaModelEnhanced:
    """Create an enhanced Ollama model with configuration integration."""
    
    config = OllamaModelConfigEnhanced(
        model_id=model_id,
        base_url=base_url,
        user_id=user_id,
        project_id=project_id,
        team_id=team_id,
        preset_name=preset_name,
        **kwargs
    )
    
    model = OllamaModelEnhanced(config)
    
    # Initialize configurations
    await model._initialize_configurations()
    
    return model




