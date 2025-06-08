class RateLimiter {
  private queues = new Map<string, Array<() => Promise<any>>>();
  private timers = new Map<string, NodeJS.Timeout>();
  private limits = new Map<string, { requests: number; window: number; current: number; resetTime: number }>();

  constructor() {
    // Default rate limits for different services
    this.setLimit('linear', 100, 60000); // 100 requests per minute
    this.setLimit('github', 5000, 3600000); // 5000 requests per hour
    this.setLimit('asana', 150, 60000); // 150 requests per minute
    this.setLimit('notion', 3, 1000); // 3 requests per second
    this.setLimit('portkey', 1000, 60000); // 1000 requests per minute
    this.setLimit('default', 60, 60000); // 60 requests per minute default
  }

  setLimit(service: string, requests: number, windowMs: number) {
    this.limits.set(service, {
      requests,
      window: windowMs,
      current: 0,
      resetTime: Date.now() + windowMs
    });
  }

  async execute<T>(service: string, fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      const limit = this.limits.get(service) || this.limits.get('default')!;
      
      // Reset counter if window has passed
      if (Date.now() > limit.resetTime) {
        limit.current = 0;
        limit.resetTime = Date.now() + limit.window;
      }

      // If under limit, execute immediately
      if (limit.current < limit.requests) {
        limit.current++;
        fn().then(resolve).catch(reject);
        return;
      }

      // Add to queue
      if (!this.queues.has(service)) {
        this.queues.set(service, []);
      }

      this.queues.get(service)!.push(async () => {
        try {
          limit.current++;
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      // Set timer to process queue
      if (!this.timers.has(service)) {
        const timer = setTimeout(() => {
          this.processQueue(service);
          this.timers.delete(service);
        }, limit.resetTime - Date.now());
        
        this.timers.set(service, timer);
      }
    });
  }

  private processQueue(service: string) {
    const queue = this.queues.get(service);
    const limit = this.limits.get(service) || this.limits.get('default')!;
    
    if (!queue || queue.length === 0) return;

    // Reset counter for new window
    limit.current = 0;
    limit.resetTime = Date.now() + limit.window;

    // Process as many requests as allowed
    const toProcess = Math.min(queue.length, limit.requests);
    const batch = queue.splice(0, toProcess);
    
    batch.forEach(fn => fn());

    // If more requests in queue, set timer for next window
    if (queue.length > 0) {
      const timer = setTimeout(() => {
        this.processQueue(service);
        this.timers.delete(service);
      }, limit.window);
      
      this.timers.set(service, timer);
    }
  }

  getStatus(service: string) {
    const limit = this.limits.get(service) || this.limits.get('default')!;
    const queueLength = this.queues.get(service)?.length || 0;
    
    return {
      current: limit.current,
      limit: limit.requests,
      remaining: limit.requests - limit.current,
      resetTime: limit.resetTime,
      queueLength
    };
  }
}

export const rateLimiter = new RateLimiter();

