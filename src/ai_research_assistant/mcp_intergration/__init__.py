"""
MCP Integration Module

This module provides Model Context Protocol (MCP) integration for the AI Research Assistant.
It manages MCP server connections and distributes tools to agents based on configuration.
"""

from .unified_mcp_client import (
    UnifiedMCPClientManager as MCPClientManager,
)
from .unified_mcp_client import (
    get_unified_mcp_client_manager as get_mcp_client_manager,
)
from .unified_mcp_client import (
    shutdown_unified_mcp_client_manager as shutdown_mcp_client_manager,
)

__all__ = [
    "MCPClientManager",
    "get_mcp_client_manager",
    "shutdown_mcp_client_manager",
]
