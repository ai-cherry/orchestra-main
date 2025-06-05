#!/bin/bash

# Cherry AI Deployment Fix Script
# Addresses root causes of mock data persistence and deployment failures

set -e

echo "🔧 CHERRY AI DEPLOYMENT FIX SCRIPT"
echo "=================================="
echo "This script will fix the root causes of deployment issues"
echo ""

# Configuration
LAMBDA_IP="150.136.94.139"
CHERRY_DOMAIN="cherry-ai.me"
USERNAME="ubuntu"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📋 Pre-flight checks...${NC}"

# Check SSH access to Lambda server
echo -n "Checking SSH access to Lambda server... "
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no $USERNAME@$LAMBDA_IP "echo 'OK'" &>/dev/null; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo "Cannot connect to Lambda server. Please ensure SSH access is configured."
    exit 1
fi

echo ""
echo -e "${YELLOW}🔍 STEP 1: Identifying Current State${NC}"
echo "======================================"

# Find where files are actually located
echo -e "${BLUE}Finding orchestrator files on server...${NC}"
ssh $USERNAME@$LAMBDA_IP << 'EOF'
echo "Searching for orchestrator files..."
find /opt/orchestra /var/www /home/ubuntu -name "*orchestrator*.html" -o -name "*orchestrator*.js" 2>/dev/null | grep -v node_modules | while read file; do
    echo "Found: $file"
    echo "  Modified: $(stat -c '%y' "$file" 2>/dev/null | cut -d. -f1)"
    echo "  Size: $(stat -c '%s' "$file" 2>/dev/null) bytes"
done
EOF

echo ""
echo -e "${YELLOW}🔍 STEP 2: Checking Nginx Configuration${NC}"
echo "========================================"

ssh $USERNAME@$LAMBDA_IP << 'EOF'
# Check nginx root directory
echo "Nginx document root:"
grep -h "root" /etc/nginx/sites-enabled/* | grep -v "#" | head -1

# Check for caching
echo -e "\nChecking for caching directives:"
grep -h "expires\|cache" /etc/nginx/sites-enabled/* | grep -v "#" || echo "No caching directives found"

# Check orchestrator location
echo -e "\nOrchestrator location block:"
grep -A5 "orchestrator" /etc/nginx/sites-enabled/* || echo "No orchestrator location found"
EOF

echo ""
echo -e "${YELLOW}🛠️ STEP 3: Creating Enhanced JavaScript${NC}"
echo "========================================"

# Create the enhanced JavaScript file locally
cat > cherry-ai-orchestrator-enhanced.js << 'JSEOF'
// Cherry AI Orchestrator - Enhanced Version with Real API
// Version: 2.0 - No Mock Data

const API_BASE_URL = '/api';  // Will be proxied by nginx to :8000

class CherryOrchestrator {
    constructor() {
        this.currentTab = 'search';
        this.searchMode = 'normal';
        this.currentPersona = 'cherry';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAPIHealth();
        setInterval(() => this.checkAPIHealth(), 30000);
    }

    async checkAPIHealth() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.updateStatus('🟢 Connected', 'success');
            } else {
                this.updateStatus('🟡 Limited', 'warning');
            }
        } catch (error) {
            console.error('API health check failed:', error);
            this.updateStatus('🔴 Offline', 'error');
        }
    }

    updateStatus(text, type) {
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
            statusEl.textContent = text;
            statusEl.className = `status-indicator ${type}`;
        }
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Search functionality
        const searchButton = document.getElementById('search-button');
        if (searchButton) {
            searchButton.addEventListener('click', () => this.performSearch());
        }

        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.performSearch();
            });
        }

        // Persona selection
        document.querySelectorAll('.persona-card').forEach(card => {
            card.addEventListener('click', (e) => {
                this.selectPersona(e.currentTarget.dataset.persona);
            });
        });

        // Search mode selection
        document.querySelectorAll('.mode-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.selectSearchMode(e.target.dataset.mode);
            });
        });
    }

    switchTab(tabName) {
        this.currentTab = tabName;
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.toggle('active', button.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });

        // Load tab-specific data
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        const contentArea = document.getElementById(`${tabName}-content`);
        if (!contentArea) return;

        contentArea.innerHTML = '<div class="loading">Loading...</div>';

        try {
            let data;
            switch(tabName) {
                case 'agents':
                    data = await this.fetchAgents();
                    this.displayAgents(data);
                    break;
                case 'workflows':
                    data = await this.fetchWorkflows();
                    this.displayWorkflows(data);
                    break;
                case 'knowledge':
                    data = await this.fetchKnowledge();
                    this.displayKnowledge(data);
                    break;
                case 'monitoring':
                    data = await this.fetchMonitoring();
                    this.displayMonitoring(data);
                    break;
            }
        } catch (error) {
            contentArea.innerHTML = `<div class="error">Failed to load ${tabName} data: ${error.message}</div>`;
        }
    }

    async performSearch() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) {
            alert('Please enter a search query');
            return;
        }

        const resultsArea = document.getElementById('search-results');
        resultsArea.innerHTML = '<div class="loading">Searching...</div>';

        try {
            const response = await fetch(`${API_BASE_URL}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    mode: this.searchMode,
                    persona: this.currentPersona
                })
            });

            if (!response.ok) {
                throw new Error(`Search failed: ${response.status}`);
            }

            const results = await response.json();
            this.displaySearchResults(results);
        } catch (error) {
            resultsArea.innerHTML = `<div class="error">Search failed: ${error.message}</div>`;
        }
    }

    displaySearchResults(results) {
        const resultsArea = document.getElementById('search-results');
        
        if (!results || results.length === 0) {
            resultsArea.innerHTML = '<div class="no-results">No results found</div>';
            return;
        }

        let html = '<div class="results-list">';
        results.forEach(result => {
            html += `
                <div class="result-item">
                    <h3>${result.title}</h3>
                    <p>${result.snippet}</p>
                    <div class="result-meta">
                        <span class="source">${result.source}</span>
                        <span class="relevance">Relevance: ${(result.relevance * 100).toFixed(1)}%</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        resultsArea.innerHTML = html;
    }

    selectPersona(persona) {
        this.currentPersona = persona;
        document.querySelectorAll('.persona-card').forEach(card => {
            card.classList.toggle('active', card.dataset.persona === persona);
        });
    }

    selectSearchMode(mode) {
        this.searchMode = mode;
        document.querySelectorAll('.mode-button').forEach(button => {
            button.classList.toggle('active', button.dataset.mode === mode);
        });
    }

    // API Methods
    async fetchAgents() {
        const response = await fetch(`${API_BASE_URL}/agents`);
        return response.json();
    }

    async fetchWorkflows() {
        const response = await fetch(`${API_BASE_URL}/workflows`);
        return response.json();
    }

    async fetchKnowledge() {
        const response = await fetch(`${API_BASE_URL}/knowledge`);
        return response.json();
    }

    async fetchMonitoring() {
        const response = await fetch(`${API_BASE_URL}/monitoring/metrics`);
        return response.json();
    }

    // Display Methods
    displayAgents(agents) {
        const content = document.getElementById('agents-content');
        if (!agents || agents.length === 0) {
            content.innerHTML = '<div class="empty-state">No agents configured</div>';
            return;
        }

        let html = '<div class="agents-grid">';
        agents.forEach(agent => {
            html += `
                <div class="agent-card">
                    <h3>${agent.name}</h3>
                    <p>${agent.description}</p>
                    <div class="agent-status ${agent.status}">${agent.status}</div>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    }

    displayWorkflows(workflows) {
        const content = document.getElementById('workflows-content');
        if (!workflows || workflows.length === 0) {
            content.innerHTML = '<div class="empty-state">No workflows found</div>';
            return;
        }

        let html = '<div class="workflows-list">';
        workflows.forEach(workflow => {
            html += `
                <div class="workflow-item">
                    <h3>${workflow.name}</h3>
                    <p>Status: ${workflow.status}</p>
                    <p>Last run: ${new Date(workflow.last_run).toLocaleString()}</p>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    }

    displayKnowledge(knowledge) {
        const content = document.getElementById('knowledge-content');
        content.innerHTML = `
            <div class="knowledge-stats">
                <div class="stat-card">
                    <h3>Total Documents</h3>
                    <p class="stat-value">${knowledge.total_documents || 0}</p>
                </div>
                <div class="stat-card">
                    <h3>Vector Embeddings</h3>
                    <p class="stat-value">${knowledge.total_embeddings || 0}</p>
                </div>
                <div class="stat-card">
                    <h3>Last Updated</h3>
                    <p class="stat-value">${knowledge.last_updated || 'Never'}</p>
                </div>
            </div>
        `;
    }

    displayMonitoring(metrics) {
        const content = document.getElementById('monitoring-content');
        content.innerHTML = `
            <div class="monitoring-dashboard">
                <div class="metric-card">
                    <h3>API Requests (24h)</h3>
                    <p class="metric-value">${metrics.api_requests_24h || 0}</p>
                </div>
                <div class="metric-card">
                    <h3>Average Response Time</h3>
                    <p class="metric-value">${metrics.avg_response_time || 0}ms</p>
                </div>
                <div class="metric-card">
                    <h3>Error Rate</h3>
                    <p class="metric-value">${metrics.error_rate || 0}%</p>
                </div>
                <div class="metric-card">
                    <h3>System Health</h3>
                    <p class="metric-value ${metrics.health_status}">${metrics.health_status || 'Unknown'}</p>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.orchestrator = new CherryOrchestrator();
});
JSEOF

echo -e "${GREEN}✅ Enhanced JavaScript created${NC}"

echo ""
echo -e "${YELLOW}🚀 STEP 4: Deploying Fixed Files${NC}"
echo "=================================="

# Copy files to server
echo -e "${BLUE}Copying enhanced JavaScript to server...${NC}"
scp cherry-ai-orchestrator-enhanced.js $USERNAME@$LAMBDA_IP:/tmp/

# Deploy and fix on server
ssh $USERNAME@$LAMBDA_IP << 'EOF'
# Ensure directory exists
sudo mkdir -p /opt/orchestra
sudo chown ubuntu:ubuntu /opt/orchestra

# Copy enhanced JS
cp /tmp/cherry-ai-orchestrator-enhanced.js /opt/orchestra/
echo "✅ Enhanced JavaScript deployed"

# Find and update HTML files to use enhanced JS
echo -e "\nUpdating HTML files to use enhanced JavaScript..."
find /opt/orchestra /var/www -name "*orchestrator*.html" 2>/dev/null | while read html_file; do
    if [ -w "$html_file" ]; then
        # Backup original
        sudo cp "$html_file" "${html_file}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Update script reference
        sudo sed -i 's/cherry-ai-orchestrator\.js/cherry-ai-orchestrator-enhanced.js/g' "$html_file"
        echo "Updated: $html_file"
    fi
done

# Fix nginx caching
echo -e "\nFixing nginx configuration..."
sudo tee /etc/nginx/conf.d/no-cache.conf > /dev/null << 'NGINX'
# Disable caching for orchestrator
location ~* \.(html|js|css)$ {
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    add_header Pragma "no-cache";
}
NGINX

# Update main nginx config if needed
if ! grep -q "orchestrator" /etc/nginx/sites-enabled/default; then
    echo -e "\nAdding orchestrator location to nginx..."
    sudo tee -a /etc/nginx/sites-enabled/default > /dev/null << 'NGINX'

    location /orchestrator/ {
        alias /opt/orchestra/;
        try_files $uri $uri/ /orchestrator/cherry-ai-orchestrator-final.html;
        
        # Disable caching
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
NGINX
fi

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
echo "✅ Nginx restarted with no-cache configuration"
EOF

echo ""
echo -e "${YELLOW}🔍 STEP 5: Verifying Deployment${NC}"
echo "================================="

# Test the deployment
echo -e "${BLUE}Testing orchestrator endpoint...${NC}"
RESPONSE=$(curl -s -I http://$LAMBDA_IP/orchestrator/ | head -1)
echo "Response: $RESPONSE"

echo -e "\n${BLUE}Testing API endpoint...${NC}"
API_RESPONSE=$(ssh $USERNAME@$LAMBDA_IP "curl -s http://localhost:8000/api/health | jq -r '.status' 2>/dev/null || echo 'Failed'")
echo "API Status: $API_RESPONSE"

echo ""
echo -e "${YELLOW}📋 STEP 6: Cherry Domain Fix${NC}"
echo "=============================="

# Check current DNS
echo -e "${BLUE}Current DNS for cherry-ai.me:${NC}"
nslookup cherry-ai.me | grep -A2 "answer:" || echo "DNS lookup failed"

echo -e "\n${YELLOW}To fix cherry-ai.me deployment:${NC}"
echo "1. Update DNS A record to point to: $LAMBDA_IP"
echo "2. Configure SSH access:"
echo "   ssh-copy-id ubuntu@cherry-ai.me"
echo "3. Once DNS propagates, run:"
echo "   ./deploy_working_interface.sh"

echo ""
echo -e "${GREEN}✅ DEPLOYMENT FIXES APPLIED${NC}"
echo "============================="
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Clear your browser cache (Ctrl+Shift+Delete)"
echo "2. Visit: http://$LAMBDA_IP/orchestrator/"
echo "3. Verify you see the real API data, not mock data"
echo "4. Check all tabs are working with real data"
echo ""
echo -e "${YELLOW}If issues persist:${NC}"
echo "- Try incognito/private browsing mode"
echo "- Check browser console for errors (F12)"
echo "- Run: python3 diagnose_cherry_deployment.py"

# Clean up
rm -f cherry-ai-orchestrator-enhanced.js