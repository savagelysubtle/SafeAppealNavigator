from typing import Callable, Dict, List, Optional, Union

import gradio as gr


class NavItem:
    """Represents a single navigation item."""

    def __init__(
        self, icon: str, label: str, page_id: str, action: Optional[Callable] = None
    ):
        self.icon = icon
        self.label = label
        self.page_id = page_id
        self.action = action  # Optional direct action


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

    def __init__(self, webui_manager, default_page_id: str = "orchestrator_page"):
        self.webui_manager = webui_manager
        self.nav_structure: List[Union[NavItem, NavGroup]] = []
        self.page_buttons: Dict[str, gr.Button] = {}
        self.page_container: Optional[gr.Column] = None
        self.default_page_id = default_page_id
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
                    # NavItem("🔧", "DB Maintenance", "db_maintenance_page"), # Example if needed
                ],
                initially_expanded=False,
            ),
            NavItem("💬", "Interactive Chat", "interactive_chat_page"),
            NavGroup(
                "System",
                [
                    NavItem("🛠️", "Tools", "tools_page"),
                    NavItem("⚙️", "Settings", "settings_page"),
                    # NavItem("💾", "Config Mgmt", "config_mgmt_page"), # Example
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

    def _create_nav_button(self, nav_item: NavItem, is_sub_item: bool = False):
        """Helper to create a single navigation button."""
        label = f"{nav_item.icon} {nav_item.label}"
        elem_classes = ["nav-button"]
        if is_sub_item:
            elem_classes.append("nav-sub-button")

        button = gr.Button(label, elem_classes=elem_classes)
        button.click(
            fn=lambda page_id=nav_item.page_id: self._handle_page_selection(page_id),
            inputs=[],
            outputs=[],  # Outputs will be handled by the main interface to update page_container
        )
        self.page_buttons[nav_item.page_id] = button
        return button

    def _create_nav_group(self, nav_group: NavGroup):
        """Helper to create a collapsible navigation group."""
        with gr.Accordion(
            nav_group.label, open=nav_group.initially_expanded, elem_classes="nav-group"
        ):
            for item in nav_group.items:
                self._create_nav_button(item, is_sub_item=True)

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
