# Payment Data Analysis Infrastructure

This document outlines the architecture and implementation strategy for a secure, isolated payment data analysis infrastructure using Google Cloud Platform (GCP). The design follows security best practices for handling sensitive payment data while enabling robust analytics capabilities.

## Architecture Overview

The architecture establishes a clear separation between general-purpose workloads and payment processing through:

1. **Project Isolation**: Dedicated GCP project for payment processing
2. **Resource Segregation**: Separate storage, processing, and analytics resources
3. **Least Privilege Access**: Purpose-specific service accounts with minimal permissions
4. **Enhanced Security Controls**: CMEK encryption, VPC Service Controls, and comprehensive audit logging

```mermaid
graph TB
    A[GCP Organization] --> B[Main Project<br/>cherry-ai-project]
    A --> C[Payment Project<br/>payment-processing-{env}]

    B --> D[General Purpose Resources]
    C --> E[Payment-Specific Resources]

    E --> F[Storage Layer]
    E --> G[Processing Layer]
    E --> H[Analytics Layer]
    E --> I[Security Controls]

    F --> F1[Cloud Storage<br/>Raw Payment Data]
    F --> F2[Firestore<br/>Transaction Records]
    F --> F3[BigQuery<br/>Structured Payment Data]

    G --> G1[Cloud Functions<br/>Payment Processing]
    G --> G2[Pub/Sub<br/>Payment Events]

    H --> H1[Vertex AI Endpoints<br/>Payment Analysis]
    H --> H2[Vector Search<br/>Pattern Recognition]
    H --> H3[BigQuery<br/>Reporting Datasets]

    I --> I1[CMEK<br/>Encryption]
    I --> I2[VPC SC<br/>Network Isolation]
    I --> I3[Audit Logging<br/>All Operations]
    I --> I4[IAM<br/>Service Accounts]
```

## Implementation Components

This architecture has been implemented with the following components:

### 1. Terraform Module for Payment Infrastructure

A complete infrastructure-as-code module is provided in `infra/modules/payment/` with:

- Project creation/configuration
- Storage resources (GCS, Firestore, BigQuery)
- Processing resources (Cloud Functions, Pub/Sub)
- Analytics infrastructure (Vertex AI, Vector Search)
- Security controls (CMEK, VPC SC, IAM, Audit logging)

### 2. Secure Vertex AI Agent Manager

A purpose-specific implementation for interacting with Vertex AI Agents for payment data analysis:

- Located at `packages/agents/runtime/security/payment_vertex_agent.py`
- Follows security best practices with no hardcoded credentials
- Implements least privilege principles with explicit operation limitations
- Provides comprehensive audit logging for all operations
- Includes automatic PII redaction for transaction data

## Security Controls

### Data Protection

1. **Customer-Managed Encryption Keys (CMEK)**

   - All payment data is encrypted using CMEK
   - 90-day key rotation policy
   - Separate key rings for payment data

2. **Network Isolation**

   - VPC Service Controls create security perimeters
   - Restricted API access for payment resources
   - Controlled data ingress/egress

3. **Identity and Access Management**

   - Purpose-specific service accounts:
     - `payment-data-reader` - Read-only access to payment data
     - `payment-data-processor` - Processing payment transactions
     - `payment-reporting` - Analytics and reporting
     - `payment-vertex-agent` - AI-based analysis with restricted permissions

4. **Audit and Compliance**
   - Comprehensive audit logging for all operations
   - Long-term storage of audit logs (365+ days)
   - Structured logging for fraud detection and security monitoring

## Vertex AI Agent Configuration

The Vertex AI agents have been reconfigured with:

1. **Scope Limitations**

   - Only allowed to perform specific payment-related operations
   - Limited to payment-specific data sources
   - PII redaction before processing

2. **Operations Audit**

   - All agent operations are logged to dedicated audit streams
   - High-risk operations require explicit approval
   - Anomalous behavior triggers alerts

3. **Secure Infrastructure Access**
   - No direct infrastructure management capabilities
   - Time-limited, scoped access tokens
   - Zero standing permissions

## Deployment Guide

### 1. Prerequisite Setup

Before deploying the payment infrastructure:

1. Ensure organization policies allow project creation (if using `create_project = true`)
2. Create an Access Context Manager policy for VPC Service Controls (if needed)
3. Set up a billing account for the payment project

### 2. Core Infrastructure Deployment

```hcl
module "payment_processing" {
  source = "./modules/payment"

  project_id     = "payment-processing-dev"
  region         = "us-west4"
  env            = "dev"
  create_project = true
  billing_account = "BILLING-ACCOUNT-ID"

  # Security features
  enable_cmek    = true
  enable_vpc_sc  = true
  access_policy_id = "ACCESS-POLICY-ID"  # Only needed if enable_vpc_sc = true
}
```

### 3. Application Integration

To use the secure Vertex AI agent manager in your applications:

```python
from packages.agents.runtime.security.payment_vertex_agent import PaymentVertexAgentManager

# Initialize with separate project for payment data
payment_agent = PaymentVertexAgentManager(
    project_id="cherry-ai-project",  # Main project
    payment_data_project_id="payment-processing-dev",  # Payment-specific project
    pubsub_topic="payment-events-dev"
)

# Analyze payment patterns securely
transaction_data = {
    "transactions": [...],  # Payment transactions
    "date_range": "2025-01-01/2025-04-01"
}
results = payment_agent.analyze_payment_patterns(transaction_data)
```

## Recommendations for Future Enhancements

1. **Advanced Data Classification**

   - Implement BigQuery column-level security
   - Automatic data classification for new datasets
   - Dynamic data masking for sensitive fields

2. **Continuous Security Monitoring**

   - Automated IAM recommendations
   - Security Health Analytics integration
   - Anomaly detection for access patterns

3. **Disaster Recovery Planning**
   - Cross-region replication for critical data
   - Regular backup verification
   - Recovery time objective (RTO) testing

## Implementation Roadmap

| Phase                  | Timeframe  | Description                                        |
| ---------------------- | ---------- | -------------------------------------------------- |
| Foundation             | 4-6 weeks  | Project isolation, IAM setup, basic infrastructure |
| Data Migration         | 6-8 weeks  | Move existing payment data, implement CMEK         |
| Analytics Capabilities | 8-10 weeks | Configure Vertex AI agents, vector search indexes  |
| Security Hardening     | 4-6 weeks  | VPC SC implementation, security testing            |
| Optimization           | Ongoing    | Performance tuning, cost optimization              |

## Conclusion

This architecture provides a secure foundation for payment data analysis while addressing the concerns around broad access permissions in the current setup. By isolating payment processing in a dedicated project with proper service accounts and security controls, the solution enables powerful analytics capabilities while maintaining robust data protection.
