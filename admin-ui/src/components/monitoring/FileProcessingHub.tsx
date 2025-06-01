import React from 'react';
import FileProcessor from './FileProcessor';
import StreamingLogMonitor from './StreamingLogMonitor';
import SystemMetricsVisualizer from './SystemMetricsVisualizer';

const FileProcessingHub: React.FC = () => {
  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Column */}
      <div className="space-y-6">
        <FileProcessor />
        <SystemMetricsVisualizer />
      </div>
      
      {/* Right Column */}
      <div className="h-full">
        <StreamingLogMonitor />
      </div>
    </div>
  );
};

export default FileProcessingHub; 