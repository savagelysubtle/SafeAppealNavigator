"""
MCP Manager: Handles connections to MCP servers and loads all available tools.

Responsibilities:
- Reads MCP server configurations (e.g., from a central mcp_servers.json).
- Establishes connections to enabled MCP servers (Stdio, SSE, HTTP).
- Manages ClientSession lifecycles.
- Loads all tools from connected servers using langchain_mcp_adapters.
- Caches loaded tools and provides access to them.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, AsyncContextManager, Dict, List, Optional, Tuple, Type

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession

# TODO: Resolve this import at the environment level for the linter.
# This utility is preferred for handling various transport types from config.
from mcp.client.utils import open_server_from_config
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


# Original param-model helper (can be kept if specific Pydantic model generation is needed outside of BaseTool.args_schema)
def create_mcp_tool_param_model(
    mcp_tool_schema: Dict[str, Any], tool_name: str
) -> Type[BaseModel]:
    """
    Creates a Pydantic model class from an MCP tool's inputSchema.
    This is useful if you need to construct a Pydantic model before it becomes
    a BaseTool's args_schema.
    """
    try:
        props = mcp_tool_schema.get("properties", {})
        required = mcp_tool_schema.get("required", [])
        field_defs = {}

        TYPE_MAP = {
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        for fname, fschema in props.items():
            py_type = TYPE_MAP.get(fschema.get("type", "string"), str)
            if fname not in required:
                py_type = Optional[py_type]  # type: ignore[valid-type]
                field_defs[fname] = (py_type, None)
            else:
                field_defs[fname] = (py_type, ...)
        return create_model(
            f"{tool_name.replace('-', '_').replace('.', '_').title()}Params",
            **field_defs,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to build param model for %s: %s", tool_name, exc)
        # Return a model that accepts any arguments if schema parsing fails
        return create_model(
            f"{tool_name.replace('-', '_').replace('.', '_').title()}FallbackParams",
            extra_args=(Optional[Dict[str, Any]], None),
        )


CONFIG_CANDIDATES = [
    Path(".cursor/mcp.json"),
    Path("mcp.json"),
    # Fallback to project-specific config location
    Path(__file__).parent.parent / "config" / "mcp" / "mcp_servers.json",
]


class MCPManager:
    """Singleton manager for MCP ClientSessions and loaded LangChain Tool objects."""

    _instance: MCPManager | None = None
    _sessions: Dict[str, ClientSession]
    _tools: List[BaseTool]
    _transport_managers: Dict[str, AsyncContextManager]
    _loading: bool  # To prevent concurrent loading

    def __new__(cls) -> MCPManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
            cls._instance._tools = []
            cls._instance._transport_managers = {}
            cls._instance._loading = False
        return cls._instance

    async def load_tools(self) -> None:  # Renamed from 'load' for clarity
        """Connects to MCP servers and loads tools. Safe to call multiple times."""
        if self._tools and not self._loading:
            logger.debug("MCP tools already loaded and not currently reloading.")
            return
        if self._loading:
            logger.debug(
                "MCPManager.load_tools() called while already loading. Awaiting completion."
            )
            while self._loading:
                await asyncio.sleep(0.1)
            return

        self._loading = True
        logger.info("Starting to load MCP tools...")
        try:
            cfg_path = next((p for p in CONFIG_CANDIDATES if p.exists()), None)
            if cfg_path is None:
                logger.error(
                    f"No MCP configuration file found in candidate paths: {CONFIG_CANDIDATES}"
                )
                self._tools = []  # Ensure tools are empty
                return  # Explicitly return if no config found

            logger.info(f"Loading MCP configuration from: {cfg_path}")
            raw_config = json.loads(cfg_path.read_text())

            if "mcpServers" in raw_config:
                servers_cfg_dict = raw_config["mcpServers"]
            elif "mcp_servers" in raw_config:  # Handle alternative key
                servers_cfg_dict = raw_config["mcp_servers"]
            else:
                logger.warning(
                    f"Could not find 'mcpServers' or 'mcp_servers' key in {cfg_path}. Assuming top level is server dict."
                )
                servers_cfg_dict = raw_config

            enabled_servers_cfg = {
                name: scfg_item
                for name, scfg_item in servers_cfg_dict.items()
                if isinstance(scfg_item, dict) and scfg_item.get("enabled", True)
            }

            if (
                not isinstance(servers_cfg_dict, dict) or not enabled_servers_cfg
            ):  # also check if servers_cfg_dict is a dict
                logger.warning(
                    f"No enabled MCP servers found or invalid format in {cfg_path}. MCPManager will have no tools."
                )
                await (
                    self.close_connections()
                )  # Close any existing connections before setting tools to empty
                self._tools = []
                self._sessions = {}
                self._transport_managers = {}
                return

            servers_to_load = enabled_servers_cfg

            await self.close_connections()  # Close existing sessions before reloading
            self._sessions = {}
            self._tools = []  # Clear tools before loading new ones
            self._transport_managers = {}

            logger.info(
                f"Found {len(servers_to_load)} enabled MCP server(s) to connect to."
            )
            for server_name, scfg in servers_to_load.items():
                logger.debug(
                    f"Attempting to connect to MCP server: {server_name} with config: {scfg}"
                )
                try:
                    session, transport_manager = await self._connect_to_one_server(scfg)
                    self._sessions[server_name] = session
                    if transport_manager:
                        self._transport_managers[server_name] = transport_manager

                    # Load tools for this specific session
                    # load_mcp_tools expects a ClientSession and returns List[BaseTool]
                    session_tools = await load_mcp_tools(session)
                    self._tools.extend(session_tools)
                    logger.info(
                        f"Successfully loaded {len(session_tools)} tools from server: {server_name}"
                    )

                except ConnectionRefusedError as e:
                    logger.error(
                        f"Connection refused for MCP server '{server_name}': {e}. Skipping."
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to connect or load tools for MCP server '{server_name}': {e}",
                        exc_info=True,
                    )

            logger.info(
                f"Finished loading tools. Total tools loaded: {len(self._tools)} from {len(self._sessions)} server(s)."
            )

        except (
            FileNotFoundError
        ):  # Should be caught by the initial check, but as a safeguard
            logger.error(
                f"MCP configuration file not found. Searched: {CONFIG_CANDIDATES}"
            )
            self._tools = []
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding MCP JSON configuration from {cfg_path}: {e}")
            self._tools = []
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during MCP tool loading: {e}",
                exc_info=True,
            )
            self._tools = []  # Ensure tools are empty on any critical failure
        finally:
            self._loading = False

    def get_all_loaded_tools(self) -> List[BaseTool]:
        """Returns a list of all loaded LangChain BaseTool objects."""
        if not self._tools and not self._loading:
            logger.warning(
                "get_all_loaded_tools called but no tools are loaded and not currently loading. Consider calling load_tools() first."
            )
        return self._tools

    async def close_connections(self) -> None:
        """Gracefully closes all active MCP sessions and their transport managers."""
        logger.info(
            f"Closing {len(self._transport_managers)} MCP transport managers and {len(self._sessions)} sessions."
        )

        # Primarily close transport managers, as they manage the underlying streams.
        # ClientSession lifecycle is often tied to these streams.
        transport_close_tasks = [
            tm.__aexit__(None, None, None)
            for tm in self._transport_managers.values()
            if tm is not None and hasattr(tm, "__aexit__")
        ]

        if transport_close_tasks:
            results = await asyncio.gather(
                *transport_close_tasks, return_exceptions=True
            )
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    manager_key_list = list(self._transport_managers.keys())
                    if i < len(manager_key_list):
                        manager_key = manager_key_list[i]
                        logger.error(
                            f"Error closing transport manager for '{manager_key}': {result}"
                        )
                    else:
                        logger.error(
                            f"Error closing an unidentified transport manager: {result}"
                        )

        # Clear stored objects after attempting to close
        self._sessions.clear()
        self._transport_managers.clear()
        # Tools are not cleared here as they are re-populated by load_tools().
        # If close_connections is meant to be a full reset, then self._tools.clear() might be added.
        logger.info(
            "Finished closing MCP transport managers. Associated sessions are implicitly closed."
        )

    async def _connect_to_one_server(
        self, server_config: Dict[str, Any]
    ) -> Tuple[ClientSession, Optional[AsyncContextManager]]:
        """
        Connects to a single MCP server based on its configuration.
        Returns a ClientSession and its transport manager (if any).
        """
        read_stream: Optional[asyncio.StreamReader] = None
        write_stream: Optional[asyncio.StreamWriter] = None
        transport_manager: Optional[AsyncContextManager] = None

        try:
            # Preferred method: Use the SDK's open_server_from_config for various transports
            # This relies on the mcp.client.utils import.
            sdk_transport_manager = await open_server_from_config(server_config)
            read_stream, write_stream, *_ = await sdk_transport_manager.__aenter__()
            transport_manager = sdk_transport_manager
            logger.debug(
                f"Connected to server using open_server_from_config: {server_config.get('name', server_config)}"
            )
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            ImportError,
        ) as e:  # Added ImportError
            logger.warning(
                f"MCP SDK's open_server_from_config failed for {server_config.get('name', server_config)} "
                f"({type(e).__name__}: {e}). Attempting direct TCP if host/port defined."
            )
            # Fallback for direct TCP if 'host' and 'port' are specified
            if "host" in server_config and "port" in server_config:
                try:
                    read_stream, write_stream = await self._custom_socket_transport(
                        server_config
                    )
                    logger.debug(
                        f"Connected to server using custom TCP transport: {server_config.get('name', server_config)}"
                    )
                except Exception as tcp_e:
                    logger.error(
                        f"Custom TCP transport also failed for {server_config.get('name', server_config)}: {tcp_e}"
                    )
                    raise ConnectionError(
                        f"Failed to connect via both SDK helper and custom TCP for {server_config.get('name', server_config)}"
                    ) from tcp_e
            else:  # No fallback possible if not TCP or if open_server_from_config fails for other reasons
                raise ConnectionError(
                    f"Cannot establish connection for {server_config.get('name', server_config)}. "
                    f"SDK helper failed and no host/port for TCP fallback."
                ) from e

        if read_stream is None or write_stream is None:
            raise ConnectionError(
                f"Failed to establish read/write streams for server: {server_config.get('name', server_config)}"
            )

        session = ClientSession(read_stream, write_stream)  # type: ignore
        await session.initialize()
        return session, transport_manager

    async def _custom_socket_transport(
        self, server_config: Dict[str, Any]
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Establishes a direct TCP socket connection."""
        host = server_config.get("host", "127.0.0.1")
        port = server_config.get("port")
        if port is None:  # Ensure port is present for custom TCP
            raise ValueError(
                f"Port is required for custom TCP transport for server: {server_config.get('name', server_config)}"
            )
        if not isinstance(port, int):
            raise ValueError(
                f"Port must be an integer, got {port} for server: {server_config.get('name', server_config)}"
            )

        logger.debug(
            f"Opening custom TCP transport to {host}:{port} for {server_config.get('name', 'Unknown Server')}"
        )
        return await asyncio.open_connection(host, port)


async def get_mcp_manager_instance() -> MCPManager:
    """
    Provides access to the singleton MCPManager instance, loading tools if not already loaded.
    """
    manager = MCPManager()
    # Load tools only if they haven't been loaded yet and not currently in the process of loading.
    if not manager.get_all_loaded_tools() and not manager._loading:
        logger.debug(
            "MCPManager instance requested, tools not loaded yet. Initiating tool loading."
        )
        await manager.load_tools()
    elif manager._loading:
        logger.debug(
            "MCPManager instance requested while tools are already loading. Waiting for completion."
        )
        while manager._loading:  # Wait if another coroutine is already loading
            await asyncio.sleep(0.1)
    else:
        logger.debug("MCPManager instance requested, tools already loaded.")
    return manager


# Example of how create_mcp_tool_param_model might be used if needed (e.g. for dynamic UI generation before tools are BaseTools)
# async def example_usage_of_param_model_creator():
#     # This is a conceptual example. In practice, you'd get the schema from an MCP tool description
#     # before it's converted to a LangChain BaseTool by load_mcp_tools.
#     # For instance, if you call session.list_tools() yourself and inspect tool.inputSchema.
#     example_schema = {
#         "type": "object",
#         "properties": {
#             "param1": {"type": "string", "description": "First parameter"},
#             "param2": {"type": "integer"}
#         },
#         "required": ["param1"]
#     }
#     ParamModel = create_mcp_tool_param_model(example_schema, "MyExampleTool")
#     # Now ParamModel can be used, e.g., ParamModel(param1="value", param2=123)
#     # Or for generating UI elements from its schema.
#     print(ParamModel.model_json_schema())
