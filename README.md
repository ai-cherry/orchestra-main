# Orchestra AI

## Project Structure (Authoritative)
- **Orchestrator:** `core/orchestrator/src/`
- **Admin UI:** `admin-ui/`
- **Utility Scripts:** `scripts/`
- **Infrastructure as Code:** `infra/`

## 🚀 Quick Start

1. **Clone the repo**
2. **Set your secrets as environment variables:**
   ```bash
   export OPENAI_API_KEY=...
   export WEAVIATE_API_KEY=...
   export MONGODB_CONNECTION_STRING=...
   export MONGODB_SERVICE_CLIENT_ID=...
   export MONGODB_SERVICE_CLIENT_SECRET=...
   export GRAFANA_ADMIN_PASSWORD=...
   export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"
   ```
3. **Run the setup script:**
   ```bash
   bash scripts/setup_local_env.sh
   ```
4. **Deploy:**
   ```bash
   bash scripts/deploy_orchestra.sh
   ```

## 🛡️ CI/CD
- All secrets are managed via GitHub Actions secrets and Pulumi.
- No manual steps required for deploys.
- The deploy workflow (`.github/workflows/deploy.yaml`) is fully automated. It uses secrets for all credentials and never prompts for input. To trigger a deploy, just push to `main`.

## Pulumi Secrets
- The Pulumi config passphrase is set automatically via:
  ```bash
  export PULUMI_CONFIG_PASSPHRASE="orchestra-dev-123"
  ```
- You never need to enter it manually.
- All secrets (API keys, DB credentials, etc.) are managed via Pulumi and GitHub Actions secrets. Never store secrets in code or scripts. To update a secret, set the environment variable and re-run `scripts/setup_local_env.sh`.

## Troubleshooting
- If Pulumi prompts for a passphrase, make sure `PULUMI_CONFIG_PASSPHRASE` is set in your environment.
- If a deploy fails, check that all required secrets are set as environment variables or GitHub secrets.
- If you see `[WARN] ... key not set` during deploy, set it with `pulumi config set --secret ...` as above.

## Maintenance
- Only one orchestrator, one admin UI, and one set of utility scripts are maintained.
- All legacy/archived code has been removed for clarity and maintainability.

---

**This project is now fully automated and streamlined for solo or team development.**

## Internals Documentation

Detailed docs live under [`/docs`](docs/):

* [`docs/memory_overview.md`](docs/memory_overview.md) – how the layered memory system works.
* [`AGENTS.md`](AGENTS.md) – how to configure and register new agents.

## 🧪 Testing

Run the **smoke test suite** (fast!) locally:

```bash
pytest -q tests/core/orchestrator
```

Add more tests under `tests/` – the CI will pick them up automatically.
