# TODO: Consider adding connection pooling configuration
"""
        name="postgres-node",
        config={
            "droplet_id": "existing-droplet-id",  # ID of existing droplet
            "droplet_name": "ubuntu-s-2vcpu-8gb-160gb-intel-sfo2-01",  # Name for reference
            "db_name": "conductor",
            "db_user": "conductor",
            "db_password": "...",  # Pulumi config key
            "ssh_private_key": "...",  # Pulumi config key
            "allowed_hosts": ["10.120.0.0/16"],  # VPC CIDR
            "python_packages": ["superagi", "autogen", "weaviate-client", "psycopg2-binary", "langfuse"]
        },
        opts=ResourceOptions(...)
    )
"""
    """
    """
        super().__init__("cherry_ai:postgres:Component", name, None, opts)

        self.config = config
        self.droplet_id = config.get("droplet_id")
        self.droplet_name = config.get("droplet_name", "app-node")
        self.db_name = config.get("db_name", "conductor")
        self.db_user = config.get("db_user", "conductor")
        self.db_password = config.get("db_password")
        self.ssh_private_key = config.get("ssh_private_key")
        self.allowed_hosts = config.get("allowed_hosts", ["10.120.0.0/16"])
        self.python_packages = config.get(
            "python_packages", ["superagi", "autogen", "weaviate-client", "psycopg2-binary", "langfuse"]
        )
        self.venv_path = config.get("venv_path", "/opt/cherry_ai/venv")
        self.app_path = config.get("app_path", "/opt/cherry_ai")

        # Get existing droplet by ID
        self.droplet = do.get_droplet(id=self.droplet_id)

        # Setup connection for remote commands
        connection = command.remote.ConnectionArgs(
            host=self.droplet.ipv4_address,
            private_key=self.ssh_private_key,
        )

        # Install PostgreSQL 16 and dependencies
        self.install_postgres = command.remote.Command(
            f"{name}-install-postgres",
            connection=connection,
            create="""
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
            """
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
            """
            f"{name}-setup-database",
            connection=connection,
            create=Output.concat(
                """
                echo "Setting up PostgreSQL database and user..."
                
                # Create database if not exists
                sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '"""
                """'" | grep -q 1 || \
                    sudo -u postgres psql -c "CREATE DATABASE """
                """;"
                
                # Create user if not exists
                sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '"""
                """'" | grep -q 1 || \
                    sudo -u postgres psql -c "CREATE USER """
                """ WITH ENCRYPTED PASSWORD '"""
                """';"
                
                # Grant privileges
                sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE """
                """ TO """
                """;"
                
                # Enable pgvector extension
                sudo -u postgres psql -d """
                """ -c "CREATE EXTENSION IF NOT EXISTS vector;"
                
                # Enable additional useful extensions
                sudo -u postgres psql -d """
                """ -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"
                sudo -u postgres psql -d """
                """ -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
                
                echo "Database setup completed successfully"
                """
        allowed_hosts_lines = "\n".join(
            [f"host    {self.db_name}    {self.db_user}    {host}    md5" for host in self.allowed_hosts]
        )

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
# Allow connections from VPC network for cherry_ai
"""
                """
                sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf
                
                # Restart PostgreSQL to apply changes
                systemctl restart postgresql
                
                echo "PostgreSQL network configuration completed"
                """
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
                mkdir -p """
                """
                if [ ! -d """
                """
                    git clone https://github.com/ai-cherry/cherry_ai-main.git """
                """
                    cd """
                """
                python3 -m venv """
                """
                """
                """
                """
                """/bin/pip install """
                """
                mkdir -p """
                """
                echo "Python environment setup completed"
                """
            f"{name}-create-service",
            connection=connection,
            create=Output.concat(
                """
                echo "Creating systemd service for conductor..."
                
                # Create systemd service file
                cat > /etc/systemd/system/cherry_ai-api.service << 'EOF'
[Unit]
Description=Cherry AI API
After=network.target postgresql.service

[Service]
Type=simple
WorkingDirectory="""
                """
Environment="PYTHONPATH="""
                """"
Environment="POSTGRES_DSN=postgres://"""
                """:"""
                """@localhost/"""
                """"
ExecStart="""
                """
                echo "Systemd service created successfully"
                """
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
            """
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
                    port_range="8080",  # cherry_ai API
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
                "postgres_dsn": Output.concat(
                    "postgres://",
                    self.db_user,
                    ":",
                    self.db_password,
                    "@",
                    self.droplet.ipv4_address,
                    ":5432/",
                    self.db_name,
                ),
                "api_endpoint": Output.concat("http://", self.droplet.ipv4_address, ":8080"),
                "langfuse_endpoint": Output.concat("http://", self.droplet.ipv4_address, ":3000"),
                "venv_path": self.venv_path,
            }
        )
