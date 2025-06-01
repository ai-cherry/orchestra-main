/**
 * Retry Manager for Pulumi Migration Framework
 * Implements sophisticated retry logic with exponential backoff,
 * jitter, and circuit breaker patterns
 */

import {
    MigrationConfig,
    RetryResult,
    RetryConfig,
} from "./types";
import { Logger } from "./logger";

export class RetryManager {
    private config: MigrationConfig;
    private logger: Logger;
    private circuitBreakers: Map<string, CircuitBreaker> = new Map();
    private defaultRetryConfig: RetryConfig;

    constructor(config: MigrationConfig, logger?: Logger) {
        this.config = config;
        this.logger = logger || new Logger("RetryManager");
        
        // Initialize default retry configuration
        this.defaultRetryConfig = {
            maxAttempts: config.retryAttempts,
            delayMs: config.retryDelayMs,
            backoffMultiplier: 2,
            maxDelayMs: 60000, // 1 minute max
            retryableErrors: [
                "ECONNRESET",
                "ETIMEDOUT",
                "ENOTFOUND",
                "RATE_LIMIT_EXCEEDED",
                "TEMPORARY_FAILURE",
                "RESOURCE_EXHAUSTED",
            ],
        };
    }

    /**
     * Execute an operation with retry logic
     */
    async executeWithRetry<T>(
        operation: () => Promise<T>,
        operationName: string,
        customConfig?: Partial<RetryConfig>
    ): Promise<RetryResult<T>> {
        const config = { ...this.defaultRetryConfig, ...customConfig };
        const circuitBreaker = this.getOrCreateCircuitBreaker(operationName);
        
        // Check circuit breaker state
        if (!circuitBreaker.allowRequest()) {
            this.logger.warn(`Circuit breaker OPEN for operation: ${operationName}`);
            return {
                success: false,
                error: new Error("Circuit breaker is OPEN"),
                attempts: 0,
                totalDuration: 0,
            };
        }

        const startTime = Date.now();
        let lastError: Error | undefined;
        let attempts = 0;

        for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
            attempts = attempt;
            
            try {
                this.logger.debug(`Attempt ${attempt}/${config.maxAttempts} for ${operationName}`);
                
                // Execute the operation
                const result = await operation();
                
                // Success - record it in circuit breaker
                circuitBreaker.recordSuccess();
                
                const totalDuration = Date.now() - startTime;
                this.logger.success(`Operation ${operationName} succeeded after ${attempt} attempts`, {
                    duration: totalDuration,
                });
                
                return {
                    success: true,
                    result,
                    attempts: attempt,
                    totalDuration,
                };
                
            } catch (error) {
                lastError = error as Error;
                
                // Record failure in circuit breaker
                circuitBreaker.recordFailure();
                
                this.logger.warn(`Attempt ${attempt} failed for ${operationName}`, {
                    error: lastError.message,
                    errorType: lastError.name,
                });
                
                // Check if error is retryable
                if (!this.isRetryableError(lastError, config.retryableErrors)) {
                    this.logger.error(`Non-retryable error for ${operationName}`, { error: lastError });
                    break;
                }
                
                // Don't delay after the last attempt
                if (attempt < config.maxAttempts) {
                    const delay = this.calculateDelay(attempt, config);
                    this.logger.debug(`Waiting ${delay}ms before retry...`);
                    await this.sleep(delay);
                }
            }
        }

        // All attempts failed
        const totalDuration = Date.now() - startTime;
        this.logger.error(`Operation ${operationName} failed after ${attempts} attempts`, {
            duration: totalDuration,
            lastError: lastError?.message,
        });

        return {
            success: false,
            error: lastError,
            attempts,
            totalDuration,
        };
    }

    /**
     * Execute multiple operations with retry and concurrency control
     */
    async executeMultipleWithRetry<T>(
        operations: Array<{ name: string; operation: () => Promise<T> }>,
        concurrency: number = 5,
        customConfig?: Partial<RetryConfig>
    ): Promise<Map<string, RetryResult<T>>> {
        const results = new Map<string, RetryResult<T>>();
        const queue = [...operations];
        const inProgress = new Set<Promise<void>>();

        while (queue.length > 0 || inProgress.size > 0) {
            // Start new operations up to concurrency limit
            while (inProgress.size < concurrency && queue.length > 0) {
                const item = queue.shift()!;
                
                const promise = this.executeWithRetry(
                    item.operation,
                    item.name,
                    customConfig
                ).then(result => {
                    results.set(item.name, result);
                    inProgress.delete(promise);
                });
                
                inProgress.add(promise);
            }

            // Wait for at least one operation to complete
            if (inProgress.size > 0) {
                await Promise.race(inProgress);
            }
        }

        return results;
    }

    /**
     * Calculate delay with exponential backoff and jitter
     */
    private calculateDelay(attempt: number, config: RetryConfig): number {
        // Exponential backoff
        const exponentialDelay = config.delayMs * Math.pow(config.backoffMultiplier, attempt - 1);
        
        // Cap at max delay
        const cappedDelay = Math.min(exponentialDelay, config.maxDelayMs);
        
        // Add jitter (±25% randomization)
        const jitterRange = cappedDelay * 0.25;
        const jitter = (Math.random() - 0.5) * 2 * jitterRange;
        
        return Math.round(cappedDelay + jitter);
    }

    /**
     * Check if an error is retryable
     */
    private isRetryableError(error: Error, retryableErrors: string[]): boolean {
        // Check error code
        if ('code' in error && retryableErrors.includes(error.code as string)) {
            return true;
        }
        
        // Check error message patterns
        const retryablePatterns = [
            /timeout/i,
            /rate limit/i,
            /temporary/i,
            /unavailable/i,
            /connection reset/i,
            /ECONNREFUSED/i,
        ];
        
        return retryablePatterns.some(pattern => pattern.test(error.message));
    }

    /**
     * Get or create circuit breaker for an operation
     */
    private getOrCreateCircuitBreaker(operationName: string): CircuitBreaker {
        if (!this.circuitBreakers.has(operationName)) {
            this.circuitBreakers.set(
                operationName,
                new CircuitBreaker(operationName, this.logger.child(`CircuitBreaker:${operationName}`))
            );
        }
        return this.circuitBreakers.get(operationName)!;
    }

    /**
     * Sleep for specified milliseconds
     */
    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get retry statistics
     */
    getStatistics(): {
        circuitBreakers: Array<{
            name: string;
            state: string;
            failures: number;
            successes: number;
        }>;
    } {
        const circuitBreakers = Array.from(this.circuitBreakers.entries()).map(([name, cb]) => ({
            name,
            state: cb.getState(),
            failures: cb.getFailureCount(),
            successes: cb.getSuccessCount(),
        }));

        return { circuitBreakers };
    }

    /**
     * Reset all circuit breakers
     */
    resetCircuitBreakers(): void {
        this.circuitBreakers.forEach(cb => cb.reset());
        this.logger.info("All circuit breakers reset");
    }
}

/**
 * Circuit Breaker implementation
 */
class CircuitBreaker {
    private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
    private failures = 0;
    private successes = 0;
    private lastFailureTime = 0;
    private readonly threshold = 5;
    private readonly timeout = 60000; // 1 minute
    private readonly successThreshold = 3;
    private halfOpenSuccesses = 0;

    constructor(
        private name: string,
        private logger: Logger
    ) {}

    allowRequest(): boolean {
        switch (this.state) {
            case CircuitBreakerState.CLOSED:
                return true;
                
            case CircuitBreakerState.OPEN:
                if (Date.now() - this.lastFailureTime > this.timeout) {
                    this.state = CircuitBreakerState.HALF_OPEN;
                    this.halfOpenSuccesses = 0;
                    this.logger.info(`Circuit breaker transitioning to HALF_OPEN`);
                    return true;
                }
                return false;
                
            case CircuitBreakerState.HALF_OPEN:
                return true;
                
            default:
                return false;
        }
    }

    recordSuccess(): void {
        this.successes++;
        
        switch (this.state) {
            case CircuitBreakerState.HALF_OPEN:
                this.halfOpenSuccesses++;
                if (this.halfOpenSuccesses >= this.successThreshold) {
                    this.state = CircuitBreakerState.CLOSED;
                    this.failures = 0;
                    this.logger.info(`Circuit breaker transitioning to CLOSED`);
                }
                break;
                
            case CircuitBreakerState.CLOSED:
                // Reset failure count on success
                this.failures = 0;
                break;
        }
    }

    recordFailure(): void {
        this.failures++;
        this.lastFailureTime = Date.now();
        
        switch (this.state) {
            case CircuitBreakerState.CLOSED:
                if (this.failures >= this.threshold) {
                    this.state = CircuitBreakerState.OPEN;
                    this.logger.warn(`Circuit breaker transitioning to OPEN after ${this.failures} failures`);
                }
                break;
                
            case CircuitBreakerState.HALF_OPEN:
                this.state = CircuitBreakerState.OPEN;
                this.logger.warn(`Circuit breaker transitioning back to OPEN`);
                break;
        }
    }

    getState(): string {
        return this.state;
    }

    getFailureCount(): number {
        return this.failures;
    }

    getSuccessCount(): number {
        return this.successes;
    }

    reset(): void {
        this.state = CircuitBreakerState.CLOSED;
        this.failures = 0;
        this.successes = 0;
        this.lastFailureTime = 0;
        this.halfOpenSuccesses = 0;
    }
}

enum CircuitBreakerState {
    CLOSED = "CLOSED",
    OPEN = "OPEN",
    HALF_OPEN = "HALF_OPEN",
}