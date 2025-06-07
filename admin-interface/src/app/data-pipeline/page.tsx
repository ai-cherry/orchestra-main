"use client"

import React, { useState, useRef, useCallback } from "react"
import { Menu, X, Upload, FileText, Database, Brain, Search, BarChart3, AlertCircle, CheckCircle, Clock, Zap, Download, Eye, Trash2, File, Layers, TrendingUp, Image, Video, Music, Archive } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { PersonaSelector } from "@/components/persona-selector"
import { usePersona } from "@/contexts/PersonaContext"
import Sidebar from "@/components/sidebar"

interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadedAt: Date
  status: 'uploading' | 'processing' | 'vectorizing' | 'indexed' | 'error'
  progress: number
  persona: string
  chunks?: number
  embeddings?: number
  summary?: string
  keyInsights?: string[]
  errorMessage?: string
}

interface DataSource {
  id: string
  name: string
  type: 'api' | 'database' | 'file'
  status: 'connected' | 'disconnected' | 'syncing' | 'error'
  lastSync?: Date
  recordCount?: number
  persona: string
  icon: string
}

interface ProcessingStats {
  totalFiles: number
  totalSize: number
  totalChunks: number
  totalEmbeddings: number
  processingTime: number
  successRate: number
}

const DataPipelinePage = () => {
  const { activePersona } = usePersona()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [dataSources, setDataSources] = useState<DataSource[]>([
    {
      id: 'hubspot',
      name: 'HubSpot CRM',
      type: 'api',
      status: 'connected',
      lastSync: new Date(Date.now() - 1000 * 60 * 15),
      recordCount: 15420,
      persona: 'sophia',
      icon: '🎯'
    },
    {
      id: 'salesforce',
      name: 'Salesforce',
      type: 'api', 
      status: 'disconnected',
      persona: 'sophia',
      icon: '☁️'
    },
    {
      id: 'gong',
      name: 'Gong.io',
      type: 'api',
      status: 'syncing',
      lastSync: new Date(),
      recordCount: 890,
      persona: 'sophia',
      icon: '🎙️'
    },
    {
      id: 'personal_finance',
      name: 'Personal Finance DB',
      type: 'database',
      status: 'connected',
      lastSync: new Date(Date.now() - 1000 * 60 * 30),
      recordCount: 3200,
      persona: 'cherry',
      icon: '💰'
    },
    {
      id: 'clinical_trials',
      name: 'Clinical Trials DB',
      type: 'database',
      status: 'connected',
      lastSync: new Date(Date.now() - 1000 * 60 * 60),
      recordCount: 850,
      persona: 'karen',
      icon: '🔬'
    }
  ])
  const [isDragging, setIsDragging] = useState(false)
  const [selectedTab, setSelectedTab] = useState<'upload' | 'sources' | 'analytics'>('upload')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const getPersonaColors = (persona: string) => {
    switch (persona) {
      case "cherry":
        return {
          bg: "bg-red-500/10 border-red-500/20",
          text: "text-red-400",
          button: "bg-red-600 hover:bg-red-700"
        }
      case "sophia":
        return {
          bg: "bg-blue-500/10 border-blue-500/20", 
          text: "text-blue-400",
          button: "bg-blue-600 hover:bg-blue-700"
        }
      case "karen":
        return {
          bg: "bg-emerald-500/10 border-emerald-500/20",
          text: "text-emerald-400", 
          button: "bg-emerald-600 hover:bg-emerald-700"
        }
      case "master":
        return {
          bg: "bg-yellow-500/10 border-yellow-500/20",
          text: "text-yellow-400",
          button: "bg-yellow-600 hover:bg-yellow-700"
        }
      default:
        return {
          bg: "bg-gray-500/10 border-gray-500/20",
          text: "text-gray-400",
          button: "bg-gray-600 hover:bg-gray-700"
        }
    }
  }

  const colors = getPersonaColors(activePersona)

  const processingStats: ProcessingStats = {
    totalFiles: uploadedFiles.length,
    totalSize: uploadedFiles.reduce((sum, file) => sum + file.size, 0),
    totalChunks: uploadedFiles.reduce((sum, file) => sum + (file.chunks || 0), 0),
    totalEmbeddings: uploadedFiles.reduce((sum, file) => sum + (file.embeddings || 0), 0),
    processingTime: uploadedFiles.reduce((sum, file) => sum + Math.random() * 10000, 0),
    successRate: uploadedFiles.length > 0 ? uploadedFiles.filter(f => f.status === 'indexed').length / uploadedFiles.length * 100 : 0
  }

  const handleFileUpload = useCallback(async (files: FileList) => {
    const newFiles: UploadedFile[] = Array.from(files).map(file => ({
      id: `file-${Date.now()}-${Math.random()}`,
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date(),
      status: 'uploading',
      progress: 0,
      persona: activePersona
    }))

    setUploadedFiles(prev => [...prev, ...newFiles])

    // Simulate file processing
    for (const file of newFiles) {
      await simulateFileProcessing(file)
    }
  }, [activePersona])

  const simulateFileProcessing = async (file: UploadedFile) => {
    const stages = [
      { status: 'uploading' as const, duration: 1000 },
      { status: 'processing' as const, duration: 2000 },
      { status: 'vectorizing' as const, duration: 3000 },
      { status: 'indexed' as const, duration: 500 }
    ]

    for (let i = 0; i < stages.length; i++) {
      const stage = stages[i]
      
      setUploadedFiles(prev => prev.map(f => 
        f.id === file.id 
          ? { 
              ...f, 
              status: stage.status,
              progress: Math.floor((i / (stages.length - 1)) * 100)
            }
          : f
      ))

      await new Promise(resolve => setTimeout(resolve, stage.duration))

      // Update progress during stage
      if (i < stages.length - 1) {
        const progressUpdates = 5
        for (let j = 1; j <= progressUpdates; j++) {
          await new Promise(resolve => setTimeout(resolve, stage.duration / progressUpdates))
          setUploadedFiles(prev => prev.map(f => 
            f.id === file.id 
              ? { 
                  ...f, 
                  progress: Math.floor((i / (stages.length - 1)) * 100) + (j / progressUpdates) * (100 / (stages.length - 1))
                }
              : f
          ))
        }
      }
    }

    // Add final metadata
    setUploadedFiles(prev => prev.map(f => 
      f.id === file.id 
        ? {
            ...f,
            progress: 100,
            chunks: Math.floor(Math.random() * 50) + 10,
            embeddings: Math.floor(Math.random() * 200) + 50,
            summary: generateFileSummary(file.name, activePersona),
            keyInsights: generateKeyInsights(file.name, activePersona)
          }
        : f
    ))
  }

  const generateFileSummary = (fileName: string, persona: string): string => {
    const summaries = {
      cherry: [
        "Financial analysis reveals strong investment opportunities in tech sector",
        "Ranch expense tracking shows 15% savings opportunity in equipment maintenance",
        "Travel itinerary optimized for cost and experience balance"
      ],
      sophia: [
        "Client data analysis identifies 3 high-risk accounts requiring immediate attention",
        "Sales pipeline shows 23% increase in qualified leads this quarter",
        "Market research indicates expanding opportunity in healthcare vertical"
      ],
      karen: [
        "Clinical trial data shows promising results for Phase II endpoints",
        "Regulatory compliance analysis reveals 2 minor documentation gaps",
        "Patient recruitment metrics exceed target by 18%"
      ],
      master: [
        "Cross-domain analysis reveals correlations between personal and business metrics",
        "Comprehensive data integration completed successfully",
        "System performance optimized across all data sources"
      ]
    }

    const personaSummaries = summaries[persona] || summaries.master
    return personaSummaries[Math.floor(Math.random() * personaSummaries.length)]
  }

  const generateKeyInsights = (fileName: string, persona: string): string[] => {
    const insights = {
      cherry: [
        "Swing trading strategy shows 12% annual return potential",
        "Ranch landscaping costs down 8% from optimization",
        "Travel expenses can be reduced by 15% with advance booking"
      ],
      sophia: [
        "Top 20% of clients generate 65% of revenue",
        "Email campaign open rates improved 34% with AI optimization",
        "Sales cycle shortened by 12 days on average"
      ],
      karen: [
        "Patient retention rate increased to 94%",
        "Clinical endpoint achievement rate: 87%",
        "Regulatory timeline accelerated by 6 weeks"
      ],
      master: [
        "System efficiency improved 28% through cross-domain optimization",
        "Data correlation accuracy reached 95%",
        "Response time improved by 40% across all queries"
      ]
    }

    const personaInsights = insights[persona] || insights.master
    return personaInsights.slice(0, 3)
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    if (e.dataTransfer.files) {
      handleFileUpload(e.dataTransfer.files)
    }
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatTimeAgo = (date: Date): string => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d ago`
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploading':
        return <Upload className="h-4 w-4 text-blue-400 animate-pulse" />
      case 'processing':
        return <Brain className="h-4 w-4 text-yellow-400 animate-spin" />
      case 'vectorizing':
        return <Database className="h-4 w-4 text-purple-400 animate-pulse" />
      case 'indexed':
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-400" />
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case 'disconnected':
        return <AlertCircle className="h-4 w-4 text-gray-400" />
      case 'syncing':
        return <Clock className="h-4 w-4 text-blue-400 animate-spin" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const recentUploads = [
    {
      id: '1',
      name: 'Q2_Financial_Report.pdf',
      type: 'document',
      size: '2.4 MB',
      status: 'completed',
      uploadedAt: '2 minutes ago',
      processedAt: '1 minute ago',
      vectorsGenerated: 1247,
      persona: 'Cherry',
      tags: ['finance', 'quarterly', 'revenue']
    },
    {
      id: '2',
      name: 'Customer_Interview_Notes.docx',
      type: 'document',
      size: '856 KB',
      status: 'processing',
      uploadedAt: '5 minutes ago',
      processedAt: null,
      vectorsGenerated: null,
      persona: 'Sophia',
      tags: ['customer-research', 'insights']
    },
    {
      id: '3',
      name: 'Product_Demo_Video.mp4',
      type: 'video',
      size: '45.2 MB',
      status: 'completed',
      uploadedAt: '1 hour ago',
      processedAt: '45 minutes ago',
      vectorsGenerated: 3456,
      persona: 'Karen',
      tags: ['product', 'demo', 'marketing']
    },
    {
      id: '4',
      name: 'Clinical_Research_Data.csv',
      type: 'data',
      size: '12.8 MB',
      status: 'failed',
      uploadedAt: '2 hours ago',
      processedAt: null,
      vectorsGenerated: null,
      persona: 'Karen',
      tags: ['clinical', 'research', 'data']
    },
    {
      id: '5',
      name: 'Marketing_Assets_Bundle.zip',
      type: 'archive',
      size: '156 MB',
      status: 'queued',
      uploadedAt: '3 hours ago',
      processedAt: null,
      vectorsGenerated: null,
      persona: 'Sophia',
      tags: ['marketing', 'assets', 'bundle']
    }
  ];

  const pipelineSteps = [
    {
      id: 'upload',
      name: 'File Upload',
      description: 'Secure file ingestion and validation',
      icon: Upload,
      status: 'active',
      filesProcessed: 1247
    },
    {
      id: 'parse',
      name: 'Content Parsing',
      description: 'Extract text and structure from files',
      icon: FileText,
      status: 'active',
      filesProcessed: 1243
    },
    {
      id: 'chunk',
      name: 'Text Chunking',
      description: 'Split content into semantic chunks',
      icon: Layers,
      status: 'active',
      filesProcessed: 1240
    },
    {
      id: 'embed',
      name: 'Vector Embedding',
      description: 'Generate vector representations',
      icon: Brain,
      status: 'active',
      filesProcessed: 1238
    },
    {
      id: 'store',
      name: 'Vector Storage',
      description: 'Store in Weaviate database',
      icon: Database,
      status: 'active',
      filesProcessed: 1238
    }
  ];

  const getFileIcon = (type) => {
    switch (type) {
      case 'document': return <FileText className="w-5 h-5" />;
      case 'video': return <Video className="w-5 h-5" />;
      case 'audio': return <Music className="w-5 h-5" />;
      case 'image': return <Image className="w-5 h-5" />;
      case 'archive': return <Archive className="w-5 h-5" />;
      case 'data': return <BarChart3 className="w-5 h-5" />;
      default: return <File className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return { bg: 'bg-green-400/10', text: 'text-green-400', border: 'border-green-400/30' };
      case 'processing': return { bg: 'bg-blue-400/10', text: 'text-blue-400', border: 'border-blue-400/30' };
      case 'queued': return { bg: 'bg-yellow-400/10', text: 'text-yellow-400', border: 'border-yellow-400/30' };
      case 'failed': return { bg: 'bg-red-400/10', text: 'text-red-400', border: 'border-red-400/30' };
      default: return { bg: 'bg-gray-400/10', text: 'text-gray-400', border: 'border-gray-400/30' };
    }
  };

  const stats = {
    totalFiles: recentUploads.length,
    completed: recentUploads.filter(f => f.status === 'completed').length,
    processing: recentUploads.filter(f => f.status === 'processing').length,
    totalVectors: recentUploads.reduce((sum, f) => sum + (f.vectorsGenerated || 0), 0)
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2a1a1a 100%)',
      color: '#ffffff',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.4)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(220, 38, 127, 0.2)',
        padding: '24px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div>
            <h1 style={{
              fontSize: '32px',
              fontWeight: '700',
              margin: '0 0 8px 0',
              background: 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Data Pipeline
            </h1>
            <p style={{
              color: '#888',
              fontSize: '16px',
              margin: '0'
            }}>
              Upload, process, and vectorize your data for AI-powered insights
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button style={{
              background: 'rgba(220, 38, 127, 0.1)',
              border: '1px solid rgba(220, 38, 127, 0.3)',
              borderRadius: '8px',
              padding: '8px 16px',
              color: '#dc267f',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}>
              <Database className="w-4 h-4" />
              View Vector Store
            </button>
          </div>
        </div>
      </div>

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '24px'
      }}>
        {/* Stats Overview */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '32px'
        }}>
          {[
            { label: 'Total Files', value: stats.totalFiles, icon: File, color: '#3b82f6' },
            { label: 'Completed', value: stats.completed, icon: CheckCircle, color: '#10b981' },
            { label: 'Processing', value: stats.processing, icon: Clock, color: '#f59e0b' },
            { label: 'Vector Embeddings', value: `${stats.totalVectors.toLocaleString()}`, icon: Brain, color: '#dc267f' }
          ].map((stat, index) => (
            <div key={index} style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              padding: '24px',
              textAlign: 'center'
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '12px'
              }}>
                <div style={{
                  background: `${stat.color}20`,
                  borderRadius: '12px',
                  padding: '12px',
                  display: 'inline-flex'
                }}>
                  <stat.icon style={{ width: '24px', height: '24px', color: stat.color }} />
                </div>
              </div>
              <div style={{
                fontSize: '32px',
                fontWeight: '700',
                color: stat.color,
                marginBottom: '4px'
              }}>
                {stat.value}
              </div>
              <div style={{
                color: '#888',
                fontSize: '14px'
              }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '24px',
          background: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '8px'
        }}>
          {[
            { id: 'upload', label: 'File Upload', icon: Upload },
            { id: 'pipeline', label: 'Processing Pipeline', icon: Zap },
            { id: 'history', label: 'Upload History', icon: FileText }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setSelectedTab(tab.id)}
              style={{
                background: selectedTab === tab.id 
                  ? 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)'
                  : 'transparent',
                border: 'none',
                borderRadius: '8px',
                padding: '12px 20px',
                color: selectedTab === tab.id ? '#ffffff' : '#888',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {selectedTab === 'upload' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            padding: '32px'
          }}>
            {/* Upload Area */}
            <div
              style={{
                border: `2px dashed ${isDragging ? '#dc267f' : 'rgba(255, 255, 255, 0.2)'}`,
                borderRadius: '12px',
                padding: '48px',
                textAlign: 'center',
                transition: 'all 0.3s ease',
                background: isDragging ? 'rgba(220, 38, 127, 0.05)' : 'rgba(0, 0, 0, 0.2)',
                cursor: 'pointer'
              }}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '16px'
              }}>
                <div style={{
                  background: 'rgba(220, 38, 127, 0.1)',
                  borderRadius: '20px',
                  padding: '20px',
                  display: 'inline-flex'
                }}>
                  <Upload style={{ width: '48px', height: '48px', color: '#dc267f' }} />
                </div>
                <div>
                  <h3 style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    margin: '0 0 8px 0',
                    color: '#ffffff'
                  }}>
                    Drop your files here
                  </h3>
                  <p style={{
                    color: '#888',
                    fontSize: '16px',
                    margin: '0 0 16px 0'
                  }}>
                    or click to browse and select files
                  </p>
                </div>
                <button style={{
                  background: 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '12px 24px',
                  color: '#ffffff',
                  fontSize: '16px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Upload className="w-5 h-5" />
                  Choose Files
                </button>
              </div>
            </div>

            {/* Supported Formats */}
            <div style={{
              marginTop: '24px',
              textAlign: 'center'
            }}>
              <p style={{
                color: '#888',
                fontSize: '14px',
                marginBottom: '12px'
              }}>
                Supported formats:
              </p>
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                flexWrap: 'wrap',
                gap: '8px'
              }}>
                {['PDF', 'DOCX', 'TXT', 'CSV', 'MP4', 'MP3', 'JPG', 'PNG', 'ZIP'].map(format => (
                  <span key={format} style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '6px',
                    padding: '4px 8px',
                    fontSize: '12px',
                    color: '#888'
                  }}>
                    {format}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'pipeline' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            padding: '32px'
          }}>
            {/* Pipeline Steps */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '32px'
            }}>
              {pipelineSteps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    flex: 1
                  }}>
                    <div style={{
                      background: step.status === 'active' 
                        ? 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)'
                        : 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '20px',
                      padding: '16px',
                      marginBottom: '12px',
                      display: 'flex'
                    }}>
                      <step.icon style={{ 
                        width: '32px', 
                        height: '32px', 
                        color: step.status === 'active' ? '#ffffff' : '#888' 
                      }} />
                    </div>
                    <h4 style={{
                      fontSize: '16px',
                      fontWeight: '600',
                      margin: '0 0 4px 0',
                      color: '#ffffff'
                    }}>
                      {step.name}
                    </h4>
                    <p style={{
                      fontSize: '12px',
                      color: '#888',
                      textAlign: 'center',
                      margin: '0 0 8px 0',
                      maxWidth: '120px'
                    }}>
                      {step.description}
                    </p>
                    <div style={{
                      fontSize: '14px',
                      fontWeight: '600',
                      color: '#dc267f'
                    }}>
                      {step.filesProcessed.toLocaleString()}
                    </div>
                    <div style={{
                      fontSize: '11px',
                      color: '#888'
                    }}>
                      files processed
                    </div>
                  </div>
                  {index < pipelineSteps.length - 1 && (
                    <div style={{
                      height: '2px',
                      width: '60px',
                      background: 'linear-gradient(90deg, #dc267f 0%, rgba(220, 38, 127, 0.3) 100%)',
                      marginBottom: '60px'
                    }} />
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* Pipeline Metrics */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px'
            }}>
              {[
                { label: 'Processing Rate', value: '12.3 files/min', trend: '+5.2%' },
                { label: 'Avg Vector Gen Time', value: '2.4 seconds', trend: '-12%' },
                { label: 'Success Rate', value: '98.7%', trend: '+1.2%' },
                { label: 'Storage Efficiency', value: '85.3%', trend: '+3.1%' }
              ].map((metric, index) => (
                <div key={index} style={{
                  background: 'rgba(0, 0, 0, 0.2)',
                  borderRadius: '12px',
                  padding: '16px',
                  textAlign: 'center'
                }}>
                  <div style={{
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#ffffff',
                    marginBottom: '4px'
                  }}>
                    {metric.value}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#888',
                    marginBottom: '8px'
                  }}>
                    {metric.label}
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: metric.trend.startsWith('+') ? '#10b981' : '#ef4444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px'
                  }}>
                    <TrendingUp className="w-3 h-3" />
                    {metric.trend}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedTab === 'history' && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.05)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '16px',
            padding: '32px'
          }}>
            {/* Upload History */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              {recentUploads.map(upload => {
                const statusStyle = getStatusColor(upload.status);
                return (
                  <div key={upload.id} style={{
                    background: 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '12px',
                    padding: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px'
                  }}>
                    {/* File Icon */}
                    <div style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '12px',
                      padding: '12px',
                      display: 'flex'
                    }}>
                      {getFileIcon(upload.type)}
                    </div>

                    {/* File Info */}
                    <div style={{ flex: 1 }}>
                      <h4 style={{
                        fontSize: '16px',
                        fontWeight: '600',
                        margin: '0 0 4px 0',
                        color: '#ffffff'
                      }}>
                        {upload.name}
                      </h4>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        fontSize: '12px',
                        color: '#888'
                      }}>
                        <span>{upload.size}</span>
                        <span>•</span>
                        <span>Uploaded {upload.uploadedAt}</span>
                        {upload.processedAt && (
                          <>
                            <span>•</span>
                            <span>Processed {upload.processedAt}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Status */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '500',
                        textTransform: 'capitalize'
                      }} className={`${statusStyle.bg} ${statusStyle.text} border ${statusStyle.border}`}>
                        {getStatusIcon(upload.status)}
                        {upload.status}
                      </div>
                    </div>

                    {/* Vectors Generated */}
                    {upload.vectorsGenerated && (
                      <div style={{
                        textAlign: 'right'
                      }}>
                        <div style={{
                          fontSize: '16px',
                          fontWeight: '600',
                          color: '#dc267f'
                        }}>
                          {upload.vectorsGenerated.toLocaleString()}
                        </div>
                        <div style={{
                          fontSize: '11px',
                          color: '#888'
                        }}>
                          vectors
                        </div>
                      </div>
                    )}

                    {/* Tags */}
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      minWidth: '120px'
                    }}>
                      <div style={{
                        fontSize: '11px',
                        color: '#888'
                      }}>
                        {upload.persona}
                      </div>
                      <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '4px'
                      }}>
                        {upload.tags.slice(0, 2).map((tag, index) => (
                          <span key={index} style={{
                            background: 'rgba(220, 38, 127, 0.1)',
                            border: '1px solid rgba(220, 38, 127, 0.3)',
                            borderRadius: '6px',
                            padding: '2px 6px',
                            fontSize: '10px',
                            color: '#dc267f'
                          }}>
                            {tag}
                          </span>
                        ))}
                        {upload.tags.length > 2 && (
                          <span style={{
                            background: 'rgba(255, 255, 255, 0.1)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '6px',
                            padding: '2px 6px',
                            fontSize: '10px',
                            color: '#888'
                          }}>
                            +{upload.tags.length - 2}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DataPipelinePage; 