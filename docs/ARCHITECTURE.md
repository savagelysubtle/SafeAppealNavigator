# savagelysubtle-airesearchagent - System Architecture (Simplified Agents)

## 1. Overall System Architecture

The `savagelysubtle-airesearchagent` is designed as a distributed, microservice-based multi-agent system. It leverages standardized protocols like A2A (Agent-to-Agent), MCP (Model Context Protocol), and AG-UI (Agent User Interaction Protocol) to ensure modularity, interoperability, and scalability. The agent hierarchy is simplified with a ChiefLegalOrchestrator delegating to specialized Coordinator agents.

```mermaid
graph TD
    subgraph User Interface Layer
        UI[Gradio Web UI]
    end

    subgraph AG-UI Backend Layer
        AGUI_Backend[AG-UI Backend Service (FastAPI + AG-UI SDK)]
    end

    subgraph Orchestration Layer (A2A Service)
        Orchestrator[ChiefLegalOrchestrator (Pydantic AI + pydantic-graph)<br>A2A Service via FastA2A]
    end

    subgraph Coordinator Agent Layer (A2A Services)
        DocCoord[DocumentProcessingCoordinator<br>(Pydantic AI)<br>A2A Service via FastA2A]
        ResearchCoord[LegalResearchCoordinator<br>(Pydantic AI)<br>A2A Service via FastA2A]
        QueryCoord[DataQueryCoordinator<br>(Pydantic AI)<br>A2A Service via FastA2A]
    end

    subgraph MCP Layer
        MCPServer[Custom MCP Server (FastMCP)<br>- Agent Registry (Agent Cards)<br>- Shared Tool Provider]
    end

    subgraph External MCP Tools & Data Stores
        MCP_FS[Rust Filesystem MCP Tool<br>(Artifact Store)]
        MCP_Chroma[ChromaDB MCP Tool<br>(Vector DB)]
        MCP_SQL[SQL DB MCP Tool<br>(SQLite/Postgres)]
        MCP_Neo4j[Neo4j MCP Tool<br>(Graph DB / Task Graph Persistence)]
    end

    UI -- AG-UI Protocol --> AGUI_Backend
    AGUI_Backend -- A2A Request/Response --> Orchestrator

    Orchestrator -- "1. Discover Agent (MCP Call)" --> MCPServer
    MCPServer -- "2. Return AgentCard" --> Orchestrator
    Orchestrator -- "3. Invoke Coordinator (A2A Call)" --> DocCoord
    Orchestrator -- "3. Invoke Coordinator (A2A Call)" --> ResearchCoord
    Orchestrator -- "3. Invoke Coordinator (A2A Call)" --> QueryCoord
    Orchestrator -- "Invoke Shared Tool (MCP Call)" --> MCPServer

    DocCoord -- "Use Tool (MCP Call)" --> MCPServer
    ResearchCoord -- "Use Tool (MCP Call)" --> MCPServer
    QueryCoord -- "Use Tool (MCP Call)" --> MCPServer

    MCPServer -- Accesses --> MCP_FS
    MCPServer -- Accesses --> MCP_Chroma
    MCPServer -- Accesses --> MCP_SQL
    MCPServer -- Accesses --> MCP_Neo4j

    %% Styling
    classDef ui fill:#D6EAF8,stroke:#3498DB,stroke-width:2px;
    classDef agui fill:#D1F2EB,stroke:#1ABC9C,stroke-width:2px;
    classDef orchestrator fill:#FCF3CF,stroke:#F1C40F,stroke-width:2px;
    classDef coordinator fill:#FDEDEC,stroke:#E74C3C,stroke-width:2px;
    classDef mcp fill:#E8DAEF,stroke:#8E44AD,stroke-width:2px;
    classDef external fill:#E5E7E9,stroke:#808B96,stroke-width:2px;

    class UI ui;
    class AGUI_Backend agui;
    class Orchestrator orchestrator;
    class DocCoord,ResearchCoord,QueryCoord coordinator;
    class MCPServer mcp;
    class MCP_FS,MCP_Chroma,MCP_SQL,MCP_Neo4j external;
```

**Interaction Flow:**

The overall flow remains similar, but the ChiefLegalOrchestrator now delegates to Coordinator agents, which internally manage a broader set of related tasks.

1.  User interacts with UI, AG-UI Backend translates to A2A for Orchestrator.
2.  **ChiefLegalOrchestrator**:
    *   Uses `pydantic-graph` for workflow.
    *   Queries MCP Server to discover appropriate **Coordinator Agents** (e.g., `DocumentProcessingCoordinator`).
    *   Invokes Coordinator Agents via A2A.
3.  **Coordinator Agents** (e.g., `DocumentProcessingCoordinator`):
    *   Are Pydantic AI agents.
    *   Receive A2A tasks from the Orchestrator.
    *   Internally manage a sequence of operations that were previously handled by more granular "Guild Member" agents. For example, `DocumentProcessingCoordinator` will handle PDF ingestion, metadata tagging, and chunking/embedding within its own logic, possibly by calling distinct internal methods or smaller, private Pydantic AI agent instances if complex LLM reasoning is needed for sub-steps.
    *   Use MCP tools for data access (e.g., `DocumentProcessingCoordinator` uses FS and ChromaDB tools).
    *   Return results to the Orchestrator via A2A.
4.  Orchestrator aggregates, and the final response flows back to the UI.

## 2. Component Deep Dive

### 2.1. ChiefLegalOrchestrator

*   **Role & Responsibilities:** Unchanged from the previous detailed description, but its direct delegates are now the Coordinator agents.
*   **Task Graph (pydantic-graph):** The nodes in its graph will now reflect transitions between coordinator-level tasks (e.g., `InvokeDocumentProcessing`, `InvokeLegalResearch`).
*   **MCP Client & A2A Client:** Functionality remains the same, but targets Coordinator Agent Cards and their A2A services.
*   **A2A Service:** Interface to AG-UI Backend remains the same.

### 2.2. Coordinator Agents (e.g., `DocumentProcessingCoordinator`, `LegalResearchCoordinator`, `DataQueryCoordinator`)

These agents replace the more granular "Guild Member" agents from the user's original org chart. Each Coordinator is a Pydantic AI agent responsible for a significant phase of the legal research workflow.

*   **General Template (Pydantic AI):**
    *   Each Coordinator (e.g., `DocumentProcessingCoordinator`) is an instance of `pydantic_ai.Agent`.
    *   `__init__`: Similar to Guild Agents before, takes `model_alias`, `tools` (MCP tools), and a `system_prompt` defining its broader coordination role for a specific domain (e.g., "You are a Document Processing Coordinator. You manage the intake, OCR, metadata extraction, chunking, and embedding of legal documents.").
    *   **Internal Logic:** The methods of a Coordinator agent will now encapsulate the logic previously distributed among several more specialized agents. For example, `DocumentProcessingCoordinator`'s `process_document_dump` skill will internally handle:
        1.  Fetching documents (via FS MCP tool).
        2.  Performing OCR (could be a local library call or a sub-LLM call if complex).
        3.  Tagging metadata (LLM call via its own Pydantic AI instance).
        4.  Chunking text.
        5.  Generating embeddings and storing them (via ChromaDB MCP tool).
        This internal complexity can be managed by helper methods or even by instantiating and using private, non-A2A Pydantic AI sub-agents if needed for very distinct LLM-driven sub-tasks within the coordinator.
*   **Skills (from Agent Cards):**
    *   Skills defined in a Coordinator's Agent Card will be higher-level.
    *   Example: `DocumentProcessingCoordinator` might have one primary skill: `process_and_store_documents(source_mcp_paths: List[str], case_id: str, target_collection: str) -> DocumentProcessingSummary`.
*   **Pydantic Models for I/O:** Inputs and outputs for Coordinator skills will be Pydantic models, wrapped in the `MessageEnvelope`.
*   **Interaction with MCP Tools:** Coordinators will be heavy users of MCP tools for data storage, retrieval, and filesystem operations.
*   **A2A Service (FastA2A):** Each Coordinator runs as an independent A2A service.

### 2.3. MCP Server

*   **Implementation (FastMCP):** Unchanged.
*   **Agent Registry (`find_agent_for_task`):**
    *   Will now load and manage Agent Cards for the ChiefLegalOrchestrator and the Coordinator agents.
    *   Embedding generation and similarity search logic remains the same but operates on a smaller set of more broadly defined agent cards.
*   **Shared MCP Tools:** Unchanged. These tools are consumed by the Coordinator agents.

### 2.4. A2A Service Layer

*   **FastA2A Usage:** Unchanged in principle. The `a2a_startup.py` script will now launch A2A services for the ChiefLegalOrchestrator and each Coordinator agent.
*   The `AdkToA2AExecutor` (or equivalent) will map incoming A2A skill requests to methods on the respective Coordinator Pydantic AI agent instances.

### 2.5. AG-UI Backend Service

*   **Role & SDK Usage:** Unchanged. It still bridges the UI to the ChiefLegalOrchestrator's A2A service.

### 2.6. Gradio Web UI

*   **Interaction:** Unchanged. It communicates with the AG-UI Backend.

## 3. Data Models & Contracts

### 3.1. Inter-Agent JSON MessageEnvelope

The `MessageEnvelope` Pydantic model remains the same as specified previously.

### 3.2. Example Coordinator Agent Skill I/O Models

**DocumentProcessingCoordinator - `process_and_store_documents` skill:**

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class DocumentSourceInfo(BaseModel):
    mcp_path: str # Path to the document in the MCP Filesystem
    original_filename: Optional[str] = None

class ProcessedDocumentInfo(BaseModel):
    source_path: str
    document_type: Optional[str] = None
    text_artifact_mcp_path: str # Path to extracted text
    metadata_artifact_mcp_path: str # Path to extracted metadata (e.g., entities)
    vector_db_chunk_ids: List[str]
    error_message: Optional[str] = None

class ProcessAndStoreDocumentsInput(BaseModel):
    document_sources: List[DocumentSourceInfo]
    case_id: str
    target_vector_collection: str

class DocumentProcessingSummary(BaseModel):
    case_id: str
    processed_documents: List[ProcessedDocumentInfo]
    overall_status: str # e.g., "Completed", "CompletedWithErrors"
    errors_summary: List[str] = Field(default_factory=list)
```

### 3.3. Agent Card Structure (JSON)

The structure remains the same, but there will be fewer cards, corresponding to the Orchestrator and Coordinators. Skills will be broader.

*Example: `agent_cards/document_processing_coordinator.json`*
```json
{
    "name": "DocumentProcessingCoordinator",
    "description": "Coordinates the entire document intake pipeline: ingestion, OCR, metadata tagging, chunking, and embedding for legal documents.",
    "version": "1.0.0",
    "provider": "savagelysubtle-airesearchagent",
    "url": "http://localhost:10101/a2a",
    "authentication": { "schemes": ["public"] },
    "capabilities": { "streaming": false, "toolUse": true, "llmPowered": true },
    "skills": [
        {
            "id": "process_and_store_documents",
            "name": "Process and Store Documents",
            "description": "Manages the full lifecycle of document intake, from raw files to indexed embeddings.",
            "inputSchema": { "$ref": "#/components/schemas/ProcessAndStoreDocumentsInput" },
            "outputSchema": { "$ref": "#/components/schemas/DocumentProcessingSummary" },
            "tags": ["document pipeline", "intake", "ocr", "embedding", "coordination"]
        }
    ],
    "embedding_text_representation": "Agent: DocumentProcessingCoordinator. Description: Coordinates the entire document intake pipeline...",
    "components": {
        "schemas": {
            "ProcessAndStoreDocumentsInput": { /* ... JSON Schema ... */ },
            "DocumentProcessingSummary": { /* ... JSON Schema ... */ }
        }
    }
}
