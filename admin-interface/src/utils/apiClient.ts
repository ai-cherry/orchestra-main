import { rateLimiter } from '../utils/rateLimiter';

interface RetryOptions {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
}

// Robust API client with retry and rate limiting.
// NOTE: For single-user, in-memory rate limiter is sufficient. For multi-user or distributed deployments, use a distributed rate limiter (e.g., Redis, Memcached).
// To upgrade, replace rateLimiter.execute with a distributed implementation.

class APIClient {
  private static instance: APIClient;
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  private constructor() {
    this.baseURL = process.env.NODE_ENV === 'production' 
      ? 'https://cherry-ai.me/api' 
      : 'http://localhost:3000/api';
    
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'User-Agent': 'Orchestra-AI/1.0'
    };
  }

  static getInstance(): APIClient {
    if (!APIClient.instance) {
      APIClient.instance = new APIClient();
    }
    return APIClient.instance;
  }

  async request<T>(
    service: string,
    endpoint: string,
    options: RequestInit = {},
    retryOptions: Partial<RetryOptions> = {}
  ): Promise<T> {
    const fullRetryOptions: RetryOptions = {
      maxAttempts: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffFactor: 2,
      ...retryOptions
    };

    return rateLimiter.execute(service, async () => {
      return this.executeWithRetry<T>(endpoint, options, fullRetryOptions);
    });
  }

  private async executeWithRetry<T>(
    endpoint: string,
    options: RequestInit,
    retryOptions: RetryOptions,
    attempt: number = 1
  ): Promise<T> {
    try {
      const url = endpoint.startsWith('http') ? endpoint : `${this.baseURL}${endpoint}`;
      
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers
        }
      });

      if (!response.ok) {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          endpoint
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (attempt >= retryOptions.maxAttempts) {
        throw error;
      }

      // Check if error is retryable
      if (this.isRetryableError(error)) {
        const delay = Math.min(
          retryOptions.baseDelay * Math.pow(retryOptions.backoffFactor, attempt - 1),
          retryOptions.maxDelay
        );

        console.warn(`Request failed (attempt ${attempt}/${retryOptions.maxAttempts}), retrying in ${delay}ms:`, error);
        
        await this.sleep(delay);
        return this.executeWithRetry<T>(endpoint, options, retryOptions, attempt + 1);
      }

      throw error;
    }
  }

  private isRetryableError(error: any): boolean {
    if (error instanceof APIError) {
      // Retry on server errors and rate limits
      return error.status >= 500 || error.status === 429;
    }

    // Retry on network errors
    return error.name === 'TypeError' || error.message.includes('fetch');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Convenience methods
  async get<T>(service: string, endpoint: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(service, endpoint, { method: 'GET', headers });
  }

  async post<T>(service: string, endpoint: string, data?: any, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(service, endpoint, {
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async put<T>(service: string, endpoint: string, data?: any, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(service, endpoint, {
      method: 'PUT',
      headers,
      body: data ? JSON.stringify(data) : undefined
    });
  }

  async delete<T>(service: string, endpoint: string, headers?: Record<string, string>): Promise<T> {
    return this.request<T>(service, endpoint, { method: 'DELETE', headers });
  }
}

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public endpoint: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export const apiClient = APIClient.getInstance();

