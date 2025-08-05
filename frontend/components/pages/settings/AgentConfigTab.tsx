import React, { useState } from 'react';
import { useAppContext } from '../../../contexts/AppContext';

interface AgentConfig {
  timeout: number;
  retryAttempts: number;
  batchSize: number;
  temperature: number;
  maxTokens: number;
}

interface AgentSettings {
  browserAgent: AgentConfig & {
    headless: boolean;
    viewportWidth: number;
    viewportHeight: number;
    userAgent: string;
  };
  researchAgent: AgentConfig & {
    searchDepth: string;
    maxResultsPerSource: number;
  };
  legalAgent: AgentConfig & {
    citationFormat: string;
    jurisdiction: string;
    maxDocumentSizeMb: number;
  };
  orchestratorAgent: AgentConfig & {
    taskPrioritization: boolean;
    parallelExecution: boolean;
    maxSubAgents: number;
  };
}

const DEFAULT_AGENT_CONFIG: AgentConfig = {
  timeout: 300,
  retryAttempts: 3,
  batchSize: 10,
  temperature: 0.7,
  maxTokens: 2048
};

const AgentConfigTab: React.FC = () => {
  const { addAuditLogEntry } = useAppContext();
  const [agentSettings, setAgentSettings] = useState<AgentSettings>({
    browserAgent: {
      ...DEFAULT_AGENT_CONFIG,
      headless: true,
      viewportWidth: 1920,
      viewportHeight: 1080,
      userAgent: ''
    },
    researchAgent: {
      ...DEFAULT_AGENT_CONFIG,
      temperature: 0.5,
      searchDepth: 'moderate',
      maxResultsPerSource: 10
    },
    legalAgent: {
      ...DEFAULT_AGENT_CONFIG,
      temperature: 0.3,
      citationFormat: 'bluebook',
      jurisdiction: 'federal',
      maxDocumentSizeMb: 50
    },
    orchestratorAgent: {
      ...DEFAULT_AGENT_CONFIG,
      taskPrioritization: true,
      parallelExecution: true,
      maxSubAgents: 5
    }
  });

  const [selectedAgent, setSelectedAgent] = useState<keyof AgentSettings>('browserAgent');

  const handleAgentSettingChange = (agent: keyof AgentSettings, field: string, value: any) => {
    setAgentSettings(prev => ({
      ...prev,
      [agent]: {
        ...prev[agent],
        [field]: value
      }
    }));
  };

  const saveSettings = () => {
    addAuditLogEntry('AGENT_CONFIG_SAVED', `Agent configurations updated for ${selectedAgent}`);
  };

  const renderAgentSpecificSettings = () => {
    const agent = agentSettings[selectedAgent];

    switch (selectedAgent) {
      case 'browserAgent':
        const browserSettings = agent as AgentSettings['browserAgent'];
        return (
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="headless"
                checked={browserSettings.headless}
                onChange={(e) => handleAgentSettingChange('browserAgent', 'headless', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <label htmlFor="headless" className="ml-2 text-sm text-textSecondary">
                Run in Headless Mode
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-textSecondary mb-1">
                  Viewport Width
                </label>
                <input
                  type="number"
                  value={browserSettings.viewportWidth}
                  onChange={(e) => handleAgentSettingChange('browserAgent', 'viewportWidth', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-textSecondary mb-1">
                  Viewport Height
                </label>
                <input
                  type="number"
                  value={browserSettings.viewportHeight}
                  onChange={(e) => handleAgentSettingChange('browserAgent', 'viewportHeight', parseInt(e.target.value))}
                  className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Custom User Agent
              </label>
              <input
                type="text"
                value={browserSettings.userAgent}
                onChange={(e) => handleAgentSettingChange('browserAgent', 'userAgent', e.target.value)}
                placeholder="Leave empty for default"
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        );

      case 'researchAgent':
        const researchSettings = agent as AgentSettings['researchAgent'];
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Search Depth
              </label>
              <select
                value={researchSettings.searchDepth}
                onChange={(e) => handleAgentSettingChange('researchAgent', 'searchDepth', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="shallow">Shallow - Quick overview</option>
                <option value="moderate">Moderate - Balanced depth</option>
                <option value="deep">Deep - Comprehensive research</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Max Results per Source
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={researchSettings.maxResultsPerSource}
                onChange={(e) => handleAgentSettingChange('researchAgent', 'maxResultsPerSource', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        );

      case 'legalAgent':
        const legalSettings = agent as AgentSettings['legalAgent'];
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Citation Format
              </label>
              <select
                value={legalSettings.citationFormat}
                onChange={(e) => handleAgentSettingChange('legalAgent', 'citationFormat', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="bluebook">Bluebook</option>
                <option value="apa">APA</option>
                <option value="mla">MLA</option>
                <option value="chicago">Chicago</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Jurisdiction
              </label>
              <select
                value={legalSettings.jurisdiction}
                onChange={(e) => handleAgentSettingChange('legalAgent', 'jurisdiction', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="federal">Federal</option>
                <option value="state">State</option>
                <option value="international">International</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Max Document Size (MB)
              </label>
              <input
                type="number"
                min="10"
                max="500"
                value={legalSettings.maxDocumentSizeMb}
                onChange={(e) => handleAgentSettingChange('legalAgent', 'maxDocumentSizeMb', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        );

      case 'orchestratorAgent':
        const orchestratorSettings = agent as AgentSettings['orchestratorAgent'];
        return (
          <div className="space-y-4">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="taskPrioritization"
                checked={orchestratorSettings.taskPrioritization}
                onChange={(e) => handleAgentSettingChange('orchestratorAgent', 'taskPrioritization', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <label htmlFor="taskPrioritization" className="ml-2 text-sm text-textSecondary">
                Enable Task Prioritization
              </label>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="parallelExecution"
                checked={orchestratorSettings.parallelExecution}
                onChange={(e) => handleAgentSettingChange('orchestratorAgent', 'parallelExecution', e.target.checked)}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <label htmlFor="parallelExecution" className="ml-2 text-sm text-textSecondary">
                Enable Parallel Execution
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-textSecondary mb-1">
                Max Sub-Agents
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={orchestratorSettings.maxSubAgents}
                onChange={(e) => handleAgentSettingChange('orchestratorAgent', 'maxSubAgents', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold text-textPrimary mb-4">Agent Configuration</h2>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Agent List */}
        <div className="lg:col-span-1">
          <h3 className="text-lg font-medium text-textPrimary mb-3">Select Agent</h3>
          <div className="space-y-2">
            {Object.keys(agentSettings).map((agentKey) => (
              <button
                key={agentKey}
                onClick={() => setSelectedAgent(agentKey as keyof AgentSettings)}
                className={`
                  w-full text-left p-3 rounded-lg border transition-all
                  ${selectedAgent === agentKey
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50'
                  }
                `}
              >
                <span className="font-medium text-textPrimary">
                  {agentKey.replace(/([A-Z])/g, ' $1').trim()}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Agent Settings */}
        <div className="lg:col-span-3">
          <div className="bg-background border border-border rounded-lg p-6">
            <h3 className="text-lg font-medium text-textPrimary mb-4 capitalize">
              {selectedAgent.replace(/([A-Z])/g, ' $1').trim()} Settings
            </h3>

            {/* Common Settings */}
            <div className="space-y-4 mb-6">
              <h4 className="text-md font-medium text-textSecondary">Common Settings</h4>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={agentSettings[selectedAgent].timeout}
                    onChange={(e) => handleAgentSettingChange(selectedAgent, 'timeout', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Retry Attempts
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={agentSettings[selectedAgent].retryAttempts}
                    onChange={(e) => handleAgentSettingChange(selectedAgent, 'retryAttempts', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={agentSettings[selectedAgent].temperature}
                    onChange={(e) => handleAgentSettingChange(selectedAgent, 'temperature', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-textSecondary mb-1">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    min="100"
                    max="8192"
                    value={agentSettings[selectedAgent].maxTokens}
                    onChange={(e) => handleAgentSettingChange(selectedAgent, 'maxTokens', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>
            </div>

            {/* Agent-Specific Settings */}
            <div>
              <h4 className="text-md font-medium text-textSecondary mb-4">Specific Settings</h4>
              {renderAgentSpecificSettings()}
            </div>

            {/* Save Button */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={saveSettings}
                className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
              >
                Save Agent Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentConfigTab;