import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import gradio as gr
from browser_use.agent.service import Agent
from gradio.components import Component

from src.browser_use_web_ui.agent.deep_research.deep_research_agent import (
    DeepResearchAgent,
)
from src.browser_use_web_ui.agent.legal_research.legal_case_agent import (
    LegalCaseResearchAgent,
)
from src.browser_use_web_ui.browser.custom_browser import CustomBrowser
from src.browser_use_web_ui.browser.custom_context import CustomBrowserContext
from src.browser_use_web_ui.controller.custom_controller import CustomController


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, Component] = {}
        self.component_to_id: dict[Component, str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # Shared MCP server config for all tabs
        self.mcp_server_config: Optional[dict] = None

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
        self.dr_save_dir: Optional[str] = None

    def init_collector_agent(self) -> None:
        """
        init collector agent
        """
        self.collector_current_task: Optional[asyncio.Task[Any]] = None
        self.collector_task_id: Optional[str] = None
        self.collector_download_dir: Optional[str] = None

    def init_legal_research_agent(self) -> None:
        """
        init legal research agent
        """
        self.lr_agent: Optional[LegalCaseResearchAgent] = None
        self.lr_current_task: Optional[asyncio.Task[Any]] = None
        self.lr_task_id: Optional[str] = None
        self.lr_download_dir: Optional[str] = None
        self.lr_research_results: Optional[Dict[str, Any]] = None

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
        config_path = os.path.join(self.settings_save_dir, f"{config_name}.json")
        with open(config_path, "w") as fw:
            json.dump(cur_settings, fw, indent=4)

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
