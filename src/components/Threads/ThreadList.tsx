import React, { useState, useEffect } from 'react';
import { threads } from '../../lib/supabase';
import type { Thread } from '../../types';

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadThreads = async () => {
    setLoading(true);
    setError('');

    try {
      const { data, error } = await threads.list();
      
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

  useEffect(() => {
    loadThreads();
  }, []);

  const handleDeleteThread = async (threadId: string, threadTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${threadTitle}"? This will archive the conversation and delete the live chat data.`)) {
      return;
    }

    try {
      const { error } = await threads.delete(threadId);
      
      if (error) {
        alert(`Failed to delete thread: ${error}`);
      } else {
        // Reload threads after deletion
        await loadThreads();
        onThreadDelete(threadId);
      }
    } catch (err) {
      alert('An error occurred while deleting the thread');
    }
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
      <div className="p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border-r border-gray-200 w-80 flex flex-col">
      {/* Header */}
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
              key={thread.thread_id}
              className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                currentThreadId === thread.thread_id ? 'bg-blue-50 border-r-2 border-blue-500' : ''
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
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteThread(thread.thread_id, thread.title);
                  }}
                  className="ml-2 p-1 text-gray-400 hover:text-red-500 transition-colors"
                  title="Delete thread"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}; 