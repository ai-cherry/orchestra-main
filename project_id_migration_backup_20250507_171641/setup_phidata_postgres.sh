#!/bin/bash
# Setup script for Phidata with PostgreSQL and PGVector

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
pip install -q phidata >=2.7.0 sqlalchemy>=2.0.0 google-cloud-sql-connector google-cloud-secret-manager pg8000

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

read -p "Would you like to generate a test script to verify connectivity? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  cat > test_postgres_connection.py << 'EOF'
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
EOF
  
  echo -e "\033[1;32mGenerated test_postgres_connection.py\033[0m"
  echo "Run the test with: python test_postgres_connection.py"
fi

# 5. Explain next steps
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
echo -e "\033[1;33mNOTE: This script has prepared your environment, but has NOT executed the actual database setup,\nas that requires the infrastructure to be provisioned by Terraform first.\033[0m"
