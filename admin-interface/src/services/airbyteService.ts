interface AirbyteConnection {
  connectionId: string;
  sourceId: string;
  destinationId: string;
  name: string;
  status: 'active' | 'inactive' | 'deprecated';
  scheduleType: 'manual' | 'basic' | 'cron';
  scheduleData?: any;
}

interface AirbyteSource {
  sourceId: string;
  sourceName: string;
  sourceDefinitionId: string;
  connectionConfiguration: any;
  name: string;
}

interface SyncResult {
  jobId: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  recordsSynced: number;
  bytesEmitted: number;
  startTime: Date;
  endTime?: Date;
}

class AirbyteCloudService {
  private baseUrl = 'https://api.airbyte.com/v1';
  private clientId = '9630134c-359d-4c9c-aa97-95ab3a2ff8f5';
  private clientSecret = 'NfwyhFUjemKlC66h7iECE9Tjedo6SGFh';
  private accessToken = 'eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6Z1BPdmhDSC1Ic21OQnhhV3lnLU11dlF6dHJERTBDSEJHZDB2MVh0Vnk0In0.eyJleHAiOjE3NDk0MTM3MjMsImlhdCI6MTc0OTQxMjgyMywianRpIjoiMjA1MDgwOWQtOWI2OS00YzI5LTk2OGUtMmE0MjM3NDY4NGQ3IiwiaXNzIjoiaHR0cHM6Ly9jbG91ZC5haXJieXRlLmNvbS9hdXRoL3JlYWxtcy9fYWlyYnl0ZS1hcHBsaWNhdGlvbi1jbGllbnRzIiwiYXVkIjoiYWNjb3VudCIsInN1YiI6IjkwNzJmYzI0LTE0MjUtNDBlNy05ZmU4LTg0ZWYxM2I2M2Q4MCIsInR5cCI6IkJlYXJlciIsImF6cCI6Ijk2MzAxMzRjLTM1OWQtNGM5Yy1hYTk3LTk1YWIzYTJmZjhmNSIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtX2FpcmJ5dGUtYXBwbGljYXRpb24tY2xpZW50cyJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImNsaWVudEhvc3QiOiIxNzIuMjMuMC42OCIsInVzZXJfaWQiOiI5MDcyZmMyNC0xNDI1LTQwZTctOWZlOC04NGVmMTNiNjNkODAiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJzZXJ2aWNlLWFjY291bnQtOTYzMDEzNGMtMzU5ZC00YzljLWFhOTctOTVhYjNhMmZmOGY1IiwiY2xpZW50QWRkcmVzcyI6IjE3Mi4yMy4wLjY4IiwiY2xpZW50X2lkIjoiOTYzMDEzNGMtMzU5ZC00YzljLWFhOTctOTVhYjNhMmZmOGY1In0.QkACm7nLW9zrKHsPP3zYpqdfQjl85RX_Mn-Kdwr8aH_7Y38v86ymaHY5PS-k6L0OeSMvUoFrbgIvNMtuq0Gl4xqi4jkrpi9uzgDouiTkJa8l0dyj1ReC9HiD-yd1Y5k0rUaVtbuQaG1gaTA0i3YwK57N1Ldj5oYQx1aKvCup_uGeyqnXc48dKe47STdCyD3p8wwkAYO8LQhhWnK4VRUGgga5Rzkp6fMTPxogN9rBuN9sgQLTjUoRnxpIP-8uB6MRlYLgplhZiLQ25YmUYZzBuDy--xzPqPxNPyRhV5KGcWomj8eNoHb5b8TBcQ292GT0dgPEf-aAv1T4mMokcNbLTA';

  constructor() {
    this.refreshTokenIfNeeded();
  }

  // Get all connections for internal data search
  async getConnections(): Promise<AirbyteConnection[]> {
    try {
      const response = await fetch(`${this.baseUrl}/connections`, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error('Error fetching connections:', error);
      return [];
    }
  }

  // Get all data sources
  async getSources(): Promise<AirbyteSource[]> {
    try {
      const response = await fetch(`${this.baseUrl}/sources`, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.data || [];
    } catch (error) {
      console.error('Error fetching sources:', error);
      return [];
    }
  }

  // Trigger manual sync for specific connection
  async triggerSync(connectionId: string): Promise<SyncResult> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          connectionId: connectionId,
          jobType: 'sync'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        jobId: data.jobId,
        status: data.status,
        recordsSynced: 0,
        bytesEmitted: 0,
        startTime: new Date()
      };
    } catch (error) {
      console.error('Error triggering sync:', error);
      throw error;
    }
  }

  // Get job status
  async getJobStatus(jobId: string): Promise<SyncResult> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        jobId: data.jobId,
        status: data.status,
        recordsSynced: data.recordsSynced || 0,
        bytesEmitted: data.bytesEmitted || 0,
        startTime: new Date(data.createdAt),
        endTime: data.updatedAt ? new Date(data.updatedAt) : undefined
      };
    } catch (error) {
      console.error('Error fetching job status:', error);
      throw error;
    }
  }

  // Search internal data through Airbyte connections
  async searchInternalData(
    query: string,
    sources?: string[],
    limit: number = 50
  ): Promise<{
    results: any[];
    sources_searched: string[];
    total_results: number;
  }> {
    try {
      const connections = await this.getConnections();
      const activeConnections = connections.filter(c => c.status === 'active');
      
      // Filter by specified sources if provided
      const targetConnections = sources 
        ? activeConnections.filter(c => sources.includes(c.name))
        : activeConnections;

      const searchResults: any[] = [];
      const sourcesSearched: string[] = [];

      // Search through each connection's data
      for (const connection of targetConnections) {
        try {
          const connectionData = await this.searchConnectionData(
            connection.connectionId,
            query,
            Math.ceil(limit / targetConnections.length)
          );
          
          searchResults.push(...connectionData);
          sourcesSearched.push(connection.name);
        } catch (error) {
          console.error(`Error searching connection ${connection.name}:`, error);
        }
      }

      return {
        results: searchResults.slice(0, limit),
        sources_searched: sourcesSearched,
        total_results: searchResults.length
      };
    } catch (error) {
      console.error('Error searching internal data:', error);
      return {
        results: [],
        sources_searched: [],
        total_results: 0
      };
    }
  }

  // Get data freshness for connections
  async getDataFreshness(): Promise<{
    connection_id: string;
    name: string;
    last_sync: Date;
    status: string;
    freshness_score: number;
  }[]> {
    try {
      const connections = await this.getConnections();
      const freshnessData = [];

      for (const connection of connections) {
        const lastJob = await this.getLastSyncJob(connection.connectionId);
        const freshnessScore = this.calculateFreshnessScore(lastJob);

        freshnessData.push({
          connection_id: connection.connectionId,
          name: connection.name,
          last_sync: lastJob?.endTime || new Date(0),
          status: lastJob?.status || 'unknown',
          freshness_score: freshnessScore
        });
      }

      return freshnessData;
    } catch (error) {
      console.error('Error getting data freshness:', error);
      return [];
    }
  }

  // Setup automated data refresh for search optimization
  async setupAutomatedRefresh(
    connectionIds: string[],
    schedule: 'hourly' | 'daily' | 'weekly' = 'daily'
  ): Promise<boolean> {
    try {
      for (const connectionId of connectionIds) {
        await this.updateConnectionSchedule(connectionId, schedule);
      }
      return true;
    } catch (error) {
      console.error('Error setting up automated refresh:', error);
      return false;
    }
  }

  // Get available data sources for persona-specific searches
  async getPersonaDataSources(persona: 'sophia' | 'karen' | 'cherry'): Promise<{
    recommended_sources: string[];
    available_connections: AirbyteConnection[];
    data_types: string[];
  }> {
    const connections = await this.getConnections();
    
    const personaMapping = {
      sophia: {
        keywords: ['business', 'sales', 'marketing', 'finance', 'crm', 'analytics'],
        recommended: ['hubspot', 'salesforce', 'google_analytics', 'stripe']
      },
      karen: {
        keywords: ['clinical', 'medical', 'research', 'pharma', 'health', 'trial'],
        recommended: ['clinical_trials', 'pubmed', 'fda', 'medical_records']
      },
      cherry: {
        keywords: ['creative', 'design', 'content', 'social', 'media', 'trends'],
        recommended: ['social_media', 'design_tools', 'content_platforms', 'trend_data']
      }
    };

    const personaConfig = personaMapping[persona];
    const relevantConnections = connections.filter(c => 
      personaConfig.keywords.some(keyword => 
        c.name.toLowerCase().includes(keyword)
      )
    );

    return {
      recommended_sources: personaConfig.recommended,
      available_connections: relevantConnections,
      data_types: this.extractDataTypes(relevantConnections)
    };
  }

  // Enhanced search with AI-powered query optimization
  async enhancedSearch(
    query: string,
    persona: 'sophia' | 'karen' | 'cherry',
    options: {
      include_external?: boolean;
      data_freshness_threshold?: number; // hours
      result_limit?: number;
      search_mode?: 'normal' | 'deep' | 'comprehensive';
    } = {}
  ): Promise<{
    internal_results: any[];
    external_results?: any[];
    data_sources: string[];
    search_metadata: {
      query_enhanced: string;
      sources_searched: number;
      freshness_scores: number[];
      search_time_ms: number;
    };
  }> {
    const startTime = Date.now();
    
    // Get persona-specific data sources
    const personaData = await this.getPersonaDataSources(persona);
    
    // Filter by data freshness if specified
    let targetSources = personaData.available_connections;
    if (options.data_freshness_threshold) {
      const freshnessData = await this.getDataFreshness();
      const freshSources = freshnessData.filter(f => {
        const hoursSinceSync = (Date.now() - f.last_sync.getTime()) / (1000 * 60 * 60);
        return hoursSinceSync <= options.data_freshness_threshold!;
      });
      
      targetSources = targetSources.filter(c => 
        freshSources.some(f => f.connection_id === c.connectionId)
      );
    }

    // Search internal data
    const internalResults = await this.searchInternalData(
      query,
      targetSources.map(c => c.name),
      options.result_limit || 50
    );

    const searchTime = Date.now() - startTime;

    return {
      internal_results: internalResults.results,
      data_sources: internalResults.sources_searched,
      search_metadata: {
        query_enhanced: query, // Could be enhanced with AI
        sources_searched: internalResults.sources_searched.length,
        freshness_scores: [], // Would calculate actual freshness scores
        search_time_ms: searchTime
      }
    };
  }

  private async refreshTokenIfNeeded(): Promise<void> {
    // Check if token is expired and refresh if needed
    try {
      const tokenPayload = JSON.parse(atob(this.accessToken.split('.')[1]));
      const expirationTime = tokenPayload.exp * 1000;
      
      if (Date.now() >= expirationTime - 300000) { // Refresh 5 minutes before expiry
        await this.refreshAccessToken();
      }
    } catch (error) {
      console.error('Error checking token expiration:', error);
    }
  }

  private async refreshAccessToken(): Promise<void> {
    try {
      const response = await fetch('https://cloud.airbyte.com/auth/realms/_airbyte-application-clients/protocol/openid-connect/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          grant_type: 'client_credentials',
          client_id: this.clientId,
          client_secret: this.clientSecret
        })
      });

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }

      const data = await response.json();
      this.accessToken = data.access_token;
    } catch (error) {
      console.error('Error refreshing access token:', error);
    }
  }

  private async searchConnectionData(
    connectionId: string,
    query: string,
    limit: number
  ): Promise<any[]> {
    // This would implement actual data search within a connection
    // For now, return mock data structure
    return [
      {
        connection_id: connectionId,
        record_id: `record_${Date.now()}`,
        content: `Mock data matching query: ${query}`,
        metadata: {
          source: 'airbyte_connection',
          timestamp: new Date(),
          relevance_score: 0.8
        }
      }
    ];
  }

  private async getLastSyncJob(connectionId: string): Promise<SyncResult | null> {
    try {
      const response = await fetch(`${this.baseUrl}/jobs?connectionId=${connectionId}&limit=1`, {
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        return null;
      }

      const data = await response.json();
      const jobs = data.data || [];
      
      if (jobs.length === 0) return null;

      const job = jobs[0];
      return {
        jobId: job.jobId,
        status: job.status,
        recordsSynced: job.recordsSynced || 0,
        bytesEmitted: job.bytesEmitted || 0,
        startTime: new Date(job.createdAt),
        endTime: job.updatedAt ? new Date(job.updatedAt) : undefined
      };
    } catch (error) {
      console.error('Error fetching last sync job:', error);
      return null;
    }
  }

  private calculateFreshnessScore(lastJob: SyncResult | null): number {
    if (!lastJob || !lastJob.endTime) return 0;

    const hoursSinceSync = (Date.now() - lastJob.endTime.getTime()) / (1000 * 60 * 60);
    
    // Score decreases as data gets older
    if (hoursSinceSync < 1) return 1.0;
    if (hoursSinceSync < 6) return 0.9;
    if (hoursSinceSync < 24) return 0.7;
    if (hoursSinceSync < 72) return 0.5;
    if (hoursSinceSync < 168) return 0.3;
    return 0.1;
  }

  private async updateConnectionSchedule(
    connectionId: string,
    schedule: 'hourly' | 'daily' | 'weekly'
  ): Promise<void> {
    const scheduleConfig = {
      hourly: { scheduleType: 'cron', cronExpression: '0 * * * *' },
      daily: { scheduleType: 'cron', cronExpression: '0 0 * * *' },
      weekly: { scheduleType: 'cron', cronExpression: '0 0 * * 0' }
    };

    try {
      await fetch(`${this.baseUrl}/connections/${connectionId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${this.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          scheduleType: scheduleConfig[schedule].scheduleType,
          scheduleData: {
            cron: {
              cronExpression: scheduleConfig[schedule].cronExpression,
              cronTimeZone: 'UTC'
            }
          }
        })
      });
    } catch (error) {
      console.error(`Error updating schedule for connection ${connectionId}:`, error);
    }
  }

  private extractDataTypes(connections: AirbyteConnection[]): string[] {
    // Extract data types from connection configurations
    const dataTypes = new Set<string>();
    
    connections.forEach(connection => {
      // This would analyze the connection configuration to determine data types
      dataTypes.add('structured');
      dataTypes.add('time_series');
      dataTypes.add('documents');
    });

    return Array.from(dataTypes);
  }
}

export default AirbyteCloudService;

