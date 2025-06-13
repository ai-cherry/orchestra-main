# 🚀 IaC Agent Complete Empowerment Guide

## Overview
This guide provides step-by-step instructions to fully empower the Orchestra AI Infrastructure as Code (IaC) Agent to manage all external API environments.

## 🎯 Services Managed by IaC Agent

1. **Lambda Labs Cloud** - GPU compute instances
2. **Pulumi** - Infrastructure as Code management
3. **GitHub** - Repository and CI/CD automation
4. **Pinecone** - Vector database service
5. **Weaviate** - Self-hosted vector store
6. **Portkey** - AI gateway and LLM routing

## 📋 Prerequisites

### Required API Keys
Obtain the following API keys from their respective platforms:

| Service | Sign Up URL | API Key Location |
|---------|-------------|------------------|
| Lambda Labs | https://cloud.lambdalabs.com | Settings → API Keys |
| Pulumi | https://app.pulumi.com | Settings → Access Tokens |
| GitHub | https://github.com | Settings → Developer Settings → Personal Access Tokens |
| Pinecone | https://app.pinecone.io | API Keys section |
| Weaviate | https://console.weaviate.cloud | (Optional for self-hosted) |
| Portkey | https://app.portkey.ai | Settings → API Keys |

## 🛠️ Installation Steps

### 1. Run the Setup Script
```bash
# Make the script executable
chmod +x scripts/setup_iac_agent.sh

# Run the setup
./scripts/setup_iac_agent.sh
```

This script will:
- Install Pulumi CLI
- Install GitHub CLI
- Install Python dependencies
- Check for API keys
- Create configuration templates
- Set up Cursor workspace

### 2. Configure API Keys

If any API keys are missing, the script creates `.env.iac`. Fill it out:

```bash
# Edit the environment file
nano .env.iac

# Add your API keys:
LAMBDA_LABS_API_KEY=your_actual_key_here
PULUMI_ACCESS_TOKEN=your_actual_token_here
GITHUB_TOKEN=ghp_your_actual_token_here
PINECONE_API_KEY=your_actual_key_here
PORTKEY_API_KEY=pk-your_actual_key_here

# Source the environment
source .env.iac
```

### 3. Update Cursor Configuration

The enhanced agent configuration is in `.cursor/agents/iac_agent_enhanced.yaml`. To activate it:

1. **Copy to replace the original:**
   ```bash
   cp .cursor/agents/iac_agent_enhanced.yaml .cursor/agents/iac_agent.yaml
   ```

2. **Restart Cursor IDE**
   - Quit Cursor completely (Cmd+Q on macOS)
   - Reopen Cursor

### 4. Test the Unified API Client

```bash
# Test all service connections
python scripts/iac_tools/unified_api_client.py status

# Expected output:
# ✅ Lambda_labs: Connected
# ✅ Pulumi: Connected
# ✅ Github: Connected
# ✅ Pinecone: Connected
# ✅ Weaviate: Connected
# ✅ Portkey: Connected
# ✅ Redis: Connected
```

## 🎮 Using the Empowered IaC Agent

### In Cursor Chat

Once configured, you can use natural language commands:

**Lambda Labs GPU Management:**
```
"Deploy a GPU instance with 1x A100 for model training"
"List all running Lambda Labs instances"
"Terminate idle GPU instances to save costs"
```

**Pulumi Infrastructure:**
```
"Create a new Pulumi stack for production"
"Deploy the complete Orchestra AI infrastructure"
"Show me the cost estimate for current resources"
```

**Vector Database Management:**
```
"Create a Pinecone index for 1536-dimension embeddings"
"Set up Weaviate schema for document storage"
"Scale Pinecone to handle 10M vectors"
```

**Portkey Configuration:**
```
"Configure Portkey routing for OpenAI and Anthropic"
"Set up fallback from GPT-4 to Claude"
"Add cost limits and rate limiting"
```

### Command Line Tools

**Lambda Labs CLI:**
```bash
# List instances
python scripts/iac_tools/lambda_labs_cli.py list

# Create instance
python scripts/iac_tools/lambda_labs_cli.py create gpu_1x_a100 us-west-2 my-ssh-key

# Terminate instance
python scripts/iac_tools/lambda_labs_cli.py terminate instance-id
```

**Unified API Client:**
```bash
# Check all services
python scripts/iac_tools/unified_api_client.py status

# List Lambda instances
python scripts/iac_tools/unified_api_client.py lambda-list

# List Pinecone indexes
python scripts/iac_tools/unified_api_client.py pinecone-list
```

## 🔧 Advanced Configuration

### Custom Automation Rules

Add to `.cursor/agents/iac_agent_enhanced.yaml`:

```yaml
automation_rules:
  - trigger: "deploy production"
    actions:
      - create_production_stack
      - provision_gpu_cluster
      - setup_vector_databases
      - configure_portkey_routing
      - enable_monitoring
```

### Cost Controls

Set monthly limits in the agent config:

```yaml
constraints:
  cost_limit_monthly: 5000
  gpu_instance_limit: 3
  require_approval_above: 1000
```

### Monitoring Integration

The agent automatically tracks:
- GPU utilization and costs
- Vector database performance
- API request counts
- Token usage across LLMs

## 🚨 Troubleshooting

### API Key Issues
```bash
# Verify environment variables
env | grep -E "(LAMBDA|PULUMI|GITHUB|PINECONE|PORTKEY)"

# Re-source environment
source .env.iac
```

### Cursor Not Recognizing Agent
1. Ensure `.cursor/agents/iac_agent.yaml` exists
2. Check workspace settings: `.vscode/settings.json`
3. Restart Cursor with fresh terminal

### Service Connection Failures
```bash
# Debug specific service
python scripts/iac_tools/unified_api_client.py status

# Check network connectivity
curl -I https://cloud.lambdalabs.com/api/v1
```

## 📊 Monitoring & Reporting

The IaC agent provides automated reporting:

```bash
# Generate infrastructure report
pulumi stack export | python -m json.tool

# Cost analysis
python scripts/iac_tools/cost_analyzer.py

# Service health dashboard
python scripts/iac_tools/unified_api_client.py status
```

## 🔐 Security Best Practices

1. **Never commit `.env.iac` to git**
   ```bash
   echo ".env.iac" >> .gitignore
   ```

2. **Use Pulumi secrets for sensitive data**
   ```bash
   pulumi config set --secret api-key $API_KEY
   ```

3. **Rotate API keys regularly**
   - Lambda Labs: Every 90 days
   - GitHub: Every 60 days
   - Others: Follow platform recommendations

4. **Enable MFA on all platforms**

## 🎯 Next Steps

1. **Deploy Your First Resource:**
   ```
   In Cursor: "Deploy a small GPU instance for testing"
   ```

2. **Set Up Vector Database:**
   ```
   In Cursor: "Create production Pinecone index for Orchestra AI"
   ```

3. **Configure AI Gateway:**
   ```
   In Cursor: "Set up Portkey with OpenAI primary and Anthropic fallback"
   ```

## 📚 Additional Resources

- [Lambda Labs API Docs](https://cloud.lambdalabs.com/api/v1/docs)
- [Pulumi Python SDK](https://www.pulumi.com/docs/languages-sdks/python/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Portkey Documentation](https://docs.portkey.ai/)

---

**Support:** For issues or questions, check the logs in `logs/iac_agent/` or run diagnostics with `python scripts/iac_tools/unified_api_client.py status` 