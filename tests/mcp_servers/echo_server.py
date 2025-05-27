from mcp.server.fastmcp import FastMCP

# Create an MCP server instance
mcp_server = FastMCP(name="EchoTestServer", version="0.1.0")

@mcp_server.tool()
def echo(message: str) -> str:
    """
    Echoes back the provided message.
    """
    print(f"[EchoServer] Received message: {message}")
    return f"Echo: {message}"

if __name__ == "__main__":
    print("[EchoServer] Starting Echo MCP Server via STDIO...")
    # When run directly, FastMCP's run method defaults to stdio transport
    # if no other transport is explicitly configured or passed to run().
    mcp_server.run()
