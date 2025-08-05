import React, { useState } from 'react';
import { useAppContext } from '../../../contexts/AppContext';

interface IntegrationSettings {
  chromaDB: {
    enabled: boolean;
    host: string;
    port: number;
    persistentPath: string;
    collectionName: string;
  };
  browser: {
    executable: string;
    downloadPath: string;
    enableExtensions: boolean;
    userDataDir: string;
  };
  database: {
    sqlitePath: string;
    enableWAL: boolean;
    maxConnections: number;
    busyTimeout: number;
  };
  wcat: {
    enabled: boolean;
    databasePath: string;
    updateFrequency: string;
  };
}

const IntegrationTab: React.FC = () => {
  const { addAuditLogEntry } = useAppContext();
  const [integrations, setIntegrations] = useState<IntegrationSettings>({
    chromaDB: {
      enabled: true,
      host: 'localhost',
      port: 8000,
      persistentPath: './chroma_db',
      collectionName: 'legal_documents'
    },
    browser: {
      executable: '',
      downloadPath: './downloads',
      enableExtensions: false,
      userDataDir: './browser_data'
    },
    database: {
      sqlitePath: './data/research.db',
      enableWAL: true,
      maxConnections: 5,
      busyTimeout: 5000
    },
    wcat: {
      enabled: true,
      databasePath: './data/wcat_decisions.db',
      updateFrequency: 'weekly'
    }
  });

  const handleIntegrationChange = (
    integration: keyof IntegrationSettings,
    field: string,
    value: any
  ) => {
    setIntegrations(prev => ({
      ...prev,
      [integration]: {
        ...prev[integration],
        [field]: value
      }
    }));
  };

  const testConnection = (integration: string) => {
    // In a real implementation, this would test the connection
    addAuditLogEntry(`${integration.toUpperCase()}_TEST`, `Testing ${integration} connection...`);
  };

  const saveSettings = () => {
    addAuditLogEntry('INTEGRATION_SETTINGS_SAVED', 'Integration settings updated');
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold text-textPrimary">Integration Settings</h2>

      {/* ChromaDB Configuration */}
      <div className="bg-background border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-textPrimary">ChromaDB Vector Database</h3>
          <button
            onClick={() => testConnection('chromaDB')}
            className="px-4 py-1 text-sm bg-secondary text-white rounded hover:bg-secondary-dark transition-colors"
          >
            Test Connection
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="chromadb-enabled"
              checked={integrations.chromaDB.enabled}
              onChange={(e) => handleIntegrationChange('chromaDB', 'enabled', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
            <label htmlFor="chromadb-enabled" className="ml-2 text-sm text-textSecondary">
              Enable ChromaDB Integration
            </label>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Host
              </label>
              <input
                type="text"
                value={integrations.chromaDB.host}
                onChange={(e) => handleIntegrationChange('chromaDB', 'host', e.target.value)}
                disabled={!integrations.chromaDB.enabled}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Port
              </label>
              <input
                type="number"
                value={integrations.chromaDB.port}
                onChange={(e) => handleIntegrationChange('chromaDB', 'port', parseInt(e.target.value))}
                disabled={!integrations.chromaDB.enabled}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Persistent Path
              </label>
              <input
                type="text"
                value={integrations.chromaDB.persistentPath}
                onChange={(e) => handleIntegrationChange('chromaDB', 'persistentPath', e.target.value)}
                disabled={!integrations.chromaDB.enabled}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Collection Name
              </label>
              <input
                type="text"
                value={integrations.chromaDB.collectionName}
                onChange={(e) => handleIntegrationChange('chromaDB', 'collectionName', e.target.value)}
                disabled={!integrations.chromaDB.enabled}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Browser Configuration */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Browser Integration</h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Browser Executable Path
            </label>
            <input
              type="text"
              value={integrations.browser.executable}
              onChange={(e) => handleIntegrationChange('browser', 'executable', e.target.value)}
              placeholder="Leave empty for auto-detection"
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Download Path
              </label>
              <input
                type="text"
                value={integrations.browser.downloadPath}
                onChange={(e) => handleIntegrationChange('browser', 'downloadPath', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                User Data Directory
              </label>
              <input
                type="text"
                value={integrations.browser.userDataDir}
                onChange={(e) => handleIntegrationChange('browser', 'userDataDir', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="browser-extensions"
              checked={integrations.browser.enableExtensions}
              onChange={(e) => handleIntegrationChange('browser', 'enableExtensions', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
            <label htmlFor="browser-extensions" className="ml-2 text-sm text-textSecondary">
              Enable Browser Extensions
            </label>
          </div>
        </div>
      </div>

      {/* Database Configuration */}
      <div className="bg-background border border-border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-textPrimary">SQLite Database</h3>
          <button
            onClick={() => testConnection('database')}
            className="px-4 py-1 text-sm bg-secondary text-white rounded hover:bg-secondary-dark transition-colors"
          >
            Test Connection
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Database Path
            </label>
            <input
              type="text"
              value={integrations.database.sqlitePath}
              onChange={(e) => handleIntegrationChange('database', 'sqlitePath', e.target.value)}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Max Connections
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={integrations.database.maxConnections}
                onChange={(e) => handleIntegrationChange('database', 'maxConnections', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Busy Timeout (ms)
              </label>
              <input
                type="number"
                min="100"
                max="30000"
                value={integrations.database.busyTimeout}
                onChange={(e) => handleIntegrationChange('database', 'busyTimeout', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="database-wal"
              checked={integrations.database.enableWAL}
              onChange={(e) => handleIntegrationChange('database', 'enableWAL', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
            <label htmlFor="database-wal" className="ml-2 text-sm text-textSecondary">
              Enable WAL Mode (Write-Ahead Logging)
            </label>
          </div>
        </div>
      </div>

      {/* WCAT Database Configuration */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">WCAT Database Integration</h3>

        <div className="space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="wcat-enabled"
              checked={integrations.wcat.enabled}
              onChange={(e) => handleIntegrationChange('wcat', 'enabled', e.target.checked)}
              className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
            />
            <label htmlFor="wcat-enabled" className="ml-2 text-sm text-textSecondary">
              Enable WCAT Database Integration
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              WCAT Database Path
            </label>
            <input
              type="text"
              value={integrations.wcat.databasePath}
              onChange={(e) => handleIntegrationChange('wcat', 'databasePath', e.target.value)}
              disabled={!integrations.wcat.enabled}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-textSecondary mb-1">
              Update Frequency
            </label>
            <select
              value={integrations.wcat.updateFrequency}
              onChange={(e) => handleIntegrationChange('wcat', 'updateFrequency', e.target.value)}
              disabled={!integrations.wcat.enabled}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="manual">Manual Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveSettings}
          className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
        >
          Save Integration Settings
        </button>
      </div>
    </div>
  );
};

export default IntegrationTab;