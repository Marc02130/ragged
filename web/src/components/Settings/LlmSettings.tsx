import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';

export type LlmSettings = {
  openai: { configured: boolean };
  xai: { configured: boolean };
  anthropic: { configured: boolean };
  chat_provider: 'openai' | 'xai' | 'anthropic';
  chat_models: Record<string, string>;
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: (settings: LlmSettings) => void;
};

const LABELS: Record<string, string> = {
  openai: 'OpenAI',
  xai: 'Grok (xAI)',
  anthropic: 'Anthropic (Claude)',
};

export const LlmSettingsModal: React.FC<Props> = ({ isOpen, onClose, onSaved }) => {
  const [data, setData] = useState<LlmSettings | null>(null);
  const [openai, setOpenai] = useState('');
  const [xai, setXai] = useState('');
  const [anthropic, setAnthropic] = useState('');
  const [provider, setProvider] = useState<'openai' | 'xai' | 'anthropic'>('openai');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setError('');
    setOpenai('');
    setXai('');
    setAnthropic('');
    void api.settings
      .llm()
      .then((row) => {
        setData(row);
        setProvider(row.chat_provider);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : 'Failed to load settings');
      });
  }, [isOpen]);

  if (!isOpen) return null;

  const save = async () => {
    setSaving(true);
    setError('');
    const body: Record<string, string> = { chat_provider: provider };
    if (openai.trim()) body.openai_api_key = openai.trim();
    if (xai.trim()) body.xai_api_key = xai.trim();
    if (anthropic.trim()) body.anthropic_api_key = anthropic.trim();
    try {
      const saved = await api.settings.updateLlm(body);
      setData(saved);
      setOpenai('');
      setXai('');
      setAnthropic('');
      onSaved?.(saved);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const clearKey = async (field: 'openai_api_key' | 'xai_api_key' | 'anthropic_api_key') => {
    setSaving(true);
    try {
      const saved = await api.settings.updateLlm({ [field]: '' });
      setData(saved);
      onSaved?.(saved);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to clear key');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 z-50">
      <div className="relative top-16 mx-auto p-6 border w-full max-w-lg shadow-lg rounded-md bg-white">
        <h3 className="text-lg font-medium text-gray-900 mb-2">AI providers</h3>
        <p className="text-sm text-gray-600 mb-4">
          Paste API keys (never shown again). Chat uses the selected provider. Uploads still embed with
          OpenAI <code>text-embedding-3-small</code> because Anthropic has no embeddings API.
        </p>
        {error && <div className="mb-3 text-sm text-red-700">{error}</div>}
        {(['openai', 'xai', 'anthropic'] as const).map((name) => (
          <div key={name} className="mb-4">
            <label className="flex items-center justify-between text-sm font-medium text-gray-700">
              <span>
                {LABELS[name]}
                {data?.[name].configured ? (
                  <span className="ml-2 text-green-700 font-normal">configured</span>
                ) : (
                  <span className="ml-2 text-gray-400 font-normal">not set</span>
                )}
              </span>
              {data?.[name].configured && (
                <button type="button" className="text-xs text-red-600" onClick={() => void clearKey(`${name}_api_key`)}>
                  Remove
                </button>
              )}
            </label>
            <input
              type="password"
              autoComplete="off"
              placeholder={data?.[name].configured ? '•••••••• (leave blank to keep)' : 'Paste API key'}
              className="mt-1 w-full px-3 py-2 border rounded-md text-sm"
              value={name === 'openai' ? openai : name === 'xai' ? xai : anthropic}
              onChange={(e) =>
                name === 'openai' ? setOpenai(e.target.value) : name === 'xai' ? setXai(e.target.value) : setAnthropic(e.target.value)
              }
            />
          </div>
        ))}
        <fieldset className="mb-4">
          <legend className="text-sm font-medium text-gray-700 mb-2">Chat with</legend>
          {(['openai', 'xai', 'anthropic'] as const).map((name) => (
            <label key={name} className="flex items-center space-x-2 text-sm mb-1">
              <input
                type="radio"
                name="chat_provider"
                value={name}
                checked={provider === name}
                onChange={() => setProvider(name)}
              />
              <span>
                {LABELS[name]}
                {data?.chat_models[name] ? ` · ${data.chat_models[name]}` : ''}
              </span>
            </label>
          ))}
        </fieldset>
        <div className="flex justify-end space-x-3">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm border rounded-md">
            Cancel
          </button>
          <button
            type="button"
            onClick={() => void save()}
            disabled={saving}
            className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};
