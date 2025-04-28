#!/bin/bash
# Install all dependencies required for Phidata with PostgreSQL

# Define colors for terminal output
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

print_header() {
    echo -e "\n${GREEN}=== $1 ===${RESET}\n"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${RESET}"
}

print_error() {
    echo -e "${RED}ERROR: $1${RESET}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 could not be found"
        return 1
    else
        echo -e "✅ $1 is installed: $(which $1)"
        return 0
    fi
}

# Print header
print_header "Installing dependencies for Phidata with PostgreSQL/PGVector"

# Check Python version
print_header "Checking Python version"
python3 --version
if [ $? -ne 0 ]; then
    print_error "Python 3 is required but not found"
    exit 1
fi

# Create virtualenv if needed
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected. It's recommended to use a virtualenv."
    read -p "Would you like to create and activate a virtual environment? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_header "Creating virtual environment"
        python3 -m pip install --upgrade virtualenv
        python3 -m virtualenv venv
        source venv/bin/activate
        echo -e "✅ Virtualenv created and activated at $(pwd)/venv"
    else
        echo "Continuing without virtualenv..."
    fi
fi

# Core dependencies
print_header "Installing Phidata and core dependencies"
pip install --upgrade pip
pip install phidata
pip install "sqlalchemy>=2.0.0"

# Check if phidata was installed correctly
python -c "import phi; print(f'Phidata successfully installed!')" || {
    print_error "Failed to import Phidata. Installation may have failed."
    exit 1
}

# Install PostgreSQL-specific packages
print_header "Installing PostgreSQL support packages"
pip install "phi-postgres>=0.2.0" "phi-vectordb>=0.1.0" pg8000 psycopg2-binary

# Google Cloud dependencies
print_header "Installing Google Cloud dependencies"
pip install google-cloud-secret-manager

# Try to install Google Cloud SQL Connector
print_header "Installing Google Cloud SQL Connector"
pip install cloud-sql-python-connector || {
    print_warning "Failed to install cloud-sql-python-connector directly, trying alternative methods..."
    
    # Try with the alternative package name
    pip install google-cloud-sql-connector || {
        print_warning "Could not install google-cloud-sql-connector through pip."
        print_warning "This package may need to be installed manually or via a special process."
        print_warning "Please refer to: https://cloud.google.com/sql/docs/postgres/connect-connectors"
    }
}

# Additional utilities
print_header "Installing additional utilities"
pip install python-dotenv

# Print summary
print_header "Installation Summary"
echo "The following packages should now be installed:"
echo ""
echo "✅ phidata - Phidata agent framework"
echo "✅ sqlalchemy - SQL toolkit and ORM"
echo "✅ phi-postgres - Phidata PostgreSQL support"
echo "✅ phi-vectordb - Phidata vector database support"
echo "✅ pg8000 - PostgreSQL driver"
echo "✅ psycopg2-binary - PostgreSQL driver alternative"
echo "✅ google-cloud-secret-manager - Secret Manager client"
echo "✅ cloud-sql-python-connector - Cloud SQL connector (if available)"
echo "✅ python-dotenv - Environment variable management"
echo ""

# Print next steps
print_header "Next Steps"
echo "1. Configure environment variables:"
echo "   source .env.postgres"
echo ""
echo "2. Test your PostgreSQL connection configuration:"
echo "   ./test_postgres_connection.py"
echo ""
echo "3. When Terraform has provisioned the infrastructure, set up the PostgreSQL schema:"
echo "   python scripts/setup_postgres_pgvector.py --apply --schema llm"
echo ""
echo "4. Register a Phidata agent with PostgreSQL storage:"
echo "   See examples/register_phidata_postgres_agent.py"
