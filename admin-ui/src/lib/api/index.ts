import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'

// Use environment variables for API URL and API key
const API_URL = import.meta.env.VITE_API_URL || window.location.origin;
const API_KEY = import.meta.env.VITE_API_KEY;
const DEFAULT_API_KEY = '4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd';

// Define the QueryBody interface with a query string property
export interface QueryBody {
  query: string
}

function getHeaders() {
  // Get token from auth store (which is the API key after login)
  const { token } = useAuthStore.getState();

  return {
    'Content-Type': 'application/json',
    'X-API-Key': token || API_KEY || DEFAULT_API_KEY,
  };
}

export function useQueryApi(body: QueryBody) {
  return useQuery({
    queryKey: ['query', body],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
  });
}

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/agents`, {
        headers: getHeaders(),
      });
      if (!res.ok) {
        throw new Error('Failed to fetch agents');
      }
      return res.json();
    },
    initialData: [],
  });
}

export function useUpload() {
  return useQuery({
    queryKey: ['upload'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/upload`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
  });
}

export function usePersonas() {
  return useQuery({
    queryKey: ['personas'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/personas`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch personas');
      return res.json();
    },
    initialData: [],
  });
}

export function useWorkflows() {
  return useQuery({
    queryKey: ['workflows'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/workflows`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch workflows');
      return res.json();
    },
    initialData: [],
  });
}

export function useIntegrations() {
  return useQuery({
    queryKey: ['integrations'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/integrations`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch integrations');
      return res.json();
    },
    initialData: [],
  });
}

export function useResources() {
  return useQuery({
    queryKey: ['resources'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/resources`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch resources');
      return res.json();
    },
    initialData: [],
  });
}

export function useLogs(limit: number = 50) {
  return useQuery({
    queryKey: ['logs', limit],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/logs?limit=${limit}`, {
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error('Failed to fetch logs');
      return res.json();
    },
    initialData: [],
    refetchInterval: 5000, // Auto-refresh logs every 5 seconds
  });
}
