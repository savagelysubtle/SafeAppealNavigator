# src/savagelysubtle_airesearchagent/mcp_integration/mcp_client_utils.py
# This file's purpose is for agents (primarily the Orchestrator) to communicate with *this* MCP server.
import httpx
import logging
from typing import Any, Dict, Optional, List

from ..config.global_settings import settings

logger = logging.getLogger(__name__)

async def find_agent_for_task_on_mcp(task_description: str) -> Optional[Dict[str, Any]]:
    """
    Calls the 'find_agent_for_task' tool on our custom MCP server (Registry).
    """
    mcp_server_url = settings.MCP_SERVER_URL
    # This endpoint is provided by *our* MCP server (server_main.py)
    tool_call_url = f"{mcp_server_url}/mcp_tool/find_agent_for_task"

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Calling {tool_call_url} with task_description: '{task_description}'")
            response = await client.post(tool_call_url, json={"task_description": task_description})
            response.raise_for_status()
            agent_card = response.json()
            logger.info(f"Received agent card for task '{task_description}': {agent_card.get('agent_id') if agent_card else 'None'}")
            return agent_card
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling find_agent_for_task: {e.response.status_code} - {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error calling find_agent_for_task: {e}", exc_info=True)
    return None

async def list_all_agents_on_mcp() -> List[Dict[str, Any]]:
    """
    Calls the 'list_all_agents' tool on our custom MCP server (Registry).
    """
    mcp_server_url = settings.MCP_SERVER_URL
    tool_call_url = f"{mcp_server_url}/mcp_tool/list_all_agents"

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Calling {tool_call_url} to list all agents")
            response = await client.get(tool_call_url)
            response.raise_for_status()
            agent_list = response.json()
            logger.info(f"Received {len(agent_list)} agent cards.")
            return agent_list
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling list_all_agents: {e.response.status_code} - {e.response.text}", exc_info=True)
    except Exception as e:
        logger.error(f"Error calling list_all_agents: {e}", exc_info=True)
    return []

# --- End of src/savagelysubtle_airesearchagent/mcp_integration/mcp_client_utils.py ---