"""
WebUI Components Module

Exports all available WebUI components including the Phase 4 specialized agents.
"""

from .agent_settings_tab import create_agent_settings_tab
from .browser_launch_tab import create_browser_launch_tab
from .browser_settings_tab import create_browser_settings_tab
from .browser_use_agent_tab import create_browser_use_agent_tab
from .collector_agent_tab import create_collector_agent_tab
from .cross_reference_agent_tab import create_cross_reference_agent_tab
from .database_maintenance_agent_tab import create_database_maintenance_agent_tab
from .deep_research_agent_tab import create_deep_research_agent_tab
from .global_settings_panel import create_global_settings_panel
from .intake_agent_tab import create_intake_agent_tab
from .legal_research_tab import create_legal_research_tab
from .load_save_config_tab import create_load_save_config_tab
from .mcp_server_tab import create_mcp_server_tab
from .search_agent_tab import create_search_agent_tab

__all__ = [
    # Core WebUI tabs
    "create_agent_settings_tab",
    "create_browser_launch_tab",
    "create_browser_settings_tab",
    "create_browser_use_agent_tab",
    "create_collector_agent_tab",
    "create_deep_research_agent_tab",
    "create_global_settings_panel",
    "create_legal_research_tab",
    "create_load_save_config_tab",
    "create_mcp_server_tab",
    # Phase 4 specialized agent tabs
    "create_intake_agent_tab",
    "create_search_agent_tab",
    "create_cross_reference_agent_tab",
    "create_database_maintenance_agent_tab",
]
