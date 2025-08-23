"""
Agent Integration for MCP Tools

This module provides lightweight helper functions for MCP tool integration with agents.
Most functionality is now handled by MCPClientManager directly.
"""

import logging

logger = logging.getLogger(__name__)


# Specialized agent mappings for the AI Research Assistant
AGENT_TYPE_MAPPINGS = {
    # Phase 1 agents from your system
    "DocumentAgent": "DocumentAgent",
    "BrowserAgent": "BrowserAgent",
    "DatabaseAgent": "DatabaseAgent",
    "OrchestratorAgent": "OrchestratorAgent",
    "CEOAgent": "CEOAgent",
    # Alternative names
    "DocumentProcessingCoordinator": "DocumentAgent",
    "LegalResearchCoordinator": "BrowserAgent",
    "DataQueryCoordinator": "DatabaseAgent",
    "ChiefLegalOrchestrator": "OrchestratorAgent",
    # Legal specific agents
    "LegalManagerAgent": "LegalManagerAgent",
    "LegalCaseAgent": "LegalCaseAgent",
    "IntakeAgent": "IntakeAgent",
    "EnhancedLegalIntakeAgent": "EnhancedLegalIntakeAgent",
    # Research agents
    "DeepResearchAgent": "DeepResearchAgent",
    "CrossReferenceAgent": "CrossReferenceAgent",
    "SearchAgent": "SearchAgent",
}


def normalize_agent_name(agent_name: str) -> str:
    """
    Normalize agent name to match configuration mappings.

    Args:
        agent_name: Original agent name

    Returns:
        Normalized agent name
    """
    return AGENT_TYPE_MAPPINGS.get(agent_name, agent_name)


# NOTE: Most MCP functionality is now handled directly by MCPClientManager:
# - inject_mcp_tools_into_agent() -> Use MCPClientManager.get_tools_for_agent()
# - get_mcp_tools_for_agent_type() -> Use MCPClientManager.get_tools_for_agent()
# - get_mcp_server_status() -> Use MCPClientManager.get_server_status()
# - call_mcp_tool_directly() -> Use MCPClientManager.call_tool()
# - get_agent_mcp_mapping() -> Handled internally by MCPClientManager
#
# See mcp_client_manager.py for the new implementation patterns.
#
# To use MCP tools with agents:
# ```python
# from ai_research_assistant.mcp_intergration import get_mcp_client_manager
#
# # Get tools for an agent
# mcp_manager = await get_mcp_client_manager()
# tools = mcp_manager.get_tools_for_agent("DocumentAgent")
#
# # Get server status
# status = mcp_manager.get_server_status()
#
# # Call a tool directly
# result = await mcp_manager.call_tool("server_name", "tool_name", arguments)
# ```
