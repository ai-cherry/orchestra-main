/**
 * State Manager for Pulumi Migration Framework
 * Handles persistent state, checkpoints, and rollback points
 */

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";
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

export class StateManager {
    private config: MigrationConfig;
    private logger: Logger;
    private stateFile: string;
    private state: MigrationState;
    private stateDir: string;

    constructor(config: MigrationConfig, logger?: Logger) {
        this.config = config;
        this.logger = logger || new Logger("StateManager");
        
        // Initialize state directory and file paths
        this.stateDir = path.join(
            process.cwd(),
            ".pulumi-migration",
            config.environment
        );
        this.stateFile = path.join(this.stateDir, "migration-state.json");
        
        // Ensure state directory exists
        this.ensureStateDirectory();
        
        // Load or initialize state
        this.state = this.loadState();
    }

    /**
     * Ensure state directory exists
     */
    private ensureStateDirectory(): void {
        if (!fs.existsSync(this.stateDir)) {
            fs.mkdirSync(this.stateDir, { recursive: true });
            this.logger.debug("Created state directory", { path: this.stateDir });
        }
    }

    /**
     * Load state from file or create new state
     */
    private loadState(): MigrationState {
        if (fs.existsSync(this.stateFile)) {
            try {
                const data = fs.readFileSync(this.stateFile, "utf-8");
                const state = JSON.parse(data) as MigrationState;
                this.logger.info("Loaded existing migration state", {
                    version: state.version,
                    status: state.status,
                    resourceCount: state.resources.length,
                });
                return state;
            } catch (error) {
                this.logger.error("Failed to load state file, creating new state", { error });
            }
        }

        // Create new state
        const newState: MigrationState = {
            version: "1.0.0",
            timestamp: new Date().toISOString(),
            environment: this.config.environment,
            status: MigrationStatus.NOT_STARTED,
            resources: [],
            checkpoints: [],
            rollbackPoints: [],
        };

        this.saveState(newState);
        return newState;
    }

    /**
     * Save state to file with atomic write
     */
    private saveState(state?: MigrationState): void {
        const stateToSave = state || this.state;
        const tempFile = `${this.stateFile}.tmp`;

        try {
            // Write to temporary file first
            fs.writeFileSync(tempFile, JSON.stringify(stateToSave, null, 2));
            
            // Atomic rename
            fs.renameSync(tempFile, this.stateFile);
            
            this.logger.debug("State saved successfully", {
                resources: stateToSave.resources.length,
                checkpoints: stateToSave.checkpoints.length,
            });
        } catch (error) {
            this.logger.error("Failed to save state", { error });
            // Clean up temp file if it exists
            if (fs.existsSync(tempFile)) {
                fs.unlinkSync(tempFile);
            }
            throw error;
        }
    }

    /**
     * Get current migration state
     */
    getState(): MigrationState {
        return { ...this.state };
    }

    /**
     * Update migration status
     */
    updateStatus(status: MigrationStatus): void {
        this.state.status = status;
        this.state.timestamp = new Date().toISOString();
        this.saveState();
        this.logger.info("Migration status updated", { status });
    }

    /**
     * Get or create resource state
     */
    getResourceState(identifier: ResourceIdentifier): ResourceState | undefined {
        return this.state.resources.find(
            r => r.identifier.type === identifier.type && 
                r.identifier.name === identifier.name
        );
    }

    /**
     * Update resource state
     */
    updateResourceState(
        identifier: ResourceIdentifier,
        updates: Partial<ResourceState>
    ): void {
        const index = this.state.resources.findIndex(
            r => r.identifier.type === identifier.type && 
                r.identifier.name === identifier.name
        );

        if (index >= 0) {
            // Update existing resource
            this.state.resources[index] = {
                ...this.state.resources[index],
                ...updates,
                lastModified: new Date().toISOString(),
            };
        } else {
            // Create new resource state
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

        this.saveState();
    }

    /**
     * Create a checkpoint
     */
    createCheckpoint(id?: string): Checkpoint {
        const checkpoint: Checkpoint = {
            id: id || this.generateId(),
            timestamp: new Date().toISOString(),
            resourcesCompleted: this.state.resources.filter(
                r => r.status === ResourceStatus.COMPLETED
            ).length,
            totalResources: this.state.resources.length,
            state: JSON.parse(JSON.stringify(this.state)), // Deep clone
        };

        this.state.checkpoints.push(checkpoint);
        this.saveState();
        
        this.logger.info("Checkpoint created", {
            id: checkpoint.id,
            completed: checkpoint.resourcesCompleted,
            total: checkpoint.totalResources,
        });

        return checkpoint;
    }

    /**
     * Restore from checkpoint
     */
    restoreCheckpoint(checkpointId: string): boolean {
        const checkpoint = this.state.checkpoints.find(cp => cp.id === checkpointId);
        
        if (!checkpoint) {
            this.logger.error("Checkpoint not found", { checkpointId });
            return false;
        }

        // Create rollback point before restoring
        this.createRollbackPoint(`Restoring checkpoint ${checkpointId}`);

        // Restore state
        this.state = JSON.parse(JSON.stringify(checkpoint.state));
        this.saveState();

        this.logger.info("Restored from checkpoint", {
            checkpointId,
            timestamp: checkpoint.timestamp,
        });

        return true;
    }

    /**
     * Create a rollback point
     */
    createRollbackPoint(reason?: string): RollbackPoint {
        const rollbackPoint: RollbackPoint = {
            id: this.generateId(),
            timestamp: new Date().toISOString(),
            beforeState: JSON.parse(JSON.stringify(this.state)),
            afterState: JSON.parse(JSON.stringify(this.state)), // Will be updated later
            reason,
        };

        this.state.rollbackPoints.push(rollbackPoint);
        this.saveState();

        this.logger.info("Rollback point created", {
            id: rollbackPoint.id,
            reason,
        });

        return rollbackPoint;
    }

    /**
     * Perform rollback to a specific point
     */
    rollback(rollbackPointId?: string): boolean {
        let rollbackPoint: RollbackPoint | undefined;

        if (rollbackPointId) {
            rollbackPoint = this.state.rollbackPoints.find(rp => rp.id === rollbackPointId);
        } else {
            // Get the most recent rollback point
            rollbackPoint = this.state.rollbackPoints[this.state.rollbackPoints.length - 1];
        }

        if (!rollbackPoint) {
            this.logger.error("No rollback point found");
            return false;
        }

        // Save current state as "after" state
        rollbackPoint.afterState = JSON.parse(JSON.stringify(this.state));

        // Restore to before state
        this.state = JSON.parse(JSON.stringify(rollbackPoint.beforeState));
        this.state.status = MigrationStatus.ROLLED_BACK;
        this.saveState();

        this.logger.info("Rolled back to previous state", {
            rollbackPointId: rollbackPoint.id,
            timestamp: rollbackPoint.timestamp,
        });

        return true;
    }

    /**
     * Get resources by status
     */
    getResourcesByStatus(status: ResourceStatus): ResourceState[] {
        return this.state.resources.filter(r => r.status === status);
    }

    /**
     * Calculate resource checksum for deduplication
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
        return this.state.resources.some(r => r.checksum === checksum);
    }

    /**
     * Clean up old checkpoints and rollback points
     */
    cleanup(keepCheckpoints: number = 10, keepRollbackPoints: number = 5): void {
        // Sort by timestamp and keep only the most recent
        this.state.checkpoints = this.state.checkpoints
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
            .slice(0, keepCheckpoints);

        this.state.rollbackPoints = this.state.rollbackPoints
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
            .slice(0, keepRollbackPoints);

        this.saveState();
        
        this.logger.info("State cleanup completed", {
            checkpoints: this.state.checkpoints.length,
            rollbackPoints: this.state.rollbackPoints.length,
        });
    }

    /**
     * Export state for backup
     */
    exportState(): string {
        const exportData = {
            ...this.state,
            exportTimestamp: new Date().toISOString(),
            exportVersion: "1.0.0",
        };
        return JSON.stringify(exportData, null, 2);
    }

    /**
     * Import state from backup
     */
    importState(data: string): boolean {
        try {
            const importData = JSON.parse(data);
            
            // Validate import data
            if (!importData.version || !importData.resources) {
                throw new Error("Invalid import data format");
            }

            // Create backup of current state
            this.createRollbackPoint("Before state import");

            // Import the state
            this.state = {
                version: importData.version,
                timestamp: importData.timestamp,
                environment: importData.environment,
                status: importData.status,
                resources: importData.resources,
                checkpoints: importData.checkpoints || [],
                rollbackPoints: importData.rollbackPoints || [],
            };

            this.saveState();
            this.logger.info("State imported successfully");
            return true;
        } catch (error) {
            this.logger.error("Failed to import state", { error });
            return false;
        }
    }

    /**
     * Generate unique ID
     */
    private generateId(): string {
        return crypto.randomBytes(16).toString("hex");
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
        const total = this.state.resources.length;
        const completed = this.state.resources.filter(r => r.status === ResourceStatus.COMPLETED).length;
        const failed = this.state.resources.filter(r => r.status === ResourceStatus.FAILED).length;
        const inProgress = this.state.resources.filter(r => r.status === ResourceStatus.IN_PROGRESS).length;
        const pending = this.state.resources.filter(r => r.status === ResourceStatus.PENDING).length;
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

        return { total, completed, failed, inProgress, pending, percentage };
    }
}