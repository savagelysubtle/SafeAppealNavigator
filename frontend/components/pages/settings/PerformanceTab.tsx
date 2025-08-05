import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../../contexts/AppContext';

interface RateLimitSettings {
  provider: string;
  requestsPerMinute: number;
  tokensPerMinute?: number;
  maxRetries: number;
  exponentialBase: number;
  jitter: boolean;
}

interface ResourceSettings {
  maxConcurrentTasks: number;
  memoryLimitMb: number;
  taskTimeout: number;
  batchSize: number;
}

const PROVIDER_RATE_LIMITS: Record<string, RateLimitSettings> = {
  google: { provider: 'google', requestsPerMinute: 5, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  openai: { provider: 'openai', requestsPerMinute: 60, tokensPerMinute: 90000, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  anthropic: { provider: 'anthropic', requestsPerMinute: 50, tokensPerMinute: 100000, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  mistral: { provider: 'mistral', requestsPerMinute: 120, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  deepseek: { provider: 'deepseek', requestsPerMinute: 60, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  watsonx: { provider: 'watsonx', requestsPerMinute: 30, maxRetries: 5, exponentialBase: 2.0, jitter: true },
  ollama: { provider: 'ollama', requestsPerMinute: 1000, maxRetries: 3, exponentialBase: 2.0, jitter: false },
};

const PerformanceTab: React.FC = () => {
  const { addAuditLogEntry } = useAppContext();
  const [rateLimits, setRateLimits] = useState<Record<string, RateLimitSettings>>(PROVIDER_RATE_LIMITS);
  const [resourceSettings, setResourceSettings] = useState<ResourceSettings>({
    maxConcurrentTasks: 10,
    memoryLimitMb: 2048,
    taskTimeout: 300,
    batchSize: 10
  });

  const handleRateLimitChange = (provider: string, field: keyof RateLimitSettings, value: any) => {
    setRateLimits(prev => ({
      ...prev,
      [provider]: {
        ...prev[provider],
        [field]: value
      }
    }));
  };

  const handleResourceChange = (field: keyof ResourceSettings, value: any) => {
    setResourceSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const saveSettings = () => {
    // In a real implementation, this would save to backend
    addAuditLogEntry('PERFORMANCE_SETTINGS_SAVED', 'Performance settings updated');
  };

  return (
    <div className="p-6 space-y-8">
      <h2 className="text-2xl font-semibold text-textPrimary">Performance Configuration</h2>

      {/* Rate Limiting Section */}
      <div>
        <h3 className="text-xl font-medium text-textPrimary mb-4">Rate Limiting</h3>
        <p className="text-sm text-textSecondary mb-4">
          Configure rate limits for each provider to avoid hitting API limits. Values are per minute.
        </p>

        <div className="space-y-4">
          {Object.entries(rateLimits).map(([provider, settings]) => (
            <div key={provider} className="p-4 bg-background border border-border rounded-lg">
              <h4 className="text-lg font-medium text-textPrimary capitalize mb-3">{provider}</h4>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Requests per Minute
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="200"
                    value={settings.requestsPerMinute}
                    onChange={(e) => handleRateLimitChange(provider, 'requestsPerMinute', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-textSecondary mt-1">
                    <span>1</span>
                    <span className="font-medium text-primary">{settings.requestsPerMinute}</span>
                    <span>200</span>
                  </div>
                </div>

                {settings.tokensPerMinute !== undefined && (
                  <div>
                    <label className="block text-sm font-medium text-textSecondary mb-1">
                      Tokens per Minute
                    </label>
                    <input
                      type="number"
                      value={settings.tokensPerMinute}
                      onChange={(e) => handleRateLimitChange(provider, 'tokensPerMinute', parseInt(e.target.value))}
                      className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Max Retries
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={settings.maxRetries}
                    onChange={(e) => handleRateLimitChange(provider, 'maxRetries', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Exponential Base
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={settings.exponentialBase}
                    onChange={(e) => handleRateLimitChange(provider, 'exponentialBase', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id={`${provider}-jitter`}
                    checked={settings.jitter}
                    onChange={(e) => handleRateLimitChange(provider, 'jitter', e.target.checked)}
                    className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
                  />
                  <label htmlFor={`${provider}-jitter`} className="ml-2 text-sm text-textSecondary">
                    Enable Jitter
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Management Section */}
      <div>
        <h3 className="text-xl font-medium text-textPrimary mb-4">Resource Management</h3>
        <p className="text-sm text-textSecondary mb-4">
          Configure system resource limits and task management settings.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-background border border-border rounded-lg">
            <label className="block text-sm font-medium text-textSecondary mb-2">
              Maximum Concurrent Tasks
            </label>
            <input
              type="range"
              min="1"
              max="50"
              value={resourceSettings.maxConcurrentTasks}
              onChange={(e) => handleResourceChange('maxConcurrentTasks', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-textSecondary mt-1">
              <span>1</span>
              <span className="font-medium text-primary">{resourceSettings.maxConcurrentTasks}</span>
              <span>50</span>
            </div>
            <p className="text-xs text-textSecondary mt-2">
              Number of tasks that can run simultaneously
            </p>
          </div>

          <div className="p-4 bg-background border border-border rounded-lg">
            <label className="block text-sm font-medium text-textSecondary mb-2">
              Memory Limit (MB)
            </label>
            <input
              type="range"
              min="512"
              max="8192"
              step="512"
              value={resourceSettings.memoryLimitMb}
              onChange={(e) => handleResourceChange('memoryLimitMb', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-textSecondary mt-1">
              <span>512</span>
              <span className="font-medium text-primary">{resourceSettings.memoryLimitMb}</span>
              <span>8192</span>
            </div>
            <p className="text-xs text-textSecondary mt-2">
              Maximum memory allocation for agent operations
            </p>
          </div>

          <div className="p-4 bg-background border border-border rounded-lg">
            <label className="block text-sm font-medium text-textSecondary mb-2">
              Task Timeout (seconds)
            </label>
            <input
              type="number"
              min="60"
              max="1800"
              value={resourceSettings.taskTimeout}
              onChange={(e) => handleResourceChange('taskTimeout', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p className="text-xs text-textSecondary mt-2">
              Maximum time allowed for a single task execution
            </p>
          </div>

          <div className="p-4 bg-background border border-border rounded-lg">
            <label className="block text-sm font-medium text-textSecondary mb-2">
              Batch Size
            </label>
            <input
              type="number"
              min="1"
              max="100"
              value={resourceSettings.batchSize}
              onChange={(e) => handleResourceChange('batchSize', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <p className="text-xs text-textSecondary mt-2">
              Number of items to process in a single batch
            </p>
          </div>
        </div>
      </div>

      {/* Resource Monitor */}
      <div className="p-4 bg-background border border-border rounded-lg">
        <h3 className="text-lg font-medium text-textPrimary mb-3">Current Resource Usage</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-textSecondary">Active Tasks</p>
            <p className="text-2xl font-semibold text-primary">0 / {resourceSettings.maxConcurrentTasks}</p>
          </div>
          <div>
            <p className="text-textSecondary">Memory Usage</p>
            <p className="text-2xl font-semibold text-primary">0 MB / {resourceSettings.memoryLimitMb} MB</p>
          </div>
          <div>
            <p className="text-textSecondary">Rate Limit Status</p>
            <p className="text-2xl font-semibold text-green-500">All Clear</p>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveSettings}
          className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
        >
          Save Performance Settings
        </button>
      </div>
    </div>
  );
};

export default PerformanceTab;