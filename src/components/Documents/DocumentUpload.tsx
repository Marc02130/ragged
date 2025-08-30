import React, { useState, useRef } from 'react';
import { documents } from '../../lib/supabase';
import type { Document, FileUploadProgress } from '../../types';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { ProgressBar } from '../UI/ProgressBar';

interface DocumentUploadProps {
  threadId: string;
  onUploadComplete: (documents: Document[]) => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  threadId,
  onUploadComplete,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadProgress[]>([]);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // File validation constants
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ALLOWED_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/rtf'
  ];

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File ${file.name} exceeds 10MB limit`;
    }

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `File type ${file.type} not supported. Allowed: PDF, DOCX, TXT, RTF`;
    }

    return null;
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    // Validate all files
    const errors: string[] = [];
    const validFiles: File[] = [];

    files.forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(error);
      } else {
        validFiles.push(file);
      }
    });

    if (errors.length > 0) {
      setError(errors.join('\n'));
      return;
    }

    if (validFiles.length > 0) {
      uploadFiles(validFiles);
    }
  };

  const uploadFiles = async (files: File[]) => {
    setUploading(true);
    setError('');
    
    // Initialize progress tracking
    const progress: FileUploadProgress[] = files.map(file => ({
      file,
      progress: 0,
      status: 'uploading'
    }));
    setUploadProgress(progress);

    try {
      const { data, error } = await documents.upload(files, threadId);
      
      if (error) {
        setError(error);
        // Update progress to show errors
        setUploadProgress(prev => prev.map(p => ({
          ...p,
          status: 'error' as const,
          error: error
        })));
        
        // Show error toast
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('error', `Upload failed: ${error}`);
        }
      } else {
        // Update progress to show completion
        setUploadProgress(prev => prev.map(p => ({
          ...p,
          progress: 100,
          status: 'complete' as const
        })));
        
        onUploadComplete(data);
        
        // Show success toast
        if (typeof window !== 'undefined' && (window as any).showToast) {
          (window as any).showToast('success', `${data.length} document(s) uploaded successfully`);
        }
        
        // Clear file input
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setUploadProgress(prev => prev.map(p => ({
        ...p,
        status: 'error' as const,
        error: errorMessage
      })));
      
      // Show error toast
      if (typeof window !== 'undefined' && (window as any).showToast) {
        (window as any).showToast('error', `Upload failed: ${errorMessage}`);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    if (files.length > 0) {
      uploadFiles(files);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'application/pdf':
        return '📄';
      case 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return '📝';
      case 'text/plain':
        return '📄';
      case 'application/rtf':
        return '📝';
      default:
        return '📁';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Documents</h3>
      
      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
          uploading ? 'border-gray-300 bg-gray-50' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <div className="space-y-4">
          <div className="text-gray-400">
            <svg className="mx-auto h-12 w-12" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          
          <div>
            <p className="text-sm text-gray-600">
              Drag and drop files here, or{' '}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="text-blue-600 hover:text-blue-500 font-medium disabled:opacity-50"
              >
                browse
              </button>
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Supported: PDF, DOCX, TXT, RTF (max 10MB each)
            </p>
          </div>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.txt,.rtf"
        onChange={handleFileSelect}
        className="hidden"
        disabled={uploading}
      />

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="text-sm text-red-700 whitespace-pre-line">{error}</div>
        </div>
      )}

      {/* Upload Progress */}
      {uploadProgress.length > 0 && (
        <div className="mt-4 space-y-3">
          <h4 className="text-sm font-medium text-gray-900">Upload Progress</h4>
          {uploadProgress.map((item, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-md">
              <div className="flex items-center space-x-3 mb-2">
                <span className="text-lg">{getFileIcon(item.file.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {item.file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(item.file.size)}
                  </p>
                </div>
              </div>
              <ProgressBar
                progress={item.progress}
                status={item.status}
                text={item.status === 'uploading' ? 'Uploading...' : 
                      item.status === 'processing' ? 'Vectorizing...' :
                      item.status === 'complete' ? 'Ready for queries' :
                      item.status === 'error' ? item.error : ''}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 