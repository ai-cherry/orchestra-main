import APIConfigService from '../config/apiConfig';

interface AsanaTask {
  gid: string;
  name: string;
  notes: string;
  completed: boolean;
  assignee?: string;
  projects: string[];
  tags: string[];
  due_on?: string;
  created_at: string;
  modified_at: string;
}

interface AsanaProject {
  gid: string;
  name: string;
  notes: string;
  color: string;
  archived: boolean;
  tasks: AsanaTask[];
  created_at: string;
  modified_at: string;
}

class AsanaService {
  private config = APIConfigService.getInstance().getAsanaConfig();

  async getProjects(): Promise<AsanaProject[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/projects`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Get detailed project information including tasks
      const detailedProjects = await Promise.all(
        data.data.map(async (project: any) => {
          const projectDetails = await this.getProjectDetails(project.gid);
          const tasks = await this.getProjectTasks(project.gid);
          return {
            ...projectDetails,
            tasks
          };
        })
      );

      return detailedProjects;
    } catch (error) {
      console.error('Asana service error:', error);
      throw new Error('Failed to fetch Asana projects');
    }
  }

  async getProjectDetails(projectId: string): Promise<AsanaProject> {
    try {
      const response = await fetch(`${this.config.baseUrl}/projects/${projectId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformProject(data.data);
    } catch (error) {
      console.error('Asana get project details error:', error);
      throw new Error('Failed to fetch Asana project details');
    }
  }

  async getProjectTasks(projectId: string): Promise<AsanaTask[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/projects/${projectId}/tasks`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Get detailed task information
      const detailedTasks = await Promise.all(
        data.data.map(async (task: any) => {
          return await this.getTaskDetails(task.gid);
        })
      );

      return detailedTasks;
    } catch (error) {
      console.error('Asana get project tasks error:', error);
      throw new Error('Failed to fetch Asana project tasks');
    }
  }

  async getTaskDetails(taskId: string): Promise<AsanaTask> {
    try {
      const response = await fetch(`${this.config.baseUrl}/tasks/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformTask(data.data);
    } catch (error) {
      console.error('Asana get task details error:', error);
      throw new Error('Failed to fetch Asana task details');
    }
  }

  async createTask(projectId: string, name: string, notes: string = '', assignee?: string): Promise<AsanaTask> {
    try {
      const taskData: any = {
        name,
        notes,
        projects: [projectId]
      };

      if (assignee) {
        taskData.assignee = assignee;
      }

      const response = await fetch(`${this.config.baseUrl}/tasks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ data: taskData })
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformTask(data.data);
    } catch (error) {
      console.error('Asana create task error:', error);
      throw new Error('Failed to create Asana task');
    }
  }

  async updateTask(taskId: string, updates: Partial<AsanaTask>): Promise<AsanaTask> {
    try {
      const updateData: any = {};
      
      if (updates.name) updateData.name = updates.name;
      if (updates.notes) updateData.notes = updates.notes;
      if (updates.completed !== undefined) updateData.completed = updates.completed;
      if (updates.due_on) updateData.due_on = updates.due_on;

      const response = await fetch(`${this.config.baseUrl}/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ data: updateData })
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return this.transformTask(data.data);
    } catch (error) {
      console.error('Asana update task error:', error);
      throw new Error('Failed to update Asana task');
    }
  }

  async searchTasks(query: string): Promise<AsanaTask[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/tasks/search?text=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Get detailed task information
      const detailedTasks = await Promise.all(
        data.data.map(async (task: any) => {
          return await this.getTaskDetails(task.gid);
        })
      );

      return detailedTasks;
    } catch (error) {
      console.error('Asana search error:', error);
      throw new Error('Failed to search Asana tasks');
    }
  }

  async completeTask(taskId: string): Promise<AsanaTask> {
    return this.updateTask(taskId, { completed: true });
  }

  async addTaskToProject(taskId: string, projectId: string): Promise<void> {
    try {
      const response = await fetch(`${this.config.baseUrl}/tasks/${taskId}/addProject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.config.accessToken}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          data: { 
            project: projectId 
          } 
        })
      });

      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Asana add task to project error:', error);
      throw new Error('Failed to add task to Asana project');
    }
  }

  private transformProject(project: any): AsanaProject {
    return {
      gid: project.gid,
      name: project.name,
      notes: project.notes || '',
      color: project.color || 'none',
      archived: project.archived || false,
      tasks: [], // Will be populated separately
      created_at: project.created_at,
      modified_at: project.modified_at
    };
  }

  private transformTask(task: any): AsanaTask {
    return {
      gid: task.gid,
      name: task.name,
      notes: task.notes || '',
      completed: task.completed || false,
      assignee: task.assignee?.name,
      projects: task.projects?.map((p: any) => p.gid) || [],
      tags: task.tags?.map((t: any) => t.name) || [],
      due_on: task.due_on,
      created_at: task.created_at,
      modified_at: task.modified_at
    };
  }
}

export default AsanaService;
export type { AsanaTask, AsanaProject };

