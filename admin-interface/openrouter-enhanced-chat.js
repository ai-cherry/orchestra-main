/**
 * OpenRouter Enhanced Chat Client for Orchestra AI Admin Interface
 * Provides cost-optimized AI interactions with smart model selection
 */

class OpenRouterChatClient {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.openRouterURL = 'https://openrouter.ai/api/v1';
        this.useOpenRouter = true;
        this.costSavings = 0;
        this.totalTokensUsed = 0;
        
        // Model pricing (per 1M tokens)
        this.modelPricing = {
            'anthropic/claude-3-haiku': 0.25,
            'anthropic/claude-3-sonnet': 3.00,
            'openai/gpt-3.5-turbo': 0.50,
            'openai/gpt-4-turbo': 10.00,
            'meta-llama/llama-2-70b-chat': 0.70,
            'deepseek/deepseek-coder': 0.14
        };
        
        // Direct API pricing for comparison
        this.directPricing = {
            'openai': 30.00,    // GPT-4 direct
            'anthropic': 15.00  // Claude direct
        };
    }

    /**
     * Send message with OpenRouter optimization
     */
    async sendMessage(messageData) {
        const startTime = Date.now();
        
        try {
            if (this.useOpenRouter) {
                const result = await this.sendOpenRouterMessage(messageData);
                this.updateCostMetrics(result);
                return result;
            } else {
                return await this.sendDirectMessage(messageData);
            }
        } catch (error) {
            console.error('OpenRouter failed, falling back to direct API:', error);
            return await this.sendDirectMessage(messageData);
        } finally {
            const responseTime = Date.now() - startTime;
            this.updateResponseTimeMetrics(responseTime);
        }
    }

    /**
     * OpenRouter message handling with smart model selection
     */
    async sendOpenRouterMessage(messageData) {
        const { persona, message, mode = 'casual', complexity = 'medium' } = messageData;
        
        // Select optimal model based on context
        const model = this.selectOptimalModel(persona, mode, complexity);
        
        // Get OpenRouter headers from backend
        const headers = await this.getOpenRouterHeaders();
        
        const requestBody = {
            model: model,
            messages: [
                { 
                    role: 'system', 
                    content: this.getPersonaPrompt(persona, mode) 
                },
                { 
                    role: 'user', 
                    content: message 
                }
            ],
            temperature: this.getPersonaTemperature(persona, mode),
            max_tokens: this.getOptimalTokenLimit(mode),
            stream: false
        };

        const response = await fetch(`${this.openRouterURL}/chat/completions`, {
            method: 'POST',
            headers: {
                ...headers,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`OpenRouter API error: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        
        return {
            content: result.choices[0].message.content,
            model_used: model,
            tokens_used: result.usage?.total_tokens || 0,
            cost: this.calculateCost(result.usage?.total_tokens || 0, model),
            savings: this.calculateSavings(result.usage?.total_tokens || 0, model),
            response_time: Date.now() - Date.now() // Will be calculated by caller
        };
    }

    /**
     * Smart model selection based on persona, mode, and complexity
     */
    selectOptimalModel(persona, mode, complexity) {
        // High complexity or specialized tasks need powerful models
        if (complexity === 'high' || mode === 'analysis' || mode === 'strategy') {
            if (persona === 'karen' && mode === 'medical') {
                return 'openai/gpt-4-turbo'; // Medical accuracy is critical
            }
            return 'anthropic/claude-3-sonnet'; // Good balance of quality and cost
        }

        // Coding tasks get specialized model
        if (mode === 'coding' || mode === 'development') {
            return 'deepseek/deepseek-coder'; // Cheapest and best for code
        }

        // Creative tasks
        if (mode === 'creative' || mode === 'writing') {
            return 'meta-llama/llama-2-70b-chat'; // Good for creative tasks
        }

        // Default to fast, cheap, high-quality model
        return 'anthropic/claude-3-haiku';
    }

    /**
     * Get persona-specific prompts
     */
    getPersonaPrompt(persona, mode) {
        const basePrompts = {
            'cherry': 'You are Cherry, a warm, playful, and empathetic personal life coach. Be supportive, creative, and engaging.',
            'sophia': 'You are Sophia, a strategic business advisor for PayReady. Be professional, analytical, and results-focused.',
            'karen': 'You are Karen, a healthcare compliance expert for ParagonRX. Be precise, knowledgeable, and patient-focused.'
        };

        const modeModifiers = {
            'casual': 'Keep the conversation light and friendly.',
            'analysis': 'Provide detailed analysis and insights.',
            'strategy': 'Focus on strategic thinking and planning.',
            'creative': 'Be imaginative and think outside the box.',
            'medical': 'Ensure medical accuracy and compliance.',
            'coding': 'Focus on clean, efficient code solutions.'
        };

        const basePrompt = basePrompts[persona] || basePrompts['cherry'];
        const modifier = modeModifiers[mode] || '';
        
        return `${basePrompt} ${modifier}`.trim();
    }

    /**
     * Get persona-specific temperature settings
     */
    getPersonaTemperature(persona, mode) {
        const baseTemperatures = {
            'cherry': 0.8,   // More creative and playful
            'sophia': 0.3,   // More focused and analytical
            'karen': 0.2     // Very precise and consistent
        };

        const modeAdjustments = {
            'creative': 0.3,   // Increase creativity
            'analysis': -0.2,  // Decrease for precision
            'medical': -0.3,   // Very precise for medical
            'coding': -0.2     // Precise for code
        };

        const baseTemp = baseTemperatures[persona] || 0.5;
        const adjustment = modeAdjustments[mode] || 0;
        
        return Math.max(0.1, Math.min(1.0, baseTemp + adjustment));
    }

    /**
     * Get optimal token limits based on mode
     */
    getOptimalTokenLimit(mode) {
        const tokenLimits = {
            'casual': 500,     // Short responses
            'analysis': 1500,  // Detailed analysis
            'strategy': 1200,  // Strategic insights
            'creative': 1000,  // Creative content
            'medical': 800,    // Precise medical info
            'coding': 1200     // Code with explanations
        };

        return tokenLimits[mode] || 800;
    }

    /**
     * Get OpenRouter headers from backend
     */
    async getOpenRouterHeaders() {
        try {
            const response = await fetch(`${this.baseURL}/api/openrouter/headers`);
            if (!response.ok) {
                throw new Error('Failed to get OpenRouter headers');
            }
            return await response.json();
        } catch (error) {
            console.error('Error getting OpenRouter headers:', error);
            // Fallback headers (will need API key from environment)
            return {
                'Authorization': 'Bearer ' + (localStorage.getItem('openrouter_key') || ''),
                'HTTP-Referer': 'https://orchestra-ai.dev',
                'X-Title': 'Orchestra AI Admin'
            };
        }
    }

    /**
     * Calculate cost for tokens used
     */
    calculateCost(tokensUsed, model) {
        const pricePerMillion = this.modelPricing[model] || 1.0;
        return (tokensUsed / 1_000_000) * pricePerMillion;
    }

    /**
     * Calculate savings compared to direct API
     */
    calculateSavings(tokensUsed, model) {
        const openRouterCost = this.calculateCost(tokensUsed, model);
        const directCost = (tokensUsed / 1_000_000) * this.directPricing.openai; // Compare to most expensive
        
        return {
            amount: directCost - openRouterCost,
            percentage: ((directCost - openRouterCost) / directCost) * 100
        };
    }

    /**
     * Update cost tracking metrics
     */
    updateCostMetrics(result) {
        this.totalTokensUsed += result.tokens_used;
        this.costSavings += result.savings.amount;
        
        // Update UI elements
        this.updateCostDisplay();
    }

    /**
     * Update response time metrics
     */
    updateResponseTimeMetrics(responseTime) {
        // Update response time display
        const responseTimeElement = document.getElementById('responseTime');
        if (responseTimeElement) {
            responseTimeElement.textContent = `${responseTime}ms`;
        }
    }

    /**
     * Update cost savings display
     */
    updateCostDisplay() {
        const savingsElement = document.getElementById('costSavings');
        const tokensElement = document.getElementById('totalTokens');
        
        if (savingsElement) {
            savingsElement.textContent = `$${this.costSavings.toFixed(4)}`;
        }
        
        if (tokensElement) {
            tokensElement.textContent = this.totalTokensUsed.toLocaleString();
        }
    }

    /**
     * Fallback to direct API
     */
    async sendDirectMessage(messageData) {
        const response = await fetch(`${this.baseURL}/api/conversation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('cherry_ai_token')}`
            },
            body: JSON.stringify(messageData)
        });

        if (!response.ok) {
            throw new Error(`Direct API error: ${response.status}`);
        }

        const result = await response.json();
        
        return {
            content: result.response || result.message,
            model_used: 'direct_api',
            tokens_used: 0,
            cost: 0,
            savings: { amount: 0, percentage: 0 }
        };
    }

    /**
     * Get available models from OpenRouter
     */
    async getAvailableModels() {
        try {
            const headers = await this.getOpenRouterHeaders();
            const response = await fetch(`${this.openRouterURL}/models`, {
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch models');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching models:', error);
            return { data: [] };
        }
    }

    /**
     * Get usage statistics
     */
    async getUsageStats() {
        try {
            const headers = await this.getOpenRouterHeaders();
            const response = await fetch(`${this.openRouterURL}/auth/key`, {
                headers: headers
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch usage stats');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching usage stats:', error);
            return null;
        }
    }

    /**
     * Toggle between OpenRouter and direct API
     */
    toggleOpenRouter(enabled) {
        this.useOpenRouter = enabled;
        
        // Update UI indicator
        const indicator = document.getElementById('openRouterStatus');
        if (indicator) {
            indicator.textContent = enabled ? '🔀 OpenRouter' : '🔗 Direct API';
            indicator.className = enabled ? 'status-openrouter' : 'status-direct';
        }
    }

    /**
     * Get current session statistics
     */
    getSessionStats() {
        return {
            totalTokensUsed: this.totalTokensUsed,
            costSavings: this.costSavings,
            useOpenRouter: this.useOpenRouter,
            averageSavingsPercentage: this.costSavings > 0 ? 
                (this.costSavings / (this.totalTokensUsed / 1_000_000 * this.directPricing.openai)) * 100 : 0
        };
    }
}

// Initialize global OpenRouter client
window.openRouterClient = new OpenRouterChatClient();

// Enhanced message sending function for chat interface
async function sendEnhancedMessage(persona, message, mode = 'casual') {
    const messageData = {
        persona: persona,
        message: message,
        mode: mode,
        complexity: detectComplexity(message),
        timestamp: new Date().toISOString()
    };

    try {
        // Show typing indicator
        showTypingIndicator(true);
        
        // Send message via OpenRouter
        const result = await window.openRouterClient.sendMessage(messageData);
        
        // Add message to chat
        addMessageToChat({
            sender: persona,
            content: result.content,
            model: result.model_used,
            tokens: result.tokens_used,
            cost: result.cost,
            savings: result.savings,
            timestamp: new Date()
        });

        return result;
        
    } catch (error) {
        console.error('Enhanced message sending failed:', error);
        
        // Add error message to chat
        addMessageToChat({
            sender: 'system',
            content: 'Sorry, I encountered an error. Please try again.',
            error: true,
            timestamp: new Date()
        });
        
        throw error;
        
    } finally {
        showTypingIndicator(false);
    }
}

// Utility function to detect message complexity
function detectComplexity(message) {
    const complexKeywords = ['analyze', 'strategy', 'detailed', 'comprehensive', 'explain in depth'];
    const simpleKeywords = ['hi', 'hello', 'thanks', 'yes', 'no'];
    
    const lowerMessage = message.toLowerCase();
    
    if (complexKeywords.some(keyword => lowerMessage.includes(keyword))) {
        return 'high';
    }
    
    if (simpleKeywords.some(keyword => lowerMessage.includes(keyword)) || message.length < 50) {
        return 'low';
    }
    
    return 'medium';
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { OpenRouterChatClient, sendEnhancedMessage };
} 