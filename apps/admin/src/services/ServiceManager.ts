import PortkeyService from './portkeyService';
import SearchService from './searchService';
import ElevenLabsService from './elevenLabsService';
import AirbyteService from './airbyteService';
import SlideSpeakService from './slideSpeakService';
import NotionWorkflowService from './notionWorkflowService';
import AILearningService from './aiLearningService';
import LinearService from './linearService';
import GitHubProjectsService from './githubProjectsService';
import AsanaService from './asanaService';
import MLService from './mlService';
import CryptoJS from 'crypto-js';

const ENCRYPTION_KEY = process.env.VITE_ENCRYPTION_KEY || 'default-dev-key';

function encrypt(text: string): string {
  return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
}

function decrypt(cipher: string): string {
  const bytes = CryptoJS.AES.decrypt(cipher, ENCRYPTION_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}

function getUserProjectConfig(): { linearProjectId?: string; asanaProjectId?: string } {
  const enc = localStorage.getItem('orchestra_project_config');
  if (!enc) return {};
  try {
    return JSON.parse(decrypt(enc));
  } catch {
    return {};
  }
}

function setUserProjectConfig(config: { linearProjectId?: string; asanaProjectId?: string }) {
  localStorage.setItem('orchestra_project_config', encrypt(JSON.stringify(config)));
}

class ServiceManager {
  private static instance: ServiceManager;
  private services: Map<string, any> = new Map();

  private constructor() {}

  public static getInstance(): ServiceManager {
    if (!ServiceManager.instance) {
      ServiceManager.instance = new ServiceManager();
    }
    return ServiceManager.instance;
  }

  public getPortkeyService(): PortkeyService {
    if (!this.services.has('portkey')) {
      this.services.set('portkey', new PortkeyService());
    }
    return this.services.get('portkey');
  }

  public getSearchService(): SearchService {
    if (!this.services.has('search')) {
      this.services.set('search', new SearchService());
    }
    return this.services.get('search');
  }

  public getElevenLabsService(): ElevenLabsService {
    if (!this.services.has('elevenLabs')) {
      this.services.set('elevenLabs', new ElevenLabsService());
    }
    return this.services.get('elevenLabs');
  }

  public getAirbyteService(): AirbyteService {
    if (!this.services.has('airbyte')) {
      this.services.set('airbyte', new AirbyteService());
    }
    return this.services.get('airbyte');
  }

  public getSlideSpeakService(): SlideSpeakService {
    if (!this.services.has('slideSpeak')) {
      this.services.set('slideSpeak', new SlideSpeakService());
    }
    return this.services.get('slideSpeak');
  }

  public getNotionWorkflowService(): NotionWorkflowService {
    if (!this.services.has('notionWorkflow')) {
      this.services.set('notionWorkflow', new NotionWorkflowService());
    }
    return this.services.get('notionWorkflow');
  }

  public getAILearningService(): AILearningService {
    if (!this.services.has('aiLearning')) {
      this.services.set('aiLearning', new AILearningService());
    }
    return this.services.get('aiLearning');
  }

  public getLinearService(): LinearService {
    if (!this.services.has('linear')) {
      this.services.set('linear', new LinearService());
    }
    return this.services.get('linear');
  }

  public getGitHubProjectsService(): GitHubProjectsService {
    if (!this.services.has('githubProjects')) {
      this.services.set('githubProjects', new GitHubProjectsService());
    }
    return this.services.get('githubProjects');
  }

  public getAsanaService(): AsanaService {
    if (!this.services.has('asana')) {
      this.services.set('asana', new AsanaService());
    }
    return this.services.get('asana');
  }

  public getMLService(): MLService {
    if (!this.services.has('ml')) {
      this.services.set('ml', new MLService());
    }
    return this.services.get('ml');
  }

  // Convenience methods for common operations
  public async searchAcrossAllPlatforms(query: string): Promise<any> {
    const searchService = this.getSearchService();
    const linearService = this.getLinearService();
    const githubService = this.getGitHubProjectsService();
    const asanaService = this.getAsanaService();

    try {
      const [webResults, linearResults, githubResults, asanaResults] = await Promise.allSettled([
        searchService.search(query),
        linearService.searchIssues(query),
        githubService.searchIssues('ai-cherry', 'orchestra-main', query),
        asanaService.searchTasks(query)
      ]);

      return {
        web: webResults.status === 'fulfilled' ? webResults.value : [],
        linear: linearResults.status === 'fulfilled' ? linearResults.value : [],
        github: githubResults.status === 'fulfilled' ? githubResults.value : [],
        asana: asanaResults.status === 'fulfilled' ? asanaResults.value : []
      };
    } catch (error) {
      console.error('Cross-platform search error:', error);
      throw new Error('Failed to search across platforms');
    }
  }

  public async createTaskAcrossAllPlatforms(title: string, description: string): Promise<any> {
    const linearService = this.getLinearService();
    const githubService = this.getGitHubProjectsService();
    const asanaService = this.getAsanaService();

    try {
      // Get default project IDs from user config
      const { linearProjectId, asanaProjectId } = getUserProjectConfig();
      if (!linearProjectId || !asanaProjectId) {
        throw new Error('Default project IDs not configured. Please set up your project config.');
      }

      const [linearTask, githubIssue, asanaTask] = await Promise.allSettled([
        linearService.createIssue(linearProjectId, title, description),
        githubService.createIssue('ai-cherry', 'orchestra-main', title, description),
        asanaService.createTask(asanaProjectId, title, description)
      ]);

      return {
        linear: linearTask.status === 'fulfilled' ? linearTask.value : null,
        github: githubIssue.status === 'fulfilled' ? githubIssue.value : null,
        asana: asanaTask.status === 'fulfilled' ? asanaTask.value : null
      };
    } catch (error) {
      console.error('Cross-platform task creation error:', error);
      throw new Error('Failed to create tasks across platforms');
    }
  }

  public async getUnifiedDashboard(): Promise<any> {
    const linearService = this.getLinearService();
    const githubService = this.getGitHubProjectsService();
    const asanaService = this.getAsanaService();

    try {
      const [linearProjects, githubProjects, asanaProjects] = await Promise.allSettled([
        linearService.getProjects(),
        githubService.getProjects('ai-cherry', 'orchestra-main'),
        asanaService.getProjects()
      ]);

      return {
        linear: {
          projects: linearProjects.status === 'fulfilled' ? linearProjects.value : [],
          status: linearProjects.status
        },
        github: {
          projects: githubProjects.status === 'fulfilled' ? githubProjects.value : [],
          status: githubProjects.status
        },
        asana: {
          projects: asanaProjects.status === 'fulfilled' ? asanaProjects.value : [],
          status: asanaProjects.status
        }
      };
    } catch (error) {
      console.error('Unified dashboard error:', error);
      throw new Error('Failed to load unified dashboard');
    }
  }

  // Clear all service instances (useful for testing or config changes)
  public clearServices(): void {
    this.services.clear();
  }

  // Get service health status
  public async getServiceHealth(): Promise<Record<string, boolean>> {
    const services = [
      'portkey', 'search', 'elevenLabs', 'airbyte', 'slideSpeak',
      'notionWorkflow', 'aiLearning', 'linear', 'githubProjects', 'asana', 'ml'
    ];

    const healthStatus: Record<string, boolean> = {};

    for (const serviceName of services) {
      try {
        // Simple health check - try to instantiate the service
        const service = this.services.get(serviceName) || this.getServiceByName(serviceName);
        healthStatus[serviceName] = !!service;
      } catch (error) {
        healthStatus[serviceName] = false;
      }
    }

    return healthStatus;
  }

  private getServiceByName(serviceName: string): any {
    switch (serviceName) {
      case 'portkey': return this.getPortkeyService();
      case 'search': return this.getSearchService();
      case 'elevenLabs': return this.getElevenLabsService();
      case 'airbyte': return this.getAirbyteService();
      case 'slideSpeak': return this.getSlideSpeakService();
      case 'notionWorkflow': return this.getNotionWorkflowService();
      case 'aiLearning': return this.getAILearningService();
      case 'linear': return this.getLinearService();
      case 'githubProjects': return this.getGitHubProjectsService();
      case 'asana': return this.getAsanaService();
      case 'ml': return this.getMLService();
      default: return null;
    }
  }
}

export default ServiceManager;

