import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
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
});
