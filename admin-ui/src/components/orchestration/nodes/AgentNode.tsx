import React, { memo } from 'react';
import { Handle, NodeProps, Position } from '@xyflow/react';
import { User } from 'lucide-react';

export const AgentNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg border-2 transition-all ${
        selected 
          ? 'border-blue-500 shadow-xl' 
          : 'border-gray-300 dark:border-gray-600'
      } min-w-[200px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-blue-500 !w-3 !h-3"
      />
      
      <div className="p-4">
        <div className="flex items-center space-x-3 mb-2">
          <div className={`p-2 rounded-lg ${data.color || 'bg-blue-100 dark:bg-blue-900/30'}`}>
            <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {data.name || 'Agent'}
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {data.type || 'General'}
            </p>
          </div>
        </div>
        
        {data.description && (
          <p className="text-xs text-gray-600 dark:text-gray-300 mt-2">
            {data.description}
          </p>
        )}
        
        {data.status && (
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs text-gray-500 dark:text-gray-400">Status:</span>
            <span className={`text-xs px-2 py-1 rounded-full ${
              data.status === 'active' 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}>
              {data.status}
            </span>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-blue-500 !w-3 !h-3"
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode'; 