#!/usr/bin/env python
"""
Script to set up Portkey virtual keys and configurations using an admin key.

This script connects to the Portkey Management API using the provided admin key,
creates virtual keys for various LLM providers, and sets up gateway configurations
for different routing strategies.

Usage:
    python scripts/setup_portkey_virtual_keys.py

Environment Variables:
    MASTER_PORTKEY_ADMIN_KEY: The Portkey Admin API key (required)
    OPENAI_API_KEY: OpenAI API key (optional)
    ANTHROPIC_API_KEY: Anthropic API key (optional)
    MISTRAL_API_KEY: Mistral API key (optional)
    COHERE_API_KEY: Cohere API key (optional)
    ... (other provider keys)
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from packages.shared.src.portkey_admin.client import PortkeyAdminClient, PortkeyAdminException
except ImportError:
    print("ERROR: Could not import PortkeyAdminClient. Make sure you're running this script from the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("portkey-setup")

# Provider configurations
PROVIDERS = [
    {
        "name": "OpenAI",
        "env_key": "OPENAI_API_KEY",
        "provider_id": "openai",
        "default_model": "gpt-4",
        "budget_limit": 100.0,
        "description": "OpenAI provider for GPT models"
    },
    {
        "name": "Anthropic",
        "env_key": "ANTHROPIC_API_KEY",
        "provider_id": "anthropic",
        "default_model": "claude-3-opus",
        "budget_limit": 100.0,
        "description": "Anthropic provider for Claude models"
    },
    {
        "name": "Mistral",
        "env_key": "MISTRAL_API_KEY",
        "provider_id": "mistral",
        "default_model": "mistral-large",
        "budget_limit": 100.0,
        "description": "Mistral provider for Mistral models"
    },
    {
        "name": "Cohere",
        "env_key": "COHERE_API_KEY",
        "provider_id": "cohere",
        "default_model": "command-r",
        "budget_limit": 100.0,
        "description": "Cohere provider for Command models"
    },
    {
        "name": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "provider_id": "openrouter",
        "default_model": "openai/gpt-3.5-turbo",
        "budget_limit": 100.0,
        "description": "OpenRouter for multi-provider access"
    },
    {
        "name": "Perplexity",
        "env_key": "PERPLEXITY_API_KEY",
        "provider_id": "perplexity",
        "default_model": "sonar-small-online",
        "budget_limit": 100.0,
        "description": "Perplexity provider for Sonar models"
    },
    {
        "name": "DeepSeek",
        "env_key": "DEEPSEEK_API_KEY",
        "provider_id": "deepseek",
        "default_model": "deepseek-coder",
        "budget_limit": 100.0,
        "description": "DeepSeek provider for code generation"
    },
    {
        "name": "Codestral",
        "env_key": "CODESTRAL_API_KEY",
        "provider_id": "codestral",
        "default_model": "codestral-latest",
        "budget_limit": 100.0,
        "description": "Codestral provider for code models"
    }
]

def get_env_value(key: str) -> Optional[str]:
    """Get environment variable, checking for GitHub organization secrets format."""
    # First, try the direct environment variable
    value = os.environ.get(key)
    if value and not value.startswith("${{") and not value.endswith("}}"):
        logger.info(f"Using environment variable for {key}")
        return value
    
    # Check for GitHub Actions secrets format: ${{ secrets.KEY_NAME }}
    github_secret_pattern = r'\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}'
    
    # Check the direct key first (might be in GitHub format)
    if value and value.startswith("${{") and value.endswith("}}"):
        import re
        match = re.search(github_secret_pattern, value)
        if match:
            secret_name = match.group(1)
            logger.info(f"Detected GitHub secret format for {key}: {secret_name}")
            
            # Try to get the actual value from the environment
            actual_value = os.environ.get(secret_name)
            if actual_value:
                logger.info(f"Found value for GitHub secret: {secret_name}")
                return actual_value
    
    # Check if there's an organization-level secret with prefix
    org_key = f"ORG_{key}"
    org_value = os.environ.get(org_key)
    if org_value:
        logger.info(f"Using organization-level secret: {org_key}")
        return org_value
    
    # Check for common organization secret naming conventions
    for prefix in ["ORG_", "GH_", "GITHUB_", ""]:
        # Try with PORTKEY prefix for Portkey-specific keys
        portkey_key = f"{prefix}PORTKEY_{key}"
        portkey_value = os.environ.get(portkey_key)
        if portkey_value:
            logger.info(f"Using Portkey-specific secret: {portkey_key}")
            return portkey_value
    
    logger.warning(f"Could not find value for {key} in environment or organization secrets")
    return None

def get_admin_key() -> str:
    """Get the Portkey admin key from environment variables or GitHub organization secrets."""
    # Try different possible names for the admin key
    possible_keys = [
        "MASTER_PORTKEY_ADMIN_KEY",
        "PORTKEY_ADMIN_KEY",
        "PORTKEY_API_KEY",  # Sometimes the main API key has admin privileges
        "PORTKEY_KEY",
        "PORTKEY_SECRET"
    ]
    
    admin_key = None
    for key in possible_keys:
        value = get_env_value(key)
        if value:
            logger.info(f"Found Portkey admin key using: {key}")
            admin_key = value
            break
    
    if not admin_key:
        # Check specifically for organization-level secrets
        org_secrets = [
            "ORG_PORTKEY_API_KEY",
            "ORG_PORTKEY_KEY",
            "ORG_PORTKEY_SECRET",
            "ORG_PORTKEY_ADMIN_KEY",
            "GITHUB_PORTKEY_API_KEY",
            "GH_PORTKEY_API_KEY"
        ]
        
        for secret in org_secrets:
            value = os.environ.get(secret)
            if value:
                logger.info(f"Found Portkey admin key in organization secret: {secret}")
                admin_key = value
                break
    
    if not admin_key:
        # Try GitHub Actions secret syntax
        for env_key, env_value in os.environ.items():
            if env_value.startswith("${{") and "secrets.PORTKEY" in env_value:
                logger.info(f"Found potential GitHub Actions secret reference: {env_key}")
                # Extract the actual secret name from the GitHub syntax
                import re
                match = re.search(r'secrets\.([A-Za-z0-9_]+)', env_value)
                if match:
                    secret_name = match.group(1)
                    logger.info(f"Attempting to use secret: {secret_name}")
                    secret_value = os.environ.get(secret_name)
                    if secret_value:
                        admin_key = secret_value
                        break
    
    if not admin_key:
        logger.error("Could not find Portkey admin key in environment variables or GitHub secrets")
        logger.info("Please set it using one of the following methods:")
        logger.info("1. Environment variable: export MASTER_PORTKEY_ADMIN_KEY=your_portkey_admin_key")
        logger.info("2. GitHub organization secret: Configure ORG_PORTKEY_API_KEY in your organization settings")
        sys.exit(1)
    
    return admin_key

def create_provider_virtual_keys(client: PortkeyAdminClient) -> Dict[str, str]:
    """Create virtual keys for providers and return a mapping of provider_id to virtual key ID."""
    virtual_keys = {}
    
    # List existing keys first
    try:
        existing_keys = client.list_virtual_keys()
        logger.info(f"Found {len(existing_keys)} existing virtual keys")
    except Exception as e:
        logger.error(f"Failed to list existing keys: {e}")
        existing_keys = []
    
    # Create a mapping of provider_id to existing key ID
    existing_keys_map = {key.provider: key.id for key in existing_keys}
    
    # Go through each provider and create a virtual key if API key is available
    for provider in PROVIDERS:
        provider_id = provider["provider_id"]
        env_key = provider["env_key"]
        name = provider["name"]
        
        # Check if we already have a key for this provider
        if provider_id in existing_keys_map:
            logger.info(f"Using existing virtual key for {name}: {existing_keys_map[provider_id]}")
            virtual_keys[provider_id] = existing_keys_map[provider_id]
            continue
        
        # Get the API key from environment
        api_key = get_env_value(env_key)
        if not api_key:
            logger.warning(f"No API key found for {name} ({env_key}). Skipping.")
            continue
        
        try:
            # Create a virtual key
            key = client.create_virtual_key(
                name=f"{name}-Production",
                provider_key=api_key,
                provider=provider_id,
                description=provider["description"],
                budget_limit=provider["budget_limit"]
            )
            
            logger.info(f"Created virtual key for {name}: {key.id}")
            virtual_keys[provider_id] = key.id
        except Exception as e:
            logger.error(f"Failed to create virtual key for {name}: {e}")
    
    return virtual_keys

def create_gateway_configs(client: PortkeyAdminClient, virtual_keys: Dict[str, str]) -> Dict[str, str]:
    """Create gateway configurations for different routing strategies."""
    gateway_configs = {}
    
    if not virtual_keys:
        logger.warning("No virtual keys available. Skipping gateway configurations.")
        return gateway_configs
    
    # Build provider configs list for gateway configurations
    provider_configs = []
    for provider in PROVIDERS:
        provider_id = provider["provider_id"]
        if provider_id in virtual_keys:
            provider_configs.append({
                "virtual_key": virtual_keys[provider_id],
                "models": [provider["default_model"]]
            })
    
    if not provider_configs:
        logger.warning("No provider configs available. Skipping gateway configurations.")
        return gateway_configs
    
    # Create fallback gateway configuration
    try:
        fallback_config = client.create_gateway_config(
            name="Orchestra-Fallback",
            routing_strategy="fallback",
            provider_configs=provider_configs,
            cache_config={"enabled": True, "ttl": 3600}
        )
        
        logger.info(f"Created fallback gateway config: {fallback_config.id}")
        gateway_configs["fallback"] = fallback_config.id
    except Exception as e:
        logger.error(f"Failed to create fallback gateway config: {e}")
    
    # Create load balancing gateway configuration
    # Add weights to provider configs for load balancing
    lb_provider_configs = []
    for i, config in enumerate(provider_configs):
        # Weight inversely proportional to position (first provider gets highest weight)
        weight = len(provider_configs) - i
        lb_config = config.copy()
        lb_config["weight"] = weight
        lb_provider_configs.append(lb_config)
    
    try:
        lb_config = client.create_gateway_config(
            name="Orchestra-LoadBalance",
            routing_strategy="loadbalance",
            provider_configs=lb_provider_configs,
            cache_config={"enabled": True, "ttl": 3600}
        )
        
        logger.info(f"Created load balancing gateway config: {lb_config.id}")
        gateway_configs["loadbalance"] = lb_config.id
    except Exception as e:
        logger.error(f"Failed to create load balancing gateway config: {e}")
    
    return gateway_configs

def generate_env_file(virtual_keys: Dict[str, str], gateway_configs: Dict[str, str]) -> str:
    """Generate environment variable contents for the virtual keys and gateway configs."""
    env_content = "# Portkey Virtual Keys Configuration\n\n"
    
    # Add Portkey API key
    env_content += "# Portkey API key\n"
    env_content += f"PORTKEY_API_KEY={get_env_value('MASTER_PORTKEY_ADMIN_KEY')}\n\n"
    
    # Add Admin key (for management operations)
    env_content += "# Admin API key for virtual key management\n"
    env_content += f"MASTER_PORTKEY_ADMIN_KEY={get_env_value('MASTER_PORTKEY_ADMIN_KEY')}\n\n"
    
    # Add virtual keys
    env_content += "# Virtual keys for different providers\n"
    for provider in PROVIDERS:
        provider_id = provider["provider_id"].upper()
        if provider["provider_id"] in virtual_keys:
            env_content += f"PORTKEY_VIRTUAL_KEY_{provider_id}={virtual_keys[provider['provider_id']]}\n"
    
    env_content += "\n"
    
    # Add gateway configurations
    env_content += "# Gateway configurations\n"
    if "fallback" in gateway_configs:
        env_content += f"PORTKEY_CONFIG_ID={gateway_configs['fallback']}\n"
    env_content += "PORTKEY_STRATEGY=fallback\n"
    env_content += "PORTKEY_CACHE_ENABLED=true\n\n"
    
    # Add preferred provider
    env_content += "# Preferred LLM provider\n"
    env_content += "PREFERRED_LLM_PROVIDER=portkey\n"
    
    return env_content

def main() -> None:
    """Main function to set up Portkey virtual keys and configurations."""
    logger.info("Starting Portkey virtual keys setup...")
    
    # Get admin key
    admin_key = get_admin_key()
    
    try:
        # Initialize client
        client = PortkeyAdminClient(api_key=admin_key)
        logger.info("Portkey admin client initialized")
        
        # Create virtual keys
        virtual_keys = create_provider_virtual_keys(client)
        
        if not virtual_keys:
            logger.warning("No virtual keys were created. Please check your API keys.")
            return
        
        # Create gateway configurations
        gateway_configs = create_gateway_configs(client, virtual_keys)
        
        # Generate and output environment variables
        env_content = generate_env_file(virtual_keys, gateway_configs)
        
        logger.info("\nSetup complete! Add these environment variables to your .env file:")
        print("\n" + env_content)
        
        # Option to save to file
        save_to_file = input("\nDo you want to save these to a new file? (y/n): ")
        if save_to_file.lower() == 'y':
            filename = input("Enter filename (default: portkey_config.env): ") or "portkey_config.env"
            
            with open(filename, "w") as f:
                f.write(env_content)
                
            logger.info(f"Configuration saved to {filename}")
            
    except Exception as e:
        logger.error(f"An error occurred during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
