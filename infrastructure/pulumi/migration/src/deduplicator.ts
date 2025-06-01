/**
 * Resource Deduplicator for Pulumi Migration Framework
 * Handles detection and resolution of duplicate resources
 */

import * as pulumi from "@pulumi/pulumi";
import * as crypto from "crypto";
import {
    MigrationConfig,
    ResourceMapping,
    ResourceIdentifier,
    DeduplicationResult,
    DeduplicationAction,
} from "./types";
import { Logger } from "./logger";

export class ResourceDeduplicator {
    private config: MigrationConfig;
    private logger: Logger;
    private resourceCache: Map<string, pulumi.Resource> = new Map();
    private checksumCache: Map<string, string> = new Map();

    constructor(config: MigrationConfig, logger?: Logger) {
        this.config = config;
        this.logger = logger || new Logger("ResourceDeduplicator");
    }

    /**
     * Check if a resource is a duplicate
     */
    async checkDuplicate(mapping: ResourceMapping): Promise<DeduplicationResult> {
        const resourceKey = this.getResourceKey(mapping.target);
        const checksum = this.calculateChecksum(mapping.target);

        this.logger.debug(`Checking for duplicates: ${resourceKey}`, { checksum });

        // Check by exact name match
        const exactMatch = await this.findExactMatch(mapping.target);
        if (exactMatch) {
            return this.handleExactMatch(mapping, exactMatch);
        }

        // Check by checksum (similar resources)
        const checksumMatch = await this.findChecksumMatch(checksum);
        if (checksumMatch) {
            return this.handleChecksumMatch(mapping, checksumMatch);
        }

        // Check by pattern matching
        const patternMatch = await this.findPatternMatch(mapping.target);
        if (patternMatch) {
            return this.handlePatternMatch(mapping, patternMatch);
        }

        // No duplicate found
        return {
            isDuplicate: false,
            suggestedAction: DeduplicationAction.SKIP,
        };
    }

    /**
     * Find exact match by name and type
     */
    private async findExactMatch(identifier: ResourceIdentifier): Promise<pulumi.Resource | undefined> {
        const key = this.getResourceKey(identifier);
        
        // Check cache first
        if (this.resourceCache.has(key)) {
            return this.resourceCache.get(key);
        }

        // In a real implementation, this would query Pulumi state
        // For now, we'll simulate by checking if resource exists
        try {
            // This is a placeholder - actual implementation would use Pulumi automation API
            const stack = await pulumi.automation.LocalWorkspace.selectStack({
                stackName: this.config.environment,
                workDir: process.cwd(),
            });

            const state = await stack.exportStack();
            const resources = state.deployment?.resources || [];

            for (const resource of resources) {
                if (resource.type === identifier.type && resource.urn?.includes(identifier.name)) {
                    // Cache the result
                    this.resourceCache.set(key, resource as any);
                    return resource as any;
                }
            }
        } catch (error) {
            this.logger.debug("Could not check existing resources", { error });
        }

        return undefined;
    }

    /**
     * Find match by checksum
     */
    private async findChecksumMatch(checksum: string): Promise<pulumi.Resource | undefined> {
        // Check if we've seen this checksum before
        for (const [key, cachedChecksum] of this.checksumCache.entries()) {
            if (cachedChecksum === checksum) {
                return this.resourceCache.get(key);
            }
        }

        return undefined;
    }

    /**
     * Find match by pattern
     */
    private async findPatternMatch(identifier: ResourceIdentifier): Promise<pulumi.Resource | undefined> {
        // Look for resources with similar naming patterns
        const patterns = [
            new RegExp(`^${identifier.name}$`, 'i'),
            new RegExp(`^${identifier.name}-\\d+$`, 'i'),
            new RegExp(`^${identifier.name}-migrated$`, 'i'),
            new RegExp(`^migrated-${identifier.name}$`, 'i'),
        ];

        for (const [key, resource] of this.resourceCache.entries()) {
            for (const pattern of patterns) {
                if (pattern.test(key.split(':')[1])) {
                    return resource;
                }
            }
        }

        return undefined;
    }

    /**
     * Handle exact match scenario
     */
    private handleExactMatch(
        mapping: ResourceMapping,
        existingResource: pulumi.Resource
    ): DeduplicationResult {
        this.logger.info(`Found exact match for resource: ${mapping.target.name}`);

        // Determine action based on migration strategy
        let action: DeduplicationAction;
        
        switch (mapping.migrationStrategy) {
            case "CREATE_NEW":
                // If resource exists and we want to create new, skip
                action = DeduplicationAction.SKIP;
                break;
            case "UPDATE_IN_PLACE":
                // Update the existing resource
                action = DeduplicationAction.UPDATE;
                break;
            case "RECREATE":
                // Replace the existing resource
                action = DeduplicationAction.REPLACE;
                break;
            default:
                action = DeduplicationAction.SKIP;
        }

        return {
            isDuplicate: true,
            existingResource,
            reason: "Exact name and type match found",
            suggestedAction: action,
        };
    }

    /**
     * Handle checksum match scenario
     */
    private handleChecksumMatch(
        mapping: ResourceMapping,
        existingResource: pulumi.Resource
    ): DeduplicationResult {
        this.logger.info(`Found checksum match for resource: ${mapping.target.name}`);

        return {
            isDuplicate: true,
            existingResource,
            reason: "Resource with identical configuration exists",
            suggestedAction: DeduplicationAction.SKIP,
        };
    }

    /**
     * Handle pattern match scenario
     */
    private handlePatternMatch(
        mapping: ResourceMapping,
        existingResource: pulumi.Resource
    ): DeduplicationResult {
        this.logger.info(`Found pattern match for resource: ${mapping.target.name}`);

        return {
            isDuplicate: true,
            existingResource,
            reason: "Similar resource pattern detected",
            suggestedAction: DeduplicationAction.MERGE,
        };
    }

    /**
     * Register a resource in the deduplication cache
     */
    registerResource(identifier: ResourceIdentifier, resource: pulumi.Resource): void {
        const key = this.getResourceKey(identifier);
        const checksum = this.calculateChecksum(identifier);

        this.resourceCache.set(key, resource);
        this.checksumCache.set(key, checksum);

        this.logger.debug(`Registered resource in deduplication cache: ${key}`);
    }

    /**
     * Calculate checksum for a resource identifier
     */
    private calculateChecksum(identifier: ResourceIdentifier): string {
        const data = {
            type: identifier.type,
            name: identifier.name,
            provider: identifier.provider,
            region: identifier.region,
            labels: identifier.labels ? this.sortObject(identifier.labels) : {},
        };

        const jsonString = JSON.stringify(data);
        return crypto.createHash('sha256').update(jsonString).digest('hex');
    }

    /**
     * Get resource key
     */
    private getResourceKey(identifier: ResourceIdentifier): string {
        return `${identifier.type}:${identifier.name}`;
    }

    /**
     * Sort object keys for consistent hashing
     */
    private sortObject(obj: Record<string, any>): Record<string, any> {
        return Object.keys(obj)
            .sort()
            .reduce((sorted, key) => {
                sorted[key] = obj[key];
                return sorted;
            }, {} as Record<string, any>);
    }

    /**
     * Clear deduplication cache
     */
    clearCache(): void {
        this.resourceCache.clear();
        this.checksumCache.clear();
        this.logger.debug("Cleared deduplication cache");
    }

    /**
     * Get deduplication statistics
     */
    getStatistics(): {
        totalCached: number;
        uniqueChecksums: number;
        duplicatesFound: number;
    } {
        const uniqueChecksums = new Set(this.checksumCache.values()).size;
        const duplicatesFound = this.checksumCache.size - uniqueChecksums;

        return {
            totalCached: this.resourceCache.size,
            uniqueChecksums,
            duplicatesFound,
        };
    }

    /**
     * Export deduplication report
     */
    exportReport(): string {
        const stats = this.getStatistics();
        const report = {
            timestamp: new Date().toISOString(),
            statistics: stats,
            resources: Array.from(this.resourceCache.keys()),
            checksums: Array.from(this.checksumCache.entries()).map(([key, checksum]) => ({
                resource: key,
                checksum: checksum.substring(0, 8) + "...", // Abbreviated for readability
            })),
        };

        return JSON.stringify(report, null, 2);
    }
}