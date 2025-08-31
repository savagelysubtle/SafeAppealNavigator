"""
Agents Package - Pure PydanticAI Implementation

This package contains AI agents built using pure PydanticAI patterns without
custom decorators or enhanced wrappers. All agents support native A2A protocol
conversion and MCP tool integration.

Components:
    base_pydantic_agent: Base agent class following PydanticAI patterns
    base_pydantic_agent_config: Configuration model for agents
"""

from .base_pydantic_agent import BasePydanticAgent
from .base_pydantic_agent_config import BasePydanticAgentConfig

__all__ = ["BasePydanticAgent", "BasePydanticAgentConfig"]
