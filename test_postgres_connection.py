#!/usr/bin/env python3
"""
Test PostgreSQL connection to Cloud SQL.
"""
import os
import sys
from typing import Optional, Dict, Any

# Check for required packages
try:
    import sqlalchemy
except ImportError:
    print("Installing SQLAlchemy...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy>=2.0.0"])
    import sqlalchemy

try:
    from google.cloud import secretmanager
except ImportError:
    print("Installing Google Cloud Secret Manager...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-secret-manager"])
    from google.cloud import secretmanager

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

def get_password_from_secret_manager(project_id: str, secret_name: str) -> Optional[str]:
    """Get password from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print_error(f"Error retrieving password from Secret Manager: {e}")
        return None

def generate_mock_connection_string(config: Dict[str, Any]) -> str:
    """Generate a PostgreSQL connection string."""
    if config.get("use_iam_auth"):
        return f"postgresql+pg8000://{config['user']}@/{config['database']}?host={config['instance_connection_name']}&enable_iam_auth=true"
    else:
        return f"postgresql+pg8000://{config['user']}:PASSWORD@/{config['database']}?host={config['instance_connection_name']}"

def test_connection_configuration() -> bool:
    """Test connection configuration without actually connecting."""
    print_header("Testing PostgreSQL Connection Configuration")
    
    # Get configuration from environment variables
    config = {
        "project_id": os.environ.get("GCP_PROJECT_ID"),
        "instance_connection_name": os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME"),
        "database": os.environ.get("CLOUD_SQL_DATABASE"),
        "user": os.environ.get("CLOUD_SQL_USER"),
        "use_iam_auth": os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "").lower() == "true",
        "password_secret_name": os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME")
    }
    
    # Check if required variables are set
    missing_vars = []
    for var in ["project_id", "instance_connection_name", "database", "user"]:
        if not config.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print_error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Print configuration
    print(f"Project ID: {config['project_id']}")
    print(f"Instance: {config['instance_connection_name']}")
    print(f"Database: {config['database']}")
    print(f"User: {config['user']}")
    print(f"Using IAM Auth: {config['use_iam_auth']}")
    
    # Check authentication method
    if config['use_iam_auth']:
        print("Authentication Method: IAM")
    else:
        if config['password_secret_name']:
            print(f"Authentication Method: Password from Secret Manager ({config['password_secret_name']})")
        else:
            print_warning("No password secret name provided for password authentication")
            return False
    
    # Generate connection string
    conn_string = generate_mock_connection_string(config)
    print(f"\nConnection String Format: {conn_string}")
    
    return True

def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    print_header("Checking Dependencies")
    
    dependencies = {
        "sqlalchemy": "SQLAlchemy (SQL toolkit and ORM)",
        "google.cloud.secretmanager": "Google Cloud Secret Manager (for password retrieval)"
    }
    
    try:
        # Try to import pg8000
        import pg8000
        dependencies["pg8000"] = "pg8000 (PostgreSQL driver)"
    except ImportError:
        print_warning("pg8000 is not installed, it will be needed for actual connection")
        print("Installing pg8000...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pg8000"])
            import pg8000
            dependencies["pg8000"] = "pg8000 (PostgreSQL driver)"
        except:
            print_error("Failed to install pg8000")
    
    try:
        # Try to import google-cloud-sql-connector
        from google.cloud.sql.connector import Connector
        dependencies["google.cloud.sql.connector"] = "Google Cloud SQL Connector"
    except ImportError:
        print_warning("google-cloud-sql-connector is not installed, it will be needed for actual connection")
        print("This package may require special installation steps.")
    
    # Check each dependency
    all_deps_installed = True
    for module, description in dependencies.items():
        try:
            __import__(module.split(".")[0])
            print(f"✅ {module}: Installed ({description})")
        except ImportError:
            print(f"❌ {module}: Not installed ({description})")
            all_deps_installed = False
    
    return all_deps_installed

def print_next_steps():
    """Print next steps for the user."""
    print_header("Next Steps")
    print("1. Install the Cloud SQL Proxy (if testing locally)")
    print("   https://cloud.google.com/sql/docs/postgres/connect-instance-auth-proxy")
    print("")
    print("2. Ensure that Terraform has successfully provisioned the infrastructure:")
    print("   - Cloud SQL PostgreSQL instance exists")
    print("   - Database user and password are created")
    print("   - Secret Manager contains the database password")
    print("")
    print("3. Run the setup_postgres_pgvector.py script:")
    print("   python scripts/setup_postgres_pgvector.py --apply --schema llm")
    print("")
    print("4. Register a Phidata agent with PostgreSQL storage:")
    print("   See examples/register_phidata_postgres_agent.py")

def main():
    """Main function to test PostgreSQL connection configuration."""
    print_header("PostgreSQL Connection Test")
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print_warning("Some dependencies are missing, but we can still check your configuration")
    
    # Test connection configuration
    config_ok = test_connection_configuration()
    
    # Print summary
    print_header("Test Summary")
    print(f"Dependencies Check: {'✅ OK' if deps_ok else '❌ Some missing'}")
    print(f"Configuration Check: {'✅ OK' if config_ok else '❌ Incomplete'}")
    
    # Print next steps
    print_next_steps()
    
    return config_ok

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
