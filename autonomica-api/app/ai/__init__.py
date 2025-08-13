"""
AI Package

Unified AI model management system for the Autonomica multi-agent platform.
Provides intelligent model selection, cost optimization, and failover capabilities.
"""

from .ai_manager import ai_manager
from .model_interface import (
    AIModelInterface,
    ModelRegistry,
    ModelSelector,
    TokenTracker,
    ModelProvider,
    ModelConfig,
    ModelCapabilities,
    TokenUsage
)

__all__ = [
    "ai_manager",
    "AIModelInterface",
    "ModelRegistry", 
    "ModelSelector",
    "TokenTracker",
    "ModelProvider",
    "ModelConfig",
    "ModelCapabilities",
    "TokenUsage"
]
