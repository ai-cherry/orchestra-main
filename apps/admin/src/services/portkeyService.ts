import APIConfigService from '../config/apiConfig';

class PortkeyService {
  private config = APIConfigService.getInstance().getPortkeyConfig();

  async sendMessage(
    message: string,
    persona: 'sophia' | 'karen' | 'cherry',
    context?: any[]
  ): Promise<any> {
    const personaConfig = this.getPersonaConfig(persona);
    
    try {
      const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json',
          'x-portkey-config': this.config.configId
        },
        body: JSON.stringify({
          model: personaConfig.model,
          messages: this.buildMessageHistory(message, context, personaConfig.systemPrompt),
          temperature: personaConfig.temperature,
          max_tokens: personaConfig.maxTokens,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`Portkey API error: ${response.status}`);
      }

      const data = await response.json();
      return {
        content: data.choices[0].message.content,
        usage: data.usage,
        model: data.model
      };
    } catch (error) {
      console.error('Portkey service error:', error);
      throw error;
    }
  }

  private getPersonaConfig(persona: string) {
    const configs = {
      sophia: {
        model: 'claude-3-5-sonnet-20241022',
        temperature: 0.1,
        maxTokens: 4000,
        systemPrompt: `You are Sophia, a business intelligence expert specializing in apartment technology, fintech, debt recovery, and proptech. 
        You provide data-driven insights, market analysis, and strategic business recommendations. 
        You can create presentations, reports, and proposals. Always ask clarifying questions when needed.
        Focus on ROI, market opportunities, and competitive positioning.`
      },
      karen: {
        model: 'claude-3-opus-20240229',
        temperature: 0.05,
        maxTokens: 4000,
        systemPrompt: `You are Karen, a clinical research expert with deep pharmaceutical and medical expertise.
        You specialize in clinical trials, drug development, FDA compliance, and medical literature analysis.
        You can create research reports, study protocols, and literature reviews. Always prioritize evidence-based medicine.
        Focus on statistical significance, methodology, and regulatory compliance.`
      },
      cherry: {
        model: 'gpt-4-turbo',
        temperature: 0.7,
        maxTokens: 4000,
        systemPrompt: `You are Cherry, a creative assistant with cross-domain knowledge and adaptive learning capabilities.
        You excel at creative content generation including songs, images, videos, stories, and innovative solutions.
        You learn from interactions across all personas and provide creative inspiration and artistic guidance.
        Focus on creativity, innovation, and cross-domain inspiration.`
      }
    };

    return configs[persona] || configs.cherry;
  }

  private buildMessageHistory(message: string, context: any[] = [], systemPrompt: string) {
    const messages = [
      { role: 'system', content: systemPrompt }
    ];

    // Add context from previous messages
    if (context && context.length > 0) {
      context.slice(-10).forEach(msg => {
        messages.push({
          role: msg.type === 'user' ? 'user' : 'assistant',
          content: msg.content
        });
      });
    }

    // Add current message
    messages.push({ role: 'user', content: message });

    return messages;
  }

  async streamMessage(
    message: string,
    persona: 'sophia' | 'karen' | 'cherry',
    context?: any[],
    onChunk?: (chunk: string) => void
  ): Promise<string> {
    const personaConfig = this.getPersonaConfig(persona);
    
    try {
      const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json',
          'x-portkey-config': this.config.configId
        },
        body: JSON.stringify({
          model: personaConfig.model,
          messages: this.buildMessageHistory(message, context, personaConfig.systemPrompt),
          temperature: personaConfig.temperature,
          max_tokens: personaConfig.maxTokens,
          stream: true
        })
      });

      if (!response.ok) {
        throw new Error(`Portkey API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;

              try {
                const parsed = JSON.parse(data);
                const content = parsed.choices?.[0]?.delta?.content;
                if (content) {
                  fullContent += content;
                  onChunk?.(content);
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
      }

      return fullContent;
    } catch (error) {
      console.error('Portkey streaming error:', error);
      throw error;
    }
  }
}

export default PortkeyService;

