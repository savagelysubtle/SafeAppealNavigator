"""
Configuration management for AI Research Assistant.
"""

# --- REWRITTEN to export the correct objects ---

from .mcp_config import (
    MCPConfigLoader,
    get_agent_mcp_tools,
    mcp_config,
    validate_agent_mcp_setup,
)

__all__ = [
    "MCPConfigLoader",
    "mcp_config",
    "get_agent_mcp_tools",
    "validate_agent_mcp_setup",
]
