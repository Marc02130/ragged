import React, { useState } from 'react';
import { ApiError } from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

interface SignUpFormProps {
  onSuccess: () => void;
  onSwitchToLogin: () => void;
}

export const SignUpForm: React.FC<SignUpFormProps> = ({ onSuccess, onSwitchToLogin }) => {
  const { register } = useAuth();
  const { showToast } = useToast();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }
    setLoading(true);
    try {
      await register(email, password);
      showToast('success', 'Account created');
      onSuccess();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'An unexpected error occurred';
      setError(message);
      showToast('error', `Sign up failed: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">Create your account</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start chatting with your documents using AI
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className="appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-t-md sm:text-sm"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            className="appearance-none relative block w-full px-3 py-2 border border-gray-300 sm:text-sm"
            placeholder="Password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <input
            id="confirmPassword"
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            className="appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-b-md sm:text-sm"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
          />
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Create account'}
          </button>
          <div className="text-center">
            <button type="button" onClick={onSwitchToLogin} className="text-sm text-blue-600">
              Already have an account? Sign in
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
