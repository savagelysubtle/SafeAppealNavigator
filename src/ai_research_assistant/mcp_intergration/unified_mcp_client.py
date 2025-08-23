"""
Unified MCP Client Manager for AI Research Assistant

This module provides a unified MCP client that supports both stdio and HTTP transports,
combining the best of the previous implementations into a single, comprehensive solution.
"""

import json
import logging
import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from pydantic_ai.tools import Tool as PydanticAITool

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for an individual MCP server supporting multiple transports."""

    name: str
    type: str = "stdio"  # stdio, http, or websocket
    enabled: bool = True

    # For stdio transport
    command: Optional[str] = None
    args: Optional[List[str]] = Field(default_factory=list)
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None

    # For HTTP transport
    baseApiUrl: Optional[str] = None
    apiKey: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # For websocket transport (future)
    websocketUrl: Optional[str] = None


class UnifiedMCPServerConnection:
    """Unified connection handler supporting multiple MCP transport types."""

    def __init__(self, name: str, config: MCPServerConfig):
        self.name = name
        self.config = config
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.http_client: Optional[httpx.AsyncClient] = None
        self.tools: List[Any] = []
        self.wrapped_tools: List[PydanticAITool] = []
        self.connected = False

    async def connect(self) -> bool:
        """Connect to the MCP server using the appropriate transport."""
        if not self.config.enabled:
            logger.info(f"Server {self.name} is disabled, skipping connection")
            return False

        try:
            if self.config.type == "stdio":
                return await self._connect_stdio()
            elif self.config.type == "http":
                return await self._connect_http()
            else:
                logger.error(f"Unsupported transport type: {self.config.type}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.name}: {e}")
            self.connected = False
            return False

    async def _connect_stdio(self) -> bool:
        """Connect using stdio transport (subprocess)."""
        if not self.config.command:
            logger.error(f"No command specified for stdio server {self.name}")
            return False

        # Create server parameters
        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args or [],
            cwd=self.config.cwd,
            env={**os.environ, **(self.config.env or {})},
        )

        # Connect using proper MCP pattern
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read_stream, write_stream = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        # Initialize the session
        await self.session.initialize()

        # Discover tools
        await self._discover_tools_stdio()

        self.connected = True
        logger.info(f"Connected to stdio MCP server: {self.name}")
        return True

    async def _connect_http(self) -> bool:
        """Connect using HTTP transport."""
        if not self.config.baseApiUrl:
            logger.error(f"No baseApiUrl specified for HTTP server {self.name}")
            return False

        # Set up HTTP client with proper headers
        headers = {"Content-Type": "application/json"}
        if self.config.apiKey:
            headers["Authorization"] = f"Bearer {self.config.apiKey}"
        if self.config.headers:
            headers.update(self.config.headers)

        self.http_client = httpx.AsyncClient(
            base_url=self.config.baseApiUrl, headers=headers, timeout=30.0
        )

        # Test connection and discover tools
        await self._discover_tools_http()

        self.connected = True
        logger.info(f"Connected to HTTP MCP server: {self.name}")
        return True

    async def _discover_tools_stdio(self):
        """Discover tools from stdio MCP server."""
        if not self.session:
            return

        try:
            # List tools from server
            response = await self.session.list_tools()
            self.tools = response.tools

            # Create wrapped tools for Pydantic AI
            self.wrapped_tools = []
            for tool in self.tools:
                wrapped_tool = self._create_pydantic_tool_stdio(tool)
                if wrapped_tool:
                    self.wrapped_tools.append(wrapped_tool)

            logger.info(
                f"Discovered {len(self.tools)} tools from stdio server {self.name}"
            )

        except Exception as e:
            logger.error(f"Failed to discover tools from stdio server {self.name}: {e}")
            self.tools = []
            self.wrapped_tools = []

    async def _discover_tools_http(self):
        """Discover tools from HTTP MCP server."""
        if not self.http_client:
            return

        try:
            # Attempt to fetch tools from standard endpoints
            tools_endpoints = [
                "/mcp/tools",
                "/tools",
                "/mcp_tool/list_all_tools",
                "/api/tools",
            ]

            tool_defs = None
            for endpoint in tools_endpoints:
                try:
                    response = await self.http_client.get(endpoint)
                    if response.status_code == 200:
                        tool_defs = response.json()
                        break
                except Exception:
                    continue

            if not tool_defs:
                logger.warning(f"Could not fetch tools from HTTP server {self.name}")
                return

            # Convert to tool objects and wrap
            self.tools = tool_defs if isinstance(tool_defs, list) else [tool_defs]
            self.wrapped_tools = []

            for tool_def in self.tools:
                wrapped_tool = self._create_pydantic_tool_http(tool_def)
                if wrapped_tool:
                    self.wrapped_tools.append(wrapped_tool)

            logger.info(
                f"Discovered {len(self.tools)} tools from HTTP server {self.name}"
            )

        except Exception as e:
            logger.error(f"Failed to discover tools from HTTP server {self.name}: {e}")
            self.tools = []
            self.wrapped_tools = []

    def _create_pydantic_tool_stdio(self, mcp_tool) -> Optional[PydanticAITool]:
        """Create a Pydantic AI tool from stdio MCP tool."""
        try:
            # Create the async function that calls the MCP tool
            async def tool_function(**kwargs) -> Dict[str, Any]:
                try:
                    if not self.session:
                        return {"success": False, "error": "No session available"}

                    result = await self.session.call_tool(mcp_tool.name, kwargs)

                    # Extract content from result (same as mcp_client_manager.py)
                    if hasattr(result, "content") and result.content:
                        content_items = []
                        for item in result.content:
                            try:
                                if hasattr(item, "type"):
                                    content_type = getattr(item, "type", "unknown")
                                    if content_type == "text":
                                        content_items.append(
                                            getattr(item, "text", str(item))
                                        )
                                    elif content_type in ["image", "audio"]:
                                        content_items.append(
                                            f"[{content_type.title()} content]"
                                        )
                                    else:
                                        content_items.append(str(item))
                                else:
                                    text_content = getattr(item, "text", None)
                                    if text_content is not None:
                                        content_items.append(text_content)
                                    else:
                                        content_items.append(str(item))
                            except AttributeError:
                                content_items.append(str(item))

                        return {
                            "success": True,
                            "result": "\n".join(content_items)
                            if content_items
                            else "Tool executed successfully",
                            "server": self.name,
                            "tool": mcp_tool.name,
                            "transport": "stdio",
                        }
                    else:
                        return {
                            "success": True,
                            "result": str(result),
                            "server": self.name,
                            "tool": mcp_tool.name,
                            "transport": "stdio",
                        }

                except Exception as e:
                    logger.error(f"Error calling stdio MCP tool {mcp_tool.name}: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "server": self.name,
                        "tool": mcp_tool.name,
                        "transport": "stdio",
                    }

            # Set function metadata
            tool_function.__name__ = f"mcp_{self.name}_{mcp_tool.name}"
            tool_function.__doc__ = (
                mcp_tool.description or f"MCP tool {mcp_tool.name} from {self.name}"
            )

            # Create Pydantic AI Tool
            pydantic_tool = PydanticAITool(
                function=tool_function,
                name=f"mcp_{self.name}_{mcp_tool.name}",
                description=mcp_tool.description
                or f"MCP tool {mcp_tool.name} from {self.name}",
            )

            return pydantic_tool

        except Exception as e:
            logger.error(
                f"Failed to create stdio Pydantic tool for {mcp_tool.name}: {e}"
            )
            return None

    def _create_pydantic_tool_http(
        self, tool_def: Dict[str, Any]
    ) -> Optional[PydanticAITool]:
        """Create a Pydantic AI tool from HTTP tool definition."""
        try:
            tool_name = tool_def.get("name", "unknown_tool")
            endpoint = tool_def.get("endpoint", f"/tools/{tool_name}")

            # Create the async function that calls the HTTP tool
            async def tool_function(**kwargs) -> Dict[str, Any]:
                try:
                    if not self.http_client:
                        return {"success": False, "error": "No HTTP client available"}

                    response = await self.http_client.post(endpoint, json=kwargs)
                    response.raise_for_status()
                    result = response.json()

                    return {
                        "success": True,
                        "result": result,
                        "server": self.name,
                        "tool": tool_name,
                        "transport": "http",
                    }

                except Exception as e:
                    logger.error(f"Error calling HTTP MCP tool {tool_name}: {e}")
                    return {
                        "success": False,
                        "error": str(e),
                        "server": self.name,
                        "tool": tool_name,
                        "transport": "http",
                    }

            # Set function metadata
            tool_function.__name__ = f"mcp_{self.name}_{tool_name}"
            tool_function.__doc__ = tool_def.get(
                "description", f"HTTP MCP tool {tool_name} from {self.name}"
            )

            # Create Pydantic AI Tool
            pydantic_tool = PydanticAITool(
                function=tool_function,
                name=f"mcp_{self.name}_{tool_name}",
                description=tool_def.get(
                    "description", f"HTTP MCP tool {tool_name} from {self.name}"
                ),
            )

            return pydantic_tool

        except Exception as e:
            logger.error(f"Failed to create HTTP Pydantic tool for {tool_def}: {e}")
            return None

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a specific tool on this server."""
        try:
            if self.config.type == "stdio":
                if not self.session:
                    return {"success": False, "error": "No stdio session available"}
                result = await self.session.call_tool(tool_name, arguments)
                return {"success": True, "result": result}

            elif self.config.type == "http":
                if not self.http_client:
                    return {"success": False, "error": "No HTTP client available"}

                # Find the tool endpoint
                tool_def = next(
                    (t for t in self.tools if t.get("name") == tool_name), None
                )
                if not tool_def:
                    return {"success": False, "error": f"Tool {tool_name} not found"}

                endpoint = tool_def.get("endpoint", f"/tools/{tool_name}")
                response = await self.http_client.post(endpoint, json=arguments)
                response.raise_for_status()
                result = response.json()
                return {"success": True, "result": result}

            else:
                return {
                    "success": False,
                    "error": f"Unsupported transport: {self.config.type}",
                }

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self.config.type == "stdio":
                await self.exit_stack.aclose()
            elif self.config.type == "http" and self.http_client:
                await self.http_client.aclose()

            self.session = None
            self.http_client = None
            self.connected = False
            logger.info(f"Disconnected from MCP server: {self.name}")
        except Exception as e:
            logger.error(f"Error disconnecting from server {self.name}: {e}")


class UnifiedMCPClientManager:
    """Unified MCP client manager supporting multiple transport types."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_path()
        self.config: Optional[Dict[str, Any]] = None
        self.connections: Dict[str, UnifiedMCPServerConnection] = {}
        self._agent_mapping_config = None
        self._load_agent_mapping()

    def _find_config_path(self) -> str:
        """Find the mcp.json configuration file."""
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

    def load_configuration(self) -> Dict[str, Any]:
        """Load MCP configuration from mcp.json."""
        with open(self.config_path, "r") as f:
            data = json.load(f)

        # Support both formats: {"mcpServers": {...}} and direct server config
        if "mcpServers" in data:
            self.config = data["mcpServers"]
        else:
            self.config = data

        # Ensure config is never None
        if self.config is None:
            self.config = {}

        logger.info(f"Loaded {len(self.config)} MCP server configurations")
        return self.config

    async def initialize_all_servers(self):
        """Initialize all enabled MCP servers."""
        if not self.config:
            self.load_configuration()

        if not self.config:
            logger.error("No configuration loaded")
            return

        # Connect to each server
        for server_name, server_config in self.config.items():
            try:
                # Create MCPServerConfig from dict
                config = MCPServerConfig(name=server_name, **server_config)

                if config.enabled:
                    connection = UnifiedMCPServerConnection(server_name, config)
                    success = await connection.connect()
                    if success:
                        self.connections[server_name] = connection
                    else:
                        logger.warning(f"Failed to connect to server: {server_name}")
            except Exception as e:
                logger.error(f"Error initializing server {server_name}: {e}")

        logger.info(f"Connected to {len(self.connections)} MCP servers")

    def get_tools_for_agent(self, agent_name: str) -> List[PydanticAITool]:
        """Get MCP tools appropriate for a specific agent."""
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
            if server_name in self.connections:
                connection = self.connections[server_name]
                if connection.connected:
                    tools.extend(connection.wrapped_tools)
                else:
                    logger.warning(f"Required server {server_name} not connected")
            else:
                logger.warning(f"Required server {server_name} not found")

        # Get tools from optional servers if available
        for server_name in agent_config.get("optional_servers", []):
            if server_name in self.connections:
                connection = self.connections[server_name]
                if connection.connected:
                    tools.extend(connection.wrapped_tools)

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
        if server_name not in self.connections:
            return {"success": False, "error": f"Server {server_name} not connected"}

        connection = self.connections[server_name]
        if not connection.connected:
            return {"success": False, "error": f"Server {server_name} not connected"}

        return await connection.call_tool(tool_name, arguments)

    async def shutdown(self):
        """Shutdown all MCP server connections."""
        for server_name, connection in self.connections.items():
            try:
                await connection.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from server {server_name}: {e}")

        self.connections.clear()

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        configured = self.config if self.config is not None else {}
        status: Dict[str, Any] = {
            "configured_servers": len(configured),
            "connected_servers": len(
                [c for c in self.connections.values() if c.connected]
            ),
            "total_tools": sum(
                len(c.tools) for c in self.connections.values() if c.connected
            ),
            "servers": {},
        }

        for server_name, server_config in configured.items():
            connection = self.connections.get(server_name)
            status["servers"][server_name] = {
                "enabled": bool(server_config.get("enabled", True)),
                "connected": bool(connection.connected) if connection else False,
                "tool_count": len(connection.tools)
                if connection and connection.connected
                else 0,
                "type": server_config.get("type", "stdio"),
                "transport": server_config.get("type", "stdio"),
            }

        return status

    async def reload_configuration(self):
        """Reload MCP configuration and restart all server connections."""
        logger.info("Reloading unified MCP configuration...")
        try:
            # Shutdown existing connections
            await self.shutdown()

            # Reload configuration
            self.load_configuration()

            # Reload agent mapping
            self._load_agent_mapping()

            # Reinitialize all servers
            await self.initialize_all_servers()

            logger.info("Unified MCP configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading unified MCP configuration: {e}")
            raise


# Global unified MCP client manager instance
_unified_mcp_client_manager: Optional[UnifiedMCPClientManager] = None


async def get_unified_mcp_client_manager() -> UnifiedMCPClientManager:
    """Get or create the global unified MCP client manager instance."""
    global _unified_mcp_client_manager
    if _unified_mcp_client_manager is None:
        _unified_mcp_client_manager = UnifiedMCPClientManager()
        await _unified_mcp_client_manager.initialize_all_servers()
    return _unified_mcp_client_manager


async def shutdown_unified_mcp_client_manager():
    """Shutdown the global unified MCP client manager."""
    global _unified_mcp_client_manager
    if _unified_mcp_client_manager:
        await _unified_mcp_client_manager.shutdown()
        _unified_mcp_client_manager = None
