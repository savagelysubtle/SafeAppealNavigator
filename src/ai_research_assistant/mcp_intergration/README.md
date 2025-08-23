# MCP Integration for AI Research Assistant

This module provides Model Context Protocol (MCP) integration, allowing agents to automatically receive MCP tools based on configuration. The implementation follows proper MCP client patterns using AsyncExitStack and stdio transport.

## Overview

The MCP integration system:
1. Reads MCP server configuration from `data/mcp.json`
2. Connects to MCP servers using proper MCP client patterns
3. Maintains persistent connections using AsyncExitStack
4. Fetches available tools from each server
5. Automatically distributes tools to agents based on mappings in `agent_mcp_mapping.json`

## Key Features

✅ **Proper MCP Client Implementation**: Follows official MCP patterns with AsyncExitStack and stdio transport
✅ **Persistent Connections**: Maintains stable connections to MCP servers
✅ **Automatic Tool Discovery**: Discovers and wraps tools from connected servers
✅ **Agent Integration**: Automatically distributes tools to agents based on configuration
✅ **Error Handling**: Robust error handling and connection management
✅ **Resource Management**: Proper cleanup and disconnection handling

## Architecture

### Components

- **MCPServerConnection**: Manages individual server connections using proper MCP patterns
- **MCPClientManager**: Orchestrates multiple server connections and tool distribution
- **AsyncExitStack**: Proper resource management for MCP connections
- **Tool Wrapping**: Automatic conversion of MCP tools to PydanticAI tools

### Connection Lifecycle

1. **Initialization**: Create server parameters and connect using stdio_client
2. **Session Management**: Use AsyncExitStack to manage ClientSession lifecycle
3. **Tool Discovery**: List and wrap tools from connected servers
4. **Persistent Operation**: Maintain connections for agent use
5. **Cleanup**: Proper disconnection and resource cleanup

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
      "enabled": true,
      "cwd": null,
      "env": {}
    },
    "unified_local_server": {
      "command": "python",
      "args": ["-m", "mcp_unified_local_server"],
      "type": "stdio",
      "enabled": true
    }
  }
}
```

### Agent Tool Mapping (`src/ai_research_assistant/config/mcp_config/agent_mcp_mapping.json`)

Defines which MCP servers and tools each agent type should receive:

```json
{
  "agent_mcp_mappings": {
    "DocumentAgent": {
      "required_servers": ["filesystem", "unified_local_server"],
      "optional_servers": [],
      "primary_tools": ["read_file", "write_file", "vector_database"]
    },
    "BrowserAgent": {
      "required_servers": ["filesystem"],
      "optional_servers": ["unified_local_server"],
      "primary_tools": ["read_file", "write_file"]
    }
  }
}
```

## Key Components

- **MCPServerConnection**: Individual server connection with proper lifecycle management
- **MCPClientManager**: Central manager for all MCP server connections
- **Tool Wrapping**: Automatic conversion of MCP tools to PydanticAI compatible tools
- **Agent Integration**: Seamless integration with existing agent architecture

## Usage with Settings Page

The React settings page (`frontend/components/pages/SettingsPage.tsx`) can edit the MCP configuration, which is then used by the backend to connect to MCP servers.

## Complete Example

```python
"""
Example usage of the new MCP integration with proper patterns.
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
    """Example of agents automatically getting MCP tools."""

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
cd src/ai_research_assistant/mcp_intergration
python README.py  # If you save the example as README.py
```

## Differences from Previous Implementation

The new implementation:
- Uses proper MCP client patterns with AsyncExitStack
- Maintains persistent connections instead of short-lived sessions
- Follows official MCP documentation patterns
- Provides better error handling and resource management
- Supports proper connection lifecycle management
- Fixes issues with session management and tool calling

## Troubleshooting

### Common Issues

1. **Server Connection Failed**: Check that the MCP server command and args are correct
2. **No Tools Available**: Verify the server is running and responding to tool list requests
3. **Tool Call Errors**: Ensure the server is still connected and responding

### Debugging

Enable debug logging to see detailed connection and tool call information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```