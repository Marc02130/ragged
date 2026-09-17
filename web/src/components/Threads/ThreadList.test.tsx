import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { ThreadList } from './ThreadList';
import { ToastProvider } from '../../context/ToastContext';
import type { Thread } from '../../types';

const thread: Thread = {
  id: 'abc',
  title: 'Lab notes',
  status: 'active',
  document_count: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  last_activity_at: '2026-01-01T00:00:00Z',
};

describe('ThreadList', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [thread],
    }) as unknown as typeof fetch;
  });

  it('highlights the selected thread by id', async () => {
    render(
      <ToastProvider>
        <ThreadList
          currentThreadId="abc"
          onThreadSelect={() => undefined}
          onThreadCreate={() => undefined}
          onThreadDelete={() => undefined}
        />
      </ToastProvider>,
    );
    const row = await screen.findByTestId('thread-abc');
    await waitFor(() => expect(row.className).toContain('bg-blue-50'));
  });
});
