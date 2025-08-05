// Application-wide constants

// Regular expression for matching policy numbers (e.g., "AP1-234-567", "RS8-999-888")
export const POLICY_NUMBER_REGEX = /\b([A-Z]{2}\d{1,2}-\d{3}-\d{3})\b/g;

// Default color for WCAT pattern tags
export const DEFAULT_WCAT_PATTERN_TAG_COLOR = '#8B5CF6'; // Purple

// Other commonly used constants
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const ALLOWED_FILE_TYPES = ['.pdf', '.docx', '.doc', '.txt', '.rtf'];

// API endpoints
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:10200';

// UI Constants
export const SIDEBAR_WIDTH = '256px'; // w-64 in Tailwind
export const HEADER_HEIGHT = '64px'; // h-16 in Tailwind

// Theme colors
export const THEME_COLORS = {
  primary: '#3B82F6',
  secondary: '#8B5CF6',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#06B6D4',
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  theme: 'app-theme',
  files: 'app-files',
  tags: 'app-tags',
  chat: 'app-chat',
  audit: 'app-audit',
  wcatCases: 'app-wcatCases',
  policyManuals: 'app-policyManuals',
  chatSessions: 'app-chat-sessions',
  sidebarState: 'main-sidebar-collapsed',
  mcpApiConfigs: 'mcp-api-configurations',
  activeApiConfig: 'mcp-active-api-config-name',
  tools: 'app-tools',
  selectedToolIds: 'app-selected-tool-ids',
  selectedFileIds: 'app-selected-file-ids',
  selectedWcatIds: 'app-selected-wcat-ids',
  dynamicMarkers: 'app-dynamic-markers',
} as const;