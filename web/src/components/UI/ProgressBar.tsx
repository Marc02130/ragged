import React from 'react';

interface ProgressBarProps {
  progress: number;
  status: 'uploading' | 'processing' | 'complete' | 'error';
  text?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status, text }) => {
  const color = {
    uploading: 'bg-blue-600',
    processing: 'bg-yellow-600',
    complete: 'bg-green-600',
    error: 'bg-red-600',
  }[status];

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{text || status}</span>
        <span className="text-sm font-medium text-gray-700">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`h-2 rounded-full ${color}`} style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
};
