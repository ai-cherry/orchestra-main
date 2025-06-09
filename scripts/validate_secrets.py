#!/usr/bin/env python3
"""
Validate that all required secrets are configured for Orchestra AI.

This script checks environment variables and provides guidance on missing configuration.
"""

import os
import sys
from typing import List, Dict, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

# Define required and optional secrets
REQUIRED_SECRETS = {
    # Frontend Deployment
    'VERCEL_TOKEN': 'Vercel API token for deployments',
    'VERCEL_ORG_ID': 'Vercel organization ID',
    
    # Infrastructure
    'LAMBDA_LABS_API_KEY': 'Lambda Labs API key for instance provisioning',
    
    # Databases
    'POSTGRES_HOST': 'PostgreSQL server address',
    'POSTGRES_DB': 'PostgreSQL database name',
    'POSTGRES_USER': 'PostgreSQL username',
    'POSTGRES_PASSWORD': 'PostgreSQL password',
    'REDIS_URL': 'Redis connection string',
    
    # Vector Databases
    'PINECONE_API_KEY': 'Pinecone API key',
    'PINECONE_ENVIRONMENT': 'Pinecone environment/region',
    'WEAVIATE_URL': 'Weaviate instance URL',
    
    # Core AI Provider (at least one required)
    'OPENAI_API_KEY': 'OpenAI API key',
}

OPTIONAL_SECRETS = {
    # Additional AI Providers
    'ANTHROPIC_API_KEY': 'Anthropic Claude API key',
    'DEEPSEEK_API_KEY': 'DeepSeek API key',
    'PERPLEXITY_API_KEY': 'Perplexity AI API key',
    'GROK_API_KEY': 'xAI Grok API key',
    
    # Integrations
    'NOTION_API_KEY': 'Notion integration token',
    'SLACK_BOT_TOKEN': 'Slack bot OAuth token',
    'SLACK_WEBHOOK_URL': 'Slack webhook URL',
    'PORTKEY_API_KEY': 'Portkey AI gateway key',
    'PORTKEY_CONFIG_ID': 'Portkey configuration ID',
    
    # Monitoring
    'GRAFANA_API_KEY': 'Grafana API key',
    'GRAFANA_URL': 'Grafana instance URL',
    
    # Infrastructure as Code
    'PULUMI_ACCESS_TOKEN': 'Pulumi service token',
    'PULUMI_CONFIG_PASSPHRASE': 'Pulumi encryption passphrase',
    
    # Additional Services
    'ELEVEN_LABS_API_KEY': 'Eleven Labs voice synthesis',
    'SERP_API_KEY': 'Search engine results API',
    'STABILITY_API_KEY': 'Stability AI image generation',
    'PHANTOM_BUSTER_API_KEY': 'PhantomBuster automation',
    'APIFY_API_KEY': 'Apify web scraping',
    'ZENROWS_API_KEY': 'ZenRows web scraping',
    'HUBSPOT_API_KEY': 'HubSpot CRM integration',
}

def check_secret(name: str) -> Tuple[bool, str]:
    """Check if a secret is configured and return its status."""
    value = os.environ.get(name)
    if value:
        # Mask the value for security
        if len(value) > 8:
            masked = f"{value[:4]}...{value[-4:]}"
        else:
            masked = "***"
        return True, masked
    return False, "Not set"

def validate_secrets() -> bool:
    """Validate all secrets and return True if all required are present."""
    print(f"\n{BOLD}🔐 Orchestra AI Secrets Validation{RESET}\n")
    
    all_valid = True
    
    # Check required secrets
    print(f"{BOLD}Required Secrets:{RESET}")
    missing_required = []
    
    for name, description in REQUIRED_SECRETS.items():
        exists, value = check_secret(name)
        if exists:
            print(f"  {GREEN}✓{RESET} {name}: {value} - {description}")
        else:
            print(f"  {RED}✗{RESET} {name}: {RED}Missing{RESET} - {description}")
            missing_required.append(name)
            all_valid = False
    
    # Check optional secrets
    print(f"\n{BOLD}Optional Secrets:{RESET}")
    configured_optional = 0
    
    for name, description in OPTIONAL_SECRETS.items():
        exists, value = check_secret(name)
        if exists:
            print(f"  {GREEN}✓{RESET} {name}: {value} - {description}")
            configured_optional += 1
        else:
            print(f"  {YELLOW}○{RESET} {name}: Not configured - {description}")
    
    # Summary
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  Required: {len(REQUIRED_SECRETS) - len(missing_required)}/{len(REQUIRED_SECRETS)} configured")
    print(f"  Optional: {configured_optional}/{len(OPTIONAL_SECRETS)} configured")
    
    if missing_required:
        print(f"\n{RED}{BOLD}❌ Missing required secrets:{RESET}")
        for name in missing_required:
            print(f"  - {name}")
        print(f"\n{YELLOW}To fix:{RESET}")
        print("  1. For GitHub Actions: Add these as repository secrets")
        print("  2. For local development: Add to .env file")
        print("  3. For production: Configure in your deployment environment")
    else:
        print(f"\n{GREEN}{BOLD}✅ All required secrets are configured!{RESET}")
    
    # Check for AI provider
    ai_providers = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'DEEPSEEK_API_KEY', 'PERPLEXITY_API_KEY', 'GROK_API_KEY']
    has_ai_provider = any(os.environ.get(key) for key in ai_providers)
    
    if not has_ai_provider:
        print(f"\n{YELLOW}{BOLD}⚠️  Warning:{RESET} No AI provider API key found.")
        print("  At least one AI provider (OpenAI, Anthropic, etc.) is recommended.")
        all_valid = False
    
    # Additional checks
    print(f"\n{BOLD}Additional Checks:{RESET}")
    
    # Check Vercel project IDs
    if os.environ.get('VERCEL_TOKEN') and os.environ.get('VERCEL_ORG_ID'):
        project_ids = ['VERCEL_ADMIN_PROJECT_ID', 'VERCEL_DASHBOARD_PROJECT_ID']
        for pid in project_ids:
            if not os.environ.get(pid):
                print(f"  {YELLOW}⚠️{RESET}  {pid} not set - needed for specific project deployments")
    
    # Check database configuration
    if all(os.environ.get(key) for key in ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']):
        print(f"  {GREEN}✓{RESET} PostgreSQL fully configured")
    else:
        print(f"  {YELLOW}⚠️{RESET}  PostgreSQL partially configured")
    
    # Environment detection
    print(f"\n{BOLD}Environment:{RESET}")
    env = os.environ.get('NODE_ENV', 'development')
    print(f"  Current: {env}")
    
    if env == 'production':
        print(f"  {YELLOW}Note:{RESET} Running in production mode - ensure all secrets are from production systems")
    
    return all_valid

def main():
    """Main entry point."""
    try:
        if validate_secrets():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error during validation: {e}{RESET}")
        sys.exit(2)

if __name__ == "__main__":
    main() 