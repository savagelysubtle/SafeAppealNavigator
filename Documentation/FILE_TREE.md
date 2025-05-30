airesearchagent/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── FILE_TREE.md
├── poetry.lock
├── pyproject.toml
├── uv.lock
├── webui.py

├── agent_cards/
│   ├── chief_legal_orchestrator.json
│   ├── document_processing_coordinator.json
│   ├── legal_research_coordinator.json
│   └── data_query_coordinator.json

├── docs/
│   ├── ARCHITECTURE.md
│   ├── WORKFLOWS.md
│   ├── MEMORY_MODEL.md
│   ├── DEVELOPMENT_KICKOFF.md
│   └── assets/
│       └── architecture_overview_simplified.mermaid

├── src/
│   └── savagelysubtle_airesearchagent/
│       ├── __init__.py
│
│       ├── agents/
│       │   ├── __init__.py
│       │   │
│       │   ├── chief_legal_orchestrator/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py        # Implements ChiefLegalOrchestrator (Pydantic AI + pydantic-graph)
│       │   │   ├── task_graph.py   # pydantic-graph definitions
│       │   │   └── prompts.py
│       │   │
│       │   ├── document_processing_coordinator/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py        # Implements DocumentProcessingCoordinator (Pydantic AI)
│       │   │   │                   # Internally manages logic for PDF ingest, metadata, chunk/embed
│       │   │   └── prompts.py
│       │   │
│       │   ├── legal_research_coordinator/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py        # Implements LegalResearchCoordinator (Pydantic AI)
│       │   │   │                   # Internally manages browser search, WCAT scraping, policy matching
│       │   │   └── prompts.py
│       │   │
│       │   ├── data_query_coordinator/
│       │   │   ├── __init__.py
│       │   │   ├── agent.py        # Implements DataQueryCoordinator (Pydantic AI)
│       │   │   │                   # Internally manages Chroma/SQLite queries and answer synthesis/report generation
│       │   │   └── prompts.py
│       │   │
│       │   └── common_utils.py     # Utilities shared across agents
│       │
│       ├── a2a_services/
│       │   ├── __init__.py
│       │   ├── startup.py          # Main script to launch any agent as an A2A service
│       │   └── executors.py
│       │
│       ├── mcp_integration/
│       │   ├── __init__.py
│       │   ├── server_main.py      # MCP Server entry point
│       │   ├── agent_registry.py
│       │   ├── shared_tools/
│       │   │   ├── __init__.py
│       │   │   ├── db_tools.py
│       │   │   ├── fs_tools.py
│       │   └── mcp_client_utils.py
│       │
│       ├── ag_ui_backend/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── router.py
│       │   ├── state_manager.py
│       │   └── a2a_client.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py           # Pydantic models (MessageEnvelope, skill I/O)
│       │   ├── enums.py
│       │   └── exceptions.py
│       │
│       ├── config/
│       │   ├── __init__.py
│       │   ├── global_settings.py
│       │   └── mcp_config/
│       │       └── mcp_servers.json
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logging_config.py
│           └── ...
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── agents/
│   │   ├── mcp_integration/
│   │   └── ...
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   └── ...
│
└── data/
    ├── sqlite/
    ├── chroma_db/
    └── artifacts_store/