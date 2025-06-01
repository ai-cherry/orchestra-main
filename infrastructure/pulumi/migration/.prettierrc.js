/**
 * Prettier configuration for Pulumi Migration Framework
 * Ensures consistent code formatting across the project
 */

module.exports = {
    // Line length
    printWidth: 100,
    
    // Indentation
    tabWidth: 4,
    useTabs: false,
    
    // Semicolons
    semi: true,
    
    // Quotes
    singleQuote: true,
    quoteProps: 'as-needed',
    
    // Trailing commas
    trailingComma: 'es5',
    
    // Brackets
    bracketSpacing: true,
    bracketSameLine: false,
    
    // Arrow functions
    arrowParens: 'avoid',
    
    // Line endings
    endOfLine: 'lf',
    
    // Markdown
    proseWrap: 'preserve',
    
    // HTML whitespace sensitivity
    htmlWhitespaceSensitivity: 'css',
    
    // Vue files
    vueIndentScriptAndStyle: false,
    
    // Embedded language formatting
    embeddedLanguageFormatting: 'auto',
    
    // Overrides for specific file types
    overrides: [
        {
            files: '*.json',
            options: {
                tabWidth: 2,
            },
        },
        {
            files: '*.yml',
            options: {
                tabWidth: 2,
            },
        },
        {
            files: '*.md',
            options: {
                proseWrap: 'always',
            },
        },
        {
            files: ['*.ts', '*.tsx'],
            options: {
                parser: 'typescript',
            },
        },
    ],
};