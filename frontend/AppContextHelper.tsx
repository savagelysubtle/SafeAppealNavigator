// Helper functions for AppContext that interact with the backend API

import { McpServerStatus } from './types';

const API_BASE_URL = 'http://localhost:10200';

/**
 * Get the current MCP server status from the backend
 */
export async function getMCPServerStatus(): Promise<McpServerStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/mcp/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get MCP status: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      isRunning: data.isRunning || false,
      error: data.error,
      version: data.version,
      allowedDirectories: data.allowedDirectories || [],
    };
  } catch (error) {
    console.error('Error fetching MCP status:', error);
    return {
      isRunning: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Write a file to the MCP server
 */
export async function writeMCPFile(path: string, content: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/mcp/write-file`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ path, content }),
    });

    return response.ok;
  } catch (error) {
    console.error('Error writing MCP file:', error);
    return false;
  }
}

/**
 * Delete a file from the MCP server
 */
export async function deleteMCPFile(path: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/mcp/delete-file`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ path }),
    });

    return response.ok;
  } catch (error) {
    console.error('Error deleting MCP file:', error);
    return false;
  }
}