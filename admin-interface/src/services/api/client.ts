import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { 
  ChatRequest, 
  ChatResponse, 
  PersonaStatus, 
  HealthStatus, 
  MemoryMetrics,
  SystemCommand,
  CommandResult,
  AuthCredentials,
  AuthResult,
  User,
  APIError,
  Persona
} from './types'

export class OrchestralAPIClient {
  private client: AxiosInstance
  private authToken: string | null = null

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.REACT_APP_API_URL || 'http://192.9.142.8:8000',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const apiError: APIError = {
          code: error.response?.status?.toString() || 'NETWORK_ERROR',
          message: error.response?.data?.message || error.message,
          details: error.response?.data,
          timestamp: new Date().toISOString()
        }
        return Promise.reject(apiError)
      }
    )
  }

  // Authentication Methods
  async login(credentials: AuthCredentials): Promise<AuthResult> {
    try {
      const response: AxiosResponse<AuthResult> = await this.client.post('/auth/login', credentials)
      if (response.data.success && response.data.token) {
        this.authToken = response.data.token
        localStorage.setItem('orchestra_auth_token', response.data.token)
      }
      return response.data
    } catch (error) {
      return {
        success: false,
        error: (error as APIError).message
      }
    }
  }

  async logout(): Promise<void> {
    this.authToken = null
    localStorage.removeItem('orchestra_auth_token')
    await this.client.post('/auth/logout').catch(() => {
      // Ignore logout errors
    })
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const response: AxiosResponse<User> = await this.client.get('/auth/user')
      return response.data
    } catch (error) {
      return null
    }
  }

  // Chat Methods
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.client.post('/chat', request)
    return {
      ...response.data,
      timestamp: new Date(response.data.timestamp).toISOString()
    }
  }

  async getConversationHistory(limit: number = 50, persona?: Persona): Promise<ChatResponse[]> {
    const params = { limit, persona }
    const response: AxiosResponse<ChatResponse[]> = await this.client.get('/chat/history', { params })
    return response.data.map(msg => ({
      ...msg,
      timestamp: new Date(msg.timestamp).toISOString()
    }))
  }

  // Persona Methods
  async getPersonaStatus(): Promise<PersonaStatus[]> {
    const response: AxiosResponse<PersonaStatus[]> = await this.client.get('/personas/status')
    return response.data
  }

  async switchPersona(persona: Persona): Promise<void> {
    await this.client.post('/personas/switch', { persona })
  }

  async getPersonaCapabilities(persona: Persona): Promise<string[]> {
    const response: AxiosResponse<{ capabilities: string[] }> = await this.client.get(`/personas/${persona}/capabilities`)
    return response.data.capabilities
  }

  // System Methods
  async getSystemHealth(): Promise<HealthStatus> {
    const response: AxiosResponse<HealthStatus> = await this.client.get('/health')
    return response.data
  }

  async getMemoryMetrics(): Promise<MemoryMetrics> {
    const response: AxiosResponse<MemoryMetrics> = await this.client.get('/system/memory')
    return response.data
  }

  async executeCommand(command: SystemCommand): Promise<CommandResult> {
    const response: AxiosResponse<CommandResult> = await this.client.post('/system/command', command)
    return response.data
  }

  // Advanced Features
  async routeTask(taskDescription: string, taskType?: string, complexity?: string, domains?: string[]): Promise<{ optimal_persona: Persona; reasoning: string }> {
    const response = await this.client.post('/system/route-task', {
      task_description: taskDescription,
      task_type: taskType,
      complexity: complexity,
      domains_involved: domains
    })
    return response.data
  }

  async crossDomainQuery(primaryPersona: Persona, query: string, requiredDomains: string[], collaborationType?: string): Promise<ChatResponse> {
    const response: AxiosResponse<ChatResponse> = await this.client.post('/system/cross-domain', {
      primary_persona: primaryPersona,
      query,
      required_domains: requiredDomains,
      collaboration_type: collaborationType
    })
    return response.data
  }

  // Utility Methods
  setAuthToken(token: string): void {
    this.authToken = token
    localStorage.setItem('orchestra_auth_token', token)
  }

  getAuthToken(): string | null {
    return this.authToken || localStorage.getItem('orchestra_auth_token')
  }

  isAuthenticated(): boolean {
    return !!this.getAuthToken()
  }

  // Initialize from stored token
  initializeAuth(): void {
    const storedToken = localStorage.getItem('orchestra_auth_token')
    if (storedToken) {
      this.authToken = storedToken
    }
  }
}

// Singleton instance
export const apiClient = new OrchestralAPIClient()

// Initialize auth on module load
apiClient.initializeAuth() 