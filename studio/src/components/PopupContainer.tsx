import { useEffect } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import type { Toast, ToastType } from '../hooks/useToast';

interface PopupItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function PopupItem({ toast, onRemove }: PopupItemProps) {
  useEffect(() => {
    if (toast.duration && toast.duration > 0) {
      const timer = setTimeout(() => {
        onRemove(toast.id);
      }, toast.duration);
      
      return () => clearTimeout(timer);
    }
  }, [toast.duration, toast.id, onRemove]);

  const getIcon = (type: ToastType) => {
    const className = "h-8 w-8";
    switch (type) {
      case 'success':
        return <CheckCircleIcon className={`${className} text-green-500`} />;
      case 'error':
        return <XCircleIcon className={`${className} text-red-500`} />;
      case 'warning':
        return <ExclamationTriangleIcon className={`${className} text-yellow-500`} />;
      case 'info':
        return <InformationCircleIcon className={`${className} text-blue-500`} />;
    }
  };

  const getColors = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 dark:bg-green-900/30 border-green-300 dark:border-green-600';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/30 border-red-300 dark:border-red-600';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-600';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600';
    }
  };

  const getTitleColor = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'text-green-900 dark:text-green-100';
      case 'error':
        return 'text-red-900 dark:text-red-100';
      case 'warning':
        return 'text-yellow-900 dark:text-yellow-100';
      case 'info':
        return 'text-blue-900 dark:text-blue-100';
    }
  };

  const getMessageColor = (type: ToastType) => {
    switch (type) {
      case 'success':
        return 'text-green-700 dark:text-green-300';
      case 'error':
        return 'text-red-700 dark:text-red-300';
      case 'warning':
        return 'text-yellow-700 dark:text-yellow-300';
      case 'info':
        return 'text-blue-700 dark:text-blue-300';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className={`relative max-w-md w-full mx-6 rounded-xl border-2 shadow-2xl overflow-hidden ${getColors(toast.type)}`}>
        <button
          onClick={() => onRemove(toast.id)}
          className="absolute top-4 right-4 p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
        >
          <XMarkIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
        </button>
        
        <div className="p-6">
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              {getIcon(toast.type)}
            </div>
            <div className="flex-1 min-w-0">
              <div className={`text-lg font-semibold ${getTitleColor(toast.type)}`}>
                {toast.title}
              </div>
              {toast.message && (
                <div className={`text-sm mt-2 ${getMessageColor(toast.type)}`}>
                  {toast.message}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface PopupContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export default function PopupContainer({ toasts, onRemove }: PopupContainerProps) {
  if (toasts.length === 0) return null;

  // Mostrar apenas o popup mais recente para não sobrepor
  const mostRecentToast = toasts[toasts.length - 1];

  return (
    <PopupItem toast={mostRecentToast} onRemove={onRemove} />
  );
}
