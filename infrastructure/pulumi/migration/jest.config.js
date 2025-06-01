/**
 * Jest configuration for Pulumi Migration Framework
 * Optimized for TypeScript testing with proper module resolution
 */

module.exports = {
    // Use ts-jest preset for TypeScript support
    preset: 'ts-jest',
    
    // Test environment
    testEnvironment: 'node',
    
    // Root directory
    roots: ['<rootDir>/src', '<rootDir>/tests'],
    
    // Test file patterns
    testMatch: [
        '**/__tests__/**/*.+(ts|tsx|js)',
        '**/?(*.)+(spec|test).+(ts|tsx|js)'
    ],
    
    // Module file extensions
    moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
    
    // Transform configuration
    transform: {
        '^.+\\.(ts|tsx)$': 'ts-jest',
    },
    
    // Module name mapper for path aliases
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1',
        '^@types/(.*)$': '<rootDir>/src/types/$1',
        '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    },
    
    // Coverage configuration
    collectCoverageFrom: [
        'src/**/*.{ts,tsx}',
        '!src/**/*.d.ts',
        '!src/**/index.ts',
        '!src/**/*.test.{ts,tsx}',
        '!src/**/*.spec.{ts,tsx}',
    ],
    
    // Coverage thresholds
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80,
        },
    },
    
    // Coverage directory
    coverageDirectory: '<rootDir>/coverage',
    
    // Setup files
    setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
    
    // Globals
    globals: {
        'ts-jest': {
            tsconfig: {
                // Override tsconfig for tests
                esModuleInterop: true,
                allowSyntheticDefaultImports: true,
            },
        },
    },
    
    // Clear mocks between tests
    clearMocks: true,
    
    // Restore mocks between tests
    restoreMocks: true,
    
    // Timeout for tests
    testTimeout: 30000,
    
    // Verbose output
    verbose: true,
    
    // Max workers for parallel execution
    maxWorkers: '50%',
};