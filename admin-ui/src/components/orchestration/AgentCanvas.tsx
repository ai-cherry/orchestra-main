import React, { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  Panel,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import useWorkflowStore from '@/store/workflowStore';
import { AgentNode } from './nodes/AgentNode';
import { WorkflowNode } from './nodes/WorkflowNode';
import { DataNode } from './nodes/DataNode';
import { Plus, Save, Play, Square, Trash2 } from 'lucide-react';

const nodeTypes = {
  agentNode: AgentNode,
  workflowNode: WorkflowNode,
  dataNode: DataNode,
};

const AgentCanvas: React.FC = () => {
  const { project } = useReactFlow();
  const {
    nodes,
    edges,
    selectedNodeId,
    isExecuting,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    deleteNode,
    startExecution,
    stopExecution,
    saveWorkflow,
    clearWorkflow,
  } = useWorkflowStore();

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = project({
        x: event.clientX,
        y: event.clientY,
      });

      addNode(type, position);
    },
    [project, addNode]
  );

  const handleSave = () => {
    const name = prompt('Enter workflow name:');
    if (name) {
      saveWorkflow(name);
    }
  };

  const handleDelete = () => {
    if (selectedNodeId && confirm('Delete selected node?')) {
      deleteNode(selectedNodeId);
    }
  };

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        fitView
        className="bg-gray-50 dark:bg-gray-900"
      >
        <Panel position="top-left" className="flex gap-2">
          <button
            onClick={handleSave}
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
            title="Save Workflow"
          >
            <Save className="h-5 w-5 text-gray-700 dark:text-gray-300" />
          </button>
          
          <button
            onClick={() => isExecuting ? stopExecution() : startExecution()}
            className={`p-2 rounded-lg shadow-md hover:shadow-lg transition-all ${
              isExecuting 
                ? 'bg-red-500 hover:bg-red-600' 
                : 'bg-green-500 hover:bg-green-600'
            }`}
            title={isExecuting ? 'Stop Execution' : 'Start Execution'}
          >
            {isExecuting ? (
              <Square className="h-5 w-5 text-white" />
            ) : (
              <Play className="h-5 w-5 text-white" />
            )}
          </button>

          <button
            onClick={handleDelete}
            disabled={!selectedNodeId}
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete Selected"
          >
            <Trash2 className="h-5 w-5 text-red-600 dark:text-red-400" />
          </button>

          <button
            onClick={clearWorkflow}
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-lg transition-shadow"
            title="Clear Canvas"
          >
            <Plus className="h-5 w-5 text-gray-700 dark:text-gray-300 rotate-45" />
          </button>
        </Panel>

        <Panel position="top-right" className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-3">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">Drag to Canvas</h3>
          <div className="space-y-2">
            <div
              draggable
              onDragStart={(e) => e.dataTransfer.setData('application/reactflow', 'agent')}
              className="px-3 py-2 bg-blue-100 dark:bg-blue-900/30 rounded cursor-move hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
            >
              <span className="text-sm text-blue-700 dark:text-blue-300">+ Agent Node</span>
            </div>
            <div
              draggable
              onDragStart={(e) => e.dataTransfer.setData('application/reactflow', 'workflow')}
              className="px-3 py-2 bg-purple-100 dark:bg-purple-900/30 rounded cursor-move hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
            >
              <span className="text-sm text-purple-700 dark:text-purple-300">+ Workflow Node</span>
            </div>
            <div
              draggable
              onDragStart={(e) => e.dataTransfer.setData('application/reactflow', 'data')}
              className="px-3 py-2 bg-green-100 dark:bg-green-900/30 rounded cursor-move hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
            >
              <span className="text-sm text-green-700 dark:text-green-300">+ Data Node</span>
            </div>
          </div>
        </Panel>

        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
        <MiniMap 
          nodeStrokeColor={(node) => {
            if (node.type === 'agentNode') return '#3b82f6';
            if (node.type === 'workflowNode') return '#8b5cf6';
            if (node.type === 'dataNode') return '#10b981';
            return '#6b7280';
          }}
          nodeColor={(node) => {
            if (node.type === 'agentNode') return '#dbeafe';
            if (node.type === 'workflowNode') return '#e9d5ff';
            if (node.type === 'dataNode') return '#d1fae5';
            return '#f3f4f6';
          }}
          className="!bg-gray-100 dark:!bg-gray-800"
        />
      </ReactFlow>
    </div>
  );
};

export default AgentCanvas; 