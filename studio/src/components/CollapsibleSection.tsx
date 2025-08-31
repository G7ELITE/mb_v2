import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

export default function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = true, 
  description,
  icon: Icon 
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="card">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-0 bg-transparent border-none text-left focus:outline-none"
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />}
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {title}
            </h2>
            {description && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                {description}
              </p>
            )}
          </div>
        </div>
        
        <div className="ml-4">
          {isExpanded ? (
            <ChevronDownIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
          ) : (
            <ChevronRightIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
          )}
        </div>
      </button>
      
      {isExpanded && (
        <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
          {children}
        </div>
      )}
    </div>
  );
}
