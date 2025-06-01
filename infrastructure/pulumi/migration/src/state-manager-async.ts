/**
 * Async State Manager for Pulumi Migration Framework
 * Enhanced version with async I/O, batching, and performance optimizations
 */

import * as fs from "fs/promises";
import * as path from "path";
import * as crypto from "crypto";
import { EventEmitter } from "events";
import {
    MigrationConfig,
    MigrationState,
    MigrationStatus,
    ResourceState,
    ResourceStatus,
    Checkpoint,
    RollbackPoint,
    ResourceIdentifier,
} from "./types";
import { Logger } from "./logger";

interface StateUpdate {
    type: "status" | "resource" | "checkpoint" | "rollback";
    data: any;
    timestamp: number;
}

export class AsyncStateManager extends EventEmitter {
    private config: MigrationConfig;
    private logger: Logger;
    private stateFile: string;
    private state: MigrationState;
    private stateDir: string;
    
    // Performance optimizations
    private writeQueue: StateUpdate[] = [];
    private writeTimer: NodeJS.Timeout | null = null;
    private writeInProgress: boolean = false;
    private readonly batchSize = 100;
    private readonly flushInterval = 1000; // 1 second
    
    // Caching
    private resourceCache: Map<string, ResourceState> = new Map();
    private checksumCache: Map<string, string> = new Map();
    
    // File locking
    private lockFile: string;
    private lockAcquired: boolean = false;

    constructor(config: MigrationConfig, logger?: Logger) {
        super();
        this.config = config;
        this.logger = logger || new Logger("AsyncStateManager");
        
        // Initialize paths
        this.stateDir = path.join(
            process.cwd(),
            ".pulumi-migration",
            config.environment
        );
        this.stateFile = path.join(this.stateDir, "migration-state.json");
        this.lockFile = `${this.stateFile}.lock`;
        
        // Initialize state (will be loaded async)
        this.state = this.createEmptyState();
    }

    /**
     * Initialize the state manager (async initialization)
     */
    async initialize(): Promise<void> {
        // Ensure state directory exists
        await this.ensureStateDirectory();
        
        // Acquire lock
        await this.acquireLock();
        
        // Load state
        this.state = await this.loadState();
        
        // Build cache
        this.rebuildCache();
        
        // Start batch writer
        this.startBatchWriter();
        
        this.logger.info("AsyncStateManager initialized");
    }

    /**
     * Cleanup and shutdown
     */
    async shutdown(): Promise<void> {
        // Stop batch writer
        if (this.writeTimer) {
            clearInterval(this.writeTimer);
            this.writeTimer = null;
        }
        
        // Flush pending writes
        await this.flushWrites();
        
        // Release lock
        await this.releaseLock();
        
        this.logger.info("AsyncStateManager shutdown complete");
    }

    /**
     * Ensure state directory exists
     */
    private async ensureStateDirectory(): Promise<void> {
        try {
            await fs.access(this.stateDir);
        } catch {
            await fs.mkdir(this.stateDir, { recursive: true });
            this.logger.debug("Created state directory", { path: this.stateDir });
        }
    }

    /**
     * Acquire file lock
     */
    private async acquireLock(retries: number = 10): Promise<void> {
        for (let i = 0; i < retries; i++) {
            try {
                // Try to create lock file exclusively
                const handle = await fs.open(this.lockFile, 'wx');
                await handle.write(JSON.stringify({
                    pid: process.pid,
                    timestamp: new Date().toISOString(),
                    environment: this.config.environment,
                }));
                await handle.close();
                
                this.lockAcquired = true;
                this.logger.debug("Lock acquired");
                return;
            } catch (error: any) {
                if (error.code === 'EEXIST') {
                    // Lock exists, check if it's stale
                    const isStale = await this.isLockStale();
                    if (isStale) {
                        await this.forceReleaseLock();
                        continue;
                    }
                    
                    // Wait and retry
                    if (i < retries - 1) {
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        continue;
                    }
                }
                throw error;
            }
        }
        
        throw new Error("Failed to acquire state lock");
    }

    /**
     * Check if lock is stale (older than 5 minutes)
     */
    private async isLockStale(): Promise<boolean> {
        try {
            const stats = await fs.stat(this.lockFile);
            const age = Date.now() - stats.mtimeMs;
            return age > 5 * 60 * 1000; // 5 minutes
        } catch {
            return true;
        }
    }

    /**
     * Force release stale lock
     */
    private async forceReleaseLock(): Promise<void> {
        try {
            await fs.unlink(this.lockFile);
            this.logger.warn("Force released stale lock");
        } catch {
            // Ignore errors
        }
    }

    /**
     * Release file lock
     */
    private async releaseLock(): Promise<void> {
        if (this.lockAcquired) {
            try {
                await fs.unlink(this.lockFile);
                this.lockAcquired = false;
                this.logger.debug("Lock released");
            } catch (error) {
                this.logger.error("Failed to release lock", { error });
            }
        }
    }

    /**
     * Load state from file or create new state
     */
    private async loadState(): Promise<MigrationState> {
        try {
            const data = await fs.readFile(this.stateFile, "utf-8");
            const state = JSON.parse(data) as MigrationState;
            
            this.logger.info("Loaded existing migration state", {
                version: state.version,
                status: state.status,
                resourceCount: state.resources.length,
            });
            
            return state;
        } catch (error: any) {
            if (error.code === 'ENOENT') {
                // File doesn't exist, create new state
                const newState = this.createEmptyState();
                await this.saveStateImmediate(newState);
                return newState;
            }
            
            this.logger.error("Failed to load state file, creating new state", { error });
            return this.createEmptyState();
        }
    }

    /**
     * Create empty state
     */
    private createEmptyState(): MigrationState {
        return {
            version: "1.0.0",
            timestamp: new Date().toISOString(),
            environment: this.config.environment,
            status: MigrationStatus.NOT_STARTED,
            resources: [],
            checkpoints: [],
            rollbackPoints: [],
        };
    }

    /**
     * Save state immediately (for critical operations)
     */
    private async saveStateImmediate(state?: MigrationState): Promise<void> {
        const stateToSave = state || this.state;
        const tempFile = `${this.stateFile}.tmp`;

        try {
            // Write to temporary file with pretty printing for debugging
            await fs.writeFile(tempFile, JSON.stringify(stateToSave, null, 2));
            
            // Atomic rename
            await fs.rename(tempFile, this.stateFile);
            
            this.logger.debug("State saved immediately", {
                resources: stateToSave.resources.length,
                checkpoints: stateToSave.checkpoints.length,
            });
            
            // Emit event
            this.emit('stateSaved', stateToSave);
        } catch (error) {
            this.logger.error("Failed to save state", { error });
            
            // Clean up temp file if it exists
            try {
                await fs.unlink(tempFile);
            } catch {
                // Ignore cleanup errors
            }
            
            throw error;
        }
    }

    /**
     * Queue state update for batched writing
     */
    private queueUpdate(update: StateUpdate): void {
        this.writeQueue.push(update);
        
        // Trigger immediate flush if queue is full
        if (this.writeQueue.length >= this.batchSize) {
            this.flushWrites().catch(error => {
                this.logger.error("Failed to flush writes", { error });
            });
        }
    }

    /**
     * Start batch writer
     */
    private startBatchWriter(): void {
        this.writeTimer = setInterval(() => {
            if (this.writeQueue.length > 0 && !this.writeInProgress) {
                this.flushWrites().catch(error => {
                    this.logger.error("Failed to flush writes", { error });
                });
            }
        }, this.flushInterval);
    }

    /**
     * Flush pending writes
     */
    private async flushWrites(): Promise<void> {
        if (this.writeInProgress || this.writeQueue.length === 0) {
            return;
        }

        this.writeInProgress = true;
        const updates = [...this.writeQueue];
        this.writeQueue = [];

        try {
            // Apply updates to state
            for (const update of updates) {
                this.applyUpdate(update);
            }
            
            // Save state
            await this.saveStateImmediate();
            
            this.logger.debug(`Flushed ${updates.length} updates`);
        } catch (error) {
            // Re-queue failed updates
            this.writeQueue.unshift(...updates);
            throw error;
        } finally {
            this.writeInProgress = false;
        }
    }

    /**
     * Apply update to state
     */
    private applyUpdate(update: StateUpdate): void {
        switch (update.type) {
            case "status":
                this.state.status = update.data.status;
                this.state.timestamp = new Date().toISOString();
                break;
                
            case "resource":
                const { identifier, updates } = update.data;
                const index = this.state.resources.findIndex(
                    r => r.identifier.type === identifier.type && 
                        r.identifier.name === identifier.name
                );
                
                if (index >= 0) {
                    this.state.resources[index] = {
                        ...this.state.resources[index],
                        ...updates,
                        lastModified: new Date().toISOString(),
                    };
                } else {
                    const newResource: ResourceState = {
                        identifier,
                        status: ResourceStatus.PENDING,
                        lastModified: new Date().toISOString(),
                        retryCount: 0,
                        errors: [],
                        ...updates,
                    };
                    this.state.resources.push(newResource);
                }
                
                // Update cache
                this.updateResourceCache(identifier);
                break;
                
            case "checkpoint":
                this.state.checkpoints.push(update.data);
                break;
                
            case "rollback":
                this.state.rollbackPoints.push(update.data);
                break;
        }
    }

    /**
     * Rebuild resource cache
     */
    private rebuildCache(): void {
        this.resourceCache.clear();
        this.checksumCache.clear();
        
        for (const resource of this.state.resources) {
            const key = this.getResourceKey(resource.identifier);
            this.resourceCache.set(key, resource);
            
            if (resource.checksum) {
                this.checksumCache.set(key, resource.checksum);
            }
        }
        
        this.logger.debug("Resource cache rebuilt", { size: this.resourceCache.size });
    }

    /**
     * Update resource cache
     */
    private updateResourceCache(identifier: ResourceIdentifier): void {
        const key = this.getResourceKey(identifier);
        const resource = this.state.resources.find(
            r => r.identifier.type === identifier.type && 
                r.identifier.name === identifier.name
        );
        
        if (resource) {
            this.resourceCache.set(key, resource);
            if (resource.checksum) {
                this.checksumCache.set(key, resource.checksum);
            }
        } else {
            this.resourceCache.delete(key);
            this.checksumCache.delete(key);
        }
    }

    /**
     * Get resource key
     */
    private getResourceKey(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    /**
     * Public API methods
     */

    /**
     * Get current migration state (returns copy)
     */
    getState(): MigrationState {
        return JSON.parse(JSON.stringify(this.state));
    }

    /**
     * Update migration status
     */
    updateStatus(status: MigrationStatus): void {
        this.queueUpdate({
            type: "status",
            data: { status },
            timestamp: Date.now(),
        });
        
        this.logger.info("Migration status updated", { status });
        this.emit('statusChanged', status);
    }

    /**
     * Get resource state from cache
     */
    getResourceState(identifier: ResourceIdentifier): ResourceState | undefined {
        const key = this.getResourceKey(identifier);
        return this.resourceCache.get(key);
    }

    /**
     * Update resource state
     */
    updateResourceState(
        identifier: ResourceIdentifier,
        updates: Partial<ResourceState>
    ): void {
        this.queueUpdate({
            type: "resource",
            data: { identifier, updates },
            timestamp: Date.now(),
        });
        
        // Update cache immediately for consistency
        this.updateResourceCache(identifier);
        
        this.emit('resourceUpdated', identifier, updates);
    }

    /**
     * Create a checkpoint
     */
    async createCheckpoint(id?: string): Promise<Checkpoint> {
        // Flush pending updates before creating checkpoint
        await this.flushWrites();
        
        const checkpoint: Checkpoint = {
            id: id || this.generateId(),
            timestamp: new Date().toISOString(),
            resourcesCompleted: this.state.resources.filter(
                r => r.status === ResourceStatus.COMPLETED
            ).length,
            totalResources: this.state.resources.length,
            state: JSON.parse(JSON.stringify(this.state)),
        };

        this.queueUpdate({
            type: "checkpoint",
            data: checkpoint,
            timestamp: Date.now(),
        });
        
        this.logger.info("Checkpoint created", {
            id: checkpoint.id,
            completed: checkpoint.resourcesCompleted,
            total: checkpoint.totalResources,
        });
        
        this.emit('checkpointCreated', checkpoint);
        return checkpoint;
    }

    /**
     * Create a rollback point
     */
    async createRollbackPoint(reason?: string): Promise<RollbackPoint> {
        // Flush pending updates before creating rollback point
        await this.flushWrites();
        
        const rollbackPoint: RollbackPoint = {
            id: this.generateId(),
            timestamp: new Date().toISOString(),
            beforeState: JSON.parse(JSON.stringify(this.state)),
            afterState: JSON.parse(JSON.stringify(this.state)),
            reason,
        };

        this.queueUpdate({
            type: "rollback",
            data: rollbackPoint,
            timestamp: Date.now(),
        });
        
        this.logger.info("Rollback point created", {
            id: rollbackPoint.id,
            reason,
        });
        
        this.emit('rollbackPointCreated', rollbackPoint);
        return rollbackPoint;
    }

    /**
     * Get resources by status (from cache)
     */
    getResourcesByStatus(status: ResourceStatus): ResourceState[] {
        return Array.from(this.resourceCache.values())
            .filter(r => r.status === status);
    }

    /**
     * Calculate resource checksum
     */
    calculateResourceChecksum(resource: ResourceIdentifier): string {
        const data = JSON.stringify({
            type: resource.type,
            name: resource.name,
            provider: resource.provider,
            region: resource.region,
            labels: resource.labels,
        });
        return crypto.createHash("sha256").update(data).digest("hex");
    }

    /**
     * Check if resource exists by checksum
     */
    resourceExistsByChecksum(checksum: string): boolean {
        return Array.from(this.checksumCache.values()).includes(checksum);
    }

    /**
     * Get migration progress statistics
     */
    getProgress(): {
        total: number;
        completed: number;
        failed: number;
        inProgress: number;
        pending: number;
        percentage: number;
    } {
        const resources = Array.from(this.resourceCache.values());
        const total = resources.length;
        const completed = resources.filter(r => r.status === ResourceStatus.COMPLETED).length;
        const failed = resources.filter(r => r.status === ResourceStatus.FAILED).length;
        const inProgress = resources.filter(r => r.status === ResourceStatus.IN_PROGRESS).length;
        const pending = resources.filter(r => r.status === ResourceStatus.PENDING).length;
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

        return { total, completed, failed, inProgress, pending, percentage };
    }

    /**
     * Generate unique ID
     */
    private generateId(): string {
        return crypto.randomBytes(16).toString("hex");
    }

    /**
     * Export state for backup
     */
    async exportState(): Promise<string> {
        await this.flushWrites();
        
        const exportData = {
            ...this.state,
            exportTimestamp: new Date().toISOString(),
            exportVersion: "1.0.0",
        };
        
        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Get state metrics
     */
    getMetrics(): {
        queueSize: number;
        cacheSize: number;
        checksumCacheSize: number;
        isWriting: boolean;
        lastWriteTime?: Date;
    } {
        return {
            queueSize: this.writeQueue.length,
            cacheSize: this.resourceCache.size,
            checksumCacheSize: this.checksumCache.size,
            isWriting: this.writeInProgress,
        };
    }

    /**
     * Clean up old checkpoints and rollback points
     * @param maxCheckpoints Maximum number of checkpoints to keep
     * @param maxRollbackPoints Maximum number of rollback points to keep
     */
    cleanup(maxCheckpoints: number = 20, maxRollbackPoints: number = 10): void {
        // Clean up old checkpoints
        if (this.state.checkpoints.length > maxCheckpoints) {
            const toRemove = this.state.checkpoints.length - maxCheckpoints;
            this.state.checkpoints = this.state.checkpoints.slice(toRemove);
            this.logger.info(`Removed ${toRemove} old checkpoints`);
        }

        // Clean up old rollback points
        if (this.state.rollbackPoints.length > maxRollbackPoints) {
            const toRemove = this.state.rollbackPoints.length - maxRollbackPoints;
            this.state.rollbackPoints = this.state.rollbackPoints.slice(toRemove);
            this.logger.info(`Removed ${toRemove} old rollback points`);
        }

        // Queue state update
        this.queueUpdate({
            type: "status",
            data: { status: this.state.status },
            timestamp: Date.now(),
        });
    }

    /**
     * Rollback to a specific rollback point
     * @param rollbackPointId The ID of the rollback point to restore
     */
    rollback(rollbackPointId: string): void {
        const rollbackPoint = this.state.rollbackPoints.find(rp => rp.id === rollbackPointId);
        
        if (!rollbackPoint) {
            throw new Error(`Rollback point not found: ${rollbackPointId}`);
        }
        
        // Restore the state from the rollback point
        this.state = JSON.parse(JSON.stringify(rollbackPoint.beforeState));
        
        // Clear caches and rebuild
        this.rebuildCache();
        
        // Update status
        this.state.status = MigrationStatus.ROLLED_BACK;
        this.state.timestamp = new Date().toISOString();
        
        // Save state immediately
        this.saveStateImmediate().catch(error => {
            this.logger.error("Failed to save state after rollback", { error });
        });
        
        this.logger.info("State rolled back successfully", { rollbackPointId });
    }
}