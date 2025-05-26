# Top-Level `webui/` Module: Development Guide

This document provides an overview and general development guidelines for the entire `src/ai_research_assistant/webui/` module of the AI Research Assistant. It serves as the main entry point for understanding the WebUI's architecture and how its various sub-modules (`pages/`, `navigation/`, `theme/`, `static/`, `shared_components/`) interact.

For detailed guidance on specific sub-modules, please refer to their respective `README.md` files (e.g., `pages/README.md`).

## Module Overview

The `webui` module is responsible for the Gradio-based web user interface. It's currently undergoing a significant refactor to improve modularity, user experience, and maintainability, guided by the `[AllBeAllUIPlan.md](mdc:plans/WUI/AllBeAllUIPlan.md)`.

## Core Structure

Refer to the `[webui-development-context.mdc](cursor://rules/webui-development-context)` rule for the detailed target directory structure. Key top-level directories include:

-   `interface.py`: The main entry point that assembles the entire UI.
-   `webui_manager.py`: Handles global state, component registration, and event coordination. (To be enhanced as `EnhancedWebuiManager`).
-   `navigation/`: Contains components related to the primary UI navigation, like the `navigation_rail.py`.
-   `pages/`: Contains modules for distinct application pages and their content. See `[pages/README.md](mdc:src/ai_research_assistant/webui/pages/README.md)` for detailed guidance on this subdirectory.
-   `shared_components/`: Houses reusable Gradio components used across multiple pages or tabs.
-   `theme/`: Defines custom Gradio themes (e.g., `modern_dark.py`).
-   `static/`: Stores static assets like custom CSS and JavaScript files.

## Working with Shared Components (`shared_components/`)

This directory is for UI elements that are generic enough to be used in multiple parts of the application. Examples include `CollapsibleCard.py` or `RateLimitSlider.py` as outlined in the `AllBeAllUIPlan.md`.

### Using Existing Shared Components

1.  **Import**: Import the necessary class or creation function from the component's module in `shared_components/` into your page view or tab module.
    ```python
    from src.ai_research_assistant.webui.shared_components.collapsible_card import CollapsibleCard
    ```
2.  **Instantiate/Use**: Create an instance of the component, passing any required parameters (like `webui_manager` if it needs access to global state or other components).
    ```python
    with CollapsibleCard(title="My Section", icon="⚙️", webui_manager=webui_manager):
        gr.Markdown("Content of the collapsible section...")
    ```
3.  **Refer to Component Documentation**: Each shared component should ideally have clear docstrings explaining its purpose, parameters, and usage examples.

### Creating New Shared Components

If you identify a UI pattern or widget that will be used in more than one place and is not tied to a specific page's logic, consider making it a shared component:

1.  **Design**: Ensure the component is genuinely reusable. It should have a clear interface and configurable parameters.
2.  **Create File**: Add a new Python file in `src/ai_research_assistant/webui/shared_components/` (e.g., `my_reusable_widget.py`).
3.  **Implement**: Define your component, usually as a class inheriting from a Gradio component (like `gr.Group`, `gr.Column`) or a function that creates and returns a set of configured Gradio components.
    *   Pass `webui_manager` to its constructor or creation function if it needs to interact with global state or other registered components.
4.  **Docstrings**: Write clear docstrings explaining how to use your new component, its parameters, and any dependencies.
5.  **Update Context**: If the component represents a significant, reusable pattern, consider mentioning it in the `webui-development-context.mdc` rule or the `AllBeAllUIPlan.md`.

## Key Development Principles

-   **Follow the Master Plan**: The `[AllBeAllUIPlan.md](mdc:plans/WUI/AllBeAllUIPlan.md)` is the primary guide for the UI refactor. Adhere to its design tokens, component patterns, and architectural decisions.
-   **Modularity**: Strive for small, focused modules. Page views orchestrate, tabs/content modules provide specific UI sections, and shared components offer reusability.
-   **State Management**: Utilize the `WebuiManager` for any state that needs to be shared across components or persisted.
-   **Naming Conventions**: Adhere to the established naming conventions (e.g., `*_view.py` for page entry points, `*_tab.py` for content modules, `create_*` prefixes for UI creation functions).
-   **Rules and Context**: Always consult the `[webui-development-context.mdc](cursor://rules/webui-development-context)` and `[ui-refactor-architecture](cursor://rules/ui-refactor-architecture)` rules for architectural guidance and the target file structure.

By following these guidelines, we can build a more robust, maintainable, and user-friendly interface for the AI Research Assistant.