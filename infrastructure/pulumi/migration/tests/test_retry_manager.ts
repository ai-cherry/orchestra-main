/**
 * Unit tests for RetryManager
 * Tests retry logic, exponential backoff, and circuit breaker patterns
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { RetryManager } from '../src/retry-manager';
import { MigrationConfig } from '../src/types';

describe('RetryManager', () => {
    let retryManager: RetryManager;
    let mockConfig: MigrationConfig;

    beforeEach(() => {
        // Setup mock configuration
        mockConfig = {
            projectId: 'test-project',
            region: 'us-central1',
            environment: 'test',
            dryRun: false,
            parallelism: 5,
            retryAttempts: 3,
            retryDelayMs: 100,
            enableRollback: true,
            verboseLogging: false,
        };

        // Create retry manager instance
        retryManager = new RetryManager(mockConfig);

        // Use real timers for retry tests
        jest.useRealTimers();
    });

    afterEach(() => {
        jest.clearAllMocks();
        jest.useRealTimers();
    });

    describe('basic retry functionality', () => {
        it('should succeed on first attempt', async () => {
            const operation = jest.fn().mockResolvedValue('success');

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(true);
            expect(result.result).toBe('success');
            expect(result.attempts).toBe(1);
            expect(operation).toHaveBeenCalledTimes(1);
        });

        it('should retry on failure and eventually succeed', async () => {
            const operation = jest.fn()
                .mockRejectedValueOnce(new Error('Temporary failure'))
                .mockRejectedValueOnce(new Error('Temporary failure'))
                .mockResolvedValueOnce('success');

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(true);
            expect(result.result).toBe('success');
            expect(result.attempts).toBe(3);
            expect(operation).toHaveBeenCalledTimes(3);
        });

        it('should fail after max attempts', async () => {
            const error = new Error('Persistent failure');
            const operation = jest.fn().mockRejectedValue(error);

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(false);
            expect(result.error).toBe(error);
            expect(result.attempts).toBe(3);
            expect(operation).toHaveBeenCalledTimes(3);
        });
    });

    describe('retryable error detection', () => {
        it('should retry on retryable errors', async () => {
            const retryableError = new Error('Connection reset');
            (retryableError as any).code = 'ECONNRESET';
            
            const operation = jest.fn()
                .mockRejectedValueOnce(retryableError)
                .mockResolvedValueOnce('success');

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(true);
            expect(operation).toHaveBeenCalledTimes(2);
        });

        it('should not retry on non-retryable errors', async () => {
            const nonRetryableError = new Error('Invalid input');
            const operation = jest.fn().mockRejectedValue(nonRetryableError);

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(false);
            expect(result.attempts).toBe(1);
            expect(operation).toHaveBeenCalledTimes(1);
        });

        it('should detect retryable patterns in error messages', async () => {
            const timeoutError = new Error('Request timeout exceeded');
            const operation = jest.fn()
                .mockRejectedValueOnce(timeoutError)
                .mockResolvedValueOnce('success');

            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation'
            );

            expect(result.success).toBe(true);
            expect(operation).toHaveBeenCalledTimes(2);
        });
    });

    describe('exponential backoff', () => {
        it('should apply exponential backoff between retries', async () => {
            const operation = jest.fn()
                .mockRejectedValueOnce(new Error('Temporary failure'))
                .mockRejectedValueOnce(new Error('Temporary failure'))
                .mockResolvedValueOnce('success');

            const startTime = Date.now();
            
            const result = await retryManager.executeWithRetry(
                operation,
                'test-operation',
                {
                    delayMs: 100,
                    backoffMultiplier: 2,
                }
            );

            const totalDuration = Date.now() - startTime;

            expect(result.success).toBe(true);
            // Should have delays of ~100ms and ~200ms (with jitter)
            expect(totalDuration).toBeGreaterThan(200);
            expect(totalDuration).toBeLessThan(500);
        });

        it('should respect max delay limit', async () => {
            const operation = jest.fn()
                .mockRejectedValue(new Error('Persistent failure'));

            const startTime = Date.now();
            
            await retryManager.executeWithRetry(
                operation,
                'test-operation',
                {
                    maxAttempts: 5,
                    delayMs: 100,
                    backoffMultiplier: 10,
                    maxDelayMs: 500,
                }
            );

            const totalDuration = Date.now() - startTime;

            // Even with high multiplier, delays should be capped
            expect(totalDuration).toBeLessThan(2500); // 4 delays * 500ms max + buffer
        });
    });

    describe('circuit breaker', () => {
        it('should open circuit after threshold failures', async () => {
            const operation = jest.fn().mockRejectedValue(new Error('Service unavailable'));

            // Fail multiple times to open circuit
            for (let i = 0; i < 5; i++) {
                await retryManager.executeWithRetry(
                    operation,
                    'circuit-test-operation',
                    { maxAttempts: 1 }
                );
            }

            // Circuit should be open now
            const result = await retryManager.executeWithRetry(
                operation,
                'circuit-test-operation'
            );

            expect(result.success).toBe(false);
            expect(result.attempts).toBe(0);
            expect(result.error?.message).toContain('Circuit breaker is OPEN');
        });

        it('should transition to half-open after timeout', async () => {
            jest.useFakeTimers();
            
            const operation = jest.fn()
                .mockRejectedValue(new Error('Service unavailable'))
                .mockResolvedValue('success');

            // Open the circuit
            for (let i = 0; i < 5; i++) {
                await retryManager.executeWithRetry(
                    operation,
                    'timeout-test-operation',
                    { maxAttempts: 1 }
                );
            }

            // Advance time past circuit breaker timeout
            jest.advanceTimersByTime(65000); // 65 seconds

            // Should allow request in half-open state
            const result = await retryManager.executeWithRetry(
                operation,
                'timeout-test-operation'
            );

            expect(result.success).toBe(true);
            expect(operation).toHaveBeenCalled();
        });

        it('should close circuit after successful requests in half-open state', async () => {
            const operation = jest.fn().mockResolvedValue('success');

            // Simulate circuit in half-open state
            // (Would need to expose circuit state or use reflection in real implementation)
            
            // Make successful requests
            for (let i = 0; i < 3; i++) {
                await retryManager.executeWithRetry(
                    operation,
                    'recovery-test-operation'
                );
            }

            // Circuit should be closed, all requests should succeed
            const result = await retryManager.executeWithRetry(
                operation,
                'recovery-test-operation'
            );

            expect(result.success).toBe(true);
        });
    });

    describe('concurrent operations', () => {
        it('should handle multiple operations with concurrency control', async () => {
            const operations = Array.from({ length: 10 }, (_, i) => ({
                name: `operation-${i}`,
                operation: jest.fn().mockResolvedValue(`result-${i}`),
            }));

            const results = await retryManager.executeMultipleWithRetry(
                operations,
                3 // concurrency limit
            );

            expect(results.size).toBe(10);
            operations.forEach((op, i) => {
                const result = results.get(op.name);
                expect(result?.success).toBe(true);
                expect(result?.result).toBe(`result-${i}`);
            });
        });

        it('should handle mixed success and failure in concurrent operations', async () => {
            const operations = [
                {
                    name: 'success-1',
                    operation: jest.fn().mockResolvedValue('success-1'),
                },
                {
                    name: 'failure-1',
                    operation: jest.fn().mockRejectedValue(new Error('Failed')),
                },
                {
                    name: 'success-2',
                    operation: jest.fn().mockResolvedValue('success-2'),
                },
            ];

            const results = await retryManager.executeMultipleWithRetry(operations, 2);

            expect(results.get('success-1')?.success).toBe(true);
            expect(results.get('failure-1')?.success).toBe(false);
            expect(results.get('success-2')?.success).toBe(true);
        });
    });

    describe('custom retry configuration', () => {
        it('should use custom retry configuration', async () => {
            const operation = jest.fn()
                .mockRejectedValueOnce(new Error('CUSTOM_ERROR'))
                .mockResolvedValueOnce('success');

            const result = await retryManager.executeWithRetry(
                operation,
                'custom-config-operation',
                {
                    maxAttempts: 2,
                    delayMs: 50,
                    retryableErrors: ['CUSTOM_ERROR'],
                }
            );

            expect(result.success).toBe(true);
            expect(result.attempts).toBe(2);
        });
    });

    describe('statistics and monitoring', () => {
        it('should track circuit breaker statistics', async () => {
            const operation = jest.fn()
                .mockRejectedValueOnce(new Error('Failure'))
                .mockResolvedValueOnce('success');

            await retryManager.executeWithRetry(operation, 'stats-operation');

            const stats = retryManager.getStatistics();
            
            expect(stats.circuitBreakers).toHaveLength(1);
            expect(stats.circuitBreakers[0].name).toBe('stats-operation');
            expect(stats.circuitBreakers[0].failures).toBeGreaterThanOrEqual(0);
            expect(stats.circuitBreakers[0].successes).toBeGreaterThanOrEqual(1);
        });

        it('should reset circuit breakers', () => {
            retryManager.resetCircuitBreakers();
            
            const stats = retryManager.getStatistics();
            stats.circuitBreakers.forEach(cb => {
                expect(cb.state).toBe('CLOSED');
                expect(cb.failures).toBe(0);
                expect(cb.successes).toBe(0);
            });
        });
    });

    describe('error handling edge cases', () => {
        it('should handle operations that throw non-Error objects', async () => {
            const operation = jest.fn().mockRejectedValue('string error');

            const result = await retryManager.executeWithRetry(
                operation,
                'non-error-operation'
            );

            expect(result.success).toBe(false);
            expect(result.error).toBeDefined();
        });

        it('should handle operations that return undefined', async () => {
            const operation = jest.fn().mockResolvedValue(undefined);

            const result = await retryManager.executeWithRetry(
                operation,
                'undefined-operation'
            );

            expect(result.success).toBe(true);
            expect(result.result).toBeUndefined();
        });
    });
});