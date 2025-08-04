# MCP Integration for AI Research Assistant

This module provides Model Context Protocol (MCP) integration, allowing agents to automatically receive MCP tools based on configuration.

## Overview

The MCP integration system:
1. Reads MCP server configuration from `data/mcp.json`
2. Connects to MCP servers (stdio or HTTP transport)
3. Fetches available tools from each server
4. Automatically distributes tools to agents based on mappings in `agent_mcp_mapping.json`

## How It Works

### Automatic Tool Loading

When any agent is initialized:
1. The base agent's `_get_initial_tools()` method automatically fetches MCP tools
2. It uses the agent's name to look up configured tools in the mapping
3. Tools are wrapped as PydanticAI tools and added to the agent

### Example

```python
from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import DocumentAgent

# Create agent - MCP tools are loaded automatically
doc_agent = DocumentAgent()

# Agent now has access to MCP tools like:
# - mcp_filesystem_read_file
# - mcp_filesystem_write_file
# - mcp_unified_local_server_vector_database
# etc.

# Use the agent normally - it can use MCP tools
result = await doc_agent.run_skill("Please read the file at /path/to/document.txt")
```

## Configuration

### MCP Server Configuration (`data/mcp.json`)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem@latest", "/path/to/files"],
      "type": "stdio",
      "enabled": true
    }
  }
}
```

### Agent Tool Mapping (`src/ai_research_assistant/config/mcp_config/agent_mcp_mapping.json`)

Defines which MCP servers and tools each agent type should receive.

## Key Components

- **MCPClientManager**: Manages MCP server connections and tool distribution
- **MCPToolWrapper**: Wraps MCP tools to be compatible with PydanticAI
- **agent_integration.py**: Helper functions for tool injection
- **base_pydantic_agent.py**: Modified to automatically load MCP tools

## Usage with Settings Page

The React settings page (`frontend/components/pages/SettingsPage.tsx`) can edit the MCP configuration, which is then used by the backend to connect to MCP servers.

## Complete Example

This example shows how agents automatically receive MCP tools based on configuration:

```python
"""
Example usage of MCP integration with agents.

This shows how agents automatically receive MCP tools based on configuration.
"""

import asyncio
import logging

from ai_research_assistant.agents.ceo_agent.agent import CEOAgent
from ai_research_assistant.agents.specialized_manager_agent.browser_agent.agent import (
    BrowserAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.document_agent.agent import (
    DocumentAgent,
)
from ai_research_assistant.mcp_intergration import (
    get_mcp_client_manager,
    shutdown_mcp_client_manager,
)

logging.basicConfig(level=logging.INFO)


async def main():
    """Example of how agents automatically get MCP tools."""

    try:
        # Initialize MCP client manager (happens automatically when first agent is created)
        print("Initializing MCP servers...")
        mcp_manager = await get_mcp_client_manager()

        # Show server status
        status = mcp_manager.get_server_status()
        print("\nMCP Server Status:")
        print(f"  Connected servers: {status['connected_servers']}")
        print(f"  Total tools available: {status['total_tools']}")

        # Create agents - they will automatically get their MCP tools
        print("\nCreating agents...")

        # CEO Agent
        ceo_agent = CEOAgent()
        print(f"\nCEO Agent initialized with {len(ceo_agent.tools)} tools")
        for tool in ceo_agent.tools[:3]:  # Show first 3 tools
            print(f"  - {tool.name}: {tool.description[:50]}...")

        # Document Agent
        doc_agent = DocumentAgent()
        print(f"\nDocument Agent initialized with {len(doc_agent.tools)} tools")
        for tool in doc_agent.tools[:3]:  # Show first 3 tools
            print(f"  - {tool.name}: {tool.description[:50]}...")

        # Browser Agent
        browser_agent = BrowserAgent()
        print(f"\nBrowser Agent initialized with {len(browser_agent.tools)} tools")
        for tool in browser_agent.tools[:3]:  # Show first 3 tools
            print(f"  - {tool.name}: {tool.description[:50]}...")

        # Example: Use an agent with its MCP tools
        print("\n\nExample usage:")
        print("When you call agent.run_skill() or agent.pydantic_agent.run(),")
        print("the agent can use any of its MCP tools automatically.")

        # Example prompt that would trigger tool use
        example_prompt = "Please list the files in the current directory"
        print(f"\nExample prompt: '{example_prompt}'")
        print(
            "The agent would automatically use the appropriate MCP file listing tool."
        )

    finally:
        # Cleanup
        print("\nShutting down MCP connections...")
        await shutdown_mcp_client_manager()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Example

```bash
python -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from ai_research_assistant.mcp_intergration.README import main
asyncio.run(main())
"
```

Or create a simple script with the code above and run it directly.