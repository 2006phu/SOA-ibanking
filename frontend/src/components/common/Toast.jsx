import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircleIcon, AlertCircleIcon, InfoIcon } from './Icons';

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, duration);
  }, []);

  const success = useCallback((msg) => addToast(msg, 'success'), [addToast]);
  const error = useCallback((msg) => addToast(msg, 'error'), [addToast]);
  const info = useCallback((msg) => addToast(msg, 'info'), [addToast]);

  return (
    <ToastContext.Provider value={{ addToast, success, error, info }}>
      {children}
      <div className="toast-container" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast-${t.type}`} style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}>
              {t.type === 'success' && <CheckCircleIcon size={18} />}
              {t.type === 'error' && <AlertCircleIcon size={18} />}
              {t.type === 'info' && <InfoIcon size={18} />}
            </span>
            <div style={{ flex: 1 }}>{t.message}</div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
