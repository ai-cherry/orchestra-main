import React, { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Check, AlertCircle, Loader2 } from 'lucide-react'
import { cn, formatBytes, getFileIcon, generateId } from '@/lib/utils'
import { usePersona } from '@/contexts/PersonaContext'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface UploadFile {
  id: string
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
  metadata?: any
}

interface MetadataFormData {
  persona: string
  fileType: string
  processingIntent: string
  customMetadata: Record<string, any>
  tags: string[]
}

// Cherry (Creative) Metadata Form
function CherryMetadataForm({ onSubmit, initialData }: { 
  onSubmit: (data: MetadataFormData) => void
  initialData?: Partial<MetadataFormData>
}) {
  const [formData, setFormData] = useState({
    creativeIntent: initialData?.customMetadata?.creativeIntent || '',
    artisticStyle: initialData?.customMetadata?.artisticStyle || [],
    targetAudience: initialData?.customMetadata?.targetAudience || '',
    brandGuidelines: initialData?.customMetadata?.brandGuidelines || '',
    usageContext: initialData?.customMetadata?.usageContext || []
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      persona: 'cherry',
      fileType: 'creative',
      processingIntent: formData.creativeIntent,
      customMetadata: formData,
      tags: [...formData.artisticStyle, ...formData.usageContext]
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Creative Intent</label>
          <select 
            value={formData.creativeIntent}
            onChange={(e) => setFormData(prev => ({ ...prev, creativeIntent: e.target.value }))}
            className="w-full p-2 border border-input rounded-md bg-background"
            required
          >
            <option value="">Select intent...</option>
            <option value="inspiration">Inspiration and Reference</option>
            <option value="style-guide">Style Guide and Branding</option>
            <option value="templates">Content Creation Templates</option>
            <option value="patterns">Design Patterns and Examples</option>
            <option value="brief">Creative Brief and Requirements</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Artistic Style</label>
          <div className="space-y-1">
            {['Modern/Contemporary', 'Minimalist', 'Bold/Dramatic', 'Elegant/Sophisticated', 'Playful/Fun', 'Professional/Corporate'].map(style => (
              <label key={style} className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.artisticStyle.includes(style)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFormData(prev => ({ ...prev, artisticStyle: [...prev.artisticStyle, style] }))
                    } else {
                      setFormData(prev => ({ ...prev, artisticStyle: prev.artisticStyle.filter((s: string) => s !== style) }))
                    }
                  }}
                  className="mr-2"
                />
                <span className="text-sm">{style}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Target Audience</label>
        <textarea
          value={formData.targetAudience}
          onChange={(e) => setFormData(prev => ({ ...prev, targetAudience: e.target.value }))}
          placeholder="Describe the intended audience for this creative content..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Brand Guidelines</label>
        <textarea
          value={formData.brandGuidelines}
          onChange={(e) => setFormData(prev => ({ ...prev, brandGuidelines: e.target.value }))}
          placeholder="Any specific brand requirements, color schemes, or style constraints..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Usage Context</label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {['Marketing Materials', 'Social Media Content', 'Website Design', 'Print Materials', 'Video Content', 'Presentations'].map(context => (
            <label key={context} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.usageContext.includes(context)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setFormData(prev => ({ ...prev, usageContext: [...prev.usageContext, context] }))
                  } else {
                    setFormData(prev => ({ ...prev, usageContext: prev.usageContext.filter((c: string) => c !== context) }))
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm">{context}</span>
            </label>
          ))}
        </div>
      </div>

      <button
        type="submit"
        className="w-full px-4 py-2 bg-cherry-600 text-white rounded-md hover:bg-cherry-700 transition-colors"
      >
        Process Creative Content
      </button>
    </form>
  )
}

// Sophia (Strategic) Metadata Form
function SophiaMetadataForm({ onSubmit, initialData }: { 
  onSubmit: (data: MetadataFormData) => void
  initialData?: Partial<MetadataFormData>
}) {
  const [formData, setFormData] = useState({
    analysisType: initialData?.customMetadata?.analysisType || '',
    businessDomain: initialData?.customMetadata?.businessDomain || [],
    timeframe: initialData?.customMetadata?.timeframe || '',
    stakeholders: initialData?.customMetadata?.stakeholders || '',
    decisionContext: initialData?.customMetadata?.decisionContext || '',
    successMetrics: initialData?.customMetadata?.successMetrics || ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      persona: 'sophia',
      fileType: 'strategic',
      processingIntent: formData.analysisType,
      customMetadata: formData,
      tags: [...formData.businessDomain, formData.timeframe].filter(Boolean)
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Analysis Type</label>
          <select 
            value={formData.analysisType}
            onChange={(e) => setFormData(prev => ({ ...prev, analysisType: e.target.value }))}
            className="w-full p-2 border border-input rounded-md bg-background"
            required
          >
            <option value="">Select type...</option>
            <option value="market-research">Market Research and Intelligence</option>
            <option value="competitive-analysis">Competitive Analysis</option>
            <option value="strategic-planning">Strategic Planning Documents</option>
            <option value="performance-metrics">Performance Metrics and KPIs</option>
            <option value="process-documentation">Business Process Documentation</option>
            <option value="risk-assessment">Risk Assessment and Compliance</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Strategic Timeframe</label>
          <div className="space-y-1">
            {['Immediate (0-3 months)', 'Short-term (3-12 months)', 'Medium-term (1-3 years)', 'Long-term (3+ years)'].map(timeframe => (
              <label key={timeframe} className="flex items-center">
                <input
                  type="radio"
                  name="timeframe"
                  value={timeframe}
                  checked={formData.timeframe === timeframe}
                  onChange={(e) => setFormData(prev => ({ ...prev, timeframe: e.target.value }))}
                  className="mr-2"
                />
                <span className="text-sm">{timeframe}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Business Domain</label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {['Technology', 'Healthcare', 'Finance', 'Retail', 'Manufacturing', 'Education', 'Government', 'Non-profit'].map(domain => (
            <label key={domain} className="flex items-center">
              <input
                type="checkbox"
                checked={formData.businessDomain.includes(domain)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setFormData(prev => ({ ...prev, businessDomain: [...prev.businessDomain, domain] }))
                  } else {
                    setFormData(prev => ({ ...prev, businessDomain: prev.businessDomain.filter((d: string) => d !== domain) }))
                  }
                }}
                className="mr-2"
              />
              <span className="text-sm">{domain}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Key Stakeholders</label>
        <textarea
          value={formData.stakeholders}
          onChange={(e) => setFormData(prev => ({ ...prev, stakeholders: e.target.value }))}
          placeholder="Who are the primary stakeholders affected by this information..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Decision Context</label>
        <textarea
          value={formData.decisionContext}
          onChange={(e) => setFormData(prev => ({ ...prev, decisionContext: e.target.value }))}
          placeholder="What strategic decisions will this information support..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Success Metrics</label>
        <textarea
          value={formData.successMetrics}
          onChange={(e) => setFormData(prev => ({ ...prev, successMetrics: e.target.value }))}
          placeholder="How will success be measured for initiatives related to this data..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <button
        type="submit"
        className="w-full px-4 py-2 bg-sophia-600 text-white rounded-md hover:bg-sophia-700 transition-colors"
      >
        Process Strategic Content
      </button>
    </form>
  )
}

// Karen (Operational) Metadata Form
function KarenMetadataForm({ onSubmit, initialData }: { 
  onSubmit: (data: MetadataFormData) => void
  initialData?: Partial<MetadataFormData>
}) {
  const [formData, setFormData] = useState({
    processCategory: initialData?.customMetadata?.processCategory || '',
    priority: initialData?.customMetadata?.priority || '',
    timeline: initialData?.customMetadata?.timeline || '',
    dependencies: initialData?.customMetadata?.dependencies || '',
    qualityStandards: initialData?.customMetadata?.qualityStandards || '',
    riskFactors: initialData?.customMetadata?.riskFactors || ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      persona: 'karen',
      fileType: 'operational',
      processingIntent: formData.processCategory,
      customMetadata: formData,
      tags: [formData.processCategory, formData.priority, formData.timeline].filter(Boolean)
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Process Category</label>
          <select 
            value={formData.processCategory}
            onChange={(e) => setFormData(prev => ({ ...prev, processCategory: e.target.value }))}
            className="w-full p-2 border border-input rounded-md bg-background"
            required
          >
            <option value="">Select category...</option>
            <option value="sop">Standard Operating Procedures</option>
            <option value="workflow">Workflow Documentation</option>
            <option value="qa">Quality Assurance Protocols</option>
            <option value="optimization">Performance Optimization</option>
            <option value="troubleshooting">Troubleshooting Guides</option>
            <option value="training">Training Materials</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Operational Priority</label>
          <div className="space-y-1">
            {['Critical - System Essential', 'High - Performance Impact', 'Medium - Process Improvement', 'Low - Reference Material'].map(priority => (
              <label key={priority} className="flex items-center">
                <input
                  type="radio"
                  name="priority"
                  value={priority}
                  checked={formData.priority === priority}
                  onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value }))}
                  className="mr-2"
                />
                <span className="text-sm">{priority}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Implementation Timeline</label>
        <select 
          value={formData.timeline}
          onChange={(e) => setFormData(prev => ({ ...prev, timeline: e.target.value }))}
          className="w-full p-2 border border-input rounded-md bg-background"
        >
          <option value="">Select timeline...</option>
          <option value="immediate">Immediate Implementation</option>
          <option value="scheduled">Scheduled Rollout</option>
          <option value="pilot">Pilot Testing Phase</option>
          <option value="future">Future Planning</option>
          <option value="reference">Reference Only</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Dependencies</label>
        <textarea
          value={formData.dependencies}
          onChange={(e) => setFormData(prev => ({ ...prev, dependencies: e.target.value }))}
          placeholder="What systems, processes, or resources does this depend on..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Quality Standards</label>
        <textarea
          value={formData.qualityStandards}
          onChange={(e) => setFormData(prev => ({ ...prev, qualityStandards: e.target.value }))}
          placeholder="What quality metrics or standards apply to this process..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Risk Factors</label>
        <textarea
          value={formData.riskFactors}
          onChange={(e) => setFormData(prev => ({ ...prev, riskFactors: e.target.value }))}
          placeholder="What operational risks should be considered..."
          className="w-full p-2 border border-input rounded-md bg-background"
          rows={3}
        />
      </div>

      <button
        type="submit"
        className="w-full px-4 py-2 bg-karen-600 text-white rounded-md hover:bg-karen-700 transition-colors"
      >
        Process Operational Content
      </button>
    </form>
  )
}

// File Upload Card Component
function FileUploadCard({ file, onRemove, onMetadataSubmit }: {
  file: UploadFile
  onRemove: (id: string) => void
  onMetadataSubmit: (id: string, metadata: MetadataFormData) => void
}) {
  const { currentPersona } = usePersona()
  const [showMetadataForm, setShowMetadataForm] = useState(false)

  const handleMetadataSubmit = (metadata: MetadataFormData) => {
    onMetadataSubmit(file.id, metadata)
    setShowMetadataForm(false)
  }

  const getStatusIcon = () => {
    switch (file.status) {
      case 'pending':
        return <FileText className="w-4 h-4 text-muted-foreground" />
      case 'uploading':
        return <Loader2 className="w-4 h-4 animate-spin text-primary" />
      case 'processing':
        return <Loader2 className="w-4 h-4 animate-spin text-yellow-500" />
      case 'completed':
        return <Check className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <FileText className="w-4 h-4 text-muted-foreground" />
    }
  }

  return (
    <div className="border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getFileIcon(file.file.name)}</span>
          <div>
            <p className="font-medium text-sm">{file.file.name}</p>
            <p className="text-xs text-muted-foreground">{formatBytes(file.file.size)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <button
            onClick={() => onRemove(file.id)}
            className="p-1 hover:bg-destructive/10 rounded-sm text-destructive"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {file.status === 'uploading' && (
        <div className="w-full bg-muted rounded-full h-2">
          <div 
            className="bg-primary h-2 rounded-full transition-all duration-300"
            style={{ width: `${file.progress}%` }}
          />
        </div>
      )}

      {file.status === 'error' && file.error && (
        <div className="text-sm text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded">
          {file.error}
        </div>
      )}

      {file.status === 'pending' && (
        <div className="space-y-2">
          <button
            onClick={() => setShowMetadataForm(!showMetadataForm)}
            className="w-full px-3 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Configure Metadata for {currentPersona.charAt(0).toUpperCase() + currentPersona.slice(1)}
          </button>
          
          {showMetadataForm && (
            <div className="border-t border-border pt-4">
              {currentPersona === 'cherry' && (
                <CherryMetadataForm onSubmit={handleMetadataSubmit} />
              )}
              {currentPersona === 'sophia' && (
                <SophiaMetadataForm onSubmit={handleMetadataSubmit} />
              )}
              {currentPersona === 'karen' && (
                <KarenMetadataForm onSubmit={handleMetadataSubmit} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Main Data Integration Page
export function DataIntegrationPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadFile[]>([])
  const { currentPersona, personaConfig } = usePersona()
  const { connectionStatus, lastMessage, subscribe } = useWebSocket()

  useEffect(() => {
    subscribe('file_uploads')
  }, [subscribe])

  useEffect(() => {
    if (lastMessage?.type === 'upload_progress') {
      setUploadedFiles(prev => prev.map(file => 
        file.id === lastMessage.file_id 
          ? { ...file, progress: lastMessage.progress, status: lastMessage.status }
          : file
      ))
    }
  }, [lastMessage])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      id: generateId(),
      file,
      progress: 0,
      status: 'pending' as const
    }))
    
    setUploadedFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize: 2 * 1024 * 1024 * 1024, // 2GB
    multiple: true
  })

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id))
  }

  const handleMetadataSubmit = async (fileId: string, metadata: MetadataFormData) => {
    const fileIndex = uploadedFiles.findIndex(f => f.id === fileId)
    if (fileIndex === -1) return

    const file = uploadedFiles[fileIndex]
    
    // Update file with metadata and start upload
    setUploadedFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, metadata, status: 'uploading' }
        : f
    ))

    try {
      const formData = new FormData()
      formData.append('file', file.file)
      formData.append('metadata', JSON.stringify(metadata))
      formData.append('persona', metadata.persona)

      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      await response.json()
      
      setUploadedFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { ...f, status: 'processing' }
          : f
      ))
      
    } catch (error) {
      setUploadedFiles(prev => prev.map(f => 
        f.id === fileId 
          ? { ...f, status: 'error', error: 'Upload failed' }
          : f
      ))
    }
  }

  const currentPersonaConfig = personaConfig[currentPersona]

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="border-b border-border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Data Integration Hub</h1>
            <p className="text-muted-foreground">
              Upload and process files for AI persona consumption
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className={cn(
              'w-2 h-2 rounded-full',
              connectionStatus === 'Connected' ? 'bg-green-500' : 'bg-red-500'
            )} />
            <span className="text-sm text-muted-foreground">
              {connectionStatus}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto">
          {/* Current Persona Info */}
          <div className="mb-8 p-4 rounded-lg border border-border bg-card">
            <div className="flex items-center gap-3 mb-2">
              <div className={cn(
                'w-3 h-3 rounded-full',
                `bg-${currentPersonaConfig.color}-500`
              )} />
              <h2 className="font-semibold">{currentPersonaConfig.name} - Data Processing</h2>
            </div>
            <p className="text-sm text-muted-foreground">{currentPersonaConfig.description}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {currentPersonaConfig.specialties.map(specialty => (
                <span key={specialty} className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-full">
                  {specialty}
                </span>
              ))}
            </div>
          </div>

          {/* File Upload Zone */}
          <div 
            {...getRootProps()} 
            className={cn(
              'upload-zone',
              isDragActive && 'drag-active'
            )}
          >
            <input {...getInputProps()} />
            <Upload className="w-12 h-12 text-primary mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {isDragActive ? 'Drop files here' : 'Drop files here or click to browse'}
            </h3>
            <p className="text-muted-foreground text-center">
              Supports all file types up to 2GB<br />
              PDF, DOCX, TXT, Images, Videos, Archives, and more
            </p>
          </div>

          {/* Uploaded Files */}
          {uploadedFiles.length > 0 && (
            <div className="mt-8 space-y-4">
              <h3 className="text-lg font-semibold">Uploaded Files ({uploadedFiles.length})</h3>
              <div className="space-y-3">
                {uploadedFiles.map(file => (
                  <FileUploadCard
                    key={file.id}
                    file={file}
                    onRemove={removeFile}
                    onMetadataSubmit={handleMetadataSubmit}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
} 