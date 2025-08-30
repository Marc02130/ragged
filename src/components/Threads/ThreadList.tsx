import React, { useState, useEffect } from 'react';
import { threads } from '../../lib/supabase';
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
  const [threadList, setThreadList] = useState<Thread[]>([]);
  const [archivedThreads, setArchivedThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingArchived, setLoadingArchived] = useState(false);
  const [error, setError] = useState('');
  const [showArchived, setShowArchived] = useState(false);

  const loadThreads = async () => {
    setLoading(true);
    setError('');

    try {
      const { data, error } = await threads.list(false); // Active threads only
      
      if (error) {
        setError(error);
      } else {
        setThreadList(data);
      }
    } catch (err) {
      setError('Failed to load threads');
    } finally {
      setLoading(false);
    }
  };

  const loadArchivedThreads = async () => {
    setLoadingArchived(true);
    try {
      const { data, error } = await threads.list(true); // Include archived
      
      if (error) {
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('error', `Failed to load archived threads: ${error}`);
        }
      } else {
        const archived = data.filter(thread => thread.status === 'archived');
        setArchivedThreads(archived);
      }
    } catch (err) {
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast('error', 'Failed to load archived threads');
      }
    } finally {
      setLoadingArchived(false);
    }
  };

  const handleArchiveThread = async (threadId: string, threadTitle: string) => {
    try {
      const { error } = await threads.archive(threadId);
      
      if (error) {
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('error', `Failed to archive thread: ${error}`);
        }
      } else {
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('success', `Thread "${threadTitle}" archived successfully`);
        }
        await loadThreads();
      }
    } catch (err) {
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast('error', 'Failed to archive thread');
      }
    }
  };

  const handleRestoreThread = async (threadId: string, threadTitle: string) => {
    try {
      const { error } = await threads.restore(threadId);
      
      if (error) {
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('error', `Failed to restore thread: ${error}`);
        }
      } else {
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('success', `Thread "${threadTitle}" restored successfully`);
        }
        await loadArchivedThreads();
        await loadThreads();
      }
    } catch (err) {
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast('error', 'Failed to restore thread');
      }
    }
  };

  useEffect(() => {
    loadThreads();
  }, []);

  useEffect(() => {
    if (showArchived) {
      loadArchivedThreads();
    }
  }, [showArchived]);

  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    threadId: string;
    threadTitle: string;
    loading: boolean;
  }>({
    isOpen: false,
    threadId: '',
    threadTitle: '',
    loading: false,
  });

  const handleDeleteThread = async (threadId: string, threadTitle: string) => {
    setDeleteModal({
      isOpen: true,
      threadId,
      threadTitle,
      loading: false,
    });
  };

  const confirmDeleteThread = async () => {
    setDeleteModal(prev => ({ ...prev, loading: true }));

    try {
      const { error } = await threads.delete(deleteModal.threadId);
      
      if (error) {
        // Show error toast
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('error', `Failed to delete thread: ${error}`);
        }
      } else {
        // Show success toast
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('success', 'Thread deleted and archived successfully');
        }
        
        // Reload threads after deletion
        await loadThreads();
        onThreadDelete(deleteModal.threadId);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred while deleting the thread';
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast('error', errorMessage);
      }
    } finally {
      setDeleteModal(prev => ({ ...prev, loading: false, isOpen: false }));
    }
  };

  const cancelDeleteThread = () => {
    setDeleteModal(prev => ({ ...prev, isOpen: false }));
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  if (loading) {
    return (
      <div className="bg-white border-r border-gray-200 w-80 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Threads</h2>
            <button
              onClick={onThreadCreate}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New
            </button>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="lg" text="Loading threads..." />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-r border-gray-200 w-80 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Threads</h2>
          <button
            onClick={onThreadCreate}
            className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New
          </button>
        </div>
        
        {/* Archive Toggle */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            {showArchived ? 'Hide Archived' : 'Show Archived'}
          </button>
          {showArchived && (
            <span className="text-xs text-gray-500">
              {archivedThreads.length} archived
            </span>
          )}
        </div>
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="p-4">
            <div className="text-sm text-red-600">{error}</div>
            <button
              onClick={loadThreads}
              className="mt-2 text-sm text-blue-600 hover:text-blue-500"
            >
              Try again
            </button>
          </div>
        )}

        {threadList.length === 0 && !error && (
          <div className="p-4 text-center">
            <p className="text-sm text-gray-500">No threads yet</p>
            <button
              onClick={onThreadCreate}
              className="mt-2 text-sm text-blue-600 hover:text-blue-500"
            >
              Create your first thread
            </button>
          </div>
        )}

        <div className="divide-y divide-gray-200">
          {threadList.map((thread) => (
            <div
              key={thread.id}
              className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                currentThreadId === thread.id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
              }`}
              onClick={() => onThreadSelect(thread)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {thread.title}
                  </h3>
                  <div className="flex items-center mt-1 text-xs text-gray-500">
                    <span>{thread.document_count} documents</span>
                    <span className="mx-1">•</span>
                    <span>{formatDate(thread.last_activity_at)}</span>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleArchiveThread(thread.id, thread.title);
                    }}
                    className="p-1 text-gray-400 hover:text-yellow-500 transition-colors"
                    title="Archive thread"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                    </svg>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteThread(thread.id, thread.title);
                    }}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    title="Delete thread"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Archived Threads */}
        {showArchived && (
          <div className="border-t border-gray-200">
            <div className="p-4 bg-gray-50">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Archived Threads</h3>
              {loadingArchived ? (
                <LoadingSpinner size="sm" text="Loading archived..." />
              ) : archivedThreads.length === 0 ? (
                <p className="text-sm text-gray-500">No archived threads</p>
              ) : (
                <div className="space-y-2">
                  {archivedThreads.map((thread) => (
                    <div
                      key={thread.id}
                      className="p-3 bg-white rounded border border-gray-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 truncate">
                            {thread.title}
                          </h4>
                          <div className="flex items-center mt-1 text-xs text-gray-500">
                            <span>{thread.document_count} documents</span>
                            <span className="mx-1">•</span>
                            <span>{formatDate(thread.last_activity_at)}</span>
                          </div>
                        </div>
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => handleRestoreThread(thread.id, thread.title)}
                            className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                            title="Restore thread"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                          </button>
                          <button
                            onClick={() => handleDeleteThread(thread.id, thread.title)}
                            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                            title="Delete thread permanently"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Delete Thread"
        message={`Are you sure you want to delete "${deleteModal.threadTitle}"? This will archive the conversation and delete the live chat data.`}
        confirmText="Delete Thread"
        cancelText="Cancel"
        type="danger"
        onConfirm={confirmDeleteThread}
        onCancel={cancelDeleteThread}
        loading={deleteModal.loading}
      />
    </div>
  );
}; 