import { useQuery } from '@tanstack/react-query'

// Use relative URLs - nginx will proxy /api to the backend
const API_URL = ''  // Empty string means use same origin

// Define the QueryBody interface with a query string property
export interface QueryBody {
  query: string
}

function getHeaders() {
  // For now, just use the hardcoded API key
  // In production, you'd want to get this from environment or secure storage
  return {
    'Content-Type': 'application/json',
    // Use the API key for backend authentication
    'X-API-Key': '4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd'
  }
}

export function useQueryApi(body: QueryBody) {
  return useQuery({
    queryKey: ['query', body],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(body)
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })
}

export function useAgents() {
  return useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/agents`, {
        headers: getHeaders()
      })
      if (!res.ok) {
        // Return empty array if endpoint doesn't exist yet
        return []
      }
      return res.json()
    },
    // Return empty array as default
    initialData: []
  })
}

export function useUpload() {
  return useQuery({
    queryKey: ['upload'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/upload`, {
        headers: getHeaders()
      })
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })
}
