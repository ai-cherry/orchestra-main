#!/bin/bash
# Startup script for AI Orchestra GCP Workstation

set -e

# Print banner
echo "======================================================================"
echo "                    AI ORCHESTRA WORKSTATION STARTUP                   "
echo "======================================================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Environment: ${ENV}"
echo "======================================================================"

# Configure Google Cloud SDK
echo "Configuring Google Cloud SDK..."
gcloud config set project "${PROJECT_ID}"
gcloud config set compute/region "${REGION}"
gcloud config set compute/zone "${REGION}-a"
gcloud auth list

# Check for service account credentials
if [ -f "/home/user/orchestra/.gcp-credentials.json" ]; then
  echo "Using service account credentials from mounted file"
  export GOOGLE_APPLICATION_CREDENTIALS="/home/user/orchestra/.gcp-credentials.json"
  gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
elif [ -f "/secrets/service-account.json" ]; then
  echo "Using service account credentials from secrets volume"
  export GOOGLE_APPLICATION_CREDENTIALS="/secrets/service-account.json"
  gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
fi

# Create symlink to poetry binary for the user
if [ ! -f "/home/user/.local/bin/poetry" ]; then
  echo "Creating symlink to Poetry..."
  mkdir -p /home/user/.local/bin
  ln -s /opt/poetry/bin/poetry /home/user/.local/bin/poetry
fi

# Initialize orchestra environment if not already done
if [ ! -f "/home/user/orchestra/.initialized" ]; then
  echo "Initializing orchestra environment..."
  
  # Check if Git repository exists
  if [ ! -d "/home/user/orchestra/.git" ]; then
    echo "Cloning AI Orchestra repository..."
    # Check if we have a repository URL in an environment variable
    if [ -n "${ORCHESTRA_REPO_URL}" ]; then
      git clone "${ORCHESTRA_REPO_URL}" /home/user/orchestra-temp
      mv /home/user/orchestra-temp/* /home/user/orchestra/
      mv /home/user/orchestra-temp/.git* /home/user/orchestra/
      rmdir /home/user/orchestra-temp
    else
      echo "No repository URL provided, skipping clone"
    fi
  fi
  
  # Create .env file if it doesn't exist
  if [ ! -f "/home/user/orchestra/.env" ]; then
    echo "Creating default .env file..."
    cat > /home/user/orchestra/.env << EOF
PROJECT_ID=${PROJECT_ID}
REGION=${REGION}
ENVIRONMENT=${ENV}
EOF
  fi
  
  # Initialize poetry environment if pyproject.toml exists
  if [ -f "/home/user/orchestra/pyproject.toml" ]; then
    echo "Installing project dependencies with Poetry..."
    cd /home/user/orchestra
    poetry install
  fi
  
  # Mark as initialized
  touch /home/user/orchestra/.initialized
  echo "Initialization complete"
fi

# Sync project files from Cloud Storage if configured
if [ -n "${ORCHESTRA_BUCKET}" ]; then
  echo "Syncing project files from ${ORCHESTRA_BUCKET}..."
  gsutil -m rsync -r "gs://${ORCHESTRA_BUCKET}/workspace/" /home/user/orchestra/ || echo "Warning: Bucket sync failed"
fi

# Set up automatic sync to Cloud Storage
if [ -n "${ORCHESTRA_BUCKET}" ]; then
  echo "Setting up automatic sync to ${ORCHESTRA_BUCKET}..."
  # Create sync script
  cat > /opt/orchestra/scripts/sync-to-bucket.sh << EOF
#!/bin/bash
echo "Syncing to bucket ${ORCHESTRA_BUCKET}..."
gsutil -m rsync -r -x ".cache/|.venv/|__pycache__/|*.pyc|.git/" /home/user/orchestra/ "gs://${ORCHESTRA_BUCKET}/workspace/"
EOF
  chmod +x /opt/orchestra/scripts/sync-to-bucket.sh
  
  # Create cron job for sync (every 10 minutes)
  echo "*/10 * * * * /opt/orchestra/scripts/sync-to-bucket.sh >/dev/null 2>&1" | crontab -
  
  # Set up sync on terminal exit
  echo "trap '/opt/orchestra/scripts/sync-to-bucket.sh' EXIT" >> /home/user/.bashrc
fi

# Configure git
if [ ! -f "/home/user/orchestra/.gitconfig" ]; then
  echo "Configuring Git..."
  git config --global init.defaultBranch main
  
  # Use username from environment if available
  if [ -n "${GIT_USER_NAME}" ]; then
    git config --global user.name "${GIT_USER_NAME}"
  fi
  
  if [ -n "${GIT_USER_EMAIL}" ]; then
    git config --global user.email "${GIT_USER_EMAIL}"
  fi
fi

# Set up Artifact Registry authentication if available
if [ -n "${PROJECT_ID}" ]; then
  echo "Setting up Artifact Registry authentication..."
  gcloud auth configure-docker "us-docker.pkg.dev" --quiet
fi

# Configure application-specific settings
if [ -f "/home/user/orchestra/setup_env.sh" ]; then
  echo "Running project-specific setup script..."
  bash /home/user/orchestra/setup_env.sh
fi

# Start any background services if needed
if [ -f "/opt/orchestra/scripts/start-services.sh" ]; then
  echo "Starting background services..."
  sudo /opt/orchestra/scripts/start-services.sh
fi

# Create help file
cat > /opt/orchestra/scripts/help.txt << EOF
AI Orchestra Workstation Commands:
---------------------------------
orchestrate setup      - Set up the development environment
orchestrate run        - Run the local development server
orchestrate test       - Run tests
orchestrate deploy     - Deploy to Cloud Run
orchestrate sync       - Sync files with Cloud Storage
orchestrate vertex     - Interact with Vertex AI
orchestrate help       - Show this help message

Environment Information:
-----------------------
Project ID:  ${PROJECT_ID}
Region:      ${REGION}
Environment: ${ENV}
EOF

# Create orchestrate script
cat > /opt/orchestra/scripts/orchestrate.sh << EOF
#!/bin/bash
# Main orchestration script for AI Orchestra

set -e

CMD="\$1"
shift

case "\$CMD" in
  setup)
    echo "Setting up development environment..."
    cd /home/user/orchestra
    poetry install
    ;;
  run)
    echo "Running local development server..."
    cd /home/user/orchestra
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ;;
  test)
    echo "Running tests..."
    cd /home/user/orchestra
    poetry run pytest "\$@"
    ;;
  deploy)
    echo "Deploying to Cloud Run..."
    cd /home/user/orchestra
    ./deploy_to_cloud_run.sh
    ;;
  sync)
    echo "Syncing files with Cloud Storage..."
    /opt/orchestra/scripts/sync-to-bucket.sh
    ;;
  vertex)
    echo "Interacting with Vertex AI..."
    cd /home/user/orchestra
    poetry run python -m agent.core.vertex_operations "\$@"
    ;;
  help)
    cat /opt/orchestra/scripts/help.txt
    ;;
  *)
    echo "Unknown command: \$CMD"
    cat /opt/orchestra/scripts/help.txt
    exit 1
    ;;
esac
EOF
chmod +x /opt/orchestra/scripts/orchestrate.sh

# Keep the container running
echo "Workstation startup complete!"
if [ "$1" = "-d" ]; then
  # Run in daemon mode
  tail -f /dev/null
else
  # Interactive mode
  exec "$@"
fi