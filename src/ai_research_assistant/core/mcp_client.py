"""
MCP Client utilities for AI Research Assistant

Provides utilities for setting up MCP clients and creating tool parameter models.
"""

import logging
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


def create_tool_param_model(tool) -> Type[BaseModel]:
    """Create a Pydantic model for MCP tool parameters."""
    try:
        # Extract parameters from tool schema if available
        if hasattr(tool, "inputSchema") and tool.inputSchema:
            schema = tool.inputSchema
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Build field definitions for pydantic model
            field_definitions = {}
            for field_name, field_schema in properties.items():
                field_type = field_schema.get("type", "string")
                field_description = field_schema.get("description", "")

                # Map JSON schema types to Python types
                python_type = str  # default
                if field_type == "integer":
                    python_type = int
                elif field_type == "number":
                    python_type = float
                elif field_type == "boolean":
                    python_type = bool
                elif field_type == "array":
                    python_type = list
                elif field_type == "object":
                    python_type = dict

                # Make optional if not required
                if field_name not in required:
                    python_type = Optional[python_type]
                    field_definitions[field_name] = (python_type, None)
                else:
                    field_definitions[field_name] = (python_type, ...)

            # Create dynamic model
            model_name = f"{tool.name.replace('-', '_').title()}Params"
            return create_model(model_name, **field_definitions)
        else:
            # Fallback to empty model
            return create_model(f"{tool.name.replace('-', '_').title()}Params")

    except Exception as e:
        logger.error(f"Error creating tool param model for {tool.name}: {e}")
        # Return minimal model as fallback
        return create_model(f"{tool.name.replace('-', '_').title()}Params")


class MCPClient:
    """Simple MCP client wrapper for managing server connections."""

    def __init__(self):
        self.server_name_to_tools: Dict[str, list] = {}
        self.connections: Dict[str, Any] = {}

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup connections when exiting."""
        for connection in self.connections.values():
            try:
                if hasattr(connection, "close"):
                    await connection.close()
            except Exception as e:
                logger.error(f"Error closing MCP connection: {e}")


async def setup_mcp_client_and_tools(
    mcp_server_config: Dict[str, Any],
) -> Optional[MCPClient]:
    """
    Setup MCP client and tools based on configuration.

    Args:
        mcp_server_config: Configuration dictionary for MCP servers

    Returns:
        MCPClient instance or None if setup fails
    """
    try:
        client = MCPClient()

        # For now, return a basic client
        # TODO: Implement actual MCP server connections based on config
        logger.info("MCP client setup initialized (placeholder implementation)")

        return client

    except Exception as e:
        logger.error(f"Failed to setup MCP client: {e}")
        return None
