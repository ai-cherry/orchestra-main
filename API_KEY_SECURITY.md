# API Key Security Guide for Cherry AI

## Overview
This guide ensures that sensitive API keys are never exposed in your codebase or GitHub repository.

## Security Rules

### 1. NEVER Commit Real API Keys
- Never commit actual API keys to Git
- Always use placeholder values in example files
- Use environment variables for real keys

### 2. Files That Should Contain API Keys
- `.env` (gitignored)
- `.env.local` (gitignored)
- Environment variables in your shell
- GitHub Secrets (for CI/CD)

### 3. Files That Should NOT Contain API Keys
- Any `.md` documentation files
- Example or template files
- Source code files
- Configuration files that will be committed

## Setting Up API Keys Securely

### For Local Development

1. **Use the setup script:**
   ```bash
   export ELEVENLABS_API_KEY=your_actual_key_here
   ./scripts/setup_api_keys.sh
   ```

2. **Or manually edit .env:**
   ```bash
   # Never commit this file!
   echo "ELEVENLABS_API_KEY=your_actual_key_here" >> .env
   ```

3. **Load environment variables:**
   ```bash
   source .env
   ```

### For Production/Deployment

1. **Use environment variables on your server:**
   ```bash
   # Add to server's environment (not in repo)
   export ELEVENLABS_API_KEY=your_actual_key_here
   ```

2. **Or use a secrets management service:**
   - AWS Secrets Manager
   - Google Secret Manager
   - Pulumi Vault
   - GitHub Secrets (for GitHub Actions)

## Checking for Exposed Keys

Before committing, always check:

```bash
# Search for potential API keys
grep -r "sk_" . --exclude-dir=.git --exclude-dir=venv --exclude-dir=node_modules --exclude=.env

# Check git status
git status

# Review changes before committing
git diff
```

## If You Accidentally Commit an API Key

1. **Immediately revoke the key** in your ElevenLabs dashboard
2. **Generate a new key**
3. **Remove from Git history:**
   ```bash
   # This rewrites history - use with caution
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force push to remote** (coordinate with team)
5. **Update all deployments** with the new key

## GitHub Secret Scanning

GitHub automatically scans for exposed secrets. If you receive an alert:
1. Revoke the exposed key immediately
2. Generate a new key
3. Update all systems using that key
4. Review how the exposure happened

## Best Practices

1. **Use different keys for different environments:**
   - Development key with limited quota
   - Production key with appropriate limits
   - Test key for CI/CD

2. **Set up key rotation:**
   - Rotate keys every 90 days
   - Document rotation procedure
   - Update all systems promptly

3. **Monitor usage:**
   - Check ElevenLabs dashboard regularly
   - Set up usage alerts
   - Monitor for unusual activity

4. **Limit key permissions:**
   - Use read-only keys where possible
   - Limit keys to specific APIs/features
   - Use IP restrictions if available

## Environment File Template

Your `.env` file should look like this (with real values):

```bash
# Production API Keys - NEVER COMMIT THIS FILE
ELEVENLABS_API_KEY=sk_[your_actual_key_here]
OPENAI_API_KEY=sk-[your_actual_key_here]
# ... other keys
```

Your `env.example` should look like this (with placeholders):

```bash
# Example environment file - Copy to .env and add real values
ELEVENLABS_API_KEY=your-elevenlabs-key-here
OPENAI_API_KEY=your-openai-key-here
# ... other keys
```

## Remember

Security is everyone's responsibility. When in doubt, ask for help rather than risk exposing sensitive credentials. 