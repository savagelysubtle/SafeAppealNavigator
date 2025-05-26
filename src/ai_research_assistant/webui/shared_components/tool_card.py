"""
Reusable Tool Card Component for Gradio interfaces.
Used to display information and actions for individual tools,
likely within an MCP Tool Marketplace.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

import gradio as gr

if TYPE_CHECKING:
    from src.ai_research_assistant.webui.webui_manager import WebuiManager


class ToolCard(gr.Group):
    """
    A Gradio component that displays information about a tool and provides actions
    like install, configure, or run.
    """

    def __init__(
        self,
        tool_metadata: Dict[str, Any],
        webui_manager: Optional["WebuiManager"] = None,
        elem_id: Optional[str] = None,
        elem_classes: Optional[list[str]] = None,
        **kwargs,
    ):
        """
        Initializes the ToolCard component.

        Args:
            tool_metadata (Dict[str, Any]): A dictionary containing metadata for the tool.
                Expected keys might include: 'name', 'description', 'version',
                'author', 'status' (e.g., 'installed', 'not_installed', 'needs_config'),
                'icon', 'tags'.
            webui_manager (Optional[WebuiManager], optional): Reference to WebUI manager. Defaults to None.
            elem_id (Optional[str], optional): HTML ID for the Gradio component. Defaults to None.
            elem_classes (Optional[list[str]], optional): CSS classes. Defaults to None.
            **kwargs: Additional keyword arguments for gr.Group.
        """
        super().__init__(**kwargs)

        self.tool_metadata = tool_metadata
        self.webui_manager = webui_manager
        self._elem_id_base = (
            elem_id
            or f"tool-card-{tool_metadata.get('name', 'unknown').lower().replace(' ', '-')}"
        )
        self._elem_classes = (elem_classes or []) + ["tool-card"]

        # --- Extract common metadata (with defaults) ---
        tool_name = self.tool_metadata.get("name", "Unnamed Tool")
        tool_icon = self.tool_metadata.get("icon", "🛠️")
        tool_description = self.tool_metadata.get(
            "description", "No description available."
        )
        tool_version = self.tool_metadata.get("version", "N/A")
        tool_status = self.tool_metadata.get(
            "status", "unknown"
        )  # e.g., installed, not_installed, error
        tool_author = self.tool_metadata.get("author", "Unknown Author")
        tool_tags = self.tool_metadata.get("tags", [])

        with self:
            with gr.Row(elem_classes=self._elem_classes + ["tool-card-header"]):
                gr.Markdown(
                    f"### {tool_icon} {tool_name}", elem_id=f"{self._elem_id_base}-name"
                )
                self.status_badge = gr.Label(
                    value=self._get_status_display(tool_status),
                    elem_id=f"{self._elem_id_base}-status-badge",
                    # Further styling via CSS based on status (e.g., color)
                    elem_classes=self._elem_classes
                    + ["tool-status-badge", f"status-{tool_status}"],
                )

            gr.Markdown(
                tool_description,
                elem_id=f"{self._elem_id_base}-description",
                elem_classes=self._elem_classes + ["tool-description"],
            )

            with gr.Row(elem_classes=self._elem_classes + ["tool-card-details"]):
                gr.Textbox(
                    value=f"Version: {tool_version}",
                    label="Version",
                    interactive=False,
                    elem_id=f"{self._elem_id_base}-version",
                )
                gr.Textbox(
                    value=f"Author: {tool_author}",
                    label="Author",
                    interactive=False,
                    elem_id=f"{self._elem_id_base}-author",
                )

            if tool_tags:
                tags_html = (
                    "<div class='tool-tags-container'>"
                    + "".join(
                        [f"<span class='tool-tag'>{tag}</span>" for tag in tool_tags]
                    )
                    + "</div>"
                )
                gr.HTML(tags_html, elem_id=f"{self._elem_id_base}-tags")

            with gr.Row(elem_classes=self._elem_classes + ["tool-card-actions"]):
                self.install_button = gr.Button(
                    "Install",
                    elem_id=f"{self._elem_id_base}-install-btn",
                    visible=(tool_status == "not_installed"),
                )
                self.configure_button = gr.Button(
                    "Configure",
                    elem_id=f"{self._elem_id_base}-configure-btn",
                    visible=(
                        tool_status == "installed" or tool_status == "needs_config"
                    ),
                )
                self.run_button = gr.Button(
                    "Run",
                    elem_id=f"{self._elem_id_base}-run-btn",
                    visible=(tool_status == "installed"),
                    variant="primary",
                )
                self.uninstall_button = gr.Button(
                    "Uninstall",
                    elem_id=f"{self._elem_id_base}-uninstall-btn",
                    visible=(tool_status == "installed"),
                    variant="stop",
                )

            # --- Event Handlers (Placeholders - to be connected by the parent UI) ---
            # Example: self.install_button.click(fn=handle_install, inputs=[gr.State(self.tool_metadata)], outputs=[...])
            # The actual logic for install/configure/run/uninstall will be implemented in the
            # MCP Marketplace view or a relevant controller that uses these ToolCards.

    def _get_status_display(self, status: str) -> str:
        """Returns a user-friendly string for the status badge."""
        status_map = {
            "installed": "✅ Installed",
            "not_installed": "➕ Not Installed",
            "needs_config": "⚙️ Needs Configuration",
            "running": "⏳ Running",
            "error": "❌ Error",
            "deprecated": "🗑️ Deprecated",
            "unknown": "❓ Unknown",
        }
        return status_map.get(status, "❓ Unknown")


# Example Usage
if __name__ == "__main__":
    from gradio.themes import Soft as SoftTheme

    example_tools_metadata = [
        {
            "name": "Super Analyzer",
            "icon": "🔍",
            "description": "Analyzes complex data structures and provides insights.",
            "version": "1.2.3",
            "status": "installed",
            "author": "AI Corp",
            "tags": ["analysis", "data", "AI"],
        },
        {
            "name": "Quick Scraper",
            "icon": "🕸️",
            "description": "Scrapes web pages efficiently.",
            "version": "0.5.0",
            "status": "not_installed",
            "author": "Scraper Inc.",
            "tags": ["web", "scraping", "utility"],
        },
        {
            "name": "Configurator Pro",
            "icon": "🔧",
            "description": "Advanced configuration management tool.",
            "version": "2.1.0",
            "status": "needs_config",
            "author": "DevTools LLC",
            "tags": ["developer", "config", "system"],
        },
        {
            "name": "Legacy Tool",
            "icon": "💾",
            "description": "An older tool that is now deprecated.",
            "version": "0.1.0",
            "status": "deprecated",
            "author": "Oldtimers Inc.",
            "tags": ["legacy"],
        },
    ]

    with gr.Blocks(theme=SoftTheme()) as demo:
        gr.Markdown("# Tool Card Demo")
        gr.Markdown("Demonstrates the `ToolCard` component for displaying MCP tools.")

        with gr.Tab("Individual Cards"):
            with gr.Row():
                for i, metadata in enumerate(example_tools_metadata):
                    with gr.Column(scale=1):
                        ToolCard(tool_metadata=metadata, elem_id=f"tool_card_demo_{i}")

        with gr.Tab("Inside a Grid (Conceptual)"):
            gr.Markdown(
                "ToolCards would typically be dynamically generated and placed in a grid or list."
            )
            # This is conceptual; a real marketplace would dynamically create these
            with gr.Column():  # Using Column to simulate a list for now
                for i, metadata in enumerate(example_tools_metadata):
                    ToolCard(tool_metadata=metadata, elem_id=f"tool_card_grid_demo_{i}")

    demo.launch()
