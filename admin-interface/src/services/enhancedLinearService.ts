import APIConfigService from '../config/apiConfig';
import { apiClient } from '../utils/apiClient';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class CacheService {
  private cache = new Map<string, CacheEntry<any>>();
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }

  has(key: string): boolean {
    const entry = this.cache.get(key);
    if (!entry) return false;
    
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  size(): number {
    return this.cache.size;
  }

  // Cache with automatic fetching
  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = this.DEFAULT_TTL
  ): Promise<T> {
    const cached = this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    const data = await fetcher();
    this.set(key, data, ttl);
    return data;
  }
}

// Enhanced Linear Service with caching and optimization
class EnhancedLinearService {
  private cache = new CacheService();
  private apiKey: string;

  constructor() {
    this.apiKey = APIConfigService.getLinearApiKey();
  }

  private async graphqlRequest(query: string, variables: any = {}) {
    const cacheKey = `linear:${btoa(query + JSON.stringify(variables))}`;
    
    return this.cache.getOrFetch(
      cacheKey,
      async () => {
        return apiClient.post('linear', 'https://api.linear.app/graphql', {
          query,
          variables
        }, {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        });
      },
      2 * 60 * 1000 // 2 minutes cache
    );
  }

  async getTeams() {
    const query = `
      query Teams {
        teams {
          nodes {
            id
            name
            key
            description
            projects {
              nodes {
                id
                name
                description
                state
              }
            }
          }
        }
      }
    `;

    const response = await this.graphqlRequest(query);
    return response.data.teams.nodes;
  }

  async getIssues(teamId?: string, limit: number = 50) {
    const query = `
      query Issues($teamId: String, $first: Int) {
        issues(
          filter: { team: { id: { eq: $teamId } } }
          first: $first
          orderBy: updatedAt
        ) {
          nodes {
            id
            title
            description
            state {
              id
              name
              type
            }
            priority
            assignee {
              id
              name
              email
            }
            team {
              id
              name
              key
            }
            project {
              id
              name
            }
            createdAt
            updatedAt
            url
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    `;

    const response = await this.graphqlRequest(query, { teamId, first: limit });
    return response.data.issues;
  }

  async createIssue(data: {
    teamId: string;
    title: string;
    description?: string;
    priority?: number;
    assigneeId?: string;
    projectId?: string;
  }) {
    const mutation = `
      mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
          success
          issue {
            id
            title
            url
          }
        }
      }
    `;

    const input = {
      teamId: data.teamId,
      title: data.title,
      description: data.description,
      priority: data.priority,
      assigneeId: data.assigneeId,
      projectId: data.projectId
    };

    const response = await apiClient.post('linear', 'https://api.linear.app/graphql', {
      query: mutation,
      variables: { input }
    }, {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    });

    // Invalidate cache
    this.cache.clear();

    return response.data.issueCreate;
  }

  async updateIssue(issueId: string, data: {
    title?: string;
    description?: string;
    stateId?: string;
    priority?: number;
    assigneeId?: string;
  }) {
    const mutation = `
      mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
        issueUpdate(id: $id, input: $input) {
          success
          issue {
            id
            title
            url
          }
        }
      }
    `;

    const response = await apiClient.post('linear', 'https://api.linear.app/graphql', {
      query: mutation,
      variables: { id: issueId, input: data }
    }, {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    });

    // Invalidate cache
    this.cache.clear();

    return response.data.issueUpdate;
  }

  async searchIssues(query: string, limit: number = 20) {
    const searchQuery = `
      query SearchIssues($query: String!, $first: Int) {
        searchIssues(query: $query, first: $first) {
          nodes {
            id
            title
            description
            state {
              name
              type
            }
            team {
              name
              key
            }
            url
          }
        }
      }
    `;

    const response = await this.graphqlRequest(searchQuery, { query, first: limit });
    return response.data.searchIssues.nodes;
  }

  // Batch operations for efficiency
  async batchCreateIssues(issues: Array<{
    teamId: string;
    title: string;
    description?: string;
    priority?: number;
  }>) {
    const results = [];
    
    // Process in batches of 5 to avoid rate limits
    for (let i = 0; i < issues.length; i += 5) {
      const batch = issues.slice(i, i + 5);
      const batchPromises = batch.map(issue => this.createIssue(issue));
      const batchResults = await Promise.allSettled(batchPromises);
      results.push(...batchResults);
    }

    return results;
  }

  // Analytics and metrics
  async getTeamMetrics(teamId: string) {
    const cacheKey = `linear:metrics:${teamId}`;
    
    return this.cache.getOrFetch(
      cacheKey,
      async () => {
        const issues = await this.getIssues(teamId, 1000);
        
        const metrics = {
          total: issues.nodes.length,
          byState: {} as Record<string, number>,
          byPriority: {} as Record<string, number>,
          avgAge: 0,
          completionRate: 0
        };

        issues.nodes.forEach(issue => {
          // Count by state
          const state = issue.state.name;
          metrics.byState[state] = (metrics.byState[state] || 0) + 1;

          // Count by priority
          const priority = issue.priority?.toString() || 'None';
          metrics.byPriority[priority] = (metrics.byPriority[priority] || 0) + 1;
        });

        // Calculate completion rate
        const completedStates = ['Done', 'Completed', 'Closed'];
        const completed = Object.entries(metrics.byState)
          .filter(([state]) => completedStates.includes(state))
          .reduce((sum, [, count]) => sum + count, 0);
        
        metrics.completionRate = metrics.total > 0 ? (completed / metrics.total) * 100 : 0;

        return metrics;
      },
      10 * 60 * 1000 // 10 minutes cache for metrics
    );
  }
}

export default EnhancedLinearService;

