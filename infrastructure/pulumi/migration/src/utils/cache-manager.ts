/**
 * Centralized cache management for the Pulumi Migration Framework
 * Coordinates multiple caches and provides unified access and monitoring
 */

import { ResourceCache, ResourceCacheOptions } from "./resource-cache";
import { LRUCache } from "./lru-cache";
import { ResourceState, ResourceIdentifier } from "../types";

export interface CacheManagerOptions {
    resourceCacheOptions?: ResourceCacheOptions;
    generalCacheSize?: number;
    enableMetrics?: boolean;
}

export interface CacheMetrics {
    resourceCache: {
        size: number;
        hits: number;
        misses: number;
        hitRate: number;
        evictions: number;
    };
    generalCaches: Record<string, {
        size: number;
        maxSize: number;
    }>;
    totalMemoryUsage: number;
    timestamp: number;
}

export class CacheManager {
    private resourceCache: ResourceCache;
    private generalCaches: Map<string, LRUCache<any>>;
    private metricsEnabled: boolean;
    private metricsHistory: CacheMetrics[];
    private maxMetricsHistory: number = 100;

    constructor(options: CacheManagerOptions = {}) {
        // Initialize resource cache
        this.resourceCache = new ResourceCache(options.resourceCacheOptions);
        
        // Initialize general caches map
        this.generalCaches = new Map();
        
        // Enable metrics collection
        this.metricsEnabled = options.enableMetrics ?? true;
        this.metricsHistory = [];
        
        // Start metrics collection if enabled
        if (this.metricsEnabled) {
            this.startMetricsCollection();
        }
    }

    /**
     * Resource Cache Operations
     */

    getResource(identifier: ResourceIdentifier): ResourceState | undefined {
        return this.resourceCache.get(identifier);
    }

    setResource(identifier: ResourceIdentifier, state: ResourceState): void {
        this.resourceCache.set(identifier, state);
    }

    hasResource(identifier: ResourceIdentifier): boolean {
        return this.resourceCache.has(identifier);
    }

    deleteResource(identifier: ResourceIdentifier): boolean {
        return this.resourceCache.delete(identifier);
    }

    getResourceByChecksum(checksum: string): ResourceIdentifier | undefined {
        return this.resourceCache.getByChecksum(checksum);
    }

    getResourcesByStatus(status: string): ResourceState[] {
        return this.resourceCache.getByStatus(status);
    }

    /**
     * General Cache Operations
     */

    createCache<T>(name: string, maxSize: number, ttl?: number): LRUCache<T> {
        if (this.generalCaches.has(name)) {
            throw new Error(`Cache '${name}' already exists`);
        }

        const cache = new LRUCache<T>({
            maxSize,
            ttl,
            onEvict: (key, value) => {
                // Log eviction for monitoring
                if (this.metricsEnabled) {
                    console.debug(`Cache '${name}' evicted: ${key}`);
                }
            },
        });

        this.generalCaches.set(name, cache);
        return cache;
    }

    getCache<T>(name: string): LRUCache<T> | undefined {
        return this.generalCaches.get(name) as LRUCache<T> | undefined;
    }

    deleteCache(name: string): boolean {
        const cache = this.generalCaches.get(name);
        if (cache) {
            cache.clear();
            return this.generalCaches.delete(name);
        }
        return false;
    }

    /**
     * Global Operations
     */

    clearAll(): void {
        // Clear resource cache
        this.resourceCache.clear();
        
        // Clear all general caches
        this.generalCaches.forEach(cache => cache.clear());
        this.generalCaches.clear();
        
        // Clear metrics history
        this.metricsHistory = [];
    }

    /**
     * Memory Management
     */

    async performGarbageCollection(): Promise<void> {
        // Force garbage collection if available
        if (global.gc) {
            global.gc();
        }
        
        // Wait a bit for GC to complete
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    async checkMemoryPressure(): Promise<boolean> {
        const usage = process.memoryUsage();
        const heapPercentage = (usage.heapUsed / usage.heapTotal) * 100;
        
        return heapPercentage > 85;
    }

    async handleMemoryPressure(): Promise<void> {
        const isUnderPressure = await this.checkMemoryPressure();
        
        if (isUnderPressure) {
            console.warn("High memory pressure detected, clearing caches...");
            
            // Clear general caches first (less critical)
            this.generalCaches.forEach((cache, name) => {
                console.debug(`Clearing cache: ${name}`);
                cache.clear();
            });
            
            // If still under pressure, clear resource cache
            if (await this.checkMemoryPressure()) {
                console.warn("Clearing resource cache due to memory pressure");
                this.resourceCache.clear();
            }
            
            // Perform garbage collection
            await this.performGarbageCollection();
        }
    }

    /**
     * Metrics and Monitoring
     */

    getMetrics(): CacheMetrics {
        const resourceCacheStats = this.resourceCache.getStats();
        const generalCacheStats: Record<string, { size: number; maxSize: number }> = {};
        
        this.generalCaches.forEach((cache, name) => {
            const stats = cache.getStats();
            generalCacheStats[name] = {
                size: stats.size,
                maxSize: stats.maxSize,
            };
        });
        
        const memoryUsage = process.memoryUsage();
        
        return {
            resourceCache: resourceCacheStats,
            generalCaches: generalCacheStats,
            totalMemoryUsage: memoryUsage.heapUsed,
            timestamp: Date.now(),
        };
    }

    getMetricsHistory(): CacheMetrics[] {
        return [...this.metricsHistory];
    }

    private startMetricsCollection(): void {
        // Collect metrics every 30 seconds
        setInterval(() => {
            const metrics = this.getMetrics();
            this.metricsHistory.push(metrics);
            
            // Keep only recent history
            if (this.metricsHistory.length > this.maxMetricsHistory) {
                this.metricsHistory.shift();
            }
            
            // Check memory pressure periodically
            this.handleMemoryPressure().catch(error => {
                console.error("Error handling memory pressure:", error);
            });
        }, 30000);
    }

    /**
     * Export and Import
     */

    exportState(): string {
        const state = {
            resourceCache: this.resourceCache.export(),
            generalCaches: {} as Record<string, any[]>,
            metrics: this.metricsHistory,
        };
        
        this.generalCaches.forEach((cache, name) => {
            state.generalCaches[name] = cache.values();
        });
        
        return JSON.stringify(state, null, 2);
    }

    importState(stateJson: string): void {
        try {
            const state = JSON.parse(stateJson);
            
            // Import resource cache
            if (state.resourceCache) {
                this.resourceCache.import(state.resourceCache);
            }
            
            // Import general caches
            if (state.generalCaches) {
                Object.entries(state.generalCaches).forEach(([name, values]) => {
                    // Create cache if it doesn't exist
                    if (!this.generalCaches.has(name)) {
                        this.createCache(name, 1000); // Default size
                    }
                    
                    // Import values
                    const cache = this.generalCaches.get(name);
                    if (cache && Array.isArray(values)) {
                        values.forEach((value, index) => {
                            cache.set(`imported-${index}`, value);
                        });
                    }
                });
            }
            
            // Import metrics history
            if (state.metrics && Array.isArray(state.metrics)) {
                this.metricsHistory = state.metrics;
            }
        } catch (error) {
            console.error("Failed to import cache state:", error);
            throw error;
        }
    }

    /**
     * Generate cache report
     */
    generateReport(): string {
        const metrics = this.getMetrics();
        const report = {
            timestamp: new Date().toISOString(),
            resourceCache: {
                ...metrics.resourceCache,
                hitRatePercentage: `${(metrics.resourceCache.hitRate * 100).toFixed(2)}%`,
            },
            generalCaches: metrics.generalCaches,
            memoryUsage: {
                heapUsed: `${(metrics.totalMemoryUsage / 1024 / 1024).toFixed(2)} MB`,
                heapTotal: `${(process.memoryUsage().heapTotal / 1024 / 1024).toFixed(2)} MB`,
                percentage: `${((metrics.totalMemoryUsage / process.memoryUsage().heapTotal) * 100).toFixed(2)}%`,
            },
            recommendations: this.generateRecommendations(metrics),
        };
        
        return JSON.stringify(report, null, 2);
    }

    private generateRecommendations(metrics: CacheMetrics): string[] {
        const recommendations: string[] = [];
        
        // Check hit rate
        if (metrics.resourceCache.hitRate < 0.5) {
            recommendations.push("Low cache hit rate detected. Consider increasing cache size or TTL.");
        }
        
        // Check evictions
        if (metrics.resourceCache.evictions > metrics.resourceCache.size * 0.1) {
            recommendations.push("High eviction rate detected. Consider increasing cache size.");
        }
        
        // Check memory usage
        const memoryPercentage = (metrics.totalMemoryUsage / process.memoryUsage().heapTotal) * 100;
        if (memoryPercentage > 80) {
            recommendations.push("High memory usage detected. Consider reducing cache sizes.");
        }
        
        return recommendations;
    }
}

/**
 * Singleton cache manager instance
 */
let globalCacheManager: CacheManager | null = null;

export function getGlobalCacheManager(options?: CacheManagerOptions): CacheManager {
    if (!globalCacheManager) {
        globalCacheManager = new CacheManager(options);
    }
    return globalCacheManager;
}

export function resetGlobalCacheManager(): void {
    if (globalCacheManager) {
        globalCacheManager.clearAll();
        globalCacheManager = null;
    }
}