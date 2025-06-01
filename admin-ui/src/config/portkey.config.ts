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
    
    // OpenRouter (Model routing - 300+ models)
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

// OpenRouter Model Catalog - Organized by use case
export const OPENROUTER_MODELS = {
  // Fast & Affordable Models
  fast: [
    { id: 'mistralai/mixtral-8x7b-instruct', name: 'Mixtral 8x7B', cost: 0.0006, speed: 'fast' },
    { id: 'meta-llama/llama-3-70b-instruct', name: 'Llama 3 70B', cost: 0.0008, speed: 'fast' },
    { id: 'google/gemma-7b-it', name: 'Gemma 7B', cost: 0.0001, speed: 'very fast' },
    { id: 'mistralai/mistral-7b-instruct', name: 'Mistral 7B', cost: 0.0002, speed: 'very fast' }
  ],
  
  // Balanced Performance Models
  balanced: [
    { id: 'anthropic/claude-3-haiku', name: 'Claude 3 Haiku', cost: 0.0025, speed: 'fast' },
    { id: 'openai/gpt-3.5-turbo', name: 'GPT-3.5 Turbo', cost: 0.002, speed: 'fast' },
    { id: 'perplexity/sonar-medium-online', name: 'Perplexity Sonar', cost: 0.006, speed: 'medium' },
    { id: 'deepseek/deepseek-chat', name: 'DeepSeek Chat', cost: 0.001, speed: 'fast' }
  ],
  
  // Premium Models
  premium: [
    { id: 'openai/gpt-4-turbo', name: 'GPT-4 Turbo', cost: 0.02, speed: 'medium' },
    { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus', cost: 0.06, speed: 'slow' },
    { id: 'google/gemini-pro-1.5', name: 'Gemini Pro 1.5', cost: 0.01, speed: 'medium' },
    { id: 'openai/gpt-4o', name: 'GPT-4o', cost: 0.015, speed: 'fast' }
  ],
  
  // Specialized Models
  specialized: {
    code: [
      { id: 'deepseek/deepseek-coder-33b-instruct', name: 'DeepSeek Coder 33B', cost: 0.008 },
      { id: 'phind/phind-codellama-34b-v2', name: 'Phind CodeLlama 34B', cost: 0.01 },
      { id: 'wizardlm/wizardcoder-33b', name: 'WizardCoder 33B', cost: 0.008 }
    ],
    creative: [
      { id: 'openai/gpt-4o', name: 'GPT-4o Creative', cost: 0.015 },
      { id: 'anthropic/claude-3-sonnet', name: 'Claude 3 Sonnet', cost: 0.02 },
      { id: 'meta-llama/llama-3-70b-instruct', name: 'Llama 3 Creative', cost: 0.0008 }
    ],
    research: [
      { id: 'perplexity/sonar-large-online', name: 'Perplexity Large', cost: 0.01 },
      { id: 'anthropic/claude-3-opus', name: 'Claude 3 Opus Research', cost: 0.06 },
      { id: 'openai/gpt-4-turbo', name: 'GPT-4 Turbo Research', cost: 0.02 }
    ]
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

// Helper function to get OpenRouter models by category
export const getOpenRouterModels = (category?: keyof typeof OPENROUTER_MODELS.specialized) => {
  if (category && OPENROUTER_MODELS.specialized[category]) {
    return OPENROUTER_MODELS.specialized[category];
  }
  return [
    ...OPENROUTER_MODELS.fast,
    ...OPENROUTER_MODELS.balanced,
    ...OPENROUTER_MODELS.premium
  ];
}; 