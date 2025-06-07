"use client"

import { useState, useCallback, useEffect } from 'react'
import { usePersona } from '@/contexts/PersonaContext'

export interface ProcessedFile {
  id: string
  name: string
  type: string
  size: number
  status: 'processing' | 'indexed' | 'error'
  chunks: number
  embeddings: number
  summary: string
  keyInsights: string[]
  persona: string
  uploadedAt: Date
}

export interface BusinessToolData {
  toolId: string
  toolName: string
  recordCount: number
  lastSync: Date
  dataTypes: string[]
  persona: string
}

export interface QueryResult {
  id: string
  source: 'file' | 'business_tool' | 'cross_domain'
  sourceId: string
  sourceName: string
  content: string
  relevanceScore: number
  metadata: {
    persona: string
    dataType: string
    timestamp: Date
    context?: string
  }
}

export interface DataQuery {
  query: string
  persona: string
  scope: 'personal' | 'business' | 'clinical' | 'cross_domain'
  sources?: string[]
  filters?: {
    dateRange?: { start: Date; end: Date }
    dataTypes?: string[]
    minRelevance?: number
  }
}

export interface CrossDomainInsight {
  id: string
  title: string
  description: string
  correlatedData: {
    personal?: QueryResult[]
    business?: QueryResult[]
    clinical?: QueryResult[]
  }
  confidenceScore: number
  actionable: boolean
  recommendations?: string[]
}

export function useDataIntegration() {
  const { activePersona } = usePersona()
  const [processedFiles, setProcessedFiles] = useState<ProcessedFile[]>([])
  const [businessToolData, setBusinessToolData] = useState<BusinessToolData[]>([])
  const [isQuerying, setIsQuerying] = useState(false)
  const [queryHistory, setQueryHistory] = useState<DataQuery[]>([])

  // Simulated business tool data
  useEffect(() => {
    setBusinessToolData([
      {
        toolId: 'hubspot',
        toolName: 'HubSpot CRM',
        recordCount: 15420,
        lastSync: new Date(Date.now() - 1000 * 60 * 15),
        dataTypes: ['contacts', 'deals', 'companies', 'activities'],
        persona: 'sophia'
      },
      {
        toolId: 'gong',
        toolName: 'Gong.io',
        recordCount: 890,
        lastSync: new Date(Date.now() - 1000 * 60 * 5),
        dataTypes: ['calls', 'transcripts', 'deals', 'insights'],
        persona: 'sophia'
      },
      {
        toolId: 'quickbooks',
        toolName: 'QuickBooks',
        recordCount: 3200,
        lastSync: new Date(Date.now() - 1000 * 60 * 30),
        dataTypes: ['transactions', 'invoices', 'expenses', 'reports'],
        persona: 'cherry'
      },
      {
        toolId: 'paragon_crm',
        toolName: 'Paragon CRM',
        recordCount: 850,
        lastSync: new Date(Date.now() - 1000 * 60 * 45),
        dataTypes: ['patients', 'studies', 'protocols', 'compliance'],
        persona: 'karen'
      }
    ])
  }, [])

  const processFile = useCallback(async (file: File, persona: string): Promise<ProcessedFile> => {
    // Simulate file processing pipeline
    const processedFile: ProcessedFile = {
      id: `file-${Date.now()}-${Math.random()}`,
      name: file.name,
      type: file.type,
      size: file.size,
      status: 'processing',
      chunks: 0,
      embeddings: 0,
      summary: '',
      keyInsights: [],
      persona,
      uploadedAt: new Date()
    }

    setProcessedFiles(prev => [...prev, processedFile])

    // Simulate processing stages
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Simulate chunking and embedding
    const chunks = Math.floor(Math.random() * 50) + 10
    const embeddings = Math.floor(Math.random() * 200) + 50

    // Generate persona-specific insights
    const insights = generateFileInsights(file.name, persona)
    const summary = generateFileSummary(file.name, persona)

    const finalFile: ProcessedFile = {
      ...processedFile,
      status: 'indexed',
      chunks,
      embeddings,
      summary,
      keyInsights: insights
    }

    setProcessedFiles(prev => 
      prev.map(f => f.id === processedFile.id ? finalFile : f)
    )

    return finalFile
  }, [])

  const executeQuery = useCallback(async (queryData: DataQuery): Promise<QueryResult[]> => {
    setIsQuerying(true)
    setQueryHistory(prev => [...prev, queryData])

    try {
      // Simulate vector search across files and business tools
      await new Promise(resolve => setTimeout(resolve, 1500))

      const results: QueryResult[] = []

      // Search processed files
      processedFiles
        .filter(file => 
          queryData.scope === 'cross_domain' || 
          file.persona === queryData.persona ||
          queryData.persona === 'master'
        )
        .forEach(file => {
          // Simulate relevance scoring
          const relevance = Math.random() * 0.8 + 0.2
          
          results.push({
            id: `file-result-${file.id}`,
            source: 'file',
            sourceId: file.id,
            sourceName: file.name,
            content: generateQueryResult(queryData.query, file),
            relevanceScore: relevance,
            metadata: {
              persona: file.persona,
              dataType: 'document',
              timestamp: file.uploadedAt,
              context: file.summary
            }
          })
        })

      // Search business tool data
      businessToolData
        .filter(tool => 
          queryData.scope === 'cross_domain' || 
          tool.persona === queryData.persona ||
          queryData.persona === 'master'
        )
        .forEach(tool => {
          const relevance = Math.random() * 0.9 + 0.1
          
          results.push({
            id: `tool-result-${tool.toolId}`,
            source: 'business_tool',
            sourceId: tool.toolId,
            sourceName: tool.toolName,
            content: generateBusinessToolResult(queryData.query, tool),
            relevanceScore: relevance,
            metadata: {
              persona: tool.persona,
              dataType: 'business_data',
              timestamp: tool.lastSync,
              context: `${tool.recordCount} records`
            }
          })
        })

      // Sort by relevance and apply filters
      let filteredResults = results
        .sort((a, b) => b.relevanceScore - a.relevanceScore)

      if (queryData.filters?.minRelevance) {
        filteredResults = filteredResults.filter(
          result => result.relevanceScore >= queryData.filters.minRelevance!
        )
      }

      if (queryData.filters?.dataTypes) {
        filteredResults = filteredResults.filter(
          result => queryData.filters.dataTypes!.includes(result.metadata.dataType)
        )
      }

      return filteredResults.slice(0, 10) // Return top 10 results

    } finally {
      setIsQuerying(false)
    }
  }, [processedFiles, businessToolData])

  const generateCrossDomainInsights = useCallback(async (): Promise<CrossDomainInsight[]> => {
    // Simulate cross-domain analysis
    await new Promise(resolve => setTimeout(resolve, 2000))

    const insights: CrossDomainInsight[] = [
      {
        id: 'insight-1',
        title: 'Business Performance Correlation with Personal Finance',
        description: 'Strong correlation found between Q4 business revenue and personal investment portfolio performance',
        correlatedData: {
          business: processedFiles.filter(f => f.persona === 'sophia').slice(0, 2).map(f => ({
            id: f.id,
            source: 'file' as const,
            sourceId: f.id,
            sourceName: f.name,
            content: f.summary,
            relevanceScore: 0.85,
            metadata: {
              persona: f.persona,
              dataType: 'document',
              timestamp: f.uploadedAt
            }
          })),
          personal: processedFiles.filter(f => f.persona === 'cherry').slice(0, 2).map(f => ({
            id: f.id,
            source: 'file' as const,
            sourceId: f.id,
            sourceName: f.name,
            content: f.summary,
            relevanceScore: 0.82,
            metadata: {
              persona: f.persona,
              dataType: 'document',
              timestamp: f.uploadedAt
            }
          }))
        },
        confidenceScore: 0.87,
        actionable: true,
        recommendations: [
          'Consider increasing business investment during high-revenue quarters',
          'Diversify personal portfolio to hedge against business volatility',
          'Set up automated investment transfers tied to business milestones'
        ]
      },
      {
        id: 'insight-2',
        title: 'Health Metrics Impact on Business Productivity',
        description: 'Client health monitoring patterns correlate with team productivity metrics',
        correlatedData: {
          clinical: processedFiles.filter(f => f.persona === 'karen').slice(0, 1).map(f => ({
            id: f.id,
            source: 'file' as const,
            sourceId: f.id,
            sourceName: f.name,
            content: f.summary,
            relevanceScore: 0.78,
            metadata: {
              persona: f.persona,
              dataType: 'document',
              timestamp: f.uploadedAt
            }
          })),
          business: businessToolData.filter(t => t.persona === 'sophia').slice(0, 1).map(t => ({
            id: t.toolId,
            source: 'business_tool' as const,
            sourceId: t.toolId,
            sourceName: t.toolName,
            content: `${t.recordCount} business records analyzed`,
            relevanceScore: 0.75,
            metadata: {
              persona: t.persona,
              dataType: 'business_data',
              timestamp: t.lastSync
            }
          }))
        },
        confidenceScore: 0.73,
        actionable: true,
        recommendations: [
          'Implement wellness programs during high-stress business periods',
          'Monitor team health metrics during product launches',
          'Establish early warning systems for productivity drops'
        ]
      }
    ]

    return insights
  }, [processedFiles, businessToolData])

  const getPersonaDataSummary = useCallback((persona: string) => {
    const files = processedFiles.filter(f => f.persona === persona)
    const tools = businessToolData.filter(t => t.persona === persona)
    
    return {
      fileCount: files.length,
      totalChunks: files.reduce((sum, f) => sum + f.chunks, 0),
      totalEmbeddings: files.reduce((sum, f) => sum + f.embeddings, 0),
      businessTools: tools.length,
      totalRecords: tools.reduce((sum, t) => sum + t.recordCount, 0),
      lastActivity: Math.max(
        ...files.map(f => f.uploadedAt.getTime()),
        ...tools.map(t => t.lastSync.getTime())
      )
    }
  }, [processedFiles, businessToolData])

  return {
    // Data
    processedFiles,
    businessToolData,
    queryHistory,
    
    // States
    isQuerying,
    
    // Actions
    processFile,
    executeQuery,
    generateCrossDomainInsights,
    getPersonaDataSummary,
    
    // Helpers
    totalFiles: processedFiles.length,
    totalBusinessTools: businessToolData.length,
    totalRecords: businessToolData.reduce((sum, tool) => sum + tool.recordCount, 0)
  }
}

// Helper functions
function generateFileInsights(fileName: string, persona: string): string[] {
  const insights = {
    cherry: [
      "Investment portfolio shows 12% annual growth potential",
      "Ranch maintenance costs optimized by 15%",
      "Travel expenses can be reduced through advance booking",
      "Diversification opportunities identified in tech sector"
    ],
    sophia: [
      "Top 20% clients generate 65% of revenue",
      "Sales cycle shortened by 12 days with AI optimization",
      "Email campaign performance improved 34%",
      "Market expansion opportunity in healthcare vertical"
    ],
    karen: [
      "Patient retention rate achieved 94% target",
      "Clinical endpoint success rate: 87%",
      "Regulatory compliance timeline accelerated 6 weeks",
      "Trial recruitment exceeded targets by 18%"
    ],
    master: [
      "Cross-domain efficiency improved 28%",
      "Data correlation accuracy: 95%",
      "System response time optimized 40%",
      "Resource utilization increased 22%"
    ]
  }

  const personaInsights = insights[persona] || insights.master
  return personaInsights.slice(0, 3)
}

function generateFileSummary(fileName: string, persona: string): string {
  const summaries = {
    cherry: [
      "Financial analysis reveals strong opportunities in technology investments",
      "Ranch expense optimization identifies significant cost savings",
      "Travel planning analysis shows budget optimization potential"
    ],
    sophia: [
      "Client data analysis identifies high-value engagement opportunities",
      "Sales performance metrics indicate strong growth trajectory",
      "Market research reveals expanding customer segments"
    ],
    karen: [
      "Clinical trial data demonstrates positive efficacy outcomes",
      "Patient management analysis shows improved retention rates",
      "Regulatory compliance review identifies optimization opportunities"
    ],
    master: [
      "Comprehensive analysis reveals cross-domain optimization potential",
      "System performance metrics indicate successful integration",
      "Multi-source data correlation provides actionable insights"
    ]
  }

  const personaSummaries = summaries[persona] || summaries.master
  return personaSummaries[Math.floor(Math.random() * personaSummaries.length)]
}

function generateQueryResult(query: string, file: ProcessedFile): string {
  return `Relevant information found in ${file.name}: ${file.summary.substring(0, 150)}... This document contains ${file.chunks} relevant sections with ${file.embeddings} indexed data points.`
}

function generateBusinessToolResult(query: string, tool: BusinessToolData): string {
  return `${tool.toolName} analysis reveals: ${tool.recordCount} records processed, showing relevant patterns in ${tool.dataTypes.join(', ')}. Last updated ${tool.lastSync.toLocaleDateString()}.`
} 