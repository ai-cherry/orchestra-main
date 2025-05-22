# Project Blueprint & Workflow Guide

## Overview

This document outlines the architecture, workflows, and best-practices for the **orchestra-main** project.  It is tailored for a *solo developer* ( `scoobyjava@cherry-ai.me` ) who prioritises performance, stability, and ease-of-use.

---

### 1. Core Infrastructure Components (GCP)

| Area | Service | Notes |
|------|---------|-------|
| **Dev Compute** | **Paperspace Core VM** | Primary SSH target used by Cursor.  Choose CPU vs GPU flavour as needed. |
| **Secrets Vault** | **Secret Manager** | Single source of truth for SA keys, OpenAI/Anthropic keys, etc. |
| **Image Registry** | **Artifact Registry** | e.g. `us-central1-docker.pkg.dev/cherry-ai-project/orchestra-images`. |
| **Build Service** | **Cloud Build** | Runs `cloudbuild.yaml`; builds & pushes Docker images. |
| **Runtime** | **Cloud Run** | Service ≈ `ai-agent-service`, region `us-central1`, unauthenticated allowed (dev). |
| **IAM SAs** | `platform-admin@…` (dev/admin)  <br> `cicd-sa@…` (CI/CD via WIF) | Grant least-priv access for respectively VM work and GitHub Actions. |

---

### 2. Daily Development Workflow

```text
1. Boot / SSH → Paperspace VM
2. Cursor ➜ Remote-SSH to VM
3. $ cd ~/orchestra-main && source venv/bin/activate
   ( ~/.gcp_env_setup.sh already exported GCP + API keys )
4. Code / test :  python app.py
5. git add/commit; git push origin main
```

---

### 3. CI/CD Pipeline

1. **Trigger** – Push to `main`.
2. **Auth** – GitHub Action ⇢ WIF ⇢ `cicd-sa@…`.
3. **Build** – Cloud Build builds Docker image per `Dockerfile`; pushes to Artifact Registry.
4. **Deploy** – Cloud Build (or second step) updates Cloud Run service to new image.
5. **Secrets in prod** – Cloud Run mounts secrets from Secret Manager as env-vars.

---

### 4. Key Repository Files

| Path | Purpose |
|------|---------|
| `requirements.txt` | Python deps for local + prod.
| `app.py` | Main Flask / FastAPI app.
| `Dockerfile` | Minimal production container.
| `cloudbuild.yaml` | Build + deploy steps.
| `.github/workflows/main.yml` | GitHub Actions pipeline.
| `.gitignore` | Keep repo clean.
| _(optional)_ `.cursor/rules/` | Prompt rules for Cursor AI assistant.

---

### 5. Secrets Handling

* **Dev VM** – `~/.gcp_env_setup.sh` fetches SA key + API keys from Secret Manager ⇒ exports env-vars.
* **CI/CD** – WIF impersonates `cicd-sa@…`; never stores long-lived keys.
* **Prod (Cloud Run)** – Service definition references Secret Manager secrets which appear as env-vars.

---

### 6. Future IaC with Pulumi (Python)

Pulumi can codify Cloud Run, Artifact Registry, Secret Manager, and IAM bindings.  A future `infrastructure/` directory could hold Pulumi stacks; run `pulumi up` locally (VM) or in CI.

---

End of document. 