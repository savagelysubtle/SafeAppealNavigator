"""
Main WebUI Interface for AI Research Assistant - Refactored for Vertical Navigation
"""

import logging

import gradio as gr

from .navigation.navigation_rail import NavigationRail
from .pages import (
    create_interactive_chat_page,
    create_orchestrator_page,
    create_settings_page,
    create_tools_page,
)
from .webui_manager import WebuiManager

# Import shared components if they are to be used directly here, otherwise pages manage them
# from .shared_components.collapsible_card import CollapsibleCard

logger = logging.getLogger(__name__)

# Define a mapping from page_id to page creation functions
PAGE_REGISTRY = {
    "orchestrator_page": create_orchestrator_page,
    "browser_agent_page": lambda wm: gr.Markdown(
        "## Browser Agent Page Content (Placeholder)"
    ),  # Placeholder
    "deep_research_page": lambda wm: gr.Markdown(
        "## Deep Research Page Content (Placeholder)"
    ),  # Placeholder
    "search_agent_page": lambda wm: gr.Markdown(
        "## Search Agent Page Content (Placeholder)"
    ),  # Placeholder
    "intake_agent_page": lambda wm: gr.Markdown(
        "## Intake Agent Page Content (Placeholder)"
    ),  # Placeholder
    "legal_research_page": lambda wm: gr.Markdown(
        "## Legal Research Page Content (Placeholder)"
    ),  # Placeholder
    "collector_agent_page": lambda wm: gr.Markdown(
        "## Collector Agent Page Content (Placeholder)"
    ),  # Placeholder
    "cross_reference_page": lambda wm: gr.Markdown(
        "## Cross Reference Page Content (Placeholder)"
    ),  # Placeholder
    "interactive_chat_page": create_interactive_chat_page,
    "tools_page": create_tools_page,
    "settings_page": create_settings_page,
}


def create_ui(theme_name="Ocean"):
    webui_manager = WebuiManager()
    navigation_rail = NavigationRail(webui_manager, default_page_id="orchestrator_page")

    with gr.Blocks(
        theme=theme_name,  # TODO: Integrate ModernDarkTheme from AllBeAllUIPlan
        title="🚀 AI Research Assistant - Vertical Nav",
        css="""
            /* Basic CSS for 3-column layout - to be refined in modern-ui.css */
            .main-container { display: flex; flex-direction: row; height: 100vh; }
            .navigation-rail-container { width: 220px; border-right: 1px solid #ccc; overflow-y: auto; padding: 10px; background-color: #f9f9f9; }
            .main-content-container { flex-grow: 1; padding: 20px; overflow-y: auto; }
            .live-output-container { width: 300px; border-left: 1px solid #ccc; overflow-y: auto; padding: 10px; background-color: #f9f9f9; }
            .nav-header { margin-bottom: 15px; }
            .nav-button { margin-bottom: 5px !important; }
            .nav-sub-button { margin-left: 15px; margin-bottom: 3px !important; }
            .nav-group { margin-bottom: 10px !important; }
            /* Add other global styles or link to modern-ui.css from static/ */
        """,
    ) as demo:
        gr.Markdown("# 🚀 AI Research Assistant - New Interface")

        # Hidden component to trigger page refreshes via event listeners
        # This will hold the page_id to be loaded.
        current_page_id_trigger = gr.Textbox(
            value=navigation_rail.default_page_id, visible=False, label="currentPageID"
        )

        with gr.Row(elem_classes="main-container"):
            with gr.Column(
                elem_id="navigation-rail-column",
                elem_classes="navigation-rail-container",
                scale=0,
                min_width=220,
            ):
                nav_rail_ui_column = (
                    navigation_rail.create_ui()
                )  # This returns the gr.Column for the nav rail

            with gr.Column(
                elem_id="main-content-column",
                elem_classes="main-content-container",
                scale=3,
            ) as main_content_area:
                # Initial page load will be handled by the event listener below
                gr.Markdown(
                    "Welcome! Select an item from the navigation menu."
                )  # Default placeholder

            with gr.Column(
                elem_id="live-output-column",
                elem_classes="live-output-container",
                scale=1,
                min_width=300,
                visible=True,
            ) as live_output_area:
                gr.Markdown("### 📢 Live Output Panel")
                gr.Textbox(
                    "Agent activity and logs will appear here...",
                    lines=20,
                    interactive=False,
                )

        # --- Event Handling for Page Navigation ---
        def load_page_content(page_id_to_load: str):
            logger.info(f"Attempting to load page content for: {page_id_to_load}")
            webui_manager.navigation_state.set_page(
                page_id_to_load
            )  # Ensure state is set

            page_factory = PAGE_REGISTRY.get(page_id_to_load)
            if page_factory:
                # Clear previous content - Gradio does this implicitly when returning new components
                # for a gr.update() target, but here we want to replace the content of 'main_content_area'
                # Returning a new gr.Column or a list of components for the 'main_content_area'
                # should replace its children.
                with (
                    gr.Blocks() as page_block
                ):  # Create a temporary block to build the page
                    page_content_components = page_factory(webui_manager)

                # This is tricky. We can't directly return components to replace children of main_content_area
                # from a handler that isn't directly outputting to it via gr.update(outputs=main_content_area).
                # A common pattern is to have the page factory functions build their UI *within*
                # the main_content_area when it's first defined, and control visibility.
                # Or, use gr.update() with a list of new components.

                # For dynamic loading, let's try returning a new Column with the content.
                # This needs to be tested if it correctly replaces the content of main_content_area.
                # A more robust way might involve JavaScript or more complex Gradio state management.

                # Simpler approach for now: Rebuild the specific page within a new Column.
                # The `outputs` of the `current_page_id_trigger.change` will target `main_content_area`.
                new_page_layout = page_factory(
                    webui_manager
                )  # This should return a gr.Column or list of components
                logger.info(
                    f"Successfully created components for page: {page_id_to_load}"
                )
                return new_page_layout
            else:
                logger.warning(f"No page factory found for page_id: {page_id_to_load}")
                return gr.Markdown(f"## Page Not Found: {page_id_to_load}")

        # When a nav button is clicked, it calls _handle_page_selection, which returns page_id.
        # We need to link that returned page_id to update the current_page_id_trigger.
        # This involves iterating over all buttons created in NavigationRail.
        for page_id_key, nav_button_component in navigation_rail.page_buttons.items():
            nav_button_component.click(
                fn=lambda pid=page_id_key: pid,  # Return the page_id associated with this button
                inputs=[],
                outputs=[current_page_id_trigger],  # Update the hidden trigger textbox
            )

        # When the trigger textbox changes (either by nav click or initial load), load the page content.
        current_page_id_trigger.change(
            fn=load_page_content,
            inputs=[current_page_id_trigger],
            outputs=[
                main_content_area
            ],  # This will replace the content of main_content_area
        )

        # Trigger initial page load after the UI is fully built
        # demo.load(fn=lambda: navigation_rail.initial_page_load_trigger(), inputs=[], outputs=[current_page_id_trigger])
        # A slightly cleaner way for initial load might be to set current_page_id_trigger.value directly
        # or ensure the default page is loaded by the first .change() event.
        # The current setup with current_page_id_trigger initially having default_page_id should trigger it.

    return demo


# To run this (example):
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     ui = create_ui()
#     ui.launch()
