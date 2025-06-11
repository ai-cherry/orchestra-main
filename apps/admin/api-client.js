/**
 * Cherry AI Admin Interface API Client
 * Handles all communication with the backend API
 */

class CherryAIApiClient {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.token = localStorage.getItem('cherry_ai_token');
        this.isLoading = false;
    }

    /**
     * Generic API request method
     */
    async request(endpoint, options = {}) {
        this.isLoading = true;
        
        try {
            const url = `${this.baseURL}${endpoint}`;
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Add authorization header if token exists
            if (this.token) {
                headers['Authorization'] = `Bearer ${this.token}`;
            }

            const config = {
                method: options.method || 'GET',
                headers,
                ...options
            };

            if (options.body && config.method !== 'GET') {
                config.body = JSON.stringify(options.body);
            }

            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Request failed for ${endpoint}:`, error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Authentication methods
     */
    async login(credentials) {
        try {
            const response = await this.request('/auth/login', {
                method: 'POST',
                body: credentials
            });

            this.token = response.access_token;
            localStorage.setItem('cherry_ai_token', this.token);
            localStorage.setItem('cherry_ai_user', JSON.stringify(response.user));
            
            return response;
        } catch (error) {
            throw new Error(`Login failed: ${error.message}`);
        }
    }

    async register(userData) {
        try {
            const response = await this.request('/auth/register', {
                method: 'POST',
                body: userData
            });
            
            return response;
        } catch (error) {
            throw new Error(`Registration failed: ${error.message}`);
        }
    }

    async getCurrentUser() {
        try {
            return await this.request('/auth/me');
        } catch (error) {
            throw new Error(`Failed to get user info: ${error.message}`);
        }
    }

    logout() {
        this.token = null;
        localStorage.removeItem('cherry_ai_token');
        localStorage.removeItem('cherry_ai_user');
    }

    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Persona management methods
     */
    async getPersonas() {
        try {
            return await this.request('/api/personas');
        } catch (error) {
            console.error('Failed to fetch personas:', error);
            // Return mock data as fallback
            return this.getMockPersonas();
        }
    }

    async getPersona(personaId) {
        try {
            return await this.request(`/api/personas/${personaId}`);
        } catch (error) {
            console.error(`Failed to fetch persona ${personaId}:`, error);
            // Return mock data as fallback
            const mockPersonas = this.getMockPersonas();
            return mockPersonas.find(p => p.id === personaId) || null;
        }
    }

    async updatePersona(personaId, updates) {
        try {
            return await this.request(`/api/personas/${personaId}`, {
                method: 'PUT',
                body: updates
            });
        } catch (error) {
            throw new Error(`Failed to update persona: ${error.message}`);
        }
    }

    /**
     * Supervisor agent methods
     */
    async getAgents() {
        try {
            return await this.request('/api/agents');
        } catch (error) {
            console.error('Failed to fetch agents:', error);
            return this.getMockAgents();
        }
    }

    async getPersonaAgents(personaId) {
        try {
            return await this.request(`/api/personas/${personaId}/agents`);
        } catch (error) {
            console.error(`Failed to fetch agents for persona ${personaId}:`, error);
            return this.getMockAgents().filter(a => a.persona_id === personaId);
        }
    }

    async updateAgent(agentId, updates) {
        try {
            return await this.request(`/api/agents/${agentId}`, {
                method: 'PUT',
                body: updates
            });
        } catch (error) {
            throw new Error(`Failed to update agent: ${error.message}`);
        }
    }

    /**
     * System monitoring methods
     */
    async getSystemMetrics() {
        try {
            return await this.request('/api/system/metrics');
        } catch (error) {
            console.error('Failed to fetch system metrics:', error);
            return this.getMockMetrics();
        }
    }

    async getSystemHealth() {
        try {
            return await this.request('/api/system/health');
        } catch (error) {
            console.error('Failed to fetch system health:', error);
            return {
                status: 'unhealthy',
                service: 'cherry-ai-admin-api',
                database: 'disconnected',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Conversation methods
     */
    async sendMessage(messageData) {
        try {
            return await this.request('/api/conversation', {
                method: 'POST',
                body: messageData
            });
        } catch (error) {
            throw new Error(`Failed to send message: ${error.message}`);
        }
    }

    async getConversationHistory(personaType, limit = 20) {
        try {
            return await this.request(`/api/conversation/history/${personaType}?limit=${limit}`);
        } catch (error) {
            console.error(`Failed to fetch conversation history for ${personaType}:`, error);
            return []; // Return empty array as fallback
        }
    }

    async getRelationshipInsights(personaType) {
        try {
            return await this.request(`/api/relationship/insights/${personaType}`);
        } catch (error) {
            console.error(`Failed to fetch relationship insights for ${personaType}:`, error);
            // Return mock insights as fallback
            return {
                relationship_stage: 'developing',
                trust_score: 0.5,
                familiarity_score: 0.5,
                interaction_count: 0,
                communication_effectiveness: 0.5,
                learning_patterns_active: 0,
                personality_adaptations: 0,
                recent_mood_trend: 0.5
            };
        }
    }

    async getActiveSessions() {
        try {
            return await this.request('/api/conversation/active-sessions');
        } catch (error) {
            console.error('Failed to fetch active sessions:', error);
            return []; // Return empty array as fallback
        }
    }

    /**
     * Mock data methods (fallback when API is unavailable)
     */
    getMockPersonas() {
        return [
            {
                id: 1,
                persona_type: "cherry",
                name: "Cherry",
                domain: "Personal Life",
                description: "Personal life coach, friend, and lifestyle manager with a playful personality",
                configuration: { role: "Life coach and personal assistant", primary_focus: "personal_growth" },
                personality_traits: { playful: 0.9, flirty: 0.8, creative: 0.9, smart: 0.95, empathetic: 0.9 },
                skills: ["personal_development", "lifestyle_management", "relationship_advice", "health_wellness"],
                tools: ["calendar", "fitness_tracker", "meal_planner", "travel_booking"],
                voice_config: { tone: "warm_playful", speech_rate: "medium", voice_model: "cherry_v2" },
                is_active: true,
                created_at: new Date().toISOString()
            },
            {
                id: 2,
                persona_type: "sophia",
                name: "Sophia",
                domain: "Pay Ready Business",
                description: "Business strategist, client expert, and revenue advisor for apartment rental business",
                configuration: { role: "Business strategist and advisor", primary_focus: "business_success" },
                personality_traits: { strategic: 0.95, professional: 0.9, intelligent: 0.95, confident: 0.9 },
                skills: ["market_analysis", "client_management", "revenue_optimization", "business_strategy"],
                tools: ["crm", "analytics_dashboard", "market_research", "financial_modeling"],
                voice_config: { tone: "professional_confident", speech_rate: "medium", voice_model: "sophia_v2" },
                is_active: true,
                created_at: new Date().toISOString()
            },
            {
                id: 3,
                persona_type: "karen",
                name: "Karen",
                domain: "ParagonRX Healthcare",
                description: "Healthcare expert, clinical trial specialist, and compliance advisor",
                configuration: { role: "Healthcare expert and compliance advisor", primary_focus: "healthcare_excellence" },
                personality_traits: { knowledgeable: 0.95, trustworthy: 0.95, patient_centered: 0.9, detail_oriented: 0.95 },
                skills: ["clinical_research", "regulatory_compliance", "patient_recruitment", "clinical_operations"],
                tools: ["clinical_trial_management", "regulatory_database", "patient_portal", "compliance_tracker"],
                voice_config: { tone: "medical_professional", speech_rate: "medium", voice_model: "karen_v2" },
                is_active: true,
                created_at: new Date().toISOString()
            }
        ];
    }

    getMockAgents() {
        return [
            // Cherry's agents
            {
                id: 1,
                persona_id: 1,
                agent_type: "health_wellness",
                name: "Health & Wellness Supervisor",
                description: "Fitness tracking, nutrition management, medical coordination",
                capabilities: ["fitness_planning", "nutrition_advice", "mental_wellness", "sleep_optimization"],
                configuration: { expertise: "holistic_health", focus_areas: ["physical", "mental", "emotional"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 2,
                persona_id: 1,
                agent_type: "relationship_management",
                name: "Relationship Management Supervisor",
                description: "Family coordination, friendship maintenance, social planning",
                capabilities: ["family_coordination", "friendship_maintenance", "social_planning", "communication_advice"],
                configuration: { expertise: "relationship_dynamics", focus_areas: ["family", "friends", "social"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 3,
                persona_id: 1,
                agent_type: "travel_planning",
                name: "Travel Planning Supervisor",
                description: "Itinerary optimization, accommodation management, travel coordination",
                capabilities: ["itinerary_creation", "booking_assistance", "local_recommendations", "travel_tips"],
                configuration: { expertise: "travel_optimization", focus_areas: ["planning", "booking", "experiences"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            // Sophia's agents
            {
                id: 4,
                persona_id: 2,
                agent_type: "client_relationship",
                name: "Client Relationship Supervisor",
                description: "Client communication, satisfaction monitoring, retention strategies",
                capabilities: ["client_communication", "satisfaction_monitoring", "retention_strategy", "relationship_growth"],
                configuration: { expertise: "client_success", focus_areas: ["communication", "satisfaction", "retention"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 5,
                persona_id: 2,
                agent_type: "market_intelligence",
                name: "Market Intelligence Supervisor",
                description: "Competitive analysis, trend monitoring, opportunity identification",
                capabilities: ["market_analysis", "competitor_tracking", "trend_forecasting", "opportunity_identification"],
                configuration: { expertise: "market_analysis", focus_areas: ["competition", "trends", "opportunities"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 6,
                persona_id: 2,
                agent_type: "financial_performance",
                name: "Financial Performance Supervisor",
                description: "Revenue optimization, cost analysis, financial planning support",
                capabilities: ["revenue_optimization", "cost_analysis", "profitability_improvement", "financial_planning"],
                configuration: { expertise: "financial_optimization", focus_areas: ["revenue", "costs", "profitability"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            // Karen's agents
            {
                id: 7,
                persona_id: 3,
                agent_type: "regulatory_compliance",
                name: "Regulatory Compliance Supervisor",
                description: "Regulation monitoring, compliance assessment, audit preparation",
                capabilities: ["regulation_monitoring", "compliance_assessment", "audit_preparation", "regulatory_strategy"],
                configuration: { expertise: "regulatory_affairs", focus_areas: ["monitoring", "compliance", "audits"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 8,
                persona_id: 3,
                agent_type: "clinical_trial_management",
                name: "Clinical Trial Management Supervisor",
                description: "Protocol optimization, operational efficiency, quality assurance",
                capabilities: ["protocol_optimization", "operational_efficiency", "quality_assurance", "trial_performance"],
                configuration: { expertise: "clinical_operations", focus_areas: ["protocols", "operations", "quality"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            },
            {
                id: 9,
                persona_id: 3,
                agent_type: "patient_recruitment",
                name: "Patient Recruitment Supervisor",
                description: "Recruitment strategies, patient engagement, retention improvement",
                capabilities: ["recruitment_strategy", "patient_engagement", "retention_improvement", "demographic_analysis"],
                configuration: { expertise: "patient_recruitment", focus_areas: ["strategy", "engagement", "retention"] },
                status: "active",
                last_active: new Date().toISOString(),
                created_at: new Date().toISOString()
            }
        ];
    }

    getMockMetrics() {
        return {
            active_sessions: 23,
            total_requests_today: 147,
            average_response_time: 245.5,
            error_rate: 0.01,
            persona_performance: {
                cherry: 85.2,
                sophia: 92.1,
                karen: 88.7
            }
        };
    }

    /**
     * Utility methods
     */
    showLoading(show = true) {
        // You can implement a loading indicator here
        document.body.classList.toggle('loading', show);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatPercentage(value) {
        return `${(value * 100).toFixed(1)}%`;
    }

    formatNumber(value) {
        return new Intl.NumberFormat('en-US').format(value);
    }
}

// Create global instance
window.apiClient = new CherryAIApiClient(); 