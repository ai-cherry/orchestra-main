import { create } from 'zustand';
import { Node, Edge, addEdge, applyNodeChanges, applyEdgeChanges, NodeChange, EdgeChange } from '@xyflow/react';
import { v4 as uuidv4 } from 'uuid';

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  isExecuting: boolean;
  executionResults: Record<string, any>;
  
  // Node operations
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (params: any) => void;
  addNode: (type: string, position: { x: number; y: number }, data?: any) => void;
  updateNode: (nodeId: string, data: any) => void;
  deleteNode: (nodeId: string) => void;
  
  // Selection
  setSelectedNode: (nodeId: string | null) => void;
  
  // Execution
  startExecution: () => void;
  stopExecution: () => void;
  updateExecutionResult: (nodeId: string, result: any) => void;
  
  // Workflow operations
  saveWorkflow: (name: string) => void;
  loadWorkflow: (workflowId: string) => void;
  clearWorkflow: () => void;
}

const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [
    {
      id: '1',
      type: 'agentNode',
      position: { x: 100, y: 100 },
      data: { 
        name: 'Data Collector', 
        type: 'collector',
        description: 'Gathers data from various sources',
        status: 'inactive' 
      },
    },
    {
      id: '2',
      type: 'workflowNode',
      position: { x: 400, y: 100 },
      data: { 
        name: 'Process Workflow', 
        steps: 5,
        trigger: 'On Data Ready',
        lastRun: '2 hours ago'
      },
    },
    {
      id: '3',
      type: 'dataNode',
      position: { x: 250, y: 250 },
      data: { 
        name: 'Customer Database', 
        dataType: 'database',
        size: '15.3 GB',
        format: 'PostgreSQL'
      },
    },
  ],
  edges: [
    { id: 'e1-2', source: '1', target: '2', animated: true },
    { id: 'e3-2', source: '3', target: '2' },
  ],
  selectedNodeId: null,
  isExecuting: false,
  executionResults: {},

  onNodesChange: (changes) => set((state) => ({
    nodes: applyNodeChanges(changes, state.nodes),
  })),

  onEdgesChange: (changes) => set((state) => ({
    edges: applyEdgeChanges(changes, state.edges),
  })),

  onConnect: (params) => set((state) => ({
    edges: addEdge({ ...params, animated: true }, state.edges),
  })),

  addNode: (type, position, data = {}) => {
    const id = uuidv4();
    const nodeTypeMap: Record<string, string> = {
      agent: 'agentNode',
      workflow: 'workflowNode',
      data: 'dataNode',
    };
    
    const newNode: Node = {
      id,
      type: nodeTypeMap[type] || 'agentNode',
      position,
      data: {
        name: `New ${type}`,
        ...data,
      },
    };
    
    set((state) => ({
      nodes: [...state.nodes, newNode],
    }));
  },

  updateNode: (nodeId, data) => set((state) => ({
    nodes: state.nodes.map((node) =>
      node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
    ),
  })),

  deleteNode: (nodeId) => set((state) => ({
    nodes: state.nodes.filter((node) => node.id !== nodeId),
    edges: state.edges.filter((edge) => edge.source !== nodeId && edge.target !== nodeId),
  })),

  setSelectedNode: (nodeId) => set({ selectedNodeId: nodeId }),

  startExecution: () => {
    set({ isExecuting: true, executionResults: {} });
    // Simulate execution
    const { nodes } = get();
    nodes.forEach((node, index) => {
      setTimeout(() => {
        get().updateExecutionResult(node.id, {
          status: 'completed',
          output: `Processed by ${node.data.name}`,
          timestamp: new Date().toISOString(),
        });
      }, (index + 1) * 1000);
    });
    
    setTimeout(() => {
      set({ isExecuting: false });
    }, nodes.length * 1000 + 500);
  },

  stopExecution: () => set({ isExecuting: false }),

  updateExecutionResult: (nodeId, result) => set((state) => ({
    executionResults: {
      ...state.executionResults,
      [nodeId]: result,
    },
  })),

  saveWorkflow: (name) => {
    const { nodes, edges } = get();
    const workflow = {
      id: uuidv4(),
      name,
      nodes,
      edges,
      createdAt: new Date().toISOString(),
    };
    // In a real app, this would save to backend
    localStorage.setItem(`workflow-${workflow.id}`, JSON.stringify(workflow));
    console.log('Workflow saved:', workflow);
  },

  loadWorkflow: (workflowId) => {
    // In a real app, this would load from backend
    const saved = localStorage.getItem(`workflow-${workflowId}`);
    if (saved) {
      const workflow = JSON.parse(saved);
      set({ nodes: workflow.nodes, edges: workflow.edges });
    }
  },

  clearWorkflow: () => set({ nodes: [], edges: [], selectedNodeId: null, executionResults: {} }),
}));

export default useWorkflowStore; 