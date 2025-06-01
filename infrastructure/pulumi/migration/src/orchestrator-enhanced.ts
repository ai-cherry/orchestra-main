/**
 * Enhanced Migration Orchestrator for Pulumi Framework
 * Integrates all improvements: async state management, resource discovery,
 * retry logic, performance optimizations, and monitoring
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
    DependencyGraph,
    ProgressReport,
    MigrationStatus,
} from "./types";
import { AsyncStateManager } from "./state-manager-async";
import { ResourceValidator } from "./validator";
import { Logger } from "./logger";
import { ResourceDeduplicator } from "./deduplicator";
import { DependencyResolver } from "./dependency-resolver";
import { RetryManager } from "./retry-manager";
import { ResourceDiscovery } from "./resource-discovery";
import PQueue from "p-queue";
import * as cliProgress from "cli-progress";
import chalk from "chalk";

export class EnhancedMigrationOrchestrator {
    private config: MigrationConfig;
    private stateManager: AsyncStateManager;
    private validator: ResourceValidator;
    private logger: Logger;
    private deduplicator: ResourceDeduplicator;
    private dependencyResolver: DependencyResolver;
    private retryManager: RetryManager;
    private resourceDiscovery: ResourceDiscovery;
    private resourceMappings: ResourceMapping[] = [];
    private migratedResources: Map<string, MigratedResource> = new Map();
    
    // Performance enhancements
    private queue: PQueue;
    private progressBar: cliProgress.SingleBar;
    private metrics: MigrationMetrics;
    
    // Monitoring
    private startTime: number = 0;
    private checkpointInterval: NodeJS.Timeout | null = null;

    constructor(
        config: MigrationConfig,
        logger?: Logger
    ) {
        this.config = config;
        this.logger = logger || new Logger("EnhancedOrchestrator", undefined, config.verboseLogging);
        
        // Initialize components
        this.stateManager = new AsyncStateManager(config, this.logger.child("StateManager"));
        this.validator = new ResourceValidator(config, this.logger.child("Validator"));
        this.deduplicator = new ResourceDeduplicator(config, this.logger.child("Deduplicator"));
        this.dependencyResolver = new DependencyResolver(this.logger.child("DependencyResolver"));
        this.retryManager = new RetryManager(config, this.logger.child("RetryManager"));
        this.resourceDiscovery = new ResourceDiscovery(config, this.logger.child("Discovery"));
        
        // Initialize queue with concurrency control
        this.queue = new PQueue({ 
            concurrency: config.parallelism,
            interval: 1000, // Rate limiting: 1 second
            intervalCap: 10, // Max 10 operations per second
        });
        
        // Initialize progress bar
        this.progressBar = new cliProgress.SingleBar({
            format: chalk.cyan('{bar}') + ' | {percentage}% | {value}/{total} Resources | ETA: {eta}s | {message}',
            barCompleteChar: '\u2588',
            barIncompleteChar: '\u2591',
            hideCursor: true,
        });
        
        // Initialize metrics
        this.metrics = {
            startTime: 0,
            endTime: 0,
            resourcesProcessed: 0,
            resourcesSucceeded: 0,
            resourcesFailed: 0,
            resourcesSkipped: 0,
            retryCount: 0,
            checkpointsCreated: 0,
            memoryUsage: [],
            apiCalls: 0,
        };
        
        // Set up event listeners
        this.setupEventListeners();
    }

    /**
     * Initialize the orchestrator
     */
    async initialize(): Promise<void> {
        this.logger.info("Initializing Enhanced Migration Orchestrator");
        
        // Initialize state manager
        await this.stateManager.initialize();
        
        // Start monitoring
        this.startMonitoring();
        
        this.logger.success("Orchestrator initialized successfully");
    }

    /**
     * Shutdown the orchestrator
     */
    async shutdown(): Promise<void> {
        this.logger.info("Shutting down orchestrator");
        
        // Stop monitoring
        this.stopMonitoring();
        
        // Clear queue
        this.queue.clear();
        
        // Shutdown state manager
        await this.stateManager.shutdown();
        
        // Close progress bar
        this.progressBar.stop();
        
        this.logger.success("Orchestrator shutdown complete");
    }

    /**
     * Execute the complete migration with all enhancements
     */
    async executeMigration(): Promise<MigrationResult> {
        this.startTime = Date.now();
        this.metrics.startTime = this.startTime;
        
        try {
            // Update status
            this.stateManager.updateStatus(MigrationStatus.IN_PROGRESS);
            
            // Phase 1: Pre-migration validation
            await this.reportProgress(MigrationPhase.VALIDATION, "Running pre-migration validation...");
            const validationResult = await this.validator.validatePreMigration();
            if (!validationResult.isValid) {
                throw new Error(`Pre-migration validation failed: ${validationResult.errors.map(e => e.message).join(", ")}`);
            }
            this.logger.success("Pre-migration validation passed");
            
            // Phase 2: Resource Discovery
            await this.reportProgress(MigrationPhase.PLANNING, "Discovering resources...");
            this.resourceMappings = await this.resourceDiscovery.discoverAll();
            this.logger.info(`Discovered ${this.resourceMappings.length} resources`);
            
            // Initialize progress bar
            this.progressBar.start(this.resourceMappings.length, 0, { message: "Initializing..." });
            
            // Phase 3: Build dependency graph
            await this.reportProgress(MigrationPhase.PLANNING, "Analyzing dependencies...");
            const dependencyGraph = await this.buildDependencyGraph();
            
            // Phase 4: Execute migration with optimizations
            await this.reportProgress(MigrationPhase.EXECUTION, "Migrating resources...");
            await this.migrateResourcesOptimized(dependencyGraph);
            
            // Phase 5: Post-migration validation
            await this.reportProgress(MigrationPhase.VERIFICATION, "Verifying migrated resources...");
            await this.verifyMigratedResources();
            
            // Phase 6: Cleanup and finalization
            await this.reportProgress(MigrationPhase.CLEANUP, "Performing cleanup...");
            await this.performCleanup();
            
            // Update final status
            const hasFailures = this.metrics.resourcesFailed > 0;
            const finalStatus = hasFailures ? MigrationStatus.PARTIALLY_COMPLETED : MigrationStatus.COMPLETED;
            this.stateManager.updateStatus(finalStatus);
            
            // Stop progress bar
            this.progressBar.stop();
            
            // Generate final result
            this.metrics.endTime = Date.now();
            const result = this.generateMigrationResult();
            
            // Log summary
            this.logMigrationSummary(result);
            
            return result;
            
        } catch (error) {
            this.logger.error("Migration failed", { error });
            this.stateManager.updateStatus(MigrationStatus.FAILED);
            this.progressBar.stop();
            
            // Attempt rollback if enabled
            if (this.config.enableRollback) {
                await this.performRollback();
            }
            
            throw error;
        }
    }

    /**
     * Build dependency graph with cycle detection
     */
    private async buildDependencyGraph(): Promise<DependencyGraph> {
        this.logger.info("Building dependency graph");
        
        const graph = this.dependencyResolver.buildGraph(this.resourceMappings);
        const cycles = this.dependencyResolver.detectCycles(graph);
        
        if (cycles.length > 0) {
            this.logger.error("Circular dependencies detected", { cycles });
            
            // Visualize the graph for debugging
            const graphViz = this.dependencyResolver.visualize(graph);
            this.logger.debug("Dependency graph visualization:\n" + graphViz);
            
            throw new Error("Cannot proceed with circular dependencies");
        }
        
        // Generate dependency report
        const report = this.dependencyResolver.generateReport(graph);
        this.logger.debug("Dependency analysis report:\n" + report);
        
        return graph;
    }

    /**
     * Migrate resources with performance optimizations
     */
    private async migrateResourcesOptimized(graph: DependencyGraph): Promise<void> {
        const levels = this.dependencyResolver.getLevels(graph);
        
        for (const [level, resourceIds] of levels.entries()) {
            this.logger.info(`Processing dependency level ${level} with ${resourceIds.length} resources`);
            
            // Create tasks for this level
            const tasks = resourceIds.map(resourceId => {
                const mapping = this.findResourceMapping(resourceId);
                if (!mapping) return null;
                
                return () => this.migrateResourceWithMetrics(mapping);
            }).filter(task => task !== null) as Array<() => Promise<void>>;
            
            // Execute tasks with queue (respects concurrency and rate limits)
            await this.queue.addAll(tasks);
            
            // Create checkpoint after each level
            await this.createLevelCheckpoint(level);
            
            // Check memory usage and pause if needed
            await this.checkMemoryPressure();
        }
    }

    /**
     * Migrate a single resource with metrics collection
     */
    private async migrateResourceWithMetrics(mapping: ResourceMapping): Promise<void> {
        const resourceKey = this.getResourceKey(mapping.source);
        const resourceStartTime = Date.now();
        
        try {
            // Update progress
            this.progressBar.increment(0, { message: `Migrating ${resourceKey}` });
            
            // Update state
            this.stateManager.updateResourceState(mapping.source, {
                status: ResourceStatus.IN_PROGRESS,
            });
            
            // Check deduplication
            const dedupResult = await this.deduplicator.checkDuplicate(mapping);
            if (dedupResult.isDuplicate && dedupResult.suggestedAction === DeduplicationAction.SKIP) {
                this.logger.info(`Skipping duplicate resource: ${resourceKey}`);
                this.handleResourceCompletion(mapping, ResourceStatus.SKIPPED);
                return;
            }
            
            // Execute migration with retry
            const retryResult = await this.retryManager.executeWithRetry(
                async () => await this.executeMigrationStrategy(mapping, dedupResult),
                resourceKey,
                {
                    retryableErrors: ["RATE_LIMIT_EXCEEDED", "QUOTA_EXCEEDED", "TIMEOUT"],
                }
            );
            
            if (retryResult.success && retryResult.result) {
                // Store migrated resource
                this.migratedResources.set(resourceKey, retryResult.result);
                
                // Update state with outputs
                this.stateManager.updateResourceState(mapping.source, {
                    status: ResourceStatus.COMPLETED,
                    pulumiUrn: await retryResult.result.pulumiResource.urn,
                });
                
                // Register with deduplicator
                this.deduplicator.registerResource(mapping.target, retryResult.result.pulumiResource);
                
                this.handleResourceCompletion(mapping, ResourceStatus.COMPLETED);
                
                // Log success with duration
                const duration = Date.now() - resourceStartTime;
                this.logger.success(`Migrated ${resourceKey} in ${duration}ms`);
                
            } else {
                throw retryResult.error || new Error("Migration failed");
            }
            
        } catch (error) {
            this.logger.error(`Failed to migrate ${resourceKey}`, { error });
            
            // Update state
            this.stateManager.updateResourceState(mapping.source, {
                status: ResourceStatus.FAILED,
                errors: [error instanceof Error ? error.message : String(error)],
            });
            
            this.handleResourceCompletion(mapping, ResourceStatus.FAILED);
            
            // Decide whether to continue
            if (!this.config.dryRun && this.metrics.resourcesFailed > 5) {
                throw new Error("Too many failures, aborting migration");
            }
        }
    }

    /**
     * Handle resource completion and update metrics
     */
    private handleResourceCompletion(mapping: ResourceMapping, status: ResourceStatus): void {
        this.metrics.resourcesProcessed++;
        
        switch (status) {
            case ResourceStatus.COMPLETED:
                this.metrics.resourcesSucceeded++;
                break;
            case ResourceStatus.FAILED:
                this.metrics.resourcesFailed++;
                break;
            case ResourceStatus.SKIPPED:
                this.metrics.resourcesSkipped++;
                break;
        }
        
        // Update progress bar
        this.progressBar.increment(1, {
            message: `Processed ${this.metrics.resourcesProcessed}/${this.resourceMappings.length}`
        });
        
        // Update retry metrics
        const retryStats = this.retryManager.getStatistics();
        this.metrics.retryCount = retryStats.circuitBreakers.reduce((sum, cb) => sum + cb.failures, 0);
    }

    /**
     * Execute migration strategy
     */
    private async executeMigrationStrategy(
        mapping: ResourceMapping,
        dedupResult: DeduplicationResult
    ): Promise<MigratedResource> {
        this.metrics.apiCalls++;
        
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
     * Create a new resource (example implementation)
     */
    private async createNewResource(mapping: ResourceMapping): Promise<MigratedResource> {
        this.logger.debug(`Creating new resource: ${mapping.target.name}`);
        
        // Resource creation would be implemented here based on type
        // This is a placeholder showing the pattern
        
        const resource = new pulumi.CustomResource(
            mapping.target.type,
            mapping.target.name,
            {
                // Resource properties would go here
            },
            {
                provider: this.getProvider(mapping.target.provider),
                ignoreChanges: this.config.dryRun ? ["*"] : undefined,
            }
        );
        
        return {
            identifier: mapping.target,
            pulumiResource: resource,
            status: ResourceStatus.COMPLETED,
            outputs: {
                id: resource.id,
                urn: resource.urn,
            },
        };
    }

    /**
     * Import existing resource
     */
    private async importExistingResource(mapping: ResourceMapping): Promise<MigratedResource> {
        this.logger.debug(`Importing existing resource: ${mapping.source.name}`);
        
        // Import would be implemented here
        // This is a placeholder
        
        return {
            identifier: mapping.target,
            pulumiResource: {} as any,
            status: ResourceStatus.COMPLETED,
            outputs: {},
        };
    }

    /**
     * Update resource in place
     */
    private async updateResource(
        mapping: ResourceMapping,
        dedupResult: DeduplicationResult
    ): Promise<MigratedResource> {
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
     * Recreate resource
     */
    private async recreateResource(mapping: ResourceMapping): Promise<MigratedResource> {
        // Delete and recreate logic would go here
        return await this.createNewResource(mapping);
    }

    /**
     * Skip resource
     */
    private skipResource(mapping: ResourceMapping): MigratedResource {
        return {
            identifier: mapping.target,
            pulumiResource: {} as any,
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
                warnings: validationResult.warnings,
            });
            
            if (this.config.enableRollback && validationResult.errors.some(e => e.severity === "critical")) {
                await this.performRollback();
                throw new Error("Critical validation errors detected, rollback performed");
            }
        }
        
        this.logger.success("Post-migration validation completed");
    }

    /**
     * Perform cleanup operations
     */
    private async performCleanup(): Promise<void> {
        this.logger.info("Performing cleanup operations");
        
        // Clean up deduplicator cache
        this.deduplicator.clearCache();
        
        // Clean up old state checkpoints
        this.stateManager.cleanup(20, 10);
        
        // Reset circuit breakers
        this.retryManager.resetCircuitBreakers();
        
        // Generate reports
        await this.generateReports();
        
        this.logger.success("Cleanup completed");
    }

    /**
     * Public rollback method
     */
    async rollback(): Promise<void> {
        await this.performRollback();
    }

    /**
     * Perform rollback
     */
    private async performRollback(): Promise<void> {
        this.logger.warn("Starting rollback process");
        
        try {
            // Create rollback point
            const rollbackPoint = await this.stateManager.createRollbackPoint("Migration rollback");
            
            // Get resources to rollback
            const resourcesToRollback = Array.from(this.migratedResources.values())
                .filter(r => r.status === ResourceStatus.COMPLETED)
                .reverse(); // Reverse order
            
            // Create rollback progress bar
            const rollbackBar = new cliProgress.SingleBar({
                format: chalk.yellow('{bar}') + ' | Rollback: {percentage}% | {value}/{total}',
            });
            rollbackBar.start(resourcesToRollback.length, 0);
            
            // Rollback each resource
            for (const resource of resourcesToRollback) {
                try {
                    await this.rollbackResource(resource);
                    rollbackBar.increment();
                } catch (error) {
                    this.logger.error(`Failed to rollback resource: ${resource.identifier.name}`, { error });
                }
            }
            
            rollbackBar.stop();
            
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
        // Rollback implementation would depend on the migration strategy
        this.stateManager.updateResourceState(resource.identifier, {
            status: ResourceStatus.ROLLED_BACK,
        });
    }

    /**
     * Setup event listeners
     */
    private setupEventListeners(): void {
        // State manager events
        this.stateManager.on('statusChanged', (status: MigrationStatus) => {
            this.logger.info(`Migration status changed to: ${status}`);
        });
        
        this.stateManager.on('checkpointCreated', (checkpoint) => {
            this.metrics.checkpointsCreated++;
            this.logger.debug(`Checkpoint created: ${checkpoint.id}`);
        });
        
        // Queue events
        this.queue.on('active', () => {
            this.logger.debug(`Queue active. Size: ${this.queue.size} Pending: ${this.queue.pending}`);
        });
        
        this.queue.on('idle', () => {
            this.logger.debug('Queue is idle');
        });
    }

    /**
     * Start monitoring
     */
    private startMonitoring(): void {
        // Create checkpoints periodically
        this.checkpointInterval = setInterval(async () => {
            if (this.stateManager.getState().status === MigrationStatus.IN_PROGRESS) {
                await this.stateManager.createCheckpoint("periodic-checkpoint");
            }
        }, 5 * 60 * 1000); // Every 5 minutes
        
        // Monitor memory usage
        setInterval(() => {
            const usage = process.memoryUsage();
            this.metrics.memoryUsage.push({
                timestamp: Date.now(),
                heapUsed: usage.heapUsed,
                heapTotal: usage.heapTotal,
                rss: usage.rss,
            });
        }, 30 * 1000); // Every 30 seconds
    }

    /**
     * Stop monitoring
     */
    private stopMonitoring(): void {
        if (this.checkpointInterval) {
            clearInterval(this.checkpointInterval);
            this.checkpointInterval = null;
        }
    }

    /**
     * Check memory pressure and pause if needed
     */
    private async checkMemoryPressure(): Promise<void> {
        const usage = process.memoryUsage();
        const heapPercentage = (usage.heapUsed / usage.heapTotal) * 100;
        
        if (heapPercentage > 85) {
            this.logger.warn(`High memory usage detected: ${heapPercentage.toFixed(2)}%`);
            
            // Pause queue
            this.queue.pause();
            
            // Force garbage collection if available
            if (global.gc) {
                global.gc();
            }
            
            // Wait a bit
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            // Resume queue
            this.queue.start();
        }
    }

    /**
     * Create checkpoint after completing a dependency level
     */
    private async createLevelCheckpoint(level: number): Promise<void> {
        const checkpoint = await this.stateManager.createCheckpoint(`level-${level}-complete`);
        this.logger.info(`Created checkpoint for level ${level}`, {
            resourcesCompleted: checkpoint.resourcesCompleted,
            totalResources: checkpoint.totalResources,
        });
    }

    /**
     * Generate migration result
     */
    private generateMigrationResult(): MigrationResult {
        const duration = this.metrics.endTime - this.metrics.startTime;
        
        return {
            success: this.metrics.resourcesFailed === 0,
            resources: Array.from(this.migratedResources.values()),
            resourcesCreated: this.metrics.resourcesSucceeded,
            resourcesUpdated: 0, // Would need separate tracking
            resourcesSkipped: this.metrics.resourcesSkipped,
            resourcesFailed: this.metrics.resourcesFailed,
            duration,
            errors: [], // Would collect from failed resources
        };
    }

    /**
     * Log migration summary
     */
    private logMigrationSummary(result: MigrationResult): void {
        const summary = `
${chalk.bold.cyan('Migration Summary')}
${'='.repeat(50)}
${chalk.green('✓ Resources Created:')} ${result.resourcesCreated}
${chalk.yellow('⚠ Resources Skipped:')} ${result.resourcesSkipped}
${chalk.red('✗ Resources Failed:')} ${result.resourcesFailed}
${chalk.blue('⏱ Total Duration:')} ${this.formatDuration(result.duration)}
${chalk.magenta('🔄 Total Retries:')} ${this.metrics.retryCount}
${chalk.cyan('💾 Checkpoints Created:')} ${this.metrics.checkpointsCreated}
${chalk.gray('📊 API Calls Made:')} ${this.metrics.apiCalls}
${'='.repeat(50)}
`;
        
        this.logger.info(summary);
    }

    /**
     * Generate detailed reports
     */
    private async generateReports(): Promise<void> {
        // State report
        const stateReport = await this.stateManager.exportState();
        await this.saveReport('state-report.json', stateReport);
        
        // Discovery report
        const discoveryReport = this.resourceDiscovery.getDiscoveryReport();
        await this.saveReport('discovery-report.json', discoveryReport);
        
        // Deduplication report
        const dedupReport = this.deduplicator.exportReport();
        await this.saveReport('deduplication-report.json', dedupReport);
        
        // Retry report
        const retryReport = JSON.stringify(this.retryManager.getStatistics(), null, 2);
        await this.saveReport('retry-report.json', retryReport);
        
        // Metrics report
        const metricsReport = JSON.stringify(this.metrics, null, 2);
        await this.saveReport('metrics-report.json', metricsReport);
        
        this.logger.info("Generated migration reports");
    }

    /**
     * Save report to file
     */
    private async saveReport(filename: string, content: string): Promise<void> {
        const fs = await import('fs/promises');
        const path = await import('path');
        
        const reportsDir = path.join(process.cwd(), '.pulumi-migration', 'reports');
        await fs.mkdir(reportsDir, { recursive: true });
        
        const filepath = path.join(reportsDir, filename);
        await fs.writeFile(filepath, content);
        
        this.logger.debug(`Saved report: ${filepath}`);
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
        
        this.logger.info(`[${phase}] ${message}`);
    }

    private getResourceKey(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    private findResourceMapping(resourceId: string): ResourceMapping | undefined {
        return this.resourceMappings.find(
            m => this.getResourceKey(m.source) === resourceId
        );
    }

    private getProvider(providerName?: string): pulumi.ProviderResource | undefined {
        // Provider management would be implemented here
        return undefined;
    }

    private formatDuration(ms: number): string {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
}

/**
 * Migration metrics interface
 */
interface MigrationMetrics {
    startTime: number;
    endTime: number;
    resourcesProcessed: number;
    resourcesSucceeded: number;
    resourcesFailed: number;
    resourcesSkipped: number;
    retryCount: number;
    checkpointsCreated: number;
    memoryUsage: Array<{
        timestamp: number;
        heapUsed: number;
        heapTotal: number;
        rss: number;
    }>;
    apiCalls: number;
}