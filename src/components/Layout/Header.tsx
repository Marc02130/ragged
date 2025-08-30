import React from 'react';
import { auth } from '../../lib/supabase';
import type { User } from '../../types';

interface HeaderProps {
  user: User | null;
  onSignOut: () => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onSignOut }) => {
  const handleSignOut = async () => {
    try {
      const { error } = await auth.signOut();
      if (error) {
        console.error('Sign out error:', error);
      } else {
        onSignOut();
      }
    } catch (err) {
      console.error('Sign out failed:', err);
    }
  };

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <h1 className="text-xl font-bold text-gray-900">RAGged</h1>
            <span className="ml-2 text-sm text-gray-500">Document Q&A with AI</span>
          </div>

          {/* User Menu */}
          {user && (
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-700">
                <span className="font-medium">{user.email}</span>
              </div>
              <button
                onClick={handleSignOut}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}; 