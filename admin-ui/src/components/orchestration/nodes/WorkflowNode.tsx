import React, { memo } from 'react';
import { Handle, NodeProps, Position } from '@xyflow/react';
import { GitBranch } from 'lucide-react';

export const WorkflowNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div 
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg border-2 transition-all ${
        selected 
          ? 'border-purple-500 shadow-xl' 
          : 'border-gray-300 dark:border-gray-600'
      } min-w-[200px]`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-purple-500 !w-3 !h-3"
      />
      
      <div className="p-4">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <GitBranch className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {data.name || 'Workflow'}
            </h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {data.steps || 0} steps
            </p>
          </div>
        </div>
        
        {data.trigger && (
          <div className="mt-2 text-xs">
            <span className="text-gray-500 dark:text-gray-400">Trigger: </span>
            <span className="text-gray-700 dark:text-gray-300">{data.trigger}</span>
          </div>
        )}
        
        {data.lastRun && (
          <div className="mt-1 text-xs">
            <span className="text-gray-500 dark:text-gray-400">Last run: </span>
            <span className="text-gray-700 dark:text-gray-300">{data.lastRun}</span>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-purple-500 !w-3 !h-3"
      />
    </div>
  );
});

WorkflowNode.displayName = 'WorkflowNode'; 