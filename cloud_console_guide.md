# Cloud Console Investigation Guide

Since you're having authentication issues in Cloud Shell, use the Google Cloud Console web interface:

## 1. Check Cloud Build Status
Go to: https://console.cloud.google.com/cloud-build/builds?project=cherry-ai-project

- Look for any failed builds (red X marks)
- Click on a build to see detailed logs
- Your recent builds show SUCCESS, so builds are working

## 2. Check Cloud Run Services
Go to: https://console.cloud.google.com/run?project=cherry-ai-project

Look for these services:
- **ai-orchestra-minimal** - Should show as "Serving traffic"
- **web-scraping-agents** - Check if deployed
- **admin-interface** - Check status
- **mcp-server** - Check status

## 3. Fix the 403 Error on ai-orchestra-minimal

In the Cloud Run console:
1. Click on **ai-orchestra-minimal**
2. Go to the **PERMISSIONS** tab
3. Click **ADD PRINCIPAL**
4. Add:
   - Principal: `allUsers`
   - Role: `Cloud Run Invoker`
5. Click **SAVE**

This will allow public access to your service.

## 4. Check Service Logs
1. In the Cloud Run service page, click on **LOGS** tab
2. Look for any error messages
3. Filter by severity if needed

## 5. Test the Service
After adding public access, test in a new browser tab:
```
https://ai-orchestra-minimal-yshgcxa7ta-uc.a.run.app/health
```

## 6. Check Secret Manager
Go to: https://console.cloud.google.com/security/secret-manager?project=cherry-ai-project

Verify these secrets exist:
- OPENAI_API_KEY
- PORTKEY_API_KEY
- REDIS_HOST
- REDIS_PASSWORD
- ZENROWS_API_KEY
- APIFY_API_KEY

## 7. Alternative: Use Cloud Shell with Fresh Auth

If you want to try Cloud Shell again:
```bash
# Clear all configs and start fresh
gcloud config configurations create fresh-config
gcloud config set project cherry-ai-project
gcloud auth login

# Then test
gcloud run services list --region=us-central1
```

## Quick Fixes via Console

### To make service public:
1. Go to Cloud Run → ai-orchestra-minimal → PERMISSIONS
2. Add `allUsers` with `Cloud Run Invoker` role

### To check why other services aren't ready:
1. Click on each service in Cloud Run console
2. Check the LOGS tab for startup errors
3. Check the REVISIONS tab to see if deployments failed

### To redeploy a service:
1. Go to Cloud Build console
2. Click "RUN TRIGGER" on the latest successful build
3. Or use "DEPLOY NEW REVISION" in Cloud Run console

## Summary of Your Current State

✅ **Working:**
- Authentication (scoobyjava@cherry-ai.me)
- Cloud Build (all recent builds successful)
- ai-orchestra-minimal is deployed

❌ **Issues:**
- ai-orchestra-minimal returns 403 (needs public access)
- Other services show as not ready
- Cloud Shell has authentication conflicts

**Immediate Action:** Use the Cloud Console to add public access to ai-orchestra-minimal service.
