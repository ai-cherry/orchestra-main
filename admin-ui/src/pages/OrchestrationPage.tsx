import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import AgentOrchestrationHub from '@/components/orchestration/AgentOrchestrationHub';
import { GitBranch } from 'lucide-react';

export function OrchestrationPage() {
  return (
    <PageWrapper 
      title="Agent Orchestration Hub" 
      description="Design and execute complex agent workflows with visual node-based editor"
    >
      <div className="h-[calc(100vh-12rem)]">
        <AgentOrchestrationHub />
      </div>
    </PageWrapper>
  );
} 