import React, { useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useToast } from '../../context/ToastContext';
import type { Thread } from '../../types';

interface CreateThreadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onThreadCreated: (thread: Thread) => void;
}

export const CreateThreadModal: React.FC<CreateThreadModalProps> = ({
  isOpen,
  onClose,
  onThreadCreated,
}) => {
  const { showToast } = useToast();
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleClose = () => {
    setTitle('');
    setError('');
    setLoading(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || loading) return;
    setLoading(true);
    setError('');
    try {
      const thread = (await api.threads.create(title.trim())) as Thread;
      showToast('success', 'Thread created successfully');
      onThreadCreated(thread);
      handleClose();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to create thread';
      setError(message);
      showToast('error', `Failed to create thread: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Thread</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label htmlFor="thread-title" className="block text-sm font-medium text-gray-700">
            Thread Title
          </label>
          <input
            id="thread-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter thread title..."
            required
            maxLength={100}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            disabled={loading}
          />
          {error && <div className="text-sm text-red-700">{error}</div>}
          <div className="flex justify-end space-x-3">
            <button type="button" onClick={handleClose} disabled={loading} className="px-4 py-2 text-sm border rounded-md">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || loading}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Thread'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
