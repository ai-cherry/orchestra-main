/**
 * Type definitions for the Pulumi migration framework
 */

import * as pulumi from "@pulumi/pulumi";

// Core configuration types
export interface MigrationConfig {
    projectId: string;
    region: string;
    environment: string;
    dryRun: boolean;
    parallelism: number;
    retryAttempts: number;
    retryDelayMs: number;
    enableRollback: boolean;
    verboseLogging: boolean;
}

// Resource identification and mapping
export interface ResourceIdentifier {
    type: string;
    name: string;
    id?: string;
    provider?: string;
    region?: string;
    labels?: Record<string, string>;
}

export interface ResourceMapping {
    source: ResourceIdentifier;
    target: ResourceIdentifier;
    dependencies: string[];
    priority: number;
    migrationStrategy: MigrationStrategy;
}

export enum MigrationStrategy {
    CREATE_NEW = "CREATE_NEW",
    IMPORT_EXISTING = "IMPORT_EXISTING",
    UPDATE_IN_PLACE = "UPDATE_IN_PLACE",
    RECREATE = "RECREATE",
    SKIP = "SKIP",
}

// State management types
export interface MigrationState {
    version: string;
    timestamp: string;
    environment: string;
    status: MigrationStatus;
    resources: ResourceState[];
    checkpoints: Checkpoint[];
    rollbackPoints: RollbackPoint[];
}

export enum MigrationStatus {
    NOT_STARTED = "NOT_STARTED",
    IN_PROGRESS = "IN_PROGRESS",
    COMPLETED = "COMPLETED",
    FAILED = "FAILED",
    ROLLED_BACK = "ROLLED_BACK",
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED",
}

export interface ResourceState {
    identifier: ResourceIdentifier;
    status: ResourceStatus;
    pulumiUrn?: string;
    checksum?: string;
    lastModified: string;
    retryCount: number;
    errors: string[];
}

export enum ResourceStatus {
    PENDING = "PENDING",
    IN_PROGRESS = "IN_PROGRESS",
    COMPLETED = "COMPLETED",
    FAILED = "FAILED",
    SKIPPED = "SKIPPED",
    ROLLED_BACK = "ROLLED_BACK",
}

export interface Checkpoint {
    id: string;
    timestamp: string;
    resourcesCompleted: number;
    totalResources: number;
    state: MigrationState;
}

export interface RollbackPoint {
    id: string;
    timestamp: string;
    beforeState: MigrationState;
    afterState: MigrationState;
    reason?: string;
}

// Validation types
export interface ValidationResult {
    isValid: boolean;
    errors: ValidationError[];
    warnings: ValidationWarning[];
    metadata?: Record<string, any>;
}

export interface ValidationError {
    code: string;
    message: string;
    resource?: ResourceIdentifier;
    severity: "critical" | "error";
}

export interface ValidationWarning {
    code: string;
    message: string;
    resource?: ResourceIdentifier;
}

// Migration execution types
export interface MigrationResult {
    success: boolean;
    resources: MigratedResource[];
    resourcesCreated: number;
    resourcesUpdated: number;
    resourcesSkipped: number;
    resourcesFailed: number;
    duration: number;
    errors: MigrationError[];
}

export interface MigratedResource {
    identifier: ResourceIdentifier;
    pulumiResource: pulumi.Resource;
    status: ResourceStatus;
    outputs?: Record<string, any>;
}

export interface MigrationError {
    resource: ResourceIdentifier;
    error: Error;
    timestamp: string;
    retryable: boolean;
}

// Progress reporting types
export interface ProgressReport {
    phase: MigrationPhase;
    currentStep: number;
    totalSteps: number;
    percentComplete: number;
    estimatedTimeRemaining?: number;
    currentResource?: ResourceIdentifier;
    message: string;
}

export enum MigrationPhase {
    INITIALIZATION = "INITIALIZATION",
    VALIDATION = "VALIDATION",
    PLANNING = "PLANNING",
    EXECUTION = "EXECUTION",
    VERIFICATION = "VERIFICATION",
    CLEANUP = "CLEANUP",
    COMPLETE = "COMPLETE",
}

// Deduplication types
export interface DeduplicationResult {
    isDuplicate: boolean;
    existingResource?: pulumi.Resource;
    reason?: string;
    suggestedAction: DeduplicationAction;
}

export enum DeduplicationAction {
    SKIP = "SKIP",
    UPDATE = "UPDATE",
    REPLACE = "REPLACE",
    MERGE = "MERGE",
}

// Retry logic types
export interface RetryConfig {
    maxAttempts: number;
    delayMs: number;
    backoffMultiplier: number;
    maxDelayMs: number;
    retryableErrors: string[];
}

export interface RetryResult<T> {
    success: boolean;
    result?: T;
    error?: Error;
    attempts: number;
    totalDuration: number;
}

// Dependency graph types
export interface DependencyGraph {
    nodes: Map<string, DependencyNode>;
    edges: Map<string, Set<string>>;
}

export interface DependencyNode {
    resource: ResourceIdentifier;
    dependencies: string[];
    dependents: string[];
    level: number;
}

// Logger types
export enum LogLevel {
    DEBUG = "DEBUG",
    INFO = "INFO",
    WARN = "WARN",
    ERROR = "ERROR",
    FATAL = "FATAL",
}

export interface LogEntry {
    timestamp: string;
    level: LogLevel;
    message: string;
    context?: Record<string, any>;
    error?: Error;
}