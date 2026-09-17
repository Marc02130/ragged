import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useToast } from '../../context/ToastContext';
import type { Thread } from '../../types';
import { ConfirmationModal } from '../UI/ConfirmationModal';
import { LoadingSpinner } from '../UI/LoadingSpinner';

interface ThreadListProps {
  currentThreadId?: string;
  onThreadSelect: (thread: Thread) => void;
  onThreadCreate: () => void;
  onThreadDelete: (threadId: string) => void;
}

export const ThreadList: React.FC<ThreadListProps> = ({
  currentThreadId,
  onThreadSelect,
  onThreadCreate,
  onThreadDelete,
}) => {
  const { showToast } = useToast();
  const [threadList, setThreadList] = useState<Thread[]>([]);
  const [archivedThreads, setArchivedThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState('');
  const [deleteModal, setDeleteModal] = useState({
    isOpen: false,
    threadId: '',
    threadTitle: '',
    loading: false,
  });

  const loadThreads = async () => {
    setLoading(true);
    setError('');
    try {
      const data = (await api.threads.list(false)) as Thread[];
      setThreadList(data);
    } catch {
      setError('Failed to load threads');
    } finally {
      setLoading(false);
    }
  };

  const loadArchived = async () => {
    try {
      const data = (await api.threads.list(true)) as Thread[];
      setArchivedThreads(data.filter((thread) => thread.status === 'archived'));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to load archived threads';
      showToast('error', message);
    }
  };

  useEffect(() => {
    void loadThreads();
  }, []);

  useEffect(() => {
    if (showArchived) {
      void loadArchived();
    }
  }, [showArchived]);

  const handleArchive = async (thread: Thread) => {
    try {
      await api.threads.archive(thread.id);
      showToast('success', `Thread "${thread.title}" archived successfully`);
      await loadThreads();
    } catch (err) {
      showToast('error', err instanceof ApiError ? err.message : 'Failed to archive thread');
    }
  };

  const handleRestore = async (thread: Thread) => {
    try {
      await api.threads.restore(thread.id);
      showToast('success', `Thread "${thread.title}" restored successfully`);
      await loadArchived();
      await loadThreads();
    } catch (err) {
      showToast('error', err instanceof ApiError ? err.message : 'Failed to restore thread');
    }
  };

  const confirmDelete = async () => {
    setDeleteModal((prev) => ({ ...prev, loading: true }));
    try {
      await api.threads.delete(deleteModal.threadId);
      showToast('success', 'Thread deleted');
      await loadThreads();
      onThreadDelete(deleteModal.threadId);
    } catch (err) {
      showToast('error', err instanceof ApiError ? err.message : 'Failed to delete thread');
    } finally {
      setDeleteModal({ isOpen: false, threadId: '', threadTitle: '', loading: false });
    }
  };

  if (loading) {
    return (
      <div className="bg-white border-r border-gray-200 w-80 flex items-center justify-center">
        <LoadingSpinner size="lg" text="Loading threads..." />
      </div>
    );
  }

  return (
    <div className="bg-white border-r border-gray-200 w-80 flex flex-col" data-testid="thread-list">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Threads</h2>
          <button
            type="button"
            onClick={onThreadCreate}
            className="px-3 py-1 text-sm font-medium rounded-md text-white bg-blue-600"
          >
            New
          </button>
        </div>
        <button type="button" onClick={() => setShowArchived(!showArchived)} className="text-sm text-gray-600">
          {showArchived ? 'Hide Archived' : 'Show Archived'}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {error && <div className="p-4 text-sm text-red-600">{error}</div>}
        {threadList.length === 0 && !error && (
          <div className="p-4 text-center text-sm text-gray-500">No threads yet</div>
        )}
        <div className="divide-y divide-gray-200">
          {threadList.map((thread) => (
            <div
              key={thread.id}
              data-testid={`thread-${thread.id}`}
              className={`p-4 cursor-pointer hover:bg-gray-50 ${
                currentThreadId === thread.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
              }`}
              onClick={() => onThreadSelect(thread)}
            >
              <div className="flex items-start justify-between">
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">{thread.title}</h3>
                  <p className="text-xs text-gray-500">{thread.document_count} documents</p>
                </div>
                <div className="flex space-x-1">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      void handleArchive(thread);
                    }}
                    className="text-xs text-gray-500"
                  >
                    Archive
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteModal({
                        isOpen: true,
                        threadId: thread.id,
                        threadTitle: thread.title,
                        loading: false,
                      });
                    }}
                    className="text-xs text-red-500"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        {showArchived && (
          <div className="border-t border-gray-200 p-4 bg-gray-50">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Archived Threads</h3>
            {archivedThreads.map((thread) => (
              <div key={thread.id} className="p-3 bg-white rounded border mb-2">
                <h4 className="text-sm font-medium truncate">{thread.title}</h4>
                <button type="button" onClick={() => void handleRestore(thread)} className="text-xs text-green-600">
                  Restore
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Delete Thread"
        message={`Are you sure you want to delete "${deleteModal.threadTitle}"?`}
        confirmText="Delete Thread"
        type="danger"
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteModal((prev) => ({ ...prev, isOpen: false }))}
        loading={deleteModal.loading}
      />
    </div>
  );
};
