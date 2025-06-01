/**
 * Portkey Configuration
 * Maps virtual keys to their respective AI services
 */

export const PORTKEY_CONFIG = {
  baseURL: process.env.PORTKEY_BASE_URL || 'https://api.portkey.ai/v1',
  apiKey: process.env.PORTKEY_API_KEY || '',
  
  // Virtual key mappings from your Portkey account
  virtualKeys: {
    // OpenAI (GPT-4, DALL-E 3)
    openai: process.env.PORTKEY_OPENAI_VIRTUAL_KEY || 'openai-api-key-345cc9',
    
    // Anthropic (Claude)
    anthropic: process.env.PORTKEY_ANTHROPIC_VIRTUAL_KEY || 'anthropic-api-k-6feca8',
    
    // Google (Gemini)
    gemini: process.env.PORTKEY_GEMINI_VIRTUAL_KEY || 'gemini-api-key-1ea5a2',
    
    // Perplexity (Search-enhanced)
    perplexity: process.env.PORTKEY_PERPLEXITY_VIRTUAL_KEY || 'perplexity-api-015025',
    
    // DeepSeek (Code generation)
    deepseek: 'deepseek-api-ke-e7859b',
    
    // X.AI (Grok)
    xai: 'xai-api-key-a760a5',
    
    // Together AI (Open source models)
    together: 'together-ai-670469',
    
    // OpenRouter (Model routing)
    openrouter: 'openrouter-api-15df95'
  },
  
  // Model mappings for specific use cases
  models: {
    // Text generation
    text: {
      default: 'gpt-4-turbo-preview',
      fast: 'gpt-3.5-turbo',
      advanced: 'claude-3-opus-20240229',
      search: 'pplx-70b-online'
    },
    
    // Image generation
    image: {
      default: 'dall-e-3',
      quality: 'dall-e-3-hd'
    },
    
    // Code generation
    code: {
      default: 'deepseek-coder-33b',
      fast: 'codellama-34b',
      review: 'claude-3-opus-20240229'
    }
  },
  
  // Cost limits per model
  costLimits: {
    daily: {
      'dall-e-3': parseInt(process.env.MAX_DALLE_REQUESTS_PER_DAY || '1000'),
      'gpt-4': parseInt(process.env.MAX_GPT4_TOKENS_PER_DAY || '1000000')
    },
    threshold: parseFloat(process.env.COST_ALERT_THRESHOLD || '0.8')
  }
};

// Helper function to get the appropriate virtual key for a provider
export const getVirtualKey = (provider: keyof typeof PORTKEY_CONFIG.virtualKeys): string => {
  const key = PORTKEY_CONFIG.virtualKeys[provider];
  if (!key) {
    throw new Error(`No virtual key configured for provider: ${provider}`);
  }
  return key;
};

// Helper function to check if Portkey is properly configured
export const isPortkeyConfigured = (): boolean => {
  return !!(PORTKEY_CONFIG.apiKey && PORTKEY_CONFIG.baseURL);
}; 