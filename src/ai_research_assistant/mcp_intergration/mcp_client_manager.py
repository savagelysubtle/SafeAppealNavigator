"""
MCP Client Manager for AI Research Assistant

This module manages MCP server connections, tool registration, and distribution to agents.
It reads configuration from data/mcp.json and provides tools to the appropriate agents.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field, create_model
from pydantic_ai.tools import Tool as PydanticAITool

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for an individual MCP server."""

    name: str
    type: str = "stdio"  # stdio or http
    command: Optional[str] = None
    args: Optional[List[str]] = Field(default_factory=list)
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    enabled: bool = True
    # For HTTP transport
    baseApiUrl: Optional[str] = None
    apiKey: Optional[str] = None


class MCPConfiguration(BaseModel):
    """Complete MCP configuration from mcp.json."""

    mcpServers: Dict[str, MCPServerConfig]


class MCPToolWrapper:
    """Wrapper for MCP tools to make them compatible with Pydantic AI."""

    def __init__(
        self,
        tool_name: str,
        tool_description: str,
        client_session: ClientSession,
        server_name: str,
    ):
        self.tool_name = tool_name
        self.tool_description = tool_description
        self.client_session = client_session
        self.server_name = server_name
        self._param_model = None

    def create_param_model(self, input_schema: Dict[str, Any]) -> type[BaseModel]:
        """Create a Pydantic model from MCP tool input schema."""
        if self._param_model is not None:
            return self._param_model

        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

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
                python_type = List[Any]
            elif field_type == "object":
                python_type = Dict[str, Any]

            # Make optional if not required
            if field_name not in required:
                python_type = Optional[python_type]
                field_definitions[field_name] = (
                    python_type,
                    Field(default=None, description=field_description),
                )
            else:
                field_definitions[field_name] = (
                    python_type,
                    Field(..., description=field_description),
                )

        model_name = (
            f"{self.server_name}_{self.tool_name.replace('-', '_').title()}Params"
        )
        self._param_model = create_model(model_name, **field_definitions)
        return self._param_model

    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """Execute the MCP tool."""
        try:
            result = await self.client_session.call_tool(
                name=self.tool_name, arguments=kwargs
            )

            # Extract content from result
            if hasattr(result, "content"):
                # Handle different content types
                content_items = []
                for item in result.content:
                    # Generic handling of content items
                    if hasattr(item, "text"):
                        content_items.append(getattr(item, "text", str(item)))
                    elif hasattr(item, "data"):
                        content_items.append("[Binary data]")
                    else:
                        content_items.append(str(item))

                return {
                    "success": True,
                    "result": "\n".join(content_items)
                    if content_items
                    else "Tool executed successfully",
                    "server": self.server_name,
                    "tool": self.tool_name,
                }
            else:
                return {
                    "success": True,
                    "result": str(result),
                    "server": self.server_name,
                    "tool": self.tool_name,
                }
        except Exception as e:
            logger.error(
                f"Error calling MCP tool {self.tool_name} on server {self.server_name}: {e}"
            )
            return {
                "success": False,
                "error": str(e),
                "server": self.server_name,
                "tool": self.tool_name,
            }


class MCPClientManager:
    """Manages MCP server connections and tool distribution to agents."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.config: Optional[MCPConfiguration] = None
        self.server_sessions: Dict[str, ClientSession] = {}
        self.server_tools: Dict[str, List[Dict[str, Any]]] = {}
        self.wrapped_tools: Dict[str, List[PydanticAITool]] = {}
        self._agent_mapping_config = None
        self._load_agent_mapping()

    def _find_config_path(self) -> str:
        """Find the mcp.json configuration file."""
        # Try multiple possible locations
        possible_paths = [
            Path("data/mcp.json"),
            Path("../../../data/mcp.json"),
            Path(__file__).parent.parent.parent.parent / "data" / "mcp.json",
            Path(os.getcwd()) / "data" / "mcp.json",
        ]

        for path in possible_paths:
            if path.exists():
                logger.info(f"Found MCP config at: {path}")
                return str(path.resolve())

        raise FileNotFoundError("Could not find mcp.json configuration file")

    def _load_agent_mapping(self):
        """Load agent to MCP tool mapping configuration."""
        mapping_path = (
            Path(__file__).parent.parent
            / "config"
            / "mcp_config"
            / "agent_mcp_mapping.json"
        )
        if mapping_path.exists():
            with open(mapping_path, "r") as f:
                self._agent_mapping_config = json.load(f)
                logger.info("Loaded agent MCP mapping configuration")
        else:
            logger.warning(f"Agent MCP mapping file not found at {mapping_path}")
            self._agent_mapping_config = {"agent_mcp_mappings": {}}

    def load_configuration(self) -> MCPConfiguration:
        """Load MCP configuration from mcp.json."""
        with open(self.config_path, "r") as f:
            data = json.load(f)

        # Convert to MCPConfiguration format
        config_data = {"mcpServers": {}}

        if "mcpServers" in data:
            # Standard MCP format
            for server_name, server_config in data["mcpServers"].items():
                config_data["mcpServers"][server_name] = MCPServerConfig(
                    name=server_name, **server_config
                )
        else:
            # Try to parse as array format (from SettingsPage)
            logger.warning("Non-standard MCP configuration format detected")

        self.config = MCPConfiguration(**config_data)
        logger.info(f"Loaded {len(self.config.mcpServers)} MCP server configurations")
        return self.config

    async def initialize_server(
        self, server_name: str, server_config: MCPServerConfig
    ) -> Optional[ClientSession]:
        """Initialize a single MCP server connection."""
        if not server_config.enabled:
            logger.info(f"Server {server_name} is disabled, skipping initialization")
            return None

        try:
            if server_config.type == "stdio":
                if not server_config.command:
                    logger.error(f"No command specified for stdio server {server_name}")
                    return None

                # Create stdio server parameters
                server_params = StdioServerParameters(
                    command=server_config.command,
                    args=server_config.args or [],
                    cwd=server_config.cwd,
                    env={**os.environ, **(server_config.env or {})},
                )

                # Create client session using async context manager
                async with stdio_client(server_params) as (read_stream, write_stream):
                    session = ClientSession(read_stream, write_stream)

                    # Initialize the session
                    await session.initialize()

                    logger.info(f"Successfully initialized MCP server: {server_name}")
                    return session

            elif server_config.type == "http":
                logger.warning(
                    f"HTTP transport not yet implemented for server: {server_name}"
                )
                return None

            else:
                logger.error(
                    f"Unknown transport type for server {server_name}: {server_config.type}"
                )
                return None

        except Exception as e:
            logger.error(f"Failed to initialize MCP server {server_name}: {e}")
            return None

    async def initialize_all_servers(self):
        """Initialize all enabled MCP servers."""
        if not self.config:
            self.load_configuration()

        if not self.config:
            logger.error("No configuration loaded")
            return

        tasks = []
        for server_name, server_config in self.config.mcpServers.items():
            if server_config.enabled:
                tasks.append(
                    (server_name, self.initialize_server(server_name, server_config))
                )

        # Initialize servers concurrently
        for server_name, task in tasks:
            session = await task
            if session:
                self.server_sessions[server_name] = session
                # Fetch tools for this server
                await self._fetch_server_tools(server_name, session)

    async def _fetch_server_tools(self, server_name: str, session: ClientSession):
        """Fetch available tools from an MCP server."""
        try:
            result = await session.list_tools()
            tools = []
            wrapped = []

            for tool in result.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema
                    if isinstance(tool.inputSchema, dict)
                    else (
                        tool.inputSchema.model_dump()
                        if hasattr(tool.inputSchema, "model_dump")
                        else {}
                    ),
                }
                tools.append(tool_info)

                # Create wrapped tool for Pydantic AI
                wrapper = MCPToolWrapper(
                    tool_name=tool.name,
                    tool_description=tool.description or "",
                    client_session=session,
                    server_name=server_name,
                )

                # Create parameter model if schema is available
                input_schema = tool_info["inputSchema"]
                if input_schema:
                    param_model = wrapper.create_param_model(input_schema)
                else:
                    param_model = create_model(f"{server_name}_{tool.name}_Params")

                # Create Pydantic AI tool
                async def create_tool_func(w=wrapper, pm=param_model):
                    async def tool_func(**kwargs) -> Dict[str, Any]:
                        return await w(**kwargs)

                    return tool_func

                tool_func = await create_tool_func()
                tool_func.__name__ = f"mcp_{server_name}_{tool.name}"
                tool_func.__doc__ = (
                    tool.description or f"MCP tool {tool.name} from {server_name}"
                )

                pydantic_tool = PydanticAITool(
                    function=tool_func,
                    name=f"mcp_{server_name}_{tool.name}",
                    description=tool.description
                    or f"MCP tool {tool.name} from {server_name}",
                )
                wrapped.append(pydantic_tool)

            self.server_tools[server_name] = tools
            self.wrapped_tools[server_name] = wrapped

            logger.info(f"Fetched {len(tools)} tools from server {server_name}")

        except Exception as e:
            logger.error(f"Failed to fetch tools from server {server_name}: {e}")
            self.server_tools[server_name] = []
            self.wrapped_tools[server_name] = []

    def get_tools_for_agent(self, agent_name: str) -> List[PydanticAITool]:
        """Get MCP tools appropriate for a specific agent based on mapping configuration."""
        tools = []

        if not self._agent_mapping_config:
            logger.warning("No agent mapping configuration loaded")
            return tools

        agent_config = self._agent_mapping_config.get("agent_mcp_mappings", {}).get(
            agent_name
        )
        if not agent_config:
            logger.info(f"No MCP mapping found for agent: {agent_name}")
            return tools

        # Get tools from required servers
        for server_name in agent_config.get("required_servers", []):
            if server_name in self.wrapped_tools:
                tools.extend(self.wrapped_tools[server_name])
            else:
                logger.warning(
                    f"Required server {server_name} not available for agent {agent_name}"
                )

        # Get tools from optional servers if available
        for server_name in agent_config.get("optional_servers", []):
            if server_name in self.wrapped_tools:
                tools.extend(self.wrapped_tools[server_name])

        # Filter to only primary tools if specified
        primary_tools = agent_config.get("primary_tools", [])
        if primary_tools:
            filtered_tools = []
            for tool in tools:
                if any(tool.name.endswith(pt) for pt in primary_tools):
                    filtered_tools.append(tool)
            tools = filtered_tools

        logger.info(f"Providing {len(tools)} MCP tools to agent {agent_name}")
        return tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool on a specific server."""
        if server_name not in self.server_sessions:
            return {"error": f"Server {server_name} not initialized"}

        session = self.server_sessions[server_name]
        try:
            result = await session.call_tool(name=tool_name, arguments=arguments)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on server {server_name}: {e}")
            return {"success": False, "error": str(e)}

    async def shutdown(self):
        """Shutdown all MCP server connections."""
        for server_name, session in self.server_sessions.items():
            try:
                # Try to close the session if the method exists
                if hasattr(session, "__aexit__"):
                    await session.__aexit__(None, None, None)
                logger.info(f"Closed connection to server {server_name}")
            except Exception as e:
                logger.error(f"Error closing connection to server {server_name}: {e}")

        self.server_sessions.clear()
        self.server_tools.clear()
        self.wrapped_tools.clear()

    def get_all_tools(self) -> Dict[str, List[PydanticAITool]]:
        """Get all available tools organized by server."""
        return self.wrapped_tools.copy()

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        status = {
            "configured_servers": len(self.config.mcpServers) if self.config else 0,
            "connected_servers": len(self.server_sessions),
            "total_tools": sum(len(tools) for tools in self.server_tools.values()),
            "servers": {},
        }

        if self.config:
            for server_name, server_config in self.config.mcpServers.items():
                status["servers"][server_name] = {
                    "enabled": server_config.enabled,
                    "connected": server_name in self.server_sessions,
                    "tool_count": len(self.server_tools.get(server_name, [])),
                    "type": server_config.type,
                }

        return status


# Global MCP client manager instance
_mcp_client_manager: Optional[MCPClientManager] = None


async def get_mcp_client_manager() -> MCPClientManager:
    """Get or create the global MCP client manager instance."""
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
        await _mcp_client_manager.initialize_all_servers()
    return _mcp_client_manager


async def shutdown_mcp_client_manager():
    """Shutdown the global MCP client manager."""
    global _mcp_client_manager
    if _mcp_client_manager:
        await _mcp_client_manager.shutdown()
        _mcp_client_manager = None
