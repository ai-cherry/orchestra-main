#!/bin/bash
# Setup script for Phidata with PostgreSQL and PGVector (non-interactive)

echo -e "\033[1;32m=== Phidata PostgreSQL Setup Script ===\033[0m\n"

# 1. Set environment variables
echo -e "\033[1;34mSetting up environment variables...\033[0m"
export GCP_REGION=us-central1
export CLOUD_SQL_INSTANCE_CONNECTION_NAME=agi-baby-cherry:us-central1:phidata-postgres-dev
export CLOUD_SQL_DATABASE=phidata_memory
export CLOUD_SQL_USER=phidata_user
export CLOUD_SQL_USE_IAM_AUTH=false
export CLOUD_SQL_PASSWORD_SECRET_NAME=postgres-password-dev

# 2. Install required dependencies
echo -e "\033[1;34mInstalling required dependencies...\033[0m"
pip install -q phidata sqlalchemy>=2.0.0 google-cloud-sql-connector google-cloud-secret-manager pg8000

# 3. Verify dependencies
echo -e "\033[1;34mVerifying Phidata installation...\033[0m"
python -c "import phi; print(f'Phidata version: {phi.__version__}')" || {
  echo -e "\033[1;31mError: Failed to import Phidata. Please check installation.\033[0m"
  exit 1
}

echo -e "\033[1;34mVerifying SQLAlchemy installation...\033[0m"
python -c "import sqlalchemy; print(f'SQLAlchemy version: {sqlalchemy.__version__}')" || {
  echo -e "\033[1;31mError: Failed to import SQLAlchemy. Please check installation.\033[0m"
  exit 1
}

echo -e "\033[1;34mVerifying Google Cloud libraries...\033[0m"
python -c "from google.cloud.sql.connector import Connector; from google.cloud import secretmanager; print('Google Cloud libraries installed')" || {
  echo -e "\033[1;31mError: Failed to import Google Cloud libraries. Please check installation.\033[0m"
  exit 1
}

# 4. Run setup
echo -e "\033[1;34mPreparing to run PostgreSQL setup script...\033[0m"
echo "This script will:"
echo "1. Connect to Cloud SQL instance ${CLOUD_SQL_INSTANCE_CONNECTION_NAME}"
echo "2. Create and configure the database schema 'llm'"
echo "3. Setup pgvector extension and recommended indexes"
echo ""

echo -e "\033[1;33mNOTE: For this script to work successfully, the Terraform infrastructure must be provisioned first.\033[0m"
echo -e "\033[1;33mWhen Terraform is available, the following command should be run first:\033[0m"
echo "./run_terraform_dev.sh"
echo ""

echo -e "\033[1;33mTo actually execute the database setup, you would run:\033[0m"
echo "python scripts/setup_postgres_pgvector.py --apply --schema llm"
echo ""

# Generate the test script automatically
echo -e "\033[1;34mGenerating test connection script...\033[0m"
cat > test_postgres_connection.py << 'EOF2'
#!/usr/bin/env python3
"""
Test PostgreSQL connection to Cloud SQL.
"""
import os
import sys
from google.cloud.sql.connector import Connector
from google.cloud import secretmanager
import sqlalchemy

def get_password_from_secret_manager(project_id, secret_name):
    """Get password from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error retrieving password from Secret Manager: {e}")
        return None

def test_connection():
    """Test connection to Cloud SQL."""
    project_id = os.environ.get("GCP_PROJECT_ID")
    instance_connection_name = os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
    database = os.environ.get("CLOUD_SQL_DATABASE")
    user = os.environ.get("CLOUD_SQL_USER")
    use_iam_auth = os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "").lower() == "true"
    password_secret_name = os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME")

    print(f"Project ID: {project_id}")
    print(f"Instance: {instance_connection_name}")
    print(f"Database: {database}")
    print(f"User: {user}")
    print(f"Using IAM Auth: {use_iam_auth}")

    if not use_iam_auth:
        password = get_password_from_secret_manager(project_id, password_secret_name)
        if not password:
            print("Failed to retrieve password from Secret Manager")
            return False

    # Create SQL connection
    connector = Connector()

    try:
        if use_iam_auth:
            def getconn():
                return connector.connect(
                    instance_connection_string=instance_connection_name,
                    driver="pg8000",
                    user=user,
                    db=database,
                    enable_iam_auth=True
                )
        else:
            def getconn():
                return connector.connect(
                    instance_connection_string=instance_connection_name,
                    driver="pg8000",
                    user=user,
                    password=password,
                    db=database
                )

        # Create SQLAlchemy engine
        engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn
        )

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text("SELECT version();"))
            version = result.scalar()
            print(f"Connected to PostgreSQL: {version}")
            return True

    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("✅ Connection test successful!")
    else:
        print("❌ Connection test failed!")
        sys.exit(1)
EOF2
  
chmod +x test_postgres_connection.py
echo -e "\033[1;32mGenerated test_postgres_connection.py\033[0m"

# 5. Create a helper script to install phidata dependencies
echo -e "\033[1;34mCreating helper script to install phidata dependencies...\033[0m"
cat > install_phidata_deps.sh << 'EOF3'
#!/bin/bash
# Install all dependencies required for Phidata with PostgreSQL

echo "Installing dependencies needed for Phidata with PostgreSQL/PGVector..."

# Core dependencies
pip install phidata>=2.7.0 'phi-postgres>=0.2.0' 'phi-vectordb>=0.1.0'

# Google Cloud dependencies
pip install google-cloud-sql-connector google-cloud-secret-manager

# Database drivers and SQLAlchemy
pip install sqlalchemy>=2.0.0 pg8000 psycopg2-binary

# Additional utilities
pip install python-dotenv

echo "All dependencies installed!"
EOF3

chmod +x install_phidata_deps.sh
echo -e "\033[1;32mCreated install_phidata_deps.sh\033[0m"

# 6. Create a verification script
echo -e "\033[1;34mCreating verification script...\033[0m"
cat > verify_phidata_setup.py << 'EOF4'
#!/usr/bin/env python3
"""
Verify Phidata Setup with PostgreSQL.

This script checks if the necessary components for Phidata with PostgreSQL
are properly set up by:
1. Checking environment variables
2. Verifying required dependencies
3. Testing PostgreSQL connectivity (if infrastructure is provisioned)
4. Checking if pgvector extension is installed
"""

import os
import sys
import importlib

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def check_env_vars():
    """Check if all required environment variables are set."""
    print(f"{GREEN}Checking environment variables...{RESET}")
    
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

def check_dependencies():
    """Check if all required dependencies are installed."""
    print(f"\n{GREEN}Checking dependencies...{RESET}")
    
    dependencies = [
        ("phi", "Phidata core package"),
        ("google.cloud.sql.connector", "Google Cloud SQL Connector"),
        ("google.cloud.secretmanager", "Google Cloud Secret Manager"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pg8000", "PostgreSQL driver")
    ]
    
    all_deps_installed = True
    for module, description in dependencies:
        try:
            importlib.import_module(module)
            print(f"{GREEN}✅ {module}: Installed ({description}){RESET}")
        except ImportError:
            print(f"{RED}❌ {module}: Not installed ({description}){RESET}")
            all_deps_installed = False
    
    # Check if specific Phidata modules are available
    try:
        from phi.storage.postgres.pgvector import PgVector2
        print(f"{GREEN}✅ phi.storage.postgres.pgvector: Installed (PgVector2 class){RESET}")
    except ImportError:
        print(f"{RED}❌ phi.storage.postgres.pgvector: Not installed (PgVector2 class){RESET}")
        all_deps_installed = False
    
    try:
        from phi.storage.assistant.pg import PgAssistantStorage
        print(f"{GREEN}✅ phi.storage.assistant.pg: Installed (PgAssistantStorage class){RESET}")
    except ImportError:
        print(f"{RED}❌ phi.storage.assistant.pg: Not installed (PgAssistantStorage class){RESET}")
        all_deps_installed = False
    
    return all_deps_installed

def try_connect_postgres():
    """Try to connect to PostgreSQL if infrastructure is provisioned."""
    print(f"\n{GREEN}Testing PostgreSQL connection (if infrastructure is provisioned)...{RESET}")
    print(f"{YELLOW}Note: This test will fail if Terraform hasn't provisioned the infrastructure yet.{RESET}")
    
    try:
        from google.cloud.sql.connector import Connector
        from google.cloud import secretmanager
        import sqlalchemy
        
        project_id = os.environ.get("GCP_PROJECT_ID")
        instance_name = os.environ.get("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
        db_name = os.environ.get("CLOUD_SQL_DATABASE")
        user = os.environ.get("CLOUD_SQL_USER")
        use_iam_auth = os.environ.get("CLOUD_SQL_USE_IAM_AUTH", "").lower() == "true"
        password_secret = os.environ.get("CLOUD_SQL_PASSWORD_SECRET_NAME")
        
        # Skip if missing vars
        if not (project_id and instance_name and db_name and user):
            print(f"{YELLOW}⚠️ Skipping connection test - missing environment variables{RESET}")
            return None
        
        # Try to get password if using password auth
        if not use_iam_auth and password_secret:
            try:
                client = secretmanager.SecretManagerServiceClient()
                secret_path = f"projects/{project_id}/secrets/{password_secret}/versions/latest"
                response = client.access_secret_version(name=secret_path)
                password = response.payload.data.decode("UTF-8")
                print(f"{GREEN}✅ Retrieved password from Secret Manager{RESET}")
            except Exception as e:
                print(f"{RED}❌ Failed to retrieve password from Secret Manager: {e}{RESET}")
                return False
        
        # Connect to PostgreSQL
        connector = Connector()
        if use_iam_auth:
            def getconn():
                return connector.connect(
                    instance_connection_string=instance_name,
                    driver="pg8000",
                    user=user,
                    db=db_name,
                    enable_iam_auth=True
                )
        else:
            def getconn():
                return connector.connect(
                    instance_connection_string=instance_name,
                    driver="pg8000",
                    user=user,
                    password=password,
                    db=db_name
                )
        
        # Create engine and test connection
        engine = sqlalchemy.create_engine("postgresql+pg8000://", creator=getconn)
        with engine.connect() as conn:
            # Test connection
            result = conn.execute(sqlalchemy.text("SELECT version();"))
            version = result.scalar()
            print(f"{GREEN}✅ Connected to PostgreSQL: {version}{RESET}")
            
            # Check if pgvector extension is installed
            try:
                result = conn.execute(sqlalchemy.text("SELECT * FROM pg_extension WHERE extname = 'vector';"))
                if result.rowcount > 0:
                    print(f"{GREEN}✅ pgvector extension is installed{RESET}")
                else:
                    print(f"{RED}❌ pgvector extension is NOT installed{RESET}")
            except Exception as e:
                print(f"{RED}❌ Error checking pgvector extension: {e}{RESET}")
        
        return True
        
    except Exception as e:
        print(f"{YELLOW}⚠️ PostgreSQL connection failed: {e}{RESET}")
        print(f"{YELLOW}This is expected if infrastructure isn't provisioned yet.{RESET}")
        return False

def main():
    """Run all verification checks."""
    print(f"\n{GREEN}=== Phidata PostgreSQL Setup Verification ==={RESET}\n")
    
    env_vars_ok = check_env_vars()
    dependencies_ok = check_dependencies()
    postgres_ok = try_connect_postgres()
    
    print(f"\n{GREEN}=== Verification Summary ==={RESET}")
    print(f"Environment Variables: {'OK' if env_vars_ok else 'Missing'}")
    print(f"Dependencies: {'OK' if dependencies_ok else 'Missing'}")
    print(f"PostgreSQL Connection: {'OK' if postgres_ok is True else 'Failed' if postgres_ok is False else 'Skipped'}")
    
    if env_vars_ok and dependencies_ok:
        if postgres_ok is True:
            print(f"\n{GREEN}✅ All checks passed! The system is ready.{RESET}")
        elif postgres_ok is False:
            print(f"\n{YELLOW}⚠️ Environment and dependencies are okay, but PostgreSQL connection failed.{RESET}")
            print(f"{YELLOW}This is expected if Terraform infrastructure hasn't been provisioned yet.{RESET}")
            print(f"\n{YELLOW}Next steps:{RESET}")
            print(f"1. Run Terraform to provision the infrastructure:")
            print(f"   ./run_terraform_dev.sh")
            print(f"2. Set up PostgreSQL schema:")
            print(f"   python scripts/setup_postgres_pgvector.py --apply --schema llm")
        else:
            print(f"\n{YELLOW}⚠️ Environment and dependencies are okay, but PostgreSQL connection was skipped.{RESET}")
            print(f"{YELLOW}Make sure to provision infrastructure before running setup.{RESET}")
    else:
        print(f"\n{RED}❌ There are issues with the environment or dependencies.{RESET}")
        print(f"{RED}Please fix these issues before proceeding.{RESET}")
        print(f"\nTo install missing dependencies, run:")
        print(f"./install_phidata_deps.sh")

if __name__ == "__main__":
    main()
EOF4

chmod +x verify_phidata_setup.py
echo -e "\033[1;32mCreated verify_phidata_setup.py\033[0m"

# 7. Explain next steps
echo -e "\n\033[1;32m=== Next Steps ===\033[0m"
echo "1. Provision infrastructure with Terraform"
echo "   -> This step is necessary before running the actual setup"
echo "2. Run the PostgreSQL setup script:"
echo "   -> python scripts/setup_postgres_pgvector.py --apply --schema llm"
echo "3. Register a Phidata agent with PostgreSQL storage:"
echo "   -> See examples/register_phidata_postgres_agent.py"
echo "4. Run integration tests to verify the setup:"
echo "   -> python -m packages.llm.src.test_phidata_integration"
echo "   -> python -m packages.tools.src.test_phidata_integration"
echo ""
echo -e "\033[1;33mYou can verify your setup anytime by running:\033[0m"
echo "./verify_phidata_setup.py"
echo ""
echo -e "\033[1;33mIf you're missing any dependencies, run:\033[0m"
echo "./install_phidata_deps.sh"
