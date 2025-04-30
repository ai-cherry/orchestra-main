#!/usr/bin/env python3
"""
Test script for environmental separation configuration.

This script validates that our Terraform environment configuration correctly handles:
1. Environment-specific secrets
2. Common secrets across environments
3. Service account access permissions by environment
"""

import os
import sys
import json
import re
from typing import Dict, List, Set, Any

# Configuration to validate
ENV_CONFIG = {
    "dev": {
        "required_secrets": [
            "openai-api-key-dev",
            "anthropic-api-key-dev",
            "redis-auth-dev",
            "db-credentials-dev",
            "test-data-key-dev"
        ],
        "forbidden_secrets": [
            "oauth-client-secret-dev",  # Production-only secret should not be in dev
            "certificate-key-dev",      # Production-only secret should not be in dev
            "alert-webhook-key-dev"     # Production-only secret should not be in dev
        ],
        "service_accounts": [
            "orchestra-dev-sa",
            "orchestrator-test-sa"
        ]
    },
    "prod": {
        "required_secrets": [
            "openai-api-key-prod",
            "anthropic-api-key-prod",
            "redis-auth-prod",
            "db-credentials-prod",
            "oauth-client-secret-prod", 
            "alert-webhook-key-prod"
        ],
        "forbidden_secrets": [
            "test-data-key-prod",       # Dev-only secret should not be in prod
            "mock-service-key-prod",    # Dev-only secret should not be in prod
            "service-account-keys-prod" # Dev-only secret should not be in prod
        ],
        "service_accounts": [
            "orchestra-prod-sa",
            "orchestrator-monitoring-sa"
        ]
    }
}

def extract_terraform_resources(tf_file: str) -> Dict[str, Any]:
    """Parse Terraform file and extract resource configuration by environment."""
    resources = {
        "dev": {
            "secrets": [],
            "service_accounts": set(),
            "iam_bindings": []
        },
        "prod": {
            "secrets": [],
            "service_accounts": set(),
            "iam_bindings": []
        }
    }
    
    with open(tf_file, 'r') as f:
        content = f.read()

    # Extract common secrets (apply to both environments)
    common_categories = ["llm_api_keys", "tool_api_keys", "infrastructure"]
    
    for category in common_categories:
        regex = f'"{category}"\\s*=\\s*{{([^}}]*)}}' 
        matches = re.findall(regex, content, re.DOTALL)
        
        for match in matches:
            key_matches = re.findall(r'"([^"]+)"\s*=', match)
            resources["dev"]["secrets"].extend([f"{key}-dev" for key in key_matches])
            resources["prod"]["secrets"].extend([f"{key}-prod" for key in key_matches])
    
    # Extract dev-only secrets
    dev_categories = ["testing", "gcp_secrets"]
    
    for category in dev_categories:
        regex = f'"{category}"\\s*=\\s*{{([^}}]*)}}' 
        matches = re.findall(regex, content, re.DOTALL)
        
        for match in matches:
            key_matches = re.findall(r'"([^"]+)"\s*=', match)
            resources["dev"]["secrets"].extend([f"{key}-dev" for key in key_matches])
            # These should NOT be in prod
    
    # Extract prod-only secrets
    prod_categories = ["security", "monitoring"]
    
    for category in prod_categories:
        regex = f'"{category}"\\s*=\\s*{{([^}}]*)}}' 
        matches = re.findall(regex, content, re.DOTALL)
        
        for match in matches:
            key_matches = re.findall(r'"([^"]+)"\s*=', match)
            resources["prod"]["secrets"].extend([f"{key}-prod" for key in key_matches])
            # These should NOT be in dev

    # Find service accounts by environment
    dev_sa_pattern = r'"orchestra-dev-sa@[^"]+"'
    prod_sa_pattern = r'"orchestra-prod-sa@[^"]+"'
    
    # Extract service accounts
    for match in re.finditer(r'"([^"]+@[^"]+\.iam\.gserviceaccount\.com)"', content):
        account = match.group(1)
        if "dev" in account:
            resources["dev"]["service_accounts"].add(account)
        if "prod" in account or "monitoring" in account:
            resources["prod"]["service_accounts"].add(account)

    return resources

def validate_environment_separation(resources: Dict[str, Any], env: str) -> List[str]:
    """Validate environment-specific configuration."""
    issues = []
    
    # Check required secrets
    env_resources = resources[env]
    for secret in ENV_CONFIG[env]["required_secrets"]:
        if secret not in env_resources["secrets"]:
            issues.append(f"Missing required secret for {env}: {secret}")

    # Check forbidden secrets
    for secret in ENV_CONFIG[env]["forbidden_secrets"]:
        if secret in env_resources["secrets"]:
            issues.append(f"Found forbidden secret in {env}: {secret}")

    # Check service accounts
    for sa in ENV_CONFIG[env]["service_accounts"]:
        found = False
        for account in env_resources["service_accounts"]:
            if sa in account:
                found = True
                break
        if not found:
            issues.append(f"Missing service account for {env}: {sa}")

    return issues

def main():
    """Main function to validate environment configuration."""
    # Find the environments.tf file
    environments_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "environments.tf")
    if not os.path.exists(environments_file):
        print(f"Error: environments.tf file not found at {environments_file}")
        return 1

    print(f"Validating environment configuration in {environments_file}...")
    resources = extract_terraform_resources(environments_file)
    
    # Print summary of configuration
    print(f"Found {len(resources['dev']['secrets'])} dev secrets defined")
    print(f"Found {len(resources['prod']['secrets'])} prod secrets defined")
    
    # For debugging - print all secrets found by environment
    print("\nDetected DEV secrets:")
    for secret in sorted(resources['dev']['secrets']):
        print(f"  - {secret}")
        
    print("\nDetected PROD secrets:")
    for secret in sorted(resources['prod']['secrets']):
        print(f"  - {secret}")

    # Validate each environment
    all_issues = []
    for env in ["dev", "prod"]:
        print(f"\nValidating {env} environment configuration...")
        issues = validate_environment_separation(resources, env)
        if issues:
            all_issues.extend(issues)
            print(f"❌ Found {len(issues)} issues with {env} environment:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"✅ No issues found with {env} environment configuration")

    # Final status
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} total issues with environment configuration")
        return 1
    else:
        print("\n✅ All environment configurations validated successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())