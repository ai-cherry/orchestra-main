import React, { useState, useEffect } from 'react';
import { usePersona } from '../../contexts/PersonaContext';
// @ts-ignore - JS module without types
import apiClient from '../../services/api-client';

interface Workflow {
  id: string;
  name: string;
  icon: string;
  description: string;
  steps: string[];
  status: string;
  personaType: string;
}

interface MCPServer {
  name: string;
  icon: string;
  description: string;
  tools: string[];
  status: string;
}

interface Agent {
  id: number;
  name: string;
  type: string;
  status: string;
}

interface ExecutionResult {
  status: 'running' | 'success' | 'error';
  message: string;
  data?: any;
}

const BusinessToolsPage = () => {
  const { currentPersona } = usePersona();
  const theme = currentPersona.theme;
  
  const [activeTab, setActiveTab] = useState('workflows');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [mcpServers, setMcpServers] = useState<MCPServer[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);

  // Available MCP servers based on your codebase
  const availableMCPServers = [
    { 
      name: 'conductor', 
      icon: '🎭', 
      description: 'Orchestrate complex workflows and agent coordination',
      tools: ['list_agents', 'run_workflow', 'get_status'],
      status: 'active'
    },
    { 
      name: 'memory', 
      icon: '🧠', 
      description: 'Store and retrieve contextual memories',
      tools: ['store_memory', 'query_memory', 'get_agent_memories'],
      status: 'active'
    },
    { 
      name: 'web_scraping', 
      icon: '🌐', 
      description: 'Extract data from websites and analyze content',
      tools: ['web_search', 'scrape_website', 'analyze_content'],
      status: 'active'
    },
    { 
      name: 'infrastructure', 
      icon: '🏗️', 
      description: 'Manage Lambda Labs infrastructure and deployments',
      tools: ['get_instances', 'deploy_infrastructure', 'get_status'],
      status: 'active'
    },
    { 
      name: 'weaviate', 
      icon: '🔍', 
      description: 'Vector search and semantic data operations',
      tools: ['vector_search', 'hybrid_search', 'get_schema'],
      status: 'active'
    }
  ];

  // Workflow templates
  const workflowTemplates = [
    {
      id: 'data-pipeline',
      name: 'Data Processing Pipeline',
      icon: '📊',
      description: 'ETL workflow for processing business data',
      steps: ['Extract', 'Transform', 'Load', 'Validate'],
      status: 'ready',
      personaType: 'sophia'
    },
    {
      id: 'agent-swarm',
      name: 'Agent Swarm Execution',
      icon: '🤖',
      description: 'Coordinate multiple agents for complex tasks',
      steps: ['Initialize', 'Distribute', 'Execute', 'Aggregate'],
      status: 'ready',
      personaType: 'all'
    },
    {
      id: 'memory-sync',
      name: 'Memory Synchronization',
      icon: '🔄',
      description: 'Sync memories across vector stores',
      steps: ['Collect', 'Embed', 'Store', 'Index'],
      status: 'ready',
      personaType: 'all'
    },
    {
      id: 'health-analysis',
      name: 'Health Data Analysis',
      icon: '🏥',
      description: 'Analyze clinical trial and health data',
      steps: ['Import', 'Validate', 'Analyze', 'Report'],
      status: 'ready',
      personaType: 'karen'
    },
    {
      id: 'lifestyle-optimization',
      name: 'Lifestyle Optimization',
      icon: '✨',
      description: 'Optimize daily routines and wellness',
      steps: ['Assess', 'Plan', 'Execute', 'Track'],
      status: 'ready',
      personaType: 'cherry'
    }
  ];

  useEffect(() => {
    loadBusinessTools();
  }, [currentPersona]);

  const loadBusinessTools = async () => {
    try {
      setLoading(true);
      
      // Filter workflows for current persona
      const filteredWorkflows = workflowTemplates.filter(
        w => w.personaType === 'all' || w.personaType === currentPersona.name.toLowerCase()
      );
      setWorkflows(filteredWorkflows);
      
      // Set MCP servers
      setMcpServers(availableMCPServers);
      
      // Mock agents data - in production, this would come from API
      setAgents([
        { id: 1, name: 'Data Processor', type: 'processor', status: 'active' },
        { id: 2, name: 'Memory Manager', type: 'memory', status: 'active' },
        { id: 3, name: 'Task Coordinator', type: 'coordinator', status: 'idle' }
      ]);
      
    } catch (error) {
      console.error('Failed to load business tools:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeMCPTool = async (server: MCPServer, tool: string) => {
    try {
      setExecutionResult({ status: 'running', message: `Executing ${tool} on ${server.name}...` });
      
      // Simulate API call - in production, use actual apiClient
      setTimeout(() => {
        setExecutionResult({
          status: 'success',
          message: `Successfully executed ${tool}`,
          data: {
            server: server.name,
            tool: tool,
            timestamp: new Date().toISOString(),
            result: 'Operation completed successfully'
          }
        });
      }, 2000);
      
    } catch (error) {
      setExecutionResult({
        status: 'error',
        message: `Failed to execute ${tool}: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const executeWorkflow = async (workflow: Workflow) => {
    try {
      setExecutionResult({ status: 'running', message: `Starting ${workflow.name}...` });
      
      // Simulate workflow execution
      setTimeout(() => {
        setExecutionResult({
          status: 'success',
          message: `Workflow ${workflow.name} completed`,
          data: {
            workflow: workflow.id,
            steps: workflow.steps,
            duration: '2.5s',
            timestamp: new Date().toISOString()
          }
        });
      }, 2500);
      
    } catch (error) {
      setExecutionResult({
        status: 'error',
        message: `Workflow failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    }
  };

  const renderWorkflowsTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workflows.map((workflow) => (
          <div
            key={workflow.id}
            className="bg-black/20 border rounded-xl p-6 hover:bg-black/30 transition-all cursor-pointer"
            style={{ borderColor: theme.border }}
            onClick={() => executeWorkflow(workflow)}
          >
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{workflow.icon}</span>
              <div>
                <h3 className="font-semibold text-white">{workflow.name}</h3>
                <p className="text-sm text-gray-400">{workflow.description}</p>
              </div>
            </div>
            
            <div className="space-y-2 mb-4">
              {workflow.steps.map((step: string, idx: number) => (
                <div key={idx} className="flex items-center gap-2">
                  <div 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: theme.primary }}
                  />
                  <span className="text-sm text-gray-300">{step}</span>
                </div>
              ))}
            </div>
            
            <div className="flex items-center justify-between">
              <span className={`text-xs px-2 py-1 rounded ${
                workflow.status === 'ready' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {workflow.status}
              </span>
              <button 
                className="text-sm px-3 py-1 rounded hover:opacity-80 transition-opacity"
                style={{ backgroundColor: theme.primary, color: '#000' }}
              >
                Execute
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMCPServersTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {mcpServers.map((server) => (
          <div
            key={server.name}
            className="bg-black/20 border rounded-xl p-6"
            style={{ borderColor: theme.border }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{server.icon}</span>
                <div>
                  <h3 className="font-semibold text-white capitalize">{server.name}</h3>
                  <p className="text-sm text-gray-400">{server.description}</p>
                </div>
              </div>
              <span className={`w-3 h-3 rounded-full ${
                server.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
              }`} />
            </div>
            
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-300">Available Tools:</h4>
              {server.tools.map((tool: string, idx: number) => (
                <button
                  key={idx}
                  onClick={() => executeMCPTool(server, tool)}
                  className="w-full text-left p-3 bg-black/30 rounded-lg hover:bg-black/50 transition-all flex items-center justify-between group"
                >
                  <span className="text-sm text-gray-300">{tool}</span>
                  <span className="text-xs opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: theme.primary }}>
                    Execute →
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderAgentsTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div
            key={agent.id}
            className="bg-black/20 border rounded-xl p-6"
            style={{ borderColor: theme.border }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white">{agent.name}</h3>
              <span className={`text-xs px-2 py-1 rounded ${
                agent.status === 'active' 
                  ? 'bg-green-500/20 text-green-400' 
                  : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {agent.status}
              </span>
            </div>
            <p className="text-sm text-gray-400 mb-4">Type: {agent.type}</p>
            <button 
              className="w-full text-sm px-3 py-2 rounded hover:opacity-80 transition-opacity"
              style={{ backgroundColor: theme.primary + '20', color: theme.primary }}
            >
              Configure
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading business tools...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>
        Business Tools
      </h1>
      <p style={{ fontSize: '1rem', color: '#888', marginBottom: '2rem' }}>
        Orchestrate workflows, manage MCP servers, and coordinate agents for{' '}
        <span style={{ color: theme.primary, fontWeight: 500 }}>{currentPersona.name}</span>
      </p>

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b" style={{ borderColor: theme.border }}>
        {['workflows', 'mcp-servers', 'agents'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium transition-all ${
              activeTab === tab 
                ? 'border-b-2 text-white' 
                : 'text-gray-400 hover:text-gray-200'
            }`}
            style={{ 
              borderColor: activeTab === tab ? theme.primary : 'transparent' 
            }}
          >
            {tab.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[60vh]">
        {activeTab === 'workflows' && renderWorkflowsTab()}
        {activeTab === 'mcp-servers' && renderMCPServersTab()}
        {activeTab === 'agents' && renderAgentsTab()}
      </div>

      {/* Execution Result */}
      {executionResult && (
        <div className={`fixed bottom-4 right-4 p-4 rounded-lg shadow-lg max-w-md ${
          executionResult.status === 'success' ? 'bg-green-500/20 border border-green-500/50' :
          executionResult.status === 'error' ? 'bg-red-500/20 border border-red-500/50' :
          'bg-blue-500/20 border border-blue-500/50'
        }`}>
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-white mb-1">{executionResult.message}</h4>
              {executionResult.data && (
                <pre className="text-xs text-gray-300 mt-2">
                  {JSON.stringify(executionResult.data, null, 2)}
                </pre>
              )}
            </div>
            <button
              onClick={() => setExecutionResult(null)}
              className="ml-4 text-gray-400 hover:text-white"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default BusinessToolsPage;