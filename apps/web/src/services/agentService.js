/**
 * Agent Service
 * 
 * This service provides functions for interacting with the AI Orchestra Agent API.
 * It handles all agent-related operations including CRUD operations, testing,
 * and retrieving conversation history.
 */

import axios from 'axios';

// Base API URL - can be configured based on environment
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080';
const AGENTS_ENDPOINT = `${API_BASE_URL}/agents`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle specific error cases
    if (error.response) {
      // Server responded with an error status
      console.error('API Error:', error.response.data);
      
      // Handle authentication errors
      if (error.response.status === 401) {
        // Redirect to login or refresh token
        localStorage.removeItem('auth_token');
        // window.location.href = '/login';
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.request);
    } else {
      // Error in setting up the request
      console.error('Request Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Get all agents with optional pagination
 * 
 * @param {Object} options - Query options
 * @param {number} options.skip - Number of items to skip
 * @param {number} options.limit - Maximum number of items to return
 * @returns {Promise<Object>} - Promise resolving to the API response
 */
export const getAgents = async (options = {}) => {
  const { skip = 0, limit = 10 } = options;
  const response = await apiClient.get(AGENTS_ENDPOINT, {
    params: { skip, limit }
  });
  return response.data;
};

/**
 * Get a specific agent by ID
 * 
 * @param {string} agentId - The ID of the agent to retrieve
 * @returns {Promise<Object>} - Promise resolving to the agent data
 */
export const getAgentById = async (agentId) => {
  const response = await apiClient.get(`${AGENTS_ENDPOINT}/${agentId}`);
  return response.data;
};

/**
 * Create a new agent
 * 
 * @param {Object} agentData - The agent configuration data
 * @returns {Promise<Object>} - Promise resolving to the created agent
 */
export const createAgent = async (agentData) => {
  const response = await apiClient.post(AGENTS_ENDPOINT, agentData);
  return response.data;
};

/**
 * Update an existing agent
 * 
 * @param {string} agentId - The ID of the agent to update
 * @param {Object} agentData - The updated agent configuration
 * @returns {Promise<Object>} - Promise resolving to the updated agent
 */
export const updateAgent = async (agentId, agentData) => {
  const response = await apiClient.put(`${AGENTS_ENDPOINT}/${agentId}`, agentData);
  return response.data;
};

/**
 * Delete an agent
 * 
 * @param {string} agentId - The ID of the agent to delete
 * @returns {Promise<void>} - Promise resolving when the agent is deleted
 */
export const deleteAgent = async (agentId) => {
  await apiClient.delete(`${AGENTS_ENDPOINT}/${agentId}`);
};

/**
 * Test an agent with a sample input
 * 
 * @param {string} agentId - The ID of the agent to test
 * @param {Object} inputData - The input data for testing
 * @returns {Promise<Object>} - Promise resolving to the test results
 */
export const testAgent = async (agentId, inputData) => {
  const response = await apiClient.post(`${AGENTS_ENDPOINT}/${agentId}/test`, inputData);
  return response.data;
};

/**
 * Get conversation history for an agent
 * 
 * @param {string} agentId - The ID of the agent
 * @param {Object} options - Query options
 * @param {number} options.skip - Number of items to skip
 * @param {number} options.limit - Maximum number of items to return
 * @returns {Promise<Object>} - Promise resolving to the conversation history
 */
export const getAgentConversations = async (agentId, options = {}) => {
  const { skip = 0, limit = 10 } = options;
  const response = await apiClient.get(`${AGENTS_ENDPOINT}/${agentId}/conversations`, {
    params: { skip, limit }
  });
  return response.data;
};

/**
 * Get metrics for an agent
 * 
 * @param {string} agentId - The ID of the agent
 * @param {Object} options - Query options
 * @param {string} options.timeRange - Time range for metrics (e.g., '1d', '7d', '30d')
 * @returns {Promise<Object>} - Promise resolving to the agent metrics
 */
export const getAgentMetrics = async (agentId, options = {}) => {
  const { timeRange = '7d' } = options;
  const response = await apiClient.get(`${AGENTS_ENDPOINT}/${agentId}/metrics`, {
    params: { timeRange }
  });
  return response.data;
};

/**
 * Export agent configuration
 * 
 * @param {string} agentId - The ID of the agent to export
 * @returns {Promise<Object>} - Promise resolving to the agent configuration
 */
export const exportAgentConfig = async (agentId) => {
  const response = await apiClient.get(`${AGENTS_ENDPOINT}/${agentId}/export`);
  return response.data;
};

/**
 * Import agent configuration
 * 
 * @param {Object} configData - The agent configuration to import
 * @returns {Promise<Object>} - Promise resolving to the imported agent
 */
export const importAgentConfig = async (configData) => {
  const response = await apiClient.post(`${AGENTS_ENDPOINT}/import`, configData);
  return response.data;
};

/**
 * Clone an existing agent
 * 
 * @param {string} agentId - The ID of the agent to clone
 * @param {Object} options - Clone options
 * @param {string} options.name - Name for the cloned agent
 * @returns {Promise<Object>} - Promise resolving to the cloned agent
 */
export const cloneAgent = async (agentId, options = {}) => {
  const response = await apiClient.post(`${AGENTS_ENDPOINT}/${agentId}/clone`, options);
  return response.data;
};

export default {
  getAgents,
  getAgentById,
  createAgent,
  updateAgent,
  deleteAgent,
  testAgent,
  getAgentConversations,
  getAgentMetrics,
  exportAgentConfig,
  importAgentConfig,
  cloneAgent
};