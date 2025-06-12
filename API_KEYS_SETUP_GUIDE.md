# 🔑 API Keys Setup Guide for Orchestra AI (Unified Secrets Hub)

## Centralized Secrets Management

All API keys and secrets are now managed via `core/secrets_manager.py`.
- **One source of truth** for all workflows (Cursor AI, Cherry, Sophia, Karen, backend, infra).
- **Loads from**: environment variables, `.env` file, or (optionally) encrypted file.
- **Easy to use** in Python, Node.js, and shell scripts.

---

## Usage Examples

### Python (All Personas, Cursor AI, Backend)
```python
from core.secrets_manager import secrets
openai_key = secrets.get_secret("OPENAI_API_KEY")
notion_token = secrets.get_secret("NOTION_API_TOKEN")
```

### Node.js (via dotenv or shell)
```js
// Use dotenv to load .env, or call secrets_manager.py via CLI
const openaiKey = process.env.OPENAI_API_KEY; // after loading .env
// Or, from shell:
// python3 core/secrets_manager.py get OPENAI_API_KEY
```

### CLI (Validation, Rotation, Debug)
```bash
# Get a secret
python3 core/secrets_manager.py get OPENAI_API_KEY

# Validate required secrets
python3 core/secrets_manager.py --validate OPENAI_API_KEY NOTION_API_TOKEN

# Rotate (update) a secret
python3 core/secrets_manager.py --rotate OPENAI_API_KEY sk-new-key-here

# Dump all loaded secrets (debug only)
python3 core/secrets_manager.py --dump
```

---

## Best Practices for Long-Term Secret Management

- **Never hardcode secrets** in code or config files.
- **Use environment variables** for CI/CD and production, `.env` for local/dev.
- **Centralize secret access** through `core/secrets_manager.py`.
- **Automate validation** of required secrets at startup and in CI.
- **Support secret rotation** and make it easy to update keys everywhere.
- **Audit and log** all secret access and changes (future: add logging).
- **Encrypt secrets at rest** if using a file-based store (future: add encryption).
- **Plan for cloud secret manager integration** (AWS, GCP, Azure) for future scale.

---

## Required API Keys

- **NOTION_API_TOKEN**: Notion integration
- **OPENAI_API_KEY**: LLM access
- **ANTHROPIC_API_KEY**: LLM access
- **VERCEL_TOKEN**: Vercel deployments
- **LAMBDA_LABS_API_KEY**: Lambda Labs infra
- **OPENROUTER_API_KEY**: (Optional) OpenRouter LLM
- **PERPLEXITY_API_KEY**: (Optional) Perplexity LLM

---

## Onboarding Checklist

1. Copy `.env.example` to `.env` and add your API keys.
2. Use `core/secrets_manager.py` for all secret access.
3. Validate with `python3 core/secrets_manager.py --validate ...`.
4. Rotate keys with `python3 core/secrets_manager.py --rotate ...`.
5. (Optional) Integrate with cloud secret manager for production.

---

**Result:**
- All workflows (Cursor AI, Cherry, Sophia, Karen, backend, infra) use a single, stable, and secure secrets hub.
- Easy to maintain, rotate, and audit.
- Ready for future scale and cloud integration.

# API Key Setup Guide (Pulumi Cloud)

All secrets and API keys are managed in Pulumi Cloud config. Never use .env for production.

## Add a Secret
```bash
pulumi config set --secret API_KEY your-key-here
```

## Rotate a Secret
```bash
pulumi config set --secret API_KEY new-key-here
```

## Validate Secrets (CI/CD)
Add a script to check for all required secrets before deploy.

## Access in Code
```python
import pulumi
config = pulumi.Config()
api_key = config.require_secret("API_KEY")
```
