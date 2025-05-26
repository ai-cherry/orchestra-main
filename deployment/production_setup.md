# GCP Production Deployment & Environment Setup with MCP

This guide outlines a comprehensive, automated approach to deploying and managing your AI agent orchestrator platform in Google Cloud Platform (GCP) using the Managed Cloud Platform (MCP) and related services.

---

## 1. **Prerequisites**

- GCP project with billing enabled
- Owner access to GCP Console and CLI
- MCP codebase (with Pulumi, FastAPI, Docker, etc.)
- GitHub repository for CI/CD

---

## 2. **Initial GCP Bootstrap (Manual, Once)**

1. **Create GCP Project**
   `gcloud projects create my-mcp-project`
2. **Enable Billing**
   Link billing account via GCP Console.
3. **Enable Required APIs**
   ```bash
   gcloud services enable run.googleapis.com secretmanager.googleapis.com \
     storage.googleapis.com pubsub.googleapis.com firestore.googleapis.com \
     monitoring.googleapis.com logging.googleapis.com
   ```
4. **Create Service Account**
   ```bash
   gcloud iam service-accounts create mcp-deployer \
     --display-name="MCP Deployer"
   ```
5. **Assign Roles**
   ```bash
   gcloud projects add-iam-policy-binding my-mcp-project \
     --member="serviceAccount:mcp-deployer@my-mcp-project.iam.gserviceaccount.com" \
     --role="roles/owner"
   ```
6. **Download Service Account Key**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=mcp-deployer@my-mcp-project.iam.gserviceaccount.com
   ```

---

## 3. **Automated Infrastructure Provisioning (Pulumi via MCP)**

1. **Configure Pulumi Stack**
   - Set GCP project, region, and credentials in `Pulumi.<stack>.yaml`.
2. **Define Infrastructure as Code**
   - Cloud Run services for each MCP server
   - Secret Manager secrets
   - Firestore database
   - Pub/Sub topics/subscriptions
   - Storage buckets
   - Monitoring dashboards/alerts
3. **Trigger Pulumi Apply via MCP**
   ```bash
   curl -X POST "https://<MCP-GATEWAY-URL>/mcp/gcp/pulumi/apply" \
     -H "Content-Type: application/json" \
     -d '{"stack_name": "production"}'
   ```
   - MCP will run `pulumi up` and return output/logs.

---

## 4. **CI/CD Pipeline (GitHub Actions Example)**

- **Build & Test:**
  - Lint, test, and build Docker images for all MCP servers.
- **Push to GCR:**
  - Authenticate with GCP and push images to Google Container Registry.
- **Deploy to Cloud Run:**
  - Use `gcloud run deploy` or Pulumi to update services.
- **Automate Secret Sync:**
  - Use MCP Secret Manager endpoints to update secrets from CI/CD.

---

## 5. **Configuration & Secrets Management**

- Store all sensitive values in GCP Secret Manager.
- Use MCP endpoints to create/update secrets as needed.
- Inject secrets into Cloud Run services via environment variables.

---

## 6. **Monitoring, Logging, and Alerting**

- **Enable GCP Operations Suite (formerly Stackdriver):**
  - Logs: View in GCP Console or export to BigQuery/Storage.
  - Metrics: Use Prometheus/Grafana or GCP dashboards.
  - Alerts: Configure for errors, latency, and resource usage.
- **MCP Health Endpoints:**
  - `/health` endpoints for all MCP servers.
  - Aggregate status in the dashboard.

---

## 7. **Scalability & Security**

- **Cloud Run Autoscaling:**
  - Set min/max instances and concurrency in Pulumi or deploy scripts.
- **IAM Best Practices:**
  - Principle of least privilege for service accounts.
- **Network Security:**
  - Restrict ingress/egress as needed.
- **Periodic Secret Rotation:**
  - Use MCP or GCP automation.

---

## 8. **Operational Automation**

- **Automated Rollbacks:**
  - Use Cloud Run revisions and MCP endpoints to revert deployments.
- **Scheduled Backups:**
  - Automate Firestore and Storage backups.
- **Disaster Recovery:**
  - Document and test restore procedures.

---

## 9. **Best Practices**

- Use MCP for all repeatable, code-driven GCP operations.
- Keep Pulumi/Terraform code in version control.
- Regularly review IAM roles and audit logs.
- Monitor costs and optimize resource usage.

---

## 10. **References**

- [Pulumi GCP Provider](https://www.pulumi.com/registry/packages/gcp/)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying)
- [Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [GCP Monitoring & Logging](https://cloud.google.com/products/operations)

---

**Summary:**
This setup ensures a secure, scalable, and fully automated production environment in GCP, leveraging MCP for end-to-end lifecycle management, rapid iteration, and operational excellence.
