/**
 * Migration Orchestrator for Pulumi Framework
 * Coordinates the entire migration process with deduplication,
 * retry logic, and rollback capabilities
 */

import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import {
    MigrationConfig,
    MigrationResult,
    MigrationPhase,
    MigrationStrategy,
    ResourceMapping,
    ResourceIdentifier,
    ResourceStatus,
    MigratedResource,
    DeduplicationResult,
    DeduplicationAction,
    RetryResult,
    DependencyGraph,
    ProgressReport,
} from "./types";
import { StateManager } from "./state-manager";
import { ResourceValidator } from "./validator";
import { Logger } from "./logger";
import { ResourceDeduplicator } from "./deduplicator";
import { DependencyResolver } from "./dependency-resolver";
import { RetryManager } from "./retry-manager";

export class MigrationOrchestrator {
    private config: MigrationConfig;
    private stateManager: StateManager;
    private validator: ResourceValidator;
    private logger: Logger;
    private deduplicator: ResourceDeduplicator;
    private dependencyResolver: DependencyResolver;
    private retryManager: RetryManager;
    private resourceMappings: ResourceMapping[] = [];
    private migratedResources: Map<string, MigratedResource> = new Map();

    constructor(
        config: MigrationConfig,
        stateManager: StateManager,
        validator: ResourceValidator,
        logger: Logger
    ) {
        this.config = config;
        this.stateManager = stateManager;
        this.validator = validator;
        this.logger = logger;
        
        // Initialize sub-components
        this.deduplicator = new ResourceDeduplicator(config, logger.child("Deduplicator"));
        this.dependencyResolver = new DependencyResolver(logger.child("DependencyResolver"));
        this.retryManager = new RetryManager(config, logger.child("RetryManager"));
    }

    /**
     * Execute the complete migration
     */
    async executeMigration(): Promise<MigrationResult> {
        const startTime = Date.now();
        const errors: any[] = [];
        
        try {
            // Update status
            this.stateManager.updateStatus("IN_PROGRESS" as any);
            
            // Phase 1: Discovery and Planning
            await this.reportProgress(MigrationPhase.PLANNING, "Discovering resources...");
            await this.discoverResources();
            
            // Phase 2: Build dependency graph
            await this.reportProgress(MigrationPhase.PLANNING, "Analyzing dependencies...");
            const dependencyGraph = await this.buildDependencyGraph();
            
            // Phase 3: Execute migration in dependency order
            await this.reportProgress(MigrationPhase.EXECUTION, "Starting resource migration...");
            const migrationResult = await this.migrateResourcesInOrder(dependencyGraph);
            
            // Phase 4: Verification
            await this.reportProgress(MigrationPhase.VERIFICATION, "Verifying migrated resources...");
            await this.verifyMigratedResources();
            
            // Phase 5: Cleanup
            await this.reportProgress(MigrationPhase.CLEANUP, "Performing cleanup...");
            await this.performCleanup();
            
            // Update final status
            const finalStatus = errors.length > 0 ? "PARTIALLY_COMPLETED" : "COMPLETED";
            this.stateManager.updateStatus(finalStatus as any);
            
            // Generate result
            const duration = Date.now() - startTime;
            const result: MigrationResult = {
                success: errors.length === 0,
                resources: Array.from(this.migratedResources.values()),
                resourcesCreated: this.countByStatus(ResourceStatus.COMPLETED),
                resourcesUpdated: 0, // Track updates separately if needed
                resourcesSkipped: this.countByStatus(ResourceStatus.SKIPPED),
                resourcesFailed: this.countByStatus(ResourceStatus.FAILED),
                duration,
                errors,
            };
            
            this.logger.success("Migration completed", {
                duration: `${duration}ms`,
                resourcesCreated: result.resourcesCreated,
                resourcesFailed: result.resourcesFailed,
            });
            
            return result;
            
        } catch (error) {
            this.logger.error("Migration failed", { error });
            this.stateManager.updateStatus("FAILED" as any);
            throw error;
        }
    }

    /**
     * Discover resources to migrate
     */
    private async discoverResources(): Promise<void> {
        this.logger.info("Starting resource discovery");
        
        // Example: Discover GCP resources
        // In a real implementation, this would scan existing infrastructure
        const resources: ResourceMapping[] = [
            {
                source: {
                    type: "gcp:compute:Instance",
                    name: "web-server-1",
                    region: "us-central1",
                },
                target: {
                    type: "gcp:compute:Instance",
                    name: "web-server-1-migrated",
                    region: this.config.region,
                },
                dependencies: [],
                priority: 1,
                migrationStrategy: MigrationStrategy.CREATE_NEW,
            },
            // Add more resources as discovered
        ];
        
        this.resourceMappings = resources;
        this.logger.info(`Discovered ${resources.length} resources for migration`);
        
        // Initialize state for each resource
        for (const mapping of resources) {
            this.stateManager.updateResourceState(mapping.source, {
                status: ResourceStatus.PENDING,
                checksum: this.stateManager.calculateResourceChecksum(mapping.source),
            });
        }
    }

    /**
     * Build dependency graph
     */
    private async buildDependencyGraph(): Promise<DependencyGraph> {
        this.logger.info("Building dependency graph");
        
        const graph = this.dependencyResolver.buildGraph(this.resourceMappings);
        const cycles = this.dependencyResolver.detectCycles(graph);
        
        if (cycles.length > 0) {
            this.logger.error("Circular dependencies detected", { cycles });
            throw new Error("Cannot proceed with circular dependencies");
        }
        
        const order = this.dependencyResolver.topologicalSort(graph);
        this.logger.info(`Dependency order determined: ${order.length} levels`);
        
        return graph;
    }

    /**
     * Migrate resources in dependency order
     */
    private async migrateResourcesInOrder(graph: DependencyGraph): Promise<void> {
        const levels = this.dependencyResolver.getLevels(graph);
        
        for (const [level, resources] of levels.entries()) {
            this.logger.info(`Migrating level ${level} with ${resources.length} resources`);
            
            // Process resources at this level in parallel
            const promises = resources.map(resourceId => 
                this.migrateResource(this.findResourceMapping(resourceId))
            );
            
            // Wait for all resources at this level with configured parallelism
            await this.executeInBatches(promises, this.config.parallelism);
            
            // Create checkpoint after each level
            this.stateManager.createCheckpoint(`level-${level}-complete`);
        }
    }

    /**
     * Migrate a single resource
     */
    private async migrateResource(mapping: ResourceMapping | undefined): Promise<void> {
        if (!mapping) return;
        
        const resourceKey = this.getResourceKey(mapping.source);
        this.logger.info(`Migrating resource: ${resourceKey}`);
        
        try {
            // Update state to in-progress
            this.stateManager.updateResourceState(mapping.source, {
                status: ResourceStatus.IN_PROGRESS,
            });
            
            // Check for deduplication
            const dedupResult = await this.deduplicator.checkDuplicate(mapping);
            if (dedupResult.isDuplicate && dedupResult.suggestedAction === DeduplicationAction.SKIP) {
                this.logger.info(`Skipping duplicate resource: ${resourceKey}`);
                this.stateManager.updateResourceState(mapping.source, {
                    status: ResourceStatus.SKIPPED,
                });
                return;
            }
            
            // Execute migration with retry logic
            const retryResult = await this.retryManager.executeWithRetry(
                async () => await this.executeMigrationStrategy(mapping, dedupResult),
                `migrate-${resourceKey}`
            );
            
            if (retryResult.success && retryResult.result) {
                // Store migrated resource
                this.migratedResources.set(resourceKey, retryResult.result);
                
                // Update state
                this.stateManager.updateResourceState(mapping.source, {
                    status: ResourceStatus.COMPLETED,
                    pulumiUrn: retryResult.result.pulumiResource.urn.apply(urn => urn),
                });
                
                this.logger.success(`Successfully migrated: ${resourceKey}`);
            } else {
                throw retryResult.error || new Error("Migration failed");
            }
            
        } catch (error) {
            this.logger.error(`Failed to migrate resource: ${resourceKey}`, { error });
            
            // Update state
            this.stateManager.updateResourceState(mapping.source, {
                status: ResourceStatus.FAILED,
                errors: [error instanceof Error ? error.message : String(error)],
            });
            
            // Decide whether to continue or fail fast
            if (this.config.dryRun) {
                this.logger.warn("Continuing in dry-run mode despite error");
            } else {
                throw error;
            }
        }
    }

    /**
     * Execute migration strategy for a resource
     */
    private async executeMigrationStrategy(
        mapping: ResourceMapping,
        dedupResult: DeduplicationResult
    ): Promise<MigratedResource> {
        switch (mapping.migrationStrategy) {
            case MigrationStrategy.CREATE_NEW:
                return await this.createNewResource(mapping);
                
            case MigrationStrategy.IMPORT_EXISTING:
                return await this.importExistingResource(mapping);
                
            case MigrationStrategy.UPDATE_IN_PLACE:
                return await this.updateResource(mapping, dedupResult);
                
            case MigrationStrategy.RECREATE:
                return await this.recreateResource(mapping);
                
            case MigrationStrategy.SKIP:
                return this.skipResource(mapping);
                
            default:
                throw new Error(`Unknown migration strategy: ${mapping.migrationStrategy}`);
        }
    }

    /**
     * Create a new resource
     */
    private async createNewResource(mapping: ResourceMapping): Promise<MigratedResource> {
        this.logger.debug(`Creating new resource: ${mapping.target.name}`);
        
        // Example: Create a GCP compute instance
        if (mapping.target.type === "gcp:compute:Instance") {
            const instance = new gcp.compute.Instance(mapping.target.name, {
                machineType: "f1-micro",
                zone: `${mapping.target.region}-a`,
                bootDisk: {
                    initializeParams: {
                        image: "debian-cloud/debian-11",
                    },
                },
                networkInterfaces: [{
                    network: "default",
                    accessConfigs: [{}], // Ephemeral IP
                }],
                labels: {
                    ...mapping.target.labels,
                    "migrated-by": "pulumi-migration",
                    "migration-date": new Date().toISOString().split('T')[0],
                },
            });
            
            return {
                identifier: mapping.target,
                pulumiResource: instance,
                status: ResourceStatus.COMPLETED,
                outputs: {
                    id: instance.id,
                    selfLink: instance.selfLink,
                    networkInterfaces: instance.networkInterfaces,
                },
            };
        }
        
        throw new Error(`Resource type not implemented: ${mapping.target.type}`);
    }

    /**
     * Import an existing resource
     */
    private async importExistingResource(mapping: ResourceMapping): Promise<MigratedResource> {
        this.logger.debug(`Importing existing resource: ${mapping.source.name}`);
        
        // Import logic would go here
        // This would use Pulumi's import functionality
        
        return {
            identifier: mapping.target,
            pulumiResource: {} as any, // Placeholder
            status: ResourceStatus.COMPLETED,
            outputs: {},
        };
    }

    /**
     * Update a resource in place
     */
    private async updateResource(
        mapping: ResourceMapping,
        dedupResult: DeduplicationResult
    ): Promise<MigratedResource> {
        this.logger.debug(`Updating resource: ${mapping.target.name}`);
        
        if (!dedupResult.existingResource) {
            throw new Error("Cannot update: existing resource not found");
        }
        
        // Update logic would go here
        
        return {
            identifier: mapping.target,
            pulumiResource: dedupResult.existingResource,
            status: ResourceStatus.COMPLETED,
            outputs: {},
        };
    }

    /**
     * Recreate a resource
     */
    private async recreateResource(mapping: ResourceMapping): Promise<MigratedResource> {
        this.logger.debug(`Recreating resource: ${mapping.target.name}`);
        
        // Delete existing and create new
        // This would involve careful orchestration
        
        return await this.createNewResource(mapping);
    }

    /**
     * Skip a resource
     */
    private skipResource(mapping: ResourceMapping): MigratedResource {
        this.logger.debug(`Skipping resource: ${mapping.target.name}`);
        
        return {
            identifier: mapping.target,
            pulumiResource: {} as any, // No actual resource
            status: ResourceStatus.SKIPPED,
            outputs: {},
        };
    }

    /**
     * Verify migrated resources
     */
    private async verifyMigratedResources(): Promise<void> {
        this.logger.info("Verifying migrated resources");
        
        const resources = Array.from(this.migratedResources.values());
        const validationResult = await this.validator.validatePostMigration(resources);
        
        if (!validationResult.isValid) {
            this.logger.error("Post-migration validation failed", {
                errors: validationResult.errors,
            });
            
            if (this.config.enableRollback) {
                await this.rollback();
            }
        }
    }

    /**
     * Perform cleanup operations
     */
    private async performCleanup(): Promise<void> {
        this.logger.info("Performing cleanup operations");
        
        // Clean up temporary resources
        // Archive logs
        // Update documentation
        
        this.stateManager.cleanup();
        this.logger.info("Cleanup completed");
    }

    /**
     * Rollback migration
     */
    async rollback(): Promise<void> {
        this.logger.warn("Starting rollback process");
        
        try {
            // Create rollback point
            const rollbackPoint = this.stateManager.createRollbackPoint("Migration rollback");
            
            // Rollback in reverse order
            const resources = Array.from(this.migratedResources.values()).reverse();
            
            for (const resource of resources) {
                if (resource.status === ResourceStatus.COMPLETED) {
                    try {
                        await this.rollbackResource(resource);
                    } catch (error) {
                        this.logger.error(`Failed to rollback resource: ${resource.identifier.name}`, { error });
                    }
                }
            }
            
            // Restore state
            this.stateManager.rollback(rollbackPoint.id);
            
            this.logger.info("Rollback completed");
        } catch (error) {
            this.logger.error("Rollback failed", { error });
            throw error;
        }
    }

    /**
     * Rollback a single resource
     */
    private async rollbackResource(resource: MigratedResource): Promise<void> {
        this.logger.debug(`Rolling back resource: ${resource.identifier.name}`);
        
        // Rollback logic would depend on the migration strategy
        // For CREATE_NEW, we would delete the resource
        // For UPDATE_IN_PLACE, we would restore previous state
        
        this.stateManager.updateResourceState(resource.identifier, {
            status: ResourceStatus.ROLLED_BACK,
        });
    }

    /**
     * Helper methods
     */
    
    private async reportProgress(phase: MigrationPhase, message: string): Promise<void> {
        const progress = this.stateManager.getProgress();
        const report: ProgressReport = {
            phase,
            currentStep: progress.completed,
            totalSteps: progress.total,
            percentComplete: progress.percentage,
            message,
        };
        
        this.logger.progress(report.currentStep, report.totalSteps, message);
    }

    private getResourceKey(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    private findResourceMapping(resourceId: string): ResourceMapping | undefined {
        return this.resourceMappings.find(
            m => this.getResourceKey(m.source) === resourceId
        );
    }

    private countByStatus(status: ResourceStatus): number {
        return Array.from(this.migratedResources.values())
            .filter(r => r.status === status).length;
    }

    private async executeInBatches<T>(
        promises: Promise<T>[],
        batchSize: number
    ): Promise<T[]> {
        const results: T[] = [];
        
        for (let i = 0; i < promises.length; i += batchSize) {
            const batch = promises.slice(i, i + batchSize);
            const batchResults = await Promise.all(batch);
            results.push(...batchResults);
        }
        
        return results;
    }
}