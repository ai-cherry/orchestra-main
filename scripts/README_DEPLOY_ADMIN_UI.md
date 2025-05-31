# Automated Admin UI + Backend Deployment

This process ensures the Admin UI always displays **real agent data** (never mock data) for both current and future deployments.

## What the Script Does
- Sets the correct API URL and API key for the frontend via `.env`.
- Builds the Admin UI with these settings.
- Deploys the built UI to the web root (`/var/www/orchestra-admin`).
- Restarts backend and nginx to pick up changes.
- Verifies that `/api/agents` returns real agent data (not mock data).
- Fails if any step is wrong.

## Usage

```bash
bash scripts/deploy_admin_ui_and_backend.sh
```

## Requirements
- `pnpm` installed
- Sudo access for deploying to web root and restarting services
- Backend must be running on the correct port (default: 8001)

## How It Works
- The script writes `.env` in `admin-ui/` with:
  - `VITE_API_URL=https://cherry-ai.me`
  - `VITE_API_KEY=4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd`
- The frontend always uses these for all API calls and authentication.
- Nginx proxies `/api` to the backend, so the UI and API are always in sync.
- The script verifies the deployment by checking for real agent IDs in the API response.

## Troubleshooting
- If the script fails, check the backend logs and nginx config.
- Make sure the backend is running and accessible from the web server.
- Ensure the API key matches the backend configuration.

## For Future Deployments
- Always use this script to deploy the Admin UI and backend together.
- Update the API URL or key in the script if your deployment changes.
