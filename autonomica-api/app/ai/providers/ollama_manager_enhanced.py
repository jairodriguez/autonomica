"""
Enhanced Ollama Manager Implementation

Extends the base OllamaManager with configuration persistence integration,
providing intelligent model management and configuration-aware operations.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

import httpx

from ..ollama_performance_monitor import ollama_performance_monitor
from ..ollama_config_manager import (
    ollama_config_manager, ConfigType, OllamaParameterPreset,
    OllamaUserPreferences, OllamaProjectConfig, OllamaTeamConfig
)

logger = logging.getLogger(__name__)


@dataclass
class ModelRecommendation:
    """Model recommendation with reasoning and configuration."""
    model_name: str
    confidence_score: float
    reasoning: str
    recommended_preset: Optional[str] = None
    estimated_performance: Optional[float] = None
    resource_requirements: Optional[Dict[str, Any]] = None


class OllamaManagerEnhanced:
    """Enhanced manager for Ollama operations with configuration integration."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Performance monitoring integration
        self.performance_monitor = ollama_performance_monitor
        
        # Configuration manager integration
        self.config_manager = ollama_config_manager
        
        logger.info(f"Enhanced OllamaManager initialized for {base_url}")

    async def get_intelligent_model_recommendations(
        self,
        task_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None,
        content_length: Optional[int] = None,
        performance_priority: str = "balanced"
    ) -> List[ModelRecommendation]:
        """Get intelligent model recommendations based on configuration and performance data."""
        try:
            recommendations = []
            
            # Get available models
            available_models = await self.list_available_models()
            
            # Get user preferences if available
            user_preferences = None
            if user_id:
                user_preferences = self.config_manager.load_user_preferences(user_id)
            
            # Get project configuration if available
            project_config = None
            if project_id:
                project_config = self.config_manager.load_project_config(project_id)
            
            # Get team configuration if available
            team_config = None
            if team_id:
                team_config = self.config_manager.load_team_config(team_id)
            
            # Get performance data for all models
            performance_data = await self.performance_monitor.get_ollama_performance_summary()
            
            for model in available_models:
                model_name = model["name"]
                
                # Calculate confidence score based on multiple factors
                confidence_score = await self._calculate_model_confidence(
                    model_name, task_type, user_preferences, project_config, 
                    team_config, performance_data, content_length, performance_priority
                )
                
                # Get recommended preset for this model and task
                recommended_preset = await self._get_recommended_preset(
                    model_name, task_type, user_preferences, project_config, team_config
                )
                
                # Get estimated performance
                estimated_performance = await self._estimate_model_performance(
                    model_name, task_type, content_length, performance_data
                )
                
                # Get resource requirements
                resource_requirements = await self._get_model_resource_requirements(model_name)
                
                # Create recommendation
                recommendation = ModelRecommendation(
                    model_name=model_name,
                    confidence_score=confidence_score,
                    reasoning=await self._generate_recommendation_reasoning(
                        model_name, task_type, confidence_score, user_preferences,
                        project_config, team_config, performance_data
                    ),
                    recommended_preset=recommended_preset,
                    estimated_performance=estimated_performance,
                    resource_requirements=resource_requirements
                )
                
                recommendations.append(recommendation)
            
            # Sort by confidence score (highest first)
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get intelligent model recommendations: {e}")
            return []

    async def _calculate_model_confidence(
        self,
        model_name: str,
        task_type: str,
        user_preferences: Optional[OllamaUserPreferences],
        project_config: Optional[OllamaProjectConfig],
        team_config: Optional[OllamaTeamConfig],
        performance_data: Dict[str, Any],
        content_length: Optional[int],
        performance_priority: str
    ) -> float:
        """Calculate confidence score for a model based on multiple factors."""
        confidence = 0.0
        
        try:
            # Base confidence from performance data
            if model_name in performance_data.get("models", {}):
                model_perf = performance_data["models"][model_name]
                success_rate = model_perf.get("success_rate", 0.5)
                avg_response_time = model_perf.get("avg_response_time", 10.0)
                
                # Higher success rate increases confidence
                confidence += success_rate * 0.3
                
                # Lower response time increases confidence (up to a point)
                if avg_response_time < 5.0:
                    confidence += 0.2
                elif avg_response_time < 10.0:
                    confidence += 0.1
                
                # Task-specific performance
                task_perf = model_perf.get("task_performance", {}).get(task_type, {})
                if task_perf:
                    task_success_rate = task_perf.get("success_rate", 0.5)
                    confidence += task_success_rate * 0.2
            
            # User preference boost
            if user_preferences:
                # Check if user has used this model for this task type
                if model_name in user_preferences.preferred_models.values():
                    confidence += 0.15
                
                # Check if user has a preset for this task type
                if task_type in user_preferences.parameter_presets:
                    confidence += 0.1
            
            # Project configuration boost
            if project_config:
                # Check if model is in project's preferred models
                if model_name in project_config.preferred_models:
                    confidence += 0.1
                
                # Check project constraints
                if project_config.model_constraints:
                    if self._check_model_constraints(model_name, project_config.model_constraints):
                        confidence += 0.1
            
            # Team configuration boost
            if team_config:
                # Check team resource limits
                if self._check_resource_limits(model_name, team_config.resource_requirements):
                    confidence += 0.05
            
            # Content length consideration
            if content_length:
                if content_length > 10000:  # Long content
                    # Prefer models with larger context windows
                    model_info = await self.get_model_info(model_name)
                    if model_info and model_info.get("num_ctx", 0) > 8000:
                        confidence += 0.1
                elif content_length < 1000:  # Short content
                    # Prefer faster models for short content
                    if model_name in ["mistral", "llama2:7b"]:
                        confidence += 0.05
            
            # Performance priority adjustment
            if performance_priority == "speed":
                # Boost faster models
                if model_name in ["mistral", "llama2:7b", "codellama:7b"]:
                    confidence += 0.1
            elif performance_priority == "quality":
                # Boost larger models
                if model_name in ["llama2:13b", "mixtral:8x7b", "llama2:70b"]:
                    confidence += 0.1
            
            # Normalize confidence to 0.0-1.0 range
            confidence = min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.warning(f"Error calculating confidence for {model_name}: {e}")
            confidence = 0.5  # Default confidence
        
        return confidence

    async def _get_recommended_preset(
        self,
        model_name: str,
        task_type: str,
        user_preferences: Optional[OllamaUserPreferences],
        project_config: Optional[OllamaProjectConfig],
        team_config: Optional[OllamaTeamConfig]
    ) -> Optional[str]:
        """Get recommended parameter preset for a model and task type."""
        try:
            # Priority order: user preferences > project config > team config > general presets
            
            # Check user preferences first
            if user_preferences and task_type in user_preferences.parameter_presets:
                return user_preferences.parameter_presets[task_type]
            
            # Check project configuration
            if project_config and task_type in project_config.parameter_presets:
                return project_config.parameter_presets[task_type]
            
            # Check team configuration
            if team_config and task_type in team_config.shared_presets:
                return team_config.shared_presets[task_type]
            
            # Get general presets for this task type
            all_presets = self.config_manager.list_parameter_presets()
            task_presets = [p for p in all_presets if task_type in p.tags]
            
            if task_presets:
                # Return the most popular preset for this task type
                most_popular = max(task_presets, key=lambda p: p.usage_count)
                return most_popular.name
            
        except Exception as e:
            logger.warning(f"Error getting recommended preset: {e}")
        
        return None

    async def _estimate_model_performance(
        self,
        model_name: str,
        task_type: str,
        content_length: Optional[int],
        performance_data: Dict[str, Any]
    ) -> Optional[float]:
        """Estimate model performance for a specific task and content length."""
        try:
            if model_name not in performance_data.get("models", {}):
                return None
            
            model_perf = performance_data["models"][model_name]
            
            # Base performance score
            base_score = model_perf.get("success_rate", 0.5)
            
            # Task-specific adjustment
            task_perf = model_perf.get("task_performance", {}).get(task_type, {})
            if task_perf:
                task_score = task_perf.get("success_rate", 0.5)
                base_score = (base_score + task_score) / 2
            
            # Content length adjustment
            if content_length:
                if content_length > 10000:
                    # Long content penalty
                    base_score *= 0.9
                elif content_length < 1000:
                    # Short content bonus
                    base_score *= 1.1
            
            return min(1.0, max(0.0, base_score))
            
        except Exception as e:
            logger.warning(f"Error estimating performance for {model_name}: {e}")
            return None

    async def _get_model_resource_requirements(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get estimated resource requirements for a model."""
        try:
            model_info = await self.get_model_info(model_name)
            if not model_info:
                return None
            
            # Estimate based on model size and type
            size = model_info.get("size", 0)
            parameters = model_info.get("parameter_size", 0)
            
            requirements = {
                "estimated_memory": f"{size / (1024**3):.1f}GB" if size else "Unknown",
                "estimated_vram": f"{size / (1024**3) * 1.5:.1f}GB" if size else "Unknown",
                "cpu_cores": max(2, parameters // 1000000000) if parameters else 2,
                "recommended_ram": f"{size / (1024**3) * 2:.1f}GB" if size else "8GB"
            }
            
            return requirements
            
        except Exception as e:
            logger.warning(f"Error getting resource requirements for {model_name}: {e}")
            return None

    async def _generate_recommendation_reasoning(
        self,
        model_name: str,
        task_type: str,
        confidence_score: float,
        user_preferences: Optional[OllamaUserPreferences],
        project_config: Optional[OllamaProjectConfig],
        team_config: Optional[OllamaTeamConfig],
        performance_data: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []
        
        try:
            # Performance-based reasoning
            if model_name in performance_data.get("models", {}):
                model_perf = performance_data["models"][model_name]
                success_rate = model_perf.get("success_rate", 0.5)
                
                if success_rate > 0.8:
                    reasons.append("Excellent success rate")
                elif success_rate > 0.6:
                    reasons.append("Good success rate")
                
                avg_response_time = model_perf.get("avg_response_time", 10.0)
                if avg_response_time < 5.0:
                    reasons.append("Fast response times")
                elif avg_response_time < 10.0:
                    reasons.append("Reasonable response times")
            
            # User preference reasoning
            if user_preferences:
                if model_name in user_preferences.preferred_models.values():
                    reasons.append("Matches user preferences")
                
                if task_type in user_preferences.parameter_presets:
                    reasons.append("User has task-specific presets")
            
            # Project configuration reasoning
            if project_config:
                if model_name in project_config.preferred_models:
                    reasons.append("Project preferred model")
                
                if project_config.model_constraints:
                    if self._check_model_constraints(model_name, project_config.model_constraints):
                        reasons.append("Meets project constraints")
            
            # Task-specific reasoning
            if task_type == "coding":
                if "code" in model_name.lower() or "llama" in model_name.lower():
                    reasons.append("Optimized for code generation")
            elif task_type == "creative":
                if "creative" in model_name.lower() or "uncensored" in model_name.lower():
                    reasons.append("Optimized for creative tasks")
            elif task_type == "analysis":
                if "llama" in model_name.lower() and "13b" in model_name.lower():
                    reasons.append("Good for analytical tasks")
            
            # Confidence-based reasoning
            if confidence_score > 0.8:
                reasons.append("High confidence recommendation")
            elif confidence_score > 0.6:
                reasons.append("Good confidence recommendation")
            else:
                reasons.append("Lower confidence but available")
            
            if not reasons:
                reasons.append("Standard recommendation")
            
            return "; ".join(reasons)
            
        except Exception as e:
            logger.warning(f"Error generating reasoning: {e}")
            return "Standard recommendation"

    def _check_model_constraints(self, model_name: str, constraints: Dict[str, Any]) -> bool:
        """Check if a model meets project constraints."""
        try:
            # Check model size constraints
            if "max_model_size" in constraints:
                # This would need model size information
                pass
            
            # Check model type constraints
            if "allowed_model_types" in constraints:
                allowed_types = constraints["allowed_model_types"]
                for model_type in allowed_types:
                    if model_type.lower() in model_name.lower():
                        return True
                return False
            
            # Check model family constraints
            if "allowed_model_families" in constraints:
                allowed_families = constraints["allowed_model_families"]
                for family in allowed_families:
                    if family.lower() in model_name.lower():
                        return True
                return False
            
            return True  # No constraints specified
            
        except Exception as e:
            logger.warning(f"Error checking model constraints: {e}")
            return True

    def _check_resource_limits(self, model_name: str, resource_requirements: Dict[str, Any]) -> bool:
        """Check if a model meets team resource limits."""
        try:
            # This would need actual system resource information
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            logger.warning(f"Error checking resource limits: {e}")
            return True

    async def create_optimized_model_config(
        self,
        model_name: str,
        task_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an optimized model configuration based on all available sources."""
        try:
            config = {
                "model_id": model_name,
                "base_url": self.base_url,
                "user_id": user_id,
                "project_id": project_id,
                "team_id": team_id
            }
            
            # Get recommended preset
            recommended_preset = await self._get_recommended_preset(
                model_name, task_type, 
                self.config_manager.load_user_preferences(user_id) if user_id else None,
                self.config_manager.load_project_config(project_id) if project_id else None,
                self.config_manager.load_team_config(team_id) if team_id else None
            )
            
            if recommended_preset:
                config["preset_name"] = recommended_preset
                
                # Load preset parameters
                preset = self.config_manager.load_parameter_preset(recommended_preset)
                if preset:
                    config.update({
                        "temperature": preset.temperature,
                        "top_p": preset.top_p,
                        "top_k": preset.top_k,
                        "repeat_penalty": preset.repeat_penalty,
                        "seed": preset.seed,
                        "num_ctx": preset.num_ctx,
                        "num_gpu": preset.num_gpu,
                        "num_thread": preset.num_thread,
                        "stop": preset.stop
                    })
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create optimized model config: {e}")
            return {"model_id": model_name, "base_url": self.base_url}

    async def get_model_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive model health summary with configuration insights."""
        try:
            # Get basic model list
            models = await self.list_available_models()
            
            # Get performance summary
            performance_summary = await self.performance_monitor.get_ollama_performance_summary()
            
            # Get configuration summary
            config_summary = self.config_manager.get_configuration_summary()
            
            # Analyze each model's health
            model_health = {}
            for model in models:
                model_name = model["name"]
                
                # Get model info
                model_info = await self.get_model_info(model_name)
                
                # Get performance data
                model_perf = performance_summary.get("models", {}).get(model_name, {})
                
                # Get configuration usage
                config_usage = await self._get_model_configuration_usage(model_name)
                
                model_health[model_name] = {
                    "status": model.get("health_status", "unknown"),
                    "performance": {
                        "success_rate": model_perf.get("success_rate", 0.0),
                        "avg_response_time": model_perf.get("avg_response_time", 0.0),
                        "total_requests": model_perf.get("total_requests", 0),
                        "error_rate": model_perf.get("error_rate", 0.0)
                    },
                    "configuration": config_usage,
                    "info": model_info,
                    "recommendations": await self._get_model_health_recommendations(
                        model_name, model_perf, config_usage
                    )
                }
            
            return {
                "total_models": len(models),
                "healthy_models": len([m for m in models if m.get("health_status") == "healthy"]),
                "model_health": model_health,
                "configuration_summary": config_summary,
                "performance_summary": performance_summary
            }
            
        except Exception as e:
            logger.error(f"Failed to get model health summary: {e}")
            return {"error": str(e)}

    async def _get_model_configuration_usage(self, model_name: str) -> Dict[str, Any]:
        """Get configuration usage statistics for a specific model."""
        try:
            # Get all presets that use this model
            all_presets = self.config_manager.list_parameter_presets()
            model_presets = [p for p in all_presets if model_name in p.tags]
            
            # Get user preferences that use this model
            # This would require additional methods in the config manager
            
            return {
                "presets_count": len(model_presets),
                "preset_names": [p.name for p in model_presets],
                "total_preset_usage": sum(p.usage_count for p in model_presets)
            }
            
        except Exception as e:
            logger.warning(f"Error getting configuration usage for {model_name}: {e}")
            return {}

    async def _get_model_health_recommendations(
        self,
        model_name: str,
        performance_data: Dict[str, Any],
        config_usage: Dict[str, Any]
    ) -> List[str]:
        """Get health recommendations for a specific model."""
        recommendations = []
        
        try:
            # Performance-based recommendations
            success_rate = performance_data.get("success_rate", 0.0)
            if success_rate < 0.5:
                recommendations.append("Low success rate - consider parameter tuning")
            
            error_rate = performance_data.get("error_rate", 0.0)
            if error_rate > 0.3:
                recommendations.append("High error rate - check model installation")
            
            # Configuration-based recommendations
            if config_usage.get("presets_count", 0) == 0:
                recommendations.append("No parameter presets - consider creating task-specific presets")
            
            # Resource-based recommendations
            # This would need actual system monitoring
            
        except Exception as e:
            logger.warning(f"Error getting health recommendations for {model_name}: {e}")
        
        return recommendations

    # Inherit all base OllamaManager methods
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List all models installed in Ollama with enhanced information."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            
            # Enhance model information with performance data and configuration usage
            enhanced_models = []
            for model in models:
                model_name = model["name"]
                performance_data = await self.performance_monitor.get_model_performance(model_name)
                config_usage = await self._get_model_configuration_usage(model_name)
                
                enhanced_model = {
                    **model,
                    "performance": performance_data.to_dict() if performance_data else None,
                    "health_status": await self._check_model_health(model_name),
                    "configuration_usage": config_usage
                }
                enhanced_models.append(enhanced_model)
            
            return enhanced_models
            
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model to Ollama with progress tracking."""
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
                            logger.info(f"Pull progress for {model_name}: {status}")
                            
                            if "error" in chunk:
                                logger.error(f"Pull error for {model_name}: {chunk['error']}")
                                return False
                                
                        except json.JSONDecodeError:
                            continue
            
            logger.info(f"Successfully pulled model {model_name}")
            
            # Create default presets for the new model
            await self._create_default_presets_for_model(model_name)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False

    async def _create_default_presets_for_model(self, model_name: str):
        """Create default parameter presets for a newly installed model."""
        try:
            # Create general-purpose preset
            general_preset = OllamaParameterPreset(
                name=f"{model_name}_general",
                description=f"General-purpose preset for {model_name}",
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                tags=["general", model_name]
            )
            
            # Create coding preset if it's a code model
            if "code" in model_name.lower() or "llama" in model_name.lower():
                coding_preset = OllamaParameterPreset(
                    name=f"{model_name}_coding",
                    description=f"Code generation preset for {model_name}",
                    temperature=0.3,
                    top_p=0.95,
                    top_k=50,
                    tags=["coding", model_name]
                )
                self.config_manager.save_parameter_preset(coding_preset)
            
            # Create creative preset
            creative_preset = OllamaParameterPreset(
                name=f"{model_name}_creative",
                description=f"Creative writing preset for {model_name}",
                temperature=0.9,
                top_p=0.8,
                top_k=30,
                tags=["creative", model_name]
            )
            
            # Save presets
            self.config_manager.save_parameter_preset(general_preset)
            self.config_manager.save_parameter_preset(creative_preset)
            
            logger.info(f"Created default presets for {model_name}")
            
        except Exception as e:
            logger.warning(f"Failed to create default presets for {model_name}: {e}")

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama with configuration cleanup."""
        try:
            payload = {"name": model_name}
            response = await self.client.delete(f"{self.base_url}/api/delete", json=payload)
            response.raise_for_status()
            
            # Clean up model-specific configurations
            await self._cleanup_model_configurations(model_name)
            
            logger.info(f"Successfully deleted model {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return False

    async def _cleanup_model_configurations(self, model_name: str):
        """Clean up configurations related to a deleted model."""
        try:
            # Remove model-specific presets
            all_presets = self.config_manager.list_parameter_presets()
            model_presets = [p for p in all_presets if model_name in p.tags]
            
            for preset in model_presets:
                # Remove model tag from preset
                preset.tags = [tag for tag in preset.tags if tag != model_name]
                if preset.tags:  # Keep preset if it has other tags
                    self.config_manager.save_parameter_preset(preset)
                else:  # Delete preset if it only had this model tag
                    # Note: This would require a delete method in the config manager
                    logger.debug(f"Preset {preset.name} no longer has model tags")
            
            logger.info(f"Cleaned up configurations for deleted model {model_name}")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup configurations for {model_name}: {e}")

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
        """Get comprehensive system status including configuration insights."""
        try:
            # Get basic Ollama status
            status = {
                "service_healthy": await self._check_service_health(),
                "models_count": len(await self.list_available_models()),
                "performance_summary": await self.performance_monitor.get_ollama_performance_summary(),
                "configuration_summary": self.config_manager.get_configuration_summary(),
                "recommendations": await self._get_system_recommendations()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    async def _get_system_recommendations(self) -> List[str]:
        """Get system-wide recommendations for optimization."""
        recommendations = []
        
        try:
            # Get configuration summary
            config_summary = self.config_manager.get_configuration_summary()
            
            # Check for missing configurations
            if config_summary.get("total_presets", 0) == 0:
                recommendations.append("No parameter presets configured - consider creating task-specific presets")
            
            if config_summary.get("total_users", 0) == 0:
                recommendations.append("No user preferences configured - consider setting up user-specific configurations")
            
            if config_summary.get("total_projects", 0) == 0:
                recommendations.append("No project configurations - consider setting up project-specific settings")
            
            # Check for configuration optimization opportunities
            presets = self.config_manager.list_parameter_presets()
            low_usage_presets = [p for p in presets if p.usage_count < 3]
            if low_usage_presets:
                recommendations.append(f"{len(low_usage_presets)} presets have low usage - consider reviewing or removing unused presets")
            
        except Exception as e:
            logger.warning(f"Error getting system recommendations: {e}")
        
        return recommendations

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
            logger.info("Enhanced OllamaManager cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Enhanced OllamaManager: {e}")


# Global instance
enhanced_ollama_manager = OllamaManagerEnhanced()




