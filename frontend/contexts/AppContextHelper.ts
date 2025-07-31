/**
 * Helper functions for MCP operations through backend API
 * Replaces direct MCP client calls with backend API endpoints
 */

const BACKEND_BASE_URL = 'http://localhost:10200';

export interface MCPServerStatus {
  isRunning: boolean;
  version?: string;
  error?: string;
  allowedDirectories?: string[];
}

export interface MCPWriteResponse {
  success: boolean;
  message: string;
  mcpPath?: string;
}

export interface MCPDeleteResponse {
  success: boolean;
  message: string;
  mcpPath?: string;
}

/**
 * Get MCP server status via backend API
 */
export async function getMCPServerStatus(): Promise<MCPServerStatus> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/server-status`);
    const result = await response.json();

    return {
      isRunning: result.is_running || false,
      version: result.version,
      error: result.error,
      allowedDirectories: result.allowed_directories || []
    };
  } catch (error) {
    console.error('Error fetching MCP server status:', error);
    return {
      isRunning: false,
      error: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
}

/**
 * Write file via backend MCP API
 */
export async function writeMCPFile(mcpPath: string, content: string): Promise<MCPWriteResponse> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/write-file`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mcp_path: mcpPath,
        content: content
      })
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error writing MCP file:', error);
    return {
      success: false,
      message: `Error writing file: ${error instanceof Error ? error.message : 'Unknown error'}`,
      mcpPath: mcpPath
    };
  }
}

/**
 * Delete file or directory via backend MCP API
 */
export async function deleteMCPFile(mcpPath: string): Promise<MCPDeleteResponse> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/delete-file`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        mcp_path: mcpPath
      })
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error deleting MCP file:', error);
    return {
      success: false,
      message: `Error deleting file: ${error instanceof Error ? error.message : 'Unknown error'}`,
      mcpPath: mcpPath
    };
  }
}