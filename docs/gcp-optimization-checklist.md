#
---

## 1. Project & API Setup

- [ ] Project created and billing enabled
- [ ] All required APIs enabled (see - [ ] Quotas reviewed and increased as needed

## 2. IAM & Service Accounts

- [ ] Dedicated service account for Orchestra AI created
- [ ] Least-privilege IAM roles assigned (owner/admin only if necessary)
- [ ] Service account keys managed securely (prefer Workload Identity)

## 3. Networking

- [ ] Custom VPC and subnet created for isolation and performance
- [ ] Firewall rules configured for required ports/services
- [ ] VPC connectors set up for
## 4. Core Managed Services

- [ ] - [ ] Redis (MemoryStore) provisioned and connected
- [ ] AlloyDB instance created and configured
- [ ] - [ ] Storage buckets (GCS) created for data and logs

## 5. Monitoring & Logging

- [ ] Monitoring dashboards (Prometheus/Grafana) set up
- [ ] Log sinks configured for long-term retention and analysis
- [ ] Alerts set for errors, latency, and quota usage

## 6. Security & Compliance

- [ ] Secrets never stored in code or state files
- [ ] IAM audit logs enabled
- [ ] Regular key/secret rotation scheduled
- [ ] Access reviewed and restricted to minimum required

## 7. Automation & CI/CD

- [ ] Pulumi stacks or gcloud scripts versioned in Git
- [ ] CI/CD pipeline (GitHub Actions/Cloud Build) runs preview/apply on PR/merge
- [ ] Manual approval required for production applies
- [ ] Automated tests for infrastructure and deployment

## 8. Performance & Cost Optimization

- [ ] Autoscaling enabled for - [ ] Resource sizes tuned for workload (CPU/memory)
- [ ] Unused resources cleaned up regularly
- [ ] Cost monitoring and alerts set up

## 9. Documentation & Onboarding

- [ ] All scripts and stacks documented
- [ ] Onboarding guide for new developers
- [ ] Troubleshooting and rollback procedures in place

---

**Tip:**
Run `bash
---
