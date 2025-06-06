import { useState, useEffect, useRef } from 'react'
import { useSystemStore } from '../stores/systemStore'

export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [lastMessage, setLastMessage] = useState(null)
  const ws = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const { setConnectionStatus: setStoreConnectionStatus } = useSystemStore()

  const connect = () => {
    try {
      ws.current = new WebSocket(url)
      setConnectionStatus('connecting')
      setStoreConnectionStatus('connecting', false)

      ws.current.onopen = () => {
        setIsConnected(true)
        setConnectionStatus('connected')
        setStoreConnectionStatus('connected', true)
        console.log('WebSocket connected')
        
        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setLastMessage(data)
          
          // Handle different message types
          switch (data.type) {
            case 'system_metrics':
              useSystemStore.getState().updateSystemHealth(data.payload)
              break
            case 'persona_status':
              // Handle persona status updates
              console.log('Persona status update:', data.payload)
              break
            case 'workflow_progress':
              // Handle workflow progress updates
              console.log('Workflow progress:', data.payload)
              break
            default:
              console.log('Unknown message type:', data.type)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      ws.current.onclose = (event) => {
        setIsConnected(false)
        setConnectionStatus('disconnected')
        setStoreConnectionStatus('disconnected', false)
        console.log('WebSocket disconnected:', event.code, event.reason)
        
        // Attempt to reconnect after 3 seconds
        if (!reconnectTimeoutRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...')
            connect()
          }, 3000)
        }
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('error')
        setStoreConnectionStatus('error', false)
      }

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setConnectionStatus('error')
      setStoreConnectionStatus('error', false)
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }

  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
      return true
    } else {
      console.warn('WebSocket is not connected')
      return false
    }
  }

  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [url])

  return {
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage,
    connect,
    disconnect
  }
}

