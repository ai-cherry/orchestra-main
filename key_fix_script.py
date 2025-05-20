#!/usr/bin/env python3
"""
key_fix_script.py - Fix common issues with GCP service account key files

This script specifically addresses the "Invalid JWT Signature" error by:
1. Checking for and fixing escaped newlines in the private key
2. Ensuring proper PEM formatting of the private key
3. Removing any non-printable characters
4. Validating the key structure

Usage:
  python key_fix_script.py --input credentials.json --output fixed_credentials.json
"""

import json
import argparse
import re
import sys
from typing import Dict, Any


def fix_private_key(private_key: str) -> str:
    """Fix common issues with private key formatting."""
    # Replace escaped newlines with actual newlines
    if "\\n" in private_key and "\n" not in private_key:
        print("Fixing: Replacing escaped newlines (\\n) with actual newlines")
        private_key = private_key.replace("\\n", "\n")

    # Ensure the key has proper BEGIN/END markers
    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        print("Fixing: Adding BEGIN PRIVATE KEY marker")
        private_key = "-----BEGIN PRIVATE KEY-----\n" + private_key.lstrip()

    if not private_key.endswith("-----END PRIVATE KEY-----\n"):
        if private_key.endswith("-----END PRIVATE KEY-----"):
            print("Fixing: Adding newline after END PRIVATE KEY marker")
            private_key = private_key + "\n"
        else:
            print("Fixing: Adding END PRIVATE KEY marker")
            private_key = private_key.rstrip() + "\n-----END PRIVATE KEY-----\n"

    # Ensure there's a newline after BEGIN and before END
    private_key = re.sub(
        r"(-----BEGIN PRIVATE KEY-----)([^\n])", r"\1\n\2", private_key
    )
    private_key = re.sub(r"([^\n])(-----END PRIVATE KEY-----)", r"\1\n\2", private_key)

    # Remove any non-printable characters
    private_key = "".join(c for c in private_key if c.isprintable() or c == "\n")

    return private_key


def main():
    parser = argparse.ArgumentParser(
        description="Fix GCP service account key file issues"
    )
    parser.add_argument(
        "--input", default="credentials.json", help="Input key file path"
    )
    parser.add_argument(
        "--output", default="fixed_credentials.json", help="Output key file path"
    )
    args = parser.parse_args()

    print(f"Reading key file: {args.input}")

    try:
        with open(args.input, "r") as f:
            content = f.read()

        # Try to parse as JSON
        try:
            key_data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error: Key file is not valid JSON: {e}")
            sys.exit(1)

        # Check if it's a service account key
        if key_data.get("type") != "service_account":
            print(f"Warning: Key type is not 'service_account': {key_data.get('type')}")

        # Check for required fields
        required_fields = [
            "type",
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
            "client_id",
            "auth_uri",
            "token_uri",
            "auth_provider_x509_cert_url",
            "client_x509_cert_url",
        ]

        missing_fields = [field for field in required_fields if field not in key_data]
        if missing_fields:
            print(
                f"Error: Key file is missing required fields: {', '.join(missing_fields)}"
            )
            sys.exit(1)

        # Fix the private key
        if "private_key" in key_data:
            original_key = key_data["private_key"]
            fixed_key = fix_private_key(original_key)

            if original_key != fixed_key:
                print("Private key was fixed. Saving updated key file.")
                key_data["private_key"] = fixed_key

                with open(args.output, "w") as f:
                    json.dump(key_data, f, indent=2)

                print(f"Fixed key saved to: {args.output}")
                print("Try authenticating with the fixed key:")
                print(f"gcloud auth activate-service-account --key-file={args.output}")
            else:
                print("No issues found with the private key.")
        else:
            print("Error: No private_key field found in the key file.")
            sys.exit(1)

    except FileNotFoundError:
        print(f"Error: Key file not found: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
