/**
 * Test setup and configuration
 * Initializes test environment and global mocks
 */

import { jest } from '@jest/globals';

// Set test environment
process.env.NODE_ENV = 'test';
process.env.PULUMI_CONFIG_PASSPHRASE = 'test-passphrase';
process.env.PULUMI_BACKEND_URL = 'file://~/.pulumi-test';

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
};

// Mock process.exit to prevent tests from exiting
process.exit = jest.fn() as any;

// Mock timers for testing time-dependent code
jest.useFakeTimers();

// Global test utilities
global.flushPromises = () => new Promise(resolve => setImmediate(resolve));

// Mock file system operations
jest.mock('fs/promises', () => ({
    access: jest.fn(),
    mkdir: jest.fn(),
    readFile: jest.fn(),
    writeFile: jest.fn(),
    unlink: jest.fn(),
    rename: jest.fn(),
    stat: jest.fn(),
    open: jest.fn(() => ({
        write: jest.fn(),
        close: jest.fn(),
    })),
}));

// Mock crypto module
jest.mock('crypto', () => ({
    createHash: jest.fn(() => ({
        update: jest.fn().mockReturnThis(),
        digest: jest.fn(() => 'mocked-hash-value'),
    })),
    randomBytes: jest.fn(() => ({
        toString: jest.fn(() => 'mocked-random-id'),
    })),
}));

// Mock EventEmitter
jest.mock('events', () => {
    const EventEmitter = jest.fn(() => ({
        on: jest.fn(),
        emit: jest.fn(),
        once: jest.fn(),
        off: jest.fn(),
        removeListener: jest.fn(),
        removeAllListeners: jest.fn(),
    }));
    return { EventEmitter };
});

// Mock Pulumi modules
jest.mock('@pulumi/pulumi', () => ({
    Config: jest.fn(() => ({
        require: jest.fn((key: string) => `mock-${key}`),
        get: jest.fn((key: string) => `mock-${key}`),
        getNumber: jest.fn(() => 5),
        getBoolean: jest.fn(() => false),
    })),
    getStack: jest.fn(() => 'test-stack'),
    automation: {
        LocalWorkspace: {
            selectStack: jest.fn(() => ({
                info: jest.fn(),
                exportStack: jest.fn(() => ({
                    deployment: {
                        resources: [],
                    },
                })),
            })),
        },
    },
    CustomResource: jest.fn(),
    Resource: jest.fn(),
    Output: jest.fn(),
}));

// Mock GCP provider
jest.mock('@pulumi/gcp', () => ({
    compute: {
        getZones: jest.fn(() => ({ zones: [] })),
        getInstances: jest.fn(() => ({ instances: [] })),
        getNetworks: jest.fn(() => ({ networks: [] })),
        getSubnetworks: jest.fn(() => ({ subnetworks: [] })),
        getDisks: jest.fn(() => ({ disks: [] })),
    },
    storage: {
        getBuckets: jest.fn(() => ({ buckets: [] })),
    },
    organizations: {
        getProject: jest.fn(() => ({ projectId: 'test-project' })),
    },
    projects: {
        getService: jest.fn(() => ({ state: 'ENABLED' })),
    },
}));

// Mock external libraries
jest.mock('p-queue', () => {
    return jest.fn(() => ({
        add: jest.fn(),
        addAll: jest.fn(),
        clear: jest.fn(),
        pause: jest.fn(),
        start: jest.fn(),
        on: jest.fn(),
        size: 0,
        pending: 0,
    }));
});

jest.mock('cli-progress', () => ({
    SingleBar: jest.fn(() => ({
        start: jest.fn(),
        stop: jest.fn(),
        increment: jest.fn(),
        update: jest.fn(),
    })),
}));

jest.mock('chalk', () => ({
    default: {
        cyan: jest.fn((text: string) => text),
        green: jest.fn((text: string) => text),
        yellow: jest.fn((text: string) => text),
        red: jest.fn((text: string) => text),
        blue: jest.fn((text: string) => text),
        gray: jest.fn((text: string) => text),
        bold: jest.fn((text: string) => text),
        magenta: jest.fn((text: string) => text),
    },
    cyan: jest.fn((text: string) => text),
    green: jest.fn((text: string) => text),
    yellow: jest.fn((text: string) => text),
    red: jest.fn((text: string) => text),
    blue: jest.fn((text: string) => text),
    gray: jest.fn((text: string) => text),
    bold: jest.fn((text: string) => text),
    magenta: jest.fn((text: string) => text),
}));

jest.mock('ora', () => {
    return jest.fn(() => ({
        start: jest.fn().mockReturnThis(),
        stop: jest.fn().mockReturnThis(),
        succeed: jest.fn().mockReturnThis(),
        fail: jest.fn().mockReturnThis(),
        info: jest.fn().mockReturnThis(),
        warn: jest.fn().mockReturnThis(),
        text: '',
    }));
});

jest.mock('winston', () => ({
    createLogger: jest.fn(() => ({
        info: jest.fn(),
        debug: jest.fn(),
        warn: jest.fn(),
        error: jest.fn(),
        child: jest.fn().mockReturnThis(),
    })),
    format: {
        combine: jest.fn(),
        timestamp: jest.fn(),
        printf: jest.fn(),
        colorize: jest.fn(),
        json: jest.fn(),
    },
    transports: {
        Console: jest.fn(),
        File: jest.fn(),
    },
}));

// Global type declarations for test utilities
declare global {
    var flushPromises: () => Promise<void>;
}

// Export for use in tests
export {};