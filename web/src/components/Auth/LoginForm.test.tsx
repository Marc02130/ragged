import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';
import { AuthProvider } from '../../context/AuthContext';
import { ToastProvider } from '../../context/ToastContext';

function renderLogin() {
  return render(
    <ToastProvider>
      <AuthProvider>
        <LoginForm onSuccess={() => undefined} onSwitchToSignUp={() => undefined} />
      </AuthProvider>
    </ToastProvider>,
  );
}

describe('LoginForm', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockImplementation((url: string) => {
      if (url === '/api/auth/me') {
        return Promise.resolve({
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Not authenticated' }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ id: '1', email: 'a@b.com', created_at: '2026-01-01T00:00:00Z' }),
      });
    }) as unknown as typeof fetch;
  });

  it('posts login to /api/auth/login', async () => {
    const user = userEvent.setup();
    renderLogin();
    await screen.findByPlaceholderText('Email address');
    await user.type(screen.getByPlaceholderText('Email address'), 'a@b.com');
    await user.type(screen.getByPlaceholderText('Password'), 'correct-horse');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    const calls = (global.fetch as jest.Mock).mock.calls.map((call) => call[0]);
    expect(calls).toContain('/api/auth/login');
    expect(calls.some((url: string) => url === '/auth/login')).toBe(false);
  });
});
