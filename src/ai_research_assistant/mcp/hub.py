"""
Defines the McpHub class, the central orchestrator for managing connections
to multiple MCP servers and dispatching tool calls.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

# Import the consolidated Pydantic models
from ..config.mcp.mcp_client_models import (
    GlobalClientConfig,
    McpToolClientData,
    ServerConfig,
)
from .connection import McpConnection

logger = logging.getLogger(__name__)

# Type alias for the UI callback
ServerStatusCallback = Callable[[str, bool, List[str], Optional[str]], Awaitable[None]]


class McpHub:
    """
    Manages multiple McpConnection instances, one for each configured MCP server.
    Provides a unified interface for discovering and calling tools across all servers.
    """

    def __init__(
        self,
        # Default config path changed to the root config/mcp_servers.json
        config_path: Path = Path(__file__).parent.parent
        / "config"
        / "mcp_servers.json",
        status_callback: Optional[ServerStatusCallback] = None,
    ):
        """
        Initializes the McpHub.
        Args:
            config_path (Path): Path to the MCP servers JSON config file.
                                Default is src/ai_research_assistant/config/mcp_servers.json
            status_callback (Optional[ServerStatusCallback]): Callback function to notify UI about server status changes.
        """
        self.config_path = config_path
        self.global_config: GlobalClientConfig = GlobalClientConfig(
            servers=[]
        )  # Initialize with empty list
        self.connections: Dict[str, McpConnection] = {}
        self._is_initialized: bool = False
        self._shutdown_event = asyncio.Event()
        self.on_server_status_change: Optional[ServerStatusCallback] = status_callback
        self._lock = asyncio.Lock()

    def _load_configs(self) -> None:
        """Loads MCP server configurations from the specified JSON file using Pydantic models."""
        logger.info(f"Loading MCP configurations from: {self.config_path}")
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                # The mcp_servers.json directly contains the list of server configs under "mcp_server_configs"
                # Adjusting parsing to match the structure of GlobalClientConfig which expects a 'servers' list.
                if "mcp_server_configs" in config_data and isinstance(
                    config_data["mcp_server_configs"], list
                ):
                    self.global_config = GlobalClientConfig(
                        servers=config_data["mcp_server_configs"]
                    )
                else:
                    # Fallback if the structure is just a list of servers (e.g. if mcp_server_configs key is removed)
                    # Or handle as an error if the structure is unexpected.
                    # For now, assuming the file provides a list directly if "mcp_server_configs" is not the key.
                    # Based on the provided mcp_servers.json, it IS under "mcp_server_configs"
                    logger.warning(
                        f"MCP config file {self.config_path} does not have the expected 'mcp_server_configs' key or it's not a list. Trying to parse as a direct list."
                    )
                    # If the root of the JSON is the list of servers:
                    # self.global_config = GlobalClientConfig(servers=config_data)
                    # For now, strict check:
                    raise ValueError(
                        "mcp_servers.json is not in the expected format with 'mcp_server_configs' key holding a list."
                    )

                logger.info(
                    f"Loaded {len(self.global_config.servers)} server configurations."
                )
            else:
                logger.warning(
                    f"MCP configuration file not found: {self.config_path}. No servers will be configured."
                )
                self.global_config = GlobalClientConfig(servers=[])
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding MCP JSON configuration from {self.config_path}: {e}",
                exc_info=True,
            )
            self.global_config = GlobalClientConfig(servers=[])
        except Exception as e:  # Includes Pydantic validation errors
            logger.error(
                f"Failed to load or parse MCP configurations from {self.config_path}: {e}",
                exc_info=True,
            )
            self.global_config = GlobalClientConfig(servers=[])

    async def initialize_all_connections(self) -> None:
        """
        Initializes connections to all non-disabled MCP servers based on loaded configuration.
        """
        if (
            self._is_initialized and not self._shutdown_event.is_set()
        ):  # Check if not in shutdown process
            logger.info(
                "MCP Hub: Already initialized and not shutting down. Call reload_configurations_and_reconnect() to force re-initialization."
            )
            # If already initialized, we might want to just ensure all current servers are still reported
            # This part can be enhanced if dynamic updates without full re-init are needed.
            # For now, if called again, it implies a desire to ensure current state or a reload.
            # Let's make it re-entrant but avoid re-creating connections if they are fine.
            # The existing logic already handles this to some extent.
            pass

        logger.info("MCP Hub: Initializing connections...")
        self._shutdown_event.clear()  # Clear shutdown flag if it was set

        async with self._lock:
            self._load_configs()  # Load or reload configurations

            if not self.global_config.servers:
                logger.warning(
                    "MCP Hub: No MCP server configurations found after loading. Hub will not connect to any servers."
                )
                # Ensure any existing connections are closed if config is now empty
                for server_name, conn_to_close in list(
                    self.connections.items()
                ):  # Iterate over a copy for safe removal
                    logger.info(
                        f"Closing stale connection to {server_name} as it's no longer in config or config is empty."
                    )
                    await conn_to_close.close()
                    self.connections.pop(server_name, None)
                    if self.on_server_status_change:
                        await self.on_server_status_change(
                            server_name,
                            False,
                            [],
                            "Removed from config or config empty",
                        )
                self._is_initialized = True
                return

            active_server_configs_dict: Dict[str, ServerConfig] = {
                sconf.name: sconf
                for sconf in self.global_config.servers
                if not sconf.disabled
            }
            current_connection_names = set(self.connections.keys())

            # Shutdown and remove connections for servers no longer in config or now disabled
            for server_name_to_check in list(
                current_connection_names
            ):  # Iterate over a copy
                if server_name_to_check not in active_server_configs_dict:
                    logger.info(
                        f"Server '{server_name_to_check}' is no longer active or removed from config. Shutting down."
                    )
                    connection_to_remove = self.connections.pop(
                        server_name_to_check, None
                    )
                    if connection_to_remove:
                        await connection_to_remove.close()
                        if self.on_server_status_change:
                            await self.on_server_status_change(
                                server_name_to_check, False, [], "Removed/Disabled"
                            )

            connection_tasks = []
            # Process active configurations
            for server_name, server_config in active_server_configs_dict.items():
                if (
                    server_name not in self.connections
                    or not self.connections[server_name].is_connected
                ):
                    logger.info(
                        f"Initializing MCP connection for server: {server_config.name}"
                    )
                    if server_name in self.connections:  # Exists but not connected
                        old_conn = self.connections[server_name]
                        await old_conn.close()  # Ensure old instance is closed

                    connection = McpConnection(
                        server_config, self
                    )  # ServerConfig from mcp_client_models
                    self.connections[server_config.name] = connection
                    connection_tasks.append(self._connect_and_notify(connection))
                else:  # Server is in connections and supposedly connected
                    existing_conn = self.connections[server_name]
                    # Check if the config object itself has changed. Pydantic models are comparable.
                    if existing_conn.server_config != server_config:
                        logger.info(
                            f"Configuration changed for connected server '{server_config.name}'. Re-initializing."
                        )
                        await existing_conn.close()
                        new_connection = McpConnection(
                            server_config, self
                        )  # ServerConfig from mcp_client_models
                        self.connections[server_config.name] = new_connection
                        connection_tasks.append(
                            self._connect_and_notify(new_connection)
                        )
                    elif (
                        self.on_server_status_change
                    ):  # Config same, still notify UI of current status
                        status = existing_conn.get_status()
                        await self.on_server_status_change(
                            server_config.name,
                            status["is_connected"],
                            status.get("discovered_tools", []),  # Use .get for safety
                            None,
                        )

            # Also handle servers marked as disabled in the config that might still be in self.connections
            for sconf in self.global_config.servers:
                if sconf.disabled and sconf.name in self.connections:
                    logger.info(
                        f"Server '{sconf.name}' is now disabled. Shutting down existing connection."
                    )
                    conn_to_disable = self.connections.pop(sconf.name)
                    await conn_to_disable.close()
                    if self.on_server_status_change:
                        await self.on_server_status_change(
                            sconf.name, False, [], "Disabled in config"
                        )
                # If it's disabled and NOT in self.connections, it's fine.
                # If UI needs to know about all configured servers including disabled ones,
                # get_all_server_statuses can handle that.

            if connection_tasks:
                results = await asyncio.gather(
                    *connection_tasks, return_exceptions=True
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        # This part is tricky as _connect_and_notify ALREADY sends status.
                        # We need to get the server name associated with the failed task.
                        # For now, relying on _connect_and_notify's finally block.
                        # Example: failed_task_conn = connection_tasks[i].get_coro().cr_frame.f_locals.get('connection')
                        # if failed_task_conn: logger.error(f"Error during connection task for {failed_task_conn.server_config.name}: {result}")
                        pass  # Logging is handled in _connect_and_notify

            logger.info("MCP Hub: All server connection initializations attempted.")

        self._is_initialized = True
        if not self._shutdown_event.is_set():  # Check if not in shutdown process
            logger.info("MCP Hub: Initialization complete.")

    async def _connect_and_notify(self, connection: McpConnection) -> None:
        """Helper to connect a single McpConnection and notify status."""
        server_name = connection.server_config.name
        error_message_details = None
        try:
            await connection.connect_and_discover()
        except Exception as e:
            logger.error(
                f"Failed to connect or discover for {server_name}: {e}", exc_info=True
            )
            connection.is_connected = False  # Ensure status is correct
            error_message_details = str(e)
        finally:
            if (
                self.on_server_status_change and not self._shutdown_event.is_set()
            ):  # Don't notify if shutting down
                status = connection.get_status()
                error_message = (
                    f"Connection/Discovery Failed: {error_message_details}"
                    if not connection.is_connected and error_message_details
                    else "Connection/Discovery Failed"
                    if not connection.is_connected
                    else None
                )
                await self.on_server_status_change(
                    server_name,
                    status["is_connected"],
                    status.get("discovered_tools", []),  # Use .get for safety
                    error_message,
                )

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        # user_confirmation_needed: bool = True, # This parameter is removed, confirmation is an upstream concern
    ) -> Any:
        """Calls a tool on a specified MCP server."""
        # Removed user_confirmation_needed logic from here.
        # The calling agent/UI controller is responsible for approval checks.
        # This hub method directly executes if called.

        async with self._lock:  # Ensure thread-safe access to connections
            if self._shutdown_event.is_set():
                logger.warning(
                    f"MCP Hub is shutting down. Cannot call tool {tool_name} on {server_name}."
                )
                raise ConnectionError("MCP Hub is shutting down.")

            connection = self.connections.get(server_name)
            if not connection or not connection.is_connected:
                logger.error(
                    f"Server '{server_name}' not found or not connected for tool call '{tool_name}'."
                )
                raise ConnectionError(
                    f"Server {server_name} is not available for tool '{tool_name}'."
                )

            tool_info = connection.get_tool_info(tool_name)
            if not tool_info:
                logger.error(f"Tool '{tool_name}' not found on server '{server_name}'.")
                raise ValueError(f"Tool {tool_name} not found on {server_name}.")

            # The plan states: "If True (or if the user approves), the process continues."
            # "The McpHub.call_tool method would then: Locate the correct McpConnection..."
            # This implies approval check happens *before* McpHub.call_tool.
            # If the tool is not auto_approve, the orchestrator/agent must have handled this.

            logger.info(
                f"Dispatching tool call '{tool_name}' to server '{server_name}' with args: {arguments}"
            )
            try:
                return await connection.execute_tool(tool_name, arguments)
            except Exception as e:  # Catch specific MCPError if SDK provides it
                logger.error(
                    f"Error executing tool '{tool_name}' via hub on '{server_name}': {e}",
                    exc_info=True,
                )
                raise  # Re-raise the original error to be handled by the caller

    def get_all_tools(self) -> List[McpToolClientData]:
        """Returns a list of all discovered tools across all connected servers."""
        all_tools: List[McpToolClientData] = []
        # Ensure thread-safe access if connections can be modified concurrently
        # For read-only access like this, if modification is locked, it might be okay.
        # However, to be safe, especially if status can change:
        # async with self._lock: # Or make connections a property that copies if accessed.
        # For now, assuming modifications are locked and this read is safe.
        for connection in self.connections.values():
            if connection.is_connected:
                all_tools.extend(list(connection.tools.values()))  # Ensure it's a list
        return all_tools

    def get_server_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Gets the status of a specific server."""
        # async with self._lock: # If reading self.connections needs protection
        connection = self.connections.get(server_name)
        if connection:
            return connection.get_status()

        # If not in connections, check if it's in config but disabled or failed to init
        for sconf in self.global_config.servers:
            if sconf.name == server_name:
                return {
                    "server_name": sconf.name,
                    "type": sconf.type,
                    "is_connected": False,
                    "discovered_tools_count": 0,
                    "discovered_tools": [],
                    "disabled": sconf.disabled,
                    "status_note": "Disabled in config"
                    if sconf.disabled
                    else "Not connected or initialized",
                }
        return None

    def get_all_server_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Gets the status of all configured servers."""
        statuses: Dict[str, Dict[str, Any]] = {}
        # async with self._lock: # If reading self.connections and self.global_config needs protection

        # Get status from active or attempted connections
        for server_name, connection in self.connections.items():
            statuses[server_name] = connection.get_status()

        # Add statuses for servers in config but not in self.connections
        # (e.g., disabled, or failed to initialize and got removed from self.connections if that logic exists)
        for sconf in self.global_config.servers:
            if sconf.name not in statuses:
                statuses[sconf.name] = {
                    "server_name": sconf.name,
                    "type": sconf.type,
                    "is_connected": False,
                    "discovered_tools_count": 0,
                    "discovered_tools": [],
                    "disabled": sconf.disabled,
                    "status_note": "Disabled in config"
                    if sconf.disabled
                    else "Not initialized or connection failed",
                }
        return statuses

    async def shutdown(self) -> None:
        """
        Gracefully closes all active MCP connections.
        """
        if not self._is_initialized:
            logger.info("MCP Hub: Shutdown called but not initialized. Nothing to do.")
            return

        if self._shutdown_event.is_set():
            logger.info("MCP Hub: Shutdown already in progress or completed.")
            return

        logger.info(
            f"MCP Hub: Initiating shutdown of {len(self.connections)} connections..."
        )
        self._shutdown_event.set()  # Signal any long-running connection tasks to stop

        async with self._lock:  # Ensure exclusive access during shutdown
            connection_close_tasks = []
            for server_name, connection in self.connections.items():
                logger.debug(
                    f"MCP Hub: Adding shutdown task for server '{server_name}'."
                )
                connection_close_tasks.append(connection.close())

            if connection_close_tasks:
                await asyncio.gather(*connection_close_tasks, return_exceptions=True)
                # Log any errors during close, but proceed

            self.connections.clear()

        # self._is_initialized = False # Keep it true but shutdown_event is set
        logger.info("MCP Hub: Shutdown sequence complete. Hub is now inactive.")

    async def reload_configurations_and_reconnect(self) -> None:
        """Forces a reload of configurations and attempts to reconnect all servers."""
        logger.info("MCP Hub: Reloading configurations and reconnecting all servers...")
        async with self._lock:  # Ensure no other operations while reloading
            self._is_initialized = False  # Force re-initialization logic
            self._shutdown_event.clear()  # Clear shutdown flag if set
            # Old connections are handled by initialize_all_connections if they are stale/disabled/removed
        await self.initialize_all_connections()
        logger.info("MCP Hub: Re-initialization attempt complete.")

    def register_status_update_callback(self, callback: ServerStatusCallback):
        """Registers a callback function to be invoked when a server's status changes."""
        self.on_server_status_change = callback
        logger.info("MCP Hub: Status update callback registered.")

    def is_shutting_down(self) -> bool:
        """Checks if the hub is in the process of shutting down."""
        return self._shutdown_event.is_set()

    def is_initialized(self) -> bool:
        """Checks if the hub has completed its initial_all_connections sequence at least once."""
        return self._is_initialized
