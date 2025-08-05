# SafeAppealNavigator Project Structure

This document outlines the actual project structure and data organization for SafeAppealNavigator.

## Root Directory Structure

```
SafeAppealNavigator/
├── data/                           # All application data storage
│   ├── sqlite/                     # PostgreSQL-style structured data
│   │   └── cases.db               # Main case database
│   ├── chroma_db/                 # Vector database for document embeddings
│   ├── artifacts_store/           # Document artifacts and processed files
│   └── mcp.json                   # MCP server configuration
├── src/ai_research_assistant/     # Main Python application
├── frontend/                      # React TypeScript frontend
├── tmp/                          # Temporary files and agent state
├── tests/                        # Test suite
├── docs/                         # Documentation
├── plans/                        # Project planning documents
└── pyproject.toml               # Python dependencies and project config
```

## Data Directory (`./data/`)

### SQLite Database (`./data/sqlite/`)
- **Purpose**: Structured relational data storage
- **Main Database**: `cases.db` - Core case information, metadata, relationships
- **Schema**: Case records, timelines, user data, system state
- **Access**: Via Database Agent through MCP tools

### Vector Database (`./data/chroma_db/`)
- **Purpose**: Document embeddings and semantic search
- **Content**: Text embeddings from legal documents, case summaries
- **Technology**: ChromaDB persistent storage
- **Access**: Via Database Agent for similarity searches

### Artifacts Store (`./data/artifacts_store/`)
- **Purpose**: Original and processed document files
- **Content**: PDFs, Word docs, images, processed text extracts
- **Organization**: Organized by case ID and document type
- **Access**: Via Document Agent for file operations

### MCP Configuration (`./data/mcp.json`)
- **Purpose**: MCP server configuration and tool routing
- **Content**: Server definitions, tool mappings, agent integrations
- **Usage**: Loaded by MCP Client Manager for agent tool access

## Agent Architecture Flow

Based on `docs/flowchart.mmd`, the agent communication follows this pattern:

```
User ←→ CEO Agent ←→ Orchestrator Agent
                          ↓
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
    Browser Agent    Legal Agent    Database Agent
            ↓             ↓             ↓
            └─────────────┼─────────────┘
                          ↓
                    MCP SERVER
                          ↓
            ┌─────────────┼─────────────┐
            ↓             ↓             ↓
        Browser      Database        Files
```

## Source Code Structure (`src/ai_research_assistant/`)

### Core Agents (`agents/`)
```
agents/
├── ceo_agent/                     # Top-level user interaction
├── orchestrator_agent/            # Task coordination and routing
└── specialized_manager_agent/
    ├── browser_agent/             # Web automation and research
    ├── legal_manager_agent/       # Legal research and analysis
    ├── document_agent/            # File I/O operations
    └── database_agent/            # Data storage and retrieval
```

### Backend Services
```
├── ag_ui_backend/                 # FastAPI WebSocket gateway
├── a2a_services/                  # Agent-to-Agent communication
├── mcp_intergration/              # MCP tool integration
├── core/                          # Shared utilities and state management
├── browser/                       # Browser automation components
└── config/                        # Configuration management
```

## Frontend Structure (`frontend/`)

```
frontend/
├── components/                    # React components
│   ├── modals/                   # Modal dialogs
│   ├── pages/                    # Page components
│   │   ├── settings/            # Settings configuration
│   │   └── wcat/                # WCAT-specific features
│   └── ui/                      # Reusable UI components
├── contexts/                     # React contexts
├── hooks/                       # Custom React hooks
└── services/                    # API and WebSocket services
```

## Temporary Files (`tmp/`)

```
tmp/
├── agent_state.db               # Agent state management (SQLite)
├── browser_sessions/            # Browser automation cache
├── processing_queue/            # Document processing queue
└── logs/                       # Application logs
```

## Configuration Files

### Python Dependencies (`pyproject.toml`)
- **Purpose**: All Python package dependencies and project metadata
- **Usage**: `uv sync` installs all dependencies
- **Groups**: Main dependencies + dev tools (pytest, ruff, ty)

### Environment Configuration (`.env`)
- **Purpose**: API keys, database paths, service configuration
- **Key Paths**:
  - `DATABASE_URL_SQLITE="sqlite:///./data/sqlite/cases.db"`
  - `CHROMA_DB_PATH="./data/chroma_db"`
  - Various API keys for LLM providers

## Data Flow Patterns

### Document Processing Flow
1. **Upload**: User uploads documents through frontend
2. **Document Agent**: Handles file I/O, saves to `artifacts_store/`
3. **Database Agent**: Processes text, creates embeddings, stores in `chroma_db/`
4. **Legal Agent**: Analyzes content, stores metadata in `sqlite/`

### Case Research Flow
1. **Legal Agent**: Receives search query from Orchestrator
2. **Browser Agent**: Performs web research via MCP SERVER
3. **Database Agent**: Searches local `chroma_db/` for similar cases
4. **Legal Agent**: Combines results, analyzes relevance
5. **CEO Agent**: Presents findings to user

### Data Persistence
- **Structured Data**: Case info, user settings → `./data/sqlite/cases.db`
- **Document Content**: File embeddings → `./data/chroma_db/`
- **Original Files**: Documents, images → `./data/artifacts_store/`
- **Agent State**: Communication state → `tmp/agent_state.db`

## Development Guidelines

### Working with Data
- **Never hardcode paths** - use configuration from `global_settings.py`
- **Database migrations** - handled through SQLite schema updates
- **Vector operations** - always go through Database Agent
- **File operations** - always go through Document Agent

### Agent Communication
- **A2A Protocol**: Agent-to-Agent messaging for coordination
- **AG-UI Protocol**: WebSocket communication with frontend
- **MCP Integration**: Tool access through configured MCP servers

### Adding New Features
1. **Identify data requirements** - which storage system?
2. **Determine agent responsibility** - which agent handles the task?
3. **Update MCP configuration** - add any required tools
4. **Implement frontend hooks** - for user interaction
5. **Update documentation** - reflect new data flows