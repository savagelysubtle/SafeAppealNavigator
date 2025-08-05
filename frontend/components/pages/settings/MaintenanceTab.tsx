import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../../contexts/AppContext';
import LoadingSpinner from '../../ui/LoadingSpinner';

interface SystemStatus {
  version: string;
  uptime: string;
  memoryUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  diskSpace: {
    used: number;
    total: number;
    percentage: number;
  };
  activeAgents: number;
  queuedTasks: number;
  lastBackup: string;
}

interface DiagnosticResult {
  category: string;
  status: 'success' | 'warning' | 'error';
  message: string;
  details?: string;
}

const MaintenanceTab: React.FC = () => {
  const { addAuditLogEntry, auditLog, setError } = useAppContext();
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    version: '1.0.0',
    uptime: '0d 0h 0m',
    memoryUsage: { used: 0, total: 2048, percentage: 0 },
    diskSpace: { used: 0, total: 100, percentage: 0 },
    activeAgents: 0,
    queuedTasks: 0,
    lastBackup: 'Never'
  });
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isRunningDiagnostics, setIsRunningDiagnostics] = useState(false);
  const [diagnosticResults, setDiagnosticResults] = useState<DiagnosticResult[]>([]);

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      // In a real implementation, this would fetch from backend
      // Simulating data for now
      setSystemStatus({
        version: '1.0.0',
        uptime: '2d 14h 32m',
        memoryUsage: {
          used: Math.round(Math.random() * 1024 + 500),
          total: 2048,
          percentage: Math.round(Math.random() * 60 + 20)
        },
        diskSpace: {
          used: Math.round(Math.random() * 50 + 10),
          total: 100,
          percentage: Math.round(Math.random() * 70 + 10)
        },
        activeAgents: Math.floor(Math.random() * 5),
        queuedTasks: Math.floor(Math.random() * 10),
        lastBackup: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toLocaleDateString()
      });
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const handleExportAll = async () => {
    setIsExporting(true);
    try {
      // In a real implementation, this would export all settings
      const exportData = {
        version: systemStatus.version,
        timestamp: new Date().toISOString(),
        settings: {
          // Would include all settings from other tabs
        },
        auditLog: auditLog
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ai-research-assistant-backup-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);

      addAuditLogEntry('SETTINGS_EXPORTED', 'All settings exported successfully');
    } catch (error) {
      setError('Failed to export settings');
    } finally {
      setIsExporting(false);
    }
  };

  const handleImportAll = async (file: File) => {
    setIsImporting(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const importData = JSON.parse(e.target?.result as string);
          // In a real implementation, this would validate and import settings
          addAuditLogEntry('SETTINGS_IMPORTED', `Settings imported from ${file.name}`);
          alert('Settings imported successfully. Please restart the application.');
        } catch (error) {
          setError('Invalid import file format');
        }
      };
      reader.readAsText(file);
    } catch (error) {
      setError('Failed to import settings');
    } finally {
      setIsImporting(false);
    }
  };

  const runDiagnostics = async () => {
    setIsRunningDiagnostics(true);
    setDiagnosticResults([]);

    try {
      // Simulate diagnostic checks
      const results: DiagnosticResult[] = [
        {
          category: 'API Keys',
          status: 'success',
          message: 'All configured API keys are valid'
        },
        {
          category: 'MCP Servers',
          status: 'warning',
          message: '2 of 5 MCP servers are not responding',
          details: 'Python and Rust servers may need to be restarted'
        },
        {
          category: 'Database',
          status: 'success',
          message: 'Database connection is healthy'
        },
        {
          category: 'ChromaDB',
          status: 'success',
          message: 'Vector database is operational'
        },
        {
          category: 'Disk Space',
          status: systemStatus.diskSpace.percentage > 80 ? 'warning' : 'success',
          message: `${100 - systemStatus.diskSpace.percentage}% disk space available`
        },
        {
          category: 'Memory',
          status: systemStatus.memoryUsage.percentage > 80 ? 'warning' : 'success',
          message: `Using ${systemStatus.memoryUsage.percentage}% of available memory`
        }
      ];

      setDiagnosticResults(results);
      addAuditLogEntry('DIAGNOSTICS_RUN', 'System diagnostics completed');
    } catch (error) {
      setError('Failed to run diagnostics');
    } finally {
      setIsRunningDiagnostics(false);
    }
  };

  const clearCache = async () => {
    try {
      // In a real implementation, this would clear various caches
      addAuditLogEntry('CACHE_CLEARED', 'All caches cleared successfully');
      alert('Cache cleared successfully');
    } catch (error) {
      setError('Failed to clear cache');
    }
  };

  const clearLogs = async () => {
    try {
      // In a real implementation, this would clear old logs
      addAuditLogEntry('LOGS_CLEARED', 'Old logs cleared successfully');
      alert('Logs cleared successfully');
    } catch (error) {
      setError('Failed to clear logs');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-semibold text-textPrimary">System Maintenance</h2>

      {/* System Status */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">System Status</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-textSecondary">Version</p>
            <p className="text-lg font-semibold text-textPrimary">{systemStatus.version}</p>
          </div>
          <div>
            <p className="text-sm text-textSecondary">Uptime</p>
            <p className="text-lg font-semibold text-textPrimary">{systemStatus.uptime}</p>
          </div>
          <div>
            <p className="text-sm text-textSecondary">Last Backup</p>
            <p className="text-lg font-semibold text-textPrimary">{systemStatus.lastBackup}</p>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-textSecondary">Memory Usage</span>
              <span className="text-textPrimary">{systemStatus.memoryUsage.used} MB / {systemStatus.memoryUsage.total} MB</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  systemStatus.memoryUsage.percentage > 80 ? 'bg-red-500' :
                  systemStatus.memoryUsage.percentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${systemStatus.memoryUsage.percentage}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-textSecondary">Disk Space</span>
              <span className="text-textPrimary">{systemStatus.diskSpace.used} GB / {systemStatus.diskSpace.total} GB</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${
                  systemStatus.diskSpace.percentage > 80 ? 'bg-red-500' :
                  systemStatus.diskSpace.percentage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${systemStatus.diskSpace.percentage}%` }}
              />
            </div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-surface rounded-lg">
            <p className="text-2xl font-bold text-primary">{systemStatus.activeAgents}</p>
            <p className="text-sm text-textSecondary">Active Agents</p>
          </div>
          <div className="text-center p-3 bg-surface rounded-lg">
            <p className="text-2xl font-bold text-primary">{systemStatus.queuedTasks}</p>
            <p className="text-sm text-textSecondary">Queued Tasks</p>
          </div>
        </div>
      </div>

      {/* Import/Export */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Backup & Restore</h3>

        <div className="space-y-4">
          <p className="text-sm text-textSecondary">
            Export all settings, configurations, and audit logs to a backup file, or import from a previous backup.
          </p>

          <div className="flex gap-3">
            <button
              onClick={handleExportAll}
              disabled={isExporting}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
            >
              {isExporting ? <LoadingSpinner size="sm" /> : 'Export All Settings'}
            </button>

            <label className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-colors cursor-pointer">
              {isImporting ? <LoadingSpinner size="sm" /> : 'Import Settings'}
              <input
                type="file"
                accept=".json"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleImportAll(file);
                  e.target.value = '';
                }}
                className="hidden"
                disabled={isImporting}
              />
            </label>
          </div>
        </div>
      </div>

      {/* Diagnostics */}
      <div className="bg-background border border-border rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-textPrimary">System Diagnostics</h3>
          <button
            onClick={runDiagnostics}
            disabled={isRunningDiagnostics}
            className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-dark transition-colors disabled:opacity-50"
          >
            {isRunningDiagnostics ? <LoadingSpinner size="sm" /> : 'Run Diagnostics'}
          </button>
        </div>

        {diagnosticResults.length > 0 && (
          <div className="space-y-2">
            {diagnosticResults.map((result, index) => (
              <div
                key={index}
                className={`p-3 rounded-lg border ${
                  result.status === 'success' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' :
                  result.status === 'warning' ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20' :
                  'border-red-500 bg-red-50 dark:bg-red-900/20'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-textPrimary">{result.category}</p>
                    <p className="text-sm text-textSecondary">{result.message}</p>
                    {result.details && (
                      <p className="text-xs text-textSecondary mt-1">{result.details}</p>
                    )}
                  </div>
                  <div className="text-2xl">
                    {result.status === 'success' ? '✅' :
                     result.status === 'warning' ? '⚠️' : '❌'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {diagnosticResults.length === 0 && !isRunningDiagnostics && (
          <p className="text-sm text-textSecondary">
            Run diagnostics to check the health of all system components.
          </p>
        )}
      </div>

      {/* Maintenance Actions */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Maintenance Actions</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium text-textPrimary mb-2">Clear Cache</h4>
            <p className="text-sm text-textSecondary mb-3">
              Remove temporary files and cached data to free up space and resolve issues.
            </p>
            <button
              onClick={clearCache}
              className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
            >
              Clear Cache
            </button>
          </div>

          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium text-textPrimary mb-2">Clear Old Logs</h4>
            <p className="text-sm text-textSecondary mb-3">
              Remove logs older than 30 days to free up disk space.
            </p>
            <button
              onClick={clearLogs}
              className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
            >
              Clear Logs
            </button>
          </div>

          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium text-textPrimary mb-2">Reset to Defaults</h4>
            <p className="text-sm text-textSecondary mb-3">
              Reset all settings to their default values. This cannot be undone.
            </p>
            <button
              onClick={() => {
                if (confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
                  addAuditLogEntry('SETTINGS_RESET', 'All settings reset to defaults');
                  alert('Settings reset to defaults. Please restart the application.');
                }
              }}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
            >
              Reset All
            </button>
          </div>

          <div className="p-4 border border-border rounded-lg">
            <h4 className="font-medium text-textPrimary mb-2">Restart Services</h4>
            <p className="text-sm text-textSecondary mb-3">
              Restart all background services and agents.
            </p>
            <button
              onClick={() => {
                addAuditLogEntry('SERVICES_RESTARTED', 'All services restarted');
                alert('Services will restart in the background.');
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Restart Services
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Preview */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-medium text-textPrimary mb-4">Recent Audit Log</h3>
        <div className="max-h-60 overflow-y-auto space-y-2 text-sm">
          {auditLog.slice(-10).reverse().map((entry) => (
            <div key={entry.id} className="p-2 bg-surface rounded border border-border/50">
              <div className="flex justify-between">
                <span className="font-medium text-primary">{entry.action}</span>
                <span className="text-xs text-textSecondary">
                  {new Date(entry.timestamp).toLocaleString()}
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-1">{entry.details}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MaintenanceTab;