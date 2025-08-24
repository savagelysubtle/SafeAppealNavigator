# src/ai_research_assistant/mcp/client.py
import logging
from typing import List, Optional

from pydantic_ai.mcp import (
    MCPServer,
    MCPServerSSE,
    MCPServerStdio,
    MCPServerStreamableHTTP,
)

# --- FIX: Import the INSTANCE from the config package ---
from ..config import mcp_config

logger = logging.getLogger(__name__)


def create_mcp_toolsets_from_config() -> List[MCPServer]:
    """
    Reads the mcp.json configuration and creates a list of MCPServer
    instances which act as toolsets for a pydantic-ai Agent.
    """
    logger.info("Creating MCP toolsets from configuration...")
    toolsets: List[MCPServer] = []
    try:
        # --- FIX: Use the mcp_config INSTANCE here ---
        server_configs = mcp_config.load_mcp_config().get("mcpServers", {})

        for server_name, config in server_configs.items():
            if not config.get("enabled", True):
                logger.debug(f"Skipping disabled server: {server_name}")
                continue

            transport_type = config.get("type", "stdio")
            tool_prefix = f"{server_name}_"
            server_toolset: Optional[MCPServer] = None

            if transport_type == "stdio":
                command = config.get("command")
                if not command:
                    logger.warning(
                        f"No command specified for stdio server '{server_name}'. Skipping."
                    )
                    continue

                server_toolset = MCPServerStdio(
                    command=command,
                    args=config.get("args", []),
                    cwd=config.get("cwd"),
                    env=config.get("env"),
                    tool_prefix=tool_prefix,
                )
                logger.info(f"Created MCPServerStdio toolset for '{server_name}'")

            elif transport_type == "sse":
                url = config.get("url")
                if not url:
                    logger.warning(
                        f"No URL specified for SSE server '{server_name}'. Skipping."
                    )
                    continue
                server_toolset = MCPServerSSE(url=url, tool_prefix=tool_prefix)
                logger.info(f"Created MCPServerSSE toolset for '{server_name}'")

            elif transport_type == "streamable-http":
                url = config.get("url")
                if not url:
                    logger.warning(
                        f"No URL specified for Streamable HTTP server '{server_name}'. Skipping."
                    )
                    continue
                server_toolset = MCPServerStreamableHTTP(
                    url=url, tool_prefix=tool_prefix
                )
                logger.info(
                    f"Created MCPServerStreamableHTTP toolset for '{server_name}'"
                )

            else:
                logger.warning(
                    f"Unsupported MCP transport type '{transport_type}' for server '{server_name}'. Skipping."
                )

            if server_toolset:
                toolsets.append(server_toolset)

    except Exception as e:
        logger.error(f"Failed to create MCP toolsets from config: {e}", exc_info=True)
        return []

    logger.info(f"Successfully created {len(toolsets)} MCP toolsets.")
    return toolsets
