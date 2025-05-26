"""
Shared MCP client & tool registry.

* Reads any mcp.json
* Connects to every listed server (stdio, SSE, Streamable HTTP, or custom TCP)
* Performs the MCP handshake once and caches ClientSession objects
* Exposes a LangChain-ready list of tools via registry.tools
* Retains create_tool_param_model for optional per-tool pydantic validation
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from mcp import ClientSession
from mcp.client.utils import open_server_from_config  # auto stdio/SSE/HTTP
from langchain_mcp_adapters.tools import load_mcp_tools
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)


# ---------- Your original param-model helper (unchanged) ----------------- #
def create_tool_param_model(tool) -> Type[BaseModel]:
    try:
        if hasattr(tool, "inputSchema") and tool.inputSchema:
            schema = tool.inputSchema
            props = schema.get("properties", {})
            required = schema.get("required", [])
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
                f"{tool.name.replace('-', '_').title()}Params", **field_defs
            )
        # fallback
        return create_model(f"{tool.name.replace('-', '_').title()}Params")
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to build param model for %s: %s", tool.name, exc)
        return create_model(f"{tool.name.replace('-', '_').title()}Params")


# ------------------------------------------------------------------------ #

CONFIG_CANDIDATES = [Path(".cursor/mcp.json"), Path("mcp.json")]


class ToolRegistry:
    """Singleton cache of MCP ClientSessions and LangChain Tool objects."""

    _instance: "ToolRegistry | None" = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, ClientSession] = {}
            cls._instance._tools: List = []
        return cls._instance

    # ---------------------- public API ----------------------------------- #
    async def load(self) -> None:
        """Boot servers & cache tools. Safe to call multiple times."""
        if self._tools:  # already initialised
            return

        cfg_path = next((p for p in CONFIG_CANDIDATES if p.exists()), None)
        if cfg_path is None:
            raise FileNotFoundError("No mcp.json or .cursor/mcp.json found")

        servers_cfg = json.loads(cfg_path.read_text())["mcpServers"]

        for name, scfg in servers_cfg.items():
            session = await self._connect_one(scfg)
            self._sessions[name] = session
            self._tools.extend(await load_mcp_tools(session))

        logger.info(
            "Loaded %d MCP tools from %d server(s).",
            len(self._tools),
            len(self._sessions),
        )

    @property
    def tools(self):
        return self._tools

    async def close(self) -> None:
        """Gracefully close all live sessions."""
        await asyncio.gather(*(sess.close() for sess in self._sessions.values()))

    # ------------------ internal transport multiplexer ------------------ #
    async def _connect_one(self, scfg: Dict[str, Any]) -> ClientSession:
        """
        Return an initialised ClientSession for a single server block.
        Falls back to raw TCP/WebSocket if the SDK helper can't handle it.
        """
        try:
            read, write, *_ = await (await open_server_from_config(scfg)).__aenter__()
        except ValueError:
            read, write = await self._socket_transport(scfg)  # custom transport

        session = ClientSession(read, write)
        await session.initialize()
        return session

    async def _socket_transport(
        self, scfg: Dict[str, Any]
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        host, port = scfg.get("host", "127.0.0.1"), scfg.get("port", 7797)
        logger.debug("Opening custom TCP transport to %s:%s", host, port)
        return await asyncio.open_connection(host, port)


# ------------------------- convenience loader --------------------------- #
async def setup_mcp_client_and_tools() -> ToolRegistry:
    """
    Thin wrapper retained for API compatibility with your project’s earlier helper.
    """
    reg = ToolRegistry()
    await reg.load()
    return reg
