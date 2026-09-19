import React, { useRef, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useToast } from '../../context/ToastContext';
import type { Document } from '../../types';
import { ProgressBar } from '../UI/ProgressBar';

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
  'application/rtf',
];

export function validateFile(file: File): string | null {
  if (file.size > MAX_FILE_SIZE) {
    return `File ${file.name} exceeds 10MB limit`;
  }
  if (!ALLOWED_TYPES.includes(file.type)) {
    return `File type ${file.type} not supported. Allowed: PDF, DOCX, TXT, RTF`;
  }
  return null;
}

interface DocumentUploadProps {
  threadId: string;
  onUploadComplete: (documents: Document[]) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ threadId, onUploadComplete }) => {
  const { showToast } = useToast();
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState<{ file: File; progress: number; status: 'uploading' | 'complete' | 'error' }[]>(
    [],
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  const takeValidFiles = (files: File[]): File[] => {
    const errors: string[] = [];
    const valid: File[] = [];
    files.forEach((file) => {
      const reason = validateFile(file);
      if (reason) {
        errors.push(reason);
      } else {
        valid.push(file);
      }
    });
    if (errors.length > 0) {
      setError(errors.join('\n'));
      return [];
    }
    setError('');
    return valid;
  };

  const uploadFiles = async (files: File[]) => {
    setUploading(true);
    setProgress(files.map((file) => ({ file, progress: 0, status: 'uploading' as const })));
    const collected: Document[] = [];
    const failures: string[] = [];
    try {
      for (let index = 0; index < files.length; index += 1) {
        const file = files[index];
        try {
          const data = (await api.documents.upload(threadId, [file])) as Document[];
          collected.push(...data);
          const ready = data.filter((doc) => doc.status === 'ready');
          const failed = data.filter((doc) => doc.status === 'failed');
          failed.forEach((doc) => {
            failures.push(doc.error_message || `${file.name} failed`);
          });
          if (!ready.length && !failed.length) {
            failures.push(`${file.name} failed`);
          }
          if (ready.length) {
            onUploadComplete([...collected]);
          }
          setProgress((prev) =>
            prev.map((item, itemIndex) =>
              itemIndex === index
                ? {
                    ...item,
                    progress: 100,
                    status: ready.length ? 'complete' : 'error',
                  }
                : item,
            ),
          );
        } catch (err) {
          const message = err instanceof ApiError ? err.message : 'Upload failed';
          failures.push(`${file.name}: ${message}`);
          setProgress((prev) =>
            prev.map((item, itemIndex) =>
              itemIndex === index ? { ...item, status: 'error' as const } : item,
            ),
          );
        }
      }
      const readyCount = collected.filter((doc) => doc.status === 'ready').length;
      if (!readyCount && failures.length) {
        const msg = failures.join('\n') || 'No usable text in uploaded file(s)';
        setError(msg);
        showToast('error', msg);
      } else if (failures.length) {
        showToast('error', `${failures.length} file(s) failed: ${failures[0]}`);
        showToast('success', `${readyCount} document(s) uploaded successfully`);
      } else if (readyCount) {
        showToast('success', `${readyCount} document(s) uploaded successfully`);
      }
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const valid = takeValidFiles(files);
    if (valid.length > 0) {
      void uploadFiles(valid);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    const valid = takeValidFiles(files);
    if (valid.length > 0) {
      void uploadFiles(valid);
    }
  };

  return (
    <div>
      <div
        className="border-2 border-dashed rounded-lg p-3 text-center"
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
        data-testid="upload-dropzone"
      >
        <p className="text-sm text-gray-600">
          Drag and drop files here, or{' '}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="text-blue-600 font-medium"
          >
            browse
          </button>
        </p>
        <p className="text-xs text-gray-500 mt-1">Supported: PDF, DOCX, TXT, RTF (max 10MB each)</p>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.txt,.rtf"
        onChange={handleFileSelect}
        className="hidden"
        disabled={uploading}
      />
      {error && <div className="mt-4 text-sm text-red-700 whitespace-pre-line">{error}</div>}
      {progress.map((item, index) => (
        <div key={index} className="mt-3">
          <p className="text-sm truncate">{item.file.name}</p>
          <ProgressBar progress={item.progress} status={item.status} />
        </div>
      ))}
    </div>
  );
};
