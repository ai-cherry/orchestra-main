import { io, Socket } from 'socket.io-client'
import { WebSocketMessage, Persona, Message } from './types'

export type WebSocketEventType = 'message' | 'typing' | 'persona_switch' | 'system_update' | 'error' | 'connected' | 'disconnected'

export interface WebSocketCallbacks {
  onMessage?: (message: Message) => void
  onTyping?: (persona: Persona, isTyping: boolean) => void
  onPersonaSwitch?: (persona: Persona) => void
  onSystemUpdate?: (update: any) => void
  onError?: (error: string) => void
  onConnected?: () => void
  onDisconnected?: () => void
}

export class WebSocketService {
  private socket: Socket | null = null
  private callbacks: WebSocketCallbacks = {}
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isConnecting = false

  constructor(private url?: string) {
    this.url = url || process.env.REACT_APP_WS_URL || 'ws://192.9.142.8:8001'
  }

  async connect(authToken?: string): Promise<void> {
    if (this.isConnecting || this.isConnected()) {
      return
    }

    this.isConnecting = true

    try {
      const socketOptions: any = {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        forceNew: true
      }

      if (authToken) {
        socketOptions.auth = { token: authToken }
      }

      this.socket = io(this.url!, socketOptions)
      this.setupEventHandlers()

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket connection timeout'))
        }, 10000)

        this.socket!.on('connect', () => {
          clearTimeout(timeout)
          this.isConnecting = false
          this.reconnectAttempts = 0
          console.log('✅ WebSocket connected to Orchestra AI')
          this.callbacks.onConnected?.()
          resolve()
        })

        this.socket!.on('connect_error', (error) => {
          clearTimeout(timeout)
          this.isConnecting = false
          console.error('❌ WebSocket connection error:', error)
          reject(error)
        })
      })
    } catch (error) {
      this.isConnecting = false
      throw error
    }
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
    this.callbacks.onDisconnected?.()
  }

  isConnected(): boolean {
    return this.socket?.connected || false
  }

  // Message sending methods
  sendMessage(persona: Persona, content: string, type: string = 'text'): void {
    if (!this.isConnected()) {
      throw new Error('WebSocket not connected')
    }

    const message: WebSocketMessage = {
      type: 'message',
      data: {
        persona,
        content,
        type,
        timestamp: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    }

    this.socket!.emit('chat_message', message)
  }

  sendTypingIndicator(persona: Persona, isTyping: boolean): void {
    if (!this.isConnected()) return

    const message: WebSocketMessage = {
      type: 'typing',
      data: { persona, isTyping },
      timestamp: new Date().toISOString()
    }

    this.socket!.emit('typing_indicator', message)
  }

  switchPersona(persona: Persona): void {
    if (!this.isConnected()) return

    const message: WebSocketMessage = {
      type: 'persona_switch',
      data: { persona },
      timestamp: new Date().toISOString()
    }

    this.socket!.emit('persona_switch', message)
  }

  // Event subscription methods
  setCallbacks(callbacks: WebSocketCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  onMessage(callback: (message: Message) => void): void {
    this.callbacks.onMessage = callback
  }

  onTyping(callback: (persona: Persona, isTyping: boolean) => void): void {
    this.callbacks.onTyping = callback
  }

  onPersonaSwitch(callback: (persona: Persona) => void): void {
    this.callbacks.onPersonaSwitch = callback
  }

  onSystemUpdate(callback: (update: any) => void): void {
    this.callbacks.onSystemUpdate = callback
  }

  onError(callback: (error: string) => void): void {
    this.callbacks.onError = callback
  }

  onConnected(callback: () => void): void {
    this.callbacks.onConnected = callback
  }

  onDisconnected(callback: () => void): void {
    this.callbacks.onDisconnected = callback
  }

  private setupEventHandlers(): void {
    if (!this.socket) return

    // Connection events
    this.socket.on('disconnect', (reason) => {
      console.log('🔌 WebSocket disconnected:', reason)
      this.callbacks.onDisconnected?.()
      
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect automatically
        return
      }
      
      this.handleReconnect()
    })

    // Chat events
    this.socket.on('chat_response', (data: WebSocketMessage) => {
      if (data.type === 'message' && this.callbacks.onMessage) {
        const message: Message = {
          id: data.data.id || Date.now().toString(),
          content: data.data.content,
          persona: data.data.persona,
          timestamp: new Date(data.data.timestamp),
          type: data.data.type || 'text',
          metadata: data.data.metadata
        }
        this.callbacks.onMessage(message)
      }
    })

    // Typing events
    this.socket.on('typing_update', (data: WebSocketMessage) => {
      if (data.type === 'typing' && this.callbacks.onTyping) {
        this.callbacks.onTyping(data.data.persona, data.data.isTyping)
      }
    })

    // Persona switch events
    this.socket.on('persona_switched', (data: WebSocketMessage) => {
      if (data.type === 'persona_switch' && this.callbacks.onPersonaSwitch) {
        this.callbacks.onPersonaSwitch(data.data.persona)
      }
    })

    // System update events
    this.socket.on('system_update', (data: WebSocketMessage) => {
      if (data.type === 'system_update' && this.callbacks.onSystemUpdate) {
        this.callbacks.onSystemUpdate(data.data)
      }
    })

    // Error events
    this.socket.on('error', (error: any) => {
      console.error('🚨 WebSocket error:', error)
      this.callbacks.onError?.(error.message || 'WebSocket error')
    })

    // Custom Orchestra AI events
    this.socket.on('persona_status_update', (data: any) => {
      this.callbacks.onSystemUpdate?.({
        type: 'persona_status',
        data
      })
    })

    this.socket.on('memory_metrics_update', (data: any) => {
      this.callbacks.onSystemUpdate?.({
        type: 'memory_metrics',
        data
      })
    })
  }

  private async handleReconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached')
      this.callbacks.onError?.('Connection lost - max reconnection attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1) // Exponential backoff

    console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms...`)

    setTimeout(async () => {
      try {
        await this.connect()
      } catch (error) {
        console.error('🚨 Reconnection failed:', error)
        this.handleReconnect()
      }
    }, delay)
  }

  // Utility methods
  getConnectionState(): 'connected' | 'connecting' | 'disconnected' {
    if (this.isConnecting) return 'connecting'
    if (this.isConnected()) return 'connected'
    return 'disconnected'
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts
  }
}

// Singleton instance
export const websocketService = new WebSocketService()

// Auto-connect when module loads (optional)
// websocketService.connect().catch(console.error) 