// Update the existing APIConfigService to include new integrations

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
  // New integrations
  linear: {
    apiKey: string;
    endpoint: string;
  };
  github: {
    token: string;
    endpoint: string;
  };
  asana: {
    accessToken: string;
    baseUrl: string;
  };
  ml: {
    apiKey: string;
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
      throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
  }

  private loadConfig(): APIConfig {
    return {
      portkey: {
        apiKey: import.meta.env.VITE_PORTKEY_API_KEY,
        configId: import.meta.env.VITE_PORTKEY_CONFIG_ID,
        baseUrl: 'https://api.portkey.ai/v1'
      },
      search: {
        brave: {
          apiKey: import.meta.env.VITE_BRAVE_API_KEY,
          endpoint: 'https://api.search.brave.com/res/v1/web/search'
        },
        perplexity: {
          apiKey: import.meta.env.VITE_PERPLEXITY_API_KEY,
          endpoint: 'https://api.perplexity.ai/chat/completions'
        }
      },
      voice: {
        elevenLabs: {
          apiKey: import.meta.env.VITE_ELEVEN_LABS_API_KEY,
          baseUrl: 'https://api.elevenlabs.io/v1'
        }
      },
      data: {
        airbyte: {
          token: import.meta.env.VITE_AIRBYTE_TOKEN,
          baseUrl: 'https://api.airbyte.com/v1'
        }
      },
      presentation: {
        slideSpeak: {
          apiKey: import.meta.env.VITE_SLIDESPEAK_API_KEY,
          baseUrl: 'https://api.slidespeak.co/v1'
        }
      },
      notion: {
        apiKey: import.meta.env.VITE_NOTION_API_KEY,
        databaseId: import.meta.env.VITE_NOTION_DATABASE_ID,
        baseUrl: 'https://api.notion.com/v1'
      },
      linear: {
        apiKey: import.meta.env.VITE_LINEAR_API_KEY,
        endpoint: 'https://api.linear.app/graphql'
      },
      github: {
        token: import.meta.env.VITE_GITHUB_TOKEN,
        endpoint: 'https://api.github.com/graphql'
      },
      asana: {
        accessToken: import.meta.env.VITE_ASANA_ACCESS_TOKEN,
        baseUrl: 'https://app.asana.com/api/1.0'
      },
      ml: {
        apiKey: import.meta.env.VITE_ML_API_KEY,
        baseUrl: import.meta.env.VITE_ML_BASE_URL || 'https://api.orchestra-ml.com/v1'
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

  public getLinearConfig() {
    return this.config.linear;
  }

  public getGitHubConfig() {
    return this.config.github;
  }

  public getAsanaConfig() {
    return this.config.asana;
  }

  public getMLConfig() {
    return this.config.ml;
  }

  public getAppConfig() {
    return this.config.app;
  }
}

export default APIConfigService;
export type { APIConfig };

