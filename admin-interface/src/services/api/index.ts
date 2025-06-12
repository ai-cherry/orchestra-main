// Main API Service Index - Orchestra AI Integration

export * from './types'
export * from './client'
export * from './websocket'

// Re-export commonly used instances
export { apiClient } from './client'
export { websocketService } from './websocket'

// Convenience functions for common operations
import { apiClient } from './client'
import { websocketService } from './websocket'
import { Persona, ChatRequest, Message } from './types'

/**
 * Initialize the Orchestra AI API services
 */
export async function initializeOrchestralAPI(authToken?: string): Promise<void> {
  try {
    // Initialize authentication if token provided
    if (authToken) {
      apiClient.setAuthToken(authToken)
    } else {
      // Try to initialize from stored token
      apiClient.initializeAuth()
    }

    // Test API connection
    const health = await apiClient.getSystemHealth()
    console.log('✅ Orchestra AI API connected:', health.status)

    // Initialize WebSocket connection
    try {
      await websocketService.connect(apiClient.getAuthToken() || undefined)
      console.log('✅ Orchestra AI WebSocket connected')
    } catch (error) {
      console.warn('⚠️ WebSocket connection failed, continuing with HTTP only:', error)
    }

  } catch (error) {
    console.error('❌ Failed to initialize Orchestra AI API:', error)
    throw error
  }
}

/**
 * Send a message to a persona with automatic error handling
 */
export async function sendPersonaMessage(
  persona: Persona, 
  message: string, 
  context?: any
): Promise<Message> {
  try {
    const request: ChatRequest = {
      persona,
      message,
      context
    }

    const response = await apiClient.sendMessage(request)
    
    return {
      id: response.id,
      content: response.content,
      persona: response.persona,
      timestamp: new Date(response.timestamp),
      type: response.type,
      metadata: response.metadata
    }
  } catch (error) {
    console.error('Failed to send message to persona:', error)
    throw error
  }
}

/**
 * Get optimal persona for a task
 */
export async function getOptimalPersona(
  taskDescription: string,
  taskType?: string,
  complexity?: string,
  domains?: string[]
): Promise<{ persona: Persona; reasoning: string }> {
  try {
    const result = await apiClient.routeTask(taskDescription, taskType, complexity, domains)
    return {
      persona: result.optimal_persona,
      reasoning: result.reasoning
    }
  } catch (error) {
    console.error('Failed to route task:', error)
    // Fallback to Cherry for coordination
    return {
      persona: 'cherry',
      reasoning: 'Fallback to Cherry due to routing error'
    }
  }
}

/**
 * Check if all services are healthy
 */
export async function checkSystemHealth(): Promise<boolean> {
  try {
    const health = await apiClient.getSystemHealth()
    return health.status === 'healthy'
  } catch (error) {
    console.error('Health check failed:', error)
    return false
  }
}

/**
 * Setup WebSocket event handlers with common patterns
 */
export function setupWebSocketHandlers(handlers: {
  onMessage?: (message: Message) => void
  onTyping?: (persona: Persona, isTyping: boolean) => void
  onPersonaSwitch?: (persona: Persona) => void
  onSystemUpdate?: (update: any) => void
  onError?: (error: string) => void
  onConnectionChange?: (connected: boolean) => void
}): void {
  websocketService.setCallbacks({
    onMessage: handlers.onMessage,
    onTyping: handlers.onTyping,
    onPersonaSwitch: handlers.onPersonaSwitch,
    onSystemUpdate: handlers.onSystemUpdate,
    onError: handlers.onError,
    onConnected: () => handlers.onConnectionChange?.(true),
    onDisconnected: () => handlers.onConnectionChange?.(false)
  })
}

/**
 * Cleanup API services
 */
export function cleanupOrchestralAPI(): void {
  websocketService.disconnect()
  apiClient.logout()
}

// Default export for convenience
export default {
  initialize: initializeOrchestralAPI,
  sendMessage: sendPersonaMessage,
  getOptimalPersona,
  checkHealth: checkSystemHealth,
  setupWebSocket: setupWebSocketHandlers,
  cleanup: cleanupOrchestralAPI,
  client: apiClient,
  websocket: websocketService
} 