Refer to the `[webui-development-context.mdc](cursor://rules/webui-development-context)` rule for the detailed target directory structure. Key top-level directories and their primary sub-modules include:

-   `interface.py`: The main entry point that assembles the entire UI.
-   `webui_manager.py`: Handles global state, component registration, and event coordination.
-   `navigation/`: Contains components related to the primary UI navigation (e.g., `navigation_rail.py`).
-   `pages/`: Contains modules for distinct application pages and their content. This is the main area for feature UIs.
    -   `pages/orchestrator/`: For the main orchestrator workflow UI and its integrated agent UIs.
    -   `pages/general/`: For standalone agent UIs (like Browser, Deep Research, Search) and other general purpose pages.
        -   `pages/general/agents/`: Specific tab modules for each general agent.
    -   `pages/tools/`: For UIs related to tools and utilities (e.g., MCP Server, Browser Launch).
    -   `pages/settings/`: For application and agent settings UIs.
    -   `pages/chat/`: For the interactive chat interface.
    -   See `[README_WEBUI_PAGES.md](mdc:src/ai_research_assistant/webui/README_WEBUI_PAGES.md)` for detailed guidance on the `pages/` subdirectory.
-   `shared_components/`: Houses reusable Gradio components used across multiple pages or tabs.
-   `theme/`: Defines custom Gradio themes (e.g., `modern_dark.py`).
-   `static/`: Stores static assets like custom CSS and JavaScript files.

## Working with Shared Components (`shared_components/`)