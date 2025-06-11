import { useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { 
  Play, 
  Pause, 
  Square, 
  Save, 
  Download, 
  Upload, 
  Plus,
  Settings,
  Zap,
  MessageSquare,
  Database,
  Globe,
  Brain,
  Image,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react'

// Custom node types for the workflow builder
const nodeTypes = {
  trigger: {
    label: 'Trigger',
    icon: Zap,
    color: 'bg-yellow-500',
    description: 'Start workflow execution'
  },
  persona: {
    label: 'Persona Action',
    icon: MessageSquare,
    color: 'bg-blue-500',
    description: 'Execute persona-specific action'
  },
  search: {
    label: 'Search',
    icon: Database,
    color: 'bg-green-500',
    description: 'Search internal or external data'
  },
  web: {
    label: 'Web Action',
    icon: Globe,
    color: 'bg-cyan-500',
    description: 'Perform web-based action'
  },
  ai: {
    label: 'AI Processing',
    icon: Brain,
    color: 'bg-purple-500',
    description: 'AI analysis or generation'
  },
  generate: {
    label: 'Generate Content',
    icon: Image,
    color: 'bg-pink-500',
    description: 'Create images, audio, or text'
  },
  condition: {
    label: 'Condition',
    icon: FileText,
    color: 'bg-orange-500',
    description: 'Conditional logic branch'
  },
  delay: {
    label: 'Delay',
    icon: Clock,
    color: 'bg-gray-500',
    description: 'Wait for specified time'
  }
}

// Custom node component
function CustomNode({ data, selected }) {
  const nodeConfig = nodeTypes[data.type] || nodeTypes.trigger
  const Icon = nodeConfig.icon

  return (
    <div className={`
      px-4 py-3 shadow-lg rounded-lg border-2 bg-white min-w-[150px]
      ${selected ? 'border-blue-500' : 'border-gray-200'}
      hover:shadow-xl transition-shadow
    `}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-1 rounded ${nodeConfig.color} text-white`}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="font-medium text-sm">{data.label}</span>
      </div>
      {data.description && (
        <p className="text-xs text-gray-600">{data.description}</p>
      )}
      {data.status && (
        <div className="mt-2">
          <Badge 
            variant="outline" 
            className={`text-xs ${
              data.status === 'completed' ? 'text-green-600' :
              data.status === 'running' ? 'text-blue-600' :
              data.status === 'error' ? 'text-red-600' :
              'text-gray-600'
            }`}
          >
            {data.status}
          </Badge>
        </div>
      )}
    </div>
  )
}

// Node palette for dragging new nodes
function NodePalette({ onAddNode }) {
  return (
    <Card className="w-64">
      <CardHeader>
        <CardTitle className="text-sm">Workflow Nodes</CardTitle>
        <CardDescription>Drag to add to workflow</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {Object.entries(nodeTypes).map(([type, config]) => {
            const Icon = config.icon
            return (
              <Button
                key={type}
                variant="outline"
                size="sm"
                onClick={() => onAddNode(type)}
                className="w-full justify-start gap-2 h-auto p-2"
              >
                <div className={`p-1 rounded ${config.color} text-white`}>
                  <Icon className="h-3 w-3" />
                </div>
                <div className="text-left">
                  <div className="text-xs font-medium">{config.label}</div>
                  <div className="text-xs text-muted-foreground">{config.description}</div>
                </div>
              </Button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

// Workflow execution panel
function ExecutionPanel({ workflow, onExecute, onStop, isRunning }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'running': return <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Execution Control</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button 
            size="sm" 
            onClick={onExecute}
            disabled={isRunning}
            className="flex-1"
          >
            <Play className="h-4 w-4 mr-2" />
            {isRunning ? 'Running...' : 'Execute'}
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            onClick={onStop}
            disabled={!isRunning}
          >
            <Square className="h-4 w-4" />
          </Button>
        </div>

        {workflow.executionHistory && workflow.executionHistory.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-medium">Execution History</h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {workflow.executionHistory.slice(-5).map((execution, index) => (
                <div key={index} className="flex items-center gap-2 text-xs">
                  {getStatusIcon(execution.status)}
                  <span className="flex-1">{execution.step}</span>
                  <span className="text-muted-foreground">
                    {new Date(execution.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

// Workflow list component
function WorkflowList({ workflows, onWorkflowSelect, onCreateNew }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Workflows</h1>
          <p className="text-muted-foreground">
            Visual workflow builder and automation
          </p>
        </div>
        <Button onClick={onCreateNew}>
          <Plus className="h-4 w-4 mr-2" />
          New Workflow
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workflows.map((workflow) => (
          <Card key={workflow.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{workflow.name}</CardTitle>
                <Badge variant="outline" className="capitalize">
                  {workflow.status}
                </Badge>
              </div>
              <CardDescription>{workflow.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Nodes: {workflow.nodeCount}</span>
                  <span>Last run: {workflow.lastRun ? new Date(workflow.lastRun).toLocaleDateString() : 'Never'}</span>
                </div>
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    onClick={() => onWorkflowSelect(workflow.id)}
                    className="flex-1"
                  >
                    Edit
                  </Button>
                  <Button size="sm" variant="outline">
                    <Play className="h-4 w-4" />
                  </Button>
                  <Button size="sm" variant="outline">
                    <Settings className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

// Main workflow builder component
function WorkflowBuilderCanvas() {
  const { workflowId } = useParams()
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isRunning, setIsRunning] = useState(false)
  const [selectedNode, setSelectedNode] = useState(null)
  const [workflowName, setWorkflowName] = useState('Untitled Workflow')

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const onAddNode = useCallback((type) => {
    const newNode = {
      id: `${type}-${Date.now()}`,
      type: 'default',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        type,
        label: nodeTypes[type].label,
        description: `New ${nodeTypes[type].label}`,
        status: 'idle'
      }
    }
    setNodes((nds) => nds.concat(newNode))
  }, [setNodes])

  const onExecuteWorkflow = useCallback(() => {
    setIsRunning(true)
    
    // Simulate workflow execution
    const executeNode = (nodeIndex) => {
      if (nodeIndex >= nodes.length) {
        setIsRunning(false)
        return
      }

      const node = nodes[nodeIndex]
      setNodes((nds) => 
        nds.map((n) => 
          n.id === node.id 
            ? { ...n, data: { ...n.data, status: 'running' } }
            : n
        )
      )

      setTimeout(() => {
        setNodes((nds) => 
          nds.map((n) => 
            n.id === node.id 
              ? { ...n, data: { ...n.data, status: 'completed' } }
              : n
          )
        )
        executeNode(nodeIndex + 1)
      }, 1000)
    }

    executeNode(0)
  }, [nodes, setNodes])

  const onStopWorkflow = useCallback(() => {
    setIsRunning(false)
    setNodes((nds) => 
      nds.map((n) => ({ 
        ...n, 
        data: { ...n.data, status: 'idle' } 
      }))
    )
  }, [setNodes])

  const onSaveWorkflow = useCallback(() => {
    const workflowData = {
      name: workflowName,
      nodes,
      edges,
      lastSaved: new Date().toISOString()
    }
    console.log('Saving workflow:', workflowData)
    // Here you would save to backend
  }, [workflowName, nodes, edges])

  return (
    <div className="h-full flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Input
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="text-lg font-semibold border-none p-0 h-auto bg-transparent"
          />
          <Badge variant="outline">
            {nodes.length} nodes, {edges.length} connections
          </Badge>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={onSaveWorkflow}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
          <Button size="sm" variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button size="sm" variant="outline">
            <Upload className="h-4 w-4 mr-2" />
            Import
          </Button>
        </div>
      </div>

      {/* Main workflow area */}
      <div className="flex-1 flex gap-4">
        {/* Node palette */}
        <NodePalette onAddNode={onAddNode} />

        {/* Flow canvas */}
        <div className="flex-1 border rounded-lg bg-gray-50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={{ default: CustomNode }}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />
            <Panel position="top-right">
              <ExecutionPanel
                workflow={{ executionHistory: [] }}
                onExecute={onExecuteWorkflow}
                onStop={onStopWorkflow}
                isRunning={isRunning}
              />
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}

export function WorkflowBuilder() {
  const { workflowId } = useParams()
  const [workflows] = useState([
    {
      id: '1',
      name: 'Cherry Daily Check-in',
      description: 'Automated daily personality and mood assessment',
      status: 'active',
      nodeCount: 8,
      lastRun: new Date().toISOString()
    },
    {
      id: '2',
      name: 'Sophia Market Analysis',
      description: 'Weekly market research and report generation',
      status: 'draft',
      nodeCount: 12,
      lastRun: null
    },
    {
      id: '3',
      name: 'Karen Patient Follow-up',
      description: 'Automated patient care coordination workflow',
      status: 'active',
      nodeCount: 15,
      lastRun: new Date(Date.now() - 86400000).toISOString()
    }
  ])

  const handleWorkflowSelect = (id) => {
    // Navigate to workflow builder with ID
    window.history.pushState({}, '', `/workflows/${id}`)
  }

  const handleCreateNew = () => {
    // Navigate to new workflow builder
    window.history.pushState({}, '', '/workflows/new')
  }

  if (workflowId) {
    return <WorkflowBuilderCanvas />
  }

  return (
    <WorkflowList
      workflows={workflows}
      onWorkflowSelect={handleWorkflowSelect}
      onCreateNew={handleCreateNew}
    />
  )
}

