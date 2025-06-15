import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react'

interface WebSocketMessage {
  type: string
  [key: string]: any
}

interface WebSocketContextType {
  connectionStatus: 'Connecting' | 'Connected' | 'Disconnected' | 'Error'
  lastMessage: WebSocketMessage | null
  sendMessage: (message: WebSocketMessage) => void
  subscribe: (channel: string) => void
  unsubscribe: (channel: string) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const ws = useRef<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'Connecting' | 'Connected' | 'Disconnected' | 'Error'>('Disconnected')
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const subscriptionsRef = useRef<Set<string>>(new Set())
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5

  const connect = () => {
    try {
      setConnectionStatus('Connecting')
      const wsUrl = `ws://localhost:8000/ws/user-${Date.now()}`
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        setConnectionStatus('Connected')
        reconnectAttempts.current = 0
        
        // Resubscribe to channels
        subscriptionsRef.current.forEach(channel => {
          sendMessage({ type: 'subscribe', channel })
        })
      }

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          setLastMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.current.onclose = () => {
        setConnectionStatus('Disconnected')
        attemptReconnect()
      }

      ws.current.onerror = () => {
        setConnectionStatus('Error')
        attemptReconnect()
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
      setConnectionStatus('Error')
      attemptReconnect()
    }
  }

  const attemptReconnect = () => {
    if (reconnectAttempts.current < maxReconnectAttempts) {
      reconnectAttempts.current++
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
      
      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, delay)
    }
  }

  const sendMessage = (message: WebSocketMessage) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
    }
  }

  const subscribe = (channel: string) => {
    subscriptionsRef.current.add(channel)
    sendMessage({ type: 'subscribe', channel })
  }

  const unsubscribe = (channel: string) => {
    subscriptionsRef.current.delete(channel)
    sendMessage({ type: 'unsubscribe', channel })
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  return (
    <WebSocketContext.Provider value={{
      connectionStatus,
      lastMessage,
      sendMessage,
      subscribe,
      unsubscribe
    }}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
} 