"""
MCP Integration Module

This module provides Model Context Protocol (MCP) integration for the AI Research Assistant.
It manages MCP server connections and distributes tools to agents based on configuration.
"""

from .mcp_client_manager import (
    MCPClientManager,
    get_mcp_client_manager,
    shutdown_mcp_client_manager,
)

__all__ = [
    "MCPClientManager",
    "get_mcp_client_manager",
    "shutdown_mcp_client_manager",
]
