import APIConfigService from '../config/apiConfig';

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
  relevanceScore: number;
  timestamp?: string;
}

class SearchService {
  private config = APIConfigService.getInstance().getSearchConfig();

  async search(
    query: string,
    persona: 'sophia' | 'karen' | 'cherry',
    mode: 'normal' | 'deep' | 'super_deep' = 'normal'
  ): Promise<SearchResult[]> {
    // Inject persona-specific bias
    const biasedQuery = this.injectPersonaBias(query, persona);
    
    // Execute parallel searches based on mode
    const searchPromises = this.getSearchPromises(biasedQuery, mode);
    const results = await Promise.allSettled(searchPromises);
    
    // Fuse and rank results
    return this.fuseResults(results, persona);
  }

  private injectPersonaBias(query: string, persona: string): string {
    const biasKeywords = {
      sophia: ['market analysis', 'business metrics', 'apartment technology', 'fintech', 'proptech'],
      karen: ['clinical trials', 'pharmaceutical research', 'medical literature', 'FDA compliance'],
      cherry: ['creative inspiration', 'innovation', 'design trends', 'technology', 'artistic']
    };

    const keywords = biasKeywords[persona] || biasKeywords.cherry;
    const selectedKeywords = keywords.slice(0, 2);
    return `${query} ${selectedKeywords.join(' ')}`;
  }

  private getSearchPromises(query: string, mode: string) {
    const promises = [];

    // Always include Brave for web search
    promises.push(this.searchBrave(query));

    if (mode === 'normal') {
      promises.push(this.searchPerplexity(query));
      promises.push(this.searchExa(query));
    } else if (mode === 'deep') {
      promises.push(this.searchPerplexity(query));
      promises.push(this.searchExa(query));
      promises.push(this.searchTavily(query));
      promises.push(this.searchApollo(query));
    } else if (mode === 'super_deep') {
      promises.push(this.searchPerplexity(query));
      promises.push(this.searchExa(query));
      promises.push(this.searchTavily(query));
      promises.push(this.searchApollo(query));
      // Add more comprehensive searches
      promises.push(this.searchBrave(query + ' research'));
      promises.push(this.searchBrave(query + ' analysis'));
    }

    return promises;
  }

  private async searchBrave(query: string): Promise<SearchResult[]> {
    try {
      const response = await fetch(`${this.config.brave.endpoint}?q=${encodeURIComponent(query)}&count=10`, {
        headers: {
          'X-Subscription-Token': this.config.brave.apiKey,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Brave API error: ${response.status}`);
      }

      const data = await response.json();
      return data.web?.results?.map((result: any) => ({
        title: result.title,
        url: result.url,
        snippet: result.description,
        source: 'brave',
        relevanceScore: 0.8,
        timestamp: result.age
      })) || [];
    } catch (error) {
      console.error('Brave search error:', error);
      return [];
    }
  }

  private async searchPerplexity(query: string): Promise<SearchResult[]> {
    try {
      const response = await fetch(this.config.perplexity.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.perplexity.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'llama-3.1-sonar-small-128k-online',
          messages: [
            {
              role: 'user',
              content: `Search and provide detailed information about: ${query}`
            }
          ]
        })
      });

      if (!response.ok) {
        throw new Error(`Perplexity API error: ${response.status}`);
      }

      const data = await response.json();
      const content = data.choices[0].message.content;
      
      // Parse Perplexity response into search results
      return [{
        title: `Perplexity Analysis: ${query}`,
        url: 'https://perplexity.ai',
        snippet: content.substring(0, 200) + '...',
        source: 'perplexity',
        relevanceScore: 0.9
      }];
    } catch (error) {
      console.error('Perplexity search error:', error);
      return [];
    }
  }

  private async searchExa(query: string): Promise<SearchResult[]> {
    try {
      const response = await fetch(this.config.exa.endpoint, {
        method: 'POST',
        headers: {
          'x-api-key': this.config.exa.apiKey,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          num_results: 10,
          include_domains: [],
          exclude_domains: []
        })
      });

      if (!response.ok) {
        throw new Error(`Exa API error: ${response.status}`);
      }

      const data = await response.json();
      return data.results?.map((result: any) => ({
        title: result.title,
        url: result.url,
        snippet: result.text?.substring(0, 200) + '...' || '',
        source: 'exa',
        relevanceScore: result.score || 0.7
      })) || [];
    } catch (error) {
      console.error('Exa search error:', error);
      return [];
    }
  }

  private async searchTavily(query: string): Promise<SearchResult[]> {
    try {
      const response = await fetch(this.config.tavily.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          api_key: this.config.tavily.apiKey,
          query: query,
          search_depth: 'basic',
          include_answer: false,
          include_images: false,
          include_raw_content: false,
          max_results: 10
        })
      });

      if (!response.ok) {
        throw new Error(`Tavily API error: ${response.status}`);
      }

      const data = await response.json();
      return data.results?.map((result: any) => ({
        title: result.title,
        url: result.url,
        snippet: result.content,
        source: 'tavily',
        relevanceScore: result.score || 0.8
      })) || [];
    } catch (error) {
      console.error('Tavily search error:', error);
      return [];
    }
  }

  private async searchApollo(query: string): Promise<SearchResult[]> {
    try {
      // Apollo is for business/people search, adapt query accordingly
      const response = await fetch(this.config.apollo.endpoint, {
        method: 'POST',
        headers: {
          'Cache-Control': 'no-cache',
          'Content-Type': 'application/json',
          'X-Api-Key': this.config.apollo.apiKey
        },
        body: JSON.stringify({
          q_keywords: query,
          page: 1,
          per_page: 10
        })
      });

      if (!response.ok) {
        throw new Error(`Apollo API error: ${response.status}`);
      }

      const data = await response.json();
      return data.people?.map((person: any) => ({
        title: `${person.first_name} ${person.last_name} - ${person.title}`,
        url: person.linkedin_url || '#',
        snippet: `${person.title} at ${person.organization_name}. ${person.city}, ${person.state}`,
        source: 'apollo',
        relevanceScore: 0.6
      })) || [];
    } catch (error) {
      console.error('Apollo search error:', error);
      return [];
    }
  }

  private fuseResults(results: PromiseSettledResult<SearchResult[]>[], persona: string): SearchResult[] {
    const allResults: SearchResult[] = [];

    results.forEach(result => {
      if (result.status === 'fulfilled') {
        allResults.push(...result.value);
      }
    });

    // Remove duplicates based on URL
    const uniqueResults = allResults.filter((result, index, self) =>
      index === self.findIndex(r => r.url === result.url)
    );

    // Sort by relevance score and persona-specific ranking
    return uniqueResults
      .sort((a, b) => this.getPersonaRelevance(b, persona) - this.getPersonaRelevance(a, persona))
      .slice(0, 20); // Limit to top 20 results
  }

  private getPersonaRelevance(result: SearchResult, persona: string): number {
    let score = result.relevanceScore;

    const personaBoosts = {
      sophia: ['business', 'market', 'financial', 'apartment', 'proptech', 'fintech'],
      karen: ['clinical', 'medical', 'pharmaceutical', 'research', 'FDA', 'drug'],
      cherry: ['creative', 'design', 'innovation', 'artistic', 'technology', 'trends']
    };

    const boostKeywords = personaBoosts[persona] || [];
    const text = (result.title + ' ' + result.snippet).toLowerCase();

    boostKeywords.forEach(keyword => {
      if (text.includes(keyword)) {
        score += 0.1;
      }
    });

    // Source-specific boosts
    if (persona === 'sophia' && (result.source === 'apollo' || result.source === 'brave')) {
      score += 0.2;
    } else if (persona === 'karen' && result.source === 'perplexity') {
      score += 0.2;
    } else if (persona === 'cherry' && result.source === 'exa') {
      score += 0.2;
    }

    return score;
  }
}

export default SearchService;

