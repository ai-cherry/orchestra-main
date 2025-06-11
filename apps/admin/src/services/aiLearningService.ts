interface UserInteraction {
  timestamp: Date;
  persona: 'sophia' | 'karen' | 'cherry';
  action: string;
  context: any;
  outcome: string;
  satisfaction?: number;
}

interface LearningPattern {
  pattern: string;
  frequency: number;
  success_rate: number;
  context_tags: string[];
  persona_specific: boolean;
}

interface PersonaPreferences {
  preferred_search_sources: string[];
  common_queries: string[];
  response_style: string;
  interaction_patterns: string[];
  success_metrics: {
    task_completion_rate: number;
    user_satisfaction: number;
    response_relevance: number;
  };
}

class AILearningService {
  private interactions: UserInteraction[] = [];
  private patterns: Map<string, LearningPattern> = new Map();
  private personaPreferences: Map<string, PersonaPreferences> = new Map();
  private learningEnabled = true;

  constructor() {
    this.initializePersonaPreferences();
    this.loadStoredLearning();
  }

  // Track user interactions for learning
  trackInteraction(
    persona: 'sophia' | 'karen' | 'cherry',
    action: string,
    context: any,
    outcome: string,
    satisfaction?: number
  ): void {
    if (!this.learningEnabled) return;

    const interaction: UserInteraction = {
      timestamp: new Date(),
      persona,
      action,
      context,
      outcome,
      satisfaction
    };

    this.interactions.push(interaction);
    this.updateLearningPatterns(interaction);
    this.updatePersonaPreferences(persona, interaction);
    this.persistLearning();
  }

  // Get personalized recommendations based on learning
  getPersonalizedRecommendations(persona: string): {
    suggested_actions: string[];
    preferred_search_mode: string;
    response_style: string;
    relevant_sources: string[];
  } {
    const preferences = this.personaPreferences.get(persona);
    const recentPatterns = this.getRecentPatterns(persona);

    return {
      suggested_actions: this.getSuggestedActions(persona, recentPatterns),
      preferred_search_mode: this.getPreferredSearchMode(persona),
      response_style: preferences?.response_style || 'balanced',
      relevant_sources: preferences?.preferred_search_sources || []
    };
  }

  // Adaptive search query enhancement
  enhanceSearchQuery(
    query: string,
    persona: string,
    context?: any
  ): {
    enhanced_query: string;
    suggested_sources: string[];
    search_mode: 'normal' | 'deep' | 'super_deep';
  } {
    const preferences = this.personaPreferences.get(persona);
    const patterns = this.getRelevantPatterns(query, persona);

    // Enhance query based on learned patterns
    let enhancedQuery = query;
    
    // Add context-specific keywords based on learning
    const contextKeywords = this.getContextKeywords(query, persona);
    if (contextKeywords.length > 0) {
      enhancedQuery += ' ' + contextKeywords.join(' ');
    }

    // Determine optimal search mode based on query complexity and past success
    const searchMode = this.determineSearchMode(query, persona, patterns);

    // Suggest best sources based on historical success
    const suggestedSources = this.getSuggestedSources(query, persona);

    return {
      enhanced_query: enhancedQuery,
      suggested_sources: suggestedSources,
      search_mode: searchMode
    };
  }

  // Predictive assistance based on context
  getPredictiveAssistance(
    currentContext: any,
    persona: string
  ): {
    predicted_needs: string[];
    suggested_actions: string[];
    proactive_searches: string[];
  } {
    const similarContexts = this.findSimilarContexts(currentContext, persona);
    const patterns = this.getContextualPatterns(currentContext, persona);

    return {
      predicted_needs: this.predictUserNeeds(similarContexts, patterns),
      suggested_actions: this.getSuggestedActions(persona, patterns),
      proactive_searches: this.getProactiveSearches(currentContext, persona)
    };
  }

  // Cross-persona learning (Cherry learns from Sophia and Karen)
  getCrossPersonaInsights(targetPersona: 'cherry'): {
    learned_patterns: LearningPattern[];
    adapted_strategies: string[];
    knowledge_transfer: any[];
  } {
    if (targetPersona !== 'cherry') {
      return { learned_patterns: [], adapted_strategies: [], knowledge_transfer: [] };
    }

    const sophiaPatterns = this.getPersonaPatterns('sophia');
    const karenPatterns = this.getPersonaPatterns('karen');

    // Extract transferable knowledge
    const transferablePatterns = this.extractTransferablePatterns(
      [...sophiaPatterns, ...karenPatterns]
    );

    return {
      learned_patterns: transferablePatterns,
      adapted_strategies: this.adaptStrategiesForCherry(transferablePatterns),
      knowledge_transfer: this.getKnowledgeTransfer(sophiaPatterns, karenPatterns)
    };
  }

  // Continuous improvement based on feedback
  updateFromFeedback(
    interactionId: string,
    feedback: {
      helpful: boolean;
      accuracy: number;
      relevance: number;
      suggestions?: string;
    }
  ): void {
    const interaction = this.interactions.find(i => 
      i.timestamp.getTime().toString() === interactionId
    );

    if (interaction) {
      interaction.satisfaction = (feedback.accuracy + feedback.relevance) / 2;
      this.updateLearningFromFeedback(interaction, feedback);
      this.persistLearning();
    }
  }

  private initializePersonaPreferences(): void {
    // Initialize with base preferences for each persona
    this.personaPreferences.set('sophia', {
      preferred_search_sources: ['brave', 'apollo', 'perplexity'],
      common_queries: ['market analysis', 'business metrics', 'competitive intelligence'],
      response_style: 'professional',
      interaction_patterns: ['data-driven', 'analytical', 'strategic'],
      success_metrics: {
        task_completion_rate: 0.85,
        user_satisfaction: 0.8,
        response_relevance: 0.9
      }
    });

    this.personaPreferences.set('karen', {
      preferred_search_sources: ['perplexity', 'exa', 'tavily'],
      common_queries: ['clinical research', 'pharmaceutical data', 'medical literature'],
      response_style: 'scientific',
      interaction_patterns: ['evidence-based', 'methodical', 'precise'],
      success_metrics: {
        task_completion_rate: 0.9,
        user_satisfaction: 0.85,
        response_relevance: 0.95
      }
    });

    this.personaPreferences.set('cherry', {
      preferred_search_sources: ['exa', 'brave', 'tavily'],
      common_queries: ['creative inspiration', 'design trends', 'innovation'],
      response_style: 'creative',
      interaction_patterns: ['exploratory', 'adaptive', 'cross-domain'],
      success_metrics: {
        task_completion_rate: 0.8,
        user_satisfaction: 0.9,
        response_relevance: 0.85
      }
    });
  }

  private updateLearningPatterns(interaction: UserInteraction): void {
    const patternKey = `${interaction.persona}_${interaction.action}`;
    const existing = this.patterns.get(patternKey);

    if (existing) {
      existing.frequency += 1;
      existing.success_rate = this.calculateSuccessRate(patternKey);
    } else {
      this.patterns.set(patternKey, {
        pattern: patternKey,
        frequency: 1,
        success_rate: interaction.satisfaction || 0.5,
        context_tags: this.extractContextTags(interaction.context),
        persona_specific: true
      });
    }
  }

  private updatePersonaPreferences(
    persona: string,
    interaction: UserInteraction
  ): void {
    const preferences = this.personaPreferences.get(persona);
    if (!preferences) return;

    // Update based on successful interactions
    if (interaction.satisfaction && interaction.satisfaction > 0.7) {
      // Update preferred sources, queries, etc.
      this.updatePreferencesFromSuccess(preferences, interaction);
    }

    this.personaPreferences.set(persona, preferences);
  }

  private getContextKeywords(query: string, persona: string): string[] {
    const preferences = this.personaPreferences.get(persona);
    if (!preferences) return [];

    // Extract relevant keywords based on persona and past successful queries
    const relevantPatterns = Array.from(this.patterns.values())
      .filter(p => p.pattern.includes(persona) && p.success_rate > 0.7);

    return relevantPatterns
      .flatMap(p => p.context_tags)
      .filter(tag => !query.toLowerCase().includes(tag.toLowerCase()))
      .slice(0, 3); // Limit to top 3 keywords
  }

  private determineSearchMode(
    query: string,
    persona: string,
    patterns: LearningPattern[]
  ): 'normal' | 'deep' | 'super_deep' {
    const queryComplexity = this.assessQueryComplexity(query);
    const historicalSuccess = this.getHistoricalSearchSuccess(persona, patterns);

    if (queryComplexity > 0.8 || historicalSuccess.deep > historicalSuccess.normal) {
      return 'super_deep';
    } else if (queryComplexity > 0.5 || historicalSuccess.deep > 0.7) {
      return 'deep';
    } else {
      return 'normal';
    }
  }

  private getSuggestedSources(query: string, persona: string): string[] {
    const preferences = this.personaPreferences.get(persona);
    const successfulSources = this.getSuccessfulSources(query, persona);
    
    return [...new Set([
      ...(preferences?.preferred_search_sources || []),
      ...successfulSources
    ])].slice(0, 5);
  }

  private extractTransferablePatterns(patterns: LearningPattern[]): LearningPattern[] {
    return patterns.filter(pattern => 
      pattern.success_rate > 0.8 && 
      pattern.frequency > 5 &&
      !pattern.persona_specific
    );
  }

  private adaptStrategiesForCherry(patterns: LearningPattern[]): string[] {
    return patterns.map(pattern => {
      // Adapt business/clinical strategies for creative use
      return `Creative adaptation: ${pattern.pattern}`;
    });
  }

  private loadStoredLearning(): void {
    try {
      const stored = localStorage.getItem('ai_learning_data');
      if (stored) {
        const data = JSON.parse(stored);
        this.interactions = data.interactions || [];
        this.patterns = new Map(data.patterns || []);
        this.personaPreferences = new Map(data.preferences || []);
      }
    } catch (error) {
      console.error('Error loading stored learning data:', error);
    }
  }

  private persistLearning(): void {
    try {
      const data = {
        interactions: this.interactions.slice(-1000), // Keep last 1000 interactions
        patterns: Array.from(this.patterns.entries()),
        preferences: Array.from(this.personaPreferences.entries())
      };
      localStorage.setItem('ai_learning_data', JSON.stringify(data));
    } catch (error) {
      console.error('Error persisting learning data:', error);
    }
  }

  // Helper methods (simplified implementations)
  private getRecentPatterns(persona: string): LearningPattern[] {
    return Array.from(this.patterns.values())
      .filter(p => p.pattern.includes(persona))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10);
  }

  private getSuggestedActions(persona: string, patterns: LearningPattern[]): string[] {
    return patterns
      .filter(p => p.success_rate > 0.7)
      .map(p => p.pattern.split('_')[1])
      .slice(0, 5);
  }

  private getPreferredSearchMode(persona: string): string {
    const preferences = this.personaPreferences.get(persona);
    // Logic to determine preferred search mode based on historical data
    return 'deep'; // Simplified
  }

  private calculateSuccessRate(patternKey: string): number {
    const relatedInteractions = this.interactions.filter(i => 
      `${i.persona}_${i.action}` === patternKey
    );
    
    const totalSatisfaction = relatedInteractions.reduce((sum, i) => 
      sum + (i.satisfaction || 0.5), 0
    );
    
    return relatedInteractions.length > 0 ? 
      totalSatisfaction / relatedInteractions.length : 0.5;
  }

  private extractContextTags(context: any): string[] {
    // Extract meaningful tags from context
    if (!context) return [];
    
    const tags: string[] = [];
    if (context.query) tags.push(...context.query.split(' ').slice(0, 3));
    if (context.source) tags.push(context.source);
    if (context.type) tags.push(context.type);
    
    return tags.filter(tag => tag.length > 2);
  }

  private assessQueryComplexity(query: string): number {
    // Simple complexity assessment based on query characteristics
    const factors = [
      query.length > 50 ? 0.3 : 0,
      (query.match(/\?/g) || []).length * 0.2,
      (query.match(/\band\b|\bor\b/gi) || []).length * 0.1,
      query.includes('compare') || query.includes('analyze') ? 0.3 : 0,
      query.includes('detailed') || query.includes('comprehensive') ? 0.2 : 0
    ];
    
    return Math.min(factors.reduce((sum, factor) => sum + factor, 0), 1);
  }

  private getHistoricalSearchSuccess(persona: string, patterns: LearningPattern[]): any {
    // Simplified implementation
    return { normal: 0.7, deep: 0.8, super_deep: 0.9 };
  }

  private getSuccessfulSources(query: string, persona: string): string[] {
    // Return sources that have been successful for similar queries
    return ['brave', 'perplexity']; // Simplified
  }

  private findSimilarContexts(currentContext: any, persona: string): UserInteraction[] {
    // Find interactions with similar context
    return this.interactions.filter(i => 
      i.persona === persona && 
      this.calculateContextSimilarity(i.context, currentContext) > 0.7
    ).slice(0, 10);
  }

  private calculateContextSimilarity(context1: any, context2: any): number {
    // Simplified similarity calculation
    return 0.8; // Placeholder
  }

  private getContextualPatterns(context: any, persona: string): LearningPattern[] {
    return Array.from(this.patterns.values())
      .filter(p => p.pattern.includes(persona))
      .slice(0, 5);
  }

  private predictUserNeeds(contexts: UserInteraction[], patterns: LearningPattern[]): string[] {
    // Predict what the user might need next
    return ['search', 'create_presentation', 'analyze_data']; // Simplified
  }

  private getProactiveSearches(context: any, persona: string): string[] {
    // Suggest searches that might be helpful
    return ['related_topics', 'recent_updates', 'competitive_analysis']; // Simplified
  }

  private getPersonaPatterns(persona: string): LearningPattern[] {
    return Array.from(this.patterns.values())
      .filter(p => p.pattern.includes(persona));
  }

  private getKnowledgeTransfer(sophiaPatterns: LearningPattern[], karenPatterns: LearningPattern[]): any[] {
    // Extract knowledge that can be transferred to Cherry
    return []; // Simplified
  }

  private updateLearningFromFeedback(interaction: UserInteraction, feedback: any): void {
    // Update learning patterns based on user feedback
    const patternKey = `${interaction.persona}_${interaction.action}`;
    const pattern = this.patterns.get(patternKey);
    
    if (pattern) {
      pattern.success_rate = (pattern.success_rate + feedback.accuracy) / 2;
    }
  }

  private updatePreferencesFromSuccess(preferences: PersonaPreferences, interaction: UserInteraction): void {
    // Update preferences based on successful interactions
    if (interaction.context?.source && !preferences.preferred_search_sources.includes(interaction.context.source)) {
      preferences.preferred_search_sources.push(interaction.context.source);
    }
  }
}

export default AILearningService;

