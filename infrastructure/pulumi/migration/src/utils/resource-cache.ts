/**
 * Resource-specific cache implementation with TTL and memory management
 * Built on top of the generic LRU cache for optimal performance
 */

import { LRUCache, createMemoryAwareLRUCache } from "./lru-cache";
import { ResourceState, ResourceIdentifier } from "../types";
import * as crypto from "crypto";

export interface ResourceCacheOptions {
    maxSize?: number;
    ttl?: number; // Time to live in milliseconds
    memoryThreshold?: number; // Percentage of heap to use (0-1)
}

export class ResourceCache {
    private cache: LRUCache<ResourceState>;
    private checksumCache: LRUCache<string>;
    private stats: {
        hits: number;
        misses: number;
        evictions: number;
    };

    constructor(options: ResourceCacheOptions = {}) {
        const maxSize = options.maxSize || 10000;
        const ttl = options.ttl || 3600000; // 1 hour default
        const memoryThreshold = options.memoryThreshold || 0.5; // Use 50% of available heap

        // Create memory-aware caches
        this.cache = createMemoryAwareLRUCache<ResourceState>(maxSize, memoryThreshold);
        this.checksumCache = createMemoryAwareLRUCache<string>(maxSize, memoryThreshold);

        // Initialize statistics
        this.stats = {
            hits: 0,
            misses: 0,
            evictions: 0,
        };

        // Set up eviction tracking
        this.setupEvictionTracking();
    }

    /**
     * Get a resource from the cache
     * @param identifier Resource identifier
     * @returns The cached resource state or undefined
     */
    get(identifier: ResourceIdentifier): ResourceState | undefined {
        const key = this.getResourceKey(identifier);
        const resource = this.cache.get(key);

        if (resource) {
            this.stats.hits++;
        } else {
            this.stats.misses++;
        }

        return resource;
    }

    /**
     * Set a resource in the cache
     * @param identifier Resource identifier
     * @param state Resource state
     */
    set(identifier: ResourceIdentifier, state: ResourceState): void {
        const key = this.getResourceKey(identifier);
        this.cache.set(key, state);

        // Also cache the checksum if present
        if (state.checksum) {
            this.checksumCache.set(key, state.checksum);
        }
    }

    /**
     * Check if a resource exists in the cache
     * @param identifier Resource identifier
     * @returns True if the resource exists
     */
    has(identifier: ResourceIdentifier): boolean {
        const key = this.getResourceKey(identifier);
        return this.cache.has(key);
    }

    /**
     * Delete a resource from the cache
     * @param identifier Resource identifier
     * @returns True if the resource was deleted
     */
    delete(identifier: ResourceIdentifier): boolean {
        const key = this.getResourceKey(identifier);
        this.checksumCache.delete(key);
        return this.cache.delete(key);
    }

    /**
     * Get resource by checksum
     * @param checksum Resource checksum
     * @returns The resource identifier or undefined
     */
    getByChecksum(checksum: string): ResourceIdentifier | undefined {
        // Search through checksum cache
        const keys = this.checksumCache.keys();
        
        for (const key of keys) {
            if (this.checksumCache.get(key) === checksum) {
                const resource = this.cache.get(key);
                if (resource) {
                    return resource.identifier;
                }
            }
        }

        return undefined;
    }

    /**
     * Calculate and cache resource checksum
     * @param identifier Resource identifier
     * @returns The calculated checksum
     */
    calculateChecksum(identifier: ResourceIdentifier): string {
        const data = JSON.stringify({
            type: identifier.type,
            name: identifier.name,
            provider: identifier.provider,
            region: identifier.region,
            labels: identifier.labels ? this.sortObject(identifier.labels) : {},
        });

        const checksum = crypto.createHash("sha256").update(data).digest("hex");
        
        // Cache the checksum
        const key = this.getResourceKey(identifier);
        this.checksumCache.set(key, checksum);

        return checksum;
    }

    /**
     * Get all resources by status
     * @param status Resource status
     * @returns Array of resources with the specified status
     */
    getByStatus(status: string): ResourceState[] {
        const resources: ResourceState[] = [];
        const values = this.cache.values();

        for (const resource of values) {
            if (resource.status === status) {
                resources.push(resource);
            }
        }

        return resources;
    }

    /**
     * Clear all cached resources
     */
    clear(): void {
        this.cache.clear();
        this.checksumCache.clear();
        this.stats = {
            hits: 0,
            misses: 0,
            evictions: 0,
        };
    }

    /**
     * Get cache statistics
     */
    getStats(): {
        size: number;
        checksumCacheSize: number;
        hits: number;
        misses: number;
        hitRate: number;
        evictions: number;
    } {
        const totalRequests = this.stats.hits + this.stats.misses;
        const hitRate = totalRequests > 0 ? this.stats.hits / totalRequests : 0;

        return {
            size: this.cache.getSize(),
            checksumCacheSize: this.checksumCache.getSize(),
            hits: this.stats.hits,
            misses: this.stats.misses,
            hitRate,
            evictions: this.stats.evictions,
        };
    }

    /**
     * Export cache contents for debugging
     */
    export(): {
        resources: Array<{ key: string; value: ResourceState }>;
        checksums: Array<{ key: string; checksum: string }>;
    } {
        const resources: Array<{ key: string; value: ResourceState }> = [];
        const checksums: Array<{ key: string; checksum: string }> = [];

        // Export resources
        const resourceKeys = this.cache.keys();
        for (const key of resourceKeys) {
            const value = this.cache.get(key);
            if (value) {
                resources.push({ key, value });
            }
        }

        // Export checksums
        const checksumKeys = this.checksumCache.keys();
        for (const key of checksumKeys) {
            const checksum = this.checksumCache.get(key);
            if (checksum) {
                checksums.push({ key, checksum });
            }
        }

        return { resources, checksums };
    }

    /**
     * Import cache contents
     */
    import(data: {
        resources: Array<{ key: string; value: ResourceState }>;
        checksums: Array<{ key: string; checksum: string }>;
    }): void {
        // Clear existing cache
        this.clear();

        // Import resources
        for (const { key, value } of data.resources) {
            const parts = key.split(":");
            if (parts.length >= 2) {
                this.set(value.identifier, value);
            }
        }

        // Import checksums
        for (const { key, checksum } of data.checksums) {
            this.checksumCache.set(key, checksum);
        }
    }

    /**
     * Private helper methods
     */

    private getResourceKey(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    private sortObject(obj: Record<string, any>): Record<string, any> {
        return Object.keys(obj)
            .sort()
            .reduce((sorted, key) => {
                sorted[key] = obj[key];
                return sorted;
            }, {} as Record<string, any>);
    }

    private setupEvictionTracking(): void {
        // Track evictions from main cache
        const originalDelete = this.cache.delete.bind(this.cache);
        this.cache.delete = (key: string) => {
            const result = originalDelete(key);
            if (result) {
                this.stats.evictions++;
            }
            return result;
        };

        // Track evictions from checksum cache
        const originalChecksumDelete = this.checksumCache.delete.bind(this.checksumCache);
        this.checksumCache.delete = (key: string) => {
            const result = originalChecksumDelete(key);
            if (result) {
                // Don't double count if both caches evict
            }
            return result;
        };
    }
}

/**
 * Create a singleton resource cache instance
 */
let globalResourceCache: ResourceCache | null = null;

export function getGlobalResourceCache(options?: ResourceCacheOptions): ResourceCache {
    if (!globalResourceCache) {
        globalResourceCache = new ResourceCache(options);
    }
    return globalResourceCache;
}

/**
 * Reset the global resource cache
 */
export function resetGlobalResourceCache(): void {
    if (globalResourceCache) {
        globalResourceCache.clear();
        globalResourceCache = null;
    }
}