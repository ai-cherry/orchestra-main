import { Client } from '@notionhq/client';

interface NotionAnalytics {
  page_views: number;
  database_queries: number;
  user_interactions: number;
  content_updates: number;
  search_queries: number;
  performance_metrics: {
    avg_response_time: number;
    success_rate: number;
    error_rate: number;
  };
}

interface WorkflowStep {
  id: string;
  name: string;
  type: 'search' | 'create' | 'update' | 'analyze' | 'notify';
  config: any;
  dependencies: string[];
  persona_specific?: 'sophia' | 'karen' | 'cherry';
}

interface Workflow {
  id: string;
  name: string;
  description: string;
  trigger: 'manual' | 'scheduled' | 'event';
  steps: WorkflowStep[];
  persona: 'sophia' | 'karen' | 'cherry' | 'all';
  active: boolean;
}

class NotionWorkflowService {
  private notion: Client;
  private workflowsDatabase = 'your_workflows_database_id'; // Replace with actual ID
  private analyticsDatabase = 'your_analytics_database_id'; // Replace with actual ID

  constructor() {
    this.notion = new Client({
      auth: process.env.NOTION_TOKEN
    });
  }

  // Get Notion analytics for dashboard
  async getNotionAnalytics(timeRange: '24h' | '7d' | '30d' = '24h'): Promise<NotionAnalytics> {
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeRange) {
        case '24h':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
      }

      // Query analytics database
      const analyticsResponse = await this.notion.databases.query({
        database_id: this.analyticsDatabase,
        filter: {
          and: [
            {
              property: 'Date',
              date: {
                on_or_after: startDate.toISOString()
              }
            },
            {
              property: 'Date',
              date: {
                on_or_before: endDate.toISOString()
              }
            }
          ]
        }
      });

      // Aggregate analytics data
      const analytics = this.aggregateAnalytics(analyticsResponse.results);
      return analytics;
    } catch (error) {
      console.error('Error fetching Notion analytics:', error);
      return this.getDefaultAnalytics();
    }
  }

  // Create automated workflow
  async createWorkflow(workflow: Omit<Workflow, 'id'>): Promise<string> {
    try {
      const response = await this.notion.pages.create({
        parent: {
          database_id: this.workflowsDatabase
        },
        properties: {
          'Name': {
            title: [
              {
                text: {
                  content: workflow.name
                }
              }
            ]
          },
          'Description': {
            rich_text: [
              {
                text: {
                  content: workflow.description
                }
              }
            ]
          },
          'Trigger': {
            select: {
              name: workflow.trigger
            }
          },
          'Persona': {
            select: {
              name: workflow.persona
            }
          },
          'Active': {
            checkbox: workflow.active
          },
          'Steps': {
            rich_text: [
              {
                text: {
                  content: JSON.stringify(workflow.steps, null, 2)
                }
              }
            ]
          }
        }
      });

      return response.id;
    } catch (error) {
      console.error('Error creating workflow:', error);
      throw error;
    }
  }

  // Execute workflow
  async executeWorkflow(workflowId: string, context?: any): Promise<{
    success: boolean;
    results: any[];
    errors: string[];
  }> {
    try {
      // Get workflow from Notion
      const workflow = await this.getWorkflow(workflowId);
      if (!workflow) {
        throw new Error('Workflow not found');
      }

      const results: any[] = [];
      const errors: string[] = [];

      // Execute steps in order
      for (const step of workflow.steps) {
        try {
          const stepResult = await this.executeWorkflowStep(step, context, results);
          results.push(stepResult);
        } catch (error) {
          errors.push(`Step ${step.name}: ${error.message}`);
        }
      }

      // Log execution
      await this.logWorkflowExecution(workflowId, results, errors);

      return {
        success: errors.length === 0,
        results,
        errors
      };
    } catch (error) {
      console.error('Error executing workflow:', error);
      return {
        success: false,
        results: [],
        errors: [error.message]
      };
    }
  }

  // Get active workflows for persona
  async getPersonaWorkflows(persona: 'sophia' | 'karen' | 'cherry'): Promise<Workflow[]> {
    try {
      const response = await this.notion.databases.query({
        database_id: this.workflowsDatabase,
        filter: {
          and: [
            {
              property: 'Active',
              checkbox: {
                equals: true
              }
            },
            {
              or: [
                {
                  property: 'Persona',
                  select: {
                    equals: persona
                  }
                },
                {
                  property: 'Persona',
                  select: {
                    equals: 'all'
                  }
                }
              ]
            }
          ]
        }
      });

      return response.results.map(page => this.parseWorkflowFromPage(page));
    } catch (error) {
      console.error('Error fetching persona workflows:', error);
      return [];
    }
  }

  // Schedule workflow execution
  async scheduleWorkflow(
    workflowId: string,
    schedule: 'hourly' | 'daily' | 'weekly' | 'monthly',
    startTime?: Date
  ): Promise<boolean> {
    try {
      // Update workflow with schedule information
      await this.notion.pages.update({
        page_id: workflowId,
        properties: {
          'Schedule': {
            select: {
              name: schedule
            }
          },
          'Next Run': {
            date: {
              start: (startTime || new Date()).toISOString()
            }
          }
        }
      });

      return true;
    } catch (error) {
      console.error('Error scheduling workflow:', error);
      return false;
    }
  }

  // Track workflow performance
  async trackWorkflowPerformance(
    workflowId: string,
    executionTime: number,
    success: boolean,
    results: any[]
  ): Promise<void> {
    try {
      await this.notion.pages.create({
        parent: {
          database_id: this.analyticsDatabase
        },
        properties: {
          'Workflow ID': {
            rich_text: [
              {
                text: {
                  content: workflowId
                }
              }
            ]
          },
          'Execution Time': {
            number: executionTime
          },
          'Success': {
            checkbox: success
          },
          'Results Count': {
            number: results.length
          },
          'Date': {
            date: {
              start: new Date().toISOString()
            }
          }
        }
      });
    } catch (error) {
      console.error('Error tracking workflow performance:', error);
    }
  }

  // Get workflow suggestions based on user behavior
  async getWorkflowSuggestions(
    persona: 'sophia' | 'karen' | 'cherry',
    recentActions: string[]
  ): Promise<{
    suggested_workflows: Workflow[];
    automation_opportunities: string[];
    efficiency_gains: number[];
  }> {
    try {
      // Analyze recent actions to suggest workflows
      const suggestions = this.analyzeActionsForWorkflows(persona, recentActions);
      
      // Get existing workflows that might be relevant
      const existingWorkflows = await this.getPersonaWorkflows(persona);
      
      // Filter out already existing workflows
      const newSuggestions = suggestions.filter(suggestion => 
        !existingWorkflows.some(existing => existing.name === suggestion.name)
      );

      return {
        suggested_workflows: newSuggestions,
        automation_opportunities: this.identifyAutomationOpportunities(recentActions),
        efficiency_gains: this.calculateEfficiencyGains(newSuggestions)
      };
    } catch (error) {
      console.error('Error getting workflow suggestions:', error);
      return {
        suggested_workflows: [],
        automation_opportunities: [],
        efficiency_gains: []
      };
    }
  }

  // Create smart dashboard widgets
  async createDashboardWidget(
    type: 'analytics' | 'workflows' | 'performance' | 'suggestions',
    persona: 'sophia' | 'karen' | 'cherry',
    config: any
  ): Promise<any> {
    switch (type) {
      case 'analytics':
        return await this.createAnalyticsWidget(persona, config);
      case 'workflows':
        return await this.createWorkflowsWidget(persona, config);
      case 'performance':
        return await this.createPerformanceWidget(persona, config);
      case 'suggestions':
        return await this.createSuggestionsWidget(persona, config);
      default:
        throw new Error(`Unknown widget type: ${type}`);
    }
  }

  private async getWorkflow(workflowId: string): Promise<Workflow | null> {
    try {
      const response = await this.notion.pages.retrieve({
        page_id: workflowId
      });

      return this.parseWorkflowFromPage(response);
    } catch (error) {
      console.error('Error fetching workflow:', error);
      return null;
    }
  }

  private async executeWorkflowStep(
    step: WorkflowStep,
    context: any,
    previousResults: any[]
  ): Promise<any> {
    switch (step.type) {
      case 'search':
        return await this.executeSearchStep(step, context);
      case 'create':
        return await this.executeCreateStep(step, context, previousResults);
      case 'update':
        return await this.executeUpdateStep(step, context, previousResults);
      case 'analyze':
        return await this.executeAnalyzeStep(step, context, previousResults);
      case 'notify':
        return await this.executeNotifyStep(step, context, previousResults);
      default:
        throw new Error(`Unknown step type: ${step.type}`);
    }
  }

  private async executeSearchStep(step: WorkflowStep, context: any): Promise<any> {
    // Implement search step execution
    return {
      step_id: step.id,
      type: 'search',
      results: [],
      timestamp: new Date()
    };
  }

  private async executeCreateStep(
    step: WorkflowStep,
    context: any,
    previousResults: any[]
  ): Promise<any> {
    // Implement create step execution
    return {
      step_id: step.id,
      type: 'create',
      created_items: [],
      timestamp: new Date()
    };
  }

  private async executeUpdateStep(
    step: WorkflowStep,
    context: any,
    previousResults: any[]
  ): Promise<any> {
    // Implement update step execution
    return {
      step_id: step.id,
      type: 'update',
      updated_items: [],
      timestamp: new Date()
    };
  }

  private async executeAnalyzeStep(
    step: WorkflowStep,
    context: any,
    previousResults: any[]
  ): Promise<any> {
    // Implement analyze step execution
    return {
      step_id: step.id,
      type: 'analyze',
      analysis_results: {},
      timestamp: new Date()
    };
  }

  private async executeNotifyStep(
    step: WorkflowStep,
    context: any,
    previousResults: any[]
  ): Promise<any> {
    // Implement notify step execution
    return {
      step_id: step.id,
      type: 'notify',
      notifications_sent: [],
      timestamp: new Date()
    };
  }

  private async logWorkflowExecution(
    workflowId: string,
    results: any[],
    errors: string[]
  ): Promise<void> {
    try {
      await this.notion.pages.create({
        parent: {
          database_id: this.analyticsDatabase
        },
        properties: {
          'Type': {
            select: {
              name: 'workflow_execution'
            }
          },
          'Workflow ID': {
            rich_text: [
              {
                text: {
                  content: workflowId
                }
              }
            ]
          },
          'Results': {
            rich_text: [
              {
                text: {
                  content: JSON.stringify(results, null, 2)
                }
              }
            ]
          },
          'Errors': {
            rich_text: [
              {
                text: {
                  content: errors.join(', ')
                }
              }
            ]
          },
          'Date': {
            date: {
              start: new Date().toISOString()
            }
          }
        }
      });
    } catch (error) {
      console.error('Error logging workflow execution:', error);
    }
  }

  private parseWorkflowFromPage(page: any): Workflow {
    // Parse Notion page into Workflow object
    return {
      id: page.id,
      name: page.properties.Name?.title?.[0]?.text?.content || '',
      description: page.properties.Description?.rich_text?.[0]?.text?.content || '',
      trigger: page.properties.Trigger?.select?.name || 'manual',
      steps: JSON.parse(page.properties.Steps?.rich_text?.[0]?.text?.content || '[]'),
      persona: page.properties.Persona?.select?.name || 'all',
      active: page.properties.Active?.checkbox || false
    };
  }

  private aggregateAnalytics(results: any[]): NotionAnalytics {
    // Aggregate analytics from Notion results
    return {
      page_views: results.length,
      database_queries: results.filter(r => r.properties.Type?.select?.name === 'database_query').length,
      user_interactions: results.filter(r => r.properties.Type?.select?.name === 'user_interaction').length,
      content_updates: results.filter(r => r.properties.Type?.select?.name === 'content_update').length,
      search_queries: results.filter(r => r.properties.Type?.select?.name === 'search_query').length,
      performance_metrics: {
        avg_response_time: 250, // Calculate from actual data
        success_rate: 0.95,
        error_rate: 0.05
      }
    };
  }

  private getDefaultAnalytics(): NotionAnalytics {
    return {
      page_views: 0,
      database_queries: 0,
      user_interactions: 0,
      content_updates: 0,
      search_queries: 0,
      performance_metrics: {
        avg_response_time: 0,
        success_rate: 0,
        error_rate: 0
      }
    };
  }

  private analyzeActionsForWorkflows(
    persona: string,
    recentActions: string[]
  ): Workflow[] {
    // Analyze recent actions to suggest new workflows
    const suggestions: Workflow[] = [];

    // Example: If user frequently searches and creates presentations
    if (recentActions.includes('search') && recentActions.includes('create_presentation')) {
      suggestions.push({
        id: 'suggested_' + Date.now(),
        name: 'Auto Research & Present',
        description: 'Automatically research a topic and create a presentation',
        trigger: 'manual',
        steps: [
          {
            id: 'search_step',
            name: 'Research Topic',
            type: 'search',
            config: { sources: ['all'], depth: 'deep' },
            dependencies: []
          },
          {
            id: 'create_step',
            name: 'Create Presentation',
            type: 'create',
            config: { type: 'presentation', template: 'business' },
            dependencies: ['search_step']
          }
        ],
        persona: persona as any,
        active: false
      });
    }

    return suggestions;
  }

  private identifyAutomationOpportunities(recentActions: string[]): string[] {
    const opportunities: string[] = [];

    // Identify repetitive patterns
    const actionCounts = recentActions.reduce((acc, action) => {
      acc[action] = (acc[action] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    Object.entries(actionCounts).forEach(([action, count]) => {
      if (count > 3) {
        opportunities.push(`Automate frequent ${action} operations`);
      }
    });

    return opportunities;
  }

  private calculateEfficiencyGains(workflows: Workflow[]): number[] {
    // Calculate estimated efficiency gains for each workflow
    return workflows.map(workflow => {
      const stepCount = workflow.steps.length;
      const estimatedTimePerStep = 30; // seconds
      const manualTime = stepCount * estimatedTimePerStep;
      const automatedTime = 5; // seconds for automated execution
      
      return ((manualTime - automatedTime) / manualTime) * 100;
    });
  }

  private async createAnalyticsWidget(persona: string, config: any): Promise<any> {
    const analytics = await this.getNotionAnalytics(config.timeRange || '24h');
    
    return {
      type: 'analytics',
      persona,
      data: analytics,
      config,
      last_updated: new Date()
    };
  }

  private async createWorkflowsWidget(persona: string, config: any): Promise<any> {
    const workflows = await this.getPersonaWorkflows(persona as any);
    
    return {
      type: 'workflows',
      persona,
      data: {
        active_workflows: workflows.filter(w => w.active).length,
        total_workflows: workflows.length,
        recent_executions: [] // Would fetch from analytics
      },
      config,
      last_updated: new Date()
    };
  }

  private async createPerformanceWidget(persona: string, config: any): Promise<any> {
    // Create performance metrics widget
    return {
      type: 'performance',
      persona,
      data: {
        response_times: [],
        success_rates: [],
        error_counts: []
      },
      config,
      last_updated: new Date()
    };
  }

  private async createSuggestionsWidget(persona: string, config: any): Promise<any> {
    const suggestions = await this.getWorkflowSuggestions(persona as any, []);
    
    return {
      type: 'suggestions',
      persona,
      data: suggestions,
      config,
      last_updated: new Date()
    };
  }
}

export default NotionWorkflowService;

