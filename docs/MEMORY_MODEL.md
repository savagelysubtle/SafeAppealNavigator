# savagelysubtle-airesearchagent - Memory & State Model Implementation (Simplified Agents)

This document details how the different layers of memory and state are implemented within the `savagelysubtle-airesearchagent` architecture, reflecting the simplified agent hierarchy.

## 1. Conversation Memory

*   **User's Definition:** "Short-term memory for the current interaction. Includes user queries, agent responses, UI state (e.g., selected documents)."
*   **Implementation:**
    *   **Primary Holder:** The **AG-UI Backend Service**.
    *   **AG-UI SDK:** Uses `ag_ui.core.types.Message` list for interaction history.
    *   **State Synchronization:** `MessagesSnapshotEvent`, `StateSnapshotEvent`, `StateDeltaEvent` with the UI.
    *   **Passing to Orchestrator:** Relevant history and UI context are passed in A2A requests to the ChiefLegalOrchestrator.
    *   **Orchestrator's Role:** The ChiefLegalOrchestrator uses this context for its LLM interactions and may pass summarized versions to Coordinator Agents.

## 2. Task Graph (Workflow State)

*   **User's Definition:** "State of the overall multi-step task. Which agents have run, their interim results, next steps, dependencies."
*   **Implementation:**
    *   **Core Engine:** The **ChiefLegalOrchestrator Agent** manages the Task Graph using **`pydantic-graph`**.
    *   **`pydantic_graph.Graph`:** Defines workflows with nodes representing coordinator-level tasks (e.g., `InvokeDocumentProcessing`, `EvaluateResearchNeeds`).
    *   **`pydantic_graph.GraphRunContext.state` (`StateT`):** Holds live workflow state: current phase, user query, case ID, references to artifacts/results from Coordinator Agents.
    *   **Persistence (MCP Neo4j Tool - Optional but Recommended):** Task Graph state can be persisted via an MCP Tool wrapping a Neo4j client, enabling resumable workflows. The `pydantic_graph.persistence.BaseStatePersistence` interface would be implemented using this tool.

## 3. Artifact Store

*   **User's Definition:** "Storage for large data objects generated during tasks (PDFs, text extractions, embeddings, draft reports)."
*   **Implementation:**
    *   **Primary Access:** The **Rust-based Filesystem MCP Server**.
    *   **MCP Tools:** Agents (Coordinators, Orchestrator) interact via MCP tools like `write_mcp_file`, `read_mcp_file`, exposed by the Custom MCP Server.
    *   **Referencing:** Agents pass MCP paths to artifacts in A2A messages.

## 4. Vector DB

*   **User's Definition:** "Stores embeddings of document chunks for semantic search (RAG)."
*   **Implementation:**
    *   **Primary Access:** **ChromaDB**, via an MCP tool (wrapping `autogen_rag_chroma` or direct client).
    *   **MCP Tools:** `add_embeddings_to_vector_db`, `query_vector_db`.
    *   **Usage:** The `DocumentProcessingCoordinator` uses `add_embeddings_to_vector_db`. The `DataQueryCoordinator` (specifically its internal knowledge retrieval logic) uses `query_vector_db`.

## 5. SQL Database

*   **User's Definition:** "Stores structured case metadata, WCAT decisions, policy documents, user profiles, audit logs."
*   **Implementation:**
    *   **Primary Access:** SQLite/PostgreSQL, via an MCP tool (wrapping `mcpDataBases` or direct client).
    *   **MCP Tools:** `execute_sql_query`, `execute_sql_statement`.
    *   **Usage:** `DocumentProcessingCoordinator` for initial metadata. `DataQueryCoordinator` for specific lookups. Audit Log can write here.

## 6. Graph Database (Neo4j)

*   **User's Definition:** For knowledge graphs, complex relationships, and Task Graph persistence.
*   **Implementation:**
    *   **Primary Access:** Neo4j, via an MCP tool wrapping a Neo4j client.
    *   **MCP Tools:** `execute_cypher_query`, `persist_task_graph_state_node`.
    *   **Usage:** Knowledge graph interactions (if a dedicated agent/coordinator handles this) and ChiefLegalOrchestrator for Task Graph state persistence.

## 7. Scratchpad / Working Memory

*   **User's Definition:** "Temporary, in-memory storage for an agent during a single task execution."
*   **Implementation:**
    *   **Pydantic AI Agent State:** For LLM-based agents (Orchestrator, Coordinators, and any internal Pydantic AI instances they use), Pydantic AI's message history (`self.messages` during a run) serves this purpose.
    *   **Local Variables:** Python methods within agents use local variables for transient data.
    *   This layer is ephemeral to a single agent's skill execution. Persistent data is explicitly saved via MCP tools.

## 8. Audit Log

*   **User's Definition:** "Immutable record of all significant system events."
*   **Implementation:**
    *   **Application-Level Logging:** Standard Python `logging` across all services.
    *   **Structured Logging:** JSON format with `timestamp`, `service_name`, `conversation_id`, `task_id`, `event_type`, `payload`.
    *   **Centralized Log Aggregation (Optional):** Via an MCP Tool (`log_audit_event`) writing to the SQL Database, or to an external logging platform.

## Memory Hand-off and Context Passing

Context is passed primarily via:

1.  **A2A Message Payloads (`MessageEnvelope`):** The Orchestrator passes necessary context (summarized history, task parameters, artifact MCP paths) to Coordinators. Coordinators return structured results.
2.  **MCP Tool Calls:** Parameters and results for data/file operations.
3.  **AG-UI State Events:** For UI synchronization.
4.  **Pydantic-graph State (`StateT`):** Managed by the Orchestrator, informs subsequent A2A delegations. Information *from* this state is packaged into A2A requests for Coordinators.
```
