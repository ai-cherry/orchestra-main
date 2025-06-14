/**
 * API Utility Module
 * Centralized API configuration and request handling
 */

// Get API URL from environment or use proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

class ApiClient {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this.timeout = API_TIMEOUT;
  }

  async request(endpoint, options = {}) {
    const url = this.baseUrl ? `${this.baseUrl}${endpoint}` : endpoint;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      throw error;
    }
  }

  // Convenience methods
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

// Create singleton instance
const apiClient = new ApiClient();

// Export named functions for direct use
export const api = {
  get: (endpoint, options) => apiClient.get(endpoint, options),
  post: (endpoint, data, options) => apiClient.post(endpoint, data, options),
  put: (endpoint, data, options) => apiClient.put(endpoint, data, options),
  delete: (endpoint, options) => apiClient.delete(endpoint, options),
};

// Export default client instance
export default apiClient; 