import APIConfigService from '../config/apiConfig';

interface GitHubProject {
  id: string;
  number: number;
  title: string;
  body: string;
  state: string;
  url: string;
  items: GitHubProjectItem[];
  createdAt: string;
  updatedAt: string;
}

interface GitHubProjectItem {
  id: string;
  title: string;
  body: string;
  state: string;
  type: 'ISSUE' | 'PULL_REQUEST' | 'DRAFT_ISSUE';
  assignees: string[];
  labels: string[];
  url: string;
  createdAt: string;
  updatedAt: string;
}

class GitHubProjectsService {
  private config = APIConfigService.getInstance().getGitHubConfig();

  async getProjects(owner: string, repo: string): Promise<GitHubProject[]> {
    try {
      const query = `
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            projectsV2(first: 20) {
              nodes {
                id
                number
                title
                shortDescription
                url
                items(first: 50) {
                  nodes {
                    id
                    type
                    content {
                      ... on Issue {
                        id
                        title
                        body
                        state
                        url
                        assignees(first: 10) {
                          nodes {
                            login
                          }
                        }
                        labels(first: 10) {
                          nodes {
                            name
                          }
                        }
                        createdAt
                        updatedAt
                      }
                      ... on PullRequest {
                        id
                        title
                        body
                        state
                        url
                        assignees(first: 10) {
                          nodes {
                            login
                          }
                        }
                        labels(first: 10) {
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
                createdAt
                updatedAt
              }
            }
          }
        }
      `;

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query, 
          variables: { owner, repo } 
        })
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformProjects(data.data.repository.projectsV2.nodes);
    } catch (error) {
      console.error('GitHub Projects service error:', error);
      throw new Error('Failed to fetch GitHub projects');
    }
  }

  async createIssue(owner: string, repo: string, title: string, body: string, labels: string[] = []): Promise<any> {
    try {
      const mutation = `
        mutation($input: CreateIssueInput!) {
          createIssue(input: $input) {
            issue {
              id
              number
              title
              body
              state
              url
              createdAt
              updatedAt
            }
          }
        }
      `;

      const variables = {
        input: {
          repositoryId: await this.getRepositoryId(owner, repo),
          title,
          body,
          labelIds: await this.getLabelIds(owner, repo, labels)
        }
      };

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.data.createIssue.issue;
    } catch (error) {
      console.error('GitHub create issue error:', error);
      throw new Error('Failed to create GitHub issue');
    }
  }

  async updateIssue(owner: string, repo: string, issueNumber: number, updates: any): Promise<any> {
    try {
      const issueId = await this.getIssueId(owner, repo, issueNumber);
      
      const mutation = `
        mutation($input: UpdateIssueInput!) {
          updateIssue(input: $input) {
            issue {
              id
              number
              title
              body
              state
              url
              updatedAt
            }
          }
        }
      `;

      const variables = {
        input: {
          id: issueId,
          ...(updates.title && { title: updates.title }),
          ...(updates.body && { body: updates.body }),
          ...(updates.state && { state: updates.state })
        }
      };

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: mutation, variables })
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.data.updateIssue.issue;
    } catch (error) {
      console.error('GitHub update issue error:', error);
      throw new Error('Failed to update GitHub issue');
    }
  }

  async searchIssues(owner: string, repo: string, query: string): Promise<any[]> {
    try {
      const searchQuery = `
        query($query: String!) {
          search(query: $query, type: ISSUE, first: 20) {
            nodes {
              ... on Issue {
                id
                number
                title
                body
                state
                url
                assignees(first: 10) {
                  nodes {
                    login
                  }
                }
                labels(first: 10) {
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
      `;

      const searchString = `repo:${owner}/${repo} ${query}`;

      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          query: searchQuery, 
          variables: { query: searchString } 
        })
      });

      if (!response.ok) {
        throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.data.search.nodes;
    } catch (error) {
      console.error('GitHub search error:', error);
      throw new Error('Failed to search GitHub issues');
    }
  }

  private async getRepositoryId(owner: string, repo: string): Promise<string> {
    const query = `
      query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
          id
        }
      }
    `;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, variables: { owner, repo } })
    });

    const data = await response.json();
    return data.data.repository.id;
  }

  private async getIssueId(owner: string, repo: string, issueNumber: number): Promise<string> {
    const query = `
      query($owner: String!, $repo: String!, $number: Int!) {
        repository(owner: $owner, name: $repo) {
          issue(number: $number) {
            id
          }
        }
      }
    `;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, variables: { owner, repo, number: issueNumber } })
    });

    const data = await response.json();
    return data.data.repository.issue.id;
  }

  private async getLabelIds(owner: string, repo: string, labelNames: string[]): Promise<string[]> {
    if (labelNames.length === 0) return [];

    const query = `
      query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
          labels(first: 100) {
            nodes {
              id
              name
            }
          }
        }
      }
    `;

    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ query, variables: { owner, repo } })
    });

    const data = await response.json();
    const labels = data.data.repository.labels.nodes;
    
    return labelNames
      .map(name => labels.find((label: any) => label.name === name)?.id)
      .filter(Boolean);
  }

  private transformProjects(projects: any[]): GitHubProject[] {
    return projects.map(project => ({
      id: project.id,
      number: project.number,
      title: project.title,
      body: project.shortDescription || '',
      state: 'OPEN', // Projects don't have states like issues
      url: project.url,
      items: project.items.nodes.map(this.transformProjectItem),
      createdAt: project.createdAt,
      updatedAt: project.updatedAt
    }));
  }

  private transformProjectItem(item: any): GitHubProjectItem {
    const content = item.content;
    return {
      id: content.id,
      title: content.title,
      body: content.body || '',
      state: content.state,
      type: item.type,
      assignees: content.assignees?.nodes?.map((assignee: any) => assignee.login) || [],
      labels: content.labels?.nodes?.map((label: any) => label.name) || [],
      url: content.url,
      createdAt: content.createdAt,
      updatedAt: content.updatedAt
    };
  }
}

export default GitHubProjectsService;
export type { GitHubProject, GitHubProjectItem };

