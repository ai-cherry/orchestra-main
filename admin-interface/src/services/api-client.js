import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(username, password) {
    const response = await this.client.post('/auth/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('auth_token', response.data.access_token);
    }
    return response.data;
  }

  async register(userData) {
    return this.client.post('/auth/register', userData);
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Persona endpoints
  async getPersonas() {
    const response = await this.client.get('/api/personas');
    return response.data;
  }

  async updatePersona(personaId, updates) {
    const response = await this.client.put(`/api/personas/${personaId}`, updates);
    return response.data;
  }

  // Agent endpoints
  async getAgents(personaId = null) {
    const url = personaId ? `/api/personas/${personaId}/agents` : '/api/agents';
    const response = await this.client.get(url);
    return response.data;
  }

  async updateAgent(agentId, updates) {
    const response = await this.client.put(`/api/agents/${agentId}`, updates);
    return response.data;
  }

  // Conversation endpoints
  async sendMessage(personaType, message, sessionId = null, mode = 'casual') {
    const response = await this.client.post('/api/conversation', {
      message,
      persona_type: personaType,
      session_id: sessionId,
      mode
    });
    return response.data;
  }

  async getConversationHistory(personaType, limit = 20) {
    const response = await this.client.get(`/api/conversation/history/${personaType}?limit=${limit}`);
    return response.data;
  }

  async getRelationshipInsights(personaType) {
    const response = await this.client.get(`/api/relationship/insights/${personaType}`);
    return response.data;
  }

  // System endpoints
  async getSystemMetrics() {
    const response = await this.client.get('/api/system/metrics');
    return response.data;
  }

  async getSystemHealth() {
    const response = await this.client.get('/api/system/health');
    return response.data;
  }

  // MCP Server endpoints
  async getMCPTools(serverName) {
    const response = await this.client.get(`/mcp/${serverName}/tools`);
    return response.data;
  }

  async callMCPTool(serverName, toolName, args) {
    const response = await this.client.post(`/mcp/${serverName}/call/${toolName}`, args);
    return response.data;
  }

  // Workflow endpoints
  async createWorkflow(workflowData) {
    const response = await this.client.post('/api/workflows', workflowData);
    return response.data;
  }

  async getWorkflows() {
    const response = await this.client.get('/api/workflows');
    return response.data;
  }

  async executeWorkflow(workflowId, params = {}) {
    const response = await this.client.post(`/api/workflows/${workflowId}/execute`, params);
    return response.data;
  }

  // Search endpoints
  async searchMemories(query, filters = {}) {
    const response = await this.client.post('/api/search/memories', { query, ...filters });
    return response.data;
  }

  async vectorSearch(collection, query, limit = 10) {
    const response = await this.client.post('/api/search/vector', {
      collection,
      query,
      limit
    });
    return response.data;
  }
}

export default new APIClient();