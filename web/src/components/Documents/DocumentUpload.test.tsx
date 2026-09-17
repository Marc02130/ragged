import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentUpload } from './DocumentUpload';
import { ToastProvider } from '../../context/ToastContext';

describe('DocumentUpload', () => {
  beforeEach(() => {
    global.fetch = jest.fn() as unknown as typeof fetch;
  });

  it('validates files on drop before uploading', () => {
    render(
      <ToastProvider>
        <DocumentUpload threadId="t1" onUploadComplete={() => undefined} />
      </ToastProvider>,
    );
    const zone = screen.getByTestId('upload-dropzone');
    const bad = new File(['mz'], 'malware.exe', { type: 'application/x-msdownload' });
    fireEvent.drop(zone, { dataTransfer: { files: [bad] } });
    expect(screen.getByText(/not supported/i)).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('does not success-toast when 201 body is status failed', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => [
        {
          id: 'd1',
          thread_id: 't1',
          file_name: 'junk.txt',
          file_size: 10,
          file_type: 'text/plain',
          title: 'junk.txt',
          status: 'failed',
          embedding_model: null,
          chunk_count: 0,
          error_message: 'no usable text after dropping junk chunks',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
    });
    render(
      <ToastProvider>
        <DocumentUpload threadId="t1" onUploadComplete={() => undefined} />
      </ToastProvider>,
    );
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(
      ['We hypothesize that this file is long enough to pass client type checks only.'],
      'note.txt',
      { type: 'text/plain' },
    );
    await userEvent.setup().upload(input, file);
    expect(
      await screen.findAllByText(/no usable text after dropping junk chunks/i),
    ).not.toHaveLength(0);
    expect(screen.queryByText(/uploaded successfully/i)).not.toBeInTheDocument();
  });
});
