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

  // Persona management
  async getPersonas() {
    return this.request('/api/personas');
  }

  async getPersona(personaId) {
    return this.request(`/api/personas/${personaId}`);
  }

  async createPersona(personaData) {
    return this.request('/api/personas', {
      method: 'POST',
      body: JSON.stringify(personaData)
    });
  }

  async updatePersona(personaId, personaData) {
    return this.request(`/api/personas/${personaId}`, {
      method: 'PUT',
      body: JSON.stringify(personaData)
    });
  }

  async deletePersona(personaId) {
    return this.request(`/api/personas/${personaId}`, {
      method: 'DELETE'
    });
  }

  async getPersonaAnalytics() {
    return this.request('/api/personas/analytics/summary');
  }

  async updatePersonaDomainLeanings(personaId, leanings) {
    return this.request(`/api/personas/${personaId}/domain-leanings`, {
      method: 'PUT',
      body: JSON.stringify(leanings)
    });
  }

  // Advanced search functionality
  async getAdvancedSearchModes() {
    return this.request('/api/search/modes');
  }

  async getSearchSources() {
    return this.request('/api/search/sources');
  }

  // Creative content functionality
  async getCreativeTemplates() {
    return this.request('/api/creative/templates');
  }

  async getCreativeGallery() {
    return this.request('/api/creative/gallery');
  }

  async getCreativeStatus() {
    return this.request('/api/creative/status');
  }

  async generateDocument(documentRequest) {
    return this.request('/api/creative/document', {
      method: 'POST',
      body: JSON.stringify(documentRequest)
    });
  }

  async generateImage(imageRequest) {
    return this.request('/api/creative/image', {
      method: 'POST',
      body: JSON.stringify(imageRequest)
    });
  }

  async generateVideo(videoRequest) {
    return this.request('/api/creative/video', {
      method: 'POST',
      body: JSON.stringify(videoRequest)
    });
  }

  async generateAudio(audioRequest) {
    return this.request('/api/creative/audio', {
      method: 'POST',
      body: JSON.stringify(audioRequest)
    });
  }

  async generatePresentation(presentationRequest) {
    return this.request('/api/creative/presentation', {
      method: 'POST',
      body: JSON.stringify(presentationRequest)
    });
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

