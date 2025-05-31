import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'

// Use environment variables for API URL and API key
const API_URL = import.meta.env.VITE_API_URL || window.location.origin;
const API_KEY = import.meta.env.VITE_API_KEY;

// Define the QueryBody interface with a query string property
export interface QueryBody {
  query: string
}

function getHeaders() {
  // Get token from auth store (which is the API key after login)
  const { token } = useAuthStore.getState();

  return {
    'Content-Type': 'application/json',
    'X-API-Key': token || API_KEY, // Use token from login, fallback to env var
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
