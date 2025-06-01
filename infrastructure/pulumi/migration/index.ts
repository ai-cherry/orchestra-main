#!/usr/bin/env node
/**
 * Pulumi Infrastructure Migration Framework - Main Entry Point
 *
 * A comprehensive solution for migrating existing infrastructure to Pulumi
 * with robust deduplication, state management, rollback capabilities, and
 * idempotent operations.
 */

import { pulumi, yargs, hideBin, dotenv, chalk, ora, fs, path } from "./src/imports";
import { EnhancedMigrationOrchestrator } from "./src/orchestrator-enhanced";
import { MigrationConfig } from "./src/types";
import { Logger, createLogger } from "./src/logger";

// Load environment variables
dotenv.config();

// ASCII Art Banner
const banner = `
${chalk.cyan(`
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ██╗   ██╗██╗     ██╗   ██╗███╗   ███╗██╗          ║
║   ██╔══██╗██║   ██║██║     ██║   ██║████╗ ████║██║          ║
║   ██████╔╝██║   ██║██║     ██║   ██║██╔████╔██║██║          ║
║   ██╔═══╝ ██║   ██║██║     ██║   ██║██║╚██╔╝██║██║          ║
║   ██║     ╚██████╔╝███████╗╚██████╔╝██║ ╚═╝ ██║██║          ║
║   ╚═╝      ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝          ║
║                                                               ║
║          Infrastructure Migration Framework v1.0.0            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
`)}`;

/**
 * CLI Command Handlers
 */

// Migrate command
async function migrate(argv: any): Promise<void> {
    console.log(banner);
    
    const spinner = ora("Initializing migration framework...").start();
    const logger = createLogger("CLI", { 
        logFile: argv.logFile,
        verbose: argv.verbose 
    });
    
    try {
        // Load configuration
        const config = await loadConfiguration(argv, logger);
        spinner.text = "Configuration loaded";
        
        // Create orchestrator
        const orchestrator = new EnhancedMigrationOrchestrator(config, logger);
        
        // Initialize
        spinner.text = "Initializing orchestrator...";
        await orchestrator.initialize();
        spinner.succeed("Orchestrator initialized");
        
        // Confirm migration
        if (!argv.yes && !await confirmMigration(config)) {
            spinner.info("Migration cancelled by user");
            process.exit(0);
        }
        
        // Execute migration
        console.log(chalk.cyan("\n🚀 Starting migration...\n"));
        const result = await orchestrator.executeMigration();
        
        // Shutdown
        await orchestrator.shutdown();
        
        if (result.success) {
            console.log(chalk.green("\n✅ Migration completed successfully!"));
        } else {
            console.log(chalk.red("\n❌ Migration completed with errors"));
            process.exit(1);
        }
        
    } catch (error) {
        spinner.fail("Migration failed");
        logger.fatal("Migration error", { error });
        console.error(chalk.red("\n💥 Fatal error:"), error);
        process.exit(1);
    }
}

// Validate command
async function validate(argv: any): Promise<void> {
    console.log(banner);
    
    const spinner = ora("Running validation...").start();
    const logger = createLogger("Validator", { verbose: argv.verbose });
    
    try {
        const config = await loadConfiguration(argv, logger);
        
        // Import validator dynamically
        const { ResourceValidator } = await import("./src/validator");
        const validator = new ResourceValidator(config, logger);
        
        spinner.text = "Running pre-migration validation...";
        const result = await validator.validatePreMigration();
        
        if (result.isValid) {
            spinner.succeed("Validation passed");
            console.log(chalk.green("\n✅ All validation checks passed!"));
        } else {
            spinner.fail("Validation failed");
            console.log(chalk.red("\n❌ Validation errors:"));
            result.errors.forEach(error => {
                console.log(chalk.red(`  • ${error.code}: ${error.message}`));
            });
        }
        
        if (result.warnings.length > 0) {
            console.log(chalk.yellow("\n⚠️  Warnings:"));
            result.warnings.forEach(warning => {
                console.log(chalk.yellow(`  • ${warning.code}: ${warning.message}`));
            });
        }
        
    } catch (error) {
        spinner.fail("Validation error");
        console.error(chalk.red("\n💥 Error:"), error);
        process.exit(1);
    }
}

// Discover command
async function discover(argv: any): Promise<void> {
    console.log(banner);
    
    const spinner = ora("Discovering resources...").start();
    const logger = createLogger("Discovery", { verbose: argv.verbose });
    
    try {
        const config = await loadConfiguration(argv, logger);
        
        // Import discovery dynamically
        const { ResourceDiscovery } = await import("./src/resource-discovery");
        const discovery = new ResourceDiscovery(config, logger);
        
        spinner.text = "Scanning infrastructure...";
        const resources = await discovery.discoverAll();
        spinner.succeed(`Discovered ${resources.length} resources`);
        
        // Display summary
        console.log(chalk.cyan("\n📊 Discovery Summary:\n"));
        
        const byType = resources.reduce((acc, r) => {
            acc[r.source.type] = (acc[r.source.type] || 0) + 1;
            return acc;
        }, {} as Record<string, number>);
        
        Object.entries(byType).forEach(([type, count]) => {
            console.log(`  ${chalk.blue(type)}: ${count}`);
        });
        
        // Save report if requested
        if (argv.output) {
            const report = discovery.getDiscoveryReport();
            fs.writeFileSync(argv.output, report);
            console.log(chalk.green(`\n✅ Report saved to: ${argv.output}`));
        }
        
    } catch (error) {
        spinner.fail("Discovery failed");
        console.error(chalk.red("\n💥 Error:"), error);
        process.exit(1);
    }
}

// Status command
async function status(argv: any): Promise<void> {
    const logger = createLogger("Status", { verbose: argv.verbose });
    
    try {
        const config = await loadConfiguration(argv, logger);
        
        // Import state manager dynamically
        const { AsyncStateManager } = await import("./src/state-manager-async");
        const stateManager = new AsyncStateManager(config, logger);
        await stateManager.initialize();
        
        const state = stateManager.getState();
        const progress = stateManager.getProgress();
        
        console.log(chalk.cyan("\n📊 Migration Status:\n"));
        console.log(`  Status: ${chalk.bold(state.status)}`);
        console.log(`  Environment: ${state.environment}`);
        console.log(`  Last Updated: ${state.timestamp}`);
        console.log(`\n  Progress:`);
        console.log(`    Total Resources: ${progress.total}`);
        console.log(`    Completed: ${chalk.green(progress.completed.toString())}`);
        console.log(`    Failed: ${chalk.red(progress.failed.toString())}`);
        console.log(`    In Progress: ${chalk.yellow(progress.inProgress.toString())}`);
        console.log(`    Pending: ${chalk.gray(progress.pending.toString())}`);
        console.log(`    Completion: ${progress.percentage}%`);
        
        await stateManager.shutdown();
        
    } catch (error) {
        console.error(chalk.red("\n💥 Error:"), error);
        process.exit(1);
    }
}

// Rollback command
async function rollback(argv: any): Promise<void> {
    console.log(banner);
    
    const spinner = ora("Preparing rollback...").start();
    const logger = createLogger("Rollback", { verbose: argv.verbose });
    
    try {
        const config = await loadConfiguration(argv, logger);
        
        // Confirm rollback
        if (!argv.yes && !await confirmRollback()) {
            spinner.info("Rollback cancelled by user");
            process.exit(0);
        }
        
        // Create orchestrator
        const orchestrator = new EnhancedMigrationOrchestrator(config, logger);
        await orchestrator.initialize();
        
        spinner.text = "Executing rollback...";
        await orchestrator.rollback();
        spinner.succeed("Rollback completed");
        
        await orchestrator.shutdown();
        
    } catch (error) {
        spinner.fail("Rollback failed");
        console.error(chalk.red("\n💥 Error:"), error);
        process.exit(1);
    }
}

/**
 * Helper Functions
 */

async function loadConfiguration(argv: any, logger: Logger): Promise<MigrationConfig> {
    // Load from Pulumi config
    const pulumiConfig = new pulumi.Config("migration");
    
    // Override with CLI arguments
    const config: MigrationConfig = {
        projectId: argv.project || pulumiConfig.require("projectId"),
        region: argv.region || pulumiConfig.get("region") || "us-central1",
        environment: argv.stack || pulumi.getStack(),
        dryRun: argv.dryRun || false,
        parallelism: argv.parallelism || pulumiConfig.getNumber("parallelism") || 5,
        retryAttempts: argv.retries || pulumiConfig.getNumber("retryAttempts") || 3,
        retryDelayMs: pulumiConfig.getNumber("retryDelayMs") || 5000,
        enableRollback: argv.rollback !== false,
        verboseLogging: argv.verbose || false,
    };
    
    // Validate configuration
    if (!config.projectId) {
        throw new Error("Project ID is required");
    }
    
    logger.debug("Configuration loaded", { config });
    return config;
}

async function confirmMigration(config: MigrationConfig): Promise<boolean> {
    console.log(chalk.yellow("\n⚠️  Migration Configuration:"));
    console.log(`  Project: ${config.projectId}`);
    console.log(`  Region: ${config.region}`);
    console.log(`  Environment: ${config.environment}`);
    console.log(`  Parallelism: ${config.parallelism}`);
    console.log(`  Dry Run: ${config.dryRun}`);
    
    const readline = await import("readline");
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
    
    return new Promise((resolve) => {
        rl.question(chalk.yellow("\n❓ Do you want to proceed? (y/N): "), (answer) => {
            rl.close();
            resolve(answer.toLowerCase() === "y");
        });
    });
}

async function confirmRollback(): Promise<boolean> {
    console.log(chalk.red("\n⚠️  WARNING: This will rollback the migration!"));
    
    const readline = await import("readline");
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
    });
    
    return new Promise((resolve) => {
        rl.question(chalk.red("\n❓ Are you sure you want to rollback? (y/N): "), (answer) => {
            rl.close();
            resolve(answer.toLowerCase() === "y");
        });
    });
}

/**
 * CLI Setup
 */

const argv = yargs(hideBin(process.argv))
    .scriptName("pulumi-migrate")
    .usage("$0 <command> [options]")
    .command(
        "migrate",
        "Execute infrastructure migration",
        (yargs) => {
            return yargs
                .option("project", {
                    alias: "p",
                    type: "string",
                    description: "GCP project ID",
                })
                .option("region", {
                    alias: "r",
                    type: "string",
                    description: "GCP region",
                })
                .option("stack", {
                    alias: "s",
                    type: "string",
                    description: "Pulumi stack name",
                })
                .option("dry-run", {
                    alias: "d",
                    type: "boolean",
                    description: "Perform a dry run without making changes",
                    default: false,
                })
                .option("parallelism", {
                    alias: "P",
                    type: "number",
                    description: "Number of parallel operations",
                })
                .option("retries", {
                    type: "number",
                    description: "Number of retry attempts",
                })
                .option("yes", {
                    alias: "y",
                    type: "boolean",
                    description: "Skip confirmation prompts",
                    default: false,
                })
                .option("verbose", {
                    alias: "v",
                    type: "boolean",
                    description: "Enable verbose logging",
                    default: false,
                })
                .option("log-file", {
                    type: "string",
                    description: "Path to log file",
                });
        },
        migrate
    )
    .command(
        "validate",
        "Validate migration prerequisites",
        (yargs) => {
            return yargs
                .option("project", {
                    alias: "p",
                    type: "string",
                    description: "GCP project ID",
                })
                .option("verbose", {
                    alias: "v",
                    type: "boolean",
                    description: "Enable verbose logging",
                    default: false,
                });
        },
        validate
    )
    .command(
        "discover",
        "Discover infrastructure resources",
        (yargs) => {
            return yargs
                .option("project", {
                    alias: "p",
                    type: "string",
                    description: "GCP project ID",
                })
                .option("output", {
                    alias: "o",
                    type: "string",
                    description: "Output file for discovery report",
                })
                .option("verbose", {
                    alias: "v",
                    type: "boolean",
                    description: "Enable verbose logging",
                    default: false,
                });
        },
        discover
    )
    .command(
        "status",
        "Show migration status",
        (yargs) => {
            return yargs
                .option("stack", {
                    alias: "s",
                    type: "string",
                    description: "Pulumi stack name",
                })
                .option("verbose", {
                    alias: "v",
                    type: "boolean",
                    description: "Enable verbose logging",
                    default: false,
                });
        },
        status
    )
    .command(
        "rollback",
        "Rollback migration",
        (yargs) => {
            return yargs
                .option("yes", {
                    alias: "y",
                    type: "boolean",
                    description: "Skip confirmation prompt",
                    default: false,
                })
                .option("verbose", {
                    alias: "v",
                    type: "boolean",
                    description: "Enable verbose logging",
                    default: false,
                });
        },
        rollback
    )
    .demandCommand(1, "You must specify a command")
    .help()
    .alias("help", "h")
    .version()
    .alias("version", "V")
    .epilogue("For more information, visit: https://github.com/your-org/pulumi-migration")
    .argv;

// Handle uncaught errors
process.on("unhandledRejection", (error) => {
    console.error(chalk.red("\n💥 Unhandled error:"), error);
    process.exit(1);
});

process.on("SIGINT", () => {
    console.log(chalk.yellow("\n\n🛑 Migration interrupted by user"));
    process.exit(130);
});