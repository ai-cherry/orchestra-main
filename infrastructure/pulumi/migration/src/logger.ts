/**
 * Logger implementation for migration framework
 * Provides structured logging with different levels and context
 */

import { LogLevel, LogEntry } from "./types";
import * as fs from "fs";
import * as path from "path";

export class Logger {
    private context: string;
    private logFile?: string;
    private verboseMode: boolean;

    constructor(context: string, logFile?: string, verbose: boolean = false) {
        this.context = context;
        this.logFile = logFile;
        this.verboseMode = verbose;

        // Create log directory if file logging is enabled
        if (this.logFile) {
            const logDir = path.dirname(this.logFile);
            if (!fs.existsSync(logDir)) {
                fs.mkdirSync(logDir, { recursive: true });
            }
        }
    }

    /**
     * Log a debug message (only shown in verbose mode)
     */
    debug(message: string, context?: Record<string, any>): void {
        if (this.verboseMode) {
            this.log(LogLevel.DEBUG, message, context);
        }
    }

    /**
     * Log an info message
     */
    info(message: string, context?: Record<string, any>): void {
        this.log(LogLevel.INFO, message, context);
    }

    /**
     * Log a warning message
     */
    warn(message: string, context?: Record<string, any>): void {
        this.log(LogLevel.WARN, message, context);
    }

    /**
     * Log an error message
     */
    error(message: string, context?: Record<string, any> | { error?: Error }): void {
        this.log(LogLevel.ERROR, message, context);
    }

    /**
     * Log a fatal error message
     */
    fatal(message: string, context?: Record<string, any> | { error?: Error }): void {
        this.log(LogLevel.FATAL, message, context);
    }

    /**
     * Log a success message (info level with special formatting)
     */
    success(message: string, context?: Record<string, any>): void {
        this.log(LogLevel.INFO, `✅ ${message}`, context);
    }

    /**
     * Log a progress update
     */
    progress(current: number, total: number, message: string): void {
        const percentage = Math.round((current / total) * 100);
        const progressBar = this.createProgressBar(percentage);
        this.log(LogLevel.INFO, `${progressBar} ${percentage}% - ${message}`, {
            current,
            total,
            percentage,
        });
    }

    /**
     * Create a child logger with additional context
     */
    child(additionalContext: string): Logger {
        return new Logger(
            `${this.context}:${additionalContext}`,
            this.logFile,
            this.verboseMode
        );
    }

    /**
     * Core logging method
     */
    private log(level: LogLevel, message: string, context?: Record<string, any>): void {
        const entry: LogEntry = {
            timestamp: new Date().toISOString(),
            level,
            message: `[${this.context}] ${message}`,
            context,
        };

        // Extract error if present in context
        if (context && 'error' in context && context.error instanceof Error) {
            entry.error = context.error;
        }

        // Console output with color coding
        this.consoleOutput(entry);

        // File output if enabled
        if (this.logFile) {
            this.fileOutput(entry);
        }
    }

    /**
     * Output to console with appropriate formatting
     */
    private consoleOutput(entry: LogEntry): void {
        const colors = {
            [LogLevel.DEBUG]: '\x1b[36m',    // Cyan
            [LogLevel.INFO]: '\x1b[37m',     // White
            [LogLevel.WARN]: '\x1b[33m',     // Yellow
            [LogLevel.ERROR]: '\x1b[31m',    // Red
            [LogLevel.FATAL]: '\x1b[35m',    // Magenta
        };
        const reset = '\x1b[0m';
        const color = colors[entry.level];

        // Format the output
        let output = `${color}[${entry.timestamp}] [${entry.level}] ${entry.message}${reset}`;

        // Add context if present
        if (entry.context && Object.keys(entry.context).length > 0) {
            const contextStr = JSON.stringify(entry.context, null, 2);
            output += `\n${color}Context: ${contextStr}${reset}`;
        }

        // Add error stack trace if present
        if (entry.error) {
            output += `\n${color}Error: ${entry.error.message}${reset}`;
            if (entry.error.stack) {
                output += `\n${color}Stack: ${entry.error.stack}${reset}`;
            }
        }

        // Output based on level
        if (entry.level === LogLevel.ERROR || entry.level === LogLevel.FATAL) {
            console.error(output);
        } else if (entry.level === LogLevel.WARN) {
            console.warn(output);
        } else {
            console.log(output);
        }
    }

    /**
     * Output to file
     */
    private fileOutput(entry: LogEntry): void {
        if (!this.logFile) return;

        const logLine = JSON.stringify({
            ...entry,
            error: entry.error ? {
                message: entry.error.message,
                stack: entry.error.stack,
                name: entry.error.name,
            } : undefined,
        }) + '\n';

        try {
            fs.appendFileSync(this.logFile, logLine);
        } catch (error) {
            console.error('Failed to write to log file:', error);
        }
    }

    /**
     * Create a visual progress bar
     */
    private createProgressBar(percentage: number): string {
        const width = 30;
        const filled = Math.round((percentage / 100) * width);
        const empty = width - filled;
        return `[${'\u2588'.repeat(filled)}${'\u2591'.repeat(empty)}]`;
    }

    /**
     * Create a structured log report
     */
    generateReport(): string {
        if (!this.logFile || !fs.existsSync(this.logFile)) {
            return 'No log file available';
        }

        const logs = fs.readFileSync(this.logFile, 'utf-8')
            .split('\n')
            .filter(line => line.trim())
            .map(line => {
                try {
                    return JSON.parse(line) as LogEntry;
                } catch {
                    return null;
                }
            })
            .filter(entry => entry !== null) as LogEntry[];

        // Generate summary
        const summary = {
            totalLogs: logs.length,
            byLevel: {
                [LogLevel.DEBUG]: logs.filter(l => l.level === LogLevel.DEBUG).length,
                [LogLevel.INFO]: logs.filter(l => l.level === LogLevel.INFO).length,
                [LogLevel.WARN]: logs.filter(l => l.level === LogLevel.WARN).length,
                [LogLevel.ERROR]: logs.filter(l => l.level === LogLevel.ERROR).length,
                [LogLevel.FATAL]: logs.filter(l => l.level === LogLevel.FATAL).length,
            },
            errors: logs.filter(l => l.level === LogLevel.ERROR || l.level === LogLevel.FATAL)
                .map(l => ({
                    timestamp: l.timestamp,
                    message: l.message,
                    error: l.error?.message,
                })),
        };

        return JSON.stringify(summary, null, 2);
    }
}

/**
 * Global logger instance factory
 */
export function createLogger(
    context: string,
    config?: { logFile?: string; verbose?: boolean }
): Logger {
    const logFile = config?.logFile || process.env.MIGRATION_LOG_FILE;
    const verbose = config?.verbose ?? process.env.VERBOSE === 'true';
    return new Logger(context, logFile, verbose);
}