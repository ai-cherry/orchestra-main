// Updated API configuration for Orchestra AI
// This ensures the frontend connects to the real backend API

const API_BASE_URL = 'https://8000-ivp4wb670lvqa3xuy004a-c02a81ef.manusvm.computer';

console.log('API Client initialized with URL:', API_BASE_URL);

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
    console.log('ApiClient created with baseURL:', this.baseURL);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    console.log('Making API request to:', url);
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      console.log(`API Response for ${endpoint}:`, response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        console.log(`API Data for ${endpoint}:`, data);
        return data;
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

  // Chat functionality
  async sendChatMessage(message, persona = 'sophia') {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: message,
        persona: persona
      })
    });
  }

  // Search functionality
  async search(query, includeDatabase = true, includeInternet = true) {
    return this.request('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        query: query,
        include_database: includeDatabase,
        include_internet: includeInternet
      })
    });
  }
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

