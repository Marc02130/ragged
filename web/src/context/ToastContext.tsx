import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { Toast, type ToastType } from '../components/UI/Toast';

type ToastItem = { id: number; type: ToastType; message: string };

type ToastContextValue = {
  showToast: (type: ToastType, message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback((type: ToastType, message: string) => {
    setToasts((current) => [...current, { id: Date.now() + Math.random(), type, message }]);
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          type={toast.type}
          message={toast.message}
          onClose={() => setToasts((current) => current.filter((item) => item.id !== toast.id))}
        />
      ))}
    </ToastContext.Provider>
  );
};

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return ctx;
}
