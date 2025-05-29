"""
PostgreSQL Component for Pulumi Infrastructure
==============================================
Provisions an existing DigitalOcean droplet as a PostgreSQL 16 + pgvector database node.
Also sets up the Python virtual environment for the orchestrator application.

Usage:
    from .postgres_component import PostgresComponent

    postgres_node = PostgresComponent(
        name="postgres-node",
        config={
            "droplet_id": "existing-droplet-id",  # ID of existing droplet
            "droplet_name": "ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01",  # Name for reference
            "db_name": "orchestrator",
            "db_user": "orchestrator",
            "db_password": "...",  # Pulumi config key
            "ssh_private_key": "...",  # Pulumi config key
            "allowed_hosts": ["10.120.0.0/16"],  # VPC CIDR
            "python_packages": ["superagi", "autogen", "weaviate-client", "psycopg2-binary", "langfuse"]
        },
        opts=ResourceOptions(...)
    )
"""

from typing import Any, Dict, List, Optional

import pulumi
import pulumi_digitalocean as do
import pulumi_command as command
from pulumi import ComponentResource, ResourceOptions, Output


class PostgresComponent(ComponentResource):
    """
    Reusable PostgreSQL component for the AI Orchestra system.
    Configures an existing DigitalOcean droplet with PostgreSQL 16 + pgvector.
    Also sets up the Python virtual environment for the orchestrator.
    """

    def __init__(
        self, name: str, config: Dict[str, Any], opts: Optional[ResourceOptions] = None
    ):
        super().__init__("orchestra:postgres:Component", name, None, opts)

        self.config = config
        self.droplet_id = config.get("droplet_id")
        self.droplet_name = config.get("droplet_name", "app-node")
        self.db_name = config.get("db_name", "orchestrator")
        self.db_user = config.get("db_user", "orchestrator")
        self.db_password = config.get("db_password")
        self.ssh_private_key = config.get("ssh_private_key")
        self.allowed_hosts = config.get("allowed_hosts", ["10.120.0.0/16"])
        self.python_packages = config.get("python_packages", [
            "superagi", "autogen", "weaviate-client", "psycopg2-binary", "langfuse"
        ])
        self.venv_path = config.get("venv_path", "/opt/orchestra/venv")
        self.app_path = config.get("app_path", "/opt/orchestra")

        # Get existing droplet by ID
        self.droplet = do.get_droplet(id=self.droplet_id)

        # Setup connection for remote commands
        connection = command.remote.ConnectionArgs(
            host=self.droplet.ipv4_address,
            user="root",
            private_key=self.ssh_private_key,
        )

        # Install PostgreSQL 16 and dependencies
        self.install_postgres = command.remote.Command(
            f"{name}-install-postgres",
            connection=connection,
            create="""
                # Add PostgreSQL repository
                echo "Installing PostgreSQL 16..."
                
                # Create the repository configuration file
                sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
                
                # Import the repository signing key
                wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
                
                # Update package lists
                apt-get update
                
                # Install PostgreSQL 16 and development libraries
                apt-get install -y postgresql-16 postgresql-contrib-16 postgresql-server-dev-16 libpq-dev
                
                # Ensure PostgreSQL is running
                systemctl enable postgresql
                systemctl start postgresql
                
                echo "PostgreSQL 16 installed successfully"
            """,
            opts=ResourceOptions(parent=self),
        )

        # Install pgvector extension
        self.install_pgvector = command.remote.Command(
            f"{name}-install-pgvector",
            connection=connection,
            create="""
                echo "Installing pgvector extension..."
                
                # Install build dependencies
                apt-get install -y git build-essential postgresql-server-dev-16
                
                # Clone and build pgvector
                cd /tmp
                if [ ! -d "pgvector" ]; then
                    git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
                fi
                cd pgvector
                make
                make install
                
                echo "pgvector extension installed successfully"
            """,
            opts=ResourceOptions(parent=self, depends_on=[self.install_postgres]),
        )

        # Create database, user, and enable extensions
        self.setup_database = command.remote.Command(
            f"{name}-setup-database",
            connection=connection,
            create=Output.concat(
                """
                echo "Setting up PostgreSQL database and user..."
                
                # Create database if not exists
                sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '""", self.db_name, """'" | grep -q 1 || \
                    sudo -u postgres psql -c "CREATE DATABASE """, self.db_name, """;"
                
                # Create user if not exists
                sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '""", self.db_user, """'" | grep -q 1 || \
                    sudo -u postgres psql -c "CREATE USER """, self.db_user, """ WITH ENCRYPTED PASSWORD '""", self.db_password, """';"
                
                # Grant privileges
                sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE """, self.db_name, """ TO """, self.db_user, """;"
                
                # Enable pgvector extension
                sudo -u postgres psql -d """, self.db_name, """ -c "CREATE EXTENSION IF NOT EXISTS vector;"
                
                # Enable additional useful extensions
                sudo -u postgres psql -d """, self.db_name, """ -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
                sudo -u postgres psql -d """, self.db_name, """ -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
                
                echo "Database setup completed successfully"
                """
            ),
            opts=ResourceOptions(parent=self, depends_on=[self.install_pgvector]),
        )

        # Configure PostgreSQL for network access
        allowed_hosts_lines = "\n".join([
            f"host    {self.db_name}    {self.db_user}    {host}    md5"
            for host in self.allowed_hosts
        ])

        self.configure_network = command.remote.Command(
            f"{name}-configure-network",
            connection=connection,
            create=Output.concat(
                """
                echo "Configuring PostgreSQL network access..."
                
                # Backup pg_hba.conf
                cp /etc/postgresql/16/main/pg_hba.conf /etc/postgresql/16/main/pg_hba.conf.bak
                
                # Add VPC network access to pg_hba.conf
                cat >> /etc/postgresql/16/main/pg_hba.conf << 'EOF'
# Allow connections from VPC network for Orchestra
""", allowed_hosts_lines, """
EOF
                
                # Configure postgresql.conf to listen on all interfaces
                sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf
                
                # Restart PostgreSQL to apply changes
                systemctl restart postgresql
                
                echo "PostgreSQL network configuration completed"
                """
            ),
            opts=ResourceOptions(parent=self, depends_on=[self.setup_database]),
        )

        # Setup Python virtual environment
        packages_str = " ".join(self.python_packages)
        
        self.setup_python_env = command.remote.Command(
            f"{name}-setup-python-env",
            connection=connection,
            create=Output.concat(
                """
                echo "Setting up Python virtual environment..."
                
                # Install Python and venv
                apt-get update
                apt-get install -y python3 python3-pip python3-venv git
                
                # Create app directory if not exists
                mkdir -p """, self.app_path, """
                
                # Clone repository if not exists
                if [ ! -d """, self.app_path, """/.git ]; then
                    git clone https://github.com/ai-cherry/orchestra-main.git """, self.app_path, """
                else
                    cd """, self.app_path, """ && git pull
                fi
                
                # Create and activate virtual environment
                python3 -m venv """, self.venv_path, """
                
                # Install required packages
                """, self.venv_path, """/bin/pip install --upgrade pip
                """, self.venv_path, """/bin/pip install """, packages_str, """
                
                # Create directory for logs
                mkdir -p """, self.app_path, """/logs
                
                echo "Python environment setup completed"
                """
            ),
            opts=ResourceOptions(parent=self),
        )

        # Create systemd service for orchestrator
        self.create_service = command.remote.Command(
            f"{name}-create-service",
            connection=connection,
            create=Output.concat(
                """
                echo "Creating systemd service for orchestrator..."
                
                # Create systemd service file
                cat > /etc/systemd/system/orchestra-api.service << 'EOF'
[Unit]
Description=Orchestra AI API
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=""", self.app_path, """
Environment="PYTHONPATH=""", self.app_path, """"
Environment="POSTGRES_DSN=postgres://""", self.db_user, """:""", self.db_password, """@localhost/""", self.db_name, """"
ExecStart=""", self.venv_path, """/bin/python -m uvicorn core.api.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
                
                # Reload systemd and enable service
                systemctl daemon-reload
                systemctl enable orchestra-api
                
                echo "Systemd service created successfully"
                """
            ),
            opts=ResourceOptions(parent=self, depends_on=[self.setup_python_env]),
        )

        # Setup Langfuse monitoring
        self.setup_langfuse = command.remote.Command(
            f"{name}-setup-langfuse",
            connection=connection,
            create="""
                echo "Setting up Langfuse monitoring..."
                
                # Install Docker if not already installed
                if ! command -v docker &> /dev/null; then
                    apt-get update
                    apt-get install -y docker.io
                    systemctl enable docker
                    systemctl start docker
                fi
                
                # Create docker-compose.yml for Langfuse
                mkdir -p /opt/langfuse
                cat > /opt/langfuse/docker-compose.yml << 'EOF'
version: '3'
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langfuse
      - NEXTAUTH_SECRET=supersecret
      - NEXTAUTH_URL=http://localhost:3000
      - SALT=supersalt
      - NEXT_PUBLIC_SIGN_UP_DISABLED=false
    depends_on:
      - postgres
      
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-postgres-data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Use different port to avoid conflict

volumes:
  langfuse-postgres-data:
EOF
                
                # Start Langfuse
                cd /opt/langfuse
                docker-compose up -d
                
                echo "Langfuse monitoring setup completed"
            """,
            opts=ResourceOptions(parent=self),
        )

        # Setup firewall rules
        self.firewall = do.Firewall(
            f"{name}-firewall",
            droplet_ids=[self.droplet_id],
            inbound_rules=[
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="22",
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="8080",  # Orchestra API
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="5432",  # PostgreSQL
                    source_addresses=self.allowed_hosts,
                ),
                do.FirewallInboundRuleArgs(
                    protocol="tcp",
                    port_range="3000",  # Langfuse UI
                    source_addresses=["0.0.0.0/0", "::/0"],
                ),
            ],
            outbound_rules=[
                do.FirewallOutboundRuleArgs(
                    protocol="tcp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0", "::/0"],
                ),
                do.FirewallOutboundRuleArgs(
                    protocol="udp",
                    port_range="all",
                    destination_addresses=["0.0.0.0/0", "::/0"],
                ),
            ],
            opts=ResourceOptions(parent=self),
        )

        # Export outputs
        self.register_outputs(
            {
                "droplet_id": self.droplet_id,
                "droplet_name": self.droplet_name,
                "db_name": self.db_name,
                "db_user": self.db_user,
                "postgres_dsn": Output.concat("postgres://", self.db_user, ":", self.db_password, "@", self.droplet.ipv4_address, ":5432/", self.db_name),
                "api_endpoint": Output.concat("http://", self.droplet.ipv4_address, ":8080"),
                "langfuse_endpoint": Output.concat("http://", self.droplet.ipv4_address, ":3000"),
                "venv_path": self.venv_path,
            }
        )
