#!/usr/bin/env python3
"""
PostgreSQL Setup Preparation Script

This script prepares for the PostgreSQL setup by:
1. Checking if required environment variables are set
2. Providing instructions for setting up Cloud SQL with pgvector
3. Generating a command for running the setup_postgres_pgvector.py script

Usage:
    python prepare_postgres_setup.py
"""

import os
from pathlib import Path

# Define colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{GREEN}=== {text} ==={RESET}\n")


def print_warning(text):
    """Print a warning message."""
    print(f"{YELLOW}WARNING: {text}{RESET}")


def print_error(text):
    """Print an error message."""
    print(f"{RED}ERROR: {text}{RESET}")


def check_environment_variables():
    """Check if required environment variables are set."""
    print_header("Checking Environment Variables")

    required_vars = {
        "GCP_PROJECT_ID": "Your Google Cloud Project ID",
        "GCP_REGION": "GCP region (e.g., 'us-central1')",
        "CLOUD_SQL_INSTANCE_CONNECTION_NAME": "Format: project:region:instance",
        "CLOUD_SQL_DATABASE": "Database name (e.g., 'phidata')",
        "CLOUD_SQL_USER": "Database user (e.g., 'postgres')",
    }

    optional_vars = {
        "CLOUD_SQL_USE_IAM_AUTH": "Set to 'true' to use IAM auth, default is 'false'",
        "CLOUD_SQL_PASSWORD_SECRET_NAME": "Name of the secret in Secret Manager containing the password",
    }

    missing_required = []
    missing_optional = []

    # Check required variables
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            missing_required.append((var, description))
            print(f"❌ {var}: Not set ({description})")
        else:
            print(f"✅ {var}: {value}")

    # Check optional variables
    print("\nOptional Variables:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if not value:
            missing_optional.append((var, description))
            print(f"⚠️ {var}: Not set ({description})")
        else:
            print(f"✅ {var}: {value}")

    return missing_required, missing_optional


def check_script_exists():
    """Check if the setup_postgres_pgvector.py script exists."""
    script_path = Path("scripts/setup_postgres_pgvector.py")

    if not script_path.exists():
        print_error(f"Script not found: {script_path}")
        return False

    print(f"✅ Found script: {script_path}")
    return True


def generate_setup_command(use_iam_auth=False):
    """Generate the command to run the PostgreSQL setup script."""
    print_header("Generated Setup Command")

    cmd = ["python scripts/setup_postgres_pgvector.py", "--apply", "--schema llm"]

    # Add IAM auth flag if needed
    if use_iam_auth:
        cmd.append("--use-iam-auth")

    command = " \\\n  ".join(cmd)
    print(f"{command}")

    return command


def create_env_file_template(missing_vars):
    """Create a template .env file with missing variables."""
    if not missing_vars:
        return

    print_header("Environment Variables Template")

    env_content = "# PostgreSQL Setup Environment Variables\n"

    for var, description in missing_vars:
        env_content += f"# {description}\n{var}=\n\n"

    env_file = Path(".env.postgres")
    env_file.write_text(env_content)

    print(f"Created template file: {env_file}")
    print(f"Please fill in the missing values in this file and run: source {env_file}")


def main():
    """Main function."""
    print_header("PostgreSQL Setup Preparation")

    # Check environment variables
    missing_required, missing_optional = check_environment_variables()

    # Check if the script exists
    script_exists = check_script_exists()

    if missing_required:
        print_error(f"Missing {len(missing_required)} required environment variables!")
        create_env_file_template(missing_required + missing_optional)
        return

    if not script_exists:
        print_error("Cannot proceed without the setup script!")
        return

    # Determine authentication method
    use_iam_auth = os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "").lower() == "true"

    if not use_iam_auth and not os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME"):
        print_warning(
            "Neither IAM authentication nor a password secret name is specified."
        )
        print_warning(
            "You will need to provide a password directly when running the script."
        )

    # Generate the setup command
    generate_setup_command(use_iam_auth)

    # Print next steps
    print_header("Next Steps")
    print("1. Make sure all environment variables are set correctly")
    print("2. Run the generated command to set up PostgreSQL with pgvector")
    print("3. Verify that the tables and extensions were created successfully")


if __name__ == "__main__":
    main()
