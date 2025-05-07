# Non-Compliant GCP Resources

## 1. Credentials Management
**Resource:** Provider Configuration
```terraform
provider "google" {
  credentials = file("/tmp/gsa-key.json")
}
```
**Issue:** Service account key stored in a temporary directory
**Compliance Risk Level:** HIGH
**Details:** Storing service account keys in /tmp creates significant security risks as this directory is often world-readable, may not be properly cleaned up, and is vulnerable to theft. This violates GCP security best practices.

## 2. IAM Role Assignment
**Resource:** google_project_iam_member.vertex_agent_run_admin
```terraform
resource "google_project_iam_member" "vertex_agent_run_admin" {
  role    = "roles/run.admin"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}
```
**Issue:** Overly permissive IAM role
**Compliance Risk Level:** MEDIUM
**Details:** The service account is granted the broad roles/run.admin permission, which provides excessive privileges. This violates the principle of least privilege and increases attack surface.

## 3. Redis Configuration
**Resource:** module.redis.google_redis_instance.cache
```terraform
# Inferred from Terraform plan
resource "google_redis_instance" "cache" {
  transit_encryption_mode = "DISABLED"
}
```
**Issue:** Missing encryption in transit
**Compliance Risk Level:** HIGH
**Details:** Redis instance is configured with transit encryption disabled, creating potential data exposure risks during network transmission. For sensitive data, transit encryption should be enabled.

## 4. Storage Bucket Configuration
**Resource:** google_storage_bucket.terraform_state
```terraform
resource "google_storage_bucket" "terraform_state" {
  name          = "cherry-ai-project-terraform-state"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
  # Missing uniform_bucket_level_access = true
}
```
**Issue:** Missing uniform bucket level access
**Compliance Risk Level:** MEDIUM
**Details:** Uniform bucket-level access is not explicitly enabled, allowing for legacy ACL permissions which are less secure and harder to manage. This should be enabled to ensure proper access control.

## 5. Cloud Run Security
**Resource:** module.orchestrator_run.google_cloud_run_service.service
```terraform
# Inferred from configuration
resource "google_cloud_run_service" "service" {
  # Missing secure environment configuration
  # No explicit security contexts defined
}
```
**Issue:** Insufficient security configuration
**Compliance Risk Level:** MEDIUM
**Details:** The Cloud Run service doesn't specify security contexts or container security policies. Running containers without security boundaries increases risk of privilege escalation.

## 6. Encryption Keys
**Resource:** Multiple resources
**Issue:** Missing CMEK (Customer Managed Encryption Keys)
**Compliance Risk Level:** MEDIUM
**Details:** Critical services like Cloud Run, Firestore, and Pub/Sub aren't configured to use Customer Managed Encryption Keys, relying instead on Google-managed keys. For sensitive workloads, CMEK is recommended for stronger security and compliance.

## 7. Monitoring Configuration
**Resource:** module.monitoring
```terraform
module "monitoring" {
  count  = var.enable_monitoring ? 1 : 0
  # Configuration can be disabled via variable
}
```
**Issue:** Optional monitoring
**Compliance Risk Level:** LOW
**Details:** Monitoring is conditionally enabled through a boolean variable, which could lead to production environments with insufficient observability if misconfigured.
