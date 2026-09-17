import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInterface } from './ChatInterface';
import { ToastProvider } from '../../context/ToastContext';

const history = [
  {
    id: 'u1',
    role: 'user',
    content: 'what color?',
    created_at: '2026-01-01T00:00:00Z',
    sources: [],
  },
  {
    id: 'a1',
    role: 'assistant',
    content: 'teal',
    created_at: '2026-01-01T00:00:01Z',
    sources: [
      {
        chunk_id: 'c1',
        document_id: 'd1',
        file_name: 'notes.txt',
        content: 'the sky is teal',
        similarity: 0.82,
      },
    ],
  },
];

describe('ChatInterface', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (init?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            user_message: {
              id: 'u2',
              role: 'user',
              content: 'next',
              created_at: '2026-01-01T00:00:02Z',
              sources: [],
            },
            assistant_message: {
              id: 'a2',
              role: 'assistant',
              content: 'from envelope',
              created_at: '2026-01-01T00:00:03Z',
              sources: history[1].sources,
            },
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => history,
      });
    }) as unknown as typeof fetch;
  });

  it('renders GET history sources and uses assistant_message on send', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ChatInterface threadId="t1" threadTitle="Lab" />
      </ToastProvider>,
    );
    expect(await screen.findByText('teal')).toBeInTheDocument();
    expect(screen.getByText('the sky is teal')).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText('Ask a question about your documents...'), 'next');
    await user.click(screen.getByRole('button', { name: 'Send' }));
    expect(await screen.findByText('from envelope')).toBeInTheDocument();

    const postCall = (global.fetch as jest.Mock).mock.calls.find((call) => call[1]?.method === 'POST');
    expect(postCall[0]).toBe('/api/threads/t1/messages');
  });
});
