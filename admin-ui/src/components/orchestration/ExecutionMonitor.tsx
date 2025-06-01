import React from 'react';
import useWorkflowStore from '@/store/workflowStore';
import { CheckCircle, Circle, Clock, AlertCircle } from 'lucide-react';

const ExecutionMonitor: React.FC = () => {
  const { nodes, isExecuting, executionResults } = useWorkflowStore();

  const getStatusIcon = (nodeId: string) => {
    const result = executionResults[nodeId];
    if (!result) {
      return <Circle className="h-4 w-4 text-gray-400" />;
    }
    if (result.status === 'completed') {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    if (result.status === 'error') {
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
    return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />;
  };

  const formatTime = (timestamp: string) => {
    if (!timestamp) return '--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Execution Monitor
        </h3>
        {isExecuting && (
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-600 dark:text-gray-400">Executing</span>
          </div>
        )}
      </div>

      <div className="space-y-3">
        {nodes.map((node) => {
          const result = executionResults[node.id];
          return (
            <div
              key={node.id}
              className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <div className="mt-0.5">{getStatusIcon(node.id)}</div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {node.data.name}
                    </h4>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {node.type.replace('Node', '')}
                    </p>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {result ? formatTime(result.timestamp) : '--:--'}
                  </span>
                </div>
                {result && result.output && (
                  <p className="mt-2 text-xs text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-600/50 p-2 rounded">
                    {result.output}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {!isExecuting && Object.keys(executionResults).length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Total Nodes:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">{nodes.length}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-gray-600 dark:text-gray-400">Completed:</span>
            <span className="font-medium text-green-600 dark:text-green-400">
              {Object.values(executionResults).filter(r => r.status === 'completed').length}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionMonitor; 