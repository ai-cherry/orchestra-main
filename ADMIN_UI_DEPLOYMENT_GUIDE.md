# Admin UI Deployment Guide

This document explains **how to build, deploy, and operate the Cherry AI Admin UI** on DigitalOcean.  
It consolidates the lessons learned during recent troubleshooting sessions (blank-white-screen issue) and should be followed for every release.

---

## 1. Build Pipeline

| Step | Command | Notes |
|------|---------|-------|
| Install Node 20 & PNPM | `npm install -g pnpm` | Node 20 is the version used in CI. |
| Install deps | `cd admin-ui && pnpm install --frozen-lockfile` | Always commit `pnpm-lock.yaml` after dependency changes. |
| Type-check & lint | `pnpm lint` | Fails build on ESLint / TS errors. |
| Unit tests | `pnpm test` | Jest/Vitest + React-Testing-Library. |
| Build | `pnpm build` | Output is written to `admin-ui/dist`. |
| Verify bundle | `ls -lh dist/assets` – JS bundle ≈ 350–400 kB, CSS ≈ 25–30 kB. |

> If the JS file is **\<10 kB** the build is corrupted (usually a Vite config or env var problem).

---

## 2. Deployment to DigitalOcean App Platform

There are **two supported paths**.

### 2.1 GitHub Actions (Recommended / CI-CD)

1. Push to `main`.  
2. `.github/workflows/deploy.yaml` runs:
   * Builds the Admin UI ➜ uploads artifact.
   * Runs Pulumi `infra/do_superagi_stack.py` (`pulumi up --stack prod`).
   * Outputs `admin_ui_live_url` (should equal `https://cherry-ai.me`).

No manual action is required if the workflow turns green.

### 2.2 Manual CLI (Hot-fix / local)

```bash
# 1. Build (see section 1)
export DIGITALOCEAN_TOKEN=...   # PAT with write permission
export PULUMI_ACCESS_TOKEN=...   # org token

# 2. Copy dist locally if you built elsewhere
rsync -av admin-ui/dist/ infra/admin_ui_site/

# 3. Deploy Infra (creates/updates App + custom domain)
cd infra
pulumi stack select prod --create
pulumi config set adminUiCustomDomain cherry-ai.me
pulumi up --yes
```

Pulumi provisions:

* `admin-ui-app-prod` – App Platform Static Site  
  * **Region:** `sfo2`  
  * **Root dir:** `admin_ui_site/`  
  * **Index / Error / Catch-all:** `index.html`

---

## 3. Domain & DNS Configuration

| Record | Type | Value |
|--------|------|-------|
| `cherry-ai.me` | `A`  | DigitalOcean load-balancer IP (shown in App overview) |
| (optional) `www` | `CNAME` | `cherry-ai.me.` |

Guidelines:

* After Pulumi finishes, copy the **Assigned IP** from the *Resources → App → Settings* page.
* Propagation can take **5–20 min**.  
  Verify with `dig +short cherry-ai.me`.

SSL:

* App Platform issues an **auto-managed Let’s Encrypt certificate**.  
* Status appears as **“Active”** usually < 15 min after A-record resolves.

---

## 4. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| Blank white page, 200 response, 300 B HTML | Missing JS bundle (bad build uploaded) | Re-run build, confirm bundle size, redeploy. |
| HTML references `/assets/index-*.js` 404 | `source_dir` wrong or files not uploaded | Ensure `admin-ui/dist` is copied to `infra/admin_ui_site` before `pulumi up`. |
| DNS resolves but HTTPS fails | Cert still provisioning | Wait up to 20 min, run `check_site_status.sh`. |
| `curl :8080` on droplet fails | API service down | SSH into droplet, `sudo systemctl status orchestra-api`. |
| GitHub Action fails "`pulumi login`" | Missing `PULUMI_ACCESS_TOKEN` secret | Add/rotate org secret (`ORG_PULUMI_ACCESS_TOKEN`). |

Useful scripts:

* `scripts/check_site_status.sh` – DNS + SSL probe.
* `deploy_admin_ui.sh` – one-liner wrapper for manual deployment.
* `check_deployment_status.py` – full health report (UI, droplet, DB, SSL, DNS).

---

## 5. Monitoring & Maintenance

### 5.1 Automated

* **GitHub Action:** `.github/workflows/health-check.yml` pings `https://cherry-ai.me` every hour – fails the workflow & sends email on non-200.
* **DigitalOcean App Metrics:** Enable **Alerts → Response Time** & **Errors**.

### 5.2 Manual Checklist (Monthly)

1. `check_deployment_status.py --token $DO_TOKEN` – all components `✓ OK`.
2. Review App Platform **Activity Log** for failed deploys.
3. Rotate **GH_*_TOKEN** org secrets if older than 90 days.
4. `pnpm outdated` ➜ bump minor versions, rebuild, push PR.
5. Verify SSL expiry (`openssl s_client -connect cherry-ai.me:443`).

### 5.3 Rollback

```
pulumi stack history prod
pulumi stack export --version <prev> | pulumi stack import
pulumi up --yes
```

Or select a previous **Deployment** in DigitalOcean UI and click **“Rollback”**.

---

## 6. Quick-Reference Commands

```bash
# One-liner deploy (with env vars set)
./deploy_admin_ui.sh

# Inspect App logs
doctl apps logs <APP_ID> --tail

# Purge CDN cache (if using DO CDN)
doctl CDN flush <CDN_ID>

# Local smoke test
npx serve admin-ui/dist
open http://localhost:5000
```

---

### Contact

*Slack*: `#orchestra-operations`  
*Email*: ops@cherry-ai.me  
*PagerDuty*: “Admin-UI prod” service
