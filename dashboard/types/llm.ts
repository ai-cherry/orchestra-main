/**
 * TypeScript types for LLM Router integration
 * 
 * These types mirror the Python implementation to ensure
 * type safety when calling the LLM router from the frontend
 */

export enum UseCase {
  CODE_GENERATION = "code_generation",
  ARCHITECTURE_DESIGN = "architecture_design",
  DEBUGGING = "debugging",
  DOCUMENTATION = "documentation",
  CHAT_CONVERSATION = "chat_conversation",
  MEMORY_PROCESSING = "memory_processing",
  WORKFLOW_ORCHESTRATION = "workflow_orchestration",
  GENERAL_PURPOSE = "general_purpose"
}

export enum ModelTier {
  PREMIUM = "premium",
  STANDARD = "standard",
  ECONOMY = "economy"
}

export interface Message {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface LLMRequest {
  messages: string | Message[];
  useCase?: UseCase;
  tier?: ModelTier;
  modelOverride?: string;
  temperatureOverride?: number;
  maxTokensOverride?: number;
  systemPromptOverride?: string;
  stream?: boolean;
  cache?: boolean;
}

export interface LLMResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface LLMMetrics {
  requests: number;
  successes: number;
  failures: number;
  fallbacks: number;
  cache_hits: number;
  total_tokens: number;
  total_cost: number;
  success_rate: number;
  cache_hit_rate: number;
  average_tokens: number;
}

// API client for LLM router
export class LLMClient {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  async complete(request: LLMRequest): Promise<LLMResponse> {
    const response = await fetch(`${this.baseUrl}/llm/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`LLM request failed: ${response.statusText}`);
    }

    return response.json();
  }

  async generateCode(
    prompt: string,
    tier: ModelTier = ModelTier.STANDARD
  ): Promise<string> {
    const response = await this.complete({
      messages: prompt,
      useCase: UseCase.CODE_GENERATION,
      tier,
    });
    return response.choices[0].message.content;
  }

  async designArchitecture(
    requirements: string,
    tier: ModelTier = ModelTier.PREMIUM
  ): Promise<string> {
    const response = await this.complete({
      messages: requirements,
      useCase: UseCase.ARCHITECTURE_DESIGN,
      tier,
    });
    return response.choices[0].message.content;
  }

  async debugCode(code: string, error: string): Promise<string> {
    const prompt = `Debug this code:\n\n${code}\n\nError:\n${error}`;
    const response = await this.complete({
      messages: prompt,
      useCase: UseCase.DEBUGGING,
      tier: ModelTier.PREMIUM,
    });
    return response.choices[0].message.content;
  }

  async chat(
    message: string,
    history?: Message[],
    tier: ModelTier = ModelTier.STANDARD
  ): Promise<string> {
    const messages = history || [];
    messages.push({ role: "user", content: message });
    
    const response = await this.complete({
      messages,
      useCase: UseCase.CHAT_CONVERSATION,
      tier,
    });
    return response.choices[0].message.content;
  }

  async getMetrics(): Promise<LLMMetrics> {
    const response = await fetch(`${this.baseUrl}/llm/metrics`);
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: ${response.statusText}`);
    }
    return response.json();
  }
}

// Export singleton instance
export const llmClient = new LLMClient();