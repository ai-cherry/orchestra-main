# Final Secret Management Guide - Cherry AI

## 🎯 Overview

Cherry AI now uses **Pulumi as the single source of truth** for all secrets. This guide documents the complete setup after migrating from GitHub Secrets and Google
## 🏗️ Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   GitHub Secrets    │     │  Google Secret Mgr  │     │   Local Config      │
│    (deprecated)     │────▶│    (deprecated)     │────▶│ managed-services.env│
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────┐
                            │   Pulumi Config     │ ← Single Source of Truth
                            │  (encrypted state)  │
                            └─────────────────────┘
                                      │
                                      ▼
                            ┌─────────────────────┐
                            │     .env file       │ ← Generated for local dev
                            │  (auto-generated)   │
                            └─────────────────────┘
```

## 📦 What Was Migrated

### From Google - All LLM API keys (OpenAI, Anthropic, Perplexity, etc.)
- Service credentials (MongoDB, Weaviate, DragonflyDB)
- Integration tokens (Slack, HuggingFace, Docker, etc.)
- Platform keys (Pulumi, GitHub PATs)

### From Local Config:
- MongoDB Atlas connection string
- DragonflyDB cloud URI
- Weaviate endpoint and API key

### Current Status in Pulumi:
✅ **Core Services**
- `mongo_uri` - MongoDB Atlas connection
- `dragonfly_uri` - DragonflyDB cloud cache
- `weaviate_url` & `weaviate_api_key` - Vector search

✅ **LLM Services**
- `openai_api_key` - OpenAI GPT models
- `anthropic_api_key` - Claude models
- `openrouter_api_key` - OpenRouter gateway
- `portkey_api_key` - Portkey LLM gateway
- `perplexity_api_key` - Perplexity AI

✅ **Deployment**
- `Lambda:api_key` - Lambda API
- `pulumi_access_token` - Pulumi cloud

## 🔧 Daily Usage

### For Developers

1. **Initial Setup** (one time):
```bash
# Set Pulumi passphrase
export PULUMI_CONFIG_PASSPHRASE="cherry_ai-dev-123"

# Generate .env from Pulumi
python scripts/generate_env_from_pulumi.py

# Source environment
source .env
```

2. **Start Development**:
```bash
# Everything is ready!
./start_cherry_ai.sh
```

### Adding New Secrets

```bash
# Navigate to infra directory
cd infra

# Add a new secret
pulumi config set --secret my_new_secret "secret-value"

# Go back and regenerate .env
cd ..
python scripts/generate_env_from_pulumi.py
```

### Updating Existing Secrets

```bash
cd infra
pulumi config set --secret openai_api_key "new-api-key"
cd ..
python scripts/generate_env_from_pulumi.py
source .env
```

## 🚀 Migration Tools

### 1. **Comprehensive Migration Script**
`scripts/migrate_all_secrets_to_pulumi.py`
- Collects secrets from GitHub, - Automatically stores them in Pulumi
- Generates migration report

### 2. **Environment Generator**
`scripts/generate_env_from_pulumi.py`
- Creates `.env` from Pulumi secrets
- Also generates `.env.example` with placeholders
- Automatically adds to `.gitignore`

### 3. **Setup Script**
`scripts/setup_all_secrets.sh`
- Loads secrets from `config/managed-services.env`
- Stores them in Pulumi
- Provides clear next steps

## 🔒 Security Measures

### Git Protection
- `.env` is gitignored
- `config/managed-services.env` is gitignored
- Git history cleanup script available: `scripts/clean_git_history.sh`

### Access Control
- Pulumi passphrase: `cherry_ai-dev-123` (for dev)
- Pulumi cloud RBAC for team access
- Service-specific API key permissions

### Best Practices
1. Never commit actual secrets
2. Rotate keys regularly
3. Use Pulumi for all environments
4. Generate `.env` files, don't edit manually

## 🚨 Important Notes

### Git History Issue
The repository history contains exposed secrets in commit `e18ece0`. To fix:

1. Run the cleanup script:
```bash
./scripts/clean_git_history.sh
```

2. Rotate these exposed keys:
- OpenAI API key
- Anthropic API key
- Lambda API key

3. Update in Pulumi:
```bash
cd infra
pulumi config set --secret openai_api_key "<new-key>"
pulumi config set --secret anthropic_api_key "<new-key>"
pulumi config set --secret Lambda:api_key "<new-token>"
```

### CI/CD Setup
For GitHub Actions, add these repository secrets:
- `PULUMI_ACCESS_TOKEN`
- `PULUMI_CONFIG_PASSPHRASE`

Then in workflows:
```yaml
- name: Setup Pulumi
  env:
    PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
    PULUMI_CONFIG_PASSPHRASE: ${{ secrets.PULUMI_CONFIG_PASSPHRASE }}
  run: |
    cd infra
    pulumi stack select ${{ env.ENVIRONMENT }}
```

## 📋 Quick Reference

| Action | Command |
|--------|---------|
| View all secrets | `cd infra && pulumi config --show-secrets` |
| Add new secret | `pulumi config set --secret <key> <value>` |
| Update secret | `pulumi config set --secret <key> <new-value>` |
| Generate .env | `python scripts/generate_env_from_pulumi.py` |
| Migrate all secrets | `python scripts/migrate_all_secrets_to_pulumi.py` |

## ✅ Verification Checklist

- [ ] All secrets migrated to Pulumi
- [ ] `.env` file generated and sourced
- [ ] Application starts successfully
- [ ] Git history cleaned (if needed)
- [ ] Exposed keys rotated (if applicable)
- [ ] Team notified of new process

## 🆘 Troubleshooting

### "Wrong passphrase" error
```bash
export PULUMI_CONFIG_PASSPHRASE="cherry_ai-dev-123"
```

### Missing secret in .env
```bash
# Check if it's in Pulumi
cd infra && pulumi config --show-secrets | grep <secret-name>

# If missing, add it
pulumi config set --secret <key> <value>

# Regenerate .env
cd .. && python scripts/generate_env_from_pulumi.py
```

### Can't find a secret's value
Check these locations in order:
1. Current environment: `env | grep <SECRET_NAME>`
2. Pulumi config: `cd infra && pulumi config --show-secrets`
3. Local config: `cat config/managed-services.env`
4. Ask team for the value

## 🎉 Success!

Your secrets are now:
- ✅ Centralized in Pulumi
- ✅ Encrypted at rest
- ✅ Version controlled (config, not values)
- ✅ Easy to rotate
- ✅ Simple to use locally

No more juggling between GitHub Secrets,
