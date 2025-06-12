/**
 * OpenRouter Service for React Native
 * Intelligent AI routing with cost optimization and fallbacks
 * 
 * @author Orchestra AI Team
 * @version 1.0.0
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';

// Configuration
const API_CONFIG = {
  baseUrl: __DEV__ ? 'http://localhost:8020' : 'https://api.orchestra-ai.dev',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// Use cases enum
export const USE_CASES = {
  CASUAL_CHAT: 'casual_chat',
  BUSINESS_ANALYSIS: 'business_analysis',
  MEDICAL_COMPLIANCE: 'medical_compliance',
  CREATIVE_WRITING: 'creative_writing',
  CODE_GENERATION: 'code_generation',
  RESEARCH_SEARCH: 'research_search',
  STRATEGIC_PLANNING: 'strategic_planning',
  QUICK_RESPONSE: 'quick_response',
};

// Personas
export const PERSONAS = {
  CHERRY: 'cherry',
  SOPHIA: 'sophia',
  KAREN: 'karen',
};

// Complexity levels
export const COMPLEXITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
};

class OpenRouterService {
  constructor() {
    this.isOnline = true;
    this.requestQueue = [];
    this.stats = {
      totalRequests: 0,
      totalCost: 0,
      totalSavings: 0,
      providerUsage: {},
    };
    
    this.initializeNetworkListener();
    this.loadStatsFromStorage();
  }

  /**
   * Initialize network connectivity listener
   */
  initializeNetworkListener() {
    NetInfo.addEventListener(state => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected;
      
      // Process queued requests when coming back online
      if (!wasOnline && this.isOnline && this.requestQueue.length > 0) {
        this.processQueuedRequests();
      }
    });
  }

  /**
   * Load statistics from local storage
   */
  async loadStatsFromStorage() {
    try {
      const savedStats = await AsyncStorage.getItem('openrouter_stats');
      if (savedStats) {
        this.stats = { ...this.stats, ...JSON.parse(savedStats) };
      }
    } catch (error) {
      console.warn('Failed to load stats from storage:', error);
    }
  }

  /**
   * Save statistics to local storage
   */
  async saveStatsToStorage() {
    try {
      await AsyncStorage.setItem('openrouter_stats', JSON.stringify(this.stats));
    } catch (error) {
      console.warn('Failed to save stats to storage:', error);
    }
  }

  /**
   * Main chat completion method
   */
  async chatCompletion({
    persona = PERSONAS.CHERRY,
    message,
    useCase = USE_CASES.CASUAL_CHAT,
    complexity = COMPLEXITY.MEDIUM,
    maxTokens = null,
    temperature = null,
    fallbackAllowed = true,
    onProgress = null,
  }) {
    // Validate inputs
    if (!message || typeof message !== 'string') {
      throw new Error('Message is required and must be a string');
    }

    if (!Object.values(PERSONAS).includes(persona)) {
      throw new Error(`Invalid persona. Must be one of: ${Object.values(PERSONAS).join(', ')}`);
    }

    if (!Object.values(USE_CASES).includes(useCase)) {
      throw new Error(`Invalid use case. Must be one of: ${Object.values(USE_CASES).join(', ')}`);
    }

    // Check network connectivity
    if (!this.isOnline) {
      if (fallbackAllowed) {
        return this.queueRequest({
          persona,
          message,
          useCase,
          complexity,
          maxTokens,
          temperature,
          fallbackAllowed,
          onProgress,
        });
      } else {
        throw new Error('No network connection available');
      }
    }

    const requestData = {
      persona,
      message,
      use_case: useCase,
      complexity,
      max_tokens: maxTokens,
      temperature,
      fallback_allowed: fallbackAllowed,
    };

    try {
      if (onProgress) {
        onProgress({ status: 'connecting', message: 'Connecting to AI service...' });
      }

      const response = await this.makeRequest('/chat', 'POST', requestData);
      
      if (onProgress) {
        onProgress({ status: 'processing', message: 'Processing response...' });
      }

      // Update statistics
      await this.updateStats(response);

      if (onProgress) {
        onProgress({ status: 'complete', message: 'Response received' });
      }

      return {
        success: true,
        data: response,
        timestamp: new Date().toISOString(),
      };

    } catch (error) {
      console.error('Chat completion failed:', error);
      
      if (onProgress) {
        onProgress({ status: 'error', message: error.message });
      }

      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Convenience method for casual chat
   */
  async casualChat(persona, message, options = {}) {
    return this.chatCompletion({
      persona,
      message,
      useCase: USE_CASES.CASUAL_CHAT,
      ...options,
    });
  }

  /**
   * Convenience method for business analysis
   */
  async businessAnalysis(persona, message, options = {}) {
    return this.chatCompletion({
      persona,
      message,
      useCase: USE_CASES.BUSINESS_ANALYSIS,
      complexity: COMPLEXITY.HIGH,
      ...options,
    });
  }

  /**
   * Convenience method for medical compliance
   */
  async medicalCompliance(persona, message, options = {}) {
    return this.chatCompletion({
      persona,
      message,
      useCase: USE_CASES.MEDICAL_COMPLIANCE,
      complexity: COMPLEXITY.HIGH,
      ...options,
    });
  }

  /**
   * Convenience method for research
   */
  async research(persona, message, options = {}) {
    return this.chatCompletion({
      persona,
      message,
      useCase: USE_CASES.RESEARCH_SEARCH,
      ...options,
    });
  }

  /**
   * Convenience method for code generation
   */
  async codeGeneration(persona, message, options = {}) {
    return this.chatCompletion({
      persona,
      message,
      useCase: USE_CASES.CODE_GENERATION,
      temperature: 0.1,
      ...options,
    });
  }

  /**
   * Get usage statistics
   */
  async getStats() {
    try {
      const serverStats = await this.makeRequest('/stats', 'GET');
      return {
        local: this.stats,
        server: serverStats,
        combined: {
          totalRequests: this.stats.totalRequests,
          totalCost: serverStats.total_cost || 0,
          totalSavings: serverStats.total_savings || 0,
          providerUsage: serverStats.provider_usage || {},
        },
      };
    } catch (error) {
      console.warn('Failed to get server stats:', error);
      return { local: this.stats };
    }
  }

  /**
   * Get available models and configurations
   */
  async getModels() {
    try {
      return await this.makeRequest('/models', 'GET');
    } catch (error) {
      console.error('Failed to get models:', error);
      throw error;
    }
  }

  /**
   * Test a specific provider
   */
  async testProvider(provider, message = 'Hello, this is a test.') {
    try {
      return await this.makeRequest(`/test/${provider}`, 'POST', { message });
    } catch (error) {
      console.error(`Failed to test provider ${provider}:`, error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      return await this.makeRequest('/health', 'GET');
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unhealthy', error: error.message };
    }
  }

  /**
   * Queue request for offline processing
   */
  async queueRequest(requestData) {
    const queuedRequest = {
      id: Date.now().toString(),
      ...requestData,
      timestamp: new Date().toISOString(),
    };

    this.requestQueue.push(queuedRequest);
    
    // Save queue to storage
    try {
      await AsyncStorage.setItem('openrouter_queue', JSON.stringify(this.requestQueue));
    } catch (error) {
      console.warn('Failed to save request queue:', error);
    }

    return {
      success: false,
      queued: true,
      queueId: queuedRequest.id,
      message: 'Request queued for when connection is restored',
    };
  }

  /**
   * Process queued requests when back online
   */
  async processQueuedRequests() {
    if (this.requestQueue.length === 0) return;

    console.log(`Processing ${this.requestQueue.length} queued requests...`);

    const results = [];
    const queue = [...this.requestQueue];
    this.requestQueue = [];

    for (const request of queue) {
      try {
        const result = await this.chatCompletion(request);
        results.push({ ...result, queueId: request.id });
      } catch (error) {
        console.error('Failed to process queued request:', error);
        results.push({
          success: false,
          error: error.message,
          queueId: request.id,
        });
      }
    }

    // Clear queue from storage
    try {
      await AsyncStorage.removeItem('openrouter_queue');
    } catch (error) {
      console.warn('Failed to clear request queue:', error);
    }

    return results;
  }

  /**
   * Make HTTP request with retry logic
   */
  async makeRequest(endpoint, method = 'GET', data = null, attempt = 1) {
    const url = `${API_CONFIG.baseUrl}${endpoint}`;
    
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Orchestra-AI-Mobile/1.0.0',
      },
      timeout: API_CONFIG.timeout,
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return await response.json();

    } catch (error) {
      console.error(`Request failed (attempt ${attempt}):`, error);

      // Retry logic
      if (attempt < API_CONFIG.retryAttempts) {
        await new Promise(resolve => 
          setTimeout(resolve, API_CONFIG.retryDelay * attempt)
        );
        return this.makeRequest(endpoint, method, data, attempt + 1);
      }

      throw error;
    }
  }

  /**
   * Update local statistics
   */
  async updateStats(response) {
    this.stats.totalRequests += 1;
    
    if (response.cost) {
      this.stats.totalCost += response.cost;
    }

    if (response.provider) {
      if (!this.stats.providerUsage[response.provider]) {
        this.stats.providerUsage[response.provider] = {
          requests: 0,
          totalCost: 0,
        };
      }
      
      this.stats.providerUsage[response.provider].requests += 1;
      if (response.cost) {
        this.stats.providerUsage[response.provider].totalCost += response.cost;
      }
    }

    await this.saveStatsToStorage();
  }

  /**
   * Clear all statistics
   */
  async clearStats() {
    this.stats = {
      totalRequests: 0,
      totalCost: 0,
      totalSavings: 0,
      providerUsage: {},
    };
    
    try {
      await AsyncStorage.removeItem('openrouter_stats');
    } catch (error) {
      console.warn('Failed to clear stats from storage:', error);
    }
  }

  /**
   * Get persona-specific recommendations
   */
  getPersonaRecommendations(persona) {
    const recommendations = {
      [PERSONAS.CHERRY]: {
        preferredUseCases: [
          USE_CASES.CASUAL_CHAT,
          USE_CASES.CREATIVE_WRITING,
          USE_CASES.QUICK_RESPONSE,
        ],
        defaultComplexity: COMPLEXITY.MEDIUM,
        defaultTemperature: 0.7,
        description: 'Cherry is great for casual conversations, creative tasks, and quick responses.',
      },
      [PERSONAS.SOPHIA]: {
        preferredUseCases: [
          USE_CASES.BUSINESS_ANALYSIS,
          USE_CASES.STRATEGIC_PLANNING,
          USE_CASES.RESEARCH_SEARCH,
        ],
        defaultComplexity: COMPLEXITY.HIGH,
        defaultTemperature: 0.3,
        description: 'Sophia excels at business analysis, strategic planning, and research.',
      },
      [PERSONAS.KAREN]: {
        preferredUseCases: [
          USE_CASES.MEDICAL_COMPLIANCE,
          USE_CASES.BUSINESS_ANALYSIS,
          USE_CASES.RESEARCH_SEARCH,
        ],
        defaultComplexity: COMPLEXITY.HIGH,
        defaultTemperature: 0.2,
        description: 'Karen specializes in medical compliance, healthcare analysis, and research.',
      },
    };

    return recommendations[persona] || recommendations[PERSONAS.CHERRY];
  }
}

// Export singleton instance
export default new OpenRouterService(); 