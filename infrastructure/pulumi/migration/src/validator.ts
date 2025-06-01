/**
 * Resource Validator for Pulumi Migration Framework
 * Performs pre and post migration validation checks
 */

import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import {
    MigrationConfig,
    ValidationResult,
    ValidationError,
    ValidationWarning,
    ResourceIdentifier,
    MigratedResource,
} from "./types";
import { Logger } from "./logger";

export class ResourceValidator {
    private config: MigrationConfig;
    private logger: Logger;
    private validationRules: ValidationRule[];

    constructor(config: MigrationConfig, logger?: Logger) {
        this.config = config;
        this.logger = logger || new Logger("ResourceValidator");
        this.validationRules = this.initializeValidationRules();
    }

    /**
     * Initialize validation rules
     */
    private initializeValidationRules(): ValidationRule[] {
        return [
            // Project and permissions validation
            {
                name: "project-access",
                description: "Validate GCP project access",
                validate: async () => this.validateProjectAccess(),
            },
            // API enablement validation
            {
                name: "required-apis",
                description: "Check required GCP APIs are enabled",
                validate: async () => this.validateRequiredAPIs(),
            },
            // Resource naming validation
            {
                name: "resource-naming",
                description: "Validate resource naming conventions",
                validate: async () => this.validateResourceNaming(),
            },
            // Quota validation
            {
                name: "quota-check",
                description: "Check GCP quotas",
                validate: async () => this.validateQuotas(),
            },
            // Network validation
            {
                name: "network-connectivity",
                description: "Validate network connectivity",
                validate: async () => this.validateNetworkConnectivity(),
            },
            // State consistency validation
            {
                name: "state-consistency",
                description: "Validate Pulumi state consistency",
                validate: async () => this.validateStateConsistency(),
            },
        ];
    }

    /**
     * Run pre-migration validation
     */
    async validatePreMigration(): Promise<ValidationResult> {
        this.logger.info("Starting pre-migration validation");
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        for (const rule of this.validationRules) {
            try {
                this.logger.debug(`Running validation: ${rule.name}`);
                const result = await rule.validate();
                
                errors.push(...result.errors);
                warnings.push(...result.warnings);
                
                if (result.errors.length > 0) {
                    this.logger.error(`Validation failed: ${rule.name}`, {
                        errors: result.errors,
                    });
                } else {
                    this.logger.debug(`Validation passed: ${rule.name}`);
                }
            } catch (error) {
                errors.push({
                    code: `VALIDATION_ERROR_${rule.name.toUpperCase()}`,
                    message: `Validation rule '${rule.name}' failed: ${error}`,
                    severity: "error",
                });
            }
        }

        const isValid = errors.filter(e => e.severity === "critical").length === 0;

        this.logger.info("Pre-migration validation completed", {
            isValid,
            errorCount: errors.length,
            warningCount: warnings.length,
        });

        return { isValid, errors, warnings };
    }

    /**
     * Run post-migration validation
     */
    async validatePostMigration(resources: MigratedResource[]): Promise<ValidationResult> {
        this.logger.info("Starting post-migration validation");
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Validate each migrated resource
        for (const resource of resources) {
            const resourceValidation = await this.validateMigratedResource(resource);
            errors.push(...resourceValidation.errors);
            warnings.push(...resourceValidation.warnings);
        }

        // Run connectivity tests
        const connectivityResult = await this.validateResourceConnectivity(resources);
        errors.push(...connectivityResult.errors);
        warnings.push(...connectivityResult.warnings);

        const isValid = errors.length === 0;

        this.logger.info("Post-migration validation completed", {
            isValid,
            errorCount: errors.length,
            warningCount: warnings.length,
        });

        return { isValid, errors, warnings };
    }

    /**
     * Validate GCP project access
     */
    private async validateProjectAccess(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        try {
            // Check if we can access the project
            const project = await gcp.organizations.getProject({
                projectId: this.config.projectId,
            });

            if (!project) {
                errors.push({
                    code: "PROJECT_ACCESS_DENIED",
                    message: `Cannot access GCP project: ${this.config.projectId}`,
                    severity: "critical",
                });
            }
        } catch (error) {
            errors.push({
                code: "PROJECT_ACCESS_ERROR",
                message: `Failed to validate project access: ${error}`,
                severity: "critical",
            });
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate required GCP APIs are enabled
     */
    private async validateRequiredAPIs(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        const requiredAPIs = [
            "compute.googleapis.com",
            "container.googleapis.com",
            "storage.googleapis.com",
            "iam.googleapis.com",
            "cloudresourcemanager.googleapis.com",
            "logging.googleapis.com",
            "monitoring.googleapis.com",
        ];

        for (const api of requiredAPIs) {
            try {
                const service = await gcp.projects.getService({
                    service: api,
                });

                if (!service || service.state !== "ENABLED") {
                    errors.push({
                        code: "API_NOT_ENABLED",
                        message: `Required API not enabled: ${api}`,
                        severity: "error",
                    });
                }
            } catch (error) {
                warnings.push({
                    code: "API_CHECK_FAILED",
                    message: `Could not verify API status: ${api}`,
                });
            }
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate resource naming conventions
     */
    private async validateResourceNaming(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Define naming patterns
        const namingPatterns = {
            compute: /^[a-z]([-a-z0-9]*[a-z0-9])?$/,
            storage: /^[a-z0-9]([-_.a-z0-9]*[a-z0-9])?$/,
            general: /^[a-zA-Z]([a-zA-Z0-9-_]*[a-zA-Z0-9])?$/,
        };

        // This would be populated with actual resources to validate
        // For now, we'll return success
        return { isValid: true, errors, warnings };
    }

    /**
     * Validate GCP quotas
     */
    private async validateQuotas(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Check key quotas
        const quotaChecks = [
            { resource: "CPUS", required: 10, region: this.config.region },
            { resource: "DISKS_TOTAL_GB", required: 100, region: this.config.region },
            { resource: "STATIC_ADDRESSES", required: 2, region: this.config.region },
        ];

        for (const check of quotaChecks) {
            try {
                // In a real implementation, we would check actual quotas
                // For now, we'll add a warning
                warnings.push({
                    code: "QUOTA_CHECK_MANUAL",
                    message: `Please verify quota for ${check.resource} >= ${check.required} in ${check.region}`,
                });
            } catch (error) {
                warnings.push({
                    code: "QUOTA_CHECK_FAILED",
                    message: `Could not verify quota for ${check.resource}`,
                });
            }
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate network connectivity
     */
    private async validateNetworkConnectivity(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Check if default network exists or custom network is specified
        try {
            const networks = await gcp.compute.getNetworks({
                project: this.config.projectId,
            });

            if (!networks || networks.networks.length === 0) {
                warnings.push({
                    code: "NO_NETWORKS_FOUND",
                    message: "No VPC networks found in project",
                });
            }
        } catch (error) {
            warnings.push({
                code: "NETWORK_CHECK_FAILED",
                message: "Could not verify network configuration",
            });
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate Pulumi state consistency
     */
    private async validateStateConsistency(): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        try {
            // Check if we can access Pulumi state
            const stack = await pulumi.automation.LocalWorkspace.selectStack({
                stackName: this.config.environment,
                workDir: process.cwd(),
            });

            const summary = await stack.info();
            if (!summary) {
                warnings.push({
                    code: "STACK_NOT_INITIALIZED",
                    message: `Pulumi stack '${this.config.environment}' not initialized`,
                });
            }
        } catch (error) {
            // Stack might not exist yet, which is okay for new migrations
            warnings.push({
                code: "STACK_CHECK_INFO",
                message: `Pulumi stack '${this.config.environment}' will be created`,
            });
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate a single migrated resource
     */
    private async validateMigratedResource(resource: MigratedResource): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Check resource exists and is accessible
        if (!resource.pulumiResource) {
            errors.push({
                code: "RESOURCE_NOT_CREATED",
                message: `Resource not created: ${resource.identifier.type}/${resource.identifier.name}`,
                severity: "error",
                resource: resource.identifier,
            });
        }

        // Check resource outputs
        if (resource.outputs) {
            for (const [key, value] of Object.entries(resource.outputs)) {
                if (value === undefined || value === null) {
                    warnings.push({
                        code: "MISSING_OUTPUT",
                        message: `Missing expected output '${key}' for resource ${resource.identifier.name}`,
                        resource: resource.identifier,
                    });
                }
            }
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Validate connectivity between migrated resources
     */
    private async validateResourceConnectivity(resources: MigratedResource[]): Promise<ValidationResult> {
        const errors: ValidationError[] = [];
        const warnings: ValidationWarning[] = [];

        // Group resources by type
        const resourcesByType = resources.reduce((acc, resource) => {
            const type = resource.identifier.type;
            if (!acc[type]) acc[type] = [];
            acc[type].push(resource);
            return acc;
        }, {} as Record<string, MigratedResource[]>);

        // Validate network connectivity for compute resources
        if (resourcesByType["gcp:compute:Instance"]) {
            for (const instance of resourcesByType["gcp:compute:Instance"]) {
                // Check if instance has network configuration
                if (!instance.outputs?.networkInterfaces) {
                    warnings.push({
                        code: "NO_NETWORK_INTERFACE",
                        message: `Instance ${instance.identifier.name} has no network interfaces`,
                        resource: instance.identifier,
                    });
                }
            }
        }

        // Validate storage bucket accessibility
        if (resourcesByType["gcp:storage:Bucket"]) {
            for (const bucket of resourcesByType["gcp:storage:Bucket"]) {
                if (!bucket.outputs?.url) {
                    warnings.push({
                        code: "BUCKET_URL_MISSING",
                        message: `Bucket ${bucket.identifier.name} has no accessible URL`,
                        resource: bucket.identifier,
                    });
                }
            }
        }

        return { isValid: errors.length === 0, errors, warnings };
    }

    /**
     * Create a custom validation rule
     */
    addCustomValidation(rule: ValidationRule): void {
        this.validationRules.push(rule);
        this.logger.debug("Added custom validation rule", { name: rule.name });
    }

    /**
     * Generate validation report
     */
    generateValidationReport(result: ValidationResult): string {
        const report = {
            timestamp: new Date().toISOString(),
            environment: this.config.environment,
            projectId: this.config.projectId,
            isValid: result.isValid,
            summary: {
                totalErrors: result.errors.length,
                criticalErrors: result.errors.filter(e => e.severity === "critical").length,
                warnings: result.warnings.length,
            },
            errors: result.errors,
            warnings: result.warnings,
        };

        return JSON.stringify(report, null, 2);
    }
}

/**
 * Validation rule interface
 */
interface ValidationRule {
    name: string;
    description: string;
    validate: () => Promise<ValidationResult>;
}