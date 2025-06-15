// Updated API configuration for production backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health check
  async getHealth() {
    return this.request('/health');
  }

  // System status
  async getSystemStatus() {
    return this.request('/api/system/status');
  }

  // Agents
  async getAgents() {
    return this.request('/api/agents');
  }

  // Personas
  async getPersonas() {
    return this.request('/api/personas');
  }

  // Workflows
  async getWorkflows() {
    return this.request('/api/workflows');
  }

  // Files
  async getFiles() {
    return this.request('/api/files');
  }

  // Activity logs
  async getActivityLogs(limit = 50) {
    return this.request(`/api/activity?limit=${limit}`);
  }
}

export const apiClient = new ApiClient();
export default apiClient;

