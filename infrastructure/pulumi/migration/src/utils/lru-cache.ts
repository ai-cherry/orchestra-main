/**
 * Generic LRU (Least Recently Used) Cache implementation
 * Provides O(1) get/set operations with automatic eviction of least recently used items
 */

export interface LRUCacheOptions {
    maxSize: number;
    ttl?: number; // Time to live in milliseconds
    onEvict?: (key: string, value: any) => void;
}

interface CacheNode<T> {
    key: string;
    value: T;
    timestamp: number;
    prev: CacheNode<T> | null;
    next: CacheNode<T> | null;
}

export class LRUCache<T> {
    private maxSize: number;
    private ttl?: number;
    private onEvict?: (key: string, value: T) => void;
    private cache: Map<string, CacheNode<T>>;
    private head: CacheNode<T> | null;
    private tail: CacheNode<T> | null;
    private size: number;

    constructor(options: LRUCacheOptions) {
        this.maxSize = options.maxSize;
        this.ttl = options.ttl;
        this.onEvict = options.onEvict;
        this.cache = new Map();
        this.head = null;
        this.tail = null;
        this.size = 0;
    }

    /**
     * Get a value from the cache
     * @param key The cache key
     * @returns The cached value or undefined
     */
    get(key: string): T | undefined {
        const node = this.cache.get(key);
        
        if (!node) {
            return undefined;
        }

        // Check TTL if configured
        if (this.ttl && Date.now() - node.timestamp > this.ttl) {
            this.delete(key);
            return undefined;
        }

        // Move to head (most recently used)
        this.moveToHead(node);
        
        return node.value;
    }

    /**
     * Set a value in the cache
     * @param key The cache key
     * @param value The value to cache
     */
    set(key: string, value: T): void {
        const existingNode = this.cache.get(key);

        if (existingNode) {
            // Update existing node
            existingNode.value = value;
            existingNode.timestamp = Date.now();
            this.moveToHead(existingNode);
        } else {
            // Create new node
            const newNode: CacheNode<T> = {
                key,
                value,
                timestamp: Date.now(),
                prev: null,
                next: null,
            };

            this.cache.set(key, newNode);
            this.addToHead(newNode);
            this.size++;

            // Evict if necessary
            if (this.size > this.maxSize) {
                this.evictLRU();
            }
        }
    }

    /**
     * Check if a key exists in the cache
     * @param key The cache key
     * @returns True if the key exists
     */
    has(key: string): boolean {
        const node = this.cache.get(key);
        
        if (!node) {
            return false;
        }

        // Check TTL if configured
        if (this.ttl && Date.now() - node.timestamp > this.ttl) {
            this.delete(key);
            return false;
        }

        return true;
    }

    /**
     * Delete a key from the cache
     * @param key The cache key
     * @returns True if the key was deleted
     */
    delete(key: string): boolean {
        const node = this.cache.get(key);
        
        if (!node) {
            return false;
        }

        this.removeNode(node);
        this.cache.delete(key);
        this.size--;

        if (this.onEvict) {
            this.onEvict(key, node.value);
        }

        return true;
    }

    /**
     * Clear all items from the cache
     */
    clear(): void {
        if (this.onEvict) {
            this.cache.forEach((node, key) => {
                this.onEvict!(key, node.value);
            });
        }

        this.cache.clear();
        this.head = null;
        this.tail = null;
        this.size = 0;
    }

    /**
     * Get the current size of the cache
     */
    getSize(): number {
        return this.size;
    }

    /**
     * Get cache statistics
     */
    getStats(): {
        size: number;
        maxSize: number;
        hitRate: number;
        evictions: number;
    } {
        return {
            size: this.size,
            maxSize: this.maxSize,
            hitRate: 0, // Would need to track hits/misses for this
            evictions: 0, // Would need to track evictions for this
        };
    }

    /**
     * Get all keys in the cache (ordered by recency)
     */
    keys(): string[] {
        const keys: string[] = [];
        let current = this.head;
        
        while (current) {
            keys.push(current.key);
            current = current.next;
        }
        
        return keys;
    }

    /**
     * Get all values in the cache (ordered by recency)
     */
    values(): T[] {
        const values: T[] = [];
        let current = this.head;
        
        while (current) {
            values.push(current.value);
            current = current.next;
        }
        
        return values;
    }

    /**
     * Private helper methods
     */

    private addToHead(node: CacheNode<T>): void {
        node.prev = null;
        node.next = this.head;

        if (this.head) {
            this.head.prev = node;
        }

        this.head = node;

        if (!this.tail) {
            this.tail = node;
        }
    }

    private removeNode(node: CacheNode<T>): void {
        if (node.prev) {
            node.prev.next = node.next;
        } else {
            this.head = node.next;
        }

        if (node.next) {
            node.next.prev = node.prev;
        } else {
            this.tail = node.prev;
        }
    }

    private moveToHead(node: CacheNode<T>): void {
        if (node === this.head) {
            return;
        }

        this.removeNode(node);
        this.addToHead(node);
    }

    private evictLRU(): void {
        if (!this.tail) {
            return;
        }

        const lru = this.tail;
        this.removeNode(lru);
        this.cache.delete(lru.key);
        this.size--;

        if (this.onEvict) {
            this.onEvict(lru.key, lru.value);
        }
    }
}

/**
 * Create a memory-aware LRU cache that respects system memory limits
 */
export function createMemoryAwareLRUCache<T>(
    baseSize: number,
    memoryThreshold: number = 0.7
): LRUCache<T> {
    // Calculate max size based on available memory
    const memoryUsage = process.memoryUsage();
    const availableMemory = memoryUsage.heapTotal - memoryUsage.heapUsed;
    const maxMemoryForCache = availableMemory * memoryThreshold;
    
    // Estimate item size (this is a rough estimate)
    const estimatedItemSize = 1024; // 1KB per item
    const maxItemsBasedOnMemory = Math.floor(maxMemoryForCache / estimatedItemSize);
    
    // Use the smaller of the two limits
    const maxSize = Math.min(baseSize, maxItemsBasedOnMemory);
    
    return new LRUCache<T>({
        maxSize,
        onEvict: (key, value) => {
            // Log eviction for monitoring
            console.debug(`LRU Cache evicted: ${key}`);
        },
    });
}