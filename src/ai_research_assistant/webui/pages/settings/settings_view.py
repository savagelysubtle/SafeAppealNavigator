import logging

import gradio as gr

from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def create_settings_page(webui_manager: WebuiManager):
    """Creates the UI for the Settings page."""
    with gr.Column(elem_id="settings_page_content") as page_column:
        gr.Markdown("## ⚙️ Settings Page")
        gr.Markdown("This page will consolidate all application and agent settings.")
        gr.Markdown("This includes:")
        gr.Markdown("- Global LLM configurations")
        gr.Markdown("- Agent-specific settings")
        gr.Markdown("- Browser settings")
        gr.Markdown("- System/UI preferences")
        gr.Markdown("- Configuration save/load management")
        # Placeholder for settings components (e.g., global_settings_panel)
        # The create_global_settings_panel will likely be integrated here.
        logger.info("Settings page created (placeholder).")
    return page_column
