# Cherry AI Orchestra Deployment Action Plan
**Date:** May 30, 2025  
**Status:** Admin UI built successfully, ready for deployment

## Current Situation

### ✅ What's Been Accomplished

1. **Admin UI Build Fixed**
   - Successfully built Admin UI with production configuration
   - CSS file: 27.14 KB (properly sized)
   - JS file: 394.17 KB (properly sized)
   - Build output verified in `admin-ui/dist/`

2. **Infrastructure Assessment**
   - Site is accessible at https://cherry-ai.me (returns HTTP 200)
   - Currently showing blank white screen (326 bytes) - this is the issue we're fixing
   - API endpoints returning 404 (backend not properly deployed)

3. **Scripts Prepared**
   - `deploy_admin_ui_quick.sh` - Quick deployment wrapper
   - `deploy_admin_ui_api.py` - Python script for DigitalOcean API deployment
   - `implement_two_node_architecture.sh` - Full infrastructure migration (for future use)

## 🚀 Immediate Actions Required

### Option 1: Manual Deployment (Requires DIGITALOCEAN_TOKEN)

1. **Set the DigitalOcean Token**
   ```bash
   export DIGITALOCEAN_TOKEN="your-digitalocean-api-token"
   ```

2. **Deploy the Fixed Admin UI**
   ```bash
   ./deploy_admin_ui_quick.sh
   ```

### Option 2: GitHub Actions Deployment (Recommended)

Since the DIGITALOCEAN_TOKEN and PULUMI_ACCESS_TOKEN are stored as GitHub secrets at the organizational level:

1. **Update GitHub Actions Workflow**
   The `.github/workflows/deploy.yaml` needs to be updated to include the migration job. Currently missing the `migrate-to-two-node-architecture` job.

2. **Push Changes to GitHub**
   ```bash
   git add admin-ui/package.json admin-ui/pnpm-lock.yaml
   git commit -m "fix: Add cssnano dependency for Admin UI build"
   git push origin main
   ```

3. **Trigger GitHub Actions**
   - Go to GitHub Actions tab
   - Run the deployment workflow manually

## 📋 Two-Node Architecture Migration (Future)

The `implement_two_node_architecture.sh` script is ready for the full migration to the two-node DigitalOcean architecture:

- **Vector + Storage Node**: CPU-Optimized Premium (4 vCPU / 8 GB) with NVMe
- **App / Orchestrator / MCP Node**: General-Purpose (8 vCPU / 32 GB)

This migration requires:
- DIGITALOCEAN_TOKEN
- PULUMI_ACCESS_TOKEN
- Data migration planning for existing services

## 🔍 Verification Steps

After deployment:

1. **Check Site Accessibility**
   ```bash
   curl -I https://cherry-ai.me
   ```

2. **Verify Content Size**
   ```bash
   curl -s https://cherry-ai.me | wc -c
   # Should be > 1000 bytes (not 326)
   ```

3. **Run Verification Script**
   ```bash
   python3 quick_verify_admin_ui.py
   ```

## 🚨 Important Notes

1. **Credentials**: All deployment methods require DIGITALOCEAN_TOKEN. This is stored as a GitHub secret but needs to be set as an environment variable for local deployment.

2. **DNS**: The domain cherry-ai.me is already configured and resolving correctly.

3. **Backend Services**: The API endpoints are returning 404, suggesting the backend services need to be deployed separately or as part of the full two-node migration.

## 📞 Next Steps Summary

1. **Immediate**: Deploy the fixed Admin UI build to resolve the blank screen issue
2. **Short-term**: Update GitHub Actions workflow for automated deployments
3. **Medium-term**: Execute the full two-node architecture migration
4. **Long-term**: Implement monitoring and automated health checks

## 🛠️ Troubleshooting

If deployment fails:
- Check DigitalOcean App Platform logs
- Verify API token permissions
- Ensure the app name "admin-ui-prod" doesn't conflict
- Check DNS propagation status 