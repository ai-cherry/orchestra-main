# Frontend-Notion Integration Guide

## 🌐 **Overview**

This guide covers the complete integration between the Orchestra AI React frontend (`admin-interface`) and Notion databases, including direct API interactions, component patterns, and data flow management.

## 📦 **Technical Stack**

### **Core Dependencies**
```json
{
  "@notionhq/client": "^2.3.0",     // Direct Notion API client
  "axios": "^1.9.0",                // HTTP client for backend API
  "react": "^19.1.0",               // React framework
  "zustand": "^5.0.5"               // State management
}
```

### **Architecture Pattern**
```
React Frontend → Dual Integration → Data Sources
    ↓                ↓                    ↓
Component Layer     API Layer        Notion Databases
    ↓                ↓                    ↓
- Dashboard UI    - Direct Client     - Task Management
- Data Display    - Backend Proxy     - Development Log  
- User Actions    - Cache Layer       - AI Tool Metrics
```

## 🔧 **Notion Client Configuration**

### **Environment Setup**
```typescript
// config/notion.ts
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.VITE_NOTION_API_TOKEN,
  notionVersion: '2022-06-28',
});

export default notion;
```

### **Environment Variables**
```bash
# .env.local
VITE_NOTION_API_TOKEN=your_notion_integration_token
VITE_NOTION_WORKSPACE_ID=your_workspace_id
VITE_API_BASE_URL=http://localhost:8000
```

## 🎯 **Core Integration Patterns**

### **1. Direct Notion API Pattern**
```typescript
// hooks/useNotionDirect.ts
import { useState, useEffect } from 'react';
import notion from '../config/notion';

export const useNotionDirect = (databaseId: string) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await notion.databases.query({
          database_id: databaseId,
        });
        setData(response.results);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [databaseId]);

  return { data, loading, error };
};
```

### **2. Backend Proxy Pattern**
```typescript
// services/notionApi.ts
import axios from 'axios';

const API_BASE = process.env.VITE_API_BASE_URL;

export const notionApi = {
  // Get tasks with caching
  getTasks: async (filters = {}) => {
    const response = await axios.get(`${API_BASE}/notion/tasks`, {
      params: filters
    });
    return response.data;
  },

  // Create new task
  createTask: async (taskData) => {
    const response = await axios.post(`${API_BASE}/notion/tasks`, taskData);
    return response.data;
  },

  // Get development metrics
  getMetrics: async (timeRange = '7d') => {
    const response = await axios.get(`${API_BASE}/notion/metrics`, {
      params: { range: timeRange }
    });
    return response.data;
  }
};
```

### **3. Hybrid Approach with Caching**
```typescript
// hooks/useNotionWithCache.ts
import { create } from 'zustand';
import { notionApi } from '../services/notionApi';

interface NotionStore {
  tasks: any[];
  metrics: any[];
  loading: boolean;
  fetchTasks: () => Promise<void>;
  fetchMetrics: () => Promise<void>;
}

export const useNotionStore = create<NotionStore>((set, get) => ({
  tasks: [],
  metrics: [],
  loading: false,

  fetchTasks: async () => {
    set({ loading: true });
    try {
      const tasks = await notionApi.getTasks();
      set({ tasks });
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      set({ loading: false });
    }
  },

  fetchMetrics: async () => {
    const metrics = await notionApi.getMetrics();
    set({ metrics });
  }
}));
```

## 🧩 **Component Patterns**

### **1. Dashboard Overview Component**
```typescript
// components/dashboard/ProjectOverview.tsx
import React, { useEffect } from 'react';
import { useNotionStore } from '../../hooks/useNotionWithCache';

export const ProjectOverview: React.FC = () => {
  const { tasks, metrics, loading, fetchTasks, fetchMetrics } = useNotionStore();

  useEffect(() => {
    fetchTasks();
    fetchMetrics();
  }, []);

  if (loading) {
    return <div className="animate-pulse">Loading project overview...</div>;
  }

  const activeTasks = tasks.filter(task => 
    task.properties.Status.select.name !== 'Done'
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard 
          title="Active Tasks" 
          value={activeTasks.length}
          trend="stable"
        />
        <MetricCard 
          title="Development Velocity" 
          value={metrics.velocity || 0}
          trend="up"
        />
        <MetricCard 
          title="AI Tool Performance" 
          value={`${metrics.aiPerformance || 0}%`}
          trend="up"
        />
      </div>
      
      <TaskList tasks={activeTasks} />
      <RecentActivity activities={metrics.recentActivity || []} />
    </div>
  );
};
```

### **2. Real-time Task Management**
```typescript
// components/tasks/TaskManager.tsx
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { notionApi } from '../../services/notionApi';

export const TaskManager: React.FC = () => {
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'Medium',
    assignee: 'Human Developer'
  });

  const queryClient = useQueryClient();

  const createTaskMutation = useMutation({
    mutationFn: notionApi.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks']);
      setNewTask({ title: '', description: '', priority: 'Medium', assignee: 'Human Developer' });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createTaskMutation.mutate(newTask);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="text"
          placeholder="Task title"
          value={newTask.title}
          onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
        
        <textarea
          placeholder="Task description"
          value={newTask.description}
          onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
          className="w-full p-2 border rounded"
          rows={3}
        />
        
        <div className="flex gap-2">
          <select
            value={newTask.priority}
            onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
            className="p-2 border rounded"
          >
            <option value="Low">Low Priority</option>
            <option value="Medium">Medium Priority</option>
            <option value="High">High Priority</option>
            <option value="Critical">Critical Priority</option>
          </select>
          
          <select
            value={newTask.assignee}
            onChange={(e) => setNewTask({ ...newTask, assignee: e.target.value })}
            className="p-2 border rounded"
          >
            <option value="Human Developer">Human Developer</option>
            <option value="Cursor AI">Cursor AI</option>
            <option value=" AI"> AI</option>
            <option value="Continue AI">Continue AI</option>
          </select>
        </div>
        
        <button
          type="submit"
          disabled={createTaskMutation.isPending}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {createTaskMutation.isPending ? 'Creating...' : 'Create Task'}
        </button>
      </form>
    </div>
  );
};
```

### **3. AI Tools Performance Monitor**
```typescript
// components/ai/ToolsPerformanceMonitor.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { notionApi } from '../../services/notionApi';

export const ToolsPerformanceMonitor: React.FC = () => {
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['ai-metrics'],
    queryFn: () => notionApi.getMetrics('1d'),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) return <div>Loading performance metrics...</div>;

  const toolMetrics = metrics?.aiTools || [];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">AI Tools Performance</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {toolMetrics.map((tool) => (
          <div key={tool.name} className="p-4 border rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">{tool.name}</h4>
              <StatusIndicator status={tool.status} />
            </div>
            
            <div className="space-y-1 text-sm text-gray-600">
              <div>Response Time: {tool.responseTime}ms</div>
              <div>Success Rate: {tool.successRate}%</div>
              <div>Last Active: {tool.lastActive}</div>
            </div>
            
            <div className="mt-3">
              <PerformanceChart data={tool.history} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 📊 **Data Flow Management**

### **1. State Management with Zustand**
```typescript
// stores/notionStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface NotionState {
  // Data
  tasks: NotionTask[];
  epics: NotionEpic[];
  metrics: NotionMetrics;
  
  // UI State
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchTasks: () => Promise<void>;
  createTask: (task: CreateTaskData) => Promise<void>;
  updateTask: (id: string, updates: Partial<NotionTask>) => Promise<void>;
  
  // Real-time updates
  subscribeToUpdates: () => void;
  unsubscribeFromUpdates: () => void;
}

export const useNotionStore = create<NotionState>()(
  devtools(
    (set, get) => ({
      tasks: [],
      epics: [],
      metrics: {},
      loading: false,
      error: null,

      fetchTasks: async () => {
        set({ loading: true, error: null });
        try {
          const tasks = await notionApi.getTasks();
          set({ tasks });
        } catch (error) {
          set({ error: error.message });
        } finally {
          set({ loading: false });
        }
      },

      createTask: async (taskData) => {
        const newTask = await notionApi.createTask(taskData);
        set(state => ({ 
          tasks: [...state.tasks, newTask] 
        }));
      },

      updateTask: async (id, updates) => {
        const updatedTask = await notionApi.updateTask(id, updates);
        set(state => ({
          tasks: state.tasks.map(task => 
            task.id === id ? { ...task, ...updatedTask } : task
          )
        }));
      },

      subscribeToUpdates: () => {
        // WebSocket or polling implementation
        const interval = setInterval(() => {
          get().fetchTasks();
        }, 60000); // Refresh every minute
        
        // Store interval ID for cleanup
        set({ updateInterval: interval });
      },

      unsubscribeFromUpdates: () => {
        const { updateInterval } = get();
        if (updateInterval) {
          clearInterval(updateInterval);
        }
      }
    }),
    { name: 'notion-store' }
  )
);
```

### **2. Query Management with React Query**
```typescript
// hooks/useNotionQueries.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notionApi } from '../services/notionApi';

export const useNotionQueries = () => {
  const queryClient = useQueryClient();

  // Queries
  const tasksQuery = useQuery({
    queryKey: ['notion', 'tasks'],
    queryFn: notionApi.getTasks,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const metricsQuery = useQuery({
    queryKey: ['notion', 'metrics'],
    queryFn: () => notionApi.getMetrics('7d'),
    refetchInterval: 1000 * 60, // 1 minute
  });

  // Mutations
  const createTaskMutation = useMutation({
    mutationFn: notionApi.createTask,
    onSuccess: () => {
      queryClient.invalidateQueries(['notion', 'tasks']);
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      notionApi.updateTask(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries(['notion', 'tasks']);
    },
  });

  return {
    tasks: tasksQuery.data || [],
    metrics: metricsQuery.data || {},
    isLoading: tasksQuery.isLoading || metricsQuery.isLoading,
    createTask: createTaskMutation.mutate,
    updateTask: updateTaskMutation.mutate,
  };
};
```

## 🔄 **Real-time Updates**

### **1. WebSocket Integration**
```typescript
// hooks/useNotionRealtime.ts
import { useEffect } from 'react';
import { useNotionStore } from '../stores/notionStore';

export const useNotionRealtime = () => {
  const { subscribeToUpdates, unsubscribeFromUpdates } = useNotionStore();

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket(`${process.env.VITE_WS_URL}/notion-updates`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      
      switch (update.type) {
        case 'TASK_UPDATED':
          useNotionStore.getState().fetchTasks();
          break;
        case 'METRICS_UPDATED':
          useNotionStore.getState().fetchMetrics();
          break;
      }
    };

    subscribeToUpdates();

    return () => {
      ws.close();
      unsubscribeFromUpdates();
    };
  }, []);
};
```

### **2. Optimistic Updates**
```typescript
// hooks/useOptimisticUpdates.ts
export const useOptimisticTaskUpdate = () => {
  const queryClient = useQueryClient();

  const updateTaskOptimistic = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      notionApi.updateTask(id, updates),
    
    onMutate: async ({ id, updates }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries(['notion', 'tasks']);
      
      // Snapshot previous value
      const previousTasks = queryClient.getQueryData(['notion', 'tasks']);
      
      // Optimistically update
      queryClient.setQueryData(['notion', 'tasks'], (old: any[]) =>
        old.map(task => task.id === id ? { ...task, ...updates } : task)
      );
      
      return { previousTasks };
    },
    
    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['notion', 'tasks'], context.previousTasks);
    },
    
    onSettled: () => {
      queryClient.invalidateQueries(['notion', 'tasks']);
    },
  });

  return updateTaskOptimistic;
};
```

## 🎨 **UI Component Patterns**

### **1. Notion-Aware Table Component**
```typescript
// components/common/NotionTable.tsx
import React from 'react';

interface NotionTableProps {
  data: NotionRecord[];
  schema: NotionSchema;
  onRowClick?: (record: NotionRecord) => void;
  onUpdate?: (id: string, updates: any) => void;
}

export const NotionTable: React.FC<NotionTableProps> = ({
  data,
  schema,
  onRowClick,
  onUpdate
}) => {
  const renderCell = (record: NotionRecord, property: string) => {
    const value = record.properties[property];
    
    switch (schema[property].type) {
      case 'title':
        return value?.title?.[0]?.text?.content || '';
      case 'select':
        return (
          <span className={`px-2 py-1 rounded text-xs ${getSelectStyles(value?.select?.name)}`}>
            {value?.select?.name || 'None'}
          </span>
        );
      case 'date':
        return value?.date?.start ? new Date(value.date.start).toLocaleDateString() : '';
      case 'number':
        return value?.number || 0;
      default:
        return '';
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {Object.keys(schema).map(property => (
              <th key={property} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {property}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map(record => (
            <tr 
              key={record.id} 
              onClick={() => onRowClick?.(record)}
              className="hover:bg-gray-50 cursor-pointer"
            >
              {Object.keys(schema).map(property => (
                <td key={property} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {renderCell(record, property)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### **2. Notion Property Editor**
```typescript
// components/common/NotionPropertyEditor.tsx
import React from 'react';

interface NotionPropertyEditorProps {
  property: string;
  value: any;
  schema: PropertySchema;
  onChange: (value: any) => void;
}

export const NotionPropertyEditor: React.FC<NotionPropertyEditorProps> = ({
  property,
  value,
  schema,
  onChange
}) => {
  const renderEditor = () => {
    switch (schema.type) {
      case 'title':
      case 'rich_text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full p-2 border rounded"
          />
        );
        
      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="">Select...</option>
            {schema.options.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
        
      case 'date':
        return (
          <input
            type="date"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className="w-full p-2 border rounded"
          />
        );
        
      case 'number':
        return (
          <input
            type="number"
            value={value || 0}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-full p-2 border rounded"
          />
        );
        
      default:
        return <div>Unsupported property type</div>;
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        {property}
        {schema.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {renderEditor()}
    </div>
  );
};
```

## 🔒 **Security & Best Practices**

### **1. API Key Management**
```typescript
// utils/security.ts
export const validateNotionToken = (token: string): boolean => {
  return token.startsWith('secret_') && token.length > 20;
};

export const sanitizeNotionData = (data: any): any => {
  // Remove sensitive fields before storing in frontend state
  const { internal_data, ...sanitized } = data;
  return sanitized;
};
```

### **2. Error Handling**
```typescript
// hooks/useNotionErrorHandler.ts
export const useNotionErrorHandler = () => {
  const handleError = (error: any) => {
    if (error.status === 401) {
      // Handle authentication error
      console.error('Notion API authentication failed');
      // Redirect to setup or show error message
    } else if (error.status === 429) {
      // Handle rate limiting
      console.warn('Notion API rate limit exceeded');
      // Implement exponential backoff
    } else if (error.status === 404) {
      // Handle not found
      console.error('Notion resource not found');
    } else {
      // Generic error handling
      console.error('Notion API error:', error);
    }
  };

  return { handleError };
};
```

## 📈 **Performance Optimization**

### **1. Caching Strategy**
```typescript
// utils/notionCache.ts
class NotionCache {
  private cache = new Map();
  private ttl = 5 * 60 * 1000; // 5 minutes

  set(key: string, data: any) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  get(key: string) {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() - item.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear() {
    this.cache.clear();
  }
}

export const notionCache = new NotionCache();
```

### **2. Pagination & Virtual Scrolling**
```typescript
// hooks/useNotionPagination.ts
export const useNotionPagination = (databaseId: string, pageSize = 50) => {
  const [cursor, setCursor] = useState<string | undefined>();
  const [allData, setAllData] = useState<any[]>([]);

  const fetchPage = async (startCursor?: string) => {
    const response = await notion.databases.query({
      database_id: databaseId,
      page_size: pageSize,
      start_cursor: startCursor,
    });

    if (startCursor) {
      setAllData(prev => [...prev, ...response.results]);
    } else {
      setAllData(response.results);
    }

    if (response.has_more) {
      setCursor(response.next_cursor);
    } else {
      setCursor(undefined);
    }
  };

  const loadMore = () => {
    if (cursor) {
      fetchPage(cursor);
    }
  };

  return { data: allData, hasMore: !!cursor, loadMore, refresh: () => fetchPage() };
};
```

## 🚀 **Deployment Considerations**

### **1. Environment-Specific Configuration**
```typescript
// config/environments.ts
const environments = {
  development: {
    notionApiUrl: 'https://api.notion.com/v1',
    rateLimitMs: 1000, // More lenient for development
    debugMode: true,
  },
  production: {
    notionApiUrl: 'https://api.notion.com/v1',
    rateLimitMs: 334, // Respect 3 requests per second limit
    debugMode: false,
  },
};

export const getConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return environments[env];
};
```

### **2. Build-Time Optimization**
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      external: ['@notionhq/client'], // Bundle splitting for larger libraries
    },
  },
  define: {
    __NOTION_API_VERSION__: JSON.stringify('2022-06-28'),
  },
});
```

---

**Last Updated**: 2025-01-24  
**Version**: 2.0  
**Contact**: Orchestra AI Development Team 