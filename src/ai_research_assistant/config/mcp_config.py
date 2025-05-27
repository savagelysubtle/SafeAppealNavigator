"""
MCP Configuration Manager (mcp_config.py)

This module is responsible for loading and providing access to static configurations
related to the Model Context Protocol (MCP) integration. It handles:
- Metadata about MCP servers (from mcp_servers.json).
- Agent-specific MCP tool/server mappings (from agent_mcp_mapping.json).
- Global development/runtime settings for MCP (e.g., caching, from development.json).

It does not handle live connections or tool loading; that is the responsibility
of the MCPManager (mcp.manager.py).

This file also defines Pydantic models for client-side MCP server and tool configuration.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import canonical models from mcp_client_models

logger = logging.getLogger(__name__)

# --- Client-side MCP Server and Tool Configuration Models ---

# --- Existing MCPConfigLoader and related functions ---


class MCPConfigLoader:
    """
    Loads and provides access to various MCP-related configuration files.

    This includes server definitions (for metadata purposes), agent-to-tool/server
    mappings, and global MCP integration settings.
    """

    def __init__(self, config_dir: Optional[str] = None):
        # Default to config directory relative to this file
        if config_dir is None:
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = Path(config_dir)

        self.mcp_config_file = self.config_dir / "mcp" / "mcp_servers.json"
        self.agent_mapping_file = self.config_dir / "agent_mcp_mapping.json"
        self.dev_settings_file = self.config_dir / "development.json"

        self._mcp_config: Optional[Dict[str, Any]] = None
        self._agent_mappings: Optional[Dict[str, Any]] = None
        self._dev_settings: Optional[Dict[str, Any]] = None

    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from JSON file."""
        if self._mcp_config is None:
            if not self.mcp_config_file.exists():
                logger.warning(f"MCP config file not found: {self.mcp_config_file}")
                self._mcp_config = {"mcp_servers": {}, "global_settings": {}}
                return self._mcp_config

            try:
                with open(self.mcp_config_file, "r") as f:
                    self._mcp_config = json.load(f)
                logger.info(f"Loaded MCP config from {self.mcp_config_file}")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")
                self._mcp_config = {"mcp_servers": {}, "global_settings": {}}

        assert self._mcp_config is not None
        return self._mcp_config

    def load_agent_mappings(self) -> Dict[str, Any]:
        """Load agent-to-MCP-tool mappings from JSON file."""
        if self._agent_mappings is None:
            if not self.agent_mapping_file.exists():
                logger.warning(
                    f"Agent mapping file not found: {self.agent_mapping_file}"
                )
                self._agent_mappings = {
                    "agent_mcp_mappings": {},
                    "global_agent_settings": {},
                }
                return self._agent_mappings

            try:
                with open(self.agent_mapping_file, "r") as f:
                    self._agent_mappings = json.load(f)
                logger.info(f"Loaded agent mappings from {self.agent_mapping_file}")
            except Exception as e:
                logger.error(f"Failed to load agent mappings: {e}")
                self._agent_mappings = {
                    "agent_mcp_mappings": {},
                    "global_agent_settings": {},
                }

        assert self._agent_mappings is not None
        return self._agent_mappings

    def load_dev_settings(self) -> Dict[str, Any]:
        """Load development settings from JSON file."""
        if self._dev_settings is None:
            if not self.dev_settings_file.exists():
                logger.warning(f"Dev settings file not found: {self.dev_settings_file}")
                self._dev_settings = {}
                return self._dev_settings

            try:
                with open(self.dev_settings_file, "r") as f:
                    self._dev_settings = json.load(f)
                logger.info(f"Loaded dev settings from {self.dev_settings_file}")
            except Exception as e:
                logger.error(f"Failed to load dev settings: {e}")
                self._dev_settings = {}

        assert self._dev_settings is not None
        return self._dev_settings

    def get_enabled_servers(self) -> List[str]:
        """Get list of enabled MCP server names."""
        config = self.load_mcp_config()
        servers = config.get("mcp_servers", {})
        return [
            name
            for name, server_config in servers.items()
            if server_config.get("enabled", False)
        ]

    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific MCP server."""
        config = self.load_mcp_config()
        servers = config.get("mcp_servers", {})
        return servers.get(server_name)

    def get_agent_tools(self, agent_class_name: str) -> List[str]:
        """Get list of MCP tools for a specific agent."""
        mappings = self.load_agent_mappings()
        agent_mappings = mappings.get("agent_mcp_mappings", {})
        agent_config = agent_mappings.get(agent_class_name, {})
        # Note: Tool names in agent_mcp_mapping.json (under 'primary_tools')
        # should match the names generated by langchain_mcp_adapters
        # (e.g., 'mcp_ServerName_OriginalToolName') for effective filtering.
        return agent_config.get("primary_tools", [])

    def get_agent_servers(self, agent_class_name: str) -> Dict[str, List[str]]:
        """Get required and optional servers for a specific agent."""
        mappings = self.load_agent_mappings()
        agent_mappings = mappings.get("agent_mcp_mappings", {})
        agent_config = agent_mappings.get(agent_class_name, {})

        return {
            "required": agent_config.get("required_servers", []),
            "optional": agent_config.get("optional_servers", []),
        }

    def validate_agent_requirements(self, agent_class_name: str) -> Dict[str, Any]:
        """Validate that all required MCP servers are available for an agent."""
        agent_servers = self.get_agent_servers(agent_class_name)
        enabled_servers = self.get_enabled_servers()

        required_servers = agent_servers["required"]
        optional_servers = agent_servers["optional"]

        missing_required = [
            srv for srv in required_servers if srv not in enabled_servers
        ]
        missing_optional = [
            srv for srv in optional_servers if srv not in enabled_servers
        ]

        return {
            "valid": len(missing_required) == 0,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "available_servers": enabled_servers,
        }

    def get_server_transport_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get transport configuration for starting an MCP server."""
        server_data = self.get_server_config(server_name)
        if not server_data:
            return None

        transport_dict = server_data.get("transport", {})

        # Resolve relative paths to absolute paths if working_directory is present
        if "working_directory" in transport_dict:
            working_dir = Path(transport_dict["working_directory"])
            if not working_dir.is_absolute():
                project_root = Path(__file__).parent.parent.parent.parent
                transport_dict["working_directory"] = str(project_root / working_dir)

        return transport_dict

    def get_mcp_cache_settings(self) -> Dict[str, Any]:
        """Get MCP caching settings from development config."""
        dev_settings = self.load_dev_settings()
        mcp_integration = dev_settings.get("mcp_integration", {})

        return {
            "enable_caching": mcp_integration.get("enable_mcp_caching", True),
            "cache_dir": mcp_integration.get("mcp_cache_dir", "./tmp/mcp_cache"),
            "cache_duration_minutes": 60,  # Default from agent mapping config
        }


# Global instance for easy importing
mcp_config = MCPConfigLoader()


# Convenience functions for common operations
def get_agent_mcp_tools(agent_class_name: str) -> List[str]:
    """Get MCP tools for an agent class."""
    return mcp_config.get_agent_tools(agent_class_name)


def validate_agent_mcp_setup(agent_class_name: str) -> bool:
    """Validate that an agent's MCP requirements are met."""
    validation = mcp_config.validate_agent_requirements(agent_class_name)
    if not validation["valid"]:
        logger.error(
            f"Agent {agent_class_name} missing required MCP servers: {validation['missing_required']}"
        )
    return validation["valid"]


def get_server_startup_config(server_name: str) -> Optional[Dict[str, Any]]:
    """Get startup configuration for an MCP server."""
    return mcp_config.get_server_transport_config(server_name)
