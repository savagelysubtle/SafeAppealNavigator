# AI Research Assistant Backend

This document provides a comprehensive guide to understanding, setting up, and running the backend services for the AI Research Assistant. This system is a sophisticated multi-agent framework designed to assist with complex research tasks, particularly in the legal domain.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Running the Application](#running-the-application)
  - [1. Start the Orchestrator Agent](#1-start-the-orchestrator-agent)
  - [2. Start the AG-UI Backend Gateway](#2-start-the-ag-ui-backend-gateway)
  - [3. Start Specialized Agents](#3-start-specialized-agents)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

The AI Research Assistant is a multi-agent system that leverages several specialized AI agents to automate and assist with research workflows. It is orchestrated by a central agent that delegates tasks to other agents based on their capabilities, such as document analysis, web research, and data querying.

The system is designed to be extensible, allowing for the addition of new agents and tools. It exposes its functionality through an A2A (Agent-to-Agent) communication protocol and includes a backend gateway to connect with user interfaces.

## System Architecture

The backend is composed of several key components that work together:

1.  **Orchestrator Agent**: This is the "brain" of the system (`ChiefLegalOrchestrator`). It receives high-level tasks, breaks them down, and delegates sub-tasks to the appropriate specialized agents.
2.  **Specialized Agents**: These are worker agents with specific skills:
    *   `DocumentProcessingCoordinator`: Handles ingestion, analysis, and summarization of documents.
    *   `LegalResearchCoordinator`: Performs web searches and interacts with legal research APIs.
    *   `DataQueryCoordinator`: Executes queries against structured databases (SQL, Vector DBs).
3.  **A2A (Agent-to-Agent) Communication Layer**: Built using `fasta2a`, this layer wraps each agent in a FastAPI service, allowing them to communicate with each other via API calls. All related code is in the `src/ai_research_assistant/a2a_services` directory.
4.  **AG-UI Backend Gateway**: A separate FastAPI application that provides a WebSocket endpoint for a frontend (e.g., a Void IDE extension) to connect to. It acts as the primary entry point for user requests and streams responses back to the UI.
5.  **MCP (Multi-Agent Control Plane) Integration**: The system is designed to integrate with MCP for dynamic tool discovery and management.

## Getting Started

Follow these steps to get the backend running on your local machine.

### Prerequisites

-   Python 3.9+
-   `uv` (e.g., `pipx install uv`)
-   Access to LLM APIs (e.g., OpenAI, Google Gemini, Anthropic)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd AiResearchAgent
    ```

2.  **Install dependencies:**
    This project uses `uv` for package management. Install all required dependencies from `pyproject.toml`.
    ```bash
    uv pip install -e .
    ```
    Or, if you have different dependency groups:
    ```bash
    uv sync --all-groups
    ```

### Configuration

The application uses environment variables for configuration. You'll need to create a `.env` file in the project root.

1.  **Create a `.env` file:**
    You can copy an existing `.env.example` if it exists, or create a new file named `.env`.

2.  **Set required environment variables:**
    Add the following variables to your `.env` file, providing your own keys and desired settings. Refer to `src/ai_research_assistant/config/global_settings.py` for a complete list of configurable variables.

    ```dotenv
    # LLM API Keys
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="..."
    ANTHROPIC_API_KEY="..."

    # Ports for A2A Services (defaults are shown)
    CHIEF_LEGAL_ORCHESTRATOR_A2A_PORT=10100
    DOCUMENT_PROCESSING_COORDINATOR_A2A_PORT=10101
    LEGAL_RESEARCH_COORDINATOR_A2A_PORT=10102
    DATA_QUERY_COORDINATOR_A2A_PORT=10103

    # Port for the AG-UI Backend
    AG_UI_BACKEND_PORT=10200
    ```

## Running the Application

To run the full backend, you will need to open multiple terminals and launch each service. Ensure you are at the project root directory and have your virtual environment activated.

### 1. Start the Orchestrator Agent

This agent is the primary router and must be running to handle any requests from the UI.

```bash
python -m src.ai_research_assistant.a2a_services.startup --agent-name ChiefLegalOrchestrator
```
*This service will run on the port defined by `CHIEF_LEGAL_ORCHESTRATOR_A2A_PORT` (defaults to 10100).*

### 2. Start the AG-UI Backend Gateway

This service provides the WebSocket endpoint (`/ws/{thread_id}`) for the UI frontend to connect to.

```bash
uvicorn src.ai_research_assistant.ag_ui_backend.main:app --host 0.0.0.0 --port 10200 --reload
```
*This service will run on the port defined by `AG_UI_BACKEND_PORT` (defaults to 10200).*

### 3. Start Specialized Agents

The orchestrator delegates tasks to these agents. They must be running to handle specific functionalities. Start each one in a separate terminal.

**Available Agents:**
- `DocumentProcessingCoordinator`
- `LegalResearchCoordinator`
- `DataQueryCoordinator`

**Example Commands:**

```bash
# Terminal 3: For Document Processing
python -m src.ai_research_assistant.a2a_services.startup --agent-name DocumentProcessingCoordinator
```

```bash
# Terminal 4: For Legal Research
python -m src.ai_research_assistant.a2a_services.startup --agent-name LegalResearchCoordinator
```

You can start any other specialized agents as needed by following the same pattern with the correct agent name.

## Project Structure

The `src/ai_research_assistant` directory contains the core logic, organized as follows:

| Directory | Description |
|---|---|
| `agents/` | Contains the core logic for all agents, including the orchestrator and specialized agents. |
| `a2a_services/` | Implements the Agent-to-Agent (A2A) communication layer, wrapping agents as FastAPI services. The `startup.py` script lives here. |
| `ag_ui_backend/`| The FastAPI backend that provides the WebSocket gateway for the frontend UI. |
| `browser/` | Code for browser automation and interaction. |
| `config/` | Contains application configuration, including `global_settings.py` for environment-based settings and `mcp_config/` for JSON-based MCP configurations. |
| `core/` | Foundational components, core business logic, and utilities shared across the application. |
| `mcp_intergration/`| Code related to MCP (Multi-Agent Control Plane) integration, including shared tools. |

## Contributing

We welcome contributions! Please follow standard practices for this project:
-   Write clean, readable code with type hints.
-   Format code using `ruff`.
-   Write tests for new features.
-   Open a pull request with a clear description of your changes.

## License

This project is licensed under the terms of the LICENSE file.