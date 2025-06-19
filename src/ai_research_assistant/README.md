# AI Research Assistant Backend

This document provides instructions for running the necessary backend services for the AI Research Assistant and its integration with the Void IDE.

## Running Services

To run the full backend, you will need to open multiple terminals and run each service. Ensure your environment variables are set up correctly (refer to `.env.example`).

### 1. Start the Chief Legal Orchestrator

This agent is the primary router and point of contact for the UI backend.

```bash
# From the project root directory
python -m src.ai_research_assistant.a2a_services.startup --agent-name ChiefLegalOrchestrator
```
*Note: The port is determined by the `CHIEF_LEGAL_ORCHESTRATOR_A2A_PORT` environment variable (defaults to 10100).*

### 2. Start the AG-UI Backend Gateway

This service provides the WebSocket endpoint (`/ws/{thread_id}`) for the Void IDE frontend to connect to.

```bash
# From the project root directory
uvicorn src.ai_research_assistant.ag_ui_backend.main:app --host 0.0.0.0 --port 10200 --reload
```

### 3. Start Specialized Agents

The orchestrator will delegate tasks to these agents based on the request. They must be running to handle specific functionalities like document analysis or legal research.

```bash
# Terminal 3: For Document Analysis
python -m src.ai_research_assistant.a2a_services.startup --agent-name DocumentAnalysisAgent

# Terminal 4: For Legal Research
python -m src.ai_research_assistant.a2a_services.startup --agent-name LegalResearchAgent
```

You can start any other specialized agents as needed by following the same pattern.