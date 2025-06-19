# AI Research Assistant IDE Integration Guide

This document provides a comprehensive guide for developers working on the integration between the `void-ide` frontend and the `ai_research_assistant` backend.

## 1. Architecture Overview

The integrated application follows a client-server architecture:

-   **Frontend (`void-ide`)**: A fork of VSCode that serves as the user interface. It has been modified to include a custom provider (`AIResearchAssistantProvider`) that communicates with our backend instead of directly with LLM providers.
-   **UI Gateway (`ag_ui_backend`)**: A Python WebSocket server (using FastAPI and Uvicorn) that acts as the single entry point for the frontend. It receives messages from the Void IDE, translates them into agent tasks, and forwards them to the appropriate backend agent. Its URL is `ws://localhost:10200/ag_ui/ws/{thread_id}`.
-   **Agent Services (`a2a_services`)**: A collection of backend Python services representing different AI agents (e.g., `ChiefLegalOrchestrator`). These agents perform the core logic, such as running research tasks, modifying files, and generating code. They communicate with each other and the UI Gateway.

The data flows from the IDE, through the gateway, to the agents, and back. The communication is based on a structured JSON protocol with custom `Part` types for streaming different kinds of content (text, diffs, notifications, etc.).

## 2. API Contract

*(Note: This section should contain the finalized API contract from Phase 1, detailing all custom `Part` types and structured requests. Please refer to the Phase 1 documentation for the complete specification.)*

### Example Request (from IDE to Gateway)

An inline edit action is transformed into a message like this:
```json
{
  "type": "inline_edit",
  "uri": "file:///path/to/your/file.py",
  "selection": "the code to be replaced",
  "prompt": "your instruction for the edit"
}
```

This is then wrapped in a `RunAgentInput` message for the WebSocket.

### Example Response Event (from Gateway to IDE)

A code diff is sent as a `Part` within the WebSocket stream:
```json
{
  "type": "application/vnd.code-diff.v1+json",
  "content": {
    "uri": "file:///path/to/your/file.py",
    "diff": "<<<<<<< ORIGINAL\n...code...\n=======\n...new code...\n>>>>>>> UPDATED"
  }
}
```

## 3. Development Setup

To set up the development environment, follow these steps:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/savagelysubtle/AiResearchAgent.git
    cd AiResearchAgent
    ```

2.  **Install Python Dependencies**: It is recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    uv pip install -r requirements.txt # Or based on pyproject.toml
    ```

3.  **Install Node.js Dependencies**: Install dependencies for the root and the `void-ide` submodule.
    ```bash
    npm install
    cd void-ide
    npm install
    cd ..
    ```
4.  **Clone the Build Tool**: The `void-builder` is required for production builds. Clone it into the project root.
    ```bash
    git clone https://github.com/voideditor/void-builder.git
    ```

5.  **Run the Unified Development Server**:
    ```bash
    npm run dev
    ```
    This single command will start the backend Python services and the frontend `void-ide` in watch mode.

## 4. How to Add a New Integrated Feature

Adding a new feature that spans the frontend and backend follows this general workflow:

1.  **Define the `Part` (Backend)**: In the `ai_research_assistant` backend, define a new Pydantic model for the `Part` type if you are introducing a new data structure. For example, if you want to display a custom chart, you might create a `Part` of type `application/vnd.custom-chart.v1+json`.

2.  **Implement Backend Logic (Backend)**: Create or modify an agent service in `a2a_services` to generate this new `Part` type as part of its output stream in response to a specific user request.

3.  **Handle the `Part` (Frontend)**: In `void-ide/src/vs/workbench/contrib/void/common/providers/aiResearchAssistantProvider.ts`, extend the `onmessage` event listener's `switch` statement to handle your new `type`.

4.  **Integrate with Void Services (Frontend)**: Within your new `case` block, use dependency injection (`@I...Service`) to get the necessary Void/VSCode services. For example, to render a custom view, you might need to interact with the panel or view services.

5.  **Trigger the Action (Frontend)**: Create a new UI element (e.g., a button, a command palette action) in the `void-ide` that, when triggered, sends the corresponding structured message to the backend via the WebSocket, initiating the entire flow.