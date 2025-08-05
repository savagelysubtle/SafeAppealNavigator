import React, { useState, useEffect } from 'react';
import { useAppContext } from '../../../contexts/AppContext';
import LoadingSpinner from '../../ui/LoadingSpinner';

interface Provider {
  id: string;
  name: string;
  icon: string;
  envKey: string;
  hasApiKey: boolean;
  isConfigured: boolean;
  models?: string[];
  defaultModel?: string;
}

const PROVIDERS: Provider[] = [
  { id: 'openai', name: 'OpenAI', icon: '🤖', envKey: 'OPENAI_API_KEY', hasApiKey: true, isConfigured: false },
  { id: 'anthropic', name: 'Anthropic (Claude)', icon: '🧠', envKey: 'ANTHROPIC_API_KEY', hasApiKey: true, isConfigured: false },
  { id: 'google', name: 'Google Gemini', icon: '✨', envKey: 'GOOGLE_API_KEY', hasApiKey: true, isConfigured: false },
  { id: 'mistral', name: 'Mistral AI', icon: '🌊', envKey: 'MISTRAL_API_KEY', hasApiKey: true, isConfigured: false },
  { id: 'ollama', name: 'Ollama (Local)', icon: '🦙', envKey: '', hasApiKey: false, isConfigured: false },
  { id: 'deepseek', name: 'DeepSeek', icon: '🔍', envKey: 'DEEPSEEK_API_KEY', hasApiKey: true, isConfigured: false },
  { id: 'watsonx', name: 'IBM WatsonX', icon: '🔷', envKey: 'WATSONX_API_KEY', hasApiKey: true, isConfigured: false },
];

const ProvidersTab: React.FC = () => {
  const { addAuditLogEntry, setError } = useAppContext();
  const [providers, setProviders] = useState<Provider[]>(PROVIDERS);
  const [selectedProvider, setSelectedProvider] = useState<string>('openai');
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [loadingProviderStatus, setLoadingProviderStatus] = useState(true);

  useEffect(() => {
    fetchProviderStatus();
  }, []);

  const fetchProviderStatus = async () => {
    setLoadingProviderStatus(true);
    try {
      const response = await fetch('http://localhost:10200/api/providers');
      if (response.ok) {
        const data = await response.json();
        // Update provider configuration status
        setProviders(prevProviders =>
          prevProviders.map(provider => ({
            ...provider,
            isConfigured: data[provider.id]?.configured || false,
            models: data[provider.id]?.models || [],
            defaultModel: data[provider.id]?.defaultModel
          }))
        );

        // Set default selected models
        const defaultModels: Record<string, string> = {};
        Object.entries(data).forEach(([providerId, providerData]: [string, any]) => {
          if (providerData.defaultModel) {
            defaultModels[providerId] = providerData.defaultModel;
          }
        });
        setSelectedModels(defaultModels);
      }
    } catch (error) {
      console.error('Error fetching provider status:', error);
      setError('Failed to fetch provider configuration status');
    } finally {
      setLoadingProviderStatus(false);
    }
  };

  const handleApiKeyChange = (providerId: string, value: string) => {
    setApiKeys(prev => ({
      ...prev,
      [providerId]: value
    }));
  };

  const handleTestApiKey = async (providerId: string) => {
    const apiKey = apiKeys[providerId];
    if (!apiKey) {
      setError('Please enter an API key to test');
      return;
    }

    setTestingProvider(providerId);
    try {
      const response = await fetch(`http://localhost:10200/api/providers/${providerId}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey,
          model: selectedModels[providerId]
        })
      });

      const result = await response.json();
      if (response.ok && result.success) {
        addAuditLogEntry(`${providerId.toUpperCase()}_API_KEY_VALIDATED`, `API key validated successfully`);
        // Update provider status
        setProviders(prev =>
          prev.map(p => p.id === providerId ? { ...p, isConfigured: true } : p)
        );
        setError(null);
      } else {
        setError(result.message || `Failed to validate ${providerId} API key`);
      }
    } catch (error) {
      setError(`Error testing ${providerId} API key: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setTestingProvider(null);
    }
  };

  const handleModelChange = (providerId: string, model: string) => {
    setSelectedModels(prev => ({
      ...prev,
      [providerId]: model
    }));
  };

  const selectedProviderData = providers.find(p => p.id === selectedProvider);

  return (
    <div className="p-6">
      <h2 className="text-2xl font-semibold text-textPrimary mb-4">LLM Provider Configuration</h2>

      {loadingProviderStatus ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Provider List */}
          <div className="lg:col-span-1">
            <h3 className="text-lg font-medium text-textPrimary mb-3">Providers</h3>
            <div className="space-y-2">
              {providers.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => setSelectedProvider(provider.id)}
                  className={`
                    w-full text-left p-3 rounded-lg border transition-all
                    ${selectedProvider === provider.id
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-primary/50'
                    }
                  `}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{provider.icon}</span>
                      <span className="font-medium text-textPrimary">{provider.name}</span>
                    </div>
                    {provider.isConfigured && (
                      <span className="text-green-500 text-sm">✓ Configured</span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Provider Configuration */}
          <div className="lg:col-span-2">
            {selectedProviderData && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-textPrimary">
                  Configure {selectedProviderData.name}
                </h3>

                {/* API Key Configuration */}
                {selectedProviderData.hasApiKey ? (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-textSecondary mb-2">
                        API Key
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="password"
                          value={apiKeys[selectedProviderData.id] || ''}
                          onChange={(e) => handleApiKeyChange(selectedProviderData.id, e.target.value)}
                          placeholder={`Enter ${selectedProviderData.name} API Key`}
                          className="flex-1 px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        />
                        <button
                          onClick={() => handleTestApiKey(selectedProviderData.id)}
                          disabled={testingProvider === selectedProviderData.id || !apiKeys[selectedProviderData.id]}
                          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
                        >
                          {testingProvider === selectedProviderData.id ? (
                            <LoadingSpinner size="sm" />
                          ) : (
                            'Test'
                          )}
                        </button>
                      </div>
                      <p className="mt-2 text-xs text-textSecondary">
                        This will update the {selectedProviderData.envKey} environment variable
                      </p>
                    </div>

                    {/* Model Selection */}
                    {selectedProviderData.models && selectedProviderData.models.length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-textSecondary mb-2">
                          Model
                        </label>
                        <select
                          value={selectedModels[selectedProviderData.id] || selectedProviderData.defaultModel || ''}
                          onChange={(e) => handleModelChange(selectedProviderData.id, e.target.value)}
                          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        >
                          <option value="">Select a model</option>
                          {selectedProviderData.models.map((model) => (
                            <option key={model} value={model}>{model}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* Provider-specific settings */}
                    {selectedProviderData.id === 'ollama' && (
                      <div>
                        <label className="block text-sm font-medium text-textSecondary mb-2">
                          Base URL
                        </label>
                        <input
                          type="text"
                          placeholder="http://localhost:11434"
                          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-4 bg-background rounded-lg border border-border">
                    <p className="text-textSecondary">
                      {selectedProviderData.name} runs locally and doesn't require an API key.
                    </p>
                    {selectedProviderData.id === 'ollama' && (
                      <div className="mt-4">
                        <label className="block text-sm font-medium text-textSecondary mb-2">
                          Ollama Base URL
                        </label>
                        <input
                          type="text"
                          placeholder="http://localhost:11434"
                          defaultValue="http://localhost:11434"
                          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Provider Information */}
                <div className="mt-6 p-4 bg-background rounded-lg border border-border">
                  <h4 className="text-sm font-medium text-textPrimary mb-2">Provider Information</h4>
                  <div className="space-y-1 text-sm text-textSecondary">
                    <p>Status: {selectedProviderData.isConfigured ?
                      <span className="text-green-500 font-medium">Configured</span> :
                      <span className="text-yellow-500 font-medium">Not Configured</span>
                    }</p>
                    {selectedProviderData.hasApiKey && (
                      <p>Environment Variable: <code className="bg-background px-1 rounded">{selectedProviderData.envKey}</code></p>
                    )}
                    {selectedProviderData.defaultModel && (
                      <p>Default Model: <code className="bg-background px-1 rounded">{selectedProviderData.defaultModel}</code></p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProvidersTab;