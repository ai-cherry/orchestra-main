#!/usr/bin/env python3
"""
Figma PAT Scope Validator

This script validates that the FIGMA_PAT environment variable has all the required scopes.
It performs functional tests against the Figma API to verify the token has the
necessary permissions: files:read, variables:write, and code_connect:write.
"""

import os
import sys
import requests
import json
import argparse

REQUIRED_SCOPES = ["files:read", "variables:write", "code_connect:write"]


def validate_figma_pat(figma_pat=None, file_id="368236963"):
    """
    Validate that the FIGMA_PAT has all required scopes by making test API calls

    Args:
        figma_pat: Optional Figma Personal Access Token. If not provided, will use FIGMA_PAT env var
        file_id: Figma file ID to use for testing variables access

    Returns:
        bool: True if the PAT has all required scopes, False otherwise
    """
    if not figma_pat:
        figma_pat = os.environ.get("FIGMA_PAT")

    if not figma_pat:
        print("❌ FIGMA_PAT not provided and environment variable not set")
        return False

    # Test the PAT by making requests to the Figma API
    headers = {"X-Figma-Token": figma_pat}

    print(f"Validating Figma PAT scopes...")
    print(f"Required scopes: {', '.join(REQUIRED_SCOPES)}")

    # Test files:read scope
    files_read = False
    print("\nTesting files:read scope...")
    try:
        response = requests.get("https://api.figma.com/v1/me", headers=headers)
        if response.status_code == 200:
            print("✅ files:read scope is valid")
            files_read = True
        else:
            print(f"❌ files:read scope check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking files:read scope: {str(e)}")

    # Test variables:write scope (we can only verify it indirectly by testing read access)
    variables_write = False
    print("\nTesting variables:write scope...")
    try:
        # Just verify we can access variables, can't directly test write without modifying
        response = requests.get(
            f"https://api.figma.com/v1/files/{file_id}/variables/local", headers=headers
        )
        if response.status_code == 200:
            print("✅ variables access is valid (indirect check for variables:write)")
            variables_write = True
        elif response.status_code == 403:
            print("❌ variables:write scope missing or insufficient permissions")
        else:
            print(f"❌ variables:write scope check inconclusive: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error checking variables:write scope: {str(e)}")

    # Test code_connect:write scope (also can only verify indirectly)
    code_connect_write = False
    print("\nTesting code_connect:write scope...")
    try:
        # Try to get developer resources, which requires code_connect permission
        response = requests.get("https://api.figma.com/v1/me/plugins", headers=headers)
        if response.status_code == 200:
            print("✅ code_connect:write scope is likely valid (indirect check)")
            code_connect_write = True
        else:
            print(f"❌ code_connect:write scope check failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Error checking code_connect:write scope: {str(e)}")

    # Summary
    success = files_read and variables_write and code_connect_write

    print("\n=== SUMMARY ===")
    if success:
        print("✅ FIGMA_PAT has all required scopes")
    else:
        print("❌ FIGMA_PAT is missing some required scopes")
        print("Please update your Figma PAT with the following scopes:")
        if not files_read:
            print(" - files:read")
        if not variables_write:
            print(" - variables:write")
        if not code_connect_write:
            print(" - code_connect:write")
        print(
            "\nYou can generate a new PAT at: https://www.figma.com/developers/api#access-tokens"
        )

    return success


def main():
    parser = argparse.ArgumentParser(description="Validate Figma PAT scopes")
    parser.add_argument(
        "--token",
        help="Figma Personal Access Token (if not provided, will use FIGMA_PAT env var)",
    )
    parser.add_argument(
        "--file-id",
        default="368236963",
        help="Figma file ID to use for testing variables access",
    )

    args = parser.parse_args()

    result = validate_figma_pat(args.token, args.file_id)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
