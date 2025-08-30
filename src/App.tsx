import React, { useState, useEffect } from 'react';
import { auth } from './lib/supabase';
import { Header } from './components/Layout/Header';
import { LoginForm } from './components/Auth/LoginForm';
import { SignUpForm } from './components/Auth/SignUpForm';
import { ThreadList } from './components/Threads/ThreadList';
import { CreateThreadModal } from './components/Threads/CreateThreadModal';
import { DocumentUpload } from './components/Documents/DocumentUpload';
import { ChatInterface } from './components/Chat/ChatInterface';
import { ErrorBoundary } from './components/UI/ErrorBoundary';
import { ToastContainer } from './components/UI/ToastContainer';
import type { User, Thread, Document } from './types';

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [currentThread, setCurrentThread] = useState<Thread | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [showSignUp, setShowSignUp] = useState(false);
  const [showCreateThread, setShowCreateThread] = useState(false);
  const [loading, setLoading] = useState(true);

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const { user: currentUser } = await auth.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Listen for auth state changes
    const { data: { subscription } } = auth.onAuthStateChange((user) => {
      if (user) {
        setUser({
          id: user.id,
          email: user.email || '',
          created_at: user.created_at
        });
      } else {
        setUser(null);
        // Clear state when user signs out
        setCurrentThread(null);
        setDocuments([]);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = () => {
    setUser(null);
    setCurrentThread(null);
    setDocuments([]);
  };

  const handleThreadSelect = (thread: Thread) => {
    setCurrentThread(thread);
  };

  const handleThreadCreate = () => {
    setShowCreateThread(true);
  };

  const handleThreadCreated = (thread: Thread) => {
    setCurrentThread(thread);
    setShowCreateThread(false);
  };

  const handleThreadDelete = (threadId: string) => {
    if (currentThread?.thread_id === threadId) {
      setCurrentThread(null);
      setDocuments([]);
    }
  };

  const handleUploadComplete = (newDocuments: Document[]) => {
    setDocuments(prev => [...newDocuments, ...prev]);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show auth forms if not logged in
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50">
        {showSignUp ? (
          <SignUpForm
            onSuccess={() => setShowSignUp(false)}
            onSwitchToLogin={() => setShowSignUp(false)}
          />
        ) : (
          <LoginForm
            onSuccess={() => {}} // Auth state change will handle this
            onSwitchToSignUp={() => setShowSignUp(true)}
          />
        )}
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <ToastContainer>
        <div className="min-h-screen bg-gray-50">
          <Header user={user} onSignOut={handleSignOut} />
          
          <div className="flex h-screen">
            {/* Thread List Sidebar */}
            <ThreadList
              currentThreadId={currentThread?.thread_id}
              onThreadSelect={handleThreadSelect}
              onThreadCreate={handleThreadCreate}
              onThreadDelete={handleThreadDelete}
            />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col">
              {currentThread ? (
                <>
                  {/* Document Upload Section */}
                  <div className="p-6 border-b border-gray-200">
                    <DocumentUpload
                      threadId={currentThread.thread_id}
                      onUploadComplete={handleUploadComplete}
                    />
                  </div>

                  {/* Chat Interface */}
                  <div className="flex-1">
                    <ChatInterface
                      threadId={currentThread.thread_id}
                      threadTitle={currentThread.title}
                    />
                  </div>
                </>
              ) : (
                /* Welcome Screen */
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-gray-400 mb-4">
                      <svg className="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to RAGged</h2>
                    <p className="text-gray-600 mb-6">
                      Select a thread or create a new one to start chatting with your documents
                    </p>
                    <button
                      onClick={handleThreadCreate}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      Create New Thread
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Create Thread Modal */}
          <CreateThreadModal
            isOpen={showCreateThread}
            onClose={() => setShowCreateThread(false)}
            onThreadCreated={handleThreadCreated}
          />
        </div>
      </ToastContainer>
    </ErrorBoundary>
  );
}

export default App;
