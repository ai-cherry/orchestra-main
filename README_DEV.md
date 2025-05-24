# AI Orchestra Developer Onboarding & Workflow

## 1. Dev Environment Setup

- **Clone the repo** to your Paperspace VM.
- **Source the environment setup script:**
  ```bash
  source ~/.gcp_env_setup.sh
  ```
  This authenticates you to GCP, fetches all secrets, and exports required env vars.

## 2. GCP & GitHub Authentication

- **GCP:**
  - Auth is handled by `~/.gcp_env_setup.sh` (uses Secret Manager, no static key files).
- **GitHub:**
  - Use SSH keys (preferred) or `gh auth login` for HTTPS.
  - To check: `gh auth status`
  - To set up: `gh auth login --web` and `gh auth setup-git`

## 3. Secrets Management

- **All secrets are stored in GCP Secret Manager.**
- **Never commit secrets or key files.**
- **To fetch a secret manually:**
  ```bash
  gcloud secrets versions access latest --secret=SECRET_NAME --project=cherry-ai-project
  ```

## 4. Deploying

- **Push to main to deploy:**
  ```bash
  git add .
  git commit -m "Your message"
  git push origin main
  ```
- **GitHub Actions will handle CI/CD and deploy to GCP.**

## 5. Rotating Secrets

- **Update the secret in GCP Secret Manager.**
- **Re-run `source ~/.gcp_env_setup.sh` to refresh your environment.**

## 6. Avoid Committing Secrets

- **.gitignore** includes all key files and `*.json`.
- **Pre-commit hook** (see below) blocks secrets from being committed.

## 7. If a Secret is Committed

- **Immediately rotate the secret in GCP.**
- **Remove the file and purge from git history using BFG or filter-branch.**
- **Force-push and notify any collaborators to re-clone.**

---

# Pre-commit Hook to Block Secrets

Create `.git/hooks/pre-commit` with:

```bash
#!/bin/bash
if git diff --cached | grep -E 'PRIVATE KEY|BEGIN RSA|BEGIN EC|AIza|AIzaSy|gho_|ghp_|sk_live_|sk_test_|project-admin-key|secret-management-key'; then
  echo "[ERROR] Potential secret detected in staged changes. Commit aborted."
  exit 1
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

# Golden Path

- **Start a new shell:** `source ~/.gcp_env_setup.sh`
- **Code.**
- **Commit.**
- **Push.**
- **Let CI/CD deploy.**

No secrets in git. No manual key management. Just code and ship.
