import React, { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useToast } from '../../context/ToastContext';
import type { Message } from '../../types';
import { LoadingSpinner } from '../UI/LoadingSpinner';

interface ChatInterfaceProps {
  threadId: string;
  threadTitle: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ threadId, threadTitle }) => {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const history = await api.messages.list(threadId);
        setMessages(history);
      } catch {
        setError('Failed to load chat history');
      }
    };
    void load();
  }, [threadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;
    const content = inputMessage.trim();
    setInputMessage('');
    setLoading(true);
    setError('');
    try {
      const data = await api.messages.create(threadId, content);
      setMessages((prev) => [...prev, data.user_message, data.assistant_message]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'An unexpected error occurred';
      setError(message);
      showToast('error', `Query failed: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (value: string) =>
    new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">{threadTitle}</h2>
        <p className="text-sm text-gray-500">
          {messages.length > 0 ? `${messages.length} messages` : 'Start a conversation'}
        </p>
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border text-gray-900'
              }`}
            >
              <div className="text-sm">{message.content}</div>
              {message.role === 'assistant' && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500 mb-2">Sources:</p>
                  {message.sources.slice(0, 3).map((source) => (
                    <div key={source.chunk_id} className="text-xs bg-gray-50 p-2 rounded mb-1">
                      <div className="text-gray-600">{source.file_name}</div>
                      <div className="text-gray-800 line-clamp-2">{source.content}</div>
                    </div>
                  ))}
                </div>
              )}
              <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-gray-500'}`}>
                {formatTime(message.created_at)}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border px-4 py-2 rounded-lg">
              <LoadingSpinner size="sm" text="Generating response..." />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="px-6 py-3 bg-red-50 text-sm text-red-700">{error}</div>}
      <form onSubmit={handleSubmit} className="bg-white border-t px-6 py-4 flex space-x-4">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={loading}
          className="flex-1 border rounded-lg px-4 py-2"
        />
        <button
          type="submit"
          disabled={!inputMessage.trim() || loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
};
