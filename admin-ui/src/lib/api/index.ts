import { useQuery } from '@tanstack/react-query'

const API_URL = import.meta.env.VITE_API_URL

export interface QueryPayload {
  query: string
  [key: string]: unknown
}

export function useQueryApi(body: QueryPayload) {
  return useQuery({
    queryKey: ['query', body],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      const res = await fetch(`${API_URL}/api/agents`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })
}

export function useUpload() {
  return useQuery({
    queryKey: ['upload'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/api/upload`)
      if (!res.ok) throw new Error('Failed')
      return res.json()
    }
  })
}
