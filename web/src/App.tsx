import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ErrorBoundary } from './components/UI/ErrorBoundary';
import { LoadingSpinner } from './components/UI/LoadingSpinner';
import { LoginForm } from './components/Auth/LoginForm';
import { SignUpForm } from './components/Auth/SignUpForm';
import { Header } from './components/Layout/Header';
import { ThreadList } from './components/Threads/ThreadList';
import { CreateThreadModal } from './components/Threads/CreateThreadModal';
import { DocumentUpload } from './components/Documents/DocumentUpload';
import { ChatInterface } from './components/Chat/ChatInterface';
import type { Document, Thread } from './types';

const Shell: React.FC = () => {
  const { user, loading } = useAuth();
  const [showSignUp, setShowSignUp] = useState(false);
  const [showCreateThread, setShowCreateThread] = useState(false);
  const [currentThread, setCurrentThread] = useState<Thread | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    );
  }

  if (!user) {
    return showSignUp ? (
      <SignUpForm onSuccess={() => setShowSignUp(false)} onSwitchToLogin={() => setShowSignUp(false)} />
    ) : (
      <LoginForm onSuccess={() => undefined} onSwitchToSignUp={() => setShowSignUp(true)} />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex" style={{ height: 'calc(100vh - 4rem)' }}>
        <ThreadList
          currentThreadId={currentThread?.id}
          onThreadSelect={(thread) => {
            setCurrentThread(thread);
            setDocuments([]);
          }}
          onThreadCreate={() => setShowCreateThread(true)}
          onThreadDelete={(id) => {
            if (currentThread?.id === id) {
              setCurrentThread(null);
              setDocuments([]);
            }
          }}
        />
        <div className="flex-1 flex flex-col">
          {currentThread ? (
            <>
              <div className="p-6 border-b border-gray-200">
                <DocumentUpload
                  threadId={currentThread.id}
                  onUploadComplete={(docs) => setDocuments((prev) => [...docs, ...prev])}
                />
                {documents.length > 0 && (
                  <p className="mt-2 text-sm text-gray-500">{documents.length} document(s) in this session</p>
                )}
              </div>
              <div className="flex-1 min-h-0">
                <ChatInterface threadId={currentThread.id} threadTitle={currentThread.title} />
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to RAGged</h2>
                <p className="text-gray-600 mb-6">Select a thread or create a new one to start chatting with your documents</p>
                <button
                  type="button"
                  onClick={() => setShowCreateThread(true)}
                  className="px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600"
                >
                  Create New Thread
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      <CreateThreadModal
        isOpen={showCreateThread}
        onClose={() => setShowCreateThread(false)}
        onThreadCreated={(thread) => {
          setCurrentThread(thread);
          setShowCreateThread(false);
        }}
      />
    </div>
  );
};

export const App: React.FC = () => (
  <ErrorBoundary>
    <ToastProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </ToastProvider>
  </ErrorBoundary>
);
