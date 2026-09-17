import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import { LlmSettingsModal, type LlmSettings } from '../Settings/LlmSettings';

const LABELS: Record<string, string> = {
  openai: 'OpenAI',
  xai: 'Grok',
  anthropic: 'Claude',
};

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [llm, setLlm] = useState<LlmSettings | null>(null);

  useEffect(() => {
    if (!user) return;
    void api.settings.llm().then(setLlm).catch(() => undefined);
  }, [user]);

  return (
    <>
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">RAGged</h1>
              <span className="ml-2 text-sm text-gray-500">Document Q&A with AI</span>
            </div>
            {user && (
              <div className="flex items-center space-x-3">
                {llm && (
                  <select
                    aria-label="Chat provider"
                    className="text-sm border rounded-md px-2 py-1"
                    value={llm.chat_provider}
                    onChange={(e) => {
                      const chat_provider = e.target.value as LlmSettings['chat_provider'];
                      void api.settings.updateLlm({ chat_provider }).then(setLlm);
                    }}
                  >
                    {(['openai', 'xai', 'anthropic'] as const).map((name) => (
                      <option key={name} value={name} disabled={!llm[name].configured}>
                        {LABELS[name]}
                        {!llm[name].configured ? ' (add key)' : ''}
                      </option>
                    ))}
                  </select>
                )}
                <button
                  type="button"
                  onClick={() => setSettingsOpen(true)}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  API keys
                </button>
                <span className="text-sm font-medium text-gray-700">{user.email}</span>
                <button
                  type="button"
                  onClick={() => void logout()}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>
      <LlmSettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={setLlm}
      />
    </>
  );
};
