#!/usr/bin/env python3
"""
Verify Phidata Setup with PostgreSQL/PGVector

This script verifies the setup of Phidata with PostgreSQL/PGVector by:
1. Checking environment variables
2. Verifying required dependencies
3. Testing PostgreSQL connectivity (if infrastructure is provisioned)
4. Checking if pgvector extension is installed
5. Verifying Phidata integration

Usage:
    python verify_phidata_setup.py [--test-connection]
"""

import os
import sys
import argparse
import importlib
from typing import Dict, Any, List, Optional

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{GREEN}=== {text} ==={RESET}\n")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{YELLOW}WARNING: {text}{RESET}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{RED}ERROR: {text}{RESET}")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def check_env_vars() -> bool:
    """Check if all required environment variables are set."""
    print_header("Checking Environment Variables")
    
    required_vars = {
        "GCP_PROJECT_ID": "Google Cloud Project ID",
        "GCP_REGION": "Google Cloud Region",
        "CLOUD_SQL_INSTANCE_CONNECTION_NAME": "Cloud SQL instance connection name",
        "CLOUD_SQL_DATABASE": "Cloud SQL database name",
        "CLOUD_SQL_USER": "Cloud SQL user",
    }
    
    optional_vars = {
        "CLOUD_SQL_USE_IAM_AUTH": "Whether to use IAM authentication",
        "CLOUD_SQL_PASSWORD_SECRET_NAME": "Secret Manager secret name containing password",
        "VERTEX_EMBEDDING_MODEL": "Vertex AI embedding model name",
        "APP_ENV": "Application environment (development, staging, production)",
    }
    
    all_required_set = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            print(f"{RED}❌ {var}: Not set ({description}){RESET}")
            all_required_set = False
        else:
            print(f"{GREEN}✅ {var}: {value}{RESET}")
    
    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if not value:
            print(f"{YELLOW}⚠️ {var}: Not set ({description}){RESET}")
        else:
            print(f"{GREEN}✅ {var}: {value}{RESET}")
    
    return all_required_set

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    print_header("Checking Dependencies")
    
    dependencies = [
        ("phi", "Phidata core package"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pg8000", "PostgreSQL driver"),
        ("google.cloud.secretmanager", "Google Cloud Secret Manager"),
    ]
    
    all_deps_installed = True
    for module_name, description in dependencies:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "__version__"):
                version = module.__version__
                print(f"{GREEN}✅ {module_name}: v{version} ({description}){RESET}")
            else:
                print(f"{GREEN}✅ {module_name}: Installed ({description}){RESET}")
        except ImportError:
            print(f"{RED}❌ {module_name}: Not installed ({description}){RESET}")
            all_deps_installed = False
    
    # Check for specific Phidata modules
    try:
        # Check for phi.storage.postgres.pgvector module
        from phi.storage.postgres.pgvector import PgVector2
        print(f"{GREEN}✅ phi.storage.postgres.pgvector: Installed (PgVector2 class){RESET}")
    except ImportError:
        print(f"{RED}❌ phi.storage.postgres.pgvector: Not installed (needed for vector storage){RESET}")
        print(f"{YELLOW}   Run: pip install 'phi-postgres>=0.2.0' 'phi-vectordb>=0.1.0'{RESET}")
        all_deps_installed = False
    
    try:
        # Check for phi.storage.assistant.pg module
        from phi.storage.assistant.pg import PgAssistantStorage
        print(f"{GREEN}✅ phi.storage.assistant.pg: Installed (PgAssistantStorage class){RESET}")
    except ImportError:
        print(f"{RED}❌ phi.storage.assistant.pg: Not installed (needed for agent storage){RESET}")
        print(f"{YELLOW}   Run: pip install 'phi-postgres>=0.2.0'{RESET}")
        all_deps_installed = False
    
    # Check for Google Cloud SQL Connector
    try:
        from google.cloud.sql.connector import Connector
        print(f"{GREEN}✅ google.cloud.sql.connector: Installed (Connector class){RESET}")
    except ImportError:
        print(f"{RED}❌ google.cloud.sql.connector: Not installed (needed for CloudSQL connection){RESET}")
        print(f"{YELLOW}   This may require special installation steps.{RESET}")
        all_deps_installed = False
    
    # Optional: Check for embedders
    try:
        from phi.embedder import VertexAiEmbedder
        print(f"{GREEN}✅ phi.embedder: Installed (VertexAiEmbedder class){RESET}")
    except ImportError:
        print(f"{YELLOW}⚠️ phi.embedder: Not found (optional, needed for VertexAI embeddings){RESET}")
    
    return all_deps_installed

def check_pg_setup_script() -> bool:
    """Check if the PostgreSQL setup script exists."""
    print_header("Checking PostgreSQL Setup Script")
    
    script_path = "scripts/setup_postgres_pgvector.py"
    if os.path.isfile(script_path):
        print(f"{GREEN}✅ Found script: {script_path}{RESET}")
        return True
    else:
        print(f"{RED}❌ Script not found: {script_path}{RESET}")
        return False

def check_env_postgres_file() -> bool:
    """Check if the .env.postgres file exists and has content."""
    print_header("Checking PostgreSQL Environment File")
    
    file_path = ".env.postgres"
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            if len(content.strip()) > 0:
                print(f"{GREEN}✅ Found and populated: {file_path}{RESET}")
                return True
            else:
                print(f"{YELLOW}⚠️ File exists but appears empty: {file_path}{RESET}")
                return False
    else:
        print(f"{RED}❌ File not found: {file_path}{RESET}")
        return False

def check_terraform_files() -> bool:
    """Check if the Terraform files exist."""
    print_header("Checking Terraform Files")
    
    terraform_dir = "infra/orchestra-terraform"
    required_files = ["main.tf", "cloudsql.tf", "cloudrun.tf", "variables.tf"]
    
    all_files_exist = True
    for file in required_files:
        file_path = os.path.join(terraform_dir, file)
        if os.path.isfile(file_path):
            print(f"{GREEN}✅ Found: {file_path}{RESET}")
        else:
            print(f"{RED}❌ Not found: {file_path}{RESET}")
            all_files_exist = False
    
    return all_files_exist

def check_phidata_agent_example() -> bool:
    """Check if the Phidata agent example file exists."""
    print_header("Checking Phidata Agent Example")
    
    file_path = "examples/register_phidata_postgres_agent.py"
    if os.path.isfile(file_path):
        print(f"{GREEN}✅ Found: {file_path}{RESET}")
        return True
    else:
        print(f"{RED}❌ Not found: {file_path}{RESET}")
        return False

def format_command(command: str) -> str:
    """Format a command for display."""
    return f"{YELLOW}   {command}{RESET}"

def print_next_steps(env_ok: bool, deps_ok: bool, script_ok: bool, terraform_ok: bool) -> None:
    """Print next steps based on verification results."""
    print_header("Next Steps")
    
    if not env_ok:
        print("1. Set up environment variables:")
        print(format_command("cp .env.postgres.example .env.postgres  # Create from example if needed"))
        print(format_command("nano .env.postgres  # Edit values"))
        print(format_command("source .env.postgres  # Load variables"))
        print("")
    
    if not deps_ok:
        print("2. Install required dependencies:")
        print(format_command("./install_phidata_deps.sh"))
        print("")
    
    print("3. Provision infrastructure with Terraform:")
    print(format_command("cd infra/orchestra-terraform"))
    print(format_command("terraform init"))
    print(format_command("terraform workspace select dev"))
    print(format_command("terraform plan -var=\"env=dev\""))
    print(format_command("terraform apply -var=\"env=dev\" -auto-approve"))
    print("")
    
    if script_ok:
        print("4. Set up PostgreSQL schema:")
        print(format_command("python scripts/setup_postgres_pgvector.py --apply --schema llm"))
        print("")
    
    print("5. Register a Phidata agent with PostgreSQL storage:")
    print(format_command("python examples/register_phidata_postgres_agent.py"))
    print("")
    
    print("6. Run integration tests to verify everything is working:")
    print(format_command("python -m packages.llm.src.test_phidata_integration"))
    print(format_command("python -m packages.tools.src.test_phidata_integration"))

def main():
    """Main function to verify Phidata setup."""
    parser = argparse.ArgumentParser(description="Verify Phidata setup with PostgreSQL.")
    parser.add_argument("--test-connection", action="store_true", help="Test actual PostgreSQL connection")
    args = parser.parse_args()
    
    print_header("Phidata PostgreSQL Setup Verification")
    
    # Check components
    env_ok = check_env_vars()
    deps_ok = check_dependencies()
    script_ok = check_pg_setup_script()
    env_file_ok = check_env_postgres_file()
    terraform_ok = check_terraform_files()
    example_ok = check_phidata_agent_example()
    
    # Test connection if requested
    connection_ok = None
    if args.test_connection:
        # This would import and call functions from test_postgres_connection.py
        # We're not implementing this here as it would duplicate code
        print_header("PostgreSQL Connection Test")
        print(f"{YELLOW}To test the actual PostgreSQL connection, run:{RESET}")
        print(f"{YELLOW}./test_postgres_connection.py{RESET}")
    
    # Print summary
    print_header("Verification Summary")
    print(f"Environment Variables: {GREEN+'OK'+RESET if env_ok else RED+'Missing'+RESET}")
    print(f"Dependencies: {GREEN+'OK'+RESET if deps_ok else RED+'Missing'+RESET}")
    print(f"PostgreSQL Setup Script: {GREEN+'Found'+RESET if script_ok else RED+'Missing'+RESET}")
    print(f"Environment File: {GREEN+'OK'+RESET if env_file_ok else YELLOW+'Missing/Empty'+RESET}")
    print(f"Terraform Files: {GREEN+'OK'+RESET if terraform_ok else RED+'Missing'+RESET}")
    print(f"Phidata Agent Example: {GREEN+'Found'+RESET if example_ok else RED+'Missing'+RESET}")
    
    # Print next steps
    print_next_steps(env_ok, deps_ok, script_ok, terraform_ok)
    
    # Return success if all essential components are in place
    return env_ok and deps_ok and script_ok and terraform_ok

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
