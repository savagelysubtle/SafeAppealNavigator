# src/ai_research_assistant/mcp_intergration/unified_mcp_client.py
import asyncio
import logging
import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Content, Tool
from pydantic_ai.tools import Tool as PydanticAITool

# Correctly import the application's single source of truth for configuration
from ..config.mcp_config import mcp_config

logger = logging.getLogger(__name__)

TransportType = Literal["stdio", "sse", "http"]


class MCPServerConnection:
    """
    Manages a persistent connection to a single MCP server.

    This class is transport-aware and handles the entire lifecycle of an MCP
    connection, including startup, tool discovery, and graceful shutdown using
    an AsyncExitStack for robust resource management.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.session: Optional[ClientSession] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[Tool] = []
        self.wrapped_tools: List[PydanticAITool] = []
        self.is_connected = False

    async def connect(self) -> None:
        """Establishes a connection using the transport specified in the config."""
        if not self.config.get("enabled", True):
            logger.info(f"MCP server '{self.name}' is disabled, skipping.")
            return

        transport_type: TransportType = self.config.get("type", "stdio")
        logger.info(
            f"Connecting to MCP server '{self.name}' via {transport_type} transport..."
        )

        try:
            if transport_type == "stdio":
                await self._connect_stdio()
            elif transport_type == "sse":
                await self._connect_sse()
            elif transport_type == "http":
                await self._connect_http()
            else:
                logger.error(
                    f"Unsupported transport type for '{self.name}': {transport_type}"
                )
                return

            self.is_connected = True
            logger.info(f"Successfully connected to MCP server: '{self.name}'")
        except Exception as e:
            logger.error(
                f"Failed to connect to MCP server '{self.name}': {e}", exc_info=True
            )
            await self.disconnect()

    async def _connect_stdio(self) -> None:
        """Establishes a connection using the stdio transport."""
        command = self.config.get("command")
        if not command:
            raise ValueError(f"No command specified for stdio server '{self.name}'.")

        cwd = self.config.get("cwd")
        if cwd and not os.path.isabs(cwd):
            project_root = Path(__file__).parent.parent.parent.parent
            cwd = str(project_root / cwd)

        params = StdioServerParameters(
            command=command,
            args=self.config.get("args", []),
            cwd=cwd,
            env={**os.environ, **self.config.get("env", {})},
        )
        read, write = await self.exit_stack.enter_async_context(stdio_client(params))
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        await self._discover_and_wrap_session_tools()

    async def _connect_sse(self) -> None:
        """Establishes a connection using the sse transport."""
        url = self.config.get("url")
        if not url:
            raise ValueError(f"No URL specified for SSE server '{self.name}'.")

        read, write = await self.exit_stack.enter_async_context(sse_client(url))
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self.session.initialize()
        await self._discover_and_wrap_session_tools()

    async def _connect_http(self) -> None:
        """Establishes a connection using the http transport."""
        base_url = self.config.get("baseApiUrl")
        if not base_url:
            raise ValueError(f"No baseApiUrl for HTTP server '{self.name}'.")

        headers = self.config.get("headers", {})
        if self.config.get("apiKey"):
            headers["Authorization"] = f"Bearer {self.config['apiKey']}"

        self.http_client = httpx.AsyncClient(base_url=base_url, headers=headers)
        await self._discover_and_wrap_http_tools()

    async def _discover_and_wrap_session_tools(self) -> None:
        """Discovers and wraps tools for session-based transports (stdio/sse)."""
        if not self.session:
            return
        response = await self.session.list_tools()
        self.tools = response.tools
        self.wrapped_tools = [
            self._create_pydantic_tool_from_session(tool) for tool in self.tools
        ]
        logger.info(f"Discovered {len(self.wrapped_tools)} tools from '{self.name}'.")

    async def _discover_and_wrap_http_tools(self) -> None:
        """Discovers and wraps tools for the HTTP transport."""
        if not self.http_client:
            return
        response = await self.http_client.get("/mcp/tools")
        response.raise_for_status()
        tool_definitions = response.json().get("tools", [])
        self.wrapped_tools = [
            self._create_pydantic_tool_from_http(tool_def)
            for tool_def in tool_definitions
        ]
        logger.info(f"Discovered {len(self.wrapped_tools)} tools from '{self.name}'.")

    def _create_pydantic_tool_from_session(self, mcp_tool: Tool) -> PydanticAITool:
        """Creates a callable PydanticAITool that executes a remote MCP tool via a session."""

        async def tool_function(**kwargs: Any) -> Dict[str, Any]:
            if not self.session:
                raise ConnectionError(f"MCP session for '{self.name}' is not active.")
            try:
                result: CallToolResult = await self.session.call_tool(
                    mcp_tool.name, kwargs
                )

                # --- CORRECTED & TYPE-SAFE LOGIC ---
                if hasattr(result, "content") and result.content:
                    content_parts = []
                    item: Content
                    for item in result.content:
                        # Explicitly check the type of the content item
                        if getattr(item, "type", None) == "text":
                            content_parts.append(getattr(item, "text", ""))
                        else:
                            # Handle non-text content gracefully
                            content_parts.append(
                                f"[{getattr(item, 'type', 'unknown').upper()} Content]"
                            )
                    return {"result": "\n".join(content_parts)}
                # --- END CORRECTION ---

                return {"result": "Tool executed with no textual output."}
            except Exception as e:
                logger.error(
                    f"Error calling MCP tool '{mcp_tool.name}': {e}", exc_info=True
                )
                return {"error": str(e)}

        tool_function.__name__ = f"mcp_{self.name}_{mcp_tool.name}"
        tool_function.__doc__ = (
            mcp_tool.description or f"MCP tool {mcp_tool.name} from {self.name}"
        )
        return PydanticAITool(function=tool_function, name=tool_function.__name__)

    def _create_pydantic_tool_from_http(
        self, tool_def: Dict[str, Any]
    ) -> PydanticAITool:
        """Creates a PydanticAITool that calls a remote MCP tool via HTTP."""
        tool_name = tool_def.get("name", "unknown_http_tool")

        async def tool_function(**kwargs: Any) -> Dict[str, Any]:
            if not self.http_client:
                raise ConnectionError(f"HTTP client for '{self.name}' is not active.")
            try:
                response = await self.http_client.post(
                    f"/mcp/tools/{tool_name}", json={"arguments": kwargs}
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(
                    f"Error calling HTTP MCP tool '{tool_name}': {e}", exc_info=True
                )
                return {"error": str(e)}

        tool_function.__name__ = f"mcp_{self.name}_{tool_name}"
        tool_function.__doc__ = (
            tool_def.get("description") or f"HTTP tool {tool_name} from {self.name}"
        )
        return PydanticAITool(function=tool_function, name=tool_function.__name__)

    async def disconnect(self) -> None:
        """Shuts down the connection and cleans up all associated resources."""
        if self.is_connected:
            logger.info(f"Disconnecting from MCP server '{self.name}'...")
            if self.http_client:
                await self.http_client.aclose()
            await self.exit_stack.aclose()
            self.is_connected = False
            logger.info(f"Disconnected from '{self.name}'.")


class MCPClientManager:
    """
    Manages all MCP server connections and distributes tools to agents.
    """

    def __init__(self) -> None:
        self.config_loader = mcp_config
        self.connections: Dict[str, MCPServerConnection] = {}
        self.is_initialized = False

    async def initialize(self) -> None:
        """Loads configuration via MCPConfigLoader and connects to all servers."""
        if self.is_initialized:
            return

        server_configs = self.config_loader.load_mcp_config().get("mcp_servers", {})
        connect_tasks = []
        for name, config in server_configs.items():
            connection = MCPServerConnection(name, config)
            self.connections[name] = connection
            connect_tasks.append(connection.connect())

        await asyncio.gather(*connect_tasks)
        self.is_initialized = True
        logger.info("MCP Client Manager initialized.")

    def get_tools_for_agent(self, agent_name: str) -> List[PydanticAITool]:
        """Gets the configured set of MCP tools for a given agent name."""
        agent_servers = self.config_loader.get_agent_servers(agent_name)
        primary_tools_filter = self.config_loader.get_agent_tools(agent_name)

        all_tools: List[PydanticAITool] = []

        for server_name in agent_servers.get("required", []) + agent_servers.get(
            "optional", []
        ):
            connection = self.connections.get(server_name)
            if connection and connection.is_connected:
                all_tools.extend(connection.wrapped_tools)
            elif server_name in agent_servers.get("required", []):
                logger.warning(
                    f"Required MCP server '{server_name}' for agent '{agent_name}' is not connected."
                )

        if primary_tools_filter:
            filtered_tools = [
                tool
                for tool in all_tools
                if any(tool.name.endswith(pt) for pt in primary_tools_filter)
            ]
            logger.info(
                f"Filtered to {len(filtered_tools)} primary tools for agent '{agent_name}'."
            )
            return filtered_tools

        logger.info(f"Providing {len(all_tools)} tools to agent '{agent_name}'.")
        return all_tools

    async def shutdown(self) -> None:
        """Shuts down all active MCP connections gracefully."""
        logger.info("Shutting down all MCP connections...")
        shutdown_tasks = [conn.disconnect() for conn in self.connections.values()]
        await asyncio.gather(*shutdown_tasks)
        self.connections.clear()
        self.is_initialized = False
        logger.info("All MCP connections shut down.")


# --- Singleton Management ---
_mcp_client_manager_instance: Optional[MCPClientManager] = None
_mcp_manager_lock = asyncio.Lock()


async def get_mcp_client_manager() -> MCPClientManager:
    """Gets the global singleton instance of the MCPClientManager."""
    global _mcp_client_manager_instance
    if _mcp_client_manager_instance is None:
        async with _mcp_manager_lock:
            if _mcp_client_manager_instance is None:
                _mcp_client_manager_instance = MCPClientManager()
                await _mcp_client_manager_instance.initialize()
    return _mcp_client_manager_instance


async def shutdown_mcp_client_manager() -> None:
    """Shuts down and cleans up the global MCP client manager instance."""
    global _mcp_client_manager_instance
    if _mcp_client_manager_instance:
        async with _mcp_manager_lock:
            if _mcp_client_manager_instance:
                await _mcp_client_manager_instance.shutdown()
                _mcp_client_manager_instance = None
