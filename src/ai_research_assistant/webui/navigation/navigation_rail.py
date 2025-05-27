from typing import Dict, List, Optional, Union

import gradio as gr


class NavItem:
    """Represents a single navigation item."""

    def __init__(
        self,
        icon: str,
        label: str,
        value: str,
        is_group: bool = False,
        children: Optional[List["NavItem"]] = None,
    ):
        self.icon = icon
        self.label = label
        self.value = value  # Corresponds to the page/tab to show or a group identifier
        self.is_group = is_group
        self.children: List["NavItem"] = children if children else []


class NavGroup:
    """Represents a group of navigation items."""

    def __init__(
        self, label: str, items: List[NavItem], initially_expanded: bool = True
    ):
        self.label = label
        self.items = items
        self.initially_expanded = initially_expanded


class NavigationRail:
    """
    Creates a vertical navigation rail with icons, labels, and collapsible groups.
    Manages page switching logic.
    """

    def __init__(self, webui_manager):
        self.webui_manager = webui_manager  # To call back for page changes
        self.nav_items: List[NavItem] = [
            NavItem(icon="🎯", label="Orchestrator", value="orchestrator_page"),
            NavItem(
                icon="👥",
                label="Agents",
                value="agents_group",
                is_group=True,
                children=[
                    NavItem(icon="📥", label="Intake", value="intake_agent_page"),
                    NavItem(icon="🔍", label="Search", value="search_agent_page"),
                    NavItem(
                        icon="🔗",
                        label="Cross-Reference",
                        value="cross_reference_agent_page",
                    ),
                    NavItem(
                        icon="🛠️",
                        label="DB Maintenance",
                        value="db_maintenance_agent_page",
                    ),
                    NavItem(
                        icon="⚖️",
                        label="Legal Research",
                        value="legal_research_agent_page",
                    ),
                    NavItem(
                        icon="🔬",
                        label="Deep Research",
                        value="deep_research_agent_page",
                    ),
                    NavItem(icon="🌐", label="Browser", value="browser_agent_page"),
                    NavItem(icon="📚", label="Collector", value="collector_agent_page"),
                ],
            ),
            NavItem(
                icon="⚙️",
                label="Tools & Settings",
                value="tools_settings_group",
                is_group=True,
                children=[
                    NavItem(
                        icon="🔧", label="MCP Marketplace", value="mcp_marketplace_page"
                    ),
                    NavItem(
                        icon="⚙️", label="Global Settings", value="global_settings_page"
                    ),
                    NavItem(
                        icon="💾",
                        label="Config Load/Save",
                        value="load_save_config_page",
                    ),
                    NavItem(
                        icon="🤖", label="Agent Settings", value="agent_settings_page"
                    ),
                ],
            ),
            NavItem(icon="💬", label="Chat", value="chat_page"),
        ]
        self.selected_value = gr.State(
            self.nav_items[0].value if self.nav_items else None
        )
        self.nav_structure: List[Union[NavItem, NavGroup]] = []
        self.page_buttons: Dict[str, gr.Button] = {}
        self.page_container: Optional[gr.Column] = None
        self.default_page_id = "orchestrator_page"
        self._define_nav_structure()
        self.nav_column_ui: Optional[gr.Column] = None

    def _define_nav_structure(self):
        """Defines the items and groups in the navigation rail."""
        self.nav_structure = [
            NavItem("🎯", "Orchestrator", "orchestrator_page"),
            NavGroup(
                "General Agents",
                [
                    NavItem("🌐", "Browser Agent", "browser_agent_page"),
                    NavItem("🔍", "Deep Research", "deep_research_page"),
                    NavItem("🔎", "Search Agent", "search_agent_page"),
                ],
                initially_expanded=False,
            ),
            NavGroup(
                "Workflow Agents",
                [
                    NavItem("📥", "Intake Agent", "intake_agent_page"),
                    NavItem("⚖️", "Legal Research", "legal_research_page"),
                    NavItem("📊", "Collector Agent", "collector_agent_page"),
                    NavItem("🔗", "Cross Reference", "cross_reference_page"),
                ],
                initially_expanded=False,
            ),
            NavItem("💬", "Interactive Chat", "interactive_chat_page"),
            NavGroup(
                "System",
                [
                    NavItem("🛠️", "Tools", "tools_page"),
                    NavItem("⚙️", "Settings", "settings_page"),
                ],
                initially_expanded=False,
            ),
        ]

    def create_ui(self) -> gr.Column:
        """Builds the Gradio UI for the navigation rail."""
        with gr.Column(
            scale=1, min_width=200, elem_classes="navigation-rail"
        ) as nav_column:
            gr.Markdown("### 🧭 Navigation", elem_classes="nav-header")

            for item_or_group in self.nav_structure:
                if isinstance(item_or_group, NavItem):
                    self._create_nav_button(item_or_group)
                elif isinstance(item_or_group, NavGroup):
                    self._create_nav_group(item_or_group)

        self.nav_column_ui = nav_column
        return self.nav_column_ui

    def _create_nav_button(self, nav_item: NavItem):
        """Helper to create a single navigation button."""
        button = gr.Button(
            value=f"{nav_item.icon} {nav_item.label}",
            elem_id=f"nav-btn-{nav_item.value}",
        )
        button.click(
            fn=self.webui_manager.set_current_page,
            inputs=[gr.Textbox(value=nav_item.value, visible=False)],
            outputs=[],  # Output will be the main content area, handled by WebuiManager
        )
        self.page_buttons[nav_item.value] = button
        return button

    def _create_nav_group(self, nav_group: NavGroup):
        """Helper to create a collapsible navigation group."""
        with gr.Accordion(
            nav_group.label, open=nav_group.initially_expanded, elem_classes="nav-group"
        ):
            for item in nav_group.items:
                self._create_nav_button(item)

    def _handle_page_selection(self, page_id: str):
        """Handles the logic when a navigation button is clicked."""
        self.webui_manager.navigation_state.set_page(page_id)

        # Here, we would typically trigger an update in the main interface.py
        # to load the new page content into self.page_container.
        # This function itself doesn't return Gradio updates directly,
        # but sets state that the main UI will react to.
        print(
            f"NavigationRail: Page selected - {page_id}. Main interface should update."
        )

        # We need a way to signal the main interface to re-render the content area.
        # This could be done via a hidden gr.Textbox that changes value,
        # and the main content area has an event listener on that textbox.
        # Or, the main interface's page loading function is passed in and called.

        # For now, we'll just update the state. The main UI will need to query this.
        # The actual page loading will be handled in interface.py
        return page_id  # Returning page_id might be useful for chaining events in interface.py

    def highlight_active_button(self, active_page_id: Optional[str]):
        """Visually highlights the active navigation button. (Placeholder)"""
        # This would involve JS or more complex Gradio updates to change button styles.
        # For simplicity, we'll skip direct visual updates here and rely on page content change.
        # In a more advanced setup, you'd use gr.update to change button appearance.
        print(f"Attempting to highlight: {active_page_id}")
        for page_id, button in self.page_buttons.items():
            if page_id == active_page_id:
                # Example: button.update(elem_classes=["nav-button", "active"]) - Gradio might not support class changes easily this way.
                # A common workaround is to have two versions of a button or use CSS with a state variable.
                pass
            else:
                # button.update(elem_classes=["nav-button"])
                pass

    def link_page_container(self, page_container: gr.Column):
        """Links the main content display area for page loading."""
        self.page_container = page_container

    def initial_page_load_trigger(self):
        """Triggers the display of the default page."""
        # This is a bit of a hack to ensure the default page content is loaded.
        # The main interface will listen to this hidden component.
        return self.default_page_id

    def render(self) -> gr.Column:
        """Renders the navigation rail using Gradio components."""
        with gr.Column(
            elem_id="navigation-rail", scale=1, min_width=200
        ) as rail_column:
            # Potentially a logo or title can go here
            gr.Markdown("### NAVIGATION", elem_id="nav-header")

            for item in self.nav_items:
                if item.is_group:
                    with gr.Accordion(
                        label=f"{item.icon} {item.label}",
                        open=False,
                        elem_id=f"nav-group-{item.value}",
                    ):
                        for child_item in item.children:
                            self._create_nav_button(child_item)
                else:
                    self._create_nav_button(item)
        return rail_column

    # def handle_nav_click(self, nav_value: str):
    #     """Handles the navigation item click and updates the selected state."""
    #     # This function will be called by WebUI manager to update the main content area
    #     # For now, just update the state which can be observed.
    #     return nav_value


# Example usage (conceptual, will be integrated into the main WebUI):
# if __name__ == "__main__":
#     nav_rail = NavigationRail()
#     with gr.Blocks(theme=ModernDarkTheme()) as demo:
#         with gr.Row():
#             selected_page_value = nav_rail.render()
#             with gr.Column(scale=4):
#                 gr.Markdown("## Main Content Area")
#                 gr.Textbox(label="Selected Page", value=selected_page_value)
#
#                 # Example of how to show/hide content based on selected_page_value
#                 # This logic will be in the main UI manager
#                 for item in nav_rail.nav_items:
#                     if not item.is_group:
#                         with gr.Box(visible=(selected_page_value == item.value)):
#                             gr.Markdown(f"### Content for {item.label}")
#                     else:
#                         for child in item.children:
#                             with gr.Box(visible=(selected_page_value == child.value)):
#                                 gr.Markdown(f"### Content for {child.label}")
#     demo.launch()
