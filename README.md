# Orchestra Main

A modern, cloud-native Python application for rapid solo development and deployment on Google Cloud Run. Designed for simplicity, security, and developer productivity.

---

## 🚀 Development Setup

1. **Connect to Paperspace VM using Cursor (SSH):**
   - Open Cursor and connect to your Paperspace VM via SSH for a seamless, cloud-based development experience.

2. **Activate the Python virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **GCP Auth & API Keys:**
   - The `~/.gcp_env_setup.sh` script runs automatically on login, handling Google Cloud authentication and loading all required API keys from GCP Secret Manager into your environment.

4. **Run the application locally for testing:**
   ```bash
   python app.py
   # or, for production-like testing:
   gunicorn --bind 0.0.0.0:8080 app:app
   ```
   - The app will listen on the port specified by the `PORT` environment variable (default: 8080).

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
- Focus on writing code, testing, and pushing to deploy!

---

For any issues or questions, check the comments in `cloudbuild.yaml`, `Dockerfile`, and `.github/workflows/main.yml` for further guidance.
