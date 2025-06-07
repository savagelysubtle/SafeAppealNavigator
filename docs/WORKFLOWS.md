# savagelysubtle-airesearchagent - Key Workflows (Simplified Agents)

This document outlines interactions for key use cases with the simplified agent hierarchy.

## 1. User Initiates Full Legal Research Workflow

```mermaid
sequenceDiagram
    participant User
    participant GradioUI
    participant AGUI_Backend as AG-UI Backend
    participant Orchestrator as ChiefLegalOrchestrator (A2A)
    participant MCPServer as MCP Server
    participant DocCoord as DocumentProcessingCoordinator (A2A)
    participant ResearchCoord as LegalResearchCoordinator (A2A)
    participant QueryCoord as DataQueryCoordinator (A2A)
    participant FS_MCP as Filesystem MCP Tool
    participant Chroma_MCP as ChromaDB MCP Tool

    User->>GradioUI: Enters query (e.g., "Research WCB case X, analyze precedents for Y")
    GradioUI->>AGUI_Backend: Send UserMessage (AG-UI Event)

    AGUI_Backend->>Orchestrator: POST A2A ExecuteTask (skill: "start_full_research_workflow", params: {query, case_docs_mcp_paths})
    activate Orchestrator
    Orchestrator->>Orchestrator: Start pydantic-graph: "FullResearchWorkflow"

    %% Document Intake Phase
    Orchestrator->>MCPServer: Call MCP Tool: find_agent_for_task(desc="coordinate document processing and embedding")
    MCPServer-->>Orchestrator: Return AgentCard (DocumentProcessingCoordinator)

    Orchestrator->>DocCoord: POST A2A ExecuteTask (skill: "process_and_store_documents", params: {document_sources, case_id, vector_collection})
    activate DocCoord
    DocCoord->>DocCoord: Internally manages: <br>1. Read files (via FS_MCP via MCPServer)<br>2. OCR/Tag (internal LLM)<br>3. Chunk<br>4. Embed & Store (via Chroma_MCP via MCPServer)
    DocCoord-->>Orchestrator: A2A TaskResult (status: success, output: {processing_summary})
    deactivate DocCoord
    Orchestrator->>Orchestrator: Update pydantic-graph state (intake_complete)

    %% Research Phase
    Orchestrator->>MCPServer: Call MCP Tool: find_agent_for_task(desc="coordinate legal research and policy analysis")
    MCPServer-->>Orchestrator: Return AgentCard (LegalResearchCoordinator)

    Orchestrator->>ResearchCoord: POST A2A ExecuteTask (skill: "conduct_comprehensive_research", params: {search_keywords, case_context})
    activate ResearchCoord
    ResearchCoord->>ResearchCoord: Internally manages: <br>1. Web Search (via MCP tool)<br>2. WCAT Scraping (via MCP tool or internal)<br>3. Policy Matching (internal LLM + data tools via MCP)
    ResearchCoord-->>Orchestrator: A2A TaskResult (status: success, output: {research_findings_summary})
    deactivate ResearchCoord
    Orchestrator->>Orchestrator: Update pydantic-graph state (research_complete)

    %% Query & Synthesis Phase
    Orchestrator->>MCPServer: Call MCP Tool: find_agent_for_task(desc="coordinate data querying and report generation")
    MCPServer-->>Orchestrator: Return AgentCard (DataQueryCoordinator)

    Orchestrator->>QueryCoord: POST A2A ExecuteTask (skill: "query_and_synthesize_report", params: {intake_summary, research_summary, query_details})
    activate QueryCoord
    QueryCoord->>QueryCoord: Internally manages: <br>1. Chroma/SQL Queries (via MCP tools)<br>2. Answer Synthesis & Report Drafting (internal LLM)
    QueryCoord-->>Orchestrator: A2A TaskResult (status: success, output: {report_artifact_mcp_path})
    deactivate QueryCoord
    Orchestrator->>Orchestrator: Update pydantic-graph state (report_generated)

    %% Finalize
    Orchestrator->>MCPServer: Call MCP Tool: read_mcp_file(path=report_artifact_mcp_path)
    MCPServer->>FS_MCP: Read File
    FS_MCP-->>MCPServer: Report Content
    MCPServer-->>Orchestrator: Report Content

    Orchestrator-->>AGUI_Backend: A2A TaskResult (final report content)
    deactivate Orchestrator

    AGUI_Backend->>GradioUI: Send TextMessageEndEvent / StateSnapshotEvent (AG-UI Events with final report)
    GradioUI->>User: Display Final Report
```

**Key Workflow Changes:**

*   The Orchestrator now delegates to higher-level Coordinator agents.
*   Each Coordinator agent encapsulates a larger part of the workflow (e.g., `DocumentProcessingCoordinator` handles the entire document intake pipeline).
*   The internal complexity of OCR, tagging, embedding, searching, etc., is managed *within* the respective Coordinator agent, which itself uses Pydantic AI and MCP tools.

## 2. Interactive Chat with Orchestrator

This workflow remains largely the same at a high level, as the user interacts with the Orchestrator. The difference is that if the Orchestrator decides to delegate a sub-task arising from the chat, it will discover and invoke a Coordinator agent rather than a more granular Guild Member.

```mermaid
sequenceDiagram
    participant User
    participant GradioUI
    participant AGUI_Backend as AG-UI Backend
    participant Orchestrator as ChiefLegalOrchestrator (A2A)
    participant MCPServer as MCP Server
    participant CoordinatorAgent as Example Coordinator Agent (A2A)

    User->>GradioUI: Types chat message
    GradioUI->>AGUI_Backend: Send UserMessage (AG-UI Event)

    AGUI_Backend->>Orchestrator: POST A2A SendMessage
    activate Orchestrator
    Orchestrator->>Orchestrator: LLM (Pydantic AI) processes message.
    %% Orchestrator decides it needs to perform, e.g., a specific type of research.
    Orchestrator->>MCPServer: Call MCP Tool: find_agent_for_task(desc="coordinate legal research on specific topic X")
    MCPServer-->>Orchestrator: Return AgentCard (LegalResearchCoordinator)

    Orchestrator->>CoordinatorAgent: POST A2A ExecuteTask (skill: "research_specific_topic", params: {topic: "X"})
    activate CoordinatorAgent
    CoordinatorAgent->>CoordinatorAgent: Perform its coordinated research tasks (internal LLM calls, MCP tool usage).
    CoordinatorAgent-->>Orchestrator: A2A TaskResult (output: {research_summary_for_X})
    deactivate CoordinatorAgent

    Orchestrator->>Orchestrator: LLM (Pydantic AI) synthesizes chat response using research_summary_for_X.
    Orchestrator-->>AGUI_Backend: A2A Message (final chat response)
    deactivate Orchestrator

    AGUI_Backend->>GradioUI: Send TextMessageContentEvent / TextMessageEndEvent
    GradioUI->>User: Displays Orchestrator's response
```
The core message flow and protocol usage remain consistent, with the primary change being the granularity of agents invoked by the Orchestrator.
```