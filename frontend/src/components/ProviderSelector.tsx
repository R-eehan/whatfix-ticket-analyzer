import React from 'react';

interface ProviderSelectorProps {
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
}

const providers = [
  { value: '', label: 'Use Default Provider', icon: '🔧' },
  { value: 'gemini', label: 'Google Gemini', icon: '🤖' },
  { value: 'openai', label: 'OpenAI GPT-4', icon: '🧠' },
  { value: 'anthropic', label: 'Anthropic Claude', icon: '🎯' },
  { value: 'mock', label: 'Mock Provider (Testing)', icon: '🧪' },
];

const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  selectedProvider,
  onProviderChange,
}) => {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        LLM Provider <span className="text-gray-500 font-normal">(Optional)</span>
      </label>
      <select
        value={selectedProvider}
        onChange={(e) => onProviderChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {providers.map((provider) => (
          <option key={provider.value} value={provider.value}>
            {provider.icon} {provider.label}
          </option>
        ))}
      </select>
      <p className="mt-1 text-xs text-gray-500">
        {selectedProvider === '' 
          ? 'Uses the default provider configured in your environment'
          : selectedProvider === 'mock' 
          ? 'Mock provider uses simulated data - no API key required'
          : `Requires ${providers.find(p => p.value === selectedProvider)?.label} API key`
        }
      </p>
    </div>
  );
};

export default ProviderSelector;
