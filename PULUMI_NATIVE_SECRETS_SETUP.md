# Pulumi Native Secret Management Setup Guide

## 🔐 **Pulumi Secret Management Best Practices**

You're absolutely right! Pulumi has excellent built-in secret management that's much better than custom solutions. Here's the complete setup:

## 📋 **Available Pulumi Secret Management Options**

### **1. Pulumi Config (Built-in Encryption)**
```bash
# Set encrypted secrets
pulumi config set --secret lambda_api_key "your_lambda_api_key"
pulumi config set --secret vercel_token "your_vercel_token"
pulumi config set --secret openai_api_key "your_openai_api_key"

# Set regular config
pulumi config set environment "production"
pulumi config set project_name "orchestra-ai"
```

### **2. Pulumi ESC (Environments, Secrets, Configuration)**
```bash
# Create ESC environment
pulumi env init ai-cherry/orchestra-production

# Add environment to stack
pulumi config env add ai-cherry/orchestra-production
```

### **3. External Provider Integration**
- **AWS Secrets Manager**: `pulumi-aws` provider
- **Azure Key Vault**: `pulumi-azure-native` provider  
- **HashiCorp Vault**: `pulumi-vault` provider
- **Google Secret Manager**: `pulumi-gcp` provider

## 🚀 **Quick Setup Commands**

### **Initialize Pulumi Project**
```bash
cd pulumi
export PATH=$PATH:$HOME/.pulumi/bin

# Initialize new stack (if not exists)
pulumi stack init production

# Or select existing stack
pulumi stack select production
```

### **Set All Required Secrets**
```bash
# Core API Keys (encrypted automatically)
pulumi config set --secret lambda_api_key "your_lambda_labs_api_key"
pulumi config set --secret github_token "your_github_token"
pulumi config set --secret vercel_token "your_vercel_token"

# AI/ML Service Keys
pulumi config set --secret openai_api_key "your_openai_api_key"
pulumi config set --secret portkey_api_key "your_portkey_api_key"
pulumi config set --secret anthropic_api_key "your_anthropic_api_key"

# Database Configuration
pulumi config set --secret database_url "postgresql://user:pass@host:5432/db"
pulumi config set --secret redis_url "redis://host:6379/0"

# Vector Database Keys
pulumi config set --secret pinecone_api_key "your_pinecone_api_key"
pulumi config set --secret weaviate_api_key "your_weaviate_api_key"

# Notion Integration
pulumi config set --secret notion_api_key "your_notion_api_key"

# Security Configuration
pulumi config set --secret jwt_secret_key "your_jwt_secret_key"
pulumi config set --secret orchestra_master_key "your_master_key"

# SSH Configuration
pulumi config set --secret ssh_private_key "$(cat ~/.ssh/id_rsa)"
pulumi config set --secret ssh_public_key "$(cat ~/.ssh/id_rsa.pub)"

# Non-secret configuration
pulumi config set environment "production"
pulumi config set project_name "orchestra-ai"
pulumi config set lambda_backend_url "http://150.136.94.139:8000"
```

### **Deploy with Native Secrets**
```bash
# Deploy using native secret management
pulumi up --stack production

# Use the new native secrets infrastructure
python infrastructure_with_native_secrets.py
```

## 🔍 **Test Secret Management**
```bash
# View configuration (secrets are masked)
pulumi config

# View with secrets revealed (be careful!)
pulumi config --show-secrets

# Test secret access in Python
python -c "
import pulumi
config = pulumi.Config()
print('Lambda API Key:', config.get_secret('lambda_api_key'))
print('Vercel Token:', config.get_secret('vercel_token'))
"
```

## 📊 **Benefits of Pulumi Native Secrets**

### **✅ Automatic Encryption**
- Secrets encrypted at rest in Pulumi state
- No custom encryption logic needed
- Industry-standard encryption algorithms

### **✅ Built-in Secret Providers**
- AWS Secrets Manager integration
- Azure Key Vault integration
- HashiCorp Vault integration
- Google Secret Manager integration

### **✅ ESC Integration**
- Centralized environment management
- Shared secrets across stacks
- Environment inheritance
- Policy-based access control

### **✅ CLI Integration**
- Easy secret management via CLI
- Masked output by default
- Secure secret sharing between team members

### **✅ Programmatic Access**
- Type-safe secret access in code
- Automatic Output handling
- No manual secret decryption

## 🎯 **Migration from Custom Secret Manager**

The new implementation (`pulumi_native_secrets.py`) provides:

1. **Drop-in replacement** for existing secret manager
2. **Backward compatibility** with existing code
3. **Enhanced security** with Pulumi encryption
4. **Better integration** with infrastructure code
5. **Team collaboration** features via ESC

## 🔧 **Advanced Configuration**

### **ESC Environment Definition**
```yaml
# orchestra-esc-env.yaml
values:
  lambda_api_key:
    fn::secret: ${LAMBDA_API_KEY}
  vercel_token:
    fn::secret: ${VERCEL_TOKEN}
  # ... other secrets
  
imports:
  - ai-cherry/shared-secrets
  - ai-cherry/orchestra-base-config
```

### **External Provider Example**
```python
import pulumi_aws as aws

# Get secret from AWS Secrets Manager
secret = aws.secretsmanager.get_secret_version(
    secret_id="orchestra-ai/production/api-keys"
)

# Use in infrastructure
lambda_api_key = secret.secret_string
```

This approach eliminates the custom secret manager and uses Pulumi's battle-tested secret management system!

