import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface ActionButton {
  label: string;
  onClick: () => void;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: 'primary' | 'secondary' | 'danger';
}

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  actions?: ActionButton[];
  previewContent?: React.ReactNode;
}

export default function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = true, 
  description,
  icon: Icon,
  actions = [],
  previewContent
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const getActionButtonClass = (variant: ActionButton['variant'] = 'secondary') => {
    const baseClass = "inline-flex items-center px-3 py-1.5 text-sm font-medium rounded-md border focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors";
    
    switch (variant) {
      case 'primary':
        return `${baseClass} text-white bg-blue-600 border-blue-600 hover:bg-blue-700 focus:ring-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600`;
      case 'danger':
        return `${baseClass} text-red-700 bg-red-50 border-red-200 hover:bg-red-100 focus:ring-red-500 dark:text-red-300 dark:bg-red-900/20 dark:border-red-800 dark:hover:bg-red-900/30`;
      default:
        return `${baseClass} text-gray-700 bg-white border-gray-300 hover:bg-gray-50 focus:ring-blue-500 dark:text-gray-300 dark:bg-gray-700 dark:border-gray-600 dark:hover:bg-gray-600`;
    }
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex-1 flex items-center gap-3 p-0 bg-transparent border-none text-left focus:outline-none mr-4"
        >
          {Icon && <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />}
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
              {title}
            </h2>
            {description && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
                {description}
              </p>
            )}
          </div>
          <div className="ml-4 flex-shrink-0">
            {isExpanded ? (
              <ChevronDownIcon className="h-5 w-5 text-gray-400 dark:text-gray-500 transition-transform duration-200" />
            ) : (
              <ChevronRightIcon className="h-5 w-5 text-gray-400 dark:text-gray-500 transition-transform duration-200" />
            )}
          </div>
        </button>
        
        {actions.length > 0 && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {actions.map((action, index) => (
              <button
                key={index}
                onClick={(e) => {
                  e.stopPropagation();
                  action.onClick();
                }}
                className={getActionButtonClass(action.variant)}
              >
                {action.icon && <action.icon className="h-4 w-4 mr-1" />}
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
      
      {!isExpanded && previewContent && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {previewContent}
          </div>
        </div>
      )}
      
      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
        isExpanded ? 'max-h-screen opacity-100 mt-6' : 'max-h-0 opacity-0'
      }`}>
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          {children}
        </div>
      </div>
    </div>
  );
}
