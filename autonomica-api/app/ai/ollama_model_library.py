"""
Ollama Model Library System

This module provides comprehensive model library management including:
- Specialized model support (code, vision, math, etc.)
- Model compatibility checking
- Intelligent model recommendations based on task type
- Custom model fine-tuning support
- Model parameter optimization
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelCategory(Enum):
    """Categories of AI models."""
    GENERAL = "general"
    CODE = "code"
    VISION = "vision"
    MATH = "math"
    MULTIMODAL = "multimodal"
    INSTRUCTION = "instruction"
    CHAT = "chat"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    TRANSLATION = "translation"

class ModelCapability(Enum):
    """Specific capabilities of AI models."""
    TEXT_GENERATION = "text_generation"
    CODE_COMPLETION = "code_completion"
    CODE_ANALYSIS = "code_analysis"
    IMAGE_UNDERSTANDING = "image_understanding"
    MATHEMATICAL_REASONING = "mathematical_reasoning"
    LOGICAL_REASONING = "logical_reasoning"
    CREATIVE_WRITING = "creative_writing"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QUESTION_ANSWERING = "question_answering"
    INSTRUCTION_FOLLOWING = "instruction_following"
    CONVERSATION = "conversation"

class ModelSize(Enum):
    """Model size categories."""
    TINY = "tiny"          # < 1B parameters
    SMALL = "small"         # 1B - 3B parameters
    MEDIUM = "medium"       # 3B - 7B parameters
    LARGE = "large"         # 7B - 13B parameters
    XLARGE = "xlarge"       # 13B - 30B parameters
    XXLARGE = "xxlarge"     # 30B - 70B parameters
    MASSIVE = "massive"     # > 70B parameters

@dataclass
class ModelMetadata:
    """Comprehensive metadata for a model."""
    name: str
    display_name: str
    description: str
    category: ModelCategory
    capabilities: Set[ModelCapability]
    size: ModelSize
    parameter_count: int
    context_length: int
    quantization_levels: List[str] = field(default_factory=list)
    license: str = "unknown"
    creator: str = "unknown"
    last_updated: Optional[datetime] = None
    performance_score: float = 0.0
    memory_requirements_gb: float = 0.0
    gpu_requirements: Optional[str] = None
    recommended_hardware: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

@dataclass
class ModelCompatibility:
    """Model compatibility information."""
    model_name: str
    system_requirements: Dict[str, Any]
    hardware_compatibility: Dict[str, bool]
    software_compatibility: Dict[str, bool]
    performance_estimate: Dict[str, Any]
    compatibility_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ModelRecommendation:
    """Model recommendation for a specific task."""
    model_name: str
    confidence_score: float
    reasoning: str
    expected_performance: Dict[str, Any]
    alternatives: List[str] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)

@dataclass
class FineTuningConfig:
    """Configuration for model fine-tuning."""
    base_model: str
    training_data_path: str
    hyperparameters: Dict[str, Any]
    target_capabilities: Set[ModelCapability]
    validation_metrics: List[str]
    expected_improvements: Dict[str, float]

class OllamaModelLibrary:
    """Comprehensive model library management system."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Model registry
        self.model_registry: Dict[str, ModelMetadata] = {}
        self.capability_index: Dict[ModelCapability, Set[str]] = {}
        self.category_index: Dict[ModelCategory, Set[str]] = {}
        
        # Compatibility cache
        self.compatibility_cache: Dict[str, ModelCompatibility] = {}
        
        # Task-to-capability mapping
        self.task_capability_mapping = self._initialize_task_mapping()
        
        # Load model registry
        self._load_model_registry()
        
        logger.info("Ollama Model Library initialized")

    def _initialize_task_mapping(self) -> Dict[str, Set[ModelCapability]]:
        """Initialize mapping from task types to required capabilities."""
        return {
            "code_generation": {ModelCapability.CODE_COMPLETION, ModelCapability.TEXT_GENERATION},
            "code_review": {ModelCapability.CODE_ANALYSIS, ModelCapability.TEXT_GENERATION},
            "code_debugging": {ModelCapability.CODE_ANALYSIS, ModelCapability.LOGICAL_REASONING},
            "image_analysis": {ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.TEXT_GENERATION},
            "mathematical_problem": {ModelCapability.MATHEMATICAL_REASONING, ModelCapability.LOGICAL_REASONING},
            "creative_writing": {ModelCapability.CREATIVE_WRITING, ModelCapability.TEXT_GENERATION},
            "translation": {ModelCapability.TRANSLATION, ModelCapability.TEXT_GENERATION},
            "summarization": {ModelCapability.SUMMARIZATION, ModelCapability.TEXT_GENERATION},
            "question_answering": {ModelCapability.QUESTION_ANSWERING, ModelCapability.TEXT_GENERATION},
            "conversation": {ModelCapability.CONVERSATION, ModelCapability.TEXT_GENERATION},
            "instruction_following": {ModelCapability.INSTRUCTION_FOLLOWING, ModelCapability.TEXT_GENERATION},
            "logical_reasoning": {ModelCapability.LOGICAL_REASONING, ModelCapability.TEXT_GENERATION},
            "data_analysis": {ModelCapability.ANALYSIS, ModelCapability.LOGICAL_REASONING},
            "document_understanding": {ModelCapability.TEXT_GENERATION, ModelCapability.ANALYSIS},
            "multimodal_task": {ModelCapability.MULTIMODAL, ModelCapability.TEXT_GENERATION}
        }

    def _load_model_registry(self):
        """Load the comprehensive model registry."""
        # This would typically load from a database or configuration file
        # For now, we'll create a comprehensive registry of popular models
        
        self.model_registry = {
            # General Purpose Models
            "llama3.1:8b": ModelMetadata(
                name="llama3.1:8b",
                display_name="Llama 3.1 8B",
                description="General-purpose language model optimized for instruction following and conversation",
                category=ModelCategory.GENERAL,
                capabilities={ModelCapability.TEXT_GENERATION, ModelCapability.INSTRUCTION_FOLLOWING, ModelCapability.CONVERSATION},
                size=ModelSize.MEDIUM,
                parameter_count=8_000_000_000,
                context_length=8192,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Meta",
                creator="Meta AI",
                performance_score=8.2,
                memory_requirements_gb=4.5,
                gpu_requirements="4GB VRAM",
                recommended_hardware="Mid-range GPU or 16GB+ RAM",
                tags=["general", "instruction", "conversation", "efficient"],
                examples=["Chat assistance", "Text generation", "Instruction following"],
                limitations=["Limited context window", "May struggle with complex reasoning"]
            ),
            
            "llama3.1:70b": ModelMetadata(
                name="llama3.1:70b",
                display_name="Llama 3.1 70B",
                description="Large-scale language model with advanced reasoning capabilities",
                category=ModelCategory.GENERAL,
                capabilities={ModelCapability.TEXT_GENERATION, ModelCapability.LOGICAL_REASONING, ModelCapability.ANALYSIS},
                size=ModelSize.XXLARGE,
                parameter_count=70_000_000_000,
                context_length=8192,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Meta",
                creator="Meta AI",
                performance_score=9.1,
                memory_requirements_gb=35.0,
                gpu_requirements="24GB+ VRAM",
                recommended_hardware="High-end GPU with 24GB+ VRAM",
                tags=["general", "reasoning", "analysis", "high-quality"],
                examples=["Complex reasoning", "Analysis tasks", "High-quality text generation"],
                limitations=["High resource requirements", "Slower inference"]
            ),
            
            # Code Models
            "codellama:7b": ModelMetadata(
                name="codellama:7b",
                display_name="Code Llama 7B",
                description="Specialized model for code generation and analysis",
                category=ModelCategory.CODE,
                capabilities={ModelCapability.CODE_COMPLETION, ModelCapability.CODE_ANALYSIS, ModelCapability.TEXT_GENERATION},
                size=ModelSize.MEDIUM,
                parameter_count=7_000_000_000,
                context_length=16384,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Meta",
                creator="Meta AI",
                performance_score=8.7,
                memory_requirements_gb=4.0,
                gpu_requirements="4GB VRAM",
                recommended_hardware="Mid-range GPU or 16GB+ RAM",
                tags=["code", "programming", "completion", "analysis"],
                examples=["Code completion", "Code review", "Debugging assistance"],
                limitations=["May struggle with complex algorithms", "Limited to programming languages"]
            ),
            
            "codellama:13b": ModelMetadata(
                name="codellama:13b",
                display_name="Code Llama 13B",
                description="Advanced code generation model with better reasoning",
                category=ModelCategory.CODE,
                capabilities={ModelCapability.CODE_COMPLETION, ModelCapability.CODE_ANALYSIS, ModelCapability.LOGICAL_REASONING},
                size=ModelSize.LARGE,
                parameter_count=13_000_000_000,
                context_length=16384,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Meta",
                creator="Meta AI",
                performance_score=9.0,
                memory_requirements_gb=7.0,
                gpu_requirements="8GB VRAM",
                recommended_hardware="Mid-range GPU with 8GB+ VRAM",
                tags=["code", "programming", "reasoning", "advanced"],
                examples=["Complex code generation", "Algorithm design", "System architecture"],
                limitations=["Higher resource requirements", "Slower than smaller models"]
            ),
            
            "deepseek-coder:6.7b": ModelMetadata(
                name="deepseek-coder:6.7b",
                display_name="DeepSeek Coder 6.7B",
                description="Efficient code generation model with strong performance",
                category=ModelCategory.CODE,
                capabilities={ModelCapability.CODE_COMPLETION, ModelCapability.CODE_ANALYSIS},
                size=ModelSize.MEDIUM,
                parameter_count=6_700_000_000,
                context_length=16384,
                quantization_levels=["q4_0", "q5_0"],
                license="DeepSeek",
                creator="DeepSeek",
                performance_score=8.5,
                memory_requirements_gb=3.5,
                gpu_requirements="4GB VRAM",
                recommended_hardware="Mid-range GPU or 16GB+ RAM",
                tags=["code", "efficient", "fast", "modern"],
                examples=["Rapid code generation", "Quick prototyping", "Code review"],
                limitations=["May lack depth in complex reasoning"]
            ),
            
            # Vision Models
            "llava:7b": ModelMetadata(
                name="llava:7b",
                display_name="LLaVA 7B",
                description="Multimodal model for image understanding and analysis",
                category=ModelCategory.VISION,
                capabilities={ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.TEXT_GENERATION, ModelCapability.MULTIMODAL},
                size=ModelSize.MEDIUM,
                parameter_count=7_000_000_000,
                context_length=4096,
                quantization_levels=["q4_0", "q5_0"],
                license="Microsoft",
                creator="Microsoft Research",
                performance_score=8.3,
                memory_requirements_gb=5.0,
                gpu_requirements="6GB VRAM",
                recommended_hardware="Mid-range GPU with 6GB+ VRAM",
                tags=["vision", "multimodal", "image", "understanding"],
                examples=["Image analysis", "Visual question answering", "Image description"],
                limitations=["Limited context window", "May struggle with complex images"]
            ),
            
            "llava:13b": ModelMetadata(
                name="llava:13b",
                display_name="LLaVA 13B",
                description="Advanced vision model with better image understanding",
                category=ModelCategory.VISION,
                capabilities={ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.TEXT_GENERATION, ModelCapability.MULTIMODAL},
                size=ModelSize.LARGE,
                parameter_count=13_000_000_000,
                context_length=4096,
                quantization_levels=["q4_0", "q5_0"],
                license="Microsoft",
                creator="Microsoft Research",
                performance_score=8.8,
                memory_requirements_gb=8.0,
                gpu_requirements="10GB VRAM",
                recommended_hardware="High-end GPU with 10GB+ VRAM",
                tags=["vision", "multimodal", "advanced", "high-quality"],
                examples=["Complex image analysis", "Detailed visual descriptions", "Visual reasoning"],
                limitations=["Higher resource requirements", "Slower inference"]
            ),
            
            # Math Models
            "math:7b": ModelMetadata(
                name="math:7b",
                display_name="Math 7B",
                description="Specialized model for mathematical reasoning and problem solving",
                category=ModelCategory.MATH,
                capabilities={ModelCapability.MATHEMATICAL_REASONING, ModelCapability.LOGICAL_REASONING, ModelCapability.TEXT_GENERATION},
                size=ModelSize.MEDIUM,
                parameter_count=7_000_000_000,
                context_length=8192,
                quantization_levels=["q4_0", "q5_0"],
                license="Open Source",
                creator="Community",
                performance_score=8.6,
                memory_requirements_gb=4.0,
                gpu_requirements="4GB VRAM",
                recommended_hardware="Mid-range GPU or 16GB+ RAM",
                tags=["math", "reasoning", "problem-solving", "logic"],
                examples=["Mathematical problem solving", "Equation solving", "Mathematical proofs"],
                limitations=["May struggle with very complex mathematics", "Limited to mathematical domains"]
            ),
            
            # Creative Models
            "mistral:7b": ModelMetadata(
                name="mistral:7b",
                display_name="Mistral 7B",
                description="Efficient model with strong creative and reasoning capabilities",
                category=ModelCategory.CREATIVE,
                capabilities={ModelCapability.CREATIVE_WRITING, ModelCapability.TEXT_GENERATION, ModelCapability.LOGICAL_REASONING},
                size=ModelSize.MEDIUM,
                parameter_count=7_000_000_000,
                context_length=8192,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Mistral AI",
                creator="Mistral AI",
                performance_score=8.4,
                memory_requirements_gb=4.0,
                gpu_requirements="4GB VRAM",
                recommended_hardware="Mid-range GPU or 16GB+ RAM",
                tags=["creative", "efficient", "reasoning", "modern"],
                examples=["Creative writing", "Story generation", "Poetry", "General reasoning"],
                limitations=["May lack depth in specialized domains"]
            ),
            
            "mixtral:8x7b": ModelMetadata(
                name="mixtral:8x7b",
                display_name="Mixtral 8x7B",
                description="Mixture of experts model with excellent performance across domains",
                category=ModelCategory.GENERAL,
                capabilities={ModelCapability.TEXT_GENERATION, ModelCapability.LOGICAL_REASONING, ModelCapability.ANALYSIS},
                size=ModelSize.LARGE,
                parameter_count=47_000_000_000,
                context_length=32768,
                quantization_levels=["q4_0", "q5_0", "q8_0"],
                license="Mistral AI",
                creator="Mistral AI",
                performance_score=9.2,
                memory_requirements_gb=24.0,
                gpu_requirements="16GB+ VRAM",
                recommended_hardware="High-end GPU with 16GB+ VRAM",
                tags=["general", "expert", "high-quality", "versatile"],
                examples=["Complex reasoning", "Multi-domain tasks", "High-quality generation"],
                limitations=["High resource requirements", "Slower inference"]
            )
        }
        
        # Build capability and category indices
        self._build_indices()
        
        logger.info(f"Loaded {len(self.model_registry)} models into registry")

    def _build_indices(self):
        """Build capability and category indices for efficient searching."""
        self.capability_index = {capability: set() for capability in ModelCapability}
        self.category_index = {category: set() for category in ModelCategory}
        
        for model_name, metadata in self.model_registry.items():
            # Add to capability index
            for capability in metadata.capabilities:
                self.capability_index[capability].add(model_name)
            
            # Add to category index
            self.category_index[metadata.category].add(model_name)

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of models available in Ollama."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            else:
                logger.error(f"Failed to get available models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model from Ollama."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/show", 
                params={"name": model_name}
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.debug(f"Model {model_name} not found in Ollama")
                return None
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None

    async def check_model_compatibility(self, model_name: str, system_info: Dict[str, Any]) -> ModelCompatibility:
        """Check if a model is compatible with the current system."""
        if model_name in self.compatibility_cache:
            return self.compatibility_cache[model_name]
        
        try:
            metadata = self.model_registry.get(model_name)
            if not metadata:
                # Try to get from Ollama
                ollama_info = await self.get_model_info(model_name)
                if ollama_info:
                    # Create basic metadata from Ollama info
                    metadata = self._create_metadata_from_ollama(model_name, ollama_info)
                else:
                    return ModelCompatibility(
                        model_name=model_name,
                        system_requirements={},
                        hardware_compatibility={},
                        software_compatibility={},
                        performance_estimate={},
                        compatibility_score=0.0,
                        warnings=["Model not found in registry or Ollama"],
                        recommendations=["Check model name or install the model"]
                    )
            
            # Check system compatibility
            compatibility = await self._evaluate_compatibility(metadata, system_info)
            
            # Cache the result
            self.compatibility_cache[model_name] = compatibility
            
            return compatibility
            
        except Exception as e:
            logger.error(f"Error checking compatibility for {model_name}: {e}")
            return ModelCompatibility(
                model_name=model_name,
                system_requirements={},
                hardware_compatibility={},
                software_compatibility={},
                performance_estimate={},
                compatibility_score=0.0,
                warnings=[f"Error during compatibility check: {e}"],
                recommendations=["Try again or check system status"]
            )

    async def _evaluate_compatibility(self, metadata: ModelMetadata, system_info: Dict[str, Any]) -> ModelCompatibility:
        """Evaluate model compatibility with system."""
        compatibility = ModelCompatibility(
            model_name=metadata.name,
            system_requirements={},
            hardware_compatibility={},
            software_compatibility={},
            performance_estimate={},
            compatibility_score=0.0,
            warnings=[],
            recommendations=[]
        )
        
        # Check memory requirements
        available_memory_gb = system_info.get("available_memory_gb", 0)
        if available_memory_gb < metadata.memory_requirements_gb:
            compatibility.warnings.append(f"Insufficient memory: {available_memory_gb}GB available, {metadata.memory_requirements_gb}GB required")
            compatibility.recommendations.append("Increase system memory or use a smaller model")
        else:
            compatibility.hardware_compatibility["memory"] = True
        
        # Check GPU requirements
        gpu_available = system_info.get("gpu_available", False)
        gpu_memory_gb = system_info.get("gpu_memory_gb", 0)
        
        if metadata.gpu_requirements:
            if not gpu_available:
                compatibility.warnings.append("GPU not available but recommended for this model")
                compatibility.recommendations.append("Consider using CPU-only mode or install GPU drivers")
            elif gpu_memory_gb < metadata.memory_requirements_gb:
                compatibility.warnings.append(f"Insufficient GPU memory: {gpu_memory_gb}GB available")
                compatibility.recommendations.append("Use a smaller model or reduce quantization level")
            else:
                compatibility.hardware_compatibility["gpu"] = True
        
        # Calculate compatibility score
        score = 0.0
        if compatibility.hardware_compatibility.get("memory", False):
            score += 0.4
        if compatibility.hardware_compatibility.get("gpu", False):
            score += 0.4
        if not compatibility.warnings:
            score += 0.2
        
        compatibility.compatibility_score = score
        
        # Performance estimate
        compatibility.performance_estimate = {
            "expected_response_time_ms": self._estimate_response_time(metadata, system_info),
            "memory_efficiency": self._calculate_memory_efficiency(metadata, system_info),
            "recommended_batch_size": self._calculate_batch_size(metadata, system_info)
        }
        
        return compatibility

    def _estimate_response_time(self, metadata: ModelMetadata, system_info: Dict[str, Any]) -> float:
        """Estimate response time based on model size and system capabilities."""
        base_time = metadata.parameter_count / 1_000_000_000 * 100  # Base ms per billion parameters
        
        # Adjust based on system capabilities
        if system_info.get("gpu_available", False):
            base_time *= 0.3  # GPU acceleration
        elif system_info.get("high_performance_cpu", False):
            base_time *= 0.7  # High-performance CPU
        
        return max(base_time, 100)  # Minimum 100ms

    def _calculate_memory_efficiency(self, metadata: ModelMetadata, system_info: Dict[str, Any]) -> float:
        """Calculate memory efficiency score."""
        available_memory = system_info.get("available_memory_gb", 1)
        required_memory = metadata.memory_requirements_gb
        
        if required_memory <= 0:
            return 1.0
        
        efficiency = available_memory / required_memory
        return min(efficiency, 2.0)  # Cap at 2.0 for efficiency

    def _calculate_batch_size(self, metadata: ModelMetadata, system_info: Dict[str, Any]) -> int:
        """Calculate recommended batch size."""
        available_memory = system_info.get("available_memory_gb", 1)
        required_memory = metadata.memory_requirements_gb
        
        if required_memory <= 0:
            return 1
        
        # Conservative batch size calculation
        batch_size = max(1, int(available_memory / required_memory * 0.8))
        return min(batch_size, 4)  # Cap at 4 for stability

    def _create_metadata_from_ollama(self, model_name: str, ollama_info: Dict[str, Any]) -> ModelMetadata:
        """Create metadata from Ollama model information."""
        # Extract size from model name or info
        size_match = re.search(r'(\d+(?:\.\d+)?)b', model_name.lower())
        parameter_count = int(float(size_match.group(1)) * 1_000_000_000) if size_match else 7_000_000_000
        
        # Estimate category based on name
        category = ModelCategory.GENERAL
        if any(keyword in model_name.lower() for keyword in ["code", "coder", "programming"]):
            category = ModelCategory.CODE
        elif any(keyword in model_name.lower() for keyword in ["vision", "llava", "image"]):
            category = ModelCategory.VISION
        elif any(keyword in model_name.lower() for keyword in ["math", "mathematical"]):
            category = ModelCategory.MATH
        
        # Estimate capabilities based on category
        capabilities = {ModelCapability.TEXT_GENERATION}
        if category == ModelCategory.CODE:
            capabilities.update([ModelCapability.CODE_COMPLETION, ModelCapability.CODE_ANALYSIS])
        elif category == ModelCategory.VISION:
            capabilities.update([ModelCapability.IMAGE_UNDERSTANDING, ModelCapability.MULTIMODAL])
        elif category == ModelCategory.MATH:
            capabilities.update([ModelCapability.MATHEMATICAL_REASONING, ModelCapability.LOGICAL_REASONING])
        
        return ModelMetadata(
            name=model_name,
            display_name=model_name.replace(":", " ").title(),
            description=f"Model loaded from Ollama: {ollama_info.get('description', 'No description available')}",
            category=category,
            capabilities=capabilities,
            size=self._estimate_model_size(parameter_count),
            parameter_count=parameter_count,
            context_length=ollama_info.get("context_length", 4096),
            quantization_levels=["q4_0", "q5_0", "q8_0"],
            license="Unknown",
            creator="Unknown",
            performance_score=7.0,  # Default score
            memory_requirements_gb=parameter_count / 2_000_000_000,  # Rough estimate
            tags=["ollama", "loaded"],
            examples=["General text generation", "Conversation", "Task completion"]
        )

    def _estimate_model_size(self, parameter_count: int) -> ModelSize:
        """Estimate model size category based on parameter count."""
        if parameter_count < 1_000_000_000:
            return ModelSize.TINY
        elif parameter_count < 3_000_000_000:
            return ModelSize.SMALL
        elif parameter_count < 7_000_000_000:
            return ModelSize.MEDIUM
        elif parameter_count < 13_000_000_000:
            return ModelSize.LARGE
        elif parameter_count < 30_000_000_000:
            return ModelSize.XLARGE
        elif parameter_count < 70_000_000_000:
            return ModelSize.XXLARGE
        else:
            return ModelSize.MASSIVE

    async def get_model_recommendations(self, task_type: str, system_info: Dict[str, Any], 
                                      preferences: Optional[Dict[str, Any]] = None) -> List[ModelRecommendation]:
        """Get model recommendations for a specific task type."""
        try:
            # Get required capabilities for the task
            required_capabilities = self.task_capability_mapping.get(task_type, set())
            if not required_capabilities:
                logger.warning(f"Unknown task type: {task_type}")
                return []
            
            # Find models with required capabilities
            candidate_models = set()
            for capability in required_capabilities:
                candidate_models.update(self.capability_index.get(capability, set()))
            
            if not candidate_models:
                logger.warning(f"No models found for task type: {task_type}")
                return []
            
            # Evaluate each candidate model
            recommendations = []
            for model_name in candidate_models:
                metadata = self.model_registry.get(model_name)
                if not metadata:
                    continue
                
                # Check compatibility
                compatibility = await self.check_model_compatibility(model_name, system_info)
                
                # Calculate confidence score
                confidence_score = self._calculate_recommendation_confidence(
                    metadata, compatibility, required_capabilities, preferences
                )
                
                # Create recommendation
                recommendation = ModelRecommendation(
                    model_name=model_name,
                    confidence_score=confidence_score,
                    reasoning=self._generate_recommendation_reasoning(metadata, compatibility, task_type),
                    expected_performance={
                        "response_time_ms": compatibility.performance_estimate.get("expected_response_time_ms", 1000),
                        "memory_efficiency": compatibility.performance_estimate.get("memory_efficiency", 1.0),
                        "compatibility_score": compatibility.compatibility_score
                    },
                    alternatives=self._find_alternatives(model_name, candidate_models, system_info),
                    trade_offs=self._identify_trade_offs(metadata, compatibility)
                )
                
                recommendations.append(recommendation)
            
            # Sort by confidence score
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return recommendations[:5]  # Return top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error getting model recommendations: {e}")
            return []

    def _calculate_recommendation_confidence(self, metadata: ModelMetadata, 
                                           compatibility: ModelCompatibility,
                                           required_capabilities: Set[ModelCapability],
                                           preferences: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score for a model recommendation."""
        score = 0.0
        
        # Base score from compatibility
        score += compatibility.compatibility_score * 0.4
        
        # Capability match score
        capability_match = len(metadata.capabilities.intersection(required_capabilities)) / len(required_capabilities)
        score += capability_match * 0.3
        
        # Performance score
        score += (metadata.performance_score / 10.0) * 0.2
        
        # Size preference (if specified)
        if preferences and "preferred_size" in preferences:
            preferred_size = preferences["preferred_size"]
            if metadata.size.value == preferred_size:
                score += 0.1
        
        return min(score, 1.0)

    def _generate_recommendation_reasoning(self, metadata: ModelMetadata, 
                                         compatibility: ModelCompatibility, 
                                         task_type: str) -> str:
        """Generate reasoning for a model recommendation."""
        reasons = []
        
        # Capability reasoning
        if metadata.category == ModelCategory.CODE and "code" in task_type:
            reasons.append("Specialized for code-related tasks")
        elif metadata.category == ModelCategory.VISION and "image" in task_type:
            reasons.append("Optimized for vision and image understanding")
        elif metadata.category == ModelCategory.MATH and "math" in task_type:
            reasons.append("Designed for mathematical reasoning")
        
        # Performance reasoning
        if compatibility.compatibility_score > 0.8:
            reasons.append("Excellent system compatibility")
        elif compatibility.compatibility_score > 0.6:
            reasons.append("Good system compatibility")
        
        # Size reasoning
        if metadata.size in [ModelSize.SMALL, ModelSize.MEDIUM]:
            reasons.append("Efficient resource usage")
        elif metadata.size in [ModelSize.LARGE, ModelSize.XLARGE]:
            reasons.append("High-quality output")
        
        return "; ".join(reasons) if reasons else "General-purpose model suitable for the task"

    def _find_alternatives(self, primary_model: str, candidate_models: Set[str], 
                          system_info: Dict[str, Any]) -> List[str]:
        """Find alternative models to the primary recommendation."""
        alternatives = []
        primary_metadata = self.model_registry.get(primary_model)
        
        if not primary_metadata:
            return alternatives
        
        for model_name in candidate_models:
            if model_name == primary_model:
                continue
            
            metadata = self.model_registry.get(model_name)
            if not metadata:
                continue
            
            # Check if it's a good alternative (different size, similar capabilities)
            if (metadata.size != primary_metadata.size and 
                metadata.capabilities.intersection(primary_metadata.capabilities)):
                alternatives.append(model_name)
            
            if len(alternatives) >= 3:  # Limit to 3 alternatives
                break
        
        return alternatives

    def _identify_trade_offs(self, metadata: ModelMetadata, 
                            compatibility: ModelCompatibility) -> List[str]:
        """Identify trade-offs for a model recommendation."""
        trade_offs = []
        
        # Size trade-offs
        if metadata.size in [ModelSize.LARGE, ModelSize.XLARGE, ModelSize.XXLARGE]:
            trade_offs.append("Higher resource requirements")
            trade_offs.append("Slower inference speed")
        elif metadata.size in [ModelSize.SMALL, ModelSize.TINY]:
            trade_offs.append("Lower quality output")
            trade_offs.append("Limited reasoning capabilities")
        
        # Compatibility trade-offs
        if compatibility.compatibility_score < 0.7:
            trade_offs.append("May have performance issues")
        
        # Capability trade-offs
        if len(metadata.capabilities) < 3:
            trade_offs.append("Limited to specific task types")
        
        return trade_offs

    async def get_model_categories(self) -> Dict[ModelCategory, List[Dict[str, Any]]]:
        """Get models organized by category."""
        categories = {}
        
        for category in ModelCategory:
            models = []
            for model_name in self.category_index.get(category, []):
                metadata = self.model_registry.get(model_name)
                if metadata:
                    models.append({
                        "name": metadata.name,
                        "display_name": metadata.display_name,
                        "description": metadata.description,
                        "size": metadata.size.value,
                        "parameter_count": metadata.parameter_count,
                        "performance_score": metadata.performance_score,
                        "capabilities": [cap.value for cap in metadata.capabilities]
                    })
            
            categories[category] = models
        
        return categories

    async def search_models(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search models by query and filters."""
        results = []
        query_lower = query.lower()
        
        for model_name, metadata in self.model_registry.items():
            # Check if model matches query
            if (query_lower in model_name.lower() or 
                query_lower in metadata.display_name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                
                # Apply filters if specified
                if filters:
                    if not self._apply_model_filters(metadata, filters):
                        continue
                
                results.append({
                    "name": metadata.name,
                    "display_name": metadata.display_name,
                    "description": metadata.description,
                    "category": metadata.category.value,
                    "size": metadata.size.value,
                    "parameter_count": metadata.parameter_count,
                    "performance_score": metadata.performance_score,
                    "capabilities": [cap.value for cap in metadata.capabilities],
                    "tags": metadata.tags
                })
        
        # Sort by relevance (performance score for now)
        results.sort(key=lambda x: x["performance_score"], reverse=True)
        
        return results

    def _apply_model_filters(self, metadata: ModelMetadata, filters: Dict[str, Any]) -> bool:
        """Apply filters to a model."""
        # Category filter
        if "category" in filters and metadata.category.value != filters["category"]:
            return False
        
        # Size filter
        if "size" in filters and metadata.size.value != filters["size"]:
            return False
        
        # Capability filter
        if "capabilities" in filters:
            required_capabilities = set(filters["capabilities"])
            if not required_capabilities.issubset(metadata.capabilities):
                return False
        
        # Performance score filter
        if "min_performance" in filters and metadata.performance_score < filters["min_performance"]:
            return False
        
        # Parameter count filter
        if "max_parameters" in filters and metadata.parameter_count > filters["max_parameters"]:
            return False
        
        return True

    async def get_model_comparison(self, model_names: List[str]) -> Dict[str, Any]:
        """Compare multiple models side by side."""
        comparison = {
            "models": [],
            "comparison_table": {},
            "recommendations": []
        }
        
        for model_name in model_names:
            metadata = self.model_registry.get(model_name)
            if metadata:
                comparison["models"].append({
                    "name": metadata.name,
                    "display_name": metadata.display_name,
                    "category": metadata.category.value,
                    "size": metadata.size.value,
                    "parameter_count": metadata.parameter_count,
                    "context_length": metadata.context_length,
                    "performance_score": metadata.performance_score,
                    "memory_requirements_gb": metadata.memory_requirements_gb,
                    "capabilities": [cap.value for cap in metadata.capabilities],
                    "tags": metadata.tags
                })
        
        # Create comparison table
        if comparison["models"]:
            comparison["comparison_table"] = {
                "Parameter Count": [m["parameter_count"] for m in comparison["models"]],
                "Performance Score": [m["performance_score"] for m in comparison["models"]],
                "Memory Requirements (GB)": [m["memory_requirements_gb"] for m in comparison["models"]],
                "Context Length": [m["context_length"] for m in comparison["models"]]
            }
        
        # Generate recommendations
        comparison["recommendations"] = self._generate_comparison_recommendations(comparison["models"])
        
        return comparison

    def _generate_comparison_recommendations(self, models: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on model comparison."""
        recommendations = []
        
        if not models:
            return recommendations
        
        # Find best performance model
        best_performance = max(models, key=lambda x: x["performance_score"])
        recommendations.append(f"Best overall performance: {best_performance['display_name']} (Score: {best_performance['performance_score']})")
        
        # Find most efficient model
        most_efficient = min(models, key=lambda x: x["memory_requirements_gb"])
        recommendations.append(f"Most memory efficient: {most_efficient['display_name']} ({most_efficient['memory_requirements_gb']}GB)")
        
        # Find largest context model
        largest_context = max(models, key=lambda x: x["context_length"])
        recommendations.append(f"Largest context window: {largest_context['display_name']} ({largest_context['context_length']} tokens)")
        
        # Find smallest model
        smallest = min(models, key=lambda x: x["parameter_count"])
        recommendations.append(f"Fastest inference: {smallest['display_name']} ({smallest['parameter_count']:,} parameters)")
        
        return recommendations

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.client.aclose()
            logger.info("Ollama Model Library cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up Ollama Model Library: {e}")

# Global instance for easy access
ollama_model_library = OllamaModelLibrary()
