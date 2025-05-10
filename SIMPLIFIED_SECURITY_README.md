# Simplified Security for Single-Developer Projects

This document outlines the streamlined security approach designed for single-developer projects. It explains which security measures have been simplified, how to use the new tools, and when to choose between more secure options and simplified alternatives.

## Overview

The AI Orchestra project was originally designed with enterprise-level security suitable for team development environments. For a single-developer project, many of these security measures create unnecessary friction during development and deployment. This simplified approach:

1. Maintains essential security protections
2. Reduces deployment friction
3. Simplifies GitHub integration
4. Creates development shortcuts for faster iteration

## Simplified Components

### GitHub Authentication

**Original approach:** Multiple token types (classic and fine-grained), organization-level secrets, and complex authentication utility.

**Simplified approach:** 
- Single GitHub token management
- Repository-level secrets instead of organization-level
- Simplified authentication script

**Files:**
- `github_auth.sh.simplified` - Streamlined GitHub authentication utility

### GitHub Secrets Management

**Original approach:** Extensive list of required organization secrets with strict verification.

**Simplified approach:**
- Reduced set of essential secrets
- Repository-level secrets instead of organization-level
- Interactive creation of missing secrets

**Files:**
- `verify_github_secrets.sh.simplified` - Streamlined verification script

### GCP Authentication

**Original approach:** Workload Identity Federation (WIF) with complex setup and verification.

**Simplified approach:**
- Option to use WIF (more secure) or Service Account Keys (simpler)
- Interactive setup process
- Clear instructions for both approaches

**Files:**
- `setup_wif.sh.simplified` - Provides both authentication options

### GitHub Actions Workflows

**Original approach:** Complex workflows with extensive verification steps.

**Simplified approach:**
- Streamlined deployment workflow
- Fewer verification steps
- Option to skip tests in development

**Files:**
- `.github/workflows/simplified-deploy-template.yml` - Streamlined workflow template

### Web Security

**Original approach:** Comprehensive CSRF protection, extensive error handling.

**Simplified approach:**
- Development mode with optional CSRF bypass
- Simplified token validation
- Environment variable control

**Files:**
- `wif_implementation/csrf_protection_dev.py` - Development-friendly CSRF protection

## How to Use

### Setting Up GitHub Authentication

1. Use the simplified GitHub authentication script:

```bash
# Make the script executable
chmod +x github_auth.sh.simplified

# Run the script
./github_auth.sh.simplified
```

This script will:
- Check for a GitHub token in environment variables or stored credentials
- Prompt you to enter a token if none is found
- Save the token for future use
- Authenticate with GitHub

### Verifying GitHub Secrets

1. Use the simplified GitHub secrets verification script:

```bash
# Make the script executable
chmod +x verify_github_secrets.sh.simplified

# Run the script
./verify_github_secrets.sh.simplified
```

This script will:
- Check for essential GitHub repository secrets
- Offer to create missing secrets interactively
- Verify that all required secrets are available

### Setting Up GCP Authentication

1. Use the simplified WIF setup script:

```bash
# Make the script executable
chmod +x setup_wif.sh.simplified

# Run the script
./setup_wif.sh.simplified
```

This script will:
- Check for GCP authentication
- Prompt you to choose between WIF (more secure) or Service Account Keys (simpler)
- Configure the selected authentication method
- Set up GitHub repository secrets
- Provide instructions for using the authentication in GitHub Actions

### Deploying with GitHub Actions

1. Copy the simplified workflow template:

```bash
# Create a new workflow file based on the template
cp .github/workflows/simplified-deploy-template.yml .github/workflows/your-service-deploy.yml
```

2. Edit the workflow file to customize it for your service:
   - Update the service name
   - Customize the file paths
   - Adjust the deployment parameters

### Using Development Mode for Web Security

1. Set environment variables to enable development mode:

```bash
# Enable development mode
export WIF_DEV_MODE=true

# Optionally bypass CSRF protection in development
export WIF_BYPASS_CSRF=true
```

2. Import the development-friendly CSRF protection in your FastAPI app:

```python
from wif_implementation.csrf_protection_dev import csrf_protect_dev

# Use the development-friendly CSRF protection
@app.post("/api/resource")
def create_resource(request: Request, _: None = Depends(csrf_protect_dev)):
    # Your code here
    pass
```

## When to Use Secure vs. Simplified Options

### Use More Secure Options When:

- Working on sensitive features
- Preparing for production deployment
- Handling confidential data
- Implementing authentication features
- Working with external APIs that require strong security

### Use Simplified Options When:

- Rapid prototyping and iteration
- Local development with no sensitive data
- Working on UI/UX features
- Testing and debugging
- Setting up initial project structure

## Toggling Between Development and Production Modes

### Persistent Mode Management

To avoid confusion when switching between development and production modes, we've created a mode indicator that:

1. Displays your current mode in your shell prompt
2. Persists your mode setting across terminal sessions
3. Provides simple commands to switch modes
4. Updates all necessary environment variables automatically

To set up the mode indicator:

```bash
# Make the script executable
chmod +x mode_indicator.sh

# Run the script and follow the prompts
./mode_indicator.sh
```

After setup, you'll see a colored mode indicator in your shell prompt:
- **[DEV]** - You're in development mode
- **[DEV-BYPASS]** - You're in development mode with CSRF protection bypassed
- **[PROD]** - You're in production mode

You can switch modes at any time using these commands:

```bash
# Switch to development mode
dev_mode

# Switch to development mode with CSRF bypass
dev_bypass_mode

# Switch to production mode
prod_mode

# Check your current mode
show_mode
```

### Manual Environment Variable Setting

If you prefer not to use the mode indicator, you can still toggle between modes manually:

```bash
# Development mode with CSRF bypassed
export WIF_DEV_MODE=true
export WIF_BYPASS_CSRF=true

# Development mode with CSRF enabled
export WIF_DEV_MODE=true
export WIF_BYPASS_CSRF=false

# Production mode (default)
export WIF_DEV_MODE=false
```

### GitHub Actions and Environment Management

Our simplified GitHub Actions workflow provides flexible environment handling that's ideal for single-developer projects:

#### Environment Selection

Toggle between development and production deployments using the `environment` parameter:

```bash
# Manually trigger workflow with environment selection
gh workflow run your-service-deploy.yml -f environment=dev

# Or push to main branch for automatic deployment to dev
git push origin main
```

#### How GitHub Environments Work

The simplified workflow manages environments through:

1. **Default Environment**: Pushes to the main branch automatically deploy to the 'dev' environment
   ```yaml
   environment: ${{ github.event.inputs.environment || 'dev' }}
   ```

2. **Environment Variables**: The environment name is passed to your application
   ```yaml
   --set-env-vars=ENV=${{ github.event.inputs.environment || 'dev' }}
   ```

3. **Authentication Method Flexibility**: 
   - Production can use the more secure Workload Identity Federation
   - Development can use the simpler Service Account key approach

#### Recommended Workflow for Single Developer

For a streamlined experience as a single developer:

1. **Daily Development**: Use local development with simplified security
2. **Feature Testing**: Push to main for automatic deployment to 'dev' environment
3. **Production Release**: Manually trigger workflow with 'prod' environment selected

#### Authentication by Environment

The workflow supports different authentication methods based on security needs:

**For Development**: 
```yaml 
# Simpler method using service account key
- name: Google Auth via Service Account Key
  if: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER == '' }}
  uses: google-github-actions/auth@v2
  with:
    credentials_json: ${{ secrets.GCP_SA_KEY }}
```

**For Production**:
```yaml
# More secure method using Workload Identity Federation
- name: Google Auth via Workload Identity Federation
  if: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER != '' }}
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
```

## Security Best Practices (Even for Single Developers)

Even in a single-developer project, some security practices should still be maintained:

1. **Don't commit secrets to Git**: Always use GitHub secrets or environment variables
2. **Rotate tokens periodically**: Change your personal access tokens every few months
3. **Use HTTPS for Git**: Avoid HTTP for repository operations
4. **Keep dependencies updated**: Regularly update dependencies to patch security vulnerabilities
5. **Backup sensitive credentials**: Store a secure backup of important credentials
6. **Use strong passwords**: Generate and use strong passwords for all services
7. **Enable 2FA**: Use two-factor authentication for GitHub and GCP accounts

## Restoring Full Security

If your project grows beyond a single developer or needs enhanced security, you can restore the full security implementation:

1. Use the original scripts instead of the simplified versions
2. Set up organization-level secrets
3. Implement Workload Identity Federation
4. Use the comprehensive GitHub Actions workflow templates
5. Enable full CSRF protection in all environments

## Files Overview

| Original File | Simplified File | Description |
|---------------|-----------------|-------------|
| `github_auth.sh` | `github_auth.sh.simplified` | GitHub authentication utility |
| `verify_github_secrets.sh` | `verify_github_secrets.sh.simplified` | GitHub secrets verification |
| `setup_wif.sh` | `setup_wif.sh.simplified` | GCP authentication setup |
| `.github/workflows/wif-deploy-template.yml` | `.github/workflows/simplified-deploy-template.yml` | GitHub Actions workflow template |
| `wif_implementation/csrf_protection.py` | `wif_implementation/csrf_protection_dev.py` | CSRF protection implementation |
