/**
 * @deprecated This file previously contained direct Google Gemini API calls.
 * All LLM functionality has been moved to the AG-UI backend which uses the
 * proper llm_provider.py system for unified LLM management.
 *
 * Frontend should now communicate with the backend through:
 * - AG-UI WebSocket for chat/conversations
 * - REST API endpoints for specific functions like API key testing
 *
 * Backend endpoints available:
 * - POST /api/test-api-key - Test LLM provider API keys
 * - WebSocket /ag_ui/ws/{thread_id} - Real-time agent communication
 */

// Placeholder functions for backward compatibility during migration
// These should be replaced with proper AG-UI backend calls

export const testApiKey = async (apiKey?: string): Promise<boolean> => {
  console.warn('testApiKey: Use backend API endpoint /api/test-api-key instead');
  return false;
};

export const summarizeEvidenceText = async (text: string): Promise<string> => {
  console.warn('summarizeEvidenceText: Use AG-UI backend through WebSocket instead');
  return 'Summary functionality moved to AG-UI backend';
};

export const identifyWcatCasePatterns = async (text: string): Promise<string[]> => {
  console.warn('identifyWcatCasePatterns: Use AG-UI backend through WebSocket instead');
  return [];
};

export const extractPolicyEntriesFromManualText = async (text: string, manualName: string): Promise<any[]> => {
  console.warn('extractPolicyEntriesFromManualText: Use AG-UI backend through WebSocket instead');
  return [];
};

export const resetChatSession = (): void => {
  console.warn('resetChatSession: Use AG-UI backend session management instead');
};