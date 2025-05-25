"""
Configuration management for AI Research Assistant

This module provides centralized configuration management including:
- MCP server configurations
- Agent-to-MCP tool mappings
- Development and runtime settings
"""

from .mcp_client_config import (
    MCPConfigLoader,
    get_agent_mcp_tools,
    get_server_startup_config,
    mcp_config,
    validate_agent_mcp_setup,
)

__all__ = [
    "MCPConfigLoader",
    "mcp_config",
    "get_agent_mcp_tools",
    "validate_agent_mcp_setup",
    "get_server_startup_config",
]
