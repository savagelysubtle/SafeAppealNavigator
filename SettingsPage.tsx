import React, { useState, useEffect } from 'react';
import { useAppContext } from './frontend/contexts/AppContext';
import { Theme, AuditLogEntry, McpServerStatus } from './frontend/types';
import ToggleSwitch from './frontend/components/ui/ToggleSwitch';
// Remove direct geminiService import - use AG-UI backend instead
import LoadingSpinner from './frontend/components/ui/LoadingSpinner';
import { getMCPServerStatus } from './frontend/contexts/AppContextHelper';

const SettingsPage: React.FC = () => {
  const {
    theme, toggleTheme, auditLog, addAuditLogEntry,
    mcpServerStatus: contextMcpStatus, setMcpServerStatus,
    apiKey: currentApiKey, setApiKey: setContextApiKey,
    setError
  } = useAppContext();

  const [newAllowedDir, setNewAllowedDir] = useState('');
  const [localApiKey, setLocalApiKey] = useState(currentApiKey || '');
  const [isTestingApiKey, setIsTestingApiKey] = useState(false);
  const [apiKeyTestResult, setApiKeyTestResult] = useState<string | null>(null);
  const [currentMcpStatus, setCurrentMcpStatus] = useState<McpServerStatus>(contextMcpStatus);
  const [importedFileError, setImportedFileError] = useState<string | null>(null);
  const [mcpConfigJson, setMcpConfigJson] = useState<string>('');

  useEffect(() => {
    setCurrentMcpStatus(contextMcpStatus);
  }, [contextMcpStatus]);

  // Load MCP config on component mount
  useEffect(() => {
    handleLoadMcpConfig();
  }, []);

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
        addAuditLogEntry('MCP_CONFIG_LOADED', 'MCP configuration loaded from data/mcp.json.');
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
        addAuditLogEntry('MCP_CONFIG_SAVED', 'MCP configuration saved to data/mcp.json.');
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
        alert(`MCP configuration from "${file.name}" loaded into editor. Click "Save Configuration" to write to data/mcp.json.`);
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
        <h3 className="text-xl font-semibold text-textPrimary mb-2">MCP Server Status</h3>

        <div className="text-sm space-y-1 text-textSecondary">
          <p>Status: {currentMcpStatus.isRunning ?
            <span className="text-green-500 font-semibold">Running</span> :
            <span className="text-red-500 font-semibold">Not Running {currentMcpStatus.error ? `(${currentMcpStatus.error.substring(0,150)}${currentMcpStatus.error.length > 150 ? '...' : ''})` : ''}</span>}
          </p>
          {currentMcpStatus.isRunning && <p>Server Version: {currentMcpStatus.version || 'N/A'}</p>}
          <p className="font-medium mt-2 text-textPrimary">Allowed Directories (from server):</p>
          {currentMcpStatus.allowedDirectories && currentMcpStatus.allowedDirectories.length > 0 ? (
            <ul className="list-disc list-inside pl-4">
              {currentMcpStatus.allowedDirectories.map(dir => <li key={dir} className="break-all">{dir}</li>)}
            </ul>
          ) : <p>No directories configured or status unavailable.</p>}
        </div>
        <button onClick={fetchMcpStatus} className="mt-2 text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded hover:bg-gray-300 dark:hover:bg-gray-600">Refresh MCP Status</button>

        <div className="mt-4">
          <label htmlFor="new-dir" className="block text-sm font-medium text-textSecondary">Add Allowed Directory</label>
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
        <h3 className="text-xl font-semibold text-textPrimary mb-2">MCP Configuration</h3>
        <p className="text-xs text-textSecondary mb-2">
          Edit your MCP server configuration (data/mcp.json). Changes are automatically saved to the backend.
        </p>

        <div className="my-4 flex gap-2">
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
            Save Configuration
          </button>
        </div>

        {importedFileError && <p className="mb-2 text-xs text-red-500">{importedFileError}</p>}

        <textarea
            value={mcpConfigJson}
            onChange={(e) => setMcpConfigJson(e.target.value)}
            rows={20}
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
    "chroma": {
      "command": "uvx",
      "args": ["chroma-mcp", "--client-type", "persistent"],
      "type": "stdio"
    }
  }
}`}
            aria-label="MCP Configuration JSON Editor"
        />

        <p className="mt-2 text-xs text-textSecondary">
          This configuration is stored in data/mcp.json and used by your AI agents for tool access.
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
