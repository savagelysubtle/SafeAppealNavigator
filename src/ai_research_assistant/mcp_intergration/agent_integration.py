"""
Agent Integration for MCP Tools

This module provides helper functions to integrate MCP tools with agents.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.mcp_intergration import get_mcp_client_manager

logger = logging.getLogger(__name__)


async def inject_mcp_tools_into_agent(
    agent: BasePydanticAgent, agent_name: Optional[str] = None
) -> List[PydanticAITool]:
    """
    Inject appropriate MCP tools into an agent based on configuration.

    Args:
        agent: The agent instance to inject tools into
        agent_name: Optional override for agent name (defaults to agent's class name)

    Returns:
        List of injected tools
    """
    if agent_name is None:
        agent_name = agent.__class__.__name__

    logger.info(f"Injecting MCP tools into {agent_name}")

    try:
        # Get MCP client manager
        mcp_manager = await get_mcp_client_manager()

        # Get tools for this agent
        mcp_tools = mcp_manager.get_tools_for_agent(agent_name)

        if mcp_tools:
            # Add tools to agent's tool list
            if hasattr(agent, "tools") and isinstance(agent.tools, list):
                agent.tools.extend(mcp_tools)
                logger.info(
                    f"Added {len(mcp_tools)} MCP tools to {agent_name}'s tools list"
                )

            # Note: The pydantic_agent will use the tools from agent.tools when initialized
            # or when tools are accessed via agent._get_initial_tools()

            logger.info(f"Injected {len(mcp_tools)} MCP tools into {agent_name}")
        else:
            logger.info(f"No MCP tools configured for {agent_name}")

        return mcp_tools

    except Exception as e:
        logger.error(f"Failed to inject MCP tools into {agent_name}: {e}")
        return []


async def get_mcp_tools_for_agent_type(agent_type: str) -> List[PydanticAITool]:
    """
    Get MCP tools configured for a specific agent type without injecting them.

    Args:
        agent_type: Name of the agent type (e.g., 'BrowserAgent', 'DocumentAgent')

    Returns:
        List of MCP tools configured for this agent type
    """
    try:
        mcp_manager = await get_mcp_client_manager()
        return mcp_manager.get_tools_for_agent(agent_type)
    except Exception as e:
        logger.error(f"Failed to get MCP tools for agent type {agent_type}: {e}")
        return []


async def get_mcp_server_status() -> Dict[str, Any]:
    """
    Get the current status of all MCP servers.

    Returns:
        Dictionary containing server status information
    """
    try:
        mcp_manager = await get_mcp_client_manager()
        return mcp_manager.get_server_status()
    except Exception as e:
        logger.error(f"Failed to get MCP server status: {e}")
        return {
            "error": str(e),
            "configured_servers": 0,
            "connected_servers": 0,
            "total_tools": 0,
            "servers": {},
        }


async def call_mcp_tool_directly(
    server_name: str, tool_name: str, arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Call an MCP tool directly without going through an agent.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        arguments: Arguments to pass to the tool

    Returns:
        Tool execution result
    """
    try:
        mcp_manager = await get_mcp_client_manager()
        return await mcp_manager.call_tool(server_name, tool_name, arguments)
    except Exception as e:
        logger.error(
            f"Failed to call MCP tool {tool_name} on server {server_name}: {e}"
        )
        return {"success": False, "error": str(e)}


def get_agent_mcp_mapping() -> Dict[str, Dict[str, Any]]:
    """
    Get the agent to MCP server/tool mapping configuration.

    Returns:
        Dictionary mapping agent names to their MCP configuration
    """
    try:
        import json
        from pathlib import Path

        mapping_path = (
            Path(__file__).parent.parent
            / "config"
            / "mcp_config"
            / "agent_mcp_mapping.json"
        )
        if mapping_path.exists():
            with open(mapping_path, "r") as f:
                data = json.load(f)
                return data.get("agent_mcp_mappings", {})
    except Exception as e:
        logger.error(f"Failed to load agent MCP mapping: {e}")

    return {}


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
