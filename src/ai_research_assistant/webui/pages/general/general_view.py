"""
Agents View

This is the main view for the agents. It will have the main layout and the tabs for the page.
"""

import logging

import gradio as gr

from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def create_general_agents_page(webui_manager: WebuiManager):
    """Creates the UI for the General Agents page."""
    with gr.Column(elem_id="general_agents_page_content") as page_column:
        gr.Markdown("## 📚 General Agents Page")
        gr.Markdown("Content for general, non-orchestrated agents will go here.")
        gr.Markdown("This includes UIs for:")
        gr.Markdown("- Browser Agent")
        gr.Markdown("- Deep Research Agent")
        gr.Markdown("- Search Agent")
        # Placeholder for actual general agent tab/component integration
        logger.info("General Agents page created (placeholder).")
    return page_column
