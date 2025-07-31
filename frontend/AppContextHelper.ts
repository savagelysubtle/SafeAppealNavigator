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
      allowedDirectories: result.allowed_directories
    };
  } catch (error: any) {
    return {
      isRunning: false,
      error: `Failed to connect to backend: ${error.message}`
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mcp_path: mcpPath, content })
    });

    const result = await response.json();
    return {
      success: result.success || false,
      message: result.message || 'Unknown error',
      mcpPath: result.mcp_path
    };
  } catch (error: any) {
    return {
      success: false,
      message: `Backend error: ${error.message}`
    };
  }
}

/**
 * Delete file via backend MCP API
 */
export async function deleteMCPFile(mcpPath: string): Promise<MCPDeleteResponse> {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/api/mcp/delete-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mcp_path: mcpPath })
    });

    const result = await response.json();
    return {
      success: result.success || false,
      message: result.message || 'Unknown error',
      mcpPath: result.mcp_path
    };
  } catch (error: any) {
    return {
      success: false,
      message: `Backend error: ${error.message}`
    };
  }
}