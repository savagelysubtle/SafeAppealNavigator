"""
Core agent architecture components for AI Research Assistant.

This module provides the foundational components for building specialized agents
with standardized configuration, resource management, and observability.
"""

from .base_agent import (
    AgentConfig,
    AgentTask,
    BaseAgent,
    TaskPriority,
    TaskStatus,
)

__all__ = [
    "AgentConfig",
    "AgentTask",
    "BaseAgent",
    "TaskPriority",
    "TaskStatus",
]
