import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../../contexts/AppContext';
import LoadingSpinner from '../../ui/LoadingSpinner';

interface MCPServer {
  id: string;
  command: string;
  args?: string[];
  type: string;
  cwd?: string;
  env?: Record<string, string>;
  enabled?: boolean;
}

interface MCPConfig {
  mcpServers: Record<string, MCPServer>;
}

const MCPConfigTab: React.FC = () => {
  const { addAuditLogEntry, setError } = useAppContext();
  const [mcpConfig, setMcpConfig] = useState<MCPConfig>({ mcpServers: {} });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [editingServer, setEditingServer] = useState<string | null>(null);
  const [newServerName, setNewServerName] = useState('');
  const [showAddServer, setShowAddServer] = useState(false);

  useEffect(() => {
    loadMCPConfig();
  }, []);

  const loadMCPConfig = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:10200/api/mcp-config');
      if (response.ok) {
        const configText = await response.text();
        const config = JSON.parse(configText);
        setMcpConfig(config);
        addAuditLogEntry('MCP_CONFIG_LOADED', 'MCP configuration loaded successfully');
      } else {
        throw new Error('Failed to load MCP configuration');
      }
    } catch (error) {
      setError(`Error loading MCP config: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const saveMCPConfig = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('http://localhost:10200/api/mcp-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: JSON.stringify(mcpConfig, null, 2) })
      });

      if (response.ok) {
        addAuditLogEntry('MCP_CONFIG_SAVED', 'MCP configuration saved successfully');
        setError(null);
      } else {
        throw new Error('Failed to save MCP configuration');
      }
    } catch (error) {
      setError(`Error saving MCP config: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleServerUpdate = (serverId: string, updates: Partial<MCPServer>) => {
    setMcpConfig(prev => ({
      mcpServers: {
        ...prev.mcpServers,
        [serverId]: {
          ...prev.mcpServers[serverId],
          ...updates
        }
      }
    }));
  };

  const handleDeleteServer = (serverId: string) => {
    const { [serverId]: deleted, ...remaining } = mcpConfig.mcpServers;
    setMcpConfig({ mcpServers: remaining });
    addAuditLogEntry('MCP_SERVER_DELETED', `Deleted MCP server: ${serverId}`);
  };

  const handleAddServer = () => {
    if (!newServerName.trim()) {
      setError('Server name cannot be empty');
      return;
    }

    if (mcpConfig.mcpServers[newServerName]) {
      setError('Server with this name already exists');
      return;
    }

    setMcpConfig(prev => ({
      mcpServers: {
        ...prev.mcpServers,
        [newServerName]: {
          id: newServerName,
          command: '',
          type: 'stdio',
          enabled: true
        }
      }
    }));

    setNewServerName('');
    setShowAddServer(false);
    setEditingServer(newServerName);
    addAuditLogEntry('MCP_SERVER_ADDED', `Added new MCP server: ${newServerName}`);
  };

  const handleToggleServer = (serverId: string) => {
    const server = mcpConfig.mcpServers[serverId];
    handleServerUpdate(serverId, { enabled: !server.enabled });
  };

  if (isLoading) {
    return (
      <div className="p-6 flex justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-textPrimary">MCP Server Configuration</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddServer(true)}
            className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-colors"
          >
            Add Server
          </button>
          <button
            onClick={saveMCPConfig}
            disabled={isSaving}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            {isSaving ? <LoadingSpinner size="sm" /> : 'Save Configuration'}
          </button>
        </div>
      </div>

      {/* Add Server Dialog */}
      {showAddServer && (
        <div className="mb-6 p-4 bg-background border border-border rounded-lg">
          <h3 className="text-lg font-medium text-textPrimary mb-3">Add New MCP Server</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={newServerName}
              onChange={(e) => setNewServerName(e.target.value)}
              placeholder="Server name (e.g., python-tools)"
              className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              onKeyPress={(e) => e.key === 'Enter' && handleAddServer()}
            />
            <button
              onClick={handleAddServer}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >
              Add
            </button>
            <button
              onClick={() => {
                setShowAddServer(false);
                setNewServerName('');
              }}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Server List */}
      <div className="space-y-4">
        {Object.entries(mcpConfig.mcpServers).map(([serverId, server]) => (
          <div
            key={serverId}
            className={`p-4 bg-background border rounded-lg transition-all ${
              server.enabled !== false ? 'border-border' : 'border-border/50 opacity-60'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleToggleServer(serverId)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    server.enabled !== false ? 'bg-primary' : 'bg-gray-400'
                  } relative`}
                >
                  <div
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      server.enabled !== false ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <h3 className="text-lg font-medium text-textPrimary">{serverId}</h3>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingServer(editingServer === serverId ? null : serverId)}
                  className="px-3 py-1 text-sm bg-secondary text-white rounded hover:bg-secondary-dark transition-colors"
                >
                  {editingServer === serverId ? 'Done' : 'Edit'}
                </button>
                <button
                  onClick={() => handleDeleteServer(serverId)}
                  className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>

            {editingServer === serverId ? (
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">Command</label>
                  <input
                    type="text"
                    value={server.command}
                    onChange={(e) => handleServerUpdate(serverId, { command: e.target.value })}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="e.g., python, npx, uvx"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">Arguments</label>
                  <input
                    type="text"
                    value={server.args?.join(' ') || ''}
                    onChange={(e) => handleServerUpdate(serverId, {
                      args: e.target.value ? e.target.value.split(' ').filter(arg => arg) : undefined
                    })}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="e.g., -m my_server, @playwright/mcp@latest"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">Type</label>
                  <select
                    value={server.type}
                    onChange={(e) => handleServerUpdate(serverId, { type: e.target.value })}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="stdio">stdio</option>
                    <option value="http">http</option>
                    <option value="websocket">websocket</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">Working Directory</label>
                  <input
                    type="text"
                    value={server.cwd || ''}
                    onChange={(e) => handleServerUpdate(serverId, { cwd: e.target.value || undefined })}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Optional: /path/to/working/directory"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">Environment Variables</label>
                  <textarea
                    value={server.env ? JSON.stringify(server.env, null, 2) : ''}
                    onChange={(e) => {
                      try {
                        const env = e.target.value ? JSON.parse(e.target.value) : undefined;
                        handleServerUpdate(serverId, { env });
                      } catch {
                        // Invalid JSON, don't update
                      }
                    }}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                    placeholder='{"LOG_LEVEL": "INFO"}'
                    rows={3}
                  />
                </div>
              </div>
            ) : (
              <div className="text-sm text-textSecondary space-y-1">
                <p><span className="font-medium">Command:</span> {server.command || 'Not configured'}</p>
                {server.args && <p><span className="font-medium">Args:</span> {server.args.join(' ')}</p>}
                <p><span className="font-medium">Type:</span> {server.type}</p>
                {server.cwd && <p><span className="font-medium">CWD:</span> {server.cwd}</p>}
              </div>
            )}
          </div>
        ))}

        {Object.keys(mcpConfig.mcpServers).length === 0 && (
          <div className="text-center py-8 text-textSecondary">
            <p>No MCP servers configured yet.</p>
            <p className="text-sm mt-2">Click "Add Server" to get started.</p>
          </div>
        )}
      </div>

      {/* Import/Export Section */}
      <div className="mt-8 p-4 bg-background border border-border rounded-lg">
        <h3 className="text-lg font-medium text-textPrimary mb-3">Import/Export Configuration</h3>
        <div className="flex gap-2">
          <button
            onClick={() => {
              const blob = new Blob([JSON.stringify(mcpConfig, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'mcp-config.json';
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-colors"
          >
            Export Configuration
          </button>
          <label className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-colors cursor-pointer">
            Import Configuration
            <input
              type="file"
              accept=".json"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  const reader = new FileReader();
                  reader.onload = (e) => {
                    try {
                      const config = JSON.parse(e.target?.result as string);
                      setMcpConfig(config);
                      addAuditLogEntry('MCP_CONFIG_IMPORTED', 'MCP configuration imported from file');
                    } catch (error) {
                      setError('Invalid configuration file');
                    }
                  };
                  reader.readAsText(file);
                }
                e.target.value = '';
              }}
              className="hidden"
            />
          </label>
        </div>
      </div>
    </div>
  );
};

export default MCPConfigTab;