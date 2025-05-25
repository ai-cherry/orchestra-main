# Orchestra Main

A modern, cloud-native Python application for rapid solo development and deployment on Google Cloud Run. Designed for simplicity, security, and developer productivity.

# ⚡ Simplicity First

This project prioritizes performance, stability, and maintainability over security and compliance. No unnecessary security scans, policies, or complex patterns are included. All automation and CI/CD is designed to be fast, simple, and developer-friendly.

---

---

### 🛠️ Migration Note (May 2025)

## All legacy admin UI code (Flask backend and HTML/Alpine frontend in `apps/admin/`) has been removed. The unified, modern admin interface is now implemented exclusively in [`admin-interface/`](admin-interface/README.md:1) using React and TypeScript. All administrative workflows, dashboards, and agent management are consolidated in this interface. See `admin-interface/README.md` for details.

## 🚀 Development Setup

1. **Connect to Paperspace VM using Cursor (SSH):**

   - Open Cursor and connect to your Paperspace VM via SSH for a seamless, cloud-based development experience.

2. **Activate the Python virtual environment (venv):**

   - If you do not see a `venv/` directory in the project root, run:
     ```bash
     ./activate_venv.sh
     ```
   - This script will create and activate the venv, and install all dependencies.
   - If the venv already exists, you can activate it directly:
     ```bash
     source venv/bin/activate
     ```
   - **Always ensure you are working inside the venv.**

3. **Verify your environment:**

   - To confirm you are inside the venv, run:
     ```bash
     command -v python
     command -v pip
     ```
   - Both commands should output a path inside `./venv/bin/`.

4. **GCP Auth & API Keys:**

   - The `~/.gcp_env_setup.sh` script runs automatically on login, handling Google Cloud authentication and loading all required API keys from GCP Secret Manager into your environment.

5. **Run the application locally for testing:**

   ```bash
   python app.py
   # or, for production-like testing:
   gunicorn --bind 0.0.0.0:8080 app:app
   ```

   - The app will listen on the port specified by the `PORT` environment variable (default: 8080).

6. **Run tests (optional):**

   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt

   # Run all tests
   pytest

   # Run tests with verbose output
   pytest -v
   ```

---

## 🚑 Troubleshooting

- **If you see errors with `which python` or `which pip`:**
  - Use `command -v python` and `command -v pip` instead.
  - Some shells (especially in Cursor or minimal environments) may not support `which`.
- **If you are not in the venv:**
  - Run `./activate_venv.sh` to create and activate it.
  - If you see a system Python path, you are not in the venv.
- **If dependencies are missing:**
  - Ensure you have run `./activate_venv.sh` at least once.

---

## 🚢 Deployment

### Admin UI (React) Deployment

The Admin UI is deployed as a static website to Google Cloud Storage and served via HTTPS Load Balancer with managed SSL and optional Cloud DNS. This is fully automated:

**CI/CD:**
- Pushing to `main` or changes in `admin-ui/` triggers `.github/workflows/admin-ui.yml`.
- The workflow builds the React app, updates the Pulumi stack (infra/admin_ui_site), and syncs the built assets to the GCS bucket.
- The site is served at https://cherry-ai.me/ (or your configured domain).

**Manual one-liner deploy:**
```bash
python scripts/deploy_admin_ui.py --stack dev --domain cherry-ai.me
```

**Requirements:** Python 3.11+ everywhere (venv, CI, Pulumi, app code).

See `infra/admin_ui_site/` and `.github/workflows/admin-ui.yml` for details.

- **CI/CD (Recommended):**

  - Pushing to the `main` branch triggers the GitHub Actions workflow (`.github/workflows/main.yml`).
  - The workflow:
    1. Authenticates with GCP using Workload Identity Federation.
    2. Installs dependencies (including testing tools).
    3. Runs tests with pytest (if tests directory exists).
    4. Submits a build to Google Cloud Build using `cloudbuild.yaml`.
    5. Builds and pushes a Docker image (see `Dockerfile`).
    6. Deploys the image to Cloud Run (`ai-orchestra-minimal`) in `us-central1`.
    7. Injects secrets from GCP Secret Manager as environment variables.

- **Manual Deployment (Option A):**

  - From your Paperspace VM, you can deploy directly:
    ```bash
    gcloud run deploy --source . --region us-central1 --platform managed --allow-unauthenticated
    ```
  - This builds and deploys the app to Cloud Run using your current source code.

- **About `cloudbuild.yaml` and `Dockerfile`:**
  - `cloudbuild.yaml` defines the CI/CD pipeline: build, test, Dockerize, push, and deploy.
  - `Dockerfile` creates a minimal, production-ready container using Gunicorn to serve your Flask app.

---

## 🔐 Secrets Management

- **All API keys and sensitive credentials are stored in GCP Secret Manager.**
- The `~/.gcp_env_setup.sh` script on the VM loads these secrets into your environment automatically.
- Cloud Run services access secrets securely via IAM permissions and the `--set-secrets` flag in the service definition.
- **Never commit secrets to the repository.**

---

## 🧑‍💻 Solo Developer Experience

- No complex local Docker or Compose setup required.
- All infrastructure-as-code (Terraform, Pulumi) is archived in `infra_legacy/` for reference.
- For detailed architecture & workflow see **docs/PROJECT_BLUEPRINT.md**.

Any legacy Terraform snippets have been removed to keep the repo clean; future IaC will be added with Pulumi if required.

---

For any issues or questions, check the comments in `cloudbuild.yaml`, `Dockerfile`, and `.github/workflows/main.yml` for further guidance.

# Orchestra AI

## Quickstart

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd orchestra-main
   ```

2. **Set up your Python environment (Python 3.11+):**

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   ```

3. **Install dependencies:**
   - For main app:
     ```bash
     pip install -r requirements.txt
     ```
   - For development (tests, lint, docs):
     ```bash
     pip install -r requirements-dev.txt
     ```
   - For web scraping agent team:
     ```bash
     pip install -r requirements-webscraping.txt
     ```
   - For production containers:
     ```bash
     pip install -r requirements-app.txt
     ```

## Requirements Structure

- `requirements/base.txt`: Core dependencies for all modules (FastAPI, GCP, AI, DB, etc.)
- `requirements/development.txt`: Dev/test/lint tools (pytest, black, mypy, etc.)
- `requirements/production.txt`: Production-only extras (gunicorn, asyncpg, etc.)
- `requirements/webscraping.txt`: Web scraping agent dependencies (playwright, scrapy, etc.)
- `requirements.txt`: Main app (includes `base.txt`)
- `requirements-dev.txt`: Dev environment (includes `development.txt`)
- `requirements-app.txt`: Production containers (includes `production.txt`)
- `requirements-webscraping.txt`: Web scraping agent (includes `webscraping.txt`)

## No Poetry or pipenv

This project uses **pip and requirements files only** for dependency management. No Poetry, pipenv, or lockfiles are required. All environments inherit from a single, authoritative `base.txt` for consistency.

## Running the App
