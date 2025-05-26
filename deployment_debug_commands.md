# Google Cloud Deployment Debug Commands

## Quick Commands for Deployment Investigation

### 1. Check Last Build Status
```bash
# Get last build status
gcloud builds list --limit=1 --format="table(id,status,createTime,duration)"

# Get last build logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

### 2. Check Cloud Run Services
```bash
# List all services with status
gcloud run services list --region=us-central1

# Get specific service details
gcloud run services describe ai-orchestra-minimal --region=us-central1

# Get service URL
gcloud run services describe ai-orchestra-minimal --region=us-central1 --format="value(status.url)"
```

### 3. View Logs
```bash
# Last 50 error logs from all Cloud Run services
gcloud logging read "resource.type=\"cloud_run_revision\" severity>=ERROR" --limit=50 --format=json

# Logs from specific service in last hour
gcloud logging read "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"ai-orchestra-minimal\" timestamp>=\"$(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=100

# Follow logs in real-time (requires alpha)
gcloud alpha run services logs tail ai-orchestra-minimal --region=us-central1
```

### 4. Check Secrets
```bash
# List all secrets
gcloud secrets list

# Check if a specific secret exists and has versions
gcloud secrets versions list OPENAI_API_KEY

# Check secret access permissions
gcloud secrets get-iam-policy OPENAI_API_KEY
```

### 5. Check Service Account Permissions
```bash
# List service accounts
gcloud iam service-accounts list

# Check roles for CI/CD service account
gcloud projects get-iam-policy cherry-ai-project --flatten="bindings[].members" --filter="bindings.members:cicd-sa@cherry-ai-project.iam.gserviceaccount.com" --format="table(bindings.role)"
```

### 6. Container Registry/Artifact Registry
```bash
# List recent images
gcloud artifacts docker images list us-central1-docker.pkg.dev/cherry-ai-project/orchestra-repo --limit=5

# Get image details
gcloud artifacts docker images describe us-central1-docker.pkg.dev/cherry-ai-project/orchestra-repo/ai-orchestra-minimal:latest
```

### 7. Debug Failed Deployments
```bash
# Find failed builds
gcloud builds list --filter="status=FAILURE" --limit=5

# Get detailed error from failed build
gcloud builds log $(gcloud builds list --filter="status=FAILURE" --limit=1 --format="value(id)") | grep -A5 -B5 "ERROR"

# Check Cloud Run deployment errors
gcloud logging read "resource.type=\"cloud_run_revision\" \"deployment failed\"" --limit=20
```

### 8. Health Checks
```bash
# Quick health check
curl -s -o /dev/null -w "%{http_code}" $(gcloud run services describe ai-orchestra-minimal --region=us-central1 --format="value(status.url)")/health

# Detailed health check with response
curl -s $(gcloud run services describe ai-orchestra-minimal --region=us-central1 --format="value(status.url)")/health | jq .
```

### 9. Resource Quotas
```bash
# Check if hitting any quotas
gcloud compute project-info describe --format="table(quotas[].metric,quotas[].limit,quotas[].usage)" | grep -v " 0$"
```

### 10. All-in-One Debug Command
```bash
# Combined status check
echo "=== BUILD STATUS ===" && \
gcloud builds list --limit=1 && \
echo -e "\n=== SERVICES ===" && \
gcloud run services list --region=us-central1 && \
echo -e "\n=== RECENT ERRORS ===" && \
gcloud logging read "severity>=ERROR timestamp>=\"$(date -u -d '30 minutes ago' '+%Y-%m-%dT%H:%M:%S')Z\"" --limit=5
```

## Pro Tips

1. **Use `--format=json` for scripting**: Add `| jq .` for pretty printing
2. **Use `--format="value(field)"` to get specific values**: Great for scripts
3. **Add `--project=cherry-ai-project` if not set as default**
4. **Use `watch` command for monitoring**: `watch -n 5 'gcloud run services list --region=us-central1'`
5. **Export logs for analysis**: Add `> deployment_logs.txt` to save output
