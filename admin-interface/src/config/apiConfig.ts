interface APIConfig {
  portkey: {
    apiKey: string;
    configId: string;
    baseUrl: string;
  };
  search: {
    brave: {
      apiKey: string;
      endpoint: string;
    };
    perplexity: {
      apiKey: string;
      endpoint: string;
    };
    exa: {
      apiKey: string;
      endpoint: string;
    };
    tavily: {
      apiKey: string;
      endpoint: string;
    };
    apollo: {
      apiKey: string;
      endpoint: string;
    };
  };
  voice: {
    elevenLabs: {
      apiKey: string;
      baseUrl: string;
    };
  };
  data: {
    airbyte: {
      token: string;
      baseUrl: string;
    };
  };
  presentation: {
    slideSpeak: {
      apiKey: string;
      baseUrl: string;
    };
  };
  notion: {
    apiKey: string;
    databaseId: string;
    baseUrl: string;
  };
  app: {
    environment: string;
    apiBaseUrl: string;
    websocketUrl: string;
  };
}

class APIConfigService {
  private static instance: APIConfigService;
  private config: APIConfig;

  private constructor() {
    this.validateEnvironment();
    this.config = this.loadConfig();
  }

  public static getInstance(): APIConfigService {
    if (!APIConfigService.instance) {
      APIConfigService.instance = new APIConfigService();
    }
    return APIConfigService.instance;
  }

  private validateEnvironment(): void {
    const requiredVars = [
      'VITE_PORTKEY_API_KEY',
      'VITE_PORTKEY_CONFIG_ID',
      'VITE_BRAVE_API_KEY',
      'VITE_PERPLEXITY_API_KEY'
    ];

    const missing = requiredVars.filter(varName => !import.meta.env[varName]);
    
    if (missing.length > 0) {
      console.error('Missing required environment variables:', missing);
      // In development, we'll warn but not throw
      if (import.meta.env.PROD) {
        throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
      }
    }
  }

  private loadConfig(): APIConfig {
    return {
      portkey: {
        apiKey: import.meta.env.VITE_PORTKEY_API_KEY || '',
        configId: import.meta.env.VITE_PORTKEY_CONFIG_ID || '',
        baseUrl: 'https://api.portkey.ai/v1'
      },
      search: {
        brave: {
          apiKey: import.meta.env.VITE_BRAVE_API_KEY || '',
          endpoint: 'https://api.search.brave.com/res/v1/web/search'
        },
        perplexity: {
          apiKey: import.meta.env.VITE_PERPLEXITY_API_KEY || '',
          endpoint: 'https://api.perplexity.ai/chat/completions'
        },
        exa: {
          apiKey: import.meta.env.VITE_EXA_API_KEY || '',
          endpoint: 'https://api.exa.ai/search'
        },
        tavily: {
          apiKey: import.meta.env.VITE_TAVILY_API_KEY || '',
          endpoint: 'https://api.tavily.com/search'
        },
        apollo: {
          apiKey: import.meta.env.VITE_APOLLO_API_KEY || '',
          endpoint: 'https://api.apollo.io/v1/mixed_people/search'
        }
      },
      voice: {
        elevenLabs: {
          apiKey: import.meta.env.VITE_ELEVEN_LABS_API_KEY || '',
          baseUrl: 'https://api.elevenlabs.io/v1'
        }
      },
      data: {
        airbyte: {
          token: import.meta.env.VITE_AIRBYTE_TOKEN || '',
          baseUrl: 'https://api.airbyte.com/v1'
        }
      },
      presentation: {
        slideSpeak: {
          apiKey: import.meta.env.VITE_SLIDESPEAK_API_KEY || '',
          baseUrl: 'https://api.slidespeak.co/v1'
        }
      },
      notion: {
        apiKey: import.meta.env.VITE_NOTION_API_KEY || '',
        databaseId: import.meta.env.VITE_NOTION_DATABASE_ID || '',
        baseUrl: 'https://api.notion.com/v1'
      },
      app: {
        environment: import.meta.env.VITE_APP_ENV || 'development',
        apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001',
        websocketUrl: import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:3001'
      }
    };
  }

  public getConfig(): APIConfig {
    return this.config;
  }

  public getPortkeyConfig() {
    return this.config.portkey;
  }

  public getSearchConfig() {
    return this.config.search;
  }

  public getVoiceConfig() {
    return this.config.voice;
  }

  public getDataConfig() {
    return this.config.data;
  }

  public getPresentationConfig() {
    return this.config.presentation;
  }

  public getNotionConfig() {
    return this.config.notion;
  }

  public getAppConfig() {
    return this.config.app;
  }

  // Helper method to check if a service is configured
  public isServiceConfigured(service: string): boolean {
    switch (service) {
      case 'portkey':
        return !!this.config.portkey.apiKey;
      case 'brave':
        return !!this.config.search.brave.apiKey;
      case 'perplexity':
        return !!this.config.search.perplexity.apiKey;
      case 'exa':
        return !!this.config.search.exa.apiKey;
      case 'tavily':
        return !!this.config.search.tavily.apiKey;
      case 'apollo':
        return !!this.config.search.apollo.apiKey;
      case 'elevenLabs':
        return !!this.config.voice.elevenLabs.apiKey;
      case 'airbyte':
        return !!this.config.data.airbyte.token;
      case 'slideSpeak':
        return !!this.config.presentation.slideSpeak.apiKey;
      case 'notion':
        return !!this.config.notion.apiKey;
      default:
        return false;
    }
  }
}

export default APIConfigService;
export type { APIConfig }; 