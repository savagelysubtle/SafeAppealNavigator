# `webui/shared_components/` Module: Guide

This document provides guidelines for using and creating reusable UI components within the `src/ai_research_assistant/webui/shared_components/` directory.

## Purpose

The `shared_components/` directory is dedicated to housing UI elements that are generic enough to be reused across multiple pages or tabs within the WebUI. This promotes consistency, reduces code duplication, and simplifies maintenance.

Examples from the `AllBeAllUIPlan.md` include:
-   `CollapsibleCard.py`
-   `RateLimitSlider.py`
-   `ToolCard.py` (for the MCP Marketplace)

## Using Existing Shared Components

1.  **Identify Need**: Determine if an existing shared component meets your UI requirement.
2.  **Import**: Import the component's class or creation function from its module within `shared_components/` into your page view (`*_view.py`) or content tab (`*_tab.py`) file.
    ```python
    from src.ai_research_assistant.webui.shared_components.collapsible_card import CollapsibleCard
    ```
3.  **Instantiate/Use**: Create an instance of the component, passing any necessary parameters. Shared components might require the `webui_manager` if they need to interact with global state or other registered UI elements.
    ```python
    with CollapsibleCard(title="My Reusable Section", icon="⚙️", webui_manager=webui_manager):
        gr.Markdown("This content is inside a shared collapsible card.")
    ```
4.  **Consult Component Docstrings**: Each shared component file should contain clear docstrings explaining its purpose, parameters, expected behavior, and usage examples. Always refer to these for specific instructions.

## Creating New Shared Components

If you develop a UI pattern or widget that you anticipate will be used in multiple distinct parts of the application and is not logically tied to a single page's specific functionality, it's a good candidate for a shared component.

1.  **Design for Reusability**:
    -   Ensure the component has a clear, well-defined interface (parameters).
    -   Make it configurable to adapt to different contexts where it might be used.
    -   Avoid hardcoding values that should be parameters.

2.  **Create File**: Add a new Python file to the `src/ai_research_assistant/webui/shared_components/` directory (e.g., `my_new_widget.py`).

3.  **Implement Component Logic**:
    -   Typically, define the component as a Python class that inherits from a base Gradio component (e.g., `gr.Group`, `gr.Column`, `gr.HTML`) or as a function that creates and returns a configured set of Gradio components.
    -   If the component needs access to global UI state or needs to trigger actions on other parts of the UI, accept an instance of `WebuiManager` as a parameter in its constructor or creation function.

4.  **Write Comprehensive Docstrings**:
    -   Clearly explain what the component does.
    -   List all parameters, their types, and their purpose.
    -   Provide simple usage examples.
    -   Mention any dependencies or important considerations.

5.  **Consider Abstraction**: If the component involves complex logic or multiple sub-elements, ensure it presents a clean and simple API to the modules that will use it.

6.  **Update Documentation (If Necessary)**:
    -   If the new shared component represents a significant or widely applicable UI pattern, consider mentioning it in the main `README_WEBUI_OVERVIEW.md` or the `AllBeAllUIPlan.md`.
    -   Ensure the `webui-development-context.mdc` rule is updated if the component becomes a standard part of the architecture.

## Theming and Layout

-   Shared components should generally adhere to the global theme (see `README_WEBUI_THEME.md`) and CSS (`static/modern-ui.css`).
-   They can accept parameters to allow for minor layout or style variations where needed, but overarching look-and-feel should be consistent with the rest of the application.

By centralizing reusable UI elements in `shared_components/`, we can build a more modular, consistent, and maintainable WebUI.