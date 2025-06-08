import PortkeyService from './portkeyService';
import SearchService from './searchService';
import ElevenLabsService from './elevenLabsService';
import AirbyteService from './airbyteService';
import SlideSpeakService from './slideSpeakService';
import NotionWorkflowService from './notionWorkflowService';
import AILearningService from './aiLearningService';

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

  // Clear all services (useful for testing or cleanup)
  public clearServices(): void {
    this.services.clear();
  }

  // Check if a service is initialized
  public isServiceInitialized(serviceName: string): boolean {
    return this.services.has(serviceName);
  }
}

export default ServiceManager; 