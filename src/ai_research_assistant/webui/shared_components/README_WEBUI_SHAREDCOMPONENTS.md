# `webui/shared_components/` Module: Guide

This document explains the `shared_components/` subdirectory within the `src/ai_research_assistant/webui/` module. It details the purpose of shared UI components and how to use existing ones or contribute new ones.

## Purpose

The `shared_components/` directory houses reusable Gradio UI components that can be utilized across multiple pages or tabs within the AI Research Assistant web interface. The goal is to promote consistency, reduce code duplication, and simplify the development of new UI sections.

These components are designed to align with the overall UI refactor plan (`plans/WUI/AllBeAllUIPlan.md`) and adhere to the defined design system and architectural patterns.

## Available Components

Below is a list of available shared components, their purpose, and basic usage examples.

### 1. `CollapsibleCard`

-   **File**: `collapsible_card.py`
-   **Purpose**: Provides a card-like container with a clickable header that expands or collapses to show/hide its content. Useful for organizing complex forms or sections with optional details.
-   **Key Features**:
    -   Customizable title and icon.
    -   Option to be open or closed by default.
    -   Integrates with Gradio's layout system.
-   **Basic Usage**:
    ```python
    from src.ai_research_assistant.webui.shared_components import CollapsibleCard

    with CollapsibleCard(title="My Section", icon="⚙️", open_by_default=True):
        gr.Markdown("Content inside the collapsible card.")
        gr.Textbox(label="My Setting")
    ```

### 2. `RateLimitSlider`

-   **File**: `rate_limit_slider.py`
-   **Purpose**: An enhanced slider for configuring requests per minute (RPM) for API providers. It includes a visual display for the current RPM and a placeholder for a timer/status.
-   **Key Features**:
    -   Customizable provider name, default RPM, min/max RPM.
    -   Displays current RPM and intended seconds per request.
    -   Includes a status label (e.g., "Ready", "Limited").
    -   Designed to integrate with `WebuiManager` for real-time status updates (requires `gr.every` polling in the main UI for live timer).
-   **Basic Usage**:
    ```python
    from src.ai_research_assistant.webui.shared_components import RateLimitSlider

    # webui_manager would typically be passed if available in the context
    RateLimitSlider(provider_name="My API Provider", default_rpm=30)
    ```

### 3. `ToolCard`

-   **File**: `tool_card.py`
-   **Purpose**: Displays information about an individual tool (e.g., from an MCP Tool Marketplace) and provides action buttons like Install, Configure, Run, or Uninstall.
-   **Key Features**:
    -   Displays tool name, icon, description, version, author, and tags from metadata.
    -   Shows a status badge (e.g., "Installed", "Not Installed").
    -   Conditionally shows action buttons based on tool status.
-   **Basic Usage**:
    ```python
    from src.ai_research_assistant.webui.shared_components import ToolCard

    tool_meta = {
        "name": "My Awesome Tool", "icon": "🚀",
        "description": "This tool does awesome things.",
        "version": "1.0", "status": "not_installed", "author": "Dev Team"
    }
    ToolCard(tool_metadata=tool_meta)
    ```

## How to Use Shared Components

1.  **Import**: Import the desired component from `src.ai_research_assistant.webui.shared_components` into your page or tab module.
2.  **Instantiate**: Create an instance of the component, passing any required arguments (like `title` for `CollapsibleCard` or `tool_metadata` for `ToolCard`).
3.  **Integrate**: Place the component within your Gradio layout (e.g., inside `gr.Column`, `gr.Row`, `gr.TabItem`).
4.  **Event Handling**: If the component has interactive elements (like buttons in `ToolCard`), connect their event handlers (`.click()`, `.change()`, etc.) to your controller logic or `WebuiManager` methods as needed.

## Contributing New Shared Components

1.  **Identify Need**: Determine if a UI element or pattern is likely to be reused in multiple places.
2.  **Design**: Follow the design tokens and patterns in `AllBeAllUIPlan.md` and related UI architecture rules.
3.  **Implement**: Create a new Python file in the `shared_components/` directory for your component. It should typically inherit from a Gradio class (e.g., `gr.Group`, `gr.Column`).
4.  **Document**: Add your new component to this README, explaining its purpose, features, and providing a basic usage example.
5.  **Export**: Add your component to `src/ai_research_assistant/webui/shared_components/__init__.py` to make it easily importable.
6.  **Test**: Create a simple `if __name__ == "__main__":` block in your component's file for standalone testing with `gr.Blocks().launch()`.

## Styling

-   Shared components should aim for a consistent look and feel by using design tokens and global CSS variables defined in `static/modern-ui.css`.
-   Use `elem_id` and `elem_classes` parameters in Gradio components for applying custom styles when necessary.

For the overall WebUI structure, refer to `README_WEBUI_OVERVIEW.md`.
For details on page creation, refer to `pages/README_WEBUI_PAGES.md`.