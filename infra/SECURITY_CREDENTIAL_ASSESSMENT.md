# SECURITY CREDENTIAL ASSESSMENT - URGENT

## Exposed Credentials Alert

This document has been created in response to the exposure of multiple sensitive credentials. The following credentials have been identified in plain text and should be considered compromised:

### 🚨 CRITICAL: OAuth 2.0 Client Credentials
- **Client ID**: 104944497835-h9l77l0ltmv4h8t9o5a02m51v8g91a9i.apps.googleusercontent.com
- **Client Secret**: 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
- **Status**: COMPROMISED

### 🚨 CRITICAL: Google API Key
- **Key**: AIzaSyDem1_BvE0eeq8PaRvnlsBXMqjI3Z3zB_U
- **Status**: COMPROMISED

### 🚨 CRITICAL: Service Account Keys
- **Service Account**: cherrybaby@agi-baby-cherry.iam.gserviceaccount.com
  - **Key ID**: 6833bc94f0e3ef8648efc1578caa23ba2b8a8a52
  - **Status**: COMPROMISED (created Apr 11 2025; never expires)
  
- **Service Account**: vertex-agent@agi-baby-cherry.iam.gserviceaccount.com
  - **Key ID**: f510256389008a55a6142d2429a185ebf216d685
  - **Status**: COMPROMISED (created Apr 20 2025; never expires)
  - **Roles**: BigQuery Admin, Cloud Storage for Firebase Admin, Compute Admin, Gemini Settings Admin, Owner, Project IAM Admin, Vertex AI Service Agent
  - **Security Concern**: This service account has OWNER permissions, which grants complete control over the project.

### 🚨 CRITICAL: Figma Personal Access Token
- **Token**: figd_JbqWhdGvNaRvQyLdZdEJslu-8hHoaotLaNKByNRz
- **Status**: COMPROMISED

### 🚨 CRITICAL: SSH Passphrase
- **Passphrase**: Huskers15
- **Status**: COMPROMISED

### 🚨 CRITICAL: Vertex API Key
- **Key**: 0d08481a204c0cdba4095bb94529221e8b8ced5c
- **Status**: COMPROMISED

## Immediate Actions Required

### 1. Revoke All Exposed Credentials

#### Google Cloud Platform
- Log in to the GCP Console: https://console.cloud.google.com/
- Revoke and regenerate all API keys
- Delete and create new service account keys
- Update OAuth client secret

```bash
# Delete compromised service account keys
gcloud iam service-accounts keys delete 6833bc94f0e3ef8648efc1578caa23ba2b8a8a52 --iam-account=cherrybaby@agi-baby-cherry.iam.gserviceaccount.com
gcloud iam service-accounts keys delete f510256389008a55a6142d2429a185ebf216d685 --iam-account=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com

# Create new keys if needed (consider using workload identity federation instead)
gcloud iam service-accounts keys create key.json --iam-account=cherrybaby@agi-baby-cherry.iam.gserviceaccount.com
```

#### Figma
- Go to Figma account settings
- Revoke the exposed personal access token
- Generate a new token

#### SSH
- Change SSH passphrases on any systems using the exposed passphrase
- Check for unauthorized access to systems

### 2. Review Access Logs

- Check GCP Cloud Audit Logs for suspicious activity
- Verify Figma access logs for unauthorized design access
- Review deployment and compute logs

```bash
# Example: Check for activities using the compromised service account
gcloud logging read "protoPayload.authenticationInfo.principalEmail=vertex-agent@agi-baby-cherry.iam.gserviceaccount.com AND timestamp>=\"2025-04-20T00:00:00Z\"" --project=agi-baby-cherry
```

### 3. Implement Secure Credential Management

- Move credentials to Secret Manager
- Implement automatic credential rotation
- Use temporary credentials for service accounts where possible

```bash
# Example: Store new credentials in Secret Manager
echo -n "NEW_CLIENT_SECRET_HERE" | gcloud secrets create oauth-client-secret --data-file=- --project=agi-baby-cherry
```

### 4. Update IAM Roles

- Apply principle of least privilege to service accounts
- Consider removing owner access from vertex-agent service account
- Create dedicated service accounts for specific functions

```bash
# Remove overly permissive Owner role
gcloud projects remove-iam-policy-binding agi-baby-cherry \
  --member=serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com \
  --role=roles/owner

# Add more specific role
gcloud projects add-iam-policy-binding agi-baby-cherry \
  --member=serviceAccount:vertex-agent@agi-baby-cherry.iam.gserviceaccount.com \
  --role=roles/aiplatform.user
```

## Long-term Security Recommendations

1. **Implement Workload Identity Federation**: Replace service account keys with workload identity federation
2. **Set up Automated Key Rotation**: Configure automatic rotation for all secrets
3. **Use CI/CD Secret Management**: Integrate with secure CI/CD secret management 
4. **Implement Access Monitoring**: Set up alerts for suspicious access patterns
5. **Security Training**: Ensure team understands secure credential handling

## Documentation Updates

All infrastructure documentation should be updated to reflect new credential handling practices and to remove any references to the compromised credentials.

---

**IMPORTANT**: The project should be considered potentially compromised until all of the above steps have been completed. Monitor for unauthorized access and activities.
