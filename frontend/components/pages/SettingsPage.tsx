import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../contexts/AppContext';
import { Theme, AuditLogEntry, McpServerStatus, McpApiConfig } from '../../types';
import ToggleSwitch from '../ui/ToggleSwitch';
// Remove direct geminiService import - use AG-UI backend instead
import LoadingSpinner from '../ui/LoadingSpinner';
import { getMCPServerStatus } from '../../contexts/AppContextHelper';

const SettingsPage: React.FC = () => {
  const {
    theme, toggleTheme, auditLog, addAuditLogEntry,
    mcpServerStatus: contextMcpStatus, setMcpServerStatus,
    apiKey: currentApiKey, setApiKey: setContextApiKey,
    setError, // mcpClient and isMcpClientLoading removed - using backend API
    mcpApiConfigs, activeApiConfigName,
    setActiveApiConfig, updateMcpApiConfigs
  } = useAppContext();

  const [newAllowedDir, setNewAllowedDir] = useState('');
  const [localApiKey, setLocalApiKey] = useState(currentApiKey || '');
  const [isTestingApiKey, setIsTestingApiKey] = useState(false);
  const [apiKeyTestResult, setApiKeyTestResult] = useState<string | null>(null);
  const [currentMcpStatus, setCurrentMcpStatus] = useState<McpServerStatus>(contextMcpStatus);

  const [apiConfigsJson, setApiConfigsJson] = useState<string>('');
  const [selectedActiveConfigInDropdown, setSelectedActiveConfigInDropdown] = useState<string>(activeApiConfigName || '');
  const [importedFileError, setImportedFileError] = useState<string | null>(null);
  const [mcpConfigJson, setMcpConfigJson] = useState<string>('');

  useEffect(() => {
    setCurrentMcpStatus(contextMcpStatus);
  }, [contextMcpStatus]);

  useEffect(() => {
    setApiConfigsJson(JSON.stringify(mcpApiConfigs, null, 2));
    setSelectedActiveConfigInDropdown(activeApiConfigName || (mcpApiConfigs.length > 0 ? mcpApiConfigs[0].configName : ''));
  }, [mcpApiConfigs, activeApiConfigName]);


  const fetchMcpStatus = async () => {
    try {
      // Use backend API instead of direct MCP client
      const status = await getMCPServerStatus();
      const mcpStatus = {
        isRunning: status.isRunning,
        error: status.error || undefined,
        version: status.version,
        allowedDirectories: status.allowedDirectories || []
      };
      setMcpServerStatus(mcpStatus);
      setCurrentMcpStatus(mcpStatus);
    } catch (err: any) {
      setError(`Failed to refresh MCP server status: ${err.message}`);
      const errorStatus = { isRunning: false, error: err.message };
      setMcpServerStatus(errorStatus);
      setCurrentMcpStatus(errorStatus);
    }
  };

  useEffect(() => {
    // Fetch MCP status on component mount using backend API
    fetchMcpStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run on mount


  const handleAddDirectory = async () => {
    if (newAllowedDir.trim() === '') {
        setError("Directory path cannot be empty.");
        return;
    }
    try {
      // TODO: Implement add directory functionality through backend API
      // For now, just show a placeholder message
      addAuditLogEntry('MCP_DIRECTORY_ADD_REQUESTED', `Directory "${newAllowedDir}" add request (backend implementation pending).`);
      setNewAllowedDir('');
      await fetchMcpStatus();
      setError("Add directory functionality will be implemented through backend API.");
    } catch (err: any) {
      setError(`Error processing add directory request: ${err.message}`);
    }
  };

  const handleApiKeySave = async () => {
    setIsTestingApiKey(true);
    setApiKeyTestResult(null);
    setError(null);

    try {
      // Test API key through AG-UI backend instead of direct frontend call
      const response = await fetch('http://localhost:10200/api/test-api-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: 'google',
          apiKey: localApiKey,
          model: 'gemini-1.5-flash' // Use stable model for testing
        }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setContextApiKey(localApiKey);
        setApiKeyTestResult("API Key is valid and saved!");
        addAuditLogEntry('API_KEY_UPDATED', 'Google API Key tested and updated successfully via backend.');
      } else {
        const errorMsg = result.message || "API Key test failed. Please check your key and try again.";
        setApiKeyTestResult(errorMsg);
        setError(errorMsg);
        addAuditLogEntry('API_KEY_TEST_FAILED', `API Key test failed: ${errorMsg}`);
      }
    } catch (error) {
      const errorMsg = `Error testing API key: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setApiKeyTestResult(errorMsg);
      setError(errorMsg);
      addAuditLogEntry('API_KEY_TEST_ERROR', errorMsg);
    }

    setIsTestingApiKey(false);
  };

  const handleSaveApiConfigs = async () => {
    setError(null);
    setImportedFileError(null);
    try {
      const parsedConfigs: McpApiConfig[] = JSON.parse(apiConfigsJson);
      if (!Array.isArray(parsedConfigs) || !parsedConfigs.every(c => c.configName && c.baseApiUrl && c.endpoints)) {
        throw new Error("Invalid JSON structure. Ensure it's an array of McpApiConfig objects, each with configName, baseApiUrl, and endpoints.");
      }

      updateMcpApiConfigs(parsedConfigs); // Update the list in context first

      let configNameToActivate: string | null = null;
      if (parsedConfigs.length > 0) {
        // Try to keep current selection if valid, otherwise pick first
        const currentSelectionIsValid = parsedConfigs.find(c => c.configName === selectedActiveConfigInDropdown);
        if (currentSelectionIsValid) {
          configNameToActivate = selectedActiveConfigInDropdown;
        } else {
          configNameToActivate = parsedConfigs[0].configName;
        }
      }
      // If parsedConfigs.length is 0, configNameToActivate remains null

      await setActiveApiConfig(configNameToActivate); // This will handle null correctly

      // Sync local dropdown state with what was actually activated
      setSelectedActiveConfigInDropdown(configNameToActivate || '');

      if (configNameToActivate) {
        // alert("API Configurations saved and applied!"); // Optional: replace with a more subtle notification
        addAuditLogEntry('MCP_API_CONFIGS_SAVED_UI', `${parsedConfigs.length} API configurations saved. Active: ${configNameToActivate}.`);
      } else {
        setError("API Configurations saved, but no configurations are available to make active.");
        addAuditLogEntry('MCP_API_CONFIGS_SAVED_UI_EMPTY', 'API configurations saved (empty list). Active config cleared.');
      }

    } catch (e: any) {
      const errorMsg = `Error saving API configurations: ${e.message}. Please ensure it's valid JSON.`;
      setError(errorMsg);
      addAuditLogEntry('MCP_API_CONFIGS_SAVE_ERROR_UI', errorMsg);
    }
  };

  const handleActiveApiConfigChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newActiveName = e.target.value;
    setSelectedActiveConfigInDropdown(newActiveName); // Update local state for dropdown
    if (newActiveName) { // Only call setActiveApiConfig if a valid name is selected
        await setActiveApiConfig(newActiveName);
    } else { // If dropdown selection becomes empty (e.g. "No API configurations loaded")
        await setActiveApiConfig(null);
    }
  };

  const handleImportApiConfigsFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    setImportedFileError(null);
    setError(null);
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const rawData = JSON.parse(text);
        let parsedData: McpApiConfig[] = [];

        // Check if it's a standard MCP client configuration
        if (rawData.mcpServers && typeof rawData.mcpServers === 'object') {
          // Convert standard MCP configuration to McpApiConfig format
          parsedData = Object.entries(rawData.mcpServers).map(([serverName, serverConfig]: [string, any]) => {
            const config: McpApiConfig = {
              configName: serverName,
              transportType: serverConfig.type === 'stdio' ? 'stdio' : 'http'
            };

            if (serverConfig.type === 'stdio') {
              config.stdioOptions = {
                command: serverConfig.command,
                args: serverConfig.args || [],
                cwd: serverConfig.cwd,
                env: serverConfig.env
              };
            } else {
              // For HTTP or other types, try to infer baseApiUrl
              config.baseApiUrl = serverConfig.baseApiUrl || `http://localhost:8080`;
              config.endpoints = serverConfig.endpoints || {};
            }

            return config;
          });

          addAuditLogEntry('MCP_STANDARD_CONFIG_CONVERTED', `Converted standard MCP configuration with ${parsedData.length} servers.`);
        }
        // Check if it's already in McpApiConfig array format
        else if (Array.isArray(rawData)) {
          parsedData = rawData;

          // Validate McpApiConfig format
          if (parsedData.length > 0 && !parsedData.every(c => c.configName)) {
            throw new Error("Invalid McpApiConfig array: Each object must have at least 'configName'.");
          }
        }
        else {
          throw new Error("Imported file must be either a standard MCP client configuration (with 'mcpServers' property) or an array of McpApiConfig objects.");
        }

        setApiConfigsJson(JSON.stringify(parsedData, null, 2));
        addAuditLogEntry('MCP_API_CONFIGS_FILE_PREPARED', `Configurations from file ${file.name} loaded into editor (${parsedData.length} configs).`);
        alert(`Configurations from "${file.name}" loaded into the editor. ${Array.isArray(rawData) ? 'Direct format detected.' : 'Standard MCP format converted.'} Review and click "Save & Apply" to persist.`);
      } catch (err: any) {
        const errorMsg = `Error processing imported file "${file.name}": ${err.message}`;
        setImportedFileError(errorMsg);
        setError(errorMsg); // Also show in global error display
        addAuditLogEntry('MCP_API_CONFIGS_FILE_IMPORT_ERROR', errorMsg);
      }
    };
    reader.onerror = () => {
      const errorMsg = `Error reading file "${file.name}".`;
      setImportedFileError(errorMsg);
      setError(errorMsg);
      addAuditLogEntry('MCP_API_CONFIGS_FILE_READ_ERROR', errorMsg);
    }
    reader.readAsText(file);
    event.target.value = ''; // Reset file input
  };

  const handleLoadMcpConfig = async () => {
    try {
      setError(null);
      const response = await fetch('http://localhost:10200/api/mcp-config', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const configData = await response.text();
        setMcpConfigJson(configData);
        addAuditLogEntry('MCP_CONFIG_LOADED', 'MCP configuration loaded from backend.');
      } else {
        throw new Error(`Failed to load MCP config: ${response.statusText}`);
      }
    } catch (error: any) {
      const errorMsg = `Error loading MCP config: ${error.message}`;
      setError(errorMsg);
      addAuditLogEntry('MCP_CONFIG_LOAD_ERROR', errorMsg);
    }
  };

  const handleSaveMcpConfig = async () => {
    try {
      setError(null);
      // Validate JSON first
      JSON.parse(mcpConfigJson);

      const response = await fetch('http://localhost:10200/api/mcp-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: mcpConfigJson })
      });

      if (response.ok) {
        addAuditLogEntry('MCP_CONFIG_SAVED', 'MCP configuration saved to backend.');
        alert('MCP configuration saved successfully!');
      } else {
        throw new Error(`Failed to save MCP config: ${response.statusText}`);
      }
    } catch (error: any) {
      const errorMsg = `Error saving MCP config: ${error.message}`;
      setError(errorMsg);
      addAuditLogEntry('MCP_CONFIG_SAVE_ERROR', errorMsg);
    }
  };

  const handleImportMcpFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    setImportedFileError(null);
    setError(null);
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        // Validate it's valid JSON
        JSON.parse(text);
        setMcpConfigJson(text);
        addAuditLogEntry('MCP_CONFIG_FILE_IMPORTED', `MCP configuration from file ${file.name} loaded into editor.`);
        alert(`MCP configuration from "${file.name}" loaded into editor.`);
      } catch (err: any) {
        const errorMsg = `Error processing MCP file "${file.name}": ${err.message}`;
        setImportedFileError(errorMsg);
        setError(errorMsg);
        addAuditLogEntry('MCP_CONFIG_FILE_IMPORT_ERROR', errorMsg);
      }
    };
    reader.onerror = () => {
      const errorMsg = `Error reading file "${file.name}".`;
      setImportedFileError(errorMsg);
      setError(errorMsg);
      addAuditLogEntry('MCP_CONFIG_FILE_READ_ERROR', errorMsg);
    };
    reader.readAsText(file);
    event.target.value = ''; // Reset file input
  };

  const activeConfigDetails = mcpApiConfigs.find(c => c.configName === activeApiConfigName);

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto">
      <h2 className="text-3xl font-semibold text-textPrimary">Settings</h2>

      <section className="bg-surface p-6 rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
        <h3 className="text-xl font-semibold text-textPrimary mb-4">Appearance</h3>
        <div className="flex items-center justify-between">
          <span className="text-textSecondary">Theme</span>
          <ToggleSwitch
            id="theme-toggle"
            checked={theme === Theme.Dark}
            onChange={() => toggleTheme()}
            label={theme === Theme.Dark ? 'Dark Mode' : 'Light Mode'}
          />
        </div>
      </section>

      <section className="bg-surface p-6 rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
        <h3 className="text-xl font-semibold text-textPrimary mb-4">LLM Provider API Key</h3>
        <p className="text-sm text-textSecondary mb-2">
          API keys are managed by the backend through the <code className="bg-background px-1 rounded">.env</code> file (GOOGLE_API_KEY, OPENAI_API_KEY, etc.).
          You can test the current Google API key here. Changes are for the current session only.
        </p>
        <div className="flex flex-col sm:flex-row gap-2 items-start">
          <input
            type="password"
            value={localApiKey}
            onChange={(e) => setLocalApiKey(e.target.value)}
            placeholder="Enter API Key to test (Google/Gemini)"
            className="flex-grow mt-1 block w-full px-3 py-2 bg-background border border-border rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
          />
          <button
            onClick={handleApiKeySave}
            disabled={isTestingApiKey || !localApiKey}
            className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50 whitespace-nowrap"
          >
            {isTestingApiKey ? <LoadingSpinner size="sm" /> : 'Test via Backend'}
          </button>
        </div>
        {apiKeyTestResult && (
          <p className={`mt-2 text-sm ${apiKeyTestResult.includes('invalid') ? 'text-red-500' : 'text-green-500'}`}>
            {apiKeyTestResult}
          </p>
        )}
         {!currentApiKey && !localApiKey && (
           <p className="mt-2 text-sm text-yellow-600 dark:text-yellow-400">
             No API Key set for testing. The backend uses keys from .env file (GOOGLE_API_KEY, etc.).
           </p>
         )}
      </section>

      <section className="bg-surface p-6 rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
        <h3 className="text-xl font-semibold text-textPrimary mb-2">MCP Server Connection & Status</h3>

        <div className="mb-4">
            <label htmlFor="active-api-config" className="block text-sm font-medium text-textSecondary">Active API Connection Profile</label>
            <select
                id="active-api-config"
                value={selectedActiveConfigInDropdown}
                onChange={handleActiveApiConfigChange}
                disabled={mcpApiConfigs.length === 0}
                className="mt-1 block w-full px-3 py-2 bg-background border border-border rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            >
                {mcpApiConfigs.length === 0 && <option value="">No API configurations loaded</option>}
                {mcpApiConfigs.map(conf => (
                    <option key={conf.configName} value={conf.configName}>{conf.configName}</option>
                ))}
            </select>
        </div>

        <h4 className="text-lg font-medium text-textPrimary mt-4 mb-1">Server Status (using "{selectedActiveConfigInDropdown || 'N/A'}")</h4>
        {/* MCP client loading status removed - status comes from backend API */}
        <div className="text-sm space-y-1 text-textSecondary">
          <p>Status: {currentMcpStatus.isRunning ?
            <span className="text-green-500 font-semibold">Running</span> :
            <span className="text-red-500 font-semibold">Not Running {currentMcpStatus.error ? `(${currentMcpStatus.error.substring(0,150)}${currentMcpStatus.error.length > 150 ? '...' : ''})` : ''}</span>}
          </p>
          {currentMcpStatus.isRunning && <p>Reported Server Version: {currentMcpStatus.version || 'N/A'}</p>}
          {activeConfigDetails && (
            <>
              <p>Expected Server Version: {activeConfigDetails.expectedServerVersion || 'Any'}</p>
              <p>Request Timeout: {activeConfigDetails.requestTimeoutMs ? `${activeConfigDetails.requestTimeoutMs} ms` : 'Default (Browser)'}</p>
            </>
          )}
          <p className="font-medium mt-2 text-textPrimary">Allowed Directories (from server):</p>
          {currentMcpStatus.allowedDirectories && currentMcpStatus.allowedDirectories.length > 0 ? (
            <ul className="list-disc list-inside pl-4">
              {currentMcpStatus.allowedDirectories.map(dir => <li key={dir} className="break-all">{dir}</li>)}
            </ul>
          ) : <p>No directories configured or status unavailable.</p>}
        </div>
        <button onClick={fetchMcpStatus} className="mt-2 text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded hover:bg-gray-300 dark:hover:bg-gray-600">Refresh MCP Status</button>

        <div className="mt-4">
          <label htmlFor="new-dir" className="block text-sm font-medium text-textSecondary">Add Allowed Directory (via active MCP connection)</label>
          <div className="flex gap-2 mt-1">
            <input
              type="text"
              id="new-dir"
              value={newAllowedDir}
              onChange={(e) => setNewAllowedDir(e.target.value)}
              placeholder="/path/to/your/case/files"
              className="flex-grow px-3 py-2 bg-background border border-border rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
            />
            <button
              onClick={handleAddDirectory}
              className="bg-secondary text-white px-4 py-2 rounded-lg hover:bg-secondary-dark transition-colors"
              disabled={newAllowedDir.trim() === ''}
            >
              Add
            </button>
          </div>
        </div>
      </section>

       <section className="bg-surface p-6 rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
        <h3 className="text-xl font-semibold text-textPrimary mb-2">MCP Configuration Editor</h3>
        <p className="text-xs text-textSecondary mb-2">
          Edit your MCP server configuration directly, similar to how Cursor handles it.
          Supports standard MCP configuration format with mcpServers.
        </p>

        <div className="my-4 flex gap-2">
          <button
            onClick={handleLoadMcpConfig}
            className="bg-secondary text-white px-3 py-2 rounded-lg hover:bg-secondary-dark transition-colors text-sm"
          >
            Load Current MCP Config
          </button>
          <label className="bg-gray-200 dark:bg-gray-700 text-textPrimary px-3 py-2 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm cursor-pointer">
            Import MCP File
            <input
              type="file"
              accept=".json"
              onChange={handleImportMcpFile}
              className="hidden"
            />
          </label>
          <button
            onClick={handleSaveMcpConfig}
            className="bg-primary text-white px-3 py-2 rounded-lg hover:bg-primary-dark transition-colors text-sm"
          >
            Save MCP Config
          </button>
        </div>

        {importedFileError && <p className="mb-2 text-xs text-red-500">{importedFileError}</p>}

        <textarea
            value={mcpConfigJson}
            onChange={(e) => setMcpConfigJson(e.target.value)}
            rows={15}
            className="w-full p-3 font-mono text-xs bg-background border border-border rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
            placeholder={`{
  "mcpServers": {
    "python-server": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "type": "stdio",
      "cwd": "/path/to/server",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@smithery/cli@latest", "run", "@smithery-ai/brave-search"],
      "type": "stdio"
    }
  }
}`}
            aria-label="MCP Configuration JSON Editor"
        />

        <p className="mt-2 text-xs text-textSecondary">
          This editor works with standard MCP configuration format. Changes are saved to the backend configuration file.
        </p>
      </section>

      <section className="bg-surface p-6 rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
        <h3 className="text-xl font-semibold text-textPrimary mb-4">Audit Log</h3>
        <div className="max-h-96 overflow-y-auto space-y-2 text-sm border border-border p-3 rounded-md bg-background">
          {auditLog.length > 0 ? auditLog.map((entry: AuditLogEntry) => (
            <div key={entry.id} className="p-2 border-b border-border/50 last:border-b-0">
              <p className="font-semibold text-textPrimary">
                {new Date(entry.timestamp).toLocaleString()} - <span className="text-primary">{entry.action}</span>
              </p>
              <p className="text-xs text-textSecondary break-all">{entry.details}</p>
            </div>
          )) : <p className="text-textSecondary text-center py-4">No audit log entries yet.</p>}
        </div>
      </section>
    </div>
  );
};

export default SettingsPage;
