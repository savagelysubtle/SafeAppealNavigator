# Specialized Manager Agents

This directory contains specialized agents that work under the Orchestrator Agent to handle specific domains of functionality. Each agent receives MCP tools automatically based on configuration in `config/mcp_config/agent_mcp_mapping.json`.

## Agent Hierarchy (Based on Flowchart)

```
User <-> CEO Agent <-> Orchestrator Agent
                              |
            +-----------------+-----------------+
            |                 |                 |
      Browser Agent     Legal Agent      Database Agent
            |                 |                 |
            |          Document Agent           |
            |                                   |
            +----------> MCP SERVER <-----------+
                             |
                    +--------+--------+
                    |        |        |
                Browser  Database  Files
```

## Agent Responsibilities

### Database Agent
- **Primary Role**: Database maintenance, document intake, and sorting
- **MCP Tools**: All Chroma database tools
  - Collection management (create, list, modify, delete)
  - Document operations (add, query, update, delete)
  - Vector search and metadata filtering
- **Key Methods**:
  - `intake_documents()` - Store documents in vector database
  - `sort_documents_into_collections()` - Organize documents by criteria
  - `maintain_database()` - Cleanup and optimization operations
  - `create_specialized_collection()` - Create purpose-specific collections

### Document Agent
- **Primary Role**: Reading existing documents and creating new documents
- **MCP Tools**: File I/O tools only (read_file, write_file, read_multiple_files)
- **Key Methods**:
  - `read_document()` - Read document content from files
  - `create_document()` - Create new documents with content
  - `create_report_from_template()` - Generate reports using templates
  - `append_to_document()` - Add content to existing documents
- **Note**: Does NOT handle database operations, embeddings, or document organization

### Browser Agent
- **Primary Role**: Web browsing, searching, and scraping
- **MCP Tools**:
  - Brave Search tools for web searching
  - Playwright tools for browser automation
- **Key Methods**:
  - `conduct_comprehensive_research()` - Perform web research on topics

### Legal Manager Agent
- **Primary Role**: Coordinate legal document creation and citation verification
- **MCP Tools**: None (coordinates through other agents)
- **Key Methods**:
  - `draft_legal_memo()` - Create legal memos (coordinates with Document Agent)
  - `verify_citations()` - Check citation accuracy
  - `review_legal_document()` - Comprehensive document review
  - `manage_legal_workflow()` - Handle complex legal workflows
- **Note**: Works through Orchestrator and coordinates with Document Agent

## MCP Tool Distribution

Tools are automatically distributed to agents based on the configuration in:
`src/ai_research_assistant/config/mcp_config/agent_mcp_mapping.json`

When an agent is initialized:
1. The base agent's `_get_initial_tools()` fetches MCP tools from the MCP client manager
2. Tools are filtered based on the agent's configured requirements
3. Tools are wrapped as PydanticAI tools and made available to the agent

## Agent Communication Flow

1. **User** communicates with **CEO Agent**
2. **CEO Agent** delegates to **Orchestrator Agent**
3. **Orchestrator Agent** coordinates between:
   - **Browser Agent** for web research
   - **Legal Agent** for legal document tasks
   - **Database Agent** for data storage and retrieval
4. **Legal Agent** coordinates with **Document Agent** for file operations
5. All agents access the **MCP Server** for their respective tools
6. **MCP Server** interfaces with:
   - **Browser** (via Browser Agent)
   - **Database** (via Database Agent)
   - **Files** (via Document Agent)

## Key Design Principles

1. **Separation of Concerns**: Each agent has a specific domain of responsibility
2. **Tool-Based Capabilities**: Agents only have access to tools relevant to their role
3. **Coordination Over Direct Access**: Higher-level agents coordinate through lower-level agents
4. **MCP Integration**: All external system access goes through MCP tools