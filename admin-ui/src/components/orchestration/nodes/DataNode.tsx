import React, { memo } from 'react';
import { Handle, NodeProps, Position } from '@xyflow/react';
import { Database, FileText, Cloud } from 'lucide-react';

const iconMap = {
  database: Database,
  file: FileText,
  api: Cloud,
};

export const DataNode = memo(({ data, selected }: NodeProps) => {
  const Icon = iconMap[data.dataType as keyof typeof iconMap] || Database;
  
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg border-2 transition-all ${
        selected 
          ? 'border-green-500 shadow-xl' 
          : 'border-gray-300 dark:border-gray-600'
      } min-w-[180px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-green-500 !w-3 !h-3"
      />
      
      <div className="p-3">
        <div className="flex items-center space-x-2 mb-2">
          <div className="p-1.5 rounded-lg bg-green-100 dark:bg-green-900/30">
            <Icon className="h-4 w-4 text-green-600 dark:text-green-400" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
              {data.name || 'Data Source'}
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {data.dataType || 'database'}
            </p>
          </div>
        </div>
        
        {data.size && (
          <div className="text-xs text-gray-600 dark:text-gray-300">
            Size: {data.size}
          </div>
        )}
        
        {data.format && (
          <div className="text-xs text-gray-600 dark:text-gray-300">
            Format: {data.format}
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-green-500 !w-3 !h-3"
      />
    </div>
  );
});

DataNode.displayName = 'DataNode'; 