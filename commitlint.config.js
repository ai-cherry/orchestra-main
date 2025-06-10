// Phase 1: Commit message linting configuration
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation only changes
        'style',    // Code style changes (formatting, etc)
        'refactor', // Code refactoring
        'perf',     // Performance improvements
        'test',     // Adding or updating tests
        'build',    // Build system or dependency updates
        'ci',       // CI/CD configuration changes
        'chore',    // Other changes that don't modify src or test files
        'revert',   // Reverts a previous commit
        'phase1',   // Phase 1 specific changes
      ],
    ],
    'subject-case': [2, 'never', ['upper-case', 'pascal-case']],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
}; 