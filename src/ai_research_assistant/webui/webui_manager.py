import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import gradio as gr
from browser_use.agent.service import Agent
from gradio.components import Component

from src.ai_research_assistant.agent.deep_research.deep_research_agent import (
    DeepResearchAgent,
)
from src.ai_research_assistant.agent.legal_research.legal_case_agent import (
    LegalCaseResearchAgent,
)
from src.ai_research_assistant.browser.custom_browser import CustomBrowser
from src.ai_research_assistant.browser.custom_context import CustomBrowserContext
from src.ai_research_assistant.config.mcp_config import mcp_config
from src.ai_research_assistant.controller.custom_controller import CustomController


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, Component] = {}
        self.component_to_id: dict[Component, str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # MCP configuration integration
        self.mcp_config_loader = mcp_config
        self.mcp_server_config: Optional[dict] = None

        # Global settings manager - will be set by global_settings_panel.py
        self.global_settings_manager: Optional[Any] = None

        # Load MCP configuration on startup
        self.refresh_mcp_config()

    def refresh_mcp_config(self) -> None:
        """Refresh MCP configuration from the configuration files."""
        try:
            self.mcp_server_config = self.mcp_config_loader.load_mcp_config()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load MCP configuration: {e}")
            self.mcp_server_config = None

    def get_mcp_tools_for_agent(self, agent_class_name: str) -> List[str]:
        """Get MCP tools available for a specific agent."""
        return self.mcp_config_loader.get_agent_tools(agent_class_name)

    def validate_agent_mcp_requirements(self, agent_class_name: str) -> bool:
        """Validate that an agent's MCP requirements are satisfied."""
        validation = self.mcp_config_loader.validate_agent_requirements(
            agent_class_name
        )
        return validation["valid"]

    def init_browser_use_agent(self) -> None:
        """
        init browser use agent
        """
        self.bu_agent: Optional[Agent] = None
        self.bu_browser: Optional[CustomBrowser] = None
        self.bu_browser_context: Optional[CustomBrowserContext] = None
        self.bu_controller: Optional[CustomController] = None
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_response_event: Optional[asyncio.Event] = None
        self.bu_user_help_response: Optional[str] = None
        self.bu_current_task: Optional[asyncio.Task[Any]] = None
        self.bu_agent_task_id: Optional[str] = None

    def init_deep_research_agent(self) -> None:
        """
        init deep research agent
        """
        self.dr_agent: Optional[DeepResearchAgent] = None
        self.dr_current_task: Optional[asyncio.Task[Any]] = None
        self.dr_task_id: Optional[str] = None
        self.dr_save_dir: Optional[str] = "./tmp/deep_research"

    def init_collector_agent(self) -> None:
        """
        init collector agent
        """
        self.collector_current_task: Optional[asyncio.Task[Any]] = None
        self.collector_task_id: Optional[str] = None
        self.collector_download_dir: Optional[str] = "./tmp/collector_downloads"

    def init_legal_research_agent(self) -> None:
        """
        init legal research agent
        """
        self.lr_agent: Optional[LegalCaseResearchAgent] = None
        self.lr_current_task: Optional[asyncio.Task[Any]] = None
        self.lr_task_id: Optional[str] = None
        self.lr_download_dir: Optional[str] = "./tmp/legal_research"
        self.lr_research_results: Optional[Dict[str, Any]] = None

    def init_intake_agent(self) -> None:
        """
        init intake agent
        """
        self.intake_current_task: Optional[asyncio.Task[Any]] = None
        self.intake_task_id: Optional[str] = None
        self.intake_output_dir: Optional[str] = "./tmp/intake_output"

    def init_search_agent(self) -> None:
        """
        init search agent
        """
        self.search_current_task: Optional[asyncio.Task[Any]] = None
        self.search_task_id: Optional[str] = None
        self.search_results: Optional[Dict[str, Any]] = None

    def init_cross_reference_agent(self) -> None:
        """
        init cross reference agent
        """
        self.cr_current_task: Optional[asyncio.Task[Any]] = None
        self.cr_task_id: Optional[str] = None
        self.cr_analysis_results: Optional[Dict[str, Any]] = None

    def init_database_maintenance_agent(self) -> None:
        """
        init database maintenance agent
        """
        self.dm_current_task: Optional[asyncio.Task[Any]] = None
        self.dm_task_id: Optional[str] = None
        self.dm_maintenance_results: Optional[Dict[str, Any]] = None

    def init_interactive_chat(self) -> None:
        """
        init interactive chat manager
        """
        self.chat_manager: Optional[Any] = None

    def add_components(
        self, tab_name: str, components_dict: dict[str, "Component"]
    ) -> None:
        """
        Add tab components
        """
        for comp_name, component in components_dict.items():
            comp_id = f"{tab_name}.{comp_name}"
            self.id_to_component[comp_id] = component
            self.component_to_id[component] = comp_id

    def get_components(self) -> list["Component"]:
        """
        Get all components
        """
        return list(self.id_to_component.values())

    def get_component_by_id(self, comp_id: str) -> "Component":
        """
        Get component by id
        """
        return self.id_to_component[comp_id]

    def get_id_by_component(self, comp: "Component") -> str:
        """
        Get id by component
        """
        return self.component_to_id[comp]

    def save_config(self, components: Dict["Component", str]) -> str:
        """
        Save config and return the path to the saved config file.
        """
        cur_settings = {}
        for comp in components:
            if (
                not isinstance(comp, gr.Button)
                and not isinstance(comp, gr.File)
                and str(getattr(comp, "interactive", True)).lower() != "false"
            ):
                comp_id = self.get_id_by_component(comp)
                cur_settings[comp_id] = components[comp]

        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        config_path = os.path.join(
            self.settings_save_dir, f"webui_config_{config_name}.json"
        )
        with open(config_path, "w") as fw:
            json.dump(cur_settings, fw, indent=4)

        return config_path

    def save_settings(self, settings: Dict[str, Any]) -> str:
        """
        Save global settings and return the path to the saved settings file.
        """
        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        config_path = os.path.join(
            self.settings_save_dir, f"global_settings_{config_name}.json"
        )
        with open(config_path, "w") as fw:
            json.dump(settings, fw, indent=4)

        return config_path

    def load_config(self, config_path: str):
        """
        Load config
        """
        with open(config_path, "r") as fr:
            ui_settings = json.load(fr)

        update_components = {}
        for comp_id, comp_val in ui_settings.items():
            if comp_id in self.id_to_component:
                comp = self.id_to_component[comp_id]
                # Remove 'type' argument, not valid for gr.Chatbot
                if comp.__class__.__name__ == "Chatbot":
                    update_components[comp] = comp.__class__(value=comp_val)
                else:
                    update_components[comp] = comp.__class__(value=comp_val)
                    if comp_id == "agent_settings.planner_llm_provider":
                        yield update_components  # yield provider, let callback run
                        time.sleep(0.1)  # wait for Gradio UI callback

        config_status = self.id_to_component["load_save_config.config_status"]
        update_components.update(
            {
                config_status: config_status.__class__(
                    value=f"Successfully loaded config: {config_path}"
                )
            }
        )
        yield update_components

    def get_agent_save_directory(
        self, agent_type: str, task_id: Optional[str] = None
    ) -> str:
        """Get the appropriate save directory for an agent type."""
        base_dirs = {
            "deep_research": "./tmp/deep_research",
            "legal_research": "./tmp/legal_research",
            "collector": "./tmp/collector_downloads",
            "browser_use": "./tmp/browser_history",
        }

        base_dir = base_dirs.get(agent_type, "./tmp/agent_output")

        if task_id:
            return os.path.join(base_dir, task_id)

        return base_dir

    def get_development_settings(self) -> Dict[str, Any]:
        """Get development settings from the configuration system."""
        try:
            return self.mcp_config_loader.load_dev_settings()
        except Exception:
            return {}
