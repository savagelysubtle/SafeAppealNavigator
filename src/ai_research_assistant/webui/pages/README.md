# `webui/pages/` Module: Structure and Development Guide

This document outlines the structure and conventions for adding new pages and their content specifically within the `src/ai_research_assistant/webui/pages/` directory. It is intended for developers and LLM agents working on the AI Research Assistant UI, detailing how to create new page categories (like `agents/`, `orchestrator/`) and populate them with views and content tabs.

## Core Concept: Page Categories and Content Views

The `pages/` directory organizes the UI into distinct sections or "pages," each corresponding to a major functional area of the application (e.g., Orchestrator, Agents, Tools, Settings).

1.  **Page Categories**: Each subdirectory within `pages/` (e.g., `agents/`, `orchestrator/`, `tools/`, `settings/`) represents a top-level page category.
2.  **Page Entry Point (`*_view.py`)**: Inside each category directory, there is a main Python file named `<category_name>_view.py` (e.g., `agents_view.py`, `orchestrator_view.py`). This file is responsible for:
    *   Defining the overall layout for that page category.
    *   Importing and arranging the actual content/tab modules from its corresponding subdirectories.
3.  **Content/Tab Modules (`*Tabs/` or `*Agents/` subfolders)**: Within each page category directory, further subdirectories (conventionally named `*Tabs` like `agentTabs/`, `settingTabs/` or more descriptive names like `dbAgents/`, `researchAgents/`) house the individual Gradio components or modules that make up the content of that page. These are typically `*_tab.py` files.

**Example Flow**: The main `interface.py` (via `NavigationRail`) loads `pages/agents/agents_view.py`. Then, `agents_view.py` might load and display several tabs whose UI is defined in files within `pages/agents/agentTabs/` (e.g., `browser_agent_tab.py`).

## Adding a New Page or Feature

Follow these steps to add a new page category or a new tab/feature within an existing page:

1.  **Identify/Create Category**: Determine the appropriate page category (e.g., `agents`, `tools`).
    *   If the category doesn't exist, create a new folder: `pages/<new_category_name>/`.
    *   Add an `__init__.py` to this new folder.
    *   Create the page entry point file: `pages/<new_category_name>/<new_category_name>_view.py`.
        *   This `_view.py` file will define a function, typically `create_<new_category_name>_view(webui_manager)`, which sets up the Gradio Blocks layout for this page and calls functions from its content modules.

2.  **Create Content Subdirectory**: Inside your category folder (`pages/<category_name>/`), create a subdirectory to hold the content modules (e.g., `myNewFeatureTabs/`). Add an `__init__.py` to it.

3.  **Develop Content Modules (`*_tab.py`)**: Inside this new subdirectory, create your Python files (e.g., `my_feature_one_tab.py`, `my_feature_two_tab.py`).
    *   Each file should define a function, typically `create_<feature_name>_tab(webui_manager)`, that returns the Gradio components for that specific tab or section.

4.  **Integrate into Page View**: In your `<category_name>_view.py` file, import the `create_*_tab` functions from your content modules and arrange them within the page's Gradio layout (e.g., using `gr.Tabs()`).

5.  **Update Navigation**: Add your new page to `src/ai_research_assistant/webui/navigation/navigation_rail.py` so it appears in the sidebar.

6.  **Update Main Interface**: Ensure `src/ai_research_assistant/webui/interface.py` correctly calls the `create_<new_category_name>_view` function to display your new page.

## Specific Guidelines for Agent UIs

The structure helps differentiate between UIs for standalone agents and agents that are part of the orchestrator workflow:

*   **Standalone/One-Off Agent UIs (`pages/agents/`)**: The `pages/agents/` directory is intended for UIs of agents that can be used independently, not necessarily as part of a larger, predefined orchestration.
    *   The `pages/agents/agents_view.py` will be the main entry point for this "General Agents" page.
    *   Individual agent UIs (e.g., for a specific browser agent, deep research agent if run standalone) will have their tab/content modules in `pages/agents/agentTabs/`.

*   **Orchestrated Agent UIs (`pages/orchestrator/`)**: The `pages/orchestrator/orchestrator_view.py` defines the main interface for the primary Legal Research Orchestrator.
    *   Agents that are primarily components *called by* or *integral to* this orchestrator will have their UI tabs/modules within subdirectories of `pages/orchestrator/`. For example:
        *   `pages/orchestrator/dbAgents/`: For UIs of agents dealing with database interactions managed by the orchestrator (e.g., Collector, Cross-Reference, DB Maintenance, Intake when part of the orchestrated flow).
        *   `pages/orchestrator/researchAgents/`: For UIs of agents performing research tasks as directed by the orchestrator (e.g., Legal Research tab).
    *   The `orchestrator_view.py` will then load and present these specific agent UIs as part of its own interface, often as tabs within the orchestrator page.

## Key Principles

-   **Modularity**: Keep page views (`*_view.py`) as orchestrators of content, and actual UI logic within the `*Tabs/` or `*Agents/` modules.
-   **Clarity**: The folder structure should make it clear where to find the UI code for any given section of the application.
-   **Consistency**: Follow the naming conventions (`*_view.py`, `*_tab.py`, `*Tabs/`).

Refer to the main `webui-development-context.mdc` rule for the complete target directory structure and other WebUI development guidelines.