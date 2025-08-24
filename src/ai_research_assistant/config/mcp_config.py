# src/ai_research_assistant/config/mcp_config.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPConfigLoader:
    """Loads and manages MCP server configurations for AI research agents."""

    def __init__(self):
        # Correctly locate config files from the project root
        project_root = Path(__file__).parent.parent.parent.parent
        self.mcp_config_file = project_root / "data" / "mcp.json"
        self.agent_mapping_file = project_root / "data" / "agent_mcp_mapping.json"

        self._mcp_config: Optional[Dict[str, Any]] = None
        self._agent_mappings: Optional[Dict[str, Any]] = None

    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from JSON file."""
        if self._mcp_config is None:
            if not self.mcp_config_file.exists():
                logger.warning(f"MCP config file not found: {self.mcp_config_file}")
                self._mcp_config = {"mcpServers": {}}
                return self._mcp_config
            try:
                with open(self.mcp_config_file, "r") as f:
                    self._mcp_config = json.load(f)
                logger.info(f"Loaded MCP config from {self.mcp_config_file}")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")
                self._mcp_config = {"mcpServers": {}}
        return self._mcp_config

    def load_agent_mappings(self) -> Dict[str, Any]:
        """Load agent-to-MCP-tool mappings from JSON file."""
        if self._agent_mappings is None:
            if not self.agent_mapping_file.exists():
                logger.warning(
                    f"Agent mapping file not found: {self.agent_mapping_file}"
                )
                self._agent_mappings = {"agent_mcp_mappings": {}}
                return self._agent_mappings
            try:
                with open(self.agent_mapping_file, "r") as f:
                    self._agent_mappings = json.load(f)
                logger.info(f"Loaded agent mappings from {self.agent_mapping_file}")
            except Exception as e:
                logger.error(f"Failed to load agent mappings: {e}")
                self._agent_mappings = {"agent_mcp_mappings": {}}
        return self._agent_mappings


# --- Global instance for easy importing ---
mcp_config = MCPConfigLoader()


# --- Convenience functions that were likely intended to be here ---
def get_agent_mcp_tools(agent_class_name: str) -> List[str]:
    """Get MCP tools for an agent class."""
    mappings = mcp_config.load_agent_mappings()
    agent_mappings = mappings.get("agent_mcp_mappings", {})
    agent_config = agent_mappings.get(agent_class_name, {})
    return agent_config.get("primary_tools", [])


def validate_agent_mcp_setup(agent_class_name: str) -> bool:
    """Validate that an agent's MCP requirements are met."""
    # This is a placeholder for more complex validation logic if needed
    return True
