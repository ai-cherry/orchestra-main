import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Agent {
  id: string;
  name: string;
  type: 'cherry' | 'sophia' | 'karen' | 'utility' | 'custom';
  icon: string;
  status: 'active' | 'idle' | 'offline' | 'error';
  tasks: number;
  uptime: string;
  lastActivity: string;
  performance: {
    responseTime: number;
    successRate: number;
    errorsToday: number;
  };
  configuration: {
    model: string;
    temperature: number;
    tools: string[];
    persona?: string;
    rules?: string;
  };
}

export interface AgentTeam {
  id: string;
  name: string;
  description: string;
  agents: string[]; // Agent IDs
  objectives: string;
  status: 'active' | 'paused' | 'completed';
  createdAt: string;
  lastActivity: string;
}

interface AgentState {
  agents: Agent[];
  teams: AgentTeam[];
  metrics: {
    totalAgents: number;
    activeAgents: number;
    tasksCompleted: number;
    averageResponseTime: number;
  };
  isLoading: boolean;
  error: string | null;
}

const initialState: AgentState = {
  agents: [
    {
      id: 'cherry-001',
      name: 'Cherry Creative',
      type: 'cherry',
      icon: '🍒',
      status: 'active',
      tasks: 47,
      uptime: '2h 34m',
      lastActivity: '2 minutes ago',
      performance: {
        responseTime: 234,
        successRate: 98.5,
        errorsToday: 1
      },
      configuration: {
        model: 'Claude-3.5-Sonnet',
        temperature: 0.9,
        tools: ['image_generation', 'web_search', 'file_analysis'],
        persona: 'cherry',
        rules: 'Be creative, playful, and helpful'
      }
    },
    {
      id: 'sophia-001',
      name: 'Sophia Business',
      type: 'sophia',
      icon: '💼',
      status: 'active',
      tasks: 82,
      uptime: '4h 12m',
      lastActivity: '5 minutes ago',
      performance: {
        responseTime: 156,
        successRate: 99.2,
        errorsToday: 0
      },
      configuration: {
        model: 'GPT-4',
        temperature: 0.3,
        tools: ['salesforce', 'hubspot', 'analytics', 'reporting'],
        persona: 'sophia',
        rules: 'Focus on business efficiency and ROI'
      }
    },
    {
      id: 'karen-001',
      name: 'Karen Healthcare',
      type: 'karen',
      icon: '🏥',
      status: 'idle',
      tasks: 13,
      uptime: '1h 45m',
      lastActivity: '15 minutes ago',
      performance: {
        responseTime: 298,
        successRate: 97.8,
        errorsToday: 0
      },
      configuration: {
        model: 'Claude-3.5-Sonnet',
        temperature: 0.1,
        tools: ['clinical_data', 'hipaa_compliance', 'patient_recruitment'],
        persona: 'karen',
        rules: 'Ensure HIPAA compliance and medical accuracy'
      }
    },
    {
      id: 'utility-001',
      name: 'File Processor',
      type: 'utility',
      icon: '📁',
      status: 'active',
      tasks: 156,
      uptime: '6h 22m',
      lastActivity: '1 minute ago',
      performance: {
        responseTime: 89,
        successRate: 99.8,
        errorsToday: 0
      },
      configuration: {
        model: 'Local-Model',
        temperature: 0.0,
        tools: ['file_parsing', 'document_analysis', 'data_extraction'],
        rules: 'Process files efficiently and accurately'
      }
    },
    {
      id: 'custom-001',
      name: 'Research Assistant',
      type: 'custom',
      icon: '🔍',
      status: 'offline',
      tasks: 0,
      uptime: '0m',
      lastActivity: 'Never',
      performance: {
        responseTime: 0,
        successRate: 0,
        errorsToday: 0
      },
      configuration: {
        model: 'GPT-4',
        temperature: 0.4,
        tools: ['web_search', 'academic_search', 'citation_formatting'],
        rules: 'Provide thorough research with proper citations'
      }
    },
    {
      id: 'utility-002',
      name: 'Data Analyzer',
      type: 'utility',
      icon: '📊',
      status: 'idle',
      tasks: 34,
      uptime: '3h 8m',
      lastActivity: '8 minutes ago',
      performance: {
        responseTime: 145,
        successRate: 98.9,
        errorsToday: 1
      },
      configuration: {
        model: 'Local-Model',
        temperature: 0.2,
        tools: ['data_analysis', 'visualization', 'statistical_modeling'],
        rules: 'Provide accurate data insights and visualizations'
      }
    }
  ],
  teams: [],
  metrics: {
    totalAgents: 6,
    activeAgents: 3,
    tasksCompleted: 332,
    averageResponseTime: 185
  },
  isLoading: false,
  error: null
};

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    updateAgentStatus: (state, action: PayloadAction<{ agentId: string; status: Agent['status'] }>) => {
      const agent = state.agents.find(a => a.id === action.payload.agentId);
      if (agent) {
        agent.status = action.payload.status;
        agent.lastActivity = new Date().toISOString();
      }
      
      // Update metrics
      state.metrics.activeAgents = state.agents.filter(a => a.status === 'active').length;
    },
    
    updateAgentPerformance: (state, action: PayloadAction<{ agentId: string; performance: Partial<Agent['performance']> }>) => {
      const agent = state.agents.find(a => a.id === action.payload.agentId);
      if (agent) {
        agent.performance = { ...agent.performance, ...action.payload.performance };
      }
      
      // Update average response time
      const totalResponseTime = state.agents.reduce((sum, a) => sum + a.performance.responseTime, 0);
      state.metrics.averageResponseTime = Math.round(totalResponseTime / state.agents.length);
    },
    
    incrementAgentTasks: (state, action: PayloadAction<string>) => {
      const agent = state.agents.find(a => a.id === action.payload);
      if (agent) {
        agent.tasks += 1;
        agent.lastActivity = new Date().toISOString();
      }
      
      state.metrics.tasksCompleted += 1;
    },
    
    updateAgentConfiguration: (state, action: PayloadAction<{ agentId: string; configuration: Partial<Agent['configuration']> }>) => {
      const agent = state.agents.find(a => a.id === action.payload.agentId);
      if (agent) {
        agent.configuration = { ...agent.configuration, ...action.payload.configuration };
      }
    },
    
    addAgent: (state, action: PayloadAction<Omit<Agent, 'id' | 'lastActivity'>>) => {
      const newAgent: Agent = {
        ...action.payload,
        id: `${action.payload.type}-${Date.now()}`,
        lastActivity: new Date().toISOString()
      };
      
      state.agents.push(newAgent);
      state.metrics.totalAgents += 1;
      
      if (newAgent.status === 'active') {
        state.metrics.activeAgents += 1;
      }
    },
    
    removeAgent: (state, action: PayloadAction<string>) => {
      const agentIndex = state.agents.findIndex(a => a.id === action.payload);
      if (agentIndex !== -1) {
        const agent = state.agents[agentIndex];
        state.agents.splice(agentIndex, 1);
        state.metrics.totalAgents -= 1;
        
        if (agent.status === 'active') {
          state.metrics.activeAgents -= 1;
        }
      }
    },
    
    createTeam: (state, action: PayloadAction<Omit<AgentTeam, 'id' | 'createdAt' | 'lastActivity'>>) => {
      const newTeam: AgentTeam = {
        ...action.payload,
        id: `team-${Date.now()}`,
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString()
      };
      
      state.teams.push(newTeam);
    },
    
    updateTeam: (state, action: PayloadAction<{ teamId: string; updates: Partial<AgentTeam> }>) => {
      const team = state.teams.find(t => t.id === action.payload.teamId);
      if (team) {
        Object.assign(team, action.payload.updates);
        team.lastActivity = new Date().toISOString();
      }
    },
    
    deleteTeam: (state, action: PayloadAction<string>) => {
      state.teams = state.teams.filter(t => t.id !== action.payload);
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    resetMetrics: (state) => {
      state.metrics = {
        totalAgents: state.agents.length,
        activeAgents: state.agents.filter(a => a.status === 'active').length,
        tasksCompleted: 0,
        averageResponseTime: 0
      };
      
      // Reset agent task counts
      state.agents.forEach(agent => {
        agent.tasks = 0;
        agent.performance.errorsToday = 0;
      });
    }
  }
});

export const {
  updateAgentStatus,
  updateAgentPerformance,
  incrementAgentTasks,
  updateAgentConfiguration,
  addAgent,
  removeAgent,
  createTeam,
  updateTeam,
  deleteTeam,
  setLoading,
  setError,
  resetMetrics
} = agentSlice.actions;

export default agentSlice.reducer; 