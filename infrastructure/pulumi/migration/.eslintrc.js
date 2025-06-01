/**
 * ESLint configuration for Pulumi Migration Framework
 * Enforces code quality and consistency standards
 */

module.exports = {
    root: true,
    parser: '@typescript-eslint/parser',
    parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.json',
        tsconfigRootDir: __dirname,
    },
    plugins: [
        '@typescript-eslint',
        'prettier',
    ],
    extends: [
        'eslint:recommended',
        'plugin:@typescript-eslint/recommended',
        'plugin:@typescript-eslint/recommended-requiring-type-checking',
        'prettier',
    ],
    env: {
        node: true,
        es2022: true,
        jest: true,
    },
    rules: {
        // TypeScript specific rules
        '@typescript-eslint/explicit-function-return-type': ['error', {
            allowExpressions: true,
            allowTypedFunctionExpressions: true,
            allowHigherOrderFunctions: true,
            allowDirectConstAssertionInArrowFunctions: true,
        }],
        '@typescript-eslint/no-explicit-any': 'error',
        '@typescript-eslint/no-unused-vars': ['error', {
            argsIgnorePattern: '^_',
            varsIgnorePattern: '^_',
        }],
        '@typescript-eslint/no-non-null-assertion': 'error',
        '@typescript-eslint/strict-boolean-expressions': ['error', {
            allowString: false,
            allowNumber: false,
            allowNullableObject: false,
        }],
        '@typescript-eslint/no-floating-promises': 'error',
        '@typescript-eslint/no-misused-promises': 'error',
        '@typescript-eslint/await-thenable': 'error',
        '@typescript-eslint/no-unnecessary-type-assertion': 'error',
        '@typescript-eslint/prefer-nullish-coalescing': 'error',
        '@typescript-eslint/prefer-optional-chain': 'error',
        '@typescript-eslint/prefer-string-starts-ends-with': 'error',
        '@typescript-eslint/prefer-includes': 'error',
        '@typescript-eslint/no-unnecessary-condition': 'error',
        
        // General JavaScript rules
        'no-console': ['warn', { allow: ['warn', 'error'] }],
        'no-debugger': 'error',
        'no-alert': 'error',
        'prefer-const': 'error',
        'no-var': 'error',
        'eqeqeq': ['error', 'always'],
        'curly': ['error', 'all'],
        'brace-style': ['error', '1tbs'],
        'no-throw-literal': 'error',
        'no-return-await': 'error',
        'require-await': 'error',
        'no-async-promise-executor': 'error',
        'prefer-promise-reject-errors': 'error',
        
        // Code organization
        'max-lines': ['warn', {
            max: 500,
            skipBlankLines: true,
            skipComments: true,
        }],
        'max-lines-per-function': ['warn', {
            max: 100,
            skipBlankLines: true,
            skipComments: true,
        }],
        'complexity': ['warn', 15],
        'max-depth': ['warn', 4],
        'max-nested-callbacks': ['warn', 3],
        
        // Prettier integration
        'prettier/prettier': 'error',
    },
    overrides: [
        {
            // Test files
            files: ['**/*.test.ts', '**/*.spec.ts', '**/tests/**/*.ts'],
            rules: {
                '@typescript-eslint/no-explicit-any': 'off',
                'max-lines': 'off',
                'max-lines-per-function': 'off',
            },
        },
        {
            // Configuration files
            files: ['*.js', '*.config.js'],
            env: {
                node: true,
            },
            rules: {
                '@typescript-eslint/no-var-requires': 'off',
            },
        },
    ],
    ignorePatterns: [
        'dist/',
        'coverage/',
        'node_modules/',
        '*.d.ts',
        '.eslintrc.js',
        'jest.config.js',
    ],
};