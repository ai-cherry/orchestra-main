import Portkey from 'portkey-ai';
import { PORTKEY_CONFIG, getVirtualKey, isPortkeyConfigured } from '@/config/portkey.config';

interface ImageOptions {
  size?: '1024x1024' | '1792x1024' | '1024x1792';
  quality?: 'standard' | 'hd';
  style?: 'vivid' | 'natural';
  n?: number;
}

interface TextOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

export class PortkeyService {
  private client: Portkey;
  
  constructor() {
    if (!isPortkeyConfigured()) {
      throw new Error('Portkey is not properly configured. Please check your environment variables.');
    }
    
    this.client = new Portkey({
      apiKey: PORTKEY_CONFIG.apiKey,
      baseURL: PORTKEY_CONFIG.baseURL
    });
  }
  
  /**
   * Generate images using DALL-E 3 via OpenAI virtual key
   */
  async generateImage(prompt: string, options?: ImageOptions) {
    try {
      const response = await this.client.images.generate({
        prompt,
        model: 'dall-e-3',
        size: options?.size || '1024x1024',
        quality: options?.quality || 'standard',
        style: options?.style || 'vivid',
        n: options?.n || 1,
        virtualKey: getVirtualKey('openai')
      });
      
      return {
        success: true,
        data: response.data,
        usage: {
          prompt_tokens: prompt.length / 4, // Rough estimate
          total_tokens: prompt.length / 4
        }
      };
    } catch (error: any) {
      console.error('Image generation failed:', error);
      throw {
        code: error?.code || 'UNKNOWN_ERROR',
        message: error?.message || 'Failed to generate image',
        provider: 'openai'
      };
    }
  }
  
  /**
   * Generate text using various models
   */
  async generateText(prompt: string, options?: TextOptions) {
    const model = options?.model || PORTKEY_CONFIG.models.text.default;
    
    // Determine which virtual key to use based on model
    let virtualKey: string;
    if (model.includes('claude')) {
      virtualKey = getVirtualKey('anthropic');
    } else if (model.includes('gemini')) {
      virtualKey = getVirtualKey('gemini');
    } else if (model.includes('pplx')) {
      virtualKey = getVirtualKey('perplexity');
    } else if (model.includes('deepseek')) {
      virtualKey = getVirtualKey('deepseek');
    } else {
      virtualKey = getVirtualKey('openai'); // Default to OpenAI
    }
    
    try {
      const messages = [
        ...(options?.systemPrompt ? [{ role: 'system' as const, content: options.systemPrompt }] : []),
        { role: 'user' as const, content: prompt }
      ];
      
      const response = await this.client.chat.completions.create({
        model,
        messages,
        temperature: options?.temperature || 0.7,
        max_tokens: options?.maxTokens || 1000,
        virtualKey
      });
      
      const content = response.choices?.[0]?.message?.content || '';
      
      return {
        success: true,
        data: content,
        usage: response.usage,
        model: response.model
      };
    } catch (error: any) {
      console.error('Text generation failed:', error);
      throw {
        code: error?.code || 'UNKNOWN_ERROR',
        message: error?.message || 'Failed to generate text',
        provider: virtualKey
      };
    }
  }
  
  /**
   * Generate code using specialized models
   */
  async generateCode(prompt: string, language?: string) {
    const model = PORTKEY_CONFIG.models.code.default;
    const systemPrompt = `You are an expert ${language || 'programming'} assistant. Generate clean, efficient, and well-documented code.`;
    
    return this.generateText(prompt, {
      model,
      systemPrompt,
      temperature: 0.3, // Lower temperature for more deterministic code
      maxTokens: 2000
    });
  }
  
  /**
   * Perform search-enhanced generation using Perplexity
   */
  async searchAndGenerate(query: string) {
    return this.generateText(query, {
      model: PORTKEY_CONFIG.models.text.search,
      temperature: 0.5,
      maxTokens: 1500
    });
  }
  
  /**
   * Check API usage and limits
   */
  async checkUsage(service: string) {
    // This would typically call a Portkey endpoint to check usage
    // For now, return mock data
    const dailyLimits = PORTKEY_CONFIG.costLimits.daily as Record<string, number>;
    const limit = dailyLimits[service] || 1000;
    
    return {
      service,
      used: Math.floor(Math.random() * 500),
      limit,
      remaining: 500,
      resetAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    };
  }
  
  /**
   * List available models for a provider
   */
  async listModels(provider: keyof typeof PORTKEY_CONFIG.virtualKeys) {
    const virtualKey = getVirtualKey(provider);
    
    try {
      const response = await this.client.models.list({ virtualKey });
      return response.data;
    } catch (error) {
      console.error('Failed to list models:', error);
      return [];
    }
  }
}

// Singleton instance
let portkeyInstance: PortkeyService | null = null;

export const getPortkeyService = (): PortkeyService => {
  if (!portkeyInstance) {
    portkeyInstance = new PortkeyService();
  }
  return portkeyInstance;
}; 