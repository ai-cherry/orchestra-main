#!/bin/bash
# deploy_admin_ui.sh
# Run this script on your local machine to deploy the Admin UI (dashboard) and reconfigure Nginx.

set -e # Exit immediately if a command exits with a non-zero status.

LAMBDA_HOST="ubuntu@150.136.94.139"
REMOTE_PROJECT_DIR="/opt/cherry-ai"

echo "🚀 Starting Admin UI (Dashboard) Deployment to Lambda Labs..."

# Step 1: Copy necessary files to the server
echo "📦 Copying service and Nginx configuration files to server..."
scp ./dashboard-ui.service "${LAMBDA_HOST}:${REMOTE_PROJECT_DIR}/dashboard-ui.service.tmp"
scp ./nginx_cherry_ai_dashboard.conf "${LAMBDA_HOST}:${REMOTE_PROJECT_DIR}/nginx_cherry_ai_dashboard.conf.tmp"

# Step 2: Execute remote commands to set up services and Nginx
echo "⚙️  Configuring server (this may take a few minutes for npm install & build)..."
ssh -t "$LAMBDA_HOST" << EOF
    set -e
    echo "    ➡️  Moving to project directory: ${REMOTE_PROJECT_DIR}"
    cd "${REMOTE_PROJECT_DIR}"

    echo "    📦 Ensuring Node.js and npm are installed..."
    if ! command -v node &> /dev/null; then
        echo "        Installing Node.js (LTS)..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "        Node.js is already installed."
    fi
    if ! command -v npm &> /dev/null; then # Should come with Node.js but check anyway
        echo "        Installing npm (usually comes with Node.js)..."
        sudo apt-get install -y npm
    else
        echo "        npm is already installed."
    fi

    echo "    🔧 Setting up Dashboard UI service (dashboard-ui.service)..."
    echo "        Moving dashboard-ui.service file to /etc/systemd/system/..."
    sudo mv "${REMOTE_PROJECT_DIR}/dashboard-ui.service.tmp" /etc/systemd/system/dashboard-ui.service
    sudo chmod 644 /etc/systemd/system/dashboard-ui.service
    sudo systemctl daemon-reload
    
    echo "        Stopping existing dashboard-ui service if running..."
    sudo systemctl stop dashboard-ui.service || true # Allow failure if not running

    echo "        Installing Dashboard dependencies (npm install --omit=dev in ${REMOTE_PROJECT_DIR}/dashboard)..."
    cd "${REMOTE_PROJECT_DIR}/dashboard"
    npm install --omit=dev --legacy-peer-deps # Added --legacy-peer-deps for compatibility
    
    echo "        Building Dashboard application (npm run build in ${REMOTE_PROJECT_DIR}/dashboard)..."
    # Ensure NEXT_PUBLIC_API_URL=/api is used from the service file by the build process if possible,
    # or ensure it's available in the environment if build happens outside service context.
    # The service file sets it, so starting the service will use it for its build step (ExecStartPre).
    cd "${REMOTE_PROJECT_DIR}" # Return to project root for systemctl commands

    echo "        Enabling and starting dashboard-ui.service..."
    sudo systemctl enable dashboard-ui.service
    sudo systemctl restart dashboard-ui.service # This will run ExecStartPre (npm install, npm build) then ExecStart (npm start)

    echo "    🛡️  Configuring Nginx..."
    echo "        Moving new Nginx configuration file..."
    sudo mv "${REMOTE_PROJECT_DIR}/nginx_cherry_ai_dashboard.conf.tmp" /etc/nginx/sites-available/cherry-ai-dashboard.conf
    
    echo "        Disabling default Nginx site if it exists and is a symlink..."
    if [ -L /etc/nginx/sites-enabled/default ]; then
        sudo rm /etc/nginx/sites-enabled/default
    fi
    # Also remove cherry-ai if it was the previous config for the API at root
    if [ -L /etc/nginx/sites-enabled/cherry-ai ]; then
        sudo rm /etc/nginx/sites-enabled/cherry-ai
    fi

    echo "        Enabling new Nginx site configuration (cherry-ai-dashboard.conf)..."
    sudo ln -sf /etc/nginx/sites-available/cherry-ai-dashboard.conf /etc/nginx/sites-enabled/cherry-ai-dashboard.conf
    
    echo "        Testing Nginx configuration..."
    sudo nginx -t
    
    echo "        Reloading Nginx..."
    sudo systemctl reload nginx

    echo "    🔄 Ensuring API backend (cherry-ai.service) is running..."
    sudo systemctl restart cherry-ai.service
    
    echo "    🔍 Checking service statuses (ignore errors if a service is just starting)..."
    sudo systemctl status dashboard-ui.service --no-pager || true
    sudo systemctl status cherry-ai.service --no-pager || true
    sudo systemctl status nginx --no-pager || true

    echo "    🎉 Remote deployment steps completed."
EOF

echo "✅ Admin UI (Dashboard) Deployment Script Execution Finished."
echo ""
echo "🖥️  Please check http://cherry-ai.me in your browser after a minute or two."
echo "    The first build of the dashboard might take some time."
_API_URL=/api`).
    *   Enable and start the `dashboard-ui.service`.
    *   Disable the old default Nginx site (if it exists and conflicts).
    *   Enable the new Nginx site configuration for the dashboard and API.
    *   Reload Nginx.
    *   Ensure the `cherry-ai.service` (FastAPI backend) is also started/restarted.

Here is the deployment script: 