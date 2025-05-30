# savagelysubtle-airesearchagent - Development Kickoff Plan (Simplified Agents)

This plan outlines a phased approach for developing the `savagelysubtle-airesearchagent` system with its simplified agent hierarchy.

## Phase 0: Preparation & Setup

1.  **Finalize Core Technologies & Versions:** Confirm versions for Python, Pydantic AI, pydantic-graph, FastA2A, FastMCP, AG-UI SDK, Gradio, database clients.
2.  **Project Initialization:** Git repo, Poetry/UV setup, core dependencies in `pyproject.toml`, implement `FILE_TREE.md` structure.
3.  **Environment Configuration:** Create and populate `.env.example` and `.env`. Implement `src/savagelysubtle_airesearchagent/config/global_settings.py`.
4.  **Basic Logging & Utilities:** Setup `logging_config.py`.
5.  **Docker Setup:** `docker-compose.yml` for databases (ChromaDB, Neo4j, PostgreSQL/SQLite) and Rust Filesystem MCP server.

## Phase 1: Implement Core Data Models & Agent Cards

1.  **`MessageEnvelope` Pydantic Model:** Define in `core/models.py`.
2.  **Initial Skill I/O Models:** Define Pydantic models for key Coordinator skills (e.g., `ProcessAndStoreDocumentsInput` for `DocumentProcessingCoordinator`).
3.  **Agent Cards:** Create JSON files in `agent_cards/` for the ChiefLegalOrchestrator and each Coordinator Agent (`DocumentProcessingCoordinator`, `LegalResearchCoordinator`, `DataQueryCoordinator`). Define their broader skills. Include `embedding_text_representation`.

## Phase 2: Develop and Test the MCP Server

1.  **MCP Server Core (FastMCP):** Implement `mcp_integration/server_main.py`.
2.  **Agent Registry:** Implement `agent_registry.py` to load Agent Cards, generate embeddings, and provide the `find_agent_for_task` MCP tool. Implement MCP resources for card listing/retrieval.
3.  **Basic Shared Tools:** Implement wrappers in `shared_tools/` for one or two key operations (e.g., `read_mcp_file` calling the Rust FS server, `query_sql_db` for SQLite).
4.  **Testing:** Unit test card loading, embedding, `find_agent_for_task`. Integration test MCP tool endpoints.

## Phase 3: Implement and Test a Coordinator Agent A2A Service

1.  **Choose Initial Coordinator:** e.g., `DocumentProcessingCoordinator`.
2.  **Pydantic AI Agent Logic:**
    *   In `agents/document_processing_coordinator/agent.py`, define `DocumentProcessingCoordinator(pydantic_ai.Agent)`.
    *   Implement its main skill (e.g., `async def process_and_store_documents(...)`). This method will internally handle the sub-steps (OCR, tagging, chunking, embedding) by calling helper methods or smaller, private Pydantic AI instances, and will use MCP tools (from Phase 2) for file access and vector storage.
3.  **A2A Service Wrapper (FastA2A):**
    *   Use `a2a_services/startup.py` to launch this Coordinator as an A2A service, injecting its MCP client utility.
4.  **Testing:**
    *   Unit test the Coordinator's skill method (mocking MCP tool calls and internal LLM calls).
    *   Integration test: Start MCP Server, Rust FS server, ChromaDB, and the `DocumentProcessingCoordinator` A2A service. Send an A2A `ExecuteTask` request to its endpoint and verify.

## Phase 4: Develop the ChiefLegalOrchestrator (Pydantic AI + pydantic-graph)

1.  **Pydantic AI Orchestrator Agent:** Define in `agents/chief_legal_orchestrator/agent.py`.
2.  **pydantic-graph Task Graph:**
    *   In `task_graph.py`, define the graph with nodes for discovering and invoking Coordinator agents.
    *   Nodes will use Python helper functions (`_python_query_mcp_for_agent`, `_python_invoke_task_agent`) to interact with the MCP Server and Coordinator A2A services.
3.  **Mocked A2A Calls to Coordinators:** Initially, `_python_invoke_task_agent` can return mocked responses.
4.  **Testing:** Unit test graph nodes. Test the Orchestrator's main skill, verifying calls to MCP discovery and (mocked) A2A invocation helpers. Start Orchestrator A2A service and test.

## Phase 5: Integrate Orchestrator with Live Coordinator Agent

1.  **Update `_python_invoke_task_agent`:** Modify this helper in the Orchestrator to make actual A2A calls to the `DocumentProcessingCoordinator` A2A service (from Phase 3).
2.  **End-to-End Test (Partial):** Start MCP Server, Rust FS Server, ChromaDB, `DocumentProcessingCoordinator` A2A Service, and `ChiefLegalOrchestrator` A2A Service. Send a task to the Orchestrator and verify the flow.

## Phase 6: Develop and Test the AG-UI Backend Service

1.  **FastAPI AG-UI Backend:** Implement `ag_ui_backend/main.py` and `router.py` using the AG-UI Python SDK.
2.  **AG-UI to Orchestrator A2A Client:** Implement `a2a_client.py` in the AG-UI backend.
3.  **State Management:** Implement `state_manager.py`.
4.  **Testing:** Unit test event/request translations. Mock Orchestrator A2A service to test AG-UI Backend. Use a WebSocket test script to verify AG-UI event handling.

## Phase 7: Integrate Gradio UI with the AG-UI Backend

1.  **Modify `webui.py`:** Update Gradio handlers to communicate with the AG-UI Backend via WebSockets for AG-UI events.
2.  **Testing:** Manual E2E testing from UI through to the single integrated Coordinator and back.

## Phase 8: Incrementally Implement Remaining Coordinator Agent A2A Services

For `LegalResearchCoordinator` and `DataQueryCoordinator`:
1.  Define their Pydantic AI logic, encapsulating their respective sub-tasks and using MCP tools.
2.  Update/finalize their Agent Cards.
3.  Enable their A2A service startup.
4.  Expand the ChiefLegalOrchestrator's `pydantic-graph` to integrate them.
5.  Test individually, then integrate with the Orchestrator.

## Phase 9: Testing, Debugging, and Refinement

1.  **Comprehensive Testing:** Unit, Integration, and E2E tests covering all workflows and components.
2.  **Performance & Scalability Testing:** (Future phase)
3.  **Refine Prompts & Logic:** Based on test results and observed behavior.

## Brief Notes:

*   **Error Handling:** Robust error handling in A2A services, MCP tools, Orchestrator graph, and AG-UI Backend.
*   **Logging:** Consistent structured logging with correlation IDs.
*   **Security:** Address inter-service communication security as needed.
*   **Streaming:** Implement A2A/AG-UI streaming for long-running tasks if required for UI responsiveness.

This revised plan focuses on creating fewer, more comprehensive Coordinator agents, simplifying the initial delegation from the Orchestrator, while still allowing for internal complexity and future specialization within those Coordinators.
```