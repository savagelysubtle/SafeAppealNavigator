"""
Reusable Collapsible Card Component for Gradio interfaces.
"""

from typing import TYPE_CHECKING, Optional

import gradio as gr
from gradio.themes import Soft as SoftTheme

if TYPE_CHECKING:
    from src.ai_research_assistant.webui.webui_manager import WebuiManager


class CollapsibleCard(gr.Group):
    """
    A Gradio component that provides a collapsible card interface.
    It allows organizing content into sections that can be expanded or collapsed by the user.
    """

    def __init__(
        self,
        title: str,
        icon: str = "📁",
        open_by_default: bool = True,
        webui_manager: Optional["WebuiManager"] = None,
        elem_id: Optional[str] = None,
        elem_classes: Optional[list[str]] = None,
        **kwargs,
    ):
        """
        Initializes the CollapsibleCard component.

        Args:
            title (str): The title displayed in the header of the card.
            icon (str, optional): An emoji or character to display as an icon in the header. Defaults to "📁".
            open_by_default (bool, optional): Whether the card should be expanded by default. Defaults to True.
            webui_manager (Optional[WebuiManager], optional): Reference to the WebUI manager for state management if needed. Defaults to None.
            elem_id (Optional[str], optional): The HTML ID for the Gradio component. Defaults to None.
            elem_classes (Optional[list[str]], optional): List of CSS classes for the Gradio component. Defaults to None.
            **kwargs: Additional keyword arguments for gr.Group.
        """
        super().__init__(**kwargs)

        self.title = title
        self.icon = icon
        self.webui_manager = webui_manager
        self._expanded = open_by_default
        self._elem_id = elem_id
        self._elem_classes = elem_classes

        with self:
            # State to hold the current expanded/collapsed state
            self.expanded_state = gr.State(value=self._expanded)

            # Header (Button for clickability)
            # Using a gr.Button with styling to look like a header for better click detection
            # The icon will change based on the expanded state using a JS trick or by re-rendering
            self.header_button = gr.Button(
                value=f"{self._get_arrow_icon()} {self.icon} {self.title}",
                variant="secondary",  # Use secondary to make it less prominent than primary action buttons
                elem_id=f"{self._elem_id}_header" if self._elem_id else None,
                elem_classes=(self._elem_classes if self._elem_classes else [])
                + ["collapsible-card-header"],
            )

            # Content Area (initially visible or hidden based on open_by_default)
            with gr.Column(
                visible=self._expanded,
                elem_id=f"{self._elem_id}_content" if self._elem_id else None,
                elem_classes=(self._elem_classes if self._elem_classes else [])
                + ["collapsible-card-content"],
            ) as self.content_column:
                # Content will be added here by the user of this component
                # Example:
                # with CollapsibleCard("Section 1") as card1:
                #     gr.Markdown("This is inside card 1")
                # The gr.Markdown will be a child of self.content_column
                pass

            # Event handler for toggling visibility
            self.header_button.click(
                fn=self._toggle_visibility,
                inputs=[self.expanded_state],
                outputs=[self.expanded_state, self.content_column, self.header_button],
            )

    def _get_arrow_icon(self) -> str:
        """Returns the appropriate arrow icon based on the expanded state."""
        return "▼" if self._expanded else "▶"

    def _toggle_visibility(
        self, current_expanded_state: bool
    ) -> tuple[bool, gr.Column, gr.Button]:
        """
        Toggles the visibility of the content area.
        This function is called when the header is clicked.
        """
        self._expanded = not current_expanded_state
        new_header_text = f"{self._get_arrow_icon()} {self.icon} {self.title}"

        # The gr.Column itself is returned to update its 'visible' property.
        # The Button is returned to update its text (arrow icon)
        return (
            self._expanded,
            gr.Column(visible=self._expanded),
            gr.Button(value=new_header_text),
        )

    # Allow using the card as a context manager
    def __enter__(self):
        self.content_column.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.content_column.__exit__(exc_type, exc_val, exc_tb)


# Example Usage (can be run standalone if Gradio is installed and this file is executed)
if __name__ == "__main__":
    # Using a simpler theme instantiation for the example
    # For custom themes, refer to Gradio documentation: from gradio.themes import Base, Color
    with gr.Blocks(theme=SoftTheme()) as demo:  # Use the imported SoftTheme
        gr.Markdown("# Collapsible Card Demo")

        with gr.Row():
            with gr.Column(scale=1):
                with CollapsibleCard(
                    title="Configuration Settings",
                    icon="⚙️",
                    open_by_default=True,
                    elem_id="config_card",
                ) as card1:
                    gr.Textbox(label="Setting 1", value="Default Value 1")
                    gr.Slider(label="Setting 2", minimum=0, maximum=100, value=50)
                    gr.Checkbox(label="Enable Feature X")

                with CollapsibleCard(
                    title="Advanced Options",
                    icon="🔧",
                    open_by_default=False,
                    elem_id="advanced_card",
                ) as card2:
                    gr.Markdown("### Advanced Configuration")
                    gr.ColorPicker(label="Theme Color")
                    gr.Radio(["Option A", "Option B"], label="Select Option")

            with gr.Column(scale=2):
                gr.Markdown("## Main Content Area")
                gr.Textbox(label="Notes", lines=5, placeholder="Enter notes here...")

                with CollapsibleCard(
                    title="View Logs",
                    icon="📜",
                    open_by_default=False,
                    elem_id="log_card",
                ) as card3:
                    gr.TextArea(
                        label="Log Output",
                        value="Log line 1\nLog line 2\nLog line 3",
                        lines=5,
                        interactive=False,
                    )

    demo.launch()
