# Admin UI Deployment Guide

This guide explains how to build and deploy the React Admin UI to the Vultr server.

## 1. Build Pipeline

| Step | Command | Notes |
|------|---------|-------|
| Install PNPM | `npm install -g pnpm` | Node 20 is used in CI |
| Install deps | `cd admin-ui && pnpm install --frozen-lockfile` | |
| Lint & test | `pnpm lint && pnpm test` | Fails on any warnings |
| Build | `pnpm build` | Outputs to `admin-ui/dist` |

## 2. Deployment via GitHub Actions

Pushing to `main` triggers `.github/workflows/deploy.yaml` which:
1. Builds the Admin UI
2. Runs `pulumi up` to update the Vultr stack
3. Copies the built files to the server via SSH

No manual steps are required if the workflow succeeds.

## 3. Manual Deployment

```bash
# Build locally
cd admin-ui
pnpm install --frozen-lockfile
pnpm build

# Copy files to server
scp -r dist/* root@<VULTR_IP>:/opt/orchestra/admin-ui/
```

The Admin UI is served by the Nginx container and is available at `http://<VULTR_IP>`.
