import React from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import AgentCanvas from './AgentCanvas';
import ExecutionMonitor from './ExecutionMonitor';

const AgentOrchestrationHub: React.FC = () => {
  return (
    <div className="h-full flex flex-col lg:flex-row gap-6">
      <div className="flex-1 min-h-[600px] lg:min-h-0">
        <ReactFlowProvider>
          <AgentCanvas />
        </ReactFlowProvider>
      </div>
      <div className="w-full lg:w-96 flex-shrink-0">
        <ExecutionMonitor />
      </div>
    </div>
  );
};

export default AgentOrchestrationHub; 