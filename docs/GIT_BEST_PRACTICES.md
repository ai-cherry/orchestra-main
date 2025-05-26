# Git Best Practices for AI Orchestra

## Overview

This guide outlines Git best practices for the AI Orchestra project, ensuring consistent, clean, and meaningful commit history.

## Commit Message Format

We follow the Conventional Commits specification with the format configured in `.gitmessage`:

```
<type>: <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code formatting (no functional changes)
- **refactor**: Code restructuring (no functional changes)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build, etc.)

### Examples

```bash
# Good commit messages
feat: add natural language query support for MongoDB
fix: resolve connection timeout in MCP servers
docs: update infrastructure guide with cost estimates
refactor: modularize Pulumi components for reusability
test: add integration tests for SuperAGI deployment

# Bad commit messages
update files
fix bug
WIP
changes
```

## Git Configuration

### Initial Setup

```bash
# Set user information
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Use the commit message template
git config --local commit.template .gitmessage

# Enable helpful aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --decorate"
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files (initial setup)
pre-commit run --all-files
```

## Workflow Best Practices

### 1. Feature Branch Workflow

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Work on your feature
# ... make changes ...

# Commit with meaningful messages
git add .
git commit  # This will open the template

# Push to remote
git push -u origin feature/your-feature-name
```

### 2. Keep Commits Atomic

Each commit should represent one logical change:

```bash
# Bad: Multiple unrelated changes in one commit
git add .
git commit -m "fix: update API and add tests and fix docs"

# Good: Separate commits for each change
git add api/
git commit -m "fix: resolve timeout in MongoDB connection"

git add tests/
git commit -m "test: add unit tests for MongoDB queries"

git add docs/
git commit -m "docs: update API documentation"
```

### 3. Interactive Rebase for Clean History

Before merging, clean up your commit history:

```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# In the editor, you can:
# - squash: combine commits
# - reword: change commit message
# - drop: remove commit
# - reorder: change commit order
```

### 4. Pull Request Guidelines

1. **Title**: Use the same format as commit messages
2. **Description**: Include:
   - What changed and why
   - How to test
   - Screenshots (if UI changes)
   - Related issues

Example PR description:
```markdown
## What
Add natural language query support for MongoDB through MCP integration

## Why
Users need an intuitive way to query data without writing MongoDB queries

## How to Test
1. Deploy the updated MCP server
2. Run: `python scripts/test_mcp_queries.py`
3. Try queries like "Show all active agents"

## Related Issues
Closes #123
```

## Environment-Specific Practices

### 1. Sensitive Data

Never commit sensitive data:

```bash
# Files that should NEVER be committed
.env.local          # Local environment variables
*.key               # Private keys
*-key.json          # Service account keys
secrets/            # Any secrets directory

# Use git-secrets to prevent accidental commits
brew install git-secrets  # or apt-get install git-secrets
git secrets --install
git secrets --register-aws  # Example for AWS
```

### 2. Large Files

Use Git LFS for large files:

```bash
# Track large model files
git lfs track "*.model"
git lfs track "*.weights"

# Add to .gitattributes
git add .gitattributes
git commit -m "chore: configure Git LFS for model files"
```

### 3. Python-Specific

```bash
# Always commit requirements changes
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update Python dependencies"

# For Pulumi infrastructure
cd infra
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update Pulumi dependencies"
```

## CI/CD Integration

Our GitHub Actions workflows enforce:

1. **Commit message format** validation
2. **Code formatting** with Black
3. **Linting** with pylint
4. **Type checking** with mypy
5. **Test coverage** requirements

### Fixing CI Failures

```bash
# Format code
black scripts/ tests/ infra/

# Fix linting issues
pylint scripts/ --fix

# Run tests locally
pytest tests/ -v

# Check types
mypy scripts/
```

## Common Scenarios

### 1. Amending the Last Commit

```bash
# Add forgotten files to last commit
git add forgotten_file.py
git commit --amend --no-edit

# Change last commit message
git commit --amend
```

### 2. Undoing Changes

```bash
# Undo last commit but keep changes
git reset --soft HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1

# Undo specific file changes
git checkout -- file.py
```

### 3. Stashing Work

```bash
# Save current work
git stash save "WIP: natural language queries"

# List stashes
git stash list

# Apply stash
git stash pop  # or git stash apply stash@{0}
```

## Branch Protection Rules

The `main` branch has these protections:

1. **Required reviews**: At least 1 approval
2. **Status checks**: All CI must pass
3. **Up-to-date**: Branch must be current with main
4. **No force push**: History is immutable

## Commit Signing (Optional but Recommended)

```bash
# Generate GPG key
gpg --gen-key

# List keys
gpg --list-secret-keys --keyid-format LONG

# Configure Git to use your key
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true

# Add public key to GitHub
gpg --armor --export YOUR_KEY_ID
# Copy output to GitHub Settings > SSH and GPG keys
```

## Quick Reference

```bash
# View commit template
cat .gitmessage

# Check current configuration
git config --list | grep -E "(commit|user|core)"

# View recent commits with graph
git lg -10

# Check pre-commit status
pre-commit run --all-files

# Validate commit message format
echo "feat: add new feature" | grep -E "^(feat|fix|docs|style|refactor|perf|test|chore):"
```

## Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Pro Git Book](https://git-scm.com/book/en/v2)
- [Project Contributing Guide](../CONTRIBUTING.md)
