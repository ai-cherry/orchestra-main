import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import FileProcessingHub from '@/components/monitoring/FileProcessingHub';
import { Monitor } from 'lucide-react';

export function MonitoringPage() {
  return (
    <PageWrapper 
      title="File Processing & Monitoring" 
      description="Process files and monitor system performance in real-time"
    >
      <div className="h-[calc(100vh-12rem)]">
        <FileProcessingHub />
      </div>
    </PageWrapper>
  );
} 