# SafeAppealNavigator Development Guide

A comprehensive guide for developers working on SafeAppealNavigator's multi-agent WCAT legal research system.

## Quick Start

### Prerequisites
- **Python 3.13+** with `uv` package manager
- **Node.js 18+** with npm
- **Git** for version control

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/savagelysubtle/safeappealnavigator.git
cd safeappealnavigator

# Set up Python environment
uv venv --python 3.13
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows CMD: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install all Python dependencies from pyproject.toml
uv sync --all-groups

# Install frontend dependencies
cd frontend
npm install
cd ..

# Set up environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration

# Install browser automation
playwright install chromium --with-deps

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

### Running the Application

```bash
# Start the complete application (backend + frontend)
python run_app.py

# Or start services individually:
# Backend only: uvicorn src.ai_research_assistant.ag_ui_backend.main:app --host 0.0.0.0 --port 10200 --reload
# Frontend only: cd frontend && npm run dev
```

## Architecture Overview

SafeAppealNavigator uses a multi-agent architecture where specialized agents coordinate through MCP (Message Control Protocol) servers:

### Agent Hierarchy
```
User Interface (React)
         ↓
   AG-UI Backend (FastAPI)
         ↓
      CEO Agent
         ↓
   Orchestrator Agent
         ↓
┌─────────┬─────────┬─────────┐
│ Browser │ Legal   │Database │
│ Agent   │ Agent   │ Agent   │
└─────────┴─────────┴─────────┘
         ↓
   Document Agent
         ↓
    MCP SERVER
         ↓
┌─────────┬─────────┬─────────┐
│Browser  │Database │ Files   │
│Tools    │Tools    │Tools    │
└─────────┴─────────┴─────────┘
```

### Data Storage Strategy
- **SQLite** (`./data/sqlite/cases.db`): Structured case data, metadata, relationships
- **ChromaDB** (`./data/chroma_db/`): Vector embeddings for document similarity search
- **Artifacts Store** (`./data/artifacts_store/`): Original documents and processed files
- **Agent State** (`tmp/agent_state.db`): Agent communication and session state

## Development Workflow

### 1. Working with Agents

Each agent has specific responsibilities:

#### CEO Agent
- **Purpose**: High-level user interaction and task delegation
- **Location**: `src/ai_research_assistant/agents/ceo_agent/`
- **Role**: Receives user requests, delegates to Orchestrator

#### Orchestrator Agent
- **Purpose**: Task coordination and routing
- **Location**: `src/ai_research_assistant/agents/orchestrator_agent/`
- **Role**: Coordinates between specialized agents

#### Specialized Agents
```python
# Browser Agent - Web automation and research
src/ai_research_assistant/agents/specialized_manager_agent/browser_agent/

# Legal Agent - Legal research and analysis
src/ai_research_assistant/agents/specialized_manager_agent/legal_manager_agent/

# Document Agent - File I/O operations
src/ai_research_assistant/agents/specialized_manager_agent/document_agent/

# Database Agent - Data storage and retrieval
src/ai_research_assistant/agents/specialized_manager_agent/database_agent/
```

### 2. Adding New Features

#### Step 1: Plan Data Requirements
Determine which storage system your feature needs:
- **Structured data** → SQLite via Database Agent
- **Document content** → ChromaDB via Database Agent
- **File storage** → Artifacts Store via Document Agent

#### Step 2: Identify Agent Responsibility
- **Web research** → Browser Agent
- **Legal analysis** → Legal Agent
- **File operations** → Document Agent
- **Data operations** → Database Agent

#### Step 3: Implement Agent Logic
```python
# Example: Adding a new tool to Legal Agent
# File: src/ai_research_assistant/agents/specialized_manager_agent/legal_manager_agent/agent.py

async def analyze_case_strength(self, case_details: dict) -> dict:
    """Analyze the strength of a legal case based on precedents."""
    # Implementation here
    pass
```

#### Step 4: Update MCP Configuration
Add new tools to `./data/mcp.json` if needed:
```json
{
  "mcpServers": {
    "new_tool": {
      "command": "path/to/tool",
      "type": "stdio"
    }
  }
}
```

#### Step 5: Create Frontend Interface
Add React components and hooks:
```typescript
// File: frontend/hooks/useCaseAnalysis.ts
export const useCaseAnalysis = () => {
  // Hook implementation
};
```

### 3. Database Operations

#### SQLite Operations (Structured Data)
```python
# Always go through Database Agent
from src.ai_research_assistant.agents.specialized_manager_agent.database_agent import DatabaseAgent

# Example usage in other agents
case_data = await database_agent.get_case_by_id(case_id)
await database_agent.update_case_status(case_id, "in_progress")
```

#### ChromaDB Operations (Vector Search)
```python
# Document similarity search
similar_docs = await database_agent.search_similar_documents(
    query_text="workplace injury back pain",
    limit=10
)
```

#### File Operations
```python
# Always go through Document Agent
from src.ai_research_assistant.agents.specialized_manager_agent.document_agent import DocumentAgent

# Save/load documents
await document_agent.save_document(file_path, case_id, category="medical")
content = await document_agent.load_document(document_id)
```

### 4. Frontend Development

#### Using AG-UI Hooks
```typescript
import { useAGUI } from '@/hooks/useAGUI';

function MyComponent() {
  const { sendMessage, lastMessage, connected } = useAGUI();

  const handleSearch = async () => {
    sendMessage({
      type: 'legal_research',
      payload: { query: 'WCAT back injury cases' }
    });
  };
}
```

#### Data Flow Pattern
1. **User Action** → React Component
2. **Component** → AG-UI Hook
3. **Hook** → WebSocket Message
4. **Backend** → Agent Coordination
5. **Agent** → MCP Tool Execution
6. **Result** → WebSocket Response
7. **Hook** → Component Update

## Testing

### Python Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_research_assistant

# Run specific agent tests
pytest tests/agents/test_legal_agent.py

# Run integration tests
pytest tests/integration/
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### Agent Testing Strategy
```python
# Example agent test
import pytest
from src.ai_research_assistant.agents.specialized_manager_agent.legal_manager_agent.agent import LegalAgent

@pytest.mark.asyncio
async def test_legal_research():
    agent = LegalAgent()
    result = await agent.search_wcat_cases("back injury")
    assert len(result) > 0
    assert "case_id" in result[0]
```

## Code Quality

### Type Hints (Required)
```python
from typing import List, Dict, Optional

async def process_case(case_id: str, documents: List[str]) -> Dict[str, any]:
    """Process a case with type hints."""
    pass
```

### Code Formatting
```bash
# Format code with Ruff
ruff format src/

# Check for issues
ruff check src/

# Type checking with Ty
ty check src/
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-wcat-search

# Make changes, commit with conventional format
git commit -m "feat: add advanced WCAT similarity search"

# Update CHANGELOG.md
# Submit pull request
```

## Debugging

### Agent Communication
Check agent logs:
```bash
tail -f tmp/logs/agent_communication.log
```

### Database Issues
```bash
# Check SQLite database
sqlite3 ./data/sqlite/cases.db ".tables"

# Check ChromaDB status
# Database Agent provides health check methods
```

### MCP Server Issues
Verify MCP configuration:
```bash
# Check MCP servers status
python -c "
from src.ai_research_assistant.mcp_intergration.mcp_client_manager import MCPClientManager
manager = MCPClientManager()
print(manager.list_available_tools())
"
```

## Performance Optimization

### Agent Coordination
- **Parallel Execution**: Orchestrator runs multiple agents simultaneously
- **Caching**: ChromaDB and SQLite provide built-in caching
- **Connection Pooling**: Database connections are pooled for efficiency

### Frontend Optimization
- **React.memo()** for expensive components
- **useMemo()** and **useCallback()** for heavy computations
- **WebSocket connection management** for real-time updates

## Deployment Considerations

### Production Setup
1. **Environment Variables**: Set all required API keys
2. **Database Initialization**: Ensure `./data/` directory structure exists
3. **Agent Services**: Consider running agents as separate services
4. **Logging**: Configure proper log levels and rotation

### Security
- **API Keys**: Never commit to version control
- **File Permissions**: Restrict access to `./data/` directory
- **Input Validation**: Sanitize all user inputs
- **CORS Configuration**: Proper frontend-backend CORS setup

This guide should get you started with SafeAppealNavigator development. For specific questions, check the detailed documentation in `/docs/` or review the agent-specific README files.