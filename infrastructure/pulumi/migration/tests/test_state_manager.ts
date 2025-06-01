/**
 * Unit tests for AsyncStateManager
 * Tests state persistence, caching, and rollback functionality
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { AsyncStateManager } from '../src/state-manager-async';
import { MigrationConfig, MigrationStatus, ResourceStatus } from '../src/types';
import * as fs from 'fs/promises';
import * as path from 'path';

// Mock the fs module
jest.mock('fs/promises');
jest.mock('events');

describe('AsyncStateManager', () => {
    let stateManager: AsyncStateManager;
    let mockConfig: MigrationConfig;
    let testStateDir: string;

    beforeEach(() => {
        // Setup mock configuration
        mockConfig = {
            projectId: 'test-project',
            region: 'us-central1',
            environment: 'test',
            dryRun: false,
            parallelism: 5,
            retryAttempts: 3,
            retryDelayMs: 1000,
            enableRollback: true,
            verboseLogging: false,
        };

        testStateDir = '/tmp/test-pulumi-migration';
        
        // Mock process.cwd()
        jest.spyOn(process, 'cwd').mockReturnValue('/test');
        
        // Create state manager instance
        stateManager = new AsyncStateManager(mockConfig);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('initialization', () => {
        it('should create state directory if it does not exist', async () => {
            const mockAccess = jest.mocked(fs.access);
            const mockMkdir = jest.mocked(fs.mkdir);
            
            mockAccess.mockRejectedValueOnce(new Error('ENOENT'));
            mockMkdir.mockResolvedValueOnce(undefined);

            await stateManager.initialize();

            expect(mockMkdir).toHaveBeenCalledWith(
                expect.stringContaining('.pulumi-migration'),
                { recursive: true }
            );
        });

        it('should load existing state file', async () => {
            const mockState = {
                version: '1.0.0',
                timestamp: new Date().toISOString(),
                environment: 'test',
                status: MigrationStatus.IN_PROGRESS,
                resources: [],
                checkpoints: [],
                rollbackPoints: [],
            };

            const mockReadFile = jest.mocked(fs.readFile);
            mockReadFile.mockResolvedValueOnce(JSON.stringify(mockState));

            await stateManager.initialize();

            const state = stateManager.getState();
            expect(state.status).toBe(MigrationStatus.IN_PROGRESS);
        });

        it('should create new state if file does not exist', async () => {
            const mockReadFile = jest.mocked(fs.readFile);
            const mockWriteFile = jest.mocked(fs.writeFile);
            
            mockReadFile.mockRejectedValueOnce({ code: 'ENOENT' });
            mockWriteFile.mockResolvedValueOnce();

            await stateManager.initialize();

            const state = stateManager.getState();
            expect(state.status).toBe(MigrationStatus.NOT_STARTED);
        });
    });

    describe('resource state management', () => {
        beforeEach(async () => {
            await stateManager.initialize();
        });

        it('should update resource state', () => {
            const identifier = {
                type: 'gcp:compute:Instance',
                name: 'test-instance',
            };

            stateManager.updateResourceState(identifier, {
                status: ResourceStatus.IN_PROGRESS,
            });

            const resourceState = stateManager.getResourceState(identifier);
            expect(resourceState?.status).toBe(ResourceStatus.IN_PROGRESS);
        });

        it('should cache resource states', () => {
            const identifier1 = {
                type: 'gcp:compute:Instance',
                name: 'instance-1',
            };
            const identifier2 = {
                type: 'gcp:compute:Instance',
                name: 'instance-2',
            };

            stateManager.updateResourceState(identifier1, {
                status: ResourceStatus.COMPLETED,
            });
            stateManager.updateResourceState(identifier2, {
                status: ResourceStatus.FAILED,
            });

            const completed = stateManager.getResourcesByStatus(ResourceStatus.COMPLETED);
            const failed = stateManager.getResourcesByStatus(ResourceStatus.FAILED);

            expect(completed).toHaveLength(1);
            expect(failed).toHaveLength(1);
        });

        it('should calculate resource checksum', () => {
            const identifier = {
                type: 'gcp:compute:Instance',
                name: 'test-instance',
                provider: 'gcp',
                region: 'us-central1',
                labels: { env: 'test' },
            };

            const checksum1 = stateManager.calculateResourceChecksum(identifier);
            const checksum2 = stateManager.calculateResourceChecksum(identifier);

            expect(checksum1).toBe(checksum2);
            expect(checksum1).toMatch(/^[a-f0-9]{64}$/); // SHA256 hex
        });
    });

    describe('checkpoint management', () => {
        beforeEach(async () => {
            await stateManager.initialize();
        });

        it('should create checkpoint', async () => {
            const mockWriteFile = jest.mocked(fs.writeFile);
            mockWriteFile.mockResolvedValue();

            // Add some resources
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-1' },
                { status: ResourceStatus.COMPLETED }
            );

            const checkpoint = await stateManager.createCheckpoint('test-checkpoint');

            expect(checkpoint.id).toBe('test-checkpoint');
            expect(checkpoint.resourcesCompleted).toBe(1);
            expect(checkpoint.totalResources).toBe(1);
        });

        it('should limit number of checkpoints', () => {
            // Add many checkpoints
            for (let i = 0; i < 30; i++) {
                stateManager.createCheckpoint(`checkpoint-${i}`);
            }

            stateManager.cleanup(10, 5);

            const state = stateManager.getState();
            expect(state.checkpoints.length).toBeLessThanOrEqual(10);
        });
    });

    describe('rollback functionality', () => {
        beforeEach(async () => {
            await stateManager.initialize();
        });

        it('should create rollback point', async () => {
            const rollbackPoint = await stateManager.createRollbackPoint('test-rollback');

            expect(rollbackPoint.id).toBeTruthy();
            expect(rollbackPoint.reason).toBe('test-rollback');
            expect(rollbackPoint.beforeState).toBeTruthy();
        });

        it('should rollback to specific point', async () => {
            // Create initial state
            stateManager.updateStatus(MigrationStatus.IN_PROGRESS);
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-1' },
                { status: ResourceStatus.COMPLETED }
            );

            // Create rollback point
            const rollbackPoint = await stateManager.createRollbackPoint('before-changes');

            // Make changes
            stateManager.updateStatus(MigrationStatus.FAILED);
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-2' },
                { status: ResourceStatus.FAILED }
            );

            // Rollback
            stateManager.rollback(rollbackPoint.id);

            const state = stateManager.getState();
            expect(state.status).toBe(MigrationStatus.ROLLED_BACK);
            expect(state.resources).toHaveLength(1);
        });

        it('should throw error for invalid rollback point', () => {
            expect(() => {
                stateManager.rollback('non-existent-id');
            }).toThrow('Rollback point not found');
        });
    });

    describe('progress tracking', () => {
        beforeEach(async () => {
            await stateManager.initialize();
        });

        it('should calculate progress correctly', () => {
            // Add resources with different statuses
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-1' },
                { status: ResourceStatus.COMPLETED }
            );
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-2' },
                { status: ResourceStatus.FAILED }
            );
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-3' },
                { status: ResourceStatus.IN_PROGRESS }
            );
            stateManager.updateResourceState(
                { type: 'gcp:compute:Instance', name: 'instance-4' },
                { status: ResourceStatus.PENDING }
            );

            const progress = stateManager.getProgress();

            expect(progress.total).toBe(4);
            expect(progress.completed).toBe(1);
            expect(progress.failed).toBe(1);
            expect(progress.inProgress).toBe(1);
            expect(progress.pending).toBe(1);
            expect(progress.percentage).toBe(25);
        });
    });

    describe('state persistence', () => {
        it('should batch write updates', async () => {
            const mockWriteFile = jest.mocked(fs.writeFile);
            mockWriteFile.mockResolvedValue();

            await stateManager.initialize();

            // Make multiple updates quickly
            for (let i = 0; i < 10; i++) {
                stateManager.updateResourceState(
                    { type: 'gcp:compute:Instance', name: `instance-${i}` },
                    { status: ResourceStatus.PENDING }
                );
            }

            // Wait for batch write
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Should have batched the writes
            expect(mockWriteFile).toHaveBeenCalledTimes(1);
        });

        it('should handle write failures gracefully', async () => {
            const mockWriteFile = jest.mocked(fs.writeFile);
            mockWriteFile.mockRejectedValue(new Error('Write failed'));

            await stateManager.initialize();

            // Should not throw
            stateManager.updateStatus(MigrationStatus.IN_PROGRESS);

            // Wait for write attempt
            await new Promise(resolve => setTimeout(resolve, 1500));

            // State should still be accessible
            const state = stateManager.getState();
            expect(state.status).toBe(MigrationStatus.IN_PROGRESS);
        });
    });

    describe('cleanup and shutdown', () => {
        it('should cleanup old checkpoints and rollback points', () => {
            // Add many checkpoints and rollback points
            for (let i = 0; i < 30; i++) {
                stateManager.createCheckpoint(`checkpoint-${i}`);
                stateManager.createRollbackPoint(`rollback-${i}`);
            }

            stateManager.cleanup(10, 5);

            const state = stateManager.getState();
            expect(state.checkpoints.length).toBe(10);
            expect(state.rollbackPoints.length).toBe(5);
        });

        it('should flush pending writes on shutdown', async () => {
            const mockWriteFile = jest.mocked(fs.writeFile);
            mockWriteFile.mockResolvedValue();

            await stateManager.initialize();

            // Make an update
            stateManager.updateStatus(MigrationStatus.COMPLETED);

            // Shutdown immediately
            await stateManager.shutdown();

            // Should have flushed the write
            expect(mockWriteFile).toHaveBeenCalled();
        });
    });

    describe('metrics', () => {
        it('should provide accurate metrics', async () => {
            await stateManager.initialize();

            // Add some resources
            for (let i = 0; i < 5; i++) {
                stateManager.updateResourceState(
                    { type: 'gcp:compute:Instance', name: `instance-${i}` },
                    { status: ResourceStatus.PENDING }
                );
            }

            const metrics = stateManager.getMetrics();

            expect(metrics.queueSize).toBeGreaterThanOrEqual(0);
            expect(metrics.cacheSize).toBe(5);
            expect(metrics.checksumCacheSize).toBe(0); // No checksums calculated
            expect(metrics.isWriting).toBe(false);
        });
    });
});
