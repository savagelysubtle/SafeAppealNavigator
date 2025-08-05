import React, { useState } from 'react';
import { useAppContext } from '../../contexts/AppContext';
import ProvidersTab from './settings/ProvidersTab';
import MCPConfigTab from './settings/MCPConfigTab';
import PerformanceTab from './settings/PerformanceTab';
import AgentConfigTab from './settings/AgentConfigTab';
import IntegrationTab from './settings/IntegrationTab';
import PreferencesTab from './settings/PreferencesTab';
import MaintenanceTab from './settings/MaintenanceTab';

interface TabConfig {
  id: string;
  label: string;
  icon: string;
  component: React.FC;
}

const Settings: React.FC = () => {
  const { theme } = useAppContext();
  const [activeTab, setActiveTab] = useState('providers');

  const tabs: TabConfig[] = [
    {
      id: 'providers',
      label: 'Providers',
      icon: '🔑',
      component: ProvidersTab
    },
    {
      id: 'mcp',
      label: 'MCP Servers',
      icon: '🔧',
      component: MCPConfigTab
    },
    {
      id: 'performance',
      label: 'Performance',
      icon: '⚡',
      component: PerformanceTab
    },
    {
      id: 'agents',
      label: 'Agent Config',
      icon: '🤖',
      component: AgentConfigTab
    },
    {
      id: 'integration',
      label: 'Integration',
      icon: '🔗',
      component: IntegrationTab
    },
    {
      id: 'preferences',
      label: 'Preferences',
      icon: '🎨',
      component: PreferencesTab
    },
    {
      id: 'maintenance',
      label: 'Maintenance',
      icon: '🛠️',
      component: MaintenanceTab
    }
  ];

  const ActiveTabComponent = tabs.find(tab => tab.id === activeTab)?.component || ProvidersTab;

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-textPrimary">Settings</h1>
          <p className="text-textSecondary mt-2">
            Configure your AI Research Assistant environment
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-border">
          <nav className="flex space-x-8" aria-label="Settings tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-3 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-primary text-primary'
                    : 'border-transparent text-textSecondary hover:text-textPrimary hover:border-border'
                  }
                `}
              >
                <span className="flex items-center gap-2">
                  <span className="text-lg">{tab.icon}</span>
                  {tab.label}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-surface rounded-lg shadow-modern-md dark:shadow-modern-md-dark border border-border">
          <ActiveTabComponent />
        </div>
      </div>
    </div>
  );
};

export default Settings;
