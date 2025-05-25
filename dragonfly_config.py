"""
DragonflyDB configuration loader for solo developer, GCP, and CI/CD.

- Prefers local hardcoded secrets (ignored by git) for dev speed.
- Falls back to environment variables (for GCP Secret Manager or GitHub Actions).
- Optionally fetches from GCP Secret Manager if running in GCP and env vars are missing.
- Never logs or prints secrets.
"""

import os

# 1. Try to import local secrets (ignored by git)
try:
    from dragonfly_secrets import (
        DRAGONFLY_CONNECTION_URI,
        DRAGONFLY_DB_INDEX,
        DRAGONFLY_HOST,
        DRAGONFLY_PASSWORD,
        DRAGONFLY_PORT,
    )

    _SOURCE = "local"
except ImportError:
    # 2. Fallback to environment variables
    DRAGONFLY_HOST = os.getenv("DRAGONFLY_HOST")
    DRAGONFLY_PORT = int(os.getenv("DRAGONFLY_PORT", "6379"))
    DRAGONFLY_PASSWORD = os.getenv("DRAGONFLY_PASSWORD")
    DRAGONFLY_DB_INDEX = int(os.getenv("DRAGONFLY_DB_INDEX", "0"))
    DRAGONFLY_CONNECTION_URI = os.getenv("DRAGONFLY_CONNECTION_URI")
    _SOURCE = "env"

    # 3. Optionally, fetch from GCP Secret Manager if running in GCP and any secret is missing
    if (
        not DRAGONFLY_HOST or not DRAGONFLY_PASSWORD or not DRAGONFLY_CONNECTION_URI
    ) and os.getenv("GOOGLE_CLOUD_PROJECT"):
        try:
            from google.cloud import secretmanager

            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            client = secretmanager.SecretManagerServiceClient()

            def get_secret(secret_id):
                name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")

            if not DRAGONFLY_HOST:
                DRAGONFLY_HOST = get_secret("DRAGONFLY_HOST")
            if not DRAGONFLY_PASSWORD:
                DRAGONFLY_PASSWORD = get_secret("DRAGONFLY_PASSWORD")
            if not DRAGONFLY_CONNECTION_URI:
                DRAGONFLY_CONNECTION_URI = get_secret("DRAGONFLY_CONNECTION_URI")
            if not DRAGONFLY_PORT:
                DRAGONFLY_PORT = int(get_secret("DRAGONFLY_PORT"))
            if not DRAGONFLY_DB_INDEX:
                DRAGONFLY_DB_INDEX = int(get_secret("DRAGONFLY_DB_INDEX"))
            _SOURCE = "gcp_secret_manager"
        except Exception:
            # If GCP Secret Manager is unavailable, fail gracefully
            pass


# For debugging (never print secrets)
def log_dragonfly_config():
    print(f"[DragonflyDB config loaded from: {_SOURCE}]")
    print(f"  HOST: {'set' if DRAGONFLY_HOST else 'MISSING'}")
    print(f"  PORT: {DRAGONFLY_PORT}")
    print(f"  PASSWORD: {'set' if DRAGONFLY_PASSWORD else 'MISSING'}")
    print(f"  DB_INDEX: {DRAGONFLY_DB_INDEX}")
    print(f"  CONNECTION_URI: {'set' if DRAGONFLY_CONNECTION_URI else 'MISSING'}")
