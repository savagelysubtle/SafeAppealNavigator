import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode, useRef } from 'react';
import { EvidenceFile, Tag, ChatMessage, AuditLogEntry, Theme, McpServerStatus, WcatCase, PolicyManual, PolicyEntry, PolicyReference, SavedChatSession, McpUserProvidedServers, McpApiConfig, AiTool, McpServerProcessConfig, DynamicMarker, McpStdioOptions } from '../types';
import { v4 as uuidv4 } from 'uuid';
import { POLICY_NUMBER_REGEX, DEFAULT_WCAT_PATTERN_TAG_COLOR } from '../constants';
// Removed direct MCP client imports - MCP is now handled entirely by the backend
// Frontend only manages UI state for MCP server configuration
// All MCP operations go through backend API endpoints at /api/mcp/*
import { getMCPServerStatus, writeMCPFile, deleteMCPFile } from './AppContextHelper';

console.log("AppContext.tsx: Module loaded.");

interface AppContextType {
  theme: Theme;
  toggleTheme: () => void;
  files: EvidenceFile[];
  addFile: (file: Omit<EvidenceFile, 'id' | 'tags' | 'annotations' | 'mcpPath' | 'isProcessing' | 'referencedPolicies'>, mcpPath: string, originalFileNameForMcp: string, contentForMcp: string) => Promise<EvidenceFile | null >;
  updateFile: (fileId: string, updates: Partial<EvidenceFile>) => void;
  deleteFile: (fileId: string) => Promise<void>;
  getFileById: (fileId: string) => EvidenceFile | undefined;
  tags: Tag[];
  addTag: (tag: Omit<Tag, 'id'>) => Tag;
  removeTagFromFile: (fileId: string, tagId: string) => void;
  addTagToFile: (fileId: string, tag: Tag) => void;
  chatHistory: ChatMessage[];
  addChatMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => ChatMessage;
  clearChatHistory: () => void;
  auditLog: AuditLogEntry[];
  addAuditLogEntry: (action: string, details: string) => void;
  mcpServerStatus: McpServerStatus;
  setMcpServerStatus: (status: McpServerStatus) => void;
  // MCP client removed - all MCP operations now go through backend API
  refreshMcpStatus: () => Promise<void>;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  currentError: string | null;
  setError: (error: string | null) => void;
  apiKey: string | null;
  setApiKey: (key: string | null) => void;

  wcatCases: WcatCase[];
  addWcatCase: (caseData: Omit<WcatCase, 'id' | 'ingestedAt' | 'tags'>, fetchedPatternTags?: Tag[]) => Promise<WcatCase>;
  updateWcatCase: (caseId: string, updates: Partial<WcatCase>) => void;
  deleteWcatCase: (caseId: string) => void;
  getWcatCaseByDecisionNumber: (decisionNumber: string) => WcatCase | undefined;
  getWcatCaseById: (id: string) => WcatCase | undefined;

  policyManuals: PolicyManual[];
  addPolicyManual: (manualInfo: { manualName: string; sourceUrl?: string; version?: string }, pdfContent: string, originalFileName: string) => Promise<PolicyManual | null>;
  deletePolicyManual: (manualId: string) => Promise<void>;
  getPolicyManualById: (manualId: string) => PolicyManual | undefined;
  getPolicyEntry: (manualId: string, policyNumber: string) => PolicyEntry | undefined;

  findRelevantWcatCases: (queryText: string, associatedFile?: EvidenceFile) => Promise<WcatCase[]>;
  extractPolicyReferencesFromFile: (file: EvidenceFile) => PolicyReference[];
  generateAndAssignWcatPatternTags: (caseId: string) => Promise<void>;

  isMainSidebarCollapsed: boolean;
  toggleMainSidebar: () => void;

  savedChatSessions: SavedChatSession[];
  saveChatSession: (name: string, messagesToSave: ChatMessage[], fileIds?: string[], wcatIds?: string[], toolIds?: string[]) => void;
  loadChatSession: (sessionId: string) => SavedChatSession | null;
  deleteChatSession: (sessionId: string) => void;

  // MCP Server Configuration Management
  userMcpServerDefinitions: McpUserProvidedServers | null; // From user's mcp.json
  mcpApiConfigs: McpApiConfig[]; // Array of API connection configurations
  activeApiConfigName: string | null;
  setActiveApiConfig: (configName: string | null) => Promise<void>;
  updateMcpApiConfigs: (newConfigs: McpApiConfig[]) => void;

  // AI Tools Management
  tools: AiTool[];
  addTool: (toolData: Omit<AiTool, 'id' | 'type' | 'mcpProcessDetails'>, type?: 'custom_abstract') => AiTool; // For custom tools
  deleteTool: (toolId: string) => void; // Only custom tools
  selectedToolIdsForContext: string[];
  toggleToolContext: (toolId: string) => void;

  // Chat Context Selection
  selectedFileIdsForContext: string[];
  toggleFileContext: (fileId: string) => void;
  selectedWcatCaseIdsForContext: string[];
  toggleWcatCaseContext: (caseId: string) => void;

  // Dynamic Markers for Generative UI
  dynamicMarkers: Record<string, DynamicMarker[]>;
  setDynamicMarkersForFile: (fileId: string, markers: DynamicMarker[]) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  console.log("AppContext.tsx: AppProvider component function STARTED.");
  const [theme, setTheme] = useState<Theme>(() => {
    const storedTheme = localStorage.getItem('app-theme') as Theme;
    return storedTheme || Theme.Dark;
  });
  const [files, setFiles] = useState<EvidenceFile[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentError, setCurrentError] = useState<string | null>(null);
  const currentErrorRef = useRef(currentError); // Ref for currentError
  useEffect(() => {
    currentErrorRef.current = currentError;
  }, [currentError]);


  const [apiKey, setApiKeyInternal] = useState<string | null>(process.env.API_KEY || null);

  const [wcatCases, setWcatCases] = useState<WcatCase[]>([]);
  const [policyManuals, setPolicyManuals] = useState<PolicyManual[]>([]);

  // MCP client state removed - all MCP operations now go through backend API
  const [mcpServerStatus, setMcpServerStatus] = useState<McpServerStatus>({ isRunning: false, error: "Checking MCP Server..." });

  const [isMainSidebarCollapsed, setIsMainSidebarCollapsed] = useState<boolean>(false);
  const [savedChatSessions, setSavedChatSessions] = useState<SavedChatSession[]>([]);

  // MCP Server Configuration State
  const [userMcpServerDefinitions, setUserMcpServerDefinitions] = useState<McpUserProvidedServers | null>(null);
  const [mcpApiConfigs, setMcpApiConfigsInternal] = useState<McpApiConfig[]>([]);
  const [activeApiConfigName, setActiveApiConfigNameInternal] = useState<string | null>(null);

  // AI Tools State
  const [tools, setTools] = useState<AiTool[]>([]);
  const [selectedToolIdsForContext, setSelectedToolIdsForContext] = useState<string[]>([]);

  // Chat Context Selection State
  const [selectedFileIdsForContext, setSelectedFileIdsForContext] = useState<string[]>([]);
  const [selectedWcatCaseIdsForContext, setSelectedWcatCaseIdsForContext] = useState<string[]>([]);

  // Dynamic Markers State
  const [dynamicMarkers, setDynamicMarkersInternal] = useState<Record<string, DynamicMarker[]>>({});


  const addAuditLogEntry = useCallback((action: string, details: string) => {
    const newEntry: AuditLogEntry = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      action,
      details,
    };
    setAuditLog((prevLog) => [newEntry, ...prevLog.slice(0, 199)]);
  }, []);

  const localSetError = useCallback((error: string | null) => {
    setCurrentError(error);
    if (error) {
        console.error("AppContext: Application Error Set:", error);
        addAuditLogEntry('APPLICATION_ERROR_SET', error);
    }
  }, [addAuditLogEntry]);

  // Add refreshMcpStatus function for Settings page
  const refreshMcpStatus = useCallback(async () => {
    try {
      const status = await getMCPServerStatus();
      setMcpServerStatus(status);
      addAuditLogEntry('MCP_STATUS_REFRESHED', 'MCP server status refreshed via backend API.');
    } catch (error: any) {
      const errorMsg = `Failed to refresh MCP status: ${error.message}`;
      setMcpServerStatus({ isRunning: false, error: errorMsg });
      localSetError(errorMsg);
      addAuditLogEntry('MCP_STATUS_REFRESH_ERROR', errorMsg);
    }
  }, [addAuditLogEntry, localSetError]);

  useEffect(() => {
    // Simplified initialization - just load configs and refresh MCP status
    const initializeSystem = async () => {
      console.log("AppContext.tsx: initializeSystem (backend API version) STARTED.");

      // Load MCP configurations from localStorage or defaults
      const storedApiConfigsStr = localStorage.getItem('mcp-api-configurations');
      if (storedApiConfigsStr) {
        try {
          const configs = JSON.parse(storedApiConfigsStr);
          setMcpApiConfigsInternal(configs);
          addAuditLogEntry('MCP_CONFIGS_LOADED', `Loaded ${configs.length} MCP configurations from localStorage.`);
        } catch (e: any) {
          addAuditLogEntry('MCP_CONFIGS_PARSE_ERROR', `Failed to parse MCP configs: ${e.message}`);
        }
      }

      // Set active config
      const activeConfigName = localStorage.getItem('mcp-active-api-config-name');
      if (activeConfigName) {
        setActiveApiConfigNameInternal(activeConfigName);
      }

      // Refresh MCP status via backend
      await refreshMcpStatus();

      // Load tools from localStorage
      const storedToolsStr = localStorage.getItem('app-tools');
      if (storedToolsStr) {
        try {
          const tools = JSON.parse(storedToolsStr);
          setTools(tools);
          addAuditLogEntry('TOOLS_LOADED', `Loaded ${tools.length} AI tools from localStorage.`);
        } catch (e: any) {
          addAuditLogEntry('TOOLS_PARSE_ERROR', `Failed to parse tools: ${e.message}`);
        }
      }

      addAuditLogEntry('APP_INIT_COMPLETE', 'Application initialization complete (backend API mode).');
    };

    initializeSystem();
  }, [addAuditLogEntry, localSetError, refreshMcpStatus]);


  const updateMcpApiConfigs = useCallback((newConfigs: McpApiConfig[]) => {
    setMcpApiConfigsInternal(newConfigs);
    localStorage.setItem('mcp-api-configurations', JSON.stringify(newConfigs));
    addAuditLogEntry('MCP_API_CONFIGS_UPDATED', `${newConfigs.length} API configurations saved.`);
  }, [addAuditLogEntry]);

  const setActiveApiConfig = useCallback(async (configName: string | null) => {
    if (configName === null) {
        setActiveApiConfigNameInternal(null);
        localStorage.removeItem('mcp-active-api-config-name');
        setMcpServerStatus({ isRunning: false, error: "No active API configuration." });
        addAuditLogEntry('MCP_ACTIVE_API_CONFIG_CLEARED', 'Active API config cleared.');
        localSetError(null);
        return;
    }

    const newActiveConfig = mcpApiConfigs.find(c => c.configName === configName);
    if (newActiveConfig) {
      setActiveApiConfigNameInternal(configName);
      localStorage.setItem('mcp-active-api-config-name', configName);

      setMcpServerStatus({ isRunning: false, error: "API configuration set, but MCP server status not yet fetched." });
      try {
        const status = await getMCPServerStatus();
        setMcpServerStatus(status);
        if (!status.isRunning && status.error) {
          localSetError(`MCP Server (${newActiveConfig.configName}) at ${newActiveConfig.baseApiUrl} Issue: ${status.error}.`);
        } else if (!status.isRunning) {
          localSetError(`MCP Server (${newActiveConfig.configName}) at ${newActiveConfig.baseApiUrl} is not running.`);
        } else {
          localSetError(null);
        }
      } catch (e: any) {
        const errorMsg = `Error fetching status for ${configName}: ${e.message}`;
        localSetError(errorMsg);
        setMcpServerStatus({isRunning: false, error: errorMsg});
        addAuditLogEntry('MCP_STATUS_FETCH_ERROR', errorMsg);
      }

    } else {
      const errorMsg = `Failed to set active API config: ${configName} not found.`;
      localSetError(errorMsg);
      addAuditLogEntry('MCP_ACTIVE_API_CONFIG_ERROR', errorMsg);
    }
  }, [mcpApiConfigs, addAuditLogEntry, localSetError]);


  useEffect(() => {
    localStorage.setItem('app-theme', theme);
    if (theme === Theme.Dark) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    const loadFromLocalStorage = (key: string, setter: Function, itemName: string) => {
        const savedData = localStorage.getItem(key);
        if (savedData) {
            try {
                setter(JSON.parse(savedData));
            } catch (e: any) {
                console.error(`AppContext.tsx: Error parsing ${itemName} from localStorage:`, e.message);
                addAuditLogEntry('LOCALSTORAGE_PARSE_ERROR', `Error parsing ${itemName}: ${e.message}. Data might be lost or reset.`);
            }
        }
    };

    loadFromLocalStorage('app-files', setFiles, 'files');
    loadFromLocalStorage('app-tags', setTags, 'tags');
    loadFromLocalStorage('app-chat', setChatHistory, 'chat history');
    loadFromLocalStorage('app-audit', setAuditLog, 'audit log');
    loadFromLocalStorage('app-wcatCases', setWcatCases, 'WCAT cases');
    loadFromLocalStorage('app-policyManuals', setPolicyManuals, 'policy manuals');
    loadFromLocalStorage('app-chat-sessions', setSavedChatSessions, 'saved chat sessions');
    loadFromLocalStorage('app-selected-tool-ids', setSelectedToolIdsForContext, 'selected tool IDs');
    loadFromLocalStorage('app-selected-file-ids', setSelectedFileIdsForContext, 'selected file IDs');
    loadFromLocalStorage('app-selected-wcat-ids', setSelectedWcatCaseIdsForContext, 'selected WCAT IDs');
    loadFromLocalStorage('app-dynamic-markers', setDynamicMarkersInternal, 'dynamic markers');

    const storedSidebarState = localStorage.getItem('main-sidebar-collapsed');
    if (storedSidebarState) {
        try { setIsMainSidebarCollapsed(JSON.parse(storedSidebarState)); } catch (e: any) { console.error("AppContext.tsx: Error parsing sidebar state from localStorage:", e.message); }
    }
  }, [addAuditLogEntry, localSetError]); // Added addAuditLogEntry and localSetError as they are dependencies

  useEffect(() => { localStorage.setItem('app-files', JSON.stringify(files)); }, [files]);
  useEffect(() => { localStorage.setItem('app-tags', JSON.stringify(tags)); }, [tags]);
  useEffect(() => { localStorage.setItem('app-chat', JSON.stringify(chatHistory)); }, [chatHistory]);
  useEffect(() => { localStorage.setItem('app-audit', JSON.stringify(auditLog)); }, [auditLog]);
  useEffect(() => { localStorage.setItem('app-wcatCases', JSON.stringify(wcatCases)); }, [wcatCases]);
  useEffect(() => { localStorage.setItem('app-policyManuals', JSON.stringify(policyManuals)); }, [policyManuals]);
  useEffect(() => { localStorage.setItem('app-chat-sessions', JSON.stringify(savedChatSessions)); }, [savedChatSessions]);
  useEffect(() => {
    localStorage.setItem('main-sidebar-collapsed', JSON.stringify(isMainSidebarCollapsed));
  }, [isMainSidebarCollapsed]);
  useEffect(() => { localStorage.setItem('app-tools', JSON.stringify(tools)); }, [tools]);
  useEffect(() => { localStorage.setItem('app-selected-tool-ids', JSON.stringify(selectedToolIdsForContext)); }, [selectedToolIdsForContext]);
  useEffect(() => { localStorage.setItem('app-selected-file-ids', JSON.stringify(selectedFileIdsForContext)); }, [selectedFileIdsForContext]);
  useEffect(() => { localStorage.setItem('app-selected-wcat-ids', JSON.stringify(selectedWcatCaseIdsForContext)); }, [selectedWcatCaseIdsForContext]);
  useEffect(() => { localStorage.setItem('app-dynamic-markers', JSON.stringify(dynamicMarkers)); }, [dynamicMarkers]);


  const setApiKey = (key: string | null) => {
    setApiKeyInternal(key);
  };

  useEffect(() => {
    const apiKeyErrorMsg = "Gemini API Key is not set. Please set it in Settings or ensure the API_KEY environment variable was available at startup.";
    if (!apiKey) {
      if (!currentErrorRef.current || (currentErrorRef.current && currentErrorRef.current.includes("Gemini API Key"))) {
        localSetError(apiKeyErrorMsg);
      }
    } else {
      if (currentErrorRef.current && currentErrorRef.current === apiKeyErrorMsg) {
        localSetError(null);
      }
    }
  }, [apiKey, localSetError]);


  const toggleTheme = useCallback(() => {
    setTheme((prevTheme) => (prevTheme === Theme.Light ? Theme.Dark : Theme.Light));
  }, []);

  const toggleMainSidebar = useCallback(() => {
    setIsMainSidebarCollapsed(prev => !prev);
  }, []);

  const extractPolicyReferencesFromFile = useCallback((file: EvidenceFile): PolicyReference[] => {
    const references: PolicyReference[] = [];
    if (!file.content && !file.summary) return references;
    const textToScan = `${file.summary || ''} ${file.content || ''}`;
    const matches = textToScan.matchAll(POLICY_NUMBER_REGEX);

    for (const match of matches) {
        const policyNumber = match[1];
        if (!references.some(r => r.policyNumber === policyNumber)) {
            let foundPolicy: PolicyEntry | undefined;
            let foundManualName: string | undefined;

            for (const manual of policyManuals) {
                foundPolicy = manual.policyEntries.find(pe => pe.policyNumber === policyNumber);
                if (foundPolicy) {
                    foundManualName = manual.manualName;
                    break;
                }
            }
            references.push({
                policyNumber,
                policyTitle: foundPolicy?.title,
                manualVersion: foundManualName
            });
        }
    }
    return references;
  }, [policyManuals]);


  const addFile = useCallback(async (
      fileData: Omit<EvidenceFile, 'id' | 'tags' | 'annotations' | 'mcpPath' | 'isProcessing' | 'referencedPolicies'>,
      mcpPath: string,
      originalFileNameForMcp: string,
      contentForMcp: string
    ): Promise<EvidenceFile | null> => {
    if (!apiKey) {
      localSetError("Gemini API Key is not set. Cannot add file to server.");
      addAuditLogEntry('ADD_FILE_ERROR_NO_API_KEY', `API Key missing for file ${fileData.name}`);
      return null;
    }

    try {
      const successOnMcp = await writeMCPFile(mcpPath, contentForMcp);
      if (!successOnMcp) {
          localSetError(`Failed to write file "${originalFileNameForMcp}" to MCP path "${mcpPath}".`);
          addAuditLogEntry('ADD_FILE_ERROR_MCP_WRITE', `Failed MCP write for ${originalFileNameForMcp} to ${mcpPath}`);
          return null;
      }
      addAuditLogEntry('FILE_WRITTEN_MCP', `File "${originalFileNameForMcp}" written to MCP path "${mcpPath}".`);

      const newFile: EvidenceFile = {
        ...fileData,
        id: uuidv4(),
        tags: [],
        annotations: [],
        mcpPath,
        isProcessing: false,
        metadata: { ...fileData.metadata, createdAt: new Date().toISOString(), modifiedAt: new Date().toISOString() },
        referencedPolicies: []
      };

      const policyRefs = extractPolicyReferencesFromFile(newFile);
      newFile.referencedPolicies = policyRefs;

      setFiles((prevFiles) => [...prevFiles, newFile]);
      addAuditLogEntry('FILE_ADDED_APP', `File "${newFile.name}" added to app. Policies found: ${policyRefs.length}`);
      return newFile;
    } catch (error: any) {
      const errorMsg = `Failed to add file "${fileData.name}" to MCP: ${error.message}`;
      localSetError(errorMsg);
      addAuditLogEntry('ADD_FILE_ERROR_MCP_GENERAL', errorMsg);
      return null;
    }
  }, [apiKey, addAuditLogEntry, extractPolicyReferencesFromFile, localSetError]);

  const updateFile = useCallback((fileId: string, updates: Partial<EvidenceFile>) => {
    setFiles((prevFiles) =>
      prevFiles.map((f) => {
        if (f.id === fileId) {
          const updatedFile = { ...f, ...updates, metadata: {...f.metadata, modifiedAt: new Date().toISOString()} };
          if (updates.content || updates.summary || updates.name) {
            updatedFile.referencedPolicies = extractPolicyReferencesFromFile(updatedFile);
            addAuditLogEntry('FILE_UPDATED_APP', `File ID "${fileId}" updated. Policies re-checked: ${updatedFile.referencedPolicies.length}. Changes: ${Object.keys(updates).join(', ')}`);
          } else {
             addAuditLogEntry('FILE_UPDATED_APP', `File ID "${fileId}" updated. Changes: ${Object.keys(updates).join(', ')}`);
          }
          return updatedFile;
        }
        return f;
      })
    );
  }, [addAuditLogEntry, extractPolicyReferencesFromFile]);

  const deleteFile = useCallback(async (fileId: string): Promise<void> => {
    const fileToDelete = files.find(f => f.id === fileId);
    if (!fileToDelete) return;

    try {
      if (fileToDelete.mcpPath) {
        const successOnMcp = await deleteMCPFile(fileToDelete.mcpPath);
        if (!successOnMcp) {
            localSetError(`Failed to delete file "${fileToDelete.name}" from MCP path "${fileToDelete.mcpPath}". It will only be removed from the app.`);
            addAuditLogEntry('DELETE_FILE_ERROR_MCP', `MCP delete failed for ${fileToDelete.name} at ${fileToDelete.mcpPath}`);
        } else {
             addAuditLogEntry('FILE_DELETED_MCP', `File "${fileToDelete.name}" deleted from MCP path "${fileToDelete.mcpPath}".`);
        }
      }
    } catch (error: any) {
      const errorMsg = `Failed to delete file "${fileToDelete.name}" from MCP: ${error.message}`;
      localSetError(errorMsg);
      addAuditLogEntry('DELETE_FILE_ERROR_MCP_GENERAL', errorMsg);
    }

    setFiles((prevFiles) => prevFiles.filter((f) => f.id !== fileId));
    setDynamicMarkersInternal(prev => {
        const newMarkers = {...prev};
        delete newMarkers[fileId];
        return newMarkers;
    });
    addAuditLogEntry('FILE_DELETED_APP', `File "${fileToDelete.name}" (ID: ${fileId}) deleted from app.`);
  }, [files, addAuditLogEntry, localSetError]);

  const getFileById = useCallback((fileId: string) => {
    return files.find(f => f.id === fileId);
  }, [files]);

  const addTag = useCallback((tagData: Omit<Tag, 'id'>): Tag => {
    const existingTag = tags.find(t => t.name.toLowerCase() === tagData.name.toLowerCase() && t.scope === tagData.scope && t.criteria === tagData.criteria);
    if (existingTag) return existingTag;

    const newTag: Tag = { ...tagData, id: uuidv4() };
    setTags((prevTags) => [...prevTags, newTag]);
    addAuditLogEntry('TAG_CREATED', `Tag "${newTag.name}" (Scope: ${newTag.scope || 'N/A'}) created.`);
    return newTag;
  }, [tags, addAuditLogEntry]);

  const removeTagFromFile = useCallback((fileId: string, tagId: string) => {
    setFiles(prevFiles => prevFiles.map(file => {
      if (file.id === fileId) {
        return { ...file, tags: file.tags.filter(tag => tag.id !== tagId) };
      }
      return file;
    }));
    const tagName = tags.find(t => t.id === tagId)?.name || 'Unknown Tag';
    addAuditLogEntry('TAG_REMOVED_FROM_FILE', `Tag "${tagName}" removed from file ID "${fileId}".`);
  }, [tags, addAuditLogEntry]);

  const addTagToFile = useCallback((fileId: string, tag: Tag) => {
    setFiles(prevFiles => prevFiles.map(file => {
      if (file.id === fileId && !file.tags.find(t => t.id === tag.id)) {
        return { ...file, tags: [...file.tags, tag] };
      }
      return file;
    }));
    addAuditLogEntry('TAG_ADDED_TO_FILE', `Tag "${tag.name}" added to file ID "${fileId}".`);
  }, [addAuditLogEntry]);

  const addChatMessage = useCallback((messageData: Omit<ChatMessage, 'id' | 'timestamp'>): ChatMessage => {
    const newMessage: ChatMessage = {
      ...messageData,
      id: uuidv4(),
      timestamp: new Date().toISOString(),
    };
    setChatHistory((prevHistory) => [...prevHistory, newMessage]);
    return newMessage;
  }, []);

  const clearChatHistory = useCallback(() => {
    setChatHistory([]);
    setSelectedFileIdsForContext([]);
    setSelectedWcatCaseIdsForContext([]);
    setSelectedToolIdsForContext([]);
    // TODO: Implement chat session reset through AG-UI backend
    // resetGeminiChatSession() - replaced with backend call
    addAuditLogEntry('CHAT_CLEARED', 'Chat history, AI session, and all context items cleared.');
  }, [addAuditLogEntry]);

  const getWcatCaseById = useCallback((id: string) => {
    return wcatCases.find(c => c.id === id);
  }, [wcatCases]);

  const addWcatCase = useCallback(async (caseData: Omit<WcatCase, 'id' | 'ingestedAt' | 'tags'>, fetchedPatternTags?: Tag[]): Promise<WcatCase> => {
    const newCase: WcatCase = {
      ...caseData,
      id: caseData.decisionNumber,
      ingestedAt: new Date().toISOString(),
      tags: fetchedPatternTags || [],
    };
    setWcatCases((prevCases) => {
      const existingIndex = prevCases.findIndex(c => c.decisionNumber === newCase.decisionNumber);
      if (existingIndex !== -1) {
        addAuditLogEntry('WCAT_CASE_UPDATED_ON_ADD', `WCAT Case "${newCase.decisionNumber}" updated as it already existed.`);
        const updatedCases = [...prevCases];
        updatedCases[existingIndex] = { ...prevCases[existingIndex], ...newCase };
        return updatedCases;
      }
      addAuditLogEntry('WCAT_CASE_ADDED', `WCAT Case "${newCase.decisionNumber}" added to database. MCP Path: ${newCase.mcpPath || 'N/A'}`);
      return [...prevCases, newCase];
    });
    return newCase;
  }, [addAuditLogEntry]);

  const updateWcatCase = useCallback((caseId: string, updates: Partial<WcatCase>) => {
    setWcatCases((prevCases) =>
      prevCases.map((c) => (c.id === caseId ? { ...c, ...updates } : c))
    );
    addAuditLogEntry('WCAT_CASE_UPDATED', `WCAT Case ID "${caseId}" updated. Changes: ${Object.keys(updates).join(', ')}`);
  }, [addAuditLogEntry]);

  const deleteWcatCase = useCallback(async (caseId: string): Promise<void> => {
    const caseToDelete = wcatCases.find(c => c.id === caseId);
    if (!caseToDelete) return;

    try {
      if (caseToDelete.mcpPath) {
        const successOnMcp = await deleteMCPFile(caseToDelete.mcpPath);
        if (!successOnMcp) {
            localSetError(`Failed to delete WCAT case file "${caseToDelete.decisionNumber}" from MCP path "${caseToDelete.mcpPath}". It will only be removed from the app database.`);
            addAuditLogEntry('DELETE_WCAT_FILE_ERROR_MCP', `MCP delete failed for WCAT ${caseToDelete.decisionNumber} at ${caseToDelete.mcpPath}`);
        } else {
             addAuditLogEntry('WCAT_FILE_DELETED_MCP', `WCAT case file "${caseToDelete.decisionNumber}" deleted from MCP path "${caseToDelete.mcpPath}".`);
        }
      }
    } catch (error: any) {
      const errorMsg = `Failed to delete WCAT case file "${caseToDelete.decisionNumber}" from MCP: ${error.message}`;
      localSetError(errorMsg);
      addAuditLogEntry('DELETE_WCAT_FILE_ERROR_MCP_GENERAL', errorMsg);
    }

    setWcatCases((prevCases) => prevCases.filter((c) => c.id !== caseId));
    addAuditLogEntry('WCAT_CASE_DELETED_APP', `WCAT Case "${caseToDelete.decisionNumber}" (ID: ${caseId}) deleted from app.`);
  }, [wcatCases, addAuditLogEntry, localSetError]);

  const generateAndAssignWcatPatternTags = useCallback(async (caseId: string): Promise<void> => {
    if (!apiKey) {
      localSetError("Cannot generate WCAT patterns: Gemini API Key is not set.");
      return;
    }
    const targetCase = wcatCases.find(c => c.id === caseId);
    if (!targetCase || !targetCase.rawTextContent) {
      localSetError(`Cannot generate WCAT patterns: Case ${caseId} not found or has no raw text content.`);
      return;
    }

    setIsLoading(true);
    try {
      addAuditLogEntry('WCAT_PATTERN_GEN_START', `Starting pattern generation for WCAT case ${targetCase.decisionNumber}`);
      // TODO: Implement WCAT pattern identification through AG-UI backend
    // const patternStrings = await identifyWcatCasePatterns(targetCase.rawTextContent);
    const patternStrings: string[] = []; // Placeholder until backend implementation
      const patternTags: Tag[] = [];
      for (const pStr of patternStrings) {
        const tag = addTag({ name: pStr, color: DEFAULT_WCAT_PATTERN_TAG_COLOR, criteria: 'wcat_pattern_generic', scope: 'wcat_pattern' });
        patternTags.push(tag);
      }
      updateWcatCase(caseId, { tags: [...(targetCase.tags || []), ...patternTags].filter((t, i, self) => self.findIndex(s => s.id === t.id) === i) });
      addAuditLogEntry('WCAT_PATTERN_GEN_SUCCESS', `Patterns generated for ${targetCase.decisionNumber}: ${patternStrings.join(', ')}`);
    } catch (error: any) {
      localSetError(`Failed to generate WCAT patterns for ${targetCase.decisionNumber}: ${error.message}`);
      addAuditLogEntry('WCAT_PATTERN_GEN_ERROR', `Error for ${targetCase.decisionNumber}: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [wcatCases, apiKey, addTag, updateWcatCase, localSetError, setIsLoading, addAuditLogEntry]);


  const getWcatCaseByDecisionNumber = useCallback((decisionNumber: string) => {
    return wcatCases.find(c => c.decisionNumber === decisionNumber);
  }, [wcatCases]);

  const addPolicyManual = useCallback(async (
      manualInfo: { manualName: string; sourceUrl?: string; version?: string },
      pdfContentString: string,
      originalFileName: string
    ): Promise<PolicyManual | null> => {
    if (!apiKey) {
      localSetError("Gemini API Key is not set. Cannot add policy manual.");
      addAuditLogEntry('ADD_POLICY_MANUAL_ERROR_NO_API_KEY', `API Key missing for manual ${manualInfo.manualName}`);
      return null;
    }

    try {
      const manualId = uuidv4();
      const mcpPath = `/policy_manuals/${manualId}_${originalFileName.replace(/[^a-zA-Z0-9_.-]/g, '_')}`;

      const mcpSuccess = await writeMCPFile(mcpPath, pdfContentString);
      if (!mcpSuccess) {
          localSetError(`Failed to write policy manual "${manualInfo.manualName}" to MCP path "${mcpPath}".`);
          addAuditLogEntry('ADD_POLICY_MANUAL_ERROR_MCP_WRITE', `Failed MCP write for ${manualInfo.manualName} to ${mcpPath}`);
          return null;
      }
      addAuditLogEntry('POLICY_MANUAL_WRITTEN_MCP', `Manual "${manualInfo.manualName}" written to MCP path "${mcpPath}".`);

      const rawTextContent = pdfContentString;

      setIsLoading(true);
      let policyEntries: PolicyEntry[] = [];
      try {
          addAuditLogEntry('POLICY_MANUAL_INDEXING_START', `AI indexing started for manual ${manualInfo.manualName}`);
          // TODO: Implement policy extraction through AG-UI backend
        // policyEntries = await extractPolicyEntriesFromManualText(rawTextContent, manualInfo.manualName);
        policyEntries = []; // Placeholder until backend implementation
          addAuditLogEntry('POLICY_MANUAL_INDEXING_SUCCESS', `AI indexing complete for ${manualInfo.manualName}. Found ${policyEntries.length} entries.`);
      } catch(error: any) {
          localSetError(`AI failed to index policy manual ${manualInfo.manualName}: ${error.message}`);
          addAuditLogEntry('POLICY_MANUAL_INDEXING_ERROR', `AI indexing error for ${manualInfo.manualName}: ${error.message}`);
      } finally {
          setIsLoading(false);
      }

      const newManual: PolicyManual = {
        id: manualId,
        manualName: manualInfo.manualName,
        sourceUrl: manualInfo.sourceUrl,
        version: manualInfo.version,
        mcpPath,
        rawTextContent,
        policyEntries,
        ingestedAt: new Date().toISOString(),
        isProcessing: false,
      };

      setPolicyManuals(prevManuals => [...prevManuals, newManual]);
      addAuditLogEntry('POLICY_MANUAL_ADDED_APP', `Policy Manual "${newManual.manualName}" added to app.`);
      return newManual;
    } catch (error: any) {
      const errorMsg = `Failed to add policy manual "${manualInfo.manualName}": ${error.message}`;
      localSetError(errorMsg);
      addAuditLogEntry('ADD_POLICY_MANUAL_ERROR_GENERAL', errorMsg);
      return null;
    }
  }, [apiKey, addAuditLogEntry, localSetError, setIsLoading]);

  const deletePolicyManual = useCallback(async (manualId: string): Promise<void> => {
    const manualToDelete = policyManuals.find(m => m.id === manualId);
    if (!manualToDelete) return;

    try {
      const successOnMcp = await deleteMCPFile(manualToDelete.mcpPath);
      if (!successOnMcp) {
          localSetError(`Failed to delete policy manual "${manualToDelete.manualName}" from MCP. It will only be removed from app.`);
          addAuditLogEntry('DELETE_POLICY_MANUAL_ERROR_MCP', `MCP delete failed for ${manualToDelete.manualName}`);
      } else {
           addAuditLogEntry('POLICY_MANUAL_DELETED_MCP', `Manual "${manualToDelete.manualName}" deleted from MCP.`);
      }
    } catch (error: any) {
      const errorMsg = `Failed to delete policy manual "${manualToDelete.manualName}" from MCP: ${error.message}`;
      localSetError(errorMsg);
      addAuditLogEntry('DELETE_POLICY_MANUAL_ERROR_GENERAL', errorMsg);
    }
    setPolicyManuals(prevManuals => prevManuals.filter(m => m.id !== manualId));
    addAuditLogEntry('POLICY_MANUAL_DELETED_APP', `Policy Manual "${manualToDelete.manualName}" deleted from app.`);
  }, [policyManuals, addAuditLogEntry, localSetError]);

  const getPolicyManualById = useCallback((manualId: string) => {
    return policyManuals.find(m => m.id === manualId);
  }, [policyManuals]);

  const getPolicyEntry = useCallback((manualId: string, policyNumber: string): PolicyEntry | undefined => {
    const manual = policyManuals.find(m => m.id === manualId);
    return manual?.policyEntries.find(pe => pe.policyNumber === policyNumber);
  }, [policyManuals]);

  const findRelevantWcatCases = useCallback(async (queryText: string, associatedFile?: EvidenceFile): Promise<WcatCase[]> => {
    const queryLower = queryText.toLowerCase();
    const queryKeywords = queryLower.split(/\s+/).filter(kw => kw.length > 2);

    let fileKeywords: string[] = [];
    let filePolicyNumbers: string[] = [];

    if (associatedFile) {
        if (associatedFile.summary) {
            fileKeywords.push(...associatedFile.summary.toLowerCase().split(/\s+/).filter(kw => kw.length > 2));
        }
        if (associatedFile.referencedPolicies) {
            filePolicyNumbers.push(...associatedFile.referencedPolicies.map(p => p.policyNumber));
        }
    }
    const allSearchKeywords = [...new Set([...queryKeywords, ...fileKeywords])];

    const scoredCases = wcatCases.map(wcase => {
        let score = 0;
        const caseText = `${wcase.aiSummary.toLowerCase()} ${wcase.keywords.join(' ').toLowerCase()} ${wcase.outcomeSummary.toLowerCase()} ${wcase.tags.map(t => t.name).join(' ').toLowerCase()}`;

        allSearchKeywords.forEach(kw => {
            if (caseText.includes(kw)) score += 1;
        });

        wcase.referencedPolicies.forEach(pol => {
            if (filePolicyNumbers.includes(pol.policyNumber)) score += 5;
            if (queryLower.includes(pol.policyNumber.toLowerCase())) score += 3;
        });

        wcase.tags.forEach(tag => {
            if (tag.scope === 'wcat_pattern' && queryLower.includes(tag.name.toLowerCase())) {
                score += 2;
            }
        });

        return { wcase, score };
    });

    return scoredCases.filter(item => item.score > 0)
                      .sort((a, b) => b.score - a.score)
                      .slice(0, 10)
                      .map(item => item.wcase);
  }, [wcatCases]);

  const saveChatSession = useCallback((name: string, messagesToSave: ChatMessage[], fileIds?: string[], wcatIds?: string[], toolIds?: string[]) => {
    const newSession: SavedChatSession = {
        id: uuidv4(),
        name,
        timestamp: new Date().toISOString(),
        messages: messagesToSave,
        relatedFileIds: fileIds,
        relatedWcatCaseIds: wcatIds,
        relatedToolIds: toolIds,
    };
    setSavedChatSessions(prev => [newSession, ...prev]);
    addAuditLogEntry('CHAT_SESSION_SAVED', `Session "${name}" saved with ${messagesToSave.length} messages.`);
  }, [addAuditLogEntry]);

  const loadChatSession = useCallback((sessionId: string): SavedChatSession | null => {
    const sessionToLoad = savedChatSessions.find(s => s.id === sessionId);
    if (sessionToLoad) {
        setChatHistory(sessionToLoad.messages);
        setSelectedFileIdsForContext(sessionToLoad.relatedFileIds || []);
        setSelectedWcatCaseIdsForContext(sessionToLoad.relatedWcatCaseIds || []);
        setSelectedToolIdsForContext(sessionToLoad.relatedToolIds || []);
        // TODO: Implement chat session reset through AG-UI backend
      // resetGeminiChatSession() - replaced with backend call
        addAuditLogEntry('CHAT_SESSION_LOADED', `Session "${sessionToLoad.name}" loaded.`);
        return sessionToLoad;
    }
    addAuditLogEntry('CHAT_SESSION_LOAD_FAILED', `Session ID "${sessionId}" not found.`);
    return null;
  }, [savedChatSessions, addAuditLogEntry]);

  const deleteChatSession = useCallback((sessionId: string) => {
    const sessionToDelete = savedChatSessions.find(s => s.id === sessionId);
    if (sessionToDelete) {
        setSavedChatSessions(prev => prev.filter(s => s.id !== sessionId));
        addAuditLogEntry('CHAT_SESSION_DELETED', `Session "${sessionToDelete.name}" (ID: ${sessionId}) deleted.`);
    }
  }, [savedChatSessions, addAuditLogEntry]);

  // AI Tool functions
  const addTool = useCallback((toolData: Omit<AiTool, 'id' | 'type' | 'mcpProcessDetails'>, type: 'custom_abstract' = 'custom_abstract'): AiTool => {
    const newTool: AiTool = {
        ...toolData,
        id: uuidv4(),
        type: type,
    };
    setTools(prevTools => [...prevTools, newTool]);
    addAuditLogEntry('AI_TOOL_ADDED', `Custom tool "${newTool.name}" added.`);
    return newTool;
  }, [addAuditLogEntry]);

  const deleteTool = useCallback((toolId: string) => {
    setTools(prevTools => {
        const toolToDelete = prevTools.find(t => t.id === toolId);
        if (toolToDelete && toolToDelete.type === 'custom_abstract') {
            addAuditLogEntry('AI_TOOL_DELETED', `Custom tool "${toolToDelete.name}" deleted.`);
            return prevTools.filter(t => t.id !== toolId);
        }
        addAuditLogEntry('AI_TOOL_DELETE_FAILED', `Failed to delete tool ID ${toolId} (not found or not custom).`);
        return prevTools;
    });
    setSelectedToolIdsForContext(prev => prev.filter(id => id !== toolId));
  }, [addAuditLogEntry]);

  const toggleToolContext = useCallback((toolId: string) => {
    setSelectedToolIdsForContext(prev =>
        prev.includes(toolId) ? prev.filter(id => id !== toolId) : [...prev, toolId]
    );
    const toolName = tools.find(t => t.id === toolId)?.name || toolId;
    addAuditLogEntry('AI_TOOL_CONTEXT_TOGGLED', `Tool "${toolName}" context toggled.`);
  }, [tools, addAuditLogEntry]);

  // Chat Context Selection Functions
  const toggleFileContext = useCallback((fileId: string) => {
    setSelectedFileIdsForContext(prev =>
      prev.includes(fileId) ? prev.filter(id => id !== fileId) : [...prev, fileId]
    );
    const fileName = files.find(f => f.id === fileId)?.name || fileId;
    addAuditLogEntry('AI_FILE_CONTEXT_TOGGLED', `File "${fileName}" context toggled.`);
  }, [files, addAuditLogEntry]);

  const toggleWcatCaseContext = useCallback((caseId: string) => {
    setSelectedWcatCaseIdsForContext(prev =>
      prev.includes(caseId) ? prev.filter(id => id !== caseId) : [...prev, caseId]
    );
    const caseName = wcatCases.find(c => c.id === caseId)?.decisionNumber || caseId;
    addAuditLogEntry('AI_WCAT_CONTEXT_TOGGLED', `WCAT Case "${caseName}" context toggled.`);
  }, [wcatCases, addAuditLogEntry]);

  const setDynamicMarkersForFile = useCallback((fileId: string, markers: DynamicMarker[]) => {
    setDynamicMarkersInternal(prev => ({ ...prev, [fileId]: markers }));
    addAuditLogEntry('DYNAMIC_MARKERS_SET', `Dynamic markers updated for file ID ${fileId}. Count: ${markers.length}.`);
  }, [addAuditLogEntry]);

  console.log("AppContext.tsx: AppProvider component function ENDING. Rendering children.");
  return (
    <AppContext.Provider value={{
      theme, toggleTheme,
      files, addFile, updateFile, deleteFile, getFileById,
      tags, addTag, removeTagFromFile, addTagToFile,
      chatHistory, addChatMessage, clearChatHistory,
      auditLog, addAuditLogEntry,
      mcpServerStatus, setMcpServerStatus, refreshMcpStatus,
      isLoading, setIsLoading,
      currentError, setError: localSetError,
      apiKey, setApiKey,
      wcatCases, addWcatCase, updateWcatCase, deleteWcatCase, getWcatCaseByDecisionNumber, getWcatCaseById,
      policyManuals, addPolicyManual, deletePolicyManual, getPolicyManualById, getPolicyEntry,
      findRelevantWcatCases, extractPolicyReferencesFromFile,
      generateAndAssignWcatPatternTags,
      isMainSidebarCollapsed, toggleMainSidebar,
      savedChatSessions, saveChatSession, loadChatSession, deleteChatSession,
      userMcpServerDefinitions, mcpApiConfigs, activeApiConfigName, setActiveApiConfig, updateMcpApiConfigs,
      tools, addTool, deleteTool, selectedToolIdsForContext, toggleToolContext,
      selectedFileIdsForContext, toggleFileContext,
      selectedWcatCaseIdsForContext, toggleWcatCaseContext,
      dynamicMarkers, setDynamicMarkersForFile
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
