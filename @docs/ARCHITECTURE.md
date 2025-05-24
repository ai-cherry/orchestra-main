# AI-Agent Solo-Dev Project (high-level)

• Cursor IDE (Max Mode) for coding + AI help
• Coder workspace on GCP A100 GPU for heavy dev / debugging
• Repo layout: agent/ dashboard/ infra/ (.github/workflows/)
• Pulumi (Python) provisions:
– Artifact Registry
– Cloud Run GPU (NVIDIA L4) for agent (Python FastAPI)
– Cloud Run (standard) for dashboard (Next.js)
– Secret Manager (OPENAI_API_KEY, PORTKEY_API_KEY, etc.)

Optimization & stability > cost & perfect security. One developer (me).

### Memory Architecture (v2)

Short-Term ➜ Redis (async, LRU eviction)
Mid-Term ➜ Firestore V2 (async, Resilient Adapter, connection pool)
Long-Term ➜ Vertex AI Vector Search (optional, fallback to backend)
All components are instantiated via `MemoryManagerFactory` with capability detection; Firestore V1 path is deprecated.

CI/CD = GitHub Actions ▶︎ build Docker ▶︎ push ▶︎ `pulumi up` (via WIF)
Secrets live **only** in Secret Manager; Cloud Run mounts them as env vars.

---

## Detailed Plan Expansion

### 1. Exact Repo Tree (Files & Folders)

- `.github/`
  - `workflows/`
    - `ci_cd.yml` (Main CI/CD pipeline)
- `agent/`
  - `app/`
    - `__init__.py`
    - `main.py` (FastAPI app definition)
    - `routers/` (API route handlers)
      - `__init__.py`
      - `chat.py` (example router)
    - `core/`
      - `__init__.py`
      - `config.py` (Settings, e.g., loaded from env vars)
    - `services/` (Business logic, e.g., AI integrations)
      - `__init__.py`
  - `Dockerfile` (For the agent service)
  - `requirements.txt` (Python dependencies)
  - `tests/` (Unit/integration tests for the agent)
- `dashboard/`
  - `pages/` (Next.js pages)
  - `components/` (React components)
  - `public/` (Static assets)
  - `styles/`
  - `lib/` (Helper functions, API clients)
  - `Dockerfile` (For the dashboard service)
  - `package.json`
  - `next.config.js`
  - `tsconfig.json` (if using TypeScript)
  - `tests/` (Unit/integration tests for the dashboard)
- `infra/`
  - `__main__.py` (Pulumi main program)
  - `Pulumi.yaml` (Project definition)
  - `Pulumi.dev.yaml` (Dev stack configuration)
  - `Pulumi.prod.yaml` (Prod stack configuration)
  - `requirements.txt` (Python dependencies for Pulumi)
  - `config.py` (Optional: shared configuration logic for Pulumi programs)
  - `modules/` (Optional: reusable Pulumi components, e.g., `cloud_run_service.py`)
- `.gitignore`
- `README.md`
- `@docs/`
  - `ARCHITECTURE.md` (This document)

### 2. Pulumi Stacks

- **`dev` stack:**
  - Purpose: For development, testing, and staging new features.
  - Resources: Might use lower-cost Cloud Run configurations (e.g., fewer vCPUs, smaller L4 GPU instance or even CPU for some tests if possible, min-instances set to 0).
  - Deployment: Triggered on pushes to a `develop` branch or feature branches.
- **`prod` stack:**
  - Purpose: Live production environment.
  - Resources: Scaled appropriately for production load, using the specified L4 GPU for the agent.
  - Deployment: Triggered on merges/pushes to the `main` branch, possibly with manual approval.

### 3. Secrets List (to be managed in GCP Secret Manager)

- `OPENAI_API_KEY`: (As mentioned) API key for OpenAI services.
- `PORTKEY_API_KEY`: (As mentioned) API key for Portkey services.
- `GCP_PROJECT_ID`: Google Cloud Project ID where resources are deployed.
- `GCP_REGION`: Default Google Cloud Region for deployments.
- `AGENT_IMAGE_URL`: URL of the agent's Docker image in Artifact Registry (Pulumi might set this dynamically during deployment based on build outputs, but good to acknowledge).
- `DASHBOARD_IMAGE_URL`: URL of the dashboard's Docker image in Artifact Registry.
- `DATABASE_URL` (Optional, if a database is needed): Connection string for a database if your services become stateful.
- Any other third-party service API keys or sensitive configuration values.

### 4. CI Workflow Outline (`.github/workflows/ci_cd.yml`)

- **Triggers:**

  - Push to `main` branch (for `prod` deployment).
  - Push to `develop` branch (for `dev` deployment).
  - Pull request against `main` or `develop` (for running tests and pre-checks).

- **Common Setup Steps (for relevant jobs):**

  - Checkout code: `actions/checkout@v3`
  - Set up Google Cloud CLI & Auth: `google-github-actions/auth@v1` (using Workload Identity Federation).
  - Set up Python: `actions/setup-python@v4`
  - Set up Node.js (for dashboard): `actions/setup-node@v3`
  - Set up Docker Buildx: `docker/setup-buildx-action@v2`
  - Login to Artifact Registry: `docker/login-action@v2` (with `gcloud auth print-access-token`)

- **Jobs:**

  - **`lint_and_test` (Run on PRs and pushes to `dev`/`main`):**

    - Steps:
      - Run linters (e.g., Black, Flake8 for Python; ESLint, Prettier for Next.js).
      - Run unit/integration tests for `agent`.
      - Run unit/integration tests for `dashboard`.

  - **`build_and_push_agent` (Run after `lint_and_test` succeeds on `dev`/`main` pushes):**

    - Steps:
      - Build Docker image for `agent`.
      - Tag image (e.g., with Git SHA, branch name).
      - Push image to GCP Artifact Registry.
      - Output image URL for deploy job.

  - **`build_and_push_dashboard` (Run after `lint_and_test` succeeds on `dev`/`main` pushes):**

    - Steps:
      - Build Docker image for `dashboard`.
      - Tag image.
      - Push image to GCP Artifact Registry.
      - Output image URL for deploy job.

  - **`deploy_dev` (Run after build jobs succeed on `develop` branch push):**

    - Needs: `build_and_push_agent`, `build_and_push_dashboard`.
    - Environment: `development` (GitHub Environment with protection rules if needed).
    - Steps:
      - Set up Pulumi: `pulumi/actions@v4`.
      - `cd infra/`
      - `pulumi login`
      - `pulumi select dev`
      - `pulumi config set agentImage <agent_image_url_from_build_job>`
      - `pulumi config set dashboardImage <dashboard_image_url_from_build_job>`
      - `pulumi up --yes --skip-preview`

  - **`deploy_prod` (Run after build jobs succeed on `main` branch push, potentially with manual approval):**
    - Needs: `build_and_push_agent`, `build_and_push_dashboard`.
    - Environment: `production` (GitHub Environment with protection rules and required reviewers).
    - Steps:
      - Set up Pulumi.
      - `cd infra/`
      - `pulumi login`
      - `pulumi select prod`
      - `pulumi config set agentImage <agent_image_url_from_build_job>`
      - `pulumi config set dashboardImage <dashboard_image_url_from_build_job>`
      - `pulumi up --yes --skip-preview` (or just `pulumi preview` then manual `pulumi up` outside CI for more control initially).

### Missing Pieces / Areas for Further Detail

- **Detailed Dev vs. Prod Configuration:** How will resource settings (CPU, memory, scaling parameters, GPU types/counts if different for dev) be managed by Pulumi for each stack? (e.g., via `Pulumi.<stack>.yaml` or Python config logic).
- **Database Strategy:** If any service requires persistent storage beyond simple object storage, a database solution (e.g., Cloud SQL, Firestore) needs to be planned and provisioned by Pulumi.
- **Logging & Monitoring:** Beyond Portkey, consider GCP's Operations Suite (Cloud Logging, Cloud Monitoring) for application and infrastructure logs/metrics. How will these be configured/utilized?
- **DNS & Custom Domains:** How will custom domains be managed for the Cloud Run services? This typically involves DNS records and potentially SSL certificate management.
- **Workload Identity Federation (WIF) Setup:** The actual setup of WIF between GitHub Actions and GCP needs to be documented/scripted (likely part of initial infra setup, not per-CI run).
- **Pulumi Project Structure in `infra/`:** The organization within `infra/` (e.g., use of Pulumi components, how shared vs. stack-specific logic is handled) can be further detailed.
- **Agent/Dashboard Specific Environment Variables:** Beyond secrets, are there non-sensitive environment variables needed for the agent or dashboard (e.g., `API_BASE_URL` for the dashboard to call the agent)? How are these configured for Cloud Run (likely via Pulumi)?
- **Initial Pulumi Setup:** How the Pulumi project and stacks are initially created and configured with GCP backend.

### 5. AI-Assisted Code Review Process

After each major PR, use the following prompt with an AI assistant (like Cursor) to review changes:

```plaintext
You are my senior reviewer. Review the diff in this PR:
1. Highlight any architecture drift vs docs/ARCHITECTURE.md
2. Point out missing tests or error handling
3. Suggest performance improvements
Return a markdown checklist I can act on.
```
