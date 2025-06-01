/**
 * Centralized import management for Pulumi Migration Framework
 * This file serves as a single source of truth for all external imports
 * to prevent missing import issues and maintain consistency
 */

// Pulumi core imports
export * as pulumi from "@pulumi/pulumi";
export * as automation from "@pulumi/pulumi/automation";

// Pulumi providers
export * as gcp from "@pulumi/gcp";

// Node.js built-in modules
export * as fs from "fs/promises";
export * as fsSync from "fs";
export * as path from "path";
export * as crypto from "crypto";
export { EventEmitter } from "events";

// Third-party libraries
export { default as PQueue } from "p-queue";
export * as cliProgress from "cli-progress";
export { default as chalk } from "chalk";
export { default as ora } from "ora";
export * as yargs from "yargs";
export { hideBin } from "yargs/helpers";
export * as dotenv from "dotenv";
export * as winston from "winston";

// Type exports for convenience
export type { Config } from "@pulumi/pulumi";
export type { LocalWorkspace } from "@pulumi/pulumi/automation";