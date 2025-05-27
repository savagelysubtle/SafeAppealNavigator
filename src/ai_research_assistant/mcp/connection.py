"""
Defines the McpConnection class responsible for managing a connection
to a single MCP server, including its lifecycle, tool discovery, and execution.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

# Conditional import for type hinting to avoid circular dependency
if TYPE_CHECKING:
    from .hub import McpHub  # Assuming McpHub will be in hub.py

# Corrected import path for Pydantic models
from ..config.mcp.mcp_client_models import (
    McpToolClientData,
    McpToolSchema,
    ServerConfig,  # This model has the 'timeout' attribute
    # Renamed from SseServerConfig for consistency if used directly
)

# Attempt to import MCP SDK components.
# These will be fully utilized once the SDK is integrated and methods are implemented.
try:
    # from mcp import ClientSession # Placeholder for actual SDK client session - Not directly used in current logic
    # from mcp import StdioServerParameters # Placeholder - Not directly used
    from mcp import types as mcp_types_sdk  # MCP SDK type definitions
    from mcp.client import (
        Client as SDKClient,
    )
    from mcp.client import (
        SseClientTransport as SDKSseClientTransport,
    )
    from mcp.client import (
        StdioClientTransport as SDKStdioClientTransport,
    )
    # from mcp.client.mcp_errors import MCPError # Assuming a common error class - Handled by generic Exception for now
    # from mcp.client.stdio import stdio_client # Placeholder for stdio transport factory - Not directly used

    MCP_SDK_AVAILABLE = True
    # Assign SDK types to local names for consistent use
    Client = SDKClient
    SseClientTransport = SDKSseClientTransport
    StdioClientTransport = SDKStdioClientTransport
    mcp_types = mcp_types_sdk
except ImportError:
    logging.getLogger(__name__).warning(
        "MCP SDK not fully available. McpConnection will have limited functionality."
    )
    MCP_SDK_AVAILABLE = False

    # Define dummy classes for linting/type-checking when SDK is not available
    # Using Type[Any] or Callable for things that are classes/constructors
    # And Any for instances or modules like mcp_types
    class DummyClient:
        def __init__(self, transport: Any):
            pass

        async def initialize(self) -> None:
            await asyncio.sleep(0)

        async def shutdown(self) -> None:
            await asyncio.sleep(0)

        async def request(self, method: str, params: Dict[str, Any]) -> Any:
            await asyncio.sleep(0)
            return {}

    class DummySseClientTransport:
        def __init__(self, url: str, timeout_s: int):
            pass

    class DummyStdioClientTransport:
        def __init__(
            self, cmd: list[str], env: Optional[Dict[str, str]], timeout_s: int
        ):
            pass

    mcp_types: Any = object()  # Placeholder for the mcp_types module
    Client: Type[DummyClient] = DummyClient  # type: ignore
    SseClientTransport: Type[DummySseClientTransport] = DummySseClientTransport  # type: ignore
    StdioClientTransport: Type[DummyStdioClientTransport] = DummyStdioClientTransport  # type: ignore
    # MCPError = Exception # type: ignore # Can map to generic Exception

logger = logging.getLogger(__name__)


class McpConnection:
    """
    Manages the connection to a single MCP server, including discovery and tool calls.
    """

    def __init__(self, server_config: ServerConfig, hub: "McpHub"):
        self.server_config = server_config
        self.hub = hub
        self.client: Optional[Client] = None
        self.transport: Optional[Union[StdioClientTransport, SseClientTransport]] = None
        self.is_connected: bool = False
        self.tools: Dict[str, McpToolClientData] = {}
        self._connection_task: Optional[asyncio.Task] = None
        # Removed transport stream/process attributes as they are managed by SDK's transport objects
        # self._transport_read_stream: Optional[Any] = None
        # self._transport_write_stream: Optional[Any] = None
        # self._transport_process: Optional[asyncio.subprocess.Process] = None

    async def connect_and_discover(self) -> None:
        """Establishes connection to the server and discovers its capabilities."""
        if self.server_config.disabled:
            logger.info(
                f"Server {self.server_config.name} is disabled and will not be connected."
            )
            return

        logger.info(
            f"Attempting to connect to MCP server: {self.server_config.name} (Type: {self.server_config.type})"
        )
        try:
            if self.server_config.type == "stdio" and self.server_config.stdio_config:
                self.transport = StdioClientTransport(
                    cmd=self.server_config.stdio_config.command,
                    env=self.server_config.stdio_config.env,
                    timeout_s=self.server_config.timeout,  # Using .timeout from ServerConfig
                )
            elif self.server_config.type == "sse" and self.server_config.sse_config:
                self.transport = SseClientTransport(
                    url=self.server_config.sse_config.url,
                    timeout_s=self.server_config.timeout,  # Using .timeout from ServerConfig
                )
            else:
                logger.error(
                    f"Invalid or incomplete configuration for server: {self.server_config.name}"
                )
                raise ValueError(
                    f"Invalid server configuration for {self.server_config.name}"
                )

            if (
                not self.transport
            ):  # Should not happen if config is valid, but as a safeguard
                raise ValueError(
                    f"Transport could not be initialized for {self.server_config.name}"
                )

            self.client = Client(
                self.transport
            )  # client is now typed as Optional[Client]

            # Assuming Client() constructor doesn't return None and initialize() is a method of Client
            # The linter might still complain if MCP_SDK_AVAILABLE is False and Client is Any.
            if (
                self.client
            ):  # Added a check for client, though SDK should ensure it's not None
                await self.client.initialize()  # type: ignore
                self.is_connected = True
                logger.info(
                    f"Successfully connected to MCP server: {self.server_config.name}"
                )
                await self._discover_capabilities()
            else:
                # This case should ideally not be reached if SDK Client behaves as expected
                raise RuntimeError(
                    f"MCP Client object could not be initialized for {self.server_config.name}"
                )

        except ConnectionRefusedError:
            logger.error(f"Connection refused by MCP server: {self.server_config.name}")
            self.is_connected = False
        except asyncio.TimeoutError:
            logger.error(
                f"Timeout during connection or initialization for MCP server: {self.server_config.name}"
            )
            self.is_connected = False
        except Exception as e:
            logger.error(
                f"Failed to connect or initialize MCP server {self.server_config.name}: {e}",
                exc_info=True,
            )
            self.is_connected = False
        finally:
            if not self.is_connected and self.client:
                try:
                    await self.client.shutdown()  # type: ignore
                except Exception as e_shutdown:
                    logger.error(
                        f"Error during client shutdown for {self.server_config.name} after connection failure: {e_shutdown}"
                    )
                self.client = None  # Ensure client is None if not connected
                self.transport = None  # Ensure transport is None if not connected

    async def _discover_capabilities(self) -> None:
        """Discovers tools and resources available on the connected server."""
        if not self.client or not self.is_connected:  # client is Optional[Client]
            logger.warning(
                f"Cannot discover capabilities, not connected to {self.server_config.name}"
            )
            return

        try:
            logger.debug(f"Discovering tools for {self.server_config.name}...")
            # Assuming client.request exists and works as expected.
            tools_response = await self.client.request(method="tools/list", params={})  # type: ignore

            raw_tools = (
                tools_response.get("tools", [])  # type: ignore
                if isinstance(tools_response, dict)
                else []
            )

            self.tools = {}
            for tool_data in raw_tools:
                tool_name = tool_data.get("name")
                if not tool_name:
                    logger.warning(
                        f"Skipping tool with no name from {self.server_config.name}: {tool_data}"
                    )
                    continue

                args_schema_data = (
                    tool_data.get("args_schema") or tool_data.get("schema") or {}
                )

                if not isinstance(args_schema_data, dict):
                    logger.warning(
                        f"Tool '{tool_name}' from {self.server_config.name} has invalid schema format. Assuming empty schema."
                    )
                    args_schema_data = {}

                # McpToolSchema is now correctly imported
                parsed_schema = McpToolSchema(**args_schema_data)

                is_auto_approved = tool_name in self.server_config.auto_approve_tools

                # McpToolClientData is now correctly imported
                tool = McpToolClientData(
                    name=tool_name,
                    description=tool_data.get("description"),
                    args_schema=parsed_schema,
                    auto_approve=is_auto_approved,
                    server_name=self.server_config.name,
                )
                self.tools[tool_name] = tool
            logger.info(
                f"Discovered {len(self.tools)} tools for {self.server_config.name}: {list(self.tools.keys())}"
            )

        except (
            Exception
        ) as e:  # Catch generic Exception, can be refined if MCPError is available
            logger.error(
                f"Error discovering capabilities for {self.server_config.name}: {e}",
                exc_info=True,
            )

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executes a tool on the MCP server."""
        if not self.client or not self.is_connected:  # client is Optional[Client]
            logger.error(
                f"Cannot execute tool {tool_name}, not connected to {self.server_config.name}"
            )
            raise ConnectionError(f"Not connected to server {self.server_config.name}")

        tool_info = self.get_tool_info(tool_name)
        if not tool_info:
            logger.error(
                f"Tool {tool_name} not found on server {self.server_config.name}"
            )
            raise ValueError(
                f"Tool {tool_name} not found on server {self.server_config.name}"
            )

        logger.info(
            f"Executing tool '{tool_name}' on server '{self.server_config.name}' with args: {arguments}"
        )
        try:
            # Assuming client.request exists and works as expected.
            response = await self.client.request(
                method="tools/call", params={"name": tool_name, "arguments": arguments}
            )  # type: ignore
            logger.info(f"Tool '{tool_name}' executed successfully. Result: {response}")
            return response
        except Exception as e:  # Catch generic Exception
            logger.error(
                f"Error executing tool '{tool_name}' on {self.server_config.name}: {e}",
                exc_info=True,
            )
            # It's better to re-raise the specific error if possible, or a custom error.
            # For now, re-raising a generic runtime error.
            raise RuntimeError(
                f"Failed to execute tool {tool_name} on {self.server_config.name}: {e}"
            ) from e

    def get_tool_info(
        self, tool_name: str
    ) -> Optional[McpToolClientData]:  # Correct return type
        """Retrieves information about a specific tool by its name."""
        return self.tools.get(tool_name)

    async def close(self) -> None:
        """Closes the connection to the MCP server."""
        logger.info(f"Attempting to close connection to {self.server_config.name}...")
        if self.client and self.is_connected:  # client is Optional[Client]
            try:
                # Assuming client.shutdown() exists.
                await self.client.shutdown()  # type: ignore
                logger.info(f"Client for {self.server_config.name} shut down.")
            except Exception as e:
                logger.error(
                    f"Error during client shutdown for {self.server_config.name}: {e}",
                    exc_info=True,
                )
        # No need to explicitly handle transport.close() if the SDK's client.shutdown() handles it.
        # If transport needs separate closing, that logic would depend on the SDK's design.
        # elif self.transport:
        # logger.debug(f"Transport for {self.server_config.name} will be released/closed if necessary.")
        # if hasattr(self.transport, 'close'):
        # await self.transport.close() # type: ignore

        self.is_connected = False
        self.client = None  # Ensure client is reset
        self.transport = None  # Ensure transport is reset
        logger.info(f"Finished close procedure for {self.server_config.name}.")

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of this connection."""
        return {
            "server_name": self.server_config.name,
            "type": self.server_config.type,
            "is_connected": self.is_connected,
            "discovered_tools_count": len(self.tools),
            "discovered_tools": list(self.tools.keys()),  # Ensure this is a list
            "disabled": self.server_config.disabled,
        }
