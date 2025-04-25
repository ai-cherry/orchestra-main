# Security Policy Exceptions

## Exception ID: SEC-EXC-2025-001
### Title: Temporary Service Account File in /tmp
**Resource:** Google Provider Configuration

**Policy Violation:**
```terraform
provider "google" {
  credentials = file("/tmp/gsa-key.json")
}
```

**Exception Details:**
* **Risk Level:** HIGH
* **Exception Duration:** 90 days
* **Requested By:** Infrastructure Team
* **Approvers Required:** CISO, Security Architect

**Justification:**
Temporary deployment pipeline requires service account keys for authentication during the transition period to Workload Identity Federation. The keys are generated at deployment time and deleted immediately after deployment completes.

**Mitigation Measures:**
1. Keys are rotated automatically every 7 days
2. File permissions are set to 0400 (read-only by owner)
3. Keys have narrowly scoped permissions limited to deployment operations
4. Audit logging captures all operations performed using these credentials
5. Automated cleanup script removes the key file immediately after successful deployment

**Remediation Plan:**
Transition to Workload Identity Federation by EOQ2 2025, eliminating the need for service account key files.

---

## Exception ID: SEC-EXC-2025-002
### Title: Redis Transit Encryption Disabled
**Resource:** Redis Instance

**Policy Violation:**
```terraform
module "redis" {
  # ...
  # Redis instance configured with transit encryption disabled
  # ...
}
```

**Exception Details:**
* **Risk Level:** MEDIUM
* **Exception Duration:** 30 days
* **Requested By:** Platform Engineering
* **Approvers Required:** Security Architect, Data Protection Officer

**Justification:**
Existing application compatibility issues prevent immediate enablement of transit encryption for Redis. The instance is deployed within a secure VPC with restricted access through VPC Service Controls.

**Mitigation Measures:**
1. Redis instance is only accessible within VPC
2. Firewall rules restrict access to specific service accounts
3. All access is logged and monitored for anomalies
4. Sensitive data is encrypted at the application level before storage

**Remediation Plan:**
Application fixes to support encrypted Redis connections are scheduled for the next sprint, with deployment in 30 days.

---

## Exception ID: SEC-EXC-2025-003
### Title: Admin Permissions for Vertex AI Service Account and API Key Usage
**Resource:** IAM Role Binding and Vertex AI API Key

**Policy Violation:**
```terraform
resource "google_project_iam_member" "vertex_agent_run_admin" {
  role    = "roles/run.admin"
  member  = "serviceAccount:vertex-agent@${var.project_id}.iam.gserviceaccount.com"
}

# Additionally, Vertex AI API key is used instead of service account authentication:
# Vertex Key: 0d08481a204c0cdba4095bb94529221e8b8ced5c
```

**Exception Details:**
* **Risk Level:** HIGH
* **Exception Duration:** 60 days
* **Requested By:** AI/ML Team
* **Approvers Required:** CISO, Security Architect, Platform Engineering Lead

**Justification:**
The Vertex AI service account currently requires administrative access to Cloud Run to deploy and manage AI-driven workloads during this initial implementation phase. Restricted IAM roles are causing deployment failures due to insufficient permissions. Additionally, a static API key (0d08481a204c0cdba4095bb94529221e8b8ced5c) is temporarily required for AI model access during the integration phase.

**Mitigation Measures:**
1. Enhanced audit logging for all Cloud Run and Vertex AI operations
2. Automated daily review of operations performed by service account and API key
3. Service account key rotation every 30 days
4. IP-based restrictions for API access
5. Alerts on suspicious activity patterns
6. The Vertex AI API key is stored in Secret Manager with strict access controls
7. API key usage is limited to specific IP ranges of deployment environments
8. All API key usage is logged in Cloud Audit Logs with detailed attribution

**Remediation Plan:**
1. Security team to work with AI/ML team to identify minimal required permissions and transition to custom IAM role with least privilege within 60 days
2. Transition from API key authentication to service account authentication for Vertex AI within 30 days
3. Implement Workload Identity Federation for all AI/ML workloads within 60 days

---

## Exception ID: SEC-EXC-2025-004
### Title: CMEK Encryption Exemption
**Resource:** Multiple GCP Resources

**Policy Violation:**
Corporate policy requires Customer Managed Encryption Keys (CMEK) for all cloud resources containing sensitive data. The following resources do not implement CMEK:

* Firestore database
* Cloud Run services
* Pub/Sub topics

**Exception Details:**
* **Risk Level:** LOW
* **Exception Duration:** 120 days
* **Requested By:** Infrastructure Team
* **Approvers Required:** CISO

**Justification:**
The current platform is in active development without processing regulated data. Implementation of CMEK would significantly increase development complexity during this initial phase. Google-managed encryption keys provide sufficient protection for current development data.

**Mitigation Measures:**
1. No PII, PHI, or other regulated data to be stored during the exception period
2. Data classification verification in CI/CD pipeline
3. Regular data scanning to verify absence of sensitive information
4. Prepare CMEK implementation design ready for activation

**Remediation Plan:**
CMEK implementation is scheduled for Q3 2025 as part of the pre-production security enhancements before onboarding sensitive customer data.

---

## Exception ID: SEC-EXC-2025-005
### Title: Bucket ACL Configuration
**Resource:** Storage Bucket

**Policy Violation:**
```terraform
resource "google_storage_bucket" "terraform_state" {
  # Missing uniform_bucket_level_access = true
}
```

**Exception Details:**
* **Risk Level:** LOW
* **Exception Duration:** 45 days
* **Requested By:** DevOps Team
* **Approvers Required:** Security Architect

**Justification:**
Legacy CI/CD pipelines require fine-grained ACL permissions for terraform state bucket access. Engineering team needs time to update pipeline configuration to use IAM permissions.

**Mitigation Measures:**
1. Regular audit of bucket ACLs to prevent public exposure
2. Restricted network access to bucket through VPC Service Controls
3. Object versioning enabled to protect from unauthorized changes
4. Automated scanning for sensitive content in state files
5. Enhanced logging for all bucket operations

**Remediation Plan:**
Update CI/CD pipelines to use service accounts with appropriate IAM roles within 45 days, then enable uniform bucket level access.

---

## Exception ID: SEC-EXC-2025-006
### Title: Optional Monitoring Configuration
**Resource:** Monitoring Module

**Policy Violation:**
```terraform
module "monitoring" {
  count = var.enable_monitoring ? 1 : 0
  # ...
}
```

**Exception Details:**
* **Risk Level:** LOW
* **Exception Duration:** 30 days
* **Requested By:** Platform Engineering
* **Approvers Required:** Security Operations Lead

**Justification:**
Development environments use minimal resources to reduce costs, and full monitoring stack is not required for all development activities. Current configuration allows conditional deployment of monitoring resources.

**Mitigation Measures:**
1. Mandatory monitoring in staging and production environments
2. Critical security alerts still enabled through organization-level monitoring
3. Regular scheduled scans of unmonitored resources
4. Weekly security review of development environments

**Remediation Plan:**
Update infrastructure to implement tiered monitoring approach, with baseline security monitoring required for all environments regardless of environment type.

---

**Required Signatures:**

Chief Information Security Officer: _________________________ Date: _________

Security Architect: _________________________ Date: _________

Platform Engineering Lead: _________________________ Date: _________

Data Protection Officer: _________________________ Date: _________
