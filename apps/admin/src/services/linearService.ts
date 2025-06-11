import APIConfigService from '../config/apiConfig';

interface LinearIssue {
  id: string;
  title: string;
  description: string;
  state: string;
  priority: number;
  assignee?: string;
  labels: string[];
  createdAt: string;
  updatedAt: string;
}

interface LinearProject {
  id: string;
  name: string;
  description: string;
  state: string;
  progress: number;
  issues: LinearIssue[];
}

class LinearService {
  private config = APIConfigService.getInstance().getLinearConfig();

  async getProjects(): Promise<LinearProject[]> {
    try {
      const query = `
        query {
          projects {
            nodes {
              id
              name
              description
              state
              progress
              issues {
                nodes {
                  id
                  title
                  description
                  state {
                    name
                  }
                  priority
                  assignee {
                    name
                  }
                  labels {
                    nodes {
                      name
                    }
                  }
                  createdAt
                  updatedAt
                }
              }
            }
          }
        }
      `;

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformProjects(data.data.projects.nodes);
    } catch (error) {
      console.error('Linear service error:', error);
      throw new Error('Failed to fetch Linear projects');
    }
  }

  async createIssue(projectId: string, title: string, description: string, priority: number = 3): Promise<LinearIssue> {
    try {
      const mutation = `
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              title
              description
              state {
                name
              }
              priority
              createdAt
              updatedAt
            }
          }
        }
      `;

      const variables = {
        input: {
          title,
          description,
          priority,
          projectId
        }
      };

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      if (!response.ok) {
        throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.data.issueCreate.success) {
        throw new Error('Failed to create Linear issue');
      }

      return this.transformIssue(data.data.issueCreate.issue);
    } catch (error) {
      console.error('Linear create issue error:', error);
      throw new Error('Failed to create Linear issue');
    }
  }

  async updateIssue(issueId: string, updates: Partial<LinearIssue>): Promise<LinearIssue> {
    try {
      const mutation = `
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              title
              description
              state {
                name
              }
              priority
              updatedAt
            }
          }
        }
      `;

      const variables = {
        id: issueId,
        input: {
          ...(updates.title && { title: updates.title }),
          ...(updates.description && { description: updates.description }),
          ...(updates.priority && { priority: updates.priority })
        }
      };

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      if (!response.ok) {
        throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      if (!data.data.issueUpdate.success) {
        throw new Error('Failed to update Linear issue');
      }

      return this.transformIssue(data.data.issueUpdate.issue);
    } catch (error) {
      console.error('Linear update issue error:', error);
      throw new Error('Failed to update Linear issue');
    }
  }

  async searchIssues(query: string): Promise<LinearIssue[]> {
    try {
      const searchQuery = `
        query IssueSearch($query: String!) {
          issueSearch(query: $query) {
            nodes {
              id
              title
              description
              state {
                name
              }
              priority
              assignee {
                name
              }
              labels {
                nodes {
                  name
                }
              }
              createdAt
              updatedAt
            }
          }
        }
      `;

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query: searchQuery, 
          variables: { query } 
        })
      });

      if (!response.ok) {
        throw new Error(`Linear API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.data.issueSearch.nodes.map(this.transformIssue);
    } catch (error) {
      console.error('Linear search error:', error);
      throw new Error('Failed to search Linear issues');
    }
  }

  private transformProjects(projects: any[]): LinearProject[] {
    return projects.map(project => ({
      id: project.id,
      name: project.name,
      description: project.description || '',
      state: project.state,
      progress: project.progress || 0,
      issues: project.issues.nodes.map(this.transformIssue)
    }));
  }

  private transformIssue(issue: any): LinearIssue {
    return {
      id: issue.id,
      title: issue.title,
      description: issue.description || '',
      state: issue.state?.name || 'Unknown',
      priority: issue.priority || 3,
      assignee: issue.assignee?.name,
      labels: issue.labels?.nodes?.map((label: any) => label.name) || [],
      createdAt: issue.createdAt,
      updatedAt: issue.updatedAt
    };
  }
}

export default LinearService;
export type { LinearIssue, LinearProject };

