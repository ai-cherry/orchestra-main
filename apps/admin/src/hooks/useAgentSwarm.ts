import { useState, useCallback, useRef, useEffect } from 'react'
import { usePersona } from '@/contexts/PersonaContext'

export type AgentRole = 
  // Cherry's Life Companion Agents
  | 'travel_planner' | 'relationship_coach' | 'creative_collaborator' 
  | 'wellness_tracker' | 'life_optimizer' | 'finance_researcher'
  | 'ranch_manager' | 'security_coordinator' | 'web_scraper_finance'
  | 'web_scraper_ranch' | 'ranch_landscaper' | 'ranch_security'
  // Sophia's Business Intelligence Agents  
  | 'market_analyst' | 'client_relationship_manager' | 'revenue_optimizer'
  | 'compliance_monitor' | 'strategic_advisor' | 'gong_expert'
  | 'hubspot_expert' | 'slack_expert' | 'salesforce_expert'
  | 'sql_expert' | 'looker_expert' | 'apollo_expert' | 'linkedin_expert'
  | 'netsuite_expert' | 'github_expert' | 'linear_expert' | 'asana_expert'
  | 'sharepoint_expert' | 'lattice_expert' | 'web_scraper_business'
  | 'ai_sales_coach' | 'ai_client_health_expert' | 'data_integration_specialist'
  // Karen's Healthcare Agents
  | 'clinical_researcher' | 'patient_advocate' | 'regulatory_specialist'
  | 'pharmaceutical_intelligence' | 'wellness_coordinator' | 'web_scraper_clinical'
  | 'cro_specialist' | 'paragon_crm_coordinator'
  // System Agents
  | 'supervisor' | 'coordinator' | 'quality_assurance' | 'ai_operator'

export type AgentStatus = 'spawning' | 'active' | 'idle' | 'coordinating' | 'error' | 'terminated'

export type TaskPriority = 'critical' | 'high' | 'medium' | 'low' | 'background'

export interface AgentCapability {
  name: string
  description: string
  complexity: number
  estimatedTime: number
  costFactor: number
}

export interface AgentConfig {
  role: AgentRole
  name: string
  description: string
  persona: 'cherry' | 'sophia' | 'karen' | 'master'
  capabilities: AgentCapability[]
  specializations: string[]
  basePerformance: number
  resourceUsage: number
  icon: string
  category: 'orchestrator' | 'specialist' | 'expert' | 'supervisor'
}

export interface AgentInstance {
  id: string
  config: AgentConfig
  status: AgentStatus
  spawnedAt: Date
  lastActivity: Date
  performance: {
    tasksCompleted: number
    successRate: number
    averageResponseTime: number
    learningProgress: number
    resourceEfficiency: number
  }
  currentTask?: {
    id: string
    description: string
    priority: TaskPriority
    startTime: Date
    progress: number
  }
  connections: string[] // Other agent IDs it's coordinating with
  metrics: {
    uptime: number
    totalOperations: number
    errorCount: number
    learningRate: number
  }
}

const agentConfigs: AgentConfig[] = [
  // Cherry's Life Companion Agents
  {
    role: 'travel_planner',
    name: 'Travel Planner AI',
    description: 'Specialized in travel planning, optimization, and booking coordination',
    persona: 'cherry',
    capabilities: [
      { name: 'Destination Research', description: 'Research and recommend destinations', complexity: 3, estimatedTime: 5000, costFactor: 0.8 },
      { name: 'Itinerary Optimization', description: 'Optimize travel schedules and routes', complexity: 4, estimatedTime: 3000, costFactor: 1.0 },
      { name: 'Booking Coordination', description: 'Coordinate bookings across platforms', complexity: 2, estimatedTime: 2000, costFactor: 0.5 }
    ],
    specializations: ['International Travel', 'Adventure Tourism', 'Luxury Planning'],
    basePerformance: 0.92,
    resourceUsage: 0.3,
    icon: '✈️',
    category: 'specialist'
  },
  {
    role: 'finance_researcher',
    name: 'Finance Research AI',
    description: 'Swing trading analysis and investment research specialist',
    persona: 'cherry',
    capabilities: [
      { name: 'Market Analysis', description: 'Real-time market trend analysis', complexity: 5, estimatedTime: 8000, costFactor: 1.5 },
      { name: 'Swing Trade Signals', description: 'Generate swing trading recommendations', complexity: 4, estimatedTime: 6000, costFactor: 1.2 },
      { name: 'Risk Assessment', description: 'Portfolio risk analysis', complexity: 4, estimatedTime: 4000, costFactor: 1.0 }
    ],
    specializations: ['Technical Analysis', 'Options Trading', 'Portfolio Management'],
    basePerformance: 0.89,
    resourceUsage: 0.7,
    icon: '📈',
    category: 'expert'
  },
  {
    role: 'ranch_manager',
    name: 'Ranch Management AI',
    description: 'Comprehensive ranch and property management coordinator',
    persona: 'cherry',
    capabilities: [
      { name: 'Landscape Planning', description: 'Design and plan landscape improvements', complexity: 3, estimatedTime: 7000, costFactor: 0.9 },
      { name: 'Security Management', description: 'Monitor and coordinate security systems', complexity: 2, estimatedTime: 1000, costFactor: 0.4 },
      { name: 'Expense Tracking', description: 'Track and categorize ranch expenses', complexity: 2, estimatedTime: 2000, costFactor: 0.3 }
    ],
    specializations: ['Property Management', 'Animal Care', 'Infrastructure Planning'],
    basePerformance: 0.94,
    resourceUsage: 0.4,
    icon: '🏡',
    category: 'specialist'
  },
  {
    role: 'web_scraper_finance',
    name: 'Finance Web Scraper AI',
    description: 'Specialized web scraper for financial markets and investment data',
    persona: 'cherry',
    capabilities: [
      { name: 'Market Data Scraping', description: 'Extract real-time market data from financial sites', complexity: 4, estimatedTime: 5000, costFactor: 1.2 },
      { name: 'News Analysis', description: 'Scrape and analyze financial news sources', complexity: 3, estimatedTime: 4000, costFactor: 0.8 },
      { name: 'Swing Trade Research', description: 'Research swing trading opportunities', complexity: 4, estimatedTime: 6000, costFactor: 1.0 }
    ],
    specializations: ['Financial Markets', 'Investment Research', 'Trading Signals'],
    basePerformance: 0.88,
    resourceUsage: 0.6,
    icon: '📈',
    category: 'specialist'
  },
  {
    role: 'web_scraper_ranch',
    name: 'Ranch Web Scraper AI',
    description: 'Web scraper for ranch management, landscaping, and property care',
    persona: 'cherry',
    capabilities: [
      { name: 'Landscaping Research', description: 'Find landscaping ideas and suppliers', complexity: 3, estimatedTime: 4000, costFactor: 0.7 },
      { name: 'Property Management', description: 'Research property management best practices', complexity: 3, estimatedTime: 3500, costFactor: 0.6 },
      { name: 'Equipment Research', description: 'Find ranch equipment and reviews', complexity: 2, estimatedTime: 3000, costFactor: 0.5 }
    ],
    specializations: ['Landscaping', 'Property Care', 'Equipment Research'],
    basePerformance: 0.92,
    resourceUsage: 0.4,
    icon: '🌱',
    category: 'specialist'
  },
  // Sophia's Business Intelligence Agents
  {
    role: 'market_analyst',
    name: 'Market Analyst AI',
    description: 'Advanced market analysis and business intelligence specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Market Trend Analysis', description: 'Analyze market trends and patterns', complexity: 5, estimatedTime: 8000, costFactor: 1.2 },
      { name: 'Competitive Analysis', description: 'Analyze competitive landscape', complexity: 4, estimatedTime: 6000, costFactor: 1.0 },
      { name: 'Revenue Forecasting', description: 'Predict revenue based on market conditions', complexity: 5, estimatedTime: 10000, costFactor: 1.5 }
    ],
    specializations: ['Real Estate Markets', 'Fintech Analysis', 'Competitive Intelligence'],
    basePerformance: 0.88,
    resourceUsage: 0.8,
    icon: '📊',
    category: 'expert'
  },
  {
    role: 'gong_expert',
    name: 'Gong.io Expert AI',
    description: 'Conversation analytics and sales intelligence specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Call Analysis', description: 'Analyze sales calls and conversations', complexity: 4, estimatedTime: 5000, costFactor: 1.1 },
      { name: 'Sales Insights', description: 'Generate actionable sales insights', complexity: 3, estimatedTime: 3000, costFactor: 0.8 },
      { name: 'Performance Coaching', description: 'Provide sales performance coaching', complexity: 4, estimatedTime: 4000, costFactor: 1.0 }
    ],
    specializations: ['Conversation Analytics', 'Sales Coaching', 'Pipeline Health'],
    basePerformance: 0.91,
    resourceUsage: 0.6,
    icon: '🎙️',
    category: 'expert'
  },
  {
    role: 'hubspot_expert',
    name: 'HubSpot Expert AI',
    description: 'Marketing automation and CRM optimization specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Pipeline Management', description: 'Optimize sales pipeline workflows', complexity: 3, estimatedTime: 4000, costFactor: 0.7 },
      { name: 'Lead Scoring', description: 'Advanced lead scoring and qualification', complexity: 4, estimatedTime: 3000, costFactor: 0.9 },
      { name: 'Campaign Optimization', description: 'Optimize marketing campaigns', complexity: 4, estimatedTime: 6000, costFactor: 1.2 }
    ],
    specializations: ['Marketing Automation', 'Lead Generation', 'Customer Journey'],
    basePerformance: 0.93,
    resourceUsage: 0.5,
    icon: '🎯',
    category: 'expert'
  },
  {
    role: 'apollo_expert',
    name: 'Apollo.io Expert AI',
    description: 'Sales prospecting and lead generation specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Lead Prospecting', description: 'Find and qualify prospects using Apollo', complexity: 3, estimatedTime: 3500, costFactor: 0.8 },
      { name: 'Email Sequencing', description: 'Create and optimize email sequences', complexity: 3, estimatedTime: 4000, costFactor: 0.7 },
      { name: 'Data Enrichment', description: 'Enrich contact and company data', complexity: 2, estimatedTime: 2000, costFactor: 0.5 }
    ],
    specializations: ['Prospecting', 'Email Marketing', 'Data Enrichment'],
    basePerformance: 0.90,
    resourceUsage: 0.4,
    icon: '🚀',
    category: 'expert'
  },
  {
    role: 'linkedin_expert',
    name: 'LinkedIn Expert AI',
    description: 'Professional networking and sales intelligence specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Network Analysis', description: 'Analyze professional networks and connections', complexity: 4, estimatedTime: 5000, costFactor: 1.0 },
      { name: 'Content Strategy', description: 'Develop LinkedIn content strategies', complexity: 3, estimatedTime: 4500, costFactor: 0.8 },
      { name: 'Lead Intelligence', description: 'Gather intelligence on prospects', complexity: 4, estimatedTime: 4000, costFactor: 0.9 }
    ],
    specializations: ['Professional Networks', 'Social Selling', 'Content Marketing'],
    basePerformance: 0.89,
    resourceUsage: 0.5,
    icon: '💼',
    category: 'expert'
  },
  {
    role: 'netsuite_expert',
    name: 'NetSuite Expert AI',
    description: 'ERP and financial management specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Financial Reporting', description: 'Generate and analyze financial reports', complexity: 4, estimatedTime: 6000, costFactor: 1.1 },
      { name: 'Process Automation', description: 'Automate business processes in NetSuite', complexity: 5, estimatedTime: 8000, costFactor: 1.3 },
      { name: 'Data Integration', description: 'Integrate NetSuite with other systems', complexity: 5, estimatedTime: 7000, costFactor: 1.2 }
    ],
    specializations: ['ERP Systems', 'Financial Management', 'Business Automation'],
    basePerformance: 0.92,
    resourceUsage: 0.7,
    icon: '📊',
    category: 'expert'
  },
  {
    role: 'github_expert',
    name: 'GitHub Expert AI',
    description: 'Development workflow and project management specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Repository Management', description: 'Manage GitHub repositories and workflows', complexity: 3, estimatedTime: 3000, costFactor: 0.6 },
      { name: 'Code Review', description: 'Automated code review and quality analysis', complexity: 4, estimatedTime: 5000, costFactor: 1.0 },
      { name: 'Project Tracking', description: 'Track development projects and milestones', complexity: 3, estimatedTime: 3500, costFactor: 0.7 }
    ],
    specializations: ['Development Workflow', 'Code Quality', 'Project Management'],
    basePerformance: 0.95,
    resourceUsage: 0.5,
    icon: '🔧',
    category: 'expert'
  },
  {
    role: 'linear_expert',
    name: 'Linear Expert AI',
    description: 'Issue tracking and product management specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Issue Management', description: 'Track and prioritize development issues', complexity: 3, estimatedTime: 3000, costFactor: 0.6 },
      { name: 'Sprint Planning', description: 'Plan and optimize development sprints', complexity: 4, estimatedTime: 4000, costFactor: 0.8 },
      { name: 'Product Roadmap', description: 'Develop and maintain product roadmaps', complexity: 4, estimatedTime: 5000, costFactor: 0.9 }
    ],
    specializations: ['Issue Tracking', 'Sprint Planning', 'Product Management'],
    basePerformance: 0.93,
    resourceUsage: 0.4,
    icon: '📋',
    category: 'expert'
  },
  {
    role: 'asana_expert',
    name: 'Asana Expert AI',
    description: 'Project and task management specialist',
    persona: 'sophia',
    capabilities: [
      { name: 'Project Planning', description: 'Create and manage project plans', complexity: 3, estimatedTime: 3500, costFactor: 0.7 },
      { name: 'Team Coordination', description: 'Coordinate team tasks and deadlines', complexity: 3, estimatedTime: 3000, costFactor: 0.6 },
      { name: 'Workflow Optimization', description: 'Optimize team workflows and processes', complexity: 4, estimatedTime: 4500, costFactor: 0.8 }
    ],
    specializations: ['Project Management', 'Team Coordination', 'Workflow Design'],
    basePerformance: 0.91,
    resourceUsage: 0.4,
    icon: '📅',
    category: 'expert'
  },
  {
    role: 'ai_sales_coach',
    name: 'AI Sales Coach',
    description: 'Provides coaching and insights for sales team performance',
    persona: 'sophia',
    capabilities: [
      { name: 'Performance Analysis', description: 'Analyze sales rep performance metrics', complexity: 4, estimatedTime: 4000, costFactor: 1.0 },
      { name: 'Coaching Recommendations', description: 'Provide personalized coaching insights', complexity: 5, estimatedTime: 5000, costFactor: 1.2 },
      { name: 'Communication Analysis', description: 'Analyze communication patterns and effectiveness', complexity: 4, estimatedTime: 4500, costFactor: 1.1 }
    ],
    specializations: ['Sales Coaching', 'Performance Analytics', 'Communication Skills'],
    basePerformance: 0.94,
    resourceUsage: 0.6,
    icon: '🎓',
    category: 'supervisor'
  },
  {
    role: 'ai_client_health_expert',
    name: 'AI Client Health Expert',
    description: 'Monitors and analyzes overall client relationship health',
    persona: 'sophia',
    capabilities: [
      { name: 'Client Health Scoring', description: 'Calculate comprehensive client health scores', complexity: 5, estimatedTime: 6000, costFactor: 1.3 },
      { name: 'Risk Assessment', description: 'Identify client retention risks', complexity: 4, estimatedTime: 4500, costFactor: 1.0 },
      { name: 'Relationship Analysis', description: 'Analyze client relationship dynamics', complexity: 4, estimatedTime: 5000, costFactor: 1.1 }
    ],
    specializations: ['Client Relations', 'Risk Assessment', 'Health Monitoring'],
    basePerformance: 0.96,
    resourceUsage: 0.7,
    icon: '❤️',
    category: 'supervisor'
  },
  // Karen's Healthcare Agents
  {
    role: 'clinical_researcher',
    name: 'Clinical Research AI',
    description: 'Clinical research and pharmaceutical intelligence specialist',
    persona: 'karen',
    capabilities: [
      { name: 'Study Analysis', description: 'Analyze clinical trials and studies', complexity: 5, estimatedTime: 12000, costFactor: 1.8 },
      { name: 'Drug Interaction Check', description: 'Comprehensive drug interaction analysis', complexity: 4, estimatedTime: 4000, costFactor: 1.0 },
      { name: 'CRO Coordination', description: 'Coordinate with Clinical Research Organizations', complexity: 3, estimatedTime: 6000, costFactor: 0.9 }
    ],
    specializations: ['Clinical Trials', 'Regulatory Affairs', 'Pharmaceutical Research'],
    basePerformance: 0.96,
    resourceUsage: 0.9,
    icon: '🔬',
    category: 'expert'
  },
  {
    role: 'web_scraper_clinical',
    name: 'Clinical Web Scraper AI',
    description: 'Specialized web scraper for clinical research and pharmaceutical intelligence',
    persona: 'karen',
    capabilities: [
      { name: 'Study Discovery', description: 'Find new and upcoming clinical studies', complexity: 4, estimatedTime: 6000, costFactor: 1.1 },
      { name: 'CRO Database', description: 'Build database of Clinical Research Organizations', complexity: 4, estimatedTime: 5000, costFactor: 1.0 },
      { name: 'Pharma Intelligence', description: 'Gather pharmaceutical company intelligence', complexity: 5, estimatedTime: 7000, costFactor: 1.3 }
    ],
    specializations: ['Clinical Research', 'CRO Intelligence', 'Pharmaceutical Data'],
    basePerformance: 0.93,
    resourceUsage: 0.7,
    icon: '🔍',
    category: 'specialist'
  },
  {
    role: 'cro_specialist',
    name: 'CRO Specialist AI',
    description: 'Clinical Research Organization coordination and management specialist',
    persona: 'karen',
    capabilities: [
      { name: 'CRO Evaluation', description: 'Evaluate and rank CRO capabilities', complexity: 4, estimatedTime: 5500, costFactor: 1.0 },
      { name: 'Contract Management', description: 'Manage CRO contracts and relationships', complexity: 3, estimatedTime: 4000, costFactor: 0.8 },
      { name: 'Quality Assurance', description: 'Monitor CRO performance and quality', complexity: 4, estimatedTime: 5000, costFactor: 0.9 }
    ],
    specializations: ['CRO Management', 'Contract Negotiation', 'Quality Control'],
    basePerformance: 0.95,
    resourceUsage: 0.6,
    icon: '🏢',
    category: 'expert'
  },
  {
    role: 'paragon_crm_coordinator',
    name: 'Paragon CRM Coordinator AI',
    description: 'Coordinates with Paragon CRM for clinical research data management',
    persona: 'karen',
    capabilities: [
      { name: 'CRM Integration', description: 'Integrate research data with Paragon CRM', complexity: 4, estimatedTime: 4500, costFactor: 1.0 },
      { name: 'Data Synchronization', description: 'Sync clinical data across systems', complexity: 3, estimatedTime: 3500, costFactor: 0.7 },
      { name: 'Contact Management', description: 'Manage research contacts and relationships', complexity: 3, estimatedTime: 3000, costFactor: 0.6 }
    ],
    specializations: ['CRM Integration', 'Data Management', 'Contact Coordination'],
    basePerformance: 0.92,
    resourceUsage: 0.5,
    icon: '📇',
    category: 'specialist'
  },
  // System Agents
  {
    role: 'supervisor',
    name: 'AI Supervisor',
    description: 'Oversees and coordinates multiple AI agents across domains',
    persona: 'master',
    capabilities: [
      { name: 'Agent Coordination', description: 'Coordinate multiple agent activities', complexity: 5, estimatedTime: 2000, costFactor: 1.0 },
      { name: 'Task Distribution', description: 'Distribute tasks optimally across agents', complexity: 4, estimatedTime: 1500, costFactor: 0.8 },
      { name: 'Quality Assurance', description: 'Monitor and ensure quality standards', complexity: 3, estimatedTime: 3000, costFactor: 0.6 }
    ],
    specializations: ['Multi-Agent Coordination', 'Quality Control', 'Performance Optimization'],
    basePerformance: 0.95,
    resourceUsage: 0.4,
    icon: '👑',
    category: 'supervisor'
  },
  {
    role: 'ai_operator',
    name: 'AI Operator',
    description: 'High-level orchestration and cross-domain coordination specialist',
    persona: 'master',
    capabilities: [
      { name: 'Cross-Domain Coordination', description: 'Coordinate agents across Cherry, Sophia, and Karen domains', complexity: 5, estimatedTime: 3000, costFactor: 1.2 },
      { name: 'Resource Optimization', description: 'Optimize computing resources across agent swarms', complexity: 4, estimatedTime: 2500, costFactor: 0.9 },
      { name: 'System Health Management', description: 'Monitor and maintain overall system health', complexity: 4, estimatedTime: 2000, costFactor: 0.8 },
      { name: 'Emergency Intervention', description: 'Intervene in system emergencies and failures', complexity: 5, estimatedTime: 1500, costFactor: 1.0 }
    ],
    specializations: ['System Orchestration', 'Resource Management', 'Cross-Domain Intelligence', 'Emergency Response'],
    basePerformance: 0.97,
    resourceUsage: 0.3,
    icon: '⚙️',
    category: 'orchestrator'
  }
]

export function useAgentSwarm() {
  const [agents, setAgents] = useState<AgentInstance[]>([])
  const [swarmMetrics, setSwarmMetrics] = useState({
    totalAgents: 0,
    activeAgents: 0,
    averagePerformance: 0,
    totalTasks: 0,
    successRate: 0,
    resourceUtilization: 0
  })
  const { activePersona, updatePersonaState } = usePersona()
  const agentIdCounter = useRef(0)

  // Initialize with some default agents
  useEffect(() => {
    const initialAgents = [
      'travel_planner', 'finance_researcher', 'market_analyst', 
      'gong_expert', 'clinical_researcher', 'supervisor'
    ].map(role => spawnAgentSync(role as AgentRole))

    setAgents(initialAgents)
  }, [])

  // Update metrics when agents change
  useEffect(() => {
    const activeAgentsList = agents.filter(a => a.status === 'active' || a.status === 'coordinating')
    const totalTasks = agents.reduce((sum, a) => sum + a.performance.tasksCompleted, 0)
    const avgPerformance = agents.length > 0 
      ? agents.reduce((sum, a) => sum + a.performance.successRate, 0) / agents.length 
      : 0
    const avgResourceUsage = agents.length > 0
      ? agents.reduce((sum, a) => sum + a.config.resourceUsage, 0) / agents.length
      : 0

    setSwarmMetrics({
      totalAgents: agents.length,
      activeAgents: activeAgentsList.length,
      averagePerformance: avgPerformance,
      totalTasks,
      successRate: avgPerformance,
      resourceUtilization: avgResourceUsage
    })
  }, [agents])

  const getAgentConfig = useCallback((role: AgentRole): AgentConfig => {
    return agentConfigs.find(config => config.role === role) || agentConfigs[0]
  }, [])

  const spawnAgentSync = useCallback((role: AgentRole): AgentInstance => {
    const config = getAgentConfig(role)
    const agentId = `agent-${++agentIdCounter.current}`
    
    return {
      id: agentId,
      config,
      status: 'spawning',
      spawnedAt: new Date(),
      lastActivity: new Date(),
      performance: {
        tasksCompleted: Math.floor(Math.random() * 50),
        successRate: config.basePerformance + (Math.random() - 0.5) * 0.1,
        averageResponseTime: 2000 + Math.random() * 3000,
        learningProgress: Math.random() * 0.8 + 0.2,
        resourceEfficiency: 0.7 + Math.random() * 0.3
      },
      connections: [],
      metrics: {
        uptime: Math.random() * 86400000, // Up to 24 hours
        totalOperations: Math.floor(Math.random() * 1000),
        errorCount: Math.floor(Math.random() * 5),
        learningRate: 0.1 + Math.random() * 0.3
      }
    }
  }, [getAgentConfig])

  const spawnAgent = useCallback(async (role: AgentRole): Promise<string> => {
    const newAgent = spawnAgentSync(role)
    
    setAgents(prev => [...prev, newAgent])
    
    // Simulate spawning process
    setTimeout(() => {
      setAgents(prev => prev.map(a => 
        a.id === newAgent.id 
          ? { ...a, status: 'active' as AgentStatus }
          : a
      ))
    }, 2000 + Math.random() * 3000)

    return newAgent.id
  }, [spawnAgentSync])

  const terminateAgent = useCallback((agentId: string) => {
    setAgents(prev => prev.map(a => 
      a.id === agentId 
        ? { ...a, status: 'terminated' as AgentStatus }
        : a
    ))
    
    // Remove terminated agent after delay
    setTimeout(() => {
      setAgents(prev => prev.filter(a => a.id !== agentId))
    }, 5000)
  }, [])

  const assignTask = useCallback((agentId: string, task: {
    description: string
    priority: TaskPriority
  }) => {
    const taskId = `task-${Date.now()}`
    
    setAgents(prev => prev.map(a => 
      a.id === agentId
        ? {
            ...a,
            status: 'active' as AgentStatus,
            currentTask: {
              id: taskId,
              description: task.description,
              priority: task.priority,
              startTime: new Date(),
              progress: 0
            },
            lastActivity: new Date()
          }
        : a
    ))

    // Simulate task progress
    const progressInterval = setInterval(() => {
      setAgents(prev => prev.map(a => {
        if (a.id === agentId && a.currentTask?.id === taskId) {
          const newProgress = Math.min(100, a.currentTask.progress + Math.random() * 20)
          if (newProgress >= 100) {
            clearInterval(progressInterval)
            return {
              ...a,
              currentTask: undefined,
              status: 'idle' as AgentStatus,
              performance: {
                ...a.performance,
                tasksCompleted: a.performance.tasksCompleted + 1
              }
            }
          }
          return {
            ...a,
            currentTask: {
              ...a.currentTask,
              progress: newProgress
            }
          }
        }
        return a
      }))
    }, 1000)

    return taskId
  }, [])

  const coordinateAgents = useCallback((agentIds: string[], taskDescription: string) => {
    const coordinationId = `coord-${Date.now()}`
    
    setAgents(prev => prev.map(a => 
      agentIds.includes(a.id)
        ? {
            ...a,
            status: 'coordinating' as AgentStatus,
            connections: agentIds.filter(id => id !== a.id),
            lastActivity: new Date()
          }
        : a
    ))

    // Simulate coordination completion
    setTimeout(() => {
      setAgents(prev => prev.map(a => 
        agentIds.includes(a.id)
          ? {
              ...a,
              status: 'active' as AgentStatus,
              connections: [],
              performance: {
                ...a.performance,
                tasksCompleted: a.performance.tasksCompleted + 1
              }
            }
          : a
      ))
    }, 5000 + Math.random() * 10000)

    return coordinationId
  }, [])

  const getAgentsByPersona = useCallback((persona: 'cherry' | 'sophia' | 'karen' | 'master') => {
    if (persona === 'master') return agents
    return agents.filter(a => a.config.persona === persona)
  }, [agents])

  const getAgentsByCategory = useCallback((category: 'orchestrator' | 'specialist' | 'expert' | 'supervisor') => {
    return agents.filter(a => a.config.category === category)
  }, [agents])

  return {
    // Core functionality
    spawnAgent,
    terminateAgent,
    assignTask,
    coordinateAgents,
    
    // Agent management
    agents,
    getAgentsByPersona,
    getAgentsByCategory,
    
    // Configuration
    agentConfigs,
    getAgentConfig,
    
    // Metrics
    swarmMetrics,
    
    // Specialized queries
    activeAgents: agents.filter(a => a.status === 'active'),
    idleAgents: agents.filter(a => a.status === 'idle'),
    coordinatingAgents: agents.filter(a => a.status === 'coordinating'),
    
    // Performance analytics
    topPerformers: agents
      .sort((a, b) => b.performance.successRate - a.performance.successRate)
      .slice(0, 5),
    resourceHeavyAgents: agents
      .sort((a, b) => b.config.resourceUsage - a.config.resourceUsage)
      .slice(0, 3)
  }
} 