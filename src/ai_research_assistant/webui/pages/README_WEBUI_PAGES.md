## Specific Guidelines for Agent UIs

The structure helps differentiate between UIs for standalone agents and agents that are part of the orchestrator workflow:

*   **Standalone/General Agent UIs (`pages/general/agents/`)**: The `pages/general/` directory, specifically its `agents/` subdirectory, is intended for UIs of agents that can be used independently, not necessarily as part of a larger, predefined orchestration. Examples include the Browser Agent, Deep Research Agent, and Search Agent.
    *   The `pages/general/general_view.py` will be the main entry point for this "General Agents" page/section.
    *   Individual agent UIs (e.g., `browser_agent_tab.py`, `deep_research_tab.py`) will have their tab/content modules in `pages/general/agents/`.

*   **Orchestrated Agent UIs (`pages/orchestrator/`)**: The `pages/orchestrator/orchestrator_view.py` defines the main interface for the primary Orchestrator.