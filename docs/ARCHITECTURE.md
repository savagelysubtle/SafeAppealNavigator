# System Architecture (Refactor v2)

![architecture_diagram](assets/architecture_overview_refactor_v2.mermaid)

## Layers

1.  **UI** – Gradio ↔ AG-UI backend (FastAPI).
2.  **CEO Agent** – Vorder-facing chatbot, no heavy lifting.
3.  **Orchestrator Agent** – Runs TaskGraph, publishes A2A `/ask|/tell|/stream`.
4.  **Specialized Manager Layer**
    *   Exports a **registry helper** that maps `CAPABILITY` tags to import paths.
    *   Discovers worker agents at start-up and attaches them to the Orchestrator graph.
5.  **Worker Agents** (`*_agent`)
    *   `document_agent` – intake pipeline.
    *   `browser_agent` – web/docket scraping.
    *   `database_agent` – pgvector queries + schema ops.
    *   `legal_manager_agent` – memo composer & citation verifier (phase-2).
6.  **Shared Services (MCP)**
    *   File store (Rust), ChromaDB, Postgres, Neo4j, OpenTelemetry.

## A2A Flow

```mermaid
sequenceDiagram
    User->>CEO: Ask legal question
    CEO->>Orchestrator: /ask (goal, context)
    Orchestrator->>document_agent: /ask (ingest docs)
    document_agent-->>Orchestrator: processed docs
    Orchestrator->>browser_agent: /ask (search precedents)
    browser_agent-->>Orchestrator: findings
    Orchestrator->>database_agent: /ask (store & fetch embeddings)
    database_agent-->>Orchestrator: vector IDs
    Orchestrator-->>CEO: Draft answer
    CEO-->>User: Final brief
```

_Only the CEO talks to the user; all back-channel chatter is A2A._
