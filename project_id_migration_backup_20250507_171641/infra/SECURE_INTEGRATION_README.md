# Secure Figma and Vertex AI Integration

This documentation provides instructions on securely integrating Figma with Vertex AI using the infrastructure defined in this repository. It also includes guidance on addressing the exposed credentials and implementing secure credential management.

## 🚨 IMPORTANT: Security Notice

Sensitive credentials have been exposed and must be rotated immediately. Refer to `SECURITY_CREDENTIAL_ASSESSMENT.md` for a complete list of exposed credentials and remediation steps.

## Infrastructure Components

### 1. Terraform Configurations

Three Terraform configurations are provided:

- `vertex_workbench_config.tf`: Provisions a standalone Vertex AI Workbench with Firestore and Redis.
- `secure_vertex_figma_integration.tf`: Securely integrates Figma with Vertex AI.
- `vertex_workbench.tfvars`: Contains variables for the Terraform configurations.

### 2. Security Scripts

- `initialize_secure_secrets.sh`: Helper script for securely storing credentials in Secret Manager.

### 3. Documentation

- `VERTEX_WORKBENCH_README.md`: Instructions for using the standalone Vertex AI setup.
- `SECURITY_CREDENTIAL_ASSESSMENT.md`: Security alert and remediation for exposed credentials.
- `non_compliant_resources.md`: Analysis of non-compliant resources in the infrastructure.
- `cost_optimized_alternatives.md`: Cost optimization recommendations.
- `security_policy_exceptions.md`: Formal security exceptions for non-compliant resources.

## Secure Setup Process

### Step 1: Secure Your Credentials

1. First, rotate all exposed credentials as outlined in `SECURITY_CREDENTIAL_ASSESSMENT.md`.
2. Run the secret initialization script to securely store new credentials:

```bash
./infra/initialize_secure_secrets.sh agi-baby-cherry
```

This script will:
- Prompt for your new credentials or use environment variables
- Store them securely in Secret Manager
- Never log or expose the credentials in plaintext

### Step 2: Apply the Terraform Configuration

```bash
# Initialize Terraform
cd infra
terraform init

# Review the execution plan
terraform plan -var-file=vertex_workbench.tfvars

# Apply the configuration
terraform apply -var-file=vertex_workbench.tfvars
```

## Figma-Vertex AI Integration Architecture

### Architecture Overview

The secure integration provides:

1. **Dedicated Service Account**: A service account with minimal required permissions.
2. **Secure Credential Storage**: All credentials stored in Secret Manager, not in code.
3. **Vertex AI Notebook**: Preconfigured with Figma integration code.
4. **Asset Storage**: A GCS bucket for Figma assets.
5. **Automatic Secret Rotation**: A Cloud Scheduler job to periodically rotate secrets.

### Security Features

- **Zero Plaintext Credentials**: No credentials are stored in code.
- **Principle of Least Privilege**: Service account has minimal permissions.
- **Secure Bootup**: Notebook uses a startup script to securely access credentials.
- **Regular Secret Rotation**: Automated monthly credential rotation.
- **Enhanced VM Security**: Shielded VM with secure boot enabled.

## Using the Integration

### Accessing the Vertex AI Notebook

1. After applying the Terraform configuration, the notebook URL will be output.
2. Navigate to the URL in your browser.
3. The notebook comes with a pre-installed `secure_figma_vertex_integration.py` module.

### Integrating Figma Designs with Vertex AI

```python
# Example Python code in the notebook
from secure_figma_vertex_integration import get_figma_file, process_figma_with_vertex

# Get Figma file data
figma_data = get_figma_file("YOUR_FIGMA_FILE_ID")

# Process with Vertex AI
results = process_figma_with_vertex(figma_data)
```

### Customizing the Integration

The integration code is a template that securely handles credentials. You can extend the `process_figma_with_vertex` function based on your specific needs:

- Generate code from Figma designs
- Analyze design patterns
- Extract design tokens
- Create 3D representations

## Security Best Practices

1. **Rotate Credentials Regularly**: Use the automated rotation or manually rotate every 30-60 days.
2. **Monitor Access Logs**: Regularly check GCP Cloud Audit Logs for suspicious activity.
3. **Review IAM Permissions**: Periodically review service account permissions.
4. **Update Dependencies**: Keep libraries and APIs up to date.
5. **Use Workload Identity**: Consider transitioning to Workload Identity Federation for service accounts.

## Troubleshooting

### Secret Access Issues

If the notebook can't access secrets:

```bash
# Check service account has secretAccessor role
gcloud projects get-iam-policy agi-baby-cherry \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:figma-vertex-integration@agi-baby-cherry.iam.gserviceaccount.com"
```

### Figma API Issues

If you encounter Figma API errors:

1. Verify your PAT has the correct permissions in Figma
2. Check network connectivity from the notebook
3. Ensure API usage is within Figma's rate limits

## Maintenance

### Adding New Secrets

```bash
# Create a new secret
echo -n "NEW_SECRET_VALUE" | gcloud secrets create new-secret-name \
  --data-file=- --project=agi-baby-cherry

# Grant the service account access
gcloud secrets add-iam-policy-binding new-secret-name \
  --member="serviceAccount:figma-vertex-integration@agi-baby-cherry.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=agi-baby-cherry
```

### Updating the Integration Code

The notebook's integration code is created by the startup script. To update it:

1. Modify the `post_startup_script` in `secure_vertex_figma_integration.tf`
2. Apply the Terraform changes
3. Restart the notebook instance

## Conclusion

This secure integration provides a way to connect Figma with Vertex AI without exposing credentials in code. By following the security best practices outlined in this document, you can maintain a secure environment for your design and AI workloads.
