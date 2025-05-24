# Orchestra Main

A modern, cloud-native Python application for rapid solo development and deployment on Google Cloud Run. Designed for simplicity, security, and developer productivity.

---

---
### 🛠️ Migration Note (May 2025)
All legacy admin UI code (Flask backend and HTML/Alpine frontend in `apps/admin/`) has been removed. The unified, modern admin interface is now implemented exclusively in [`admin-interface/`](admin-interface/README.md:1) using React and TypeScript. All administrative workflows, dashboards, and agent management are consolidated in this interface. See `admin-interface/README.md` for details.
---
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

- **CI/CD (Recommended):**
  - Pushing to the `main` branch triggers the GitHub Actions workflow (`.github/workflows/main.yml`).
  - The workflow:
    1. Runs tests and linting.
    2. Submits a build to Google Cloud Build using `cloudbuild.yaml`.
    3. Builds and pushes a Docker image (see `Dockerfile`).
    4. Deploys the image to Cloud Run (`orchestra-main-service`) in `us-central1`.
    5. Injects secrets from GCP Secret Manager as environment variables.

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
