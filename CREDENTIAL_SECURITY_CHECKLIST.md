# Credential Security Checklist

**CRITICAL: Several sensitive credentials were exposed in the original task description. This document outlines immediate actions to take and best practices for future credential management.**

## Immediate Actions Required

- [ ] **Rotate ALL exposed GCP credentials**:
  - Google API Key (`AIzaSyDem1_BvE0eeq8PaRvnlsBXMqjI3Z3zB_U`)
  - OAuth Client Secret (`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`)
  - Service account keys (both `6833bc94f0e3ef8648efc1578caa23ba2b8a8a52` and `f510256389008a55a6142d2429a185ebf216d685`)
  - Vertex alternative key (`0d08481a204c0cdba4095bb94529221e8b8ced5c`)
  - Figma PAT (`figd_JbqWhdGvNaRvQyLdZdEJslu-8hHoaotLaNKByNRz`)

- [ ] **Update GCP IAM permissions**:
  - Review and restrict overly permissive roles (especially Owner and Admin roles)
  - Apply principle of least privilege to all service accounts and users

- [ ] **Secure SSH credentials**:
  - Change SSH passphrase (`Huskers15`)
  - Use SSH keys instead of passwords when possible

## Future Credential Management Best Practices

### 1. Use Secret Manager for All Credentials

```bash
# Store a secret in Secret Manager
gcloud secrets create api-key --data-file=/path/to/api-key.txt

# Access a secret in your application
gcloud secrets versions access latest --secret=api-key
```

### 2. Implement Short-Lived Credentials

- Replace long-lived service account keys with:
  - Workload Identity Federation for GKE
  - Service account impersonation
  - Temporary access tokens

### 3. Set Up Proper Rotation Schedules

- API Keys: Every 90 days
- OAuth Secrets: Every 180 days
- Service Account Keys: Every 90 days or replace with alternative approaches

### 4. Implement Audit Logging

```bash
# Enable Data Access audit logs
gcloud projects update cherry-ai-project \
    --update-labels=enable-audit-logs=true

# View access logs
gcloud logging read "resource.type=service_account AND protoPayload.methodName=ServiceAccountKeyService.CreateServiceAccountKey"
```

### 5. Use the Memory System's Privacy Controls

Leverage the newly implemented privacy features:

```python
# Create privacy-enhanced memory manager
privacy_manager = PrivacyEnhancedMemoryManager(
    underlying_manager=base_adapter,
    config=StorageConfig(
        environment="prod",
        enable_dev_notes=False,
        default_privacy_level="sensitive",
        enforce_privacy_classification=True
    ),
    pii_config=PIIDetectionConfig(
        enable_pii_detection=True,
        enable_pii_redaction=True,
        default_retention_days=90
    )
)
```

## References

- [Google Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [GCP Key Management Service](https://cloud.google.com/kms/docs)
