#!/usr/bin/env python
"""
Portkey Virtual Keys Management Script.

This script provides a command-line interface for managing Portkey virtual keys,
allowing administrators to create, list, update, and delete virtual keys for
different providers without needing to use the Portkey web dashboard.

Usage:
    python scripts/manage_portkey_keys.py create-key --name "OpenAI Prod" --provider openai --key "sk-..."
    python scripts/manage_portkey_keys.py list-keys
    python scripts/manage_portkey_keys.py rotate-key --id "vk_..." --new-key "sk-..."
    python scripts/manage_portkey_keys.py create-config --name "Fallback Config" --strategy fallback

Environment Variables:
    MASTER_PORTKEY_ADMIN_KEY: The Portkey Admin API key (required)
"""

import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Add project root to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from packages.shared.src.portkey_admin.client import (
        PortkeyAdminClient,
        PortkeyAdminException,
    )
except ImportError:
    print(
        "ERROR: Could not import PortkeyAdminClient. Make sure you're running this script from the project root."
    )
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("portkey-manager")

# Available providers in Portkey
AVAILABLE_PROVIDERS = [
    "openai",
    "anthropic",
    "mistral",
    "huggingface",
    "cohere",
    "openrouter",
    "perplexity",
    "deepseek",
    "codestral",
    "cody",
    "continue",
    "grok",
    "google",
    "azure",
    "aws",
    "pinecone",
    "weaviate",
    "elevenlabs",
]

# Routing strategies
ROUTING_STRATEGIES = ["fallback", "loadbalance", "cost_aware"]


def format_output(data: Any, output_format: str = "pretty") -> str:
    """Format output data in the requested format."""
    if output_format == "json":
        return json.dumps(data, indent=2)
    else:
        # Pretty format for humans
        if isinstance(data, list):
            if not data:
                return "No items found."

            if hasattr(data[0], "__dict__"):
                # Format dataclass objects
                result = []
                for item in data:
                    item_dict = {
                        k: v for k, v in item.__dict__.items() if not k.startswith("_")
                    }
                    result.append(
                        "\n".join([f"{k}: {v}" for k, v in item_dict.items()])
                    )
                return "\n\n".join(result)

            return "\n".join([str(item) for item in data])
        elif hasattr(data, "__dict__"):
            # Format dataclass object
            item_dict = {
                k: v for k, v in data.__dict__.items() if not k.startswith("_")
            }
            return "\n".join([f"{k}: {v}" for k, v in item_dict.items()])
        else:
            return str(data)


def create_key(args: argparse.Namespace) -> None:
    """Create a new virtual key."""
    try:
        client = PortkeyAdminClient()

        # Validate provider
        if args.provider not in AVAILABLE_PROVIDERS:
            providers_str = ", ".join(AVAILABLE_PROVIDERS)
            logger.warning(
                f"Provider '{args.provider}' is not in the list of known providers: {providers_str}"
            )
            if not args.force:
                logger.error("Use --force to create a key with this provider anyway.")
                return

        # Create the virtual key
        key = client.create_virtual_key(
            name=args.name,
            provider_key=args.key,
            provider=args.provider,
            description=args.description,
            budget_limit=args.budget_limit,
            rate_limit=args.rate_limit,
        )

        print(f"Successfully created virtual key: {key.id}")
        print("\nTo use this key, add the following to your .env file:")
        env_var = f"PORTKEY_VIRTUAL_KEY_{args.provider.upper()}"
        print(f"{env_var}={key.id}")

        if args.output:
            print("\nFull details:")
            print(format_output(key, args.format))

    except PortkeyAdminException as e:
        logger.error(f"Failed to create virtual key: {e}")
        sys.exit(1)


def list_keys(args: argparse.Namespace) -> None:
    """List virtual keys."""
    try:
        client = PortkeyAdminClient()
        keys = client.list_virtual_keys(provider=args.provider)

        if args.format == "json":
            print(
                json.dumps(
                    [
                        {k: v for k, v in key.__dict__.items() if not k.startswith("_")}
                        for key in keys
                    ],
                    indent=2,
                )
            )
        else:
            print(f"Found {len(keys)} virtual keys:")
            for key in keys:
                print(f"\nID: {key.id}")
                print(f"Name: {key.name}")
                print(f"Provider: {key.provider}")
                print(f"Created: {key.created_at}")
                if key.last_used:
                    print(f"Last used: {key.last_used}")
                if key.usage_stats:
                    print(
                        f"Usage: ${key.usage_stats.get('total_cost', 0):.4f} "
                        f"({key.usage_stats.get('total_tokens', 0)} tokens)"
                    )

    except PortkeyAdminException as e:
        logger.error(f"Failed to list virtual keys: {e}")
        sys.exit(1)


def get_key(args: argparse.Namespace) -> None:
    """Get details for a specific virtual key."""
    try:
        client = PortkeyAdminClient()
        key = client.get_virtual_key(args.id)
        print(format_output(key, args.format))

    except PortkeyAdminException as e:
        logger.error(f"Failed to get virtual key: {e}")
        sys.exit(1)


def update_key(args: argparse.Namespace) -> None:
    """Update a virtual key."""
    try:
        client = PortkeyAdminClient()

        # Only include non-None parameters in the update
        update_params = {}
        if args.name:
            update_params["name"] = args.name
        if args.description:
            update_params["description"] = args.description
        if args.budget_limit is not None:
            update_params["budget_limit"] = args.budget_limit
        if args.rate_limit is not None:
            update_params["rate_limit"] = args.rate_limit

        if not update_params:
            logger.error(
                "No update parameters provided. Use --name, --description, --budget-limit, or --rate-limit."
            )
            return

        # Update the key
        key = client.update_virtual_key(args.id, **update_params)
        print(f"Successfully updated virtual key: {key.id}")

        if args.output:
            print("\nUpdated details:")
            print(format_output(key, args.format))

    except PortkeyAdminException as e:
        logger.error(f"Failed to update virtual key: {e}")
        sys.exit(1)


def delete_key(args: argparse.Namespace) -> None:
    """Delete a virtual key."""
    try:
        client = PortkeyAdminClient()

        # Confirm deletion if not forced
        if not args.force:
            confirm = input(
                f"Are you sure you want to delete virtual key '{args.id}'? This cannot be undone. (y/N): "
            )
            if confirm.lower() != "y":
                print("Deletion cancelled.")
                return

        # Delete the key
        result = client.delete_virtual_key(args.id)
        if result:
            print(f"Successfully deleted virtual key: {args.id}")
        else:
            print(f"Failed to delete virtual key: {args.id}")

    except PortkeyAdminException as e:
        logger.error(f"Failed to delete virtual key: {e}")
        sys.exit(1)


def rotate_key(args: argparse.Namespace) -> None:
    """Rotate a virtual key's provider key."""
    try:
        client = PortkeyAdminClient()

        # Rotate the key
        key = client.rotate_virtual_key(args.id, args.new_key)
        print(f"Successfully rotated virtual key: {key.id}")

        if args.output:
            print("\nUpdated details:")
            print(format_output(key, args.format))

    except PortkeyAdminException as e:
        logger.error(f"Failed to rotate virtual key: {e}")
        sys.exit(1)


def create_config(args: argparse.Namespace) -> None:
    """Create a new gateway configuration."""
    try:
        client = PortkeyAdminClient()

        # Validate strategy
        if args.strategy not in ROUTING_STRATEGIES:
            strategies_str = ", ".join(ROUTING_STRATEGIES)
            logger.error(
                f"Strategy '{args.strategy}' is not valid. Choose from: {strategies_str}"
            )
            return

        # Parse provider configs
        provider_configs = []
        if args.providers:
            try:
                provider_configs = json.loads(args.providers)
            except json.JSONDecodeError:
                logger.error(
                    'Invalid JSON format for providers. Example: \'[{"virtual_key": "vk_...", "weight": 1}]\''
                )
                return

        # Parse cache config
        cache_config = None
        if args.cache_config:
            try:
                cache_config = json.loads(args.cache_config)
            except json.JSONDecodeError:
                logger.error("Invalid JSON format for cache config.")
                return

        # Create the gateway config
        config = client.create_gateway_config(
            name=args.name,
            routing_strategy=args.strategy,
            provider_configs=provider_configs,
            cache_config=cache_config,
        )

        print(f"Successfully created gateway config: {config.id}")
        print("\nTo use this config, add the following to your .env file:")
        print(f"PORTKEY_CONFIG_ID={config.id}")

        if args.output:
            print("\nFull details:")
            print(format_output(config, args.format))

    except PortkeyAdminException as e:
        logger.error(f"Failed to create gateway config: {e}")
        sys.exit(1)


def list_configs(args: argparse.Namespace) -> None:
    """List gateway configurations."""
    try:
        client = PortkeyAdminClient()
        configs = client.list_gateway_configs()

        if args.format == "json":
            print(
                json.dumps(
                    [
                        {
                            k: v
                            for k, v in config.__dict__.items()
                            if not k.startswith("_")
                        }
                        for config in configs
                    ],
                    indent=2,
                )
            )
        else:
            print(f"Found {len(configs)} gateway configurations:")
            for config in configs:
                print(f"\nID: {config.id}")
                print(f"Name: {config.name}")
                print(f"Strategy: {config.routing_strategy}")
                print(f"Provider configs: {len(config.provider_configs)}")
                if config.cache_config:
                    print("Cache enabled: Yes")
                else:
                    print("Cache enabled: No")

    except PortkeyAdminException as e:
        logger.error(f"Failed to list gateway configs: {e}")
        sys.exit(1)


def get_usage(args: argparse.Namespace) -> None:
    """Get usage statistics."""
    try:
        client = PortkeyAdminClient()

        params = {}
        if args.start_date:
            params["start_date"] = args.start_date
        if args.end_date:
            params["end_date"] = args.end_date
        if args.key_id:
            params["virtual_key_id"] = args.key_id
        if args.provider:
            params["provider"] = args.provider

        stats = client.get_usage_stats(**params)

        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            print("Usage Statistics:")
            if "period" in stats:
                print(f"Period: {stats['period']}")

            if "total" in stats:
                print(f"\nTotal cost: ${stats['total'].get('cost', 0):.4f}")
                print(f"Total tokens: {stats['total'].get('tokens', 0):,}")
                print(f"Total requests: {stats['total'].get('requests', 0):,}")

            if "by_provider" in stats:
                print("\nBreakdown by provider:")
                for provider, data in stats["by_provider"].items():
                    print(f"  {provider}:")
                    print(f"    Cost: ${data.get('cost', 0):.4f}")
                    print(f"    Tokens: {data.get('tokens', 0):,}")
                    print(f"    Requests: {data.get('requests', 0):,}")

            if "by_virtual_key" in stats:
                print("\nBreakdown by virtual key:")
                for key_id, data in stats["by_virtual_key"].items():
                    print(f"  {key_id}:")
                    print(f"    Name: {data.get('name', 'Unnamed')}")
                    print(f"    Provider: {data.get('provider', 'Unknown')}")
                    print(f"    Cost: ${data.get('cost', 0):.4f}")
                    print(f"    Tokens: {data.get('tokens', 0):,}")
                    print(f"    Requests: {data.get('requests', 0):,}")

    except PortkeyAdminException as e:
        logger.error(f"Failed to get usage stats: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Manage Portkey virtual keys")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Common arguments
    output_args = argparse.ArgumentParser(add_help=False)
    output_args.add_argument(
        "--output", "-o", action="store_true", help="Show detailed output"
    )
    output_args.add_argument(
        "--format",
        "-f",
        choices=["pretty", "json"],
        default="pretty",
        help="Output format (default: pretty)",
    )

    # Create key command
    create_key_parser = subparsers.add_parser(
        "create-key", help="Create a new virtual key", parents=[output_args]
    )
    create_key_parser.add_argument(
        "--name", "-n", required=True, help="Name for the virtual key"
    )
    create_key_parser.add_argument(
        "--provider",
        "-p",
        required=True,
        help="Provider name (e.g., openai, anthropic)",
    )
    create_key_parser.add_argument(
        "--key", "-k", required=True, help="Provider API key"
    )
    create_key_parser.add_argument(
        "--description", "-d", help="Description for the key"
    )
    create_key_parser.add_argument(
        "--budget-limit", "-b", type=float, help="Monthly budget limit in USD"
    )
    create_key_parser.add_argument(
        "--rate-limit", "-r", type=int, help="Rate limit (requests per minute)"
    )
    create_key_parser.add_argument(
        "--force",
        action="store_true",
        help="Force creation even if provider is unknown",
    )
    create_key_parser.set_defaults(func=create_key)

    # List keys command
    list_keys_parser = subparsers.add_parser(
        "list-keys", help="List virtual keys", parents=[output_args]
    )
    list_keys_parser.add_argument("--provider", "-p", help="Filter by provider")
    list_keys_parser.set_defaults(func=list_keys)

    # Get key command
    get_key_parser = subparsers.add_parser(
        "get-key", help="Get details for a specific virtual key", parents=[output_args]
    )
    get_key_parser.add_argument("--id", "-i", required=True, help="Virtual key ID")
    get_key_parser.set_defaults(func=get_key)

    # Update key command
    update_key_parser = subparsers.add_parser(
        "update-key", help="Update a virtual key", parents=[output_args]
    )
    update_key_parser.add_argument("--id", "-i", required=True, help="Virtual key ID")
    update_key_parser.add_argument("--name", "-n", help="New name for the key")
    update_key_parser.add_argument(
        "--description", "-d", help="New description for the key"
    )
    update_key_parser.add_argument(
        "--budget-limit", "-b", type=float, help="New monthly budget limit in USD"
    )
    update_key_parser.add_argument(
        "--rate-limit", "-r", type=int, help="New rate limit (requests per minute)"
    )
    update_key_parser.set_defaults(func=update_key)

    # Delete key command
    delete_key_parser = subparsers.add_parser("delete-key", help="Delete a virtual key")
    delete_key_parser.add_argument("--id", "-i", required=True, help="Virtual key ID")
    delete_key_parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )
    delete_key_parser.set_defaults(func=delete_key)

    # Rotate key command
    rotate_key_parser = subparsers.add_parser(
        "rotate-key",
        help="Rotate a virtual key's provider API key",
        parents=[output_args],
    )
    rotate_key_parser.add_argument("--id", "-i", required=True, help="Virtual key ID")
    rotate_key_parser.add_argument(
        "--new-key", "-k", required=True, help="New provider API key"
    )
    rotate_key_parser.set_defaults(func=rotate_key)

    # Create config command
    create_config_parser = subparsers.add_parser(
        "create-config",
        help="Create a new gateway configuration",
        parents=[output_args],
    )
    create_config_parser.add_argument(
        "--name", "-n", required=True, help="Name for the gateway configuration"
    )
    create_config_parser.add_argument(
        "--strategy",
        "-s",
        required=True,
        choices=ROUTING_STRATEGIES,
        help="Routing strategy",
    )
    create_config_parser.add_argument(
        "--providers", "-p", help="Provider configurations as JSON array"
    )
    create_config_parser.add_argument(
        "--cache-config", "-c", help="Cache configuration as JSON object"
    )
    create_config_parser.set_defaults(func=create_config)

    # List configs command
    list_configs_parser = subparsers.add_parser(
        "list-configs", help="List gateway configurations", parents=[output_args]
    )
    list_configs_parser.set_defaults(func=list_configs)

    # Get usage command
    get_usage_parser = subparsers.add_parser(
        "get-usage", help="Get usage statistics", parents=[output_args]
    )
    get_usage_parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    get_usage_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    get_usage_parser.add_argument("--key-id", "-k", help="Filter by virtual key ID")
    get_usage_parser.add_argument("--provider", "-p", help="Filter by provider")
    get_usage_parser.set_defaults(func=get_usage)

    # Parse arguments
    args = parser.parse_args()

    # Check if a command was specified
    if not args.command:
        parser.print_help()
        return

    # Check for required environment variable
    if not os.environ.get("MASTER_PORTKEY_ADMIN_KEY"):
        logger.error("MASTER_PORTKEY_ADMIN_KEY environment variable is required")
        sys.exit(1)

    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
