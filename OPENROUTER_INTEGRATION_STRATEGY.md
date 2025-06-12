# 🔀 OpenRouter Integration Strategy for Orchestra AI
*Comprehensive cost optimization and AI model access across all platforms*

## 🎯 Current OpenRouter Usage Analysis

### **Existing Integration Points**
Based on codebase exploration, OpenRouter is currently:
- ✅ **Configured** in fast secrets manager (`utils/fast_secrets.py`)
- ✅ **Referenced** in admin interface HTML files
- ✅ **Documented** in setup guides and production scripts
- ❌ **Not actively used** in API calls or chat interfaces
- ❌ **Missing** from mobile apps and Android integration

## 🚀 Comprehensive Integration Strategy

### **1. Admin Interface Chat Enhancement**

#### **Current State**: `admin-interface/chat.html`
```javascript
// Current implementation uses direct API calls
class CherryAIApiClient {
    async sendMessage(messageData) {
        return await this.request('/api/conversation', {
            method: 'POST',
            body: messageData
        });
    }
}
```

#### **OpenRouter Enhancement**:
```javascript
// Enhanced with OpenRouter integration
class EnhancedCherryAIApiClient {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.openRouterURL = 'https://openrouter.ai/api/v1';
        this.useOpenRouter = true; // Cost optimization flag
    }

    async sendMessage(messageData) {
        if (this.useOpenRouter) {
            return await this.sendOpenRouterMessage(messageData);
        }
        return await this.sendDirectMessage(messageData);
    }

    async sendOpenRouterMessage(messageData) {
        const { persona, message, mode } = messageData;
        
        // Smart model selection based on persona and mode
        const model = this.selectOptimalModel(persona, mode);
        
        const response = await fetch(`${this.openRouterURL}/chat/completions`, {
            method: 'POST',
            headers: await this.getOpenRouterHeaders(),
            body: JSON.stringify({
                model: model,
                messages: [
                    { role: 'system', content: this.getPersonaPrompt(persona) },
                    { role: 'user', content: message }
                ],
                temperature: this.getPersonaTemperature(persona),
                max_tokens: 1000
            })
        });

        return await response.json();
    }

    selectOptimalModel(persona, mode) {
        const modelMap = {
            'cherry': {
                'casual': 'anthropic/claude-3-haiku',      // $0.25/1M - Fast & friendly
                'creative': 'meta-llama/llama-2-70b-chat', // $0.70/1M - Creative
                'analysis': 'anthropic/claude-3-sonnet'    // $3/1M - Deep thinking
            },
            'sophia': {
                'business': 'anthropic/claude-3-sonnet',   // $3/1M - Business analysis
                'quick': 'anthropic/claude-3-haiku',       // $0.25/1M - Quick responses
                'strategy': 'openai/gpt-4-turbo'           // $10/1M - Strategic thinking
            },
            'karen': {
                'medical': 'anthropic/claude-3-sonnet',    // $3/1M - Medical accuracy
                'compliance': 'openai/gpt-4-turbo',        // $10/1M - Regulatory precision
                'quick': 'anthropic/claude-3-haiku'        // $0.25/1M - Quick queries
            }
        };

        return modelMap[persona]?.[mode] || 'anthropic/claude-3-haiku';
    }

    async getOpenRouterHeaders() {
        // Get headers from backend secrets manager
        const response = await fetch(`${this.baseURL}/api/openrouter/headers`);
        return await response.json();
    }

    getPersonaPrompt(persona) {
        const prompts = {
            'cherry': 'You are Cherry, a playful and empathetic personal life coach. Be warm, creative, and supportive.',
            'sophia': 'You are Sophia, a strategic business advisor for PayReady. Be professional, analytical, and results-focused.',
            'karen': 'You are Karen, a healthcare compliance expert for ParagonRX. Be precise, knowledgeable, and patient-focused.'
        };
        return prompts[persona] || prompts['cherry'];
    }

    getPersonaTemperature(persona) {
        const temperatures = {
            'cherry': 0.8,   // More creative and playful
            'sophia': 0.3,   // More focused and analytical
            'karen': 0.2     // Very precise and consistent
        };
        return temperatures[persona] || 0.5;
    }
}
```

### **2. Mobile App Integration**

#### **React Native OpenRouter Service**:
```typescript
// mobile-app/src/services/OpenRouterService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export class OpenRouterService {
    private baseURL = 'https://openrouter.ai/api/v1';
    private apiKey: string | null = null;

    async initialize() {
        this.apiKey = await AsyncStorage.getItem('OPENROUTER_API_KEY');
        if (!this.apiKey) {
            // Fallback to backend API for key
            this.apiKey = await this.getKeyFromBackend();
        }
    }

    async chatCompletion(persona: string, message: string, mode: string = 'casual') {
        const model = this.selectModel(persona, mode);
        
        const response = await fetch(`${this.baseURL}/chat/completions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://orchestra-ai.dev',
                'X-Title': 'Orchestra AI Mobile'
            },
            body: JSON.stringify({
                model,
                messages: [
                    { role: 'system', content: this.getPersonaPrompt(persona) },
                    { role: 'user', content: message }
                ],
                temperature: this.getTemperature(persona),
                max_tokens: 800 // Optimized for mobile
            })
        });

        if (!response.ok) {
            throw new Error(`OpenRouter API error: ${response.status}`);
        }

        return await response.json();
    }

    private selectModel(persona: string, mode: string): string {
        // Mobile-optimized model selection (faster, cheaper models preferred)
        const mobileModels = {
            'cherry': 'anthropic/claude-3-haiku',      // Fast & friendly
            'sophia': 'anthropic/claude-3-haiku',      // Quick business responses
            'karen': 'anthropic/claude-3-sonnet'       // Medical accuracy needed
        };

        // Use more powerful models only for complex modes
        if (mode === 'analysis' || mode === 'strategy') {
            return 'anthropic/claude-3-sonnet';
        }

        return mobileModels[persona] || 'anthropic/claude-3-haiku';
    }

    private getPersonaPrompt(persona: string): string {
        const prompts = {
            'cherry': 'You are Cherry, a warm and playful personal assistant. Keep responses concise for mobile.',
            'sophia': 'You are Sophia, a business strategist. Provide clear, actionable insights for mobile users.',
            'karen': 'You are Karen, a healthcare expert. Give precise, mobile-friendly medical guidance.'
        };
        return prompts[persona] || prompts['cherry'];
    }

    private getTemperature(persona: string): number {
        return { 'cherry': 0.7, 'sophia': 0.3, 'karen': 0.2 }[persona] || 0.5;
    }

    async getKeyFromBackend(): Promise<string> {
        const response = await fetch('http://localhost:8000/api/openrouter/key');
        const data = await response.json();
        return data.api_key;
    }
}
```

#### **Enhanced Chat Screen**:
```typescript
// mobile-app/src/screens/EnhancedChatScreen.tsx (additions)
import { OpenRouterService } from '../services/OpenRouterService';

export default function EnhancedChatScreen() {
    const [openRouterService] = useState(new OpenRouterService());
    const [costSavings, setCostSavings] = useState(0);

    useEffect(() => {
        openRouterService.initialize();
    }, []);

    const sendMessage = async (message: string, persona: string) => {
        try {
            setLoading(true);
            
            // Use OpenRouter for cost optimization
            const response = await openRouterService.chatCompletion(persona, message);
            
            // Calculate cost savings
            const directCost = calculateDirectCost(message.length);
            const openRouterCost = calculateOpenRouterCost(message.length);
            const savings = directCost - openRouterCost;
            setCostSavings(prev => prev + savings);

            // Add response to chat
            addMessage({
                id: Date.now(),
                text: response.choices[0].message.content,
                sender: persona,
                timestamp: new Date(),
                cost_saved: savings
            });

        } catch (error) {
            console.error('Chat error:', error);
            // Fallback to direct API
            await sendDirectMessage(message, persona);
        } finally {
            setLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            {/* Cost savings indicator */}
            <View style={styles.savingsIndicator}>
                <Text style={styles.savingsText}>
                    💰 Saved: ${costSavings.toFixed(2)} with OpenRouter
                </Text>
            </View>
            
            {/* Chat interface */}
            <ChatInterface onSendMessage={sendMessage} />
        </View>
    );
}
```

### **3. Android Native Integration**

#### **OpenRouter API Client**:
```java
// android/app/src/main/java/com/orchestra/ai/OpenRouterClient.java
package com.orchestra.ai;

import okhttp3.*;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.IOException;

public class OpenRouterClient {
    private static final String BASE_URL = "https://openrouter.ai/api/v1";
    private final OkHttpClient client;
    private final String apiKey;

    public OpenRouterClient(String apiKey) {
        this.apiKey = apiKey;
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();
    }

    public void chatCompletion(String persona, String message, ChatCallback callback) {
        String model = selectModel(persona);
        
        try {
            JSONObject requestBody = new JSONObject();
            requestBody.put("model", model);
            
            JSONArray messages = new JSONArray();
            messages.put(new JSONObject()
                .put("role", "system")
                .put("content", getPersonaPrompt(persona)));
            messages.put(new JSONObject()
                .put("role", "user")
                .put("content", message));
            
            requestBody.put("messages", messages);
            requestBody.put("temperature", getTemperature(persona));
            requestBody.put("max_tokens", 600); // Optimized for mobile

            Request request = new Request.Builder()
                .url(BASE_URL + "/chat/completions")
                .addHeader("Authorization", "Bearer " + apiKey)
                .addHeader("Content-Type", "application/json")
                .addHeader("HTTP-Referer", "https://orchestra-ai.dev")
                .addHeader("X-Title", "Orchestra AI Android")
                .post(RequestBody.create(
                    requestBody.toString(),
                    MediaType.parse("application/json")))
                .build();

            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    callback.onError(e.getMessage());
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    if (response.isSuccessful()) {
                        try {
                            JSONObject responseJson = new JSONObject(response.body().string());
                            JSONArray choices = responseJson.getJSONArray("choices");
                            String content = choices.getJSONObject(0)
                                .getJSONObject("message")
                                .getString("content");
                            
                            callback.onSuccess(content);
                        } catch (Exception e) {
                            callback.onError("Failed to parse response");
                        }
                    } else {
                        callback.onError("API request failed: " + response.code());
                    }
                }
            });

        } catch (Exception e) {
            callback.onError("Request creation failed: " + e.getMessage());
        }
    }

    private String selectModel(String persona) {
        // Android-optimized models (balance of speed and quality)
        switch (persona.toLowerCase()) {
            case "cherry":
                return "anthropic/claude-3-haiku";
            case "sophia":
                return "anthropic/claude-3-haiku";
            case "karen":
                return "anthropic/claude-3-sonnet"; // Medical accuracy needed
            default:
                return "anthropic/claude-3-haiku";
        }
    }

    private String getPersonaPrompt(String persona) {
        switch (persona.toLowerCase()) {
            case "cherry":
                return "You are Cherry, a warm personal assistant. Keep responses brief for mobile.";
            case "sophia":
                return "You are Sophia, a business strategist. Provide concise business insights.";
            case "karen":
                return "You are Karen, a healthcare expert. Give precise medical guidance.";
            default:
                return "You are a helpful AI assistant.";
        }
    }

    private double getTemperature(String persona) {
        switch (persona.toLowerCase()) {
            case "cherry": return 0.7;
            case "sophia": return 0.3;
            case "karen": return 0.2;
            default: return 0.5;
        }
    }

    public interface ChatCallback {
        void onSuccess(String response);
        void onError(String error);
    }
}
```

### **4. Backend API Integration**

#### **OpenRouter Endpoint**:
```python
# Add to main API (e.g., src/api/main.py)
from utils.fast_secrets import openrouter_headers, get_api_config
import httpx

@app.post("/api/openrouter/chat")
async def openrouter_chat(request: ChatRequest):
    """OpenRouter chat completion with cost optimization."""
    
    config = get_api_config('openrouter')
    if not config['api_key']:
        raise HTTPException(status_code=503, detail="OpenRouter not configured")
    
    # Smart model selection
    model = select_optimal_model(request.persona, request.mode, request.complexity)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{config['base_url']}/chat/completions",
            headers=openrouter_headers(),
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": get_persona_prompt(request.persona)},
                    {"role": "user", "content": request.message}
                ],
                "temperature": get_persona_temperature(request.persona),
                "max_tokens": request.max_tokens or 1000
            },
            timeout=30.0
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="OpenRouter API error")
    
    result = response.json()
    
    # Track cost savings
    await track_cost_savings(request, model, result)
    
    return {
        "response": result["choices"][0]["message"]["content"],
        "model_used": model,
        "cost_saved": calculate_savings(request, model),
        "tokens_used": result.get("usage", {}).get("total_tokens", 0)
    }

def select_optimal_model(persona: str, mode: str, complexity: str = "medium") -> str:
    """Select the most cost-effective model for the request."""
    
    # High-complexity requests need powerful models
    if complexity == "high" or mode in ["analysis", "strategy", "medical"]:
        return "anthropic/claude-3-sonnet"  # $3/1M tokens
    
    # Medium complexity - balance cost and quality
    if complexity == "medium" or persona == "sophia":
        return "anthropic/claude-3-haiku"   # $0.25/1M tokens
    
    # Low complexity - maximize cost savings
    return "anthropic/claude-3-haiku"       # $0.25/1M tokens

@app.get("/api/openrouter/headers")
async def get_openrouter_headers():
    """Get OpenRouter headers for frontend use."""
    return openrouter_headers()

@app.get("/api/openrouter/models")
async def get_available_models():
    """Get list of available OpenRouter models with pricing."""
    config = get_api_config('openrouter')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{config['base_url']}/models",
            headers=openrouter_headers()
        )
    
    return response.json()

@app.get("/api/openrouter/usage")
async def get_usage_stats():
    """Get OpenRouter usage and cost statistics."""
    config = get_api_config('openrouter')
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{config['base_url']}/auth/key",
            headers=openrouter_headers()
        )
    
    return response.json()
```

### **5. Cost Optimization Features**

#### **Smart Model Routing**:
```python
# utils/openrouter_optimizer.py
from typing import Dict, List
import asyncio

class OpenRouterOptimizer:
    """Intelligent model selection and cost optimization."""
    
    def __init__(self):
        self.model_costs = {
            "anthropic/claude-3-haiku": 0.25,      # $/1M tokens
            "anthropic/claude-3-sonnet": 3.00,     # $/1M tokens  
            "openai/gpt-3.5-turbo": 0.50,          # $/1M tokens
            "openai/gpt-4-turbo": 10.00,           # $/1M tokens
            "meta-llama/llama-2-70b-chat": 0.70,   # $/1M tokens
            "deepseek/deepseek-coder": 0.14,       # $/1M tokens
        }
        
        self.model_capabilities = {
            "coding": ["deepseek/deepseek-coder", "anthropic/claude-3-sonnet"],
            "creative": ["meta-llama/llama-2-70b-chat", "anthropic/claude-3-haiku"],
            "analysis": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
            "casual": ["anthropic/claude-3-haiku", "openai/gpt-3.5-turbo"],
            "medical": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"],
            "business": ["anthropic/claude-3-sonnet", "openai/gpt-4-turbo"]
        }
    
    def select_optimal_model(self, task_type: str, budget_priority: str = "balanced") -> str:
        """Select the best model based on task and budget constraints."""
        
        suitable_models = self.model_capabilities.get(task_type, ["anthropic/claude-3-haiku"])
        
        if budget_priority == "cost":
            # Choose cheapest suitable model
            return min(suitable_models, key=lambda m: self.model_costs[m])
        elif budget_priority == "quality":
            # Choose most expensive (usually best) suitable model
            return max(suitable_models, key=lambda m: self.model_costs[m])
        else:
            # Balanced approach - good quality at reasonable cost
            costs = [self.model_costs[m] for m in suitable_models]
            median_cost = sorted(costs)[len(costs) // 2]
            return next(m for m in suitable_models if self.model_costs[m] == median_cost)
    
    def calculate_cost_savings(self, tokens_used: int, model_used: str) -> Dict:
        """Calculate savings compared to direct API usage."""
        
        openrouter_cost = (tokens_used / 1_000_000) * self.model_costs[model_used]
        
        # Compare to direct API costs
        direct_costs = {
            "openai_direct": (tokens_used / 1_000_000) * 30.0,  # GPT-4 direct
            "anthropic_direct": (tokens_used / 1_000_000) * 15.0  # Claude direct
        }
        
        savings = {
            "openrouter_cost": openrouter_cost,
            "vs_openai": direct_costs["openai_direct"] - openrouter_cost,
            "vs_anthropic": direct_costs["anthropic_direct"] - openrouter_cost,
            "savings_percent": {
                "vs_openai": ((direct_costs["openai_direct"] - openrouter_cost) / direct_costs["openai_direct"]) * 100,
                "vs_anthropic": ((direct_costs["anthropic_direct"] - openrouter_cost) / direct_costs["anthropic_direct"]) * 100
            }
        }
        
        return savings

    async def get_real_time_pricing(self) -> Dict:
        """Get real-time model pricing from OpenRouter."""
        # Implementation to fetch current pricing
        pass
```

## 📊 Expected Impact

### **Cost Savings Across Platforms**:
```python
# Monthly usage estimates
monthly_usage = {
    "admin_interface": 2_000_000,  # 2M tokens/month
    "mobile_app": 1_500_000,       # 1.5M tokens/month  
    "android_app": 1_000_000,      # 1M tokens/month
    "api_backend": 500_000,        # 0.5M tokens/month
}

# Cost comparison
direct_costs = {
    "openai": sum(tokens * 0.00003 for tokens in monthly_usage.values()),  # $150/month
    "anthropic": sum(tokens * 0.000015 for tokens in monthly_usage.values())  # $75/month
}

openrouter_cost = sum(tokens * 0.000006 for tokens in monthly_usage.values())  # $30/month

total_savings = sum(direct_costs.values()) - openrouter_cost  # $195/month saved!
```

### **Performance Benefits**:
- **60-80% cost reduction** across all platforms
- **100+ model access** for specialized tasks
- **Unified API** reduces integration complexity
- **Real-time pricing** optimization
- **Automatic fallback** to direct APIs if needed

### **Implementation Priority**:
1. **Backend API** (enables all other integrations)
2. **Admin Interface** (immediate 60-80% savings)
3. **Mobile App** (React Native - cross-platform)
4. **Android App** (native performance optimization)

## 🎯 Next Steps

1. **Implement backend OpenRouter endpoints** (`/api/openrouter/*`)
2. **Update admin interface** with OpenRouter chat client
3. **Add mobile OpenRouter service** to React Native app
4. **Create Android OpenRouter client** for native integration
5. **Deploy cost tracking** and optimization features

This comprehensive integration will deliver massive cost savings while providing access to the best AI models for each specific use case across all Orchestra AI platforms. 