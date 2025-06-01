/**
 * Resource Discovery for Pulumi Migration Framework
 * Discovers and catalogs existing infrastructure resources
 */

import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import {
    MigrationConfig,
    ResourceMapping,
    ResourceIdentifier,
    MigrationStrategy,
} from "./types";
import { Logger } from "./logger";

export interface DiscoveryProvider {
    name: string;
    discover(): Promise<ResourceMapping[]>;
}

export class ResourceDiscovery {
    private config: MigrationConfig;
    private logger: Logger;
    private providers: Map<string, DiscoveryProvider> = new Map();
    private discoveredResources: ResourceMapping[] = [];

    constructor(config: MigrationConfig, logger?: Logger) {
        this.config = config;
        this.logger = logger || new Logger("ResourceDiscovery");
        
        // Initialize providers based on configuration
        this.initializeProviders();
    }

    /**
     * Initialize discovery providers
     */
    private initializeProviders(): void {
        // GCP Provider
        if (this.config.projectId) {
            this.providers.set("gcp", new GCPDiscoveryProvider(this.config, this.logger.child("GCP")));
        }
        
        // Add more providers as needed (AWS, Azure, etc.)
        
        this.logger.info(`Initialized ${this.providers.size} discovery providers`);
    }

    /**
     * Discover all resources across all providers
     */
    async discoverAll(): Promise<ResourceMapping[]> {
        this.logger.info("Starting comprehensive resource discovery");
        this.discoveredResources = [];
        
        // Run discovery for each provider in parallel
        const discoveries = Array.from(this.providers.entries()).map(async ([name, provider]) => {
            try {
                this.logger.info(`Running discovery for provider: ${name}`);
                const resources = await provider.discover();
                this.logger.info(`Discovered ${resources.length} resources from ${name}`);
                return resources;
            } catch (error) {
                this.logger.error(`Discovery failed for provider ${name}`, { error });
                return [];
            }
        });
        
        const results = await Promise.all(discoveries);
        this.discoveredResources = results.flat();
        
        // Post-process discovered resources
        await this.postProcessResources();
        
        this.logger.success(`Total resources discovered: ${this.discoveredResources.length}`);
        return this.discoveredResources;
    }

    /**
     * Post-process discovered resources
     */
    private async postProcessResources(): Promise<void> {
        // Detect dependencies
        await this.detectDependencies();
        
        // Assign priorities
        this.assignPriorities();
        
        // Determine migration strategies
        this.determineMigrationStrategies();
    }

    /**
     * Detect dependencies between resources
     */
    private async detectDependencies(): Promise<void> {
        this.logger.info("Detecting resource dependencies");
        
        for (const resource of this.discoveredResources) {
            const dependencies: string[] = [];
            
            // Example: VMs depend on networks
            if (resource.source.type === "gcp:compute:Instance") {
                const networkDeps = this.discoveredResources
                    .filter(r => r.source.type === "gcp:compute:Network")
                    .map(r => this.getResourceId(r.source));
                dependencies.push(...networkDeps);
            }
            
            // Example: Disks depend on nothing (base resources)
            if (resource.source.type === "gcp:compute:Disk") {
                // No dependencies
            }
            
            // Add more dependency detection logic based on resource types
            
            resource.dependencies = dependencies;
        }
        
        this.logger.info("Dependency detection complete");
    }

    /**
     * Assign priorities based on resource types and dependencies
     */
    private assignPriorities(): void {
        const priorityMap: Record<string, number> = {
            // Network resources have highest priority
            "gcp:compute:Network": 1,
            "gcp:compute:Subnetwork": 2,
            "gcp:compute:Firewall": 3,
            
            // Storage resources
            "gcp:storage:Bucket": 4,
            "gcp:compute:Disk": 5,
            
            // Compute resources
            "gcp:compute:Instance": 6,
            "gcp:compute:InstanceGroup": 7,
            
            // Load balancing
            "gcp:compute:TargetPool": 8,
            "gcp:compute:ForwardingRule": 9,
            
            // Default priority
            "default": 10,
        };
        
        for (const resource of this.discoveredResources) {
            resource.priority = priorityMap[resource.source.type] || priorityMap.default;
        }
        
        // Sort by priority
        this.discoveredResources.sort((a, b) => a.priority - b.priority);
    }

    /**
     * Determine migration strategies for resources
     */
    private determineMigrationStrategies(): void {
        for (const resource of this.discoveredResources) {
            // Default strategy
            let strategy = MigrationStrategy.IMPORT_EXISTING;
            
            // Resources that should be recreated
            if (this.shouldRecreate(resource)) {
                strategy = MigrationStrategy.RECREATE;
            }
            
            // Resources that should be skipped
            if (this.shouldSkip(resource)) {
                strategy = MigrationStrategy.SKIP;
            }
            
            // Resources that can be updated in place
            if (this.canUpdateInPlace(resource)) {
                strategy = MigrationStrategy.UPDATE_IN_PLACE;
            }
            
            resource.migrationStrategy = strategy;
        }
    }

    /**
     * Check if resource should be recreated
     */
    private shouldRecreate(resource: ResourceMapping): boolean {
        // Example: Recreate resources with specific labels
        if (resource.source.labels?.["recreate"] === "true") {
            return true;
        }
        
        // Add more logic based on resource state, age, etc.
        return false;
    }

    /**
     * Check if resource should be skipped
     */
    private shouldSkip(resource: ResourceMapping): boolean {
        // Example: Skip resources with specific labels
        if (resource.source.labels?.["skip-migration"] === "true") {
            return true;
        }
        
        // Skip temporary or ephemeral resources
        if (resource.source.name.includes("temp-") || resource.source.name.includes("tmp-")) {
            return true;
        }
        
        return false;
    }

    /**
     * Check if resource can be updated in place
     */
    private canUpdateInPlace(resource: ResourceMapping): boolean {
        // Some resource types support in-place updates
        const updatableTypes = [
            "gcp:compute:Instance",
            "gcp:storage:Bucket",
        ];
        
        return updatableTypes.includes(resource.source.type);
    }

    /**
     * Get resource ID
     */
    private getResourceId(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    /**
     * Filter discovered resources
     */
    filterResources(predicate: (resource: ResourceMapping) => boolean): ResourceMapping[] {
        return this.discoveredResources.filter(predicate);
    }

    /**
     * Get discovery report
     */
    getDiscoveryReport(): string {
        const report = {
            timestamp: new Date().toISOString(),
            totalResources: this.discoveredResources.length,
            byProvider: {} as Record<string, number>,
            byType: {} as Record<string, number>,
            byStrategy: {} as Record<string, number>,
            byPriority: {} as Record<number, number>,
        };
        
        // Count by provider
        for (const resource of this.discoveredResources) {
            const provider = resource.source.provider || "unknown";
            report.byProvider[provider] = (report.byProvider[provider] || 0) + 1;
            
            // Count by type
            report.byType[resource.source.type] = (report.byType[resource.source.type] || 0) + 1;
            
            // Count by strategy
            report.byStrategy[resource.migrationStrategy] = (report.byStrategy[resource.migrationStrategy] || 0) + 1;
            
            // Count by priority
            report.byPriority[resource.priority] = (report.byPriority[resource.priority] || 0) + 1;
        }
        
        return JSON.stringify(report, null, 2);
    }
}

/**
 * GCP Discovery Provider
 */
class GCPDiscoveryProvider implements DiscoveryProvider {
    name = "gcp";
    private config: MigrationConfig;
    private logger: Logger;

    constructor(config: MigrationConfig, logger: Logger) {
        this.config = config;
        this.logger = logger;
    }

    async discover(): Promise<ResourceMapping[]> {
        const resources: ResourceMapping[] = [];
        
        try {
            // Discover compute instances
            const instances = await this.discoverComputeInstances();
            resources.push(...instances);
            
            // Discover networks
            const networks = await this.discoverNetworks();
            resources.push(...networks);
            
            // Discover storage buckets
            const buckets = await this.discoverStorageBuckets();
            resources.push(...buckets);
            
            // Discover disks
            const disks = await this.discoverDisks();
            resources.push(...disks);
            
            // Add more resource types as needed
            
        } catch (error) {
            this.logger.error("GCP discovery failed", { error });
        }
        
        return resources;
    }

    /**
     * Discover compute instances
     */
    private async discoverComputeInstances(): Promise<ResourceMapping[]> {
        const resources: ResourceMapping[] = [];
        
        try {
            // List all zones in the region
            const zones = await gcp.compute.getZones({
                project: this.config.projectId,
                filter: `region eq .*${this.config.region}.*`,
            });
            
            for (const zone of zones.zones) {
                // Get instances in each zone
                const instances = await gcp.compute.getInstances({
                    project: this.config.projectId,
                    zone: zone.name,
                });
                
                for (const instance of instances.instances) {
                    const mapping: ResourceMapping = {
                        source: {
                            type: "gcp:compute:Instance",
                            name: instance.name,
                            id: instance.id,
                            provider: "gcp",
                            region: this.config.region,
                            labels: instance.labels || {},
                        },
                        target: {
                            type: "gcp:compute:Instance",
                            name: `${instance.name}-migrated`,
                            provider: "gcp",
                            region: this.config.region,
                            labels: {
                                ...instance.labels,
                                "migrated-from": instance.name,
                                "migration-date": new Date().toISOString().split('T')[0],
                            },
                        },
                        dependencies: [],
                        priority: 0,
                        migrationStrategy: MigrationStrategy.IMPORT_EXISTING,
                    };
                    
                    resources.push(mapping);
                }
            }
            
            this.logger.info(`Discovered ${resources.length} compute instances`);
        } catch (error) {
            this.logger.error("Failed to discover compute instances", { error });
        }
        
        return resources;
    }

    /**
     * Discover networks
     */
    private async discoverNetworks(): Promise<ResourceMapping[]> {
        const resources: ResourceMapping[] = [];
        
        try {
            const networks = await gcp.compute.getNetworks({
                project: this.config.projectId,
            });
            
            for (const network of networks.networks) {
                const mapping: ResourceMapping = {
                    source: {
                        type: "gcp:compute:Network",
                        name: network.name,
                        id: network.id,
                        provider: "gcp",
                        labels: {},
                    },
                    target: {
                        type: "gcp:compute:Network",
                        name: `${network.name}-migrated`,
                        provider: "gcp",
                        labels: {
                            "migrated-from": network.name,
                        },
                    },
                    dependencies: [],
                    priority: 0,
                    migrationStrategy: MigrationStrategy.IMPORT_EXISTING,
                };
                
                resources.push(mapping);
            }
            
            // Discover subnetworks
            const subnetworks = await gcp.compute.getSubnetworks({
                project: this.config.projectId,
                region: this.config.region,
            });
            
            for (const subnet of subnetworks.subnetworks) {
                const mapping: ResourceMapping = {
                    source: {
                        type: "gcp:compute:Subnetwork",
                        name: subnet.name,
                        id: subnet.id,
                        provider: "gcp",
                        region: this.config.region,
                        labels: {},
                    },
                    target: {
                        type: "gcp:compute:Subnetwork",
                        name: `${subnet.name}-migrated`,
                        provider: "gcp",
                        region: this.config.region,
                        labels: {
                            "migrated-from": subnet.name,
                        },
                    },
                    dependencies: [],
                    priority: 0,
                    migrationStrategy: MigrationStrategy.IMPORT_EXISTING,
                };
                
                resources.push(mapping);
            }
            
            this.logger.info(`Discovered ${resources.length} network resources`);
        } catch (error) {
            this.logger.error("Failed to discover networks", { error });
        }
        
        return resources;
    }

    /**
     * Discover storage buckets
     */
    private async discoverStorageBuckets(): Promise<ResourceMapping[]> {
        const resources: ResourceMapping[] = [];
        
        try {
            const buckets = await gcp.storage.getBuckets({
                project: this.config.projectId,
            });
            
            for (const bucket of buckets.buckets) {
                const mapping: ResourceMapping = {
                    source: {
                        type: "gcp:storage:Bucket",
                        name: bucket.name,
                        id: bucket.id,
                        provider: "gcp",
                        labels: bucket.labels || {},
                    },
                    target: {
                        type: "gcp:storage:Bucket",
                        name: `${bucket.name}-migrated`,
                        provider: "gcp",
                        labels: {
                            ...bucket.labels,
                            "migrated-from": bucket.name,
                        },
                    },
                    dependencies: [],
                    priority: 0,
                    migrationStrategy: MigrationStrategy.IMPORT_EXISTING,
                };
                
                resources.push(mapping);
            }
            
            this.logger.info(`Discovered ${resources.length} storage buckets`);
        } catch (error) {
            this.logger.error("Failed to discover storage buckets", { error });
        }
        
        return resources;
    }

    /**
     * Discover persistent disks
     */
    private async discoverDisks(): Promise<ResourceMapping[]> {
        const resources: ResourceMapping[] = [];
        
        try {
            // List all zones in the region
            const zones = await gcp.compute.getZones({
                project: this.config.projectId,
                filter: `region eq .*${this.config.region}.*`,
            });
            
            for (const zone of zones.zones) {
                const disks = await gcp.compute.getDisks({
                    project: this.config.projectId,
                    zone: zone.name,
                });
                
                for (const disk of disks.disks) {
                    const mapping: ResourceMapping = {
                        source: {
                            type: "gcp:compute:Disk",
                            name: disk.name,
                            id: disk.id,
                            provider: "gcp",
                            region: this.config.region,
                            labels: disk.labels || {},
                        },
                        target: {
                            type: "gcp:compute:Disk",
                            name: `${disk.name}-migrated`,
                            provider: "gcp",
                            region: this.config.region,
                            labels: {
                                ...disk.labels,
                                "migrated-from": disk.name,
                            },
                        },
                        dependencies: [],
                        priority: 0,
                        migrationStrategy: MigrationStrategy.IMPORT_EXISTING,
                    };
                    
                    resources.push(mapping);
                }
            }
            
            this.logger.info(`Discovered ${resources.length} persistent disks`);
        } catch (error) {
            this.logger.error("Failed to discover disks", { error });
        }
        
        return resources;
    }
}