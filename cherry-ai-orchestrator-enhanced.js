// Cherry AI Orchestrator - Enhanced JavaScript Module
// Connects to real Lambda Labs backend services

// Global state management
const AppState = {
    currentPersona: 'cherry',
    currentTab: 'dashboard',
    searchModes: {
        domain: 'summary',
        web: 'creative'
    },
    // Update to use actual Lambda Labs server
    apiEndpoint: 'http://150.136.94.139:8000',
    weaviateEndpoint: 'http://150.136.94.139:8080',
    sessionId: `session_${Date.now()}`,
    activeConnections: new Map(),
    searchHistory: [],
    metrics: {
        apiCalls: 0,
        successRate: 100,
        avgResponseTime: 0
    },
    // Real data storage
    agents: [],
    orchestrations: [],
    workflows: []
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing Cherry AI Orchestrator...');
    
    // Check API connection
    await checkAPIConnection();
    setInterval(checkAPIConnection, 30000);
    
    // Update time
    updateDateTime();
    setInterval(updateDateTime, 60000);
    
    // Load real data
    await loadRealData();
    
    // Load saved preferences
    loadUserPreferences();
    
    // Initialize real-time updates
    initializeRealtimeUpdates();
}

// API Connection Management
async function checkAPIConnection() {
    const statusElement = document.querySelector('.status-dot');
    const statusText = statusElement?.nextElementSibling;
    
    try {
        // Check Cherry AI API
        const response = await fetch(`${AppState.apiEndpoint}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (statusElement) {
                statusElement.style.background = '#4ade80';
                statusText.textContent = 'API Connected';
            }
            updateSystemMetrics(data);
        } else {
            throw new Error('API unhealthy');
        }
        
        // Also check Weaviate
        const weaviateResponse = await fetch(`${AppState.weaviateEndpoint}/v1/.well-known/ready`);
        if (weaviateResponse.ok) {
            console.log('Weaviate is ready');
        }
        
    } catch (error) {
        if (statusElement) {
            statusElement.style.background = '#ef4444';
            statusText.textContent = 'API Offline';
        }
        console.error('API connection error:', error);
    }
}

// Load real data from backend
async function loadRealData() {
    try {
        // Load agents
        const agentsResponse = await fetch(`${AppState.apiEndpoint}/api/agents`);
        if (agentsResponse.ok) {
            AppState.agents = await agentsResponse.json();
            updateAgentsList();
        }
        
        // Load orchestrations
        const orchestrationsResponse = await fetch(`${AppState.apiEndpoint}/api/orchestrations`);
        if (orchestrationsResponse.ok) {
            AppState.orchestrations = await orchestrationsResponse.json();
            updateOrchestrationsList();
        }
        
        // Load workflows
        const workflowsResponse = await fetch(`${AppState.apiEndpoint}/api/workflows`);
        if (workflowsResponse.ok) {
            AppState.workflows = await workflowsResponse.json();
            updateWorkflowsList();
        }
        
    } catch (error) {
        console.error('Failed to load data:', error);
    }
}

// Update UI with real data
function updateAgentsList() {
    const container = document.querySelector('#agents-tab .agents-list');
    if (!container) return;
    
    if (AppState.agents.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                <div style="font-size: 3rem; margin-bottom: 20px;">🤖</div>
                <div>No agents deployed yet</div>
                <button class="search-button" style="margin-top: 20px;" onclick="createAgent('custom')">
                    Create First Agent
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = AppState.agents.map(agent => `
        <div class="agent-card" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>${agent.name}</h4>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        Type: ${agent.type} | Status: ${agent.status} | Created: ${formatTimestamp(agent.created)}
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="action-button" onclick="viewAgentDetails('${agent.id}')">View</button>
                    <button class="action-button" onclick="configureAgent('${agent.id}')">Configure</button>
                    <button class="action-button" style="background: #ef4444;" onclick="deleteAgent('${agent.id}')">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

function updateOrchestrationsList() {
    const container = document.querySelector('#orchestrations-tab .orchestrations-list');
    if (!container) return;
    
    if (AppState.orchestrations.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                <div style="font-size: 3rem; margin-bottom: 20px;">🎼</div>
                <div>No orchestrations running</div>
                <button class="search-button" style="margin-top: 20px;" onclick="deployOrchestration('new')">
                    Start Orchestration
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = AppState.orchestrations.map(orch => `
        <div class="orchestration-card" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 16px;">
            <div>
                <h4>${orch.name}</h4>
                <div style="color: var(--text-secondary); font-size: 0.9rem;">
                    Status: ${orch.status} | Progress: ${orch.progress}% | Started: ${formatTimestamp(orch.started)}
                </div>
                <div style="margin-top: 10px;">
                    <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px;">
                        <div style="background: var(--primary); height: 100%; width: ${orch.progress}%; border-radius: 4px;"></div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

function updateWorkflowsList() {
    const container = document.querySelector('#workflows-tab .workflows-list');
    if (!container) return;
    
    if (AppState.workflows.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--text-tertiary);">
                <div style="font-size: 3rem; margin-bottom: 20px;">🔄</div>
                <div>No workflows defined</div>
                <button class="search-button" style="margin-top: 20px;" onclick="createWorkflow()">
                    Create Workflow
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = AppState.workflows.map(workflow => `
        <div class="workflow-card" style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 16px;">
            <div>
                <h4>${workflow.name}</h4>
                <div style="color: var(--text-secondary); font-size: 0.9rem;">
                    Steps: ${workflow.steps.length} | Last Run: ${workflow.lastRun ? formatTimestamp(workflow.lastRun) : 'Never'}
                </div>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button class="action-button" onclick="editWorkflow('${workflow.id}')">Edit</button>
                    <button class="action-button" onclick="runWorkflow('${workflow.id}')">Run</button>
                </div>
            </div>
        </div>
    `).join('');
}

// Enhanced Search with Weaviate
async function performSearch(type) {
    const inputId = type === 'domain' ? 'domain-search-input' : 'web-search-input';
    const query = document.getElementById(inputId).value.trim();
    
    if (!query) {
        showNotification('Please enter a search query', 'warning');
        return;
    }
    
    // Show loading state
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.classList.remove('hidden');
    resultsContainer.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <span>Searching...</span>
        </div>
    `;
    
    try {
        const searchType = type === 'domain' ? 'internal' : 'external';
        const mode = AppState.searchModes[type];
        
        // For domain search, use Weaviate
        if (type === 'domain') {
            const weaviateQuery = {
                query: `{
                    Get {
                        AgentMemory(
                            nearText: {
                                concepts: ["${query}"]
                            }
                            limit: 10
                        ) {
                            content
                            agent_id
                            memory_type
                            importance
                            created_at
                        }
                    }
                }`
            };
            
            const response = await fetch(`${AppState.weaviateEndpoint}/v1/graphql`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(weaviateQuery)
            });
            
            if (response.ok) {
                const data = await response.json();
                displayWeaviateResults(data, query);
                return;
            }
        }
        
        // Fallback to regular API search
        const response = await fetch(`${AppState.apiEndpoint}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': AppState.sessionId
            },
            body: JSON.stringify({
                query: query,
                mode: mode,
                type: searchType,
                persona: AppState.currentPersona
            })
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        displaySearchResults(data, type);
        
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error">
                <strong>Search failed:</strong> ${error.message}
            </div>
        `;
    }
}

function displayWeaviateResults(data, query) {
    const resultsContainer = document.getElementById('search-results');
    const memories = data.data?.Get?.AgentMemory || [];
    
    if (memories.length === 0) {
        resultsContainer.innerHTML = `
            <div class="results-container">
                <div class="text-center" style="padding: 40px; color: var(--text-tertiary);">
                    No memories found for "${query}"
                </div>
            </div>
        `;
        return;
    }
    
    let html = '<div class="results-container">';
    html += `
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 10px;">Memory Search Results</h3>
            <div style="display: flex; gap: 20px; color: var(--text-secondary);">
                <span>Query: "${query}"</span>
                <span>Source: Weaviate Vector DB</span>
                <span>Results: ${memories.length}</span>
            </div>
        </div>
    `;
    
    memories.forEach((memory, index) => {
        html += `
            <div class="result-item" onclick="expandResult(${index})">
                <div class="result-title">Agent ${memory.agent_id} - ${memory.memory_type}</div>
                <div class="result-snippet">${memory.content}</div>
                <div class="result-meta">
                    <span>Importance: ${memory.importance}</span>
                    <span>Created: ${formatTimestamp(memory.created_at)}</span>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsContainer.innerHTML = html;
}

// Real-time updates
function initializeRealtimeUpdates() {
    // Poll for updates every 5 seconds
    setInterval(async () => {
        await loadRealData();
    }, 5000);
}

// Persona Management
function switchPersona(persona) {
    AppState.currentPersona = persona;
    document.body.setAttribute('data-persona', persona);
    
    // Update UI elements
    document.querySelectorAll('.persona-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-persona="${persona}"]`)?.classList.add('active');
    
    // Update header
    const activePersonaElement = document.getElementById('active-persona');
    if (activePersonaElement) {
        activePersonaElement.textContent = persona.charAt(0).toUpperCase() + persona.slice(1);
    }
    
    // Update logo
    const logos = { cherry: '🍒', sophia: '💼', karen: '🏥' };
    const logoElement = document.querySelector('.logo span');
    if (logoElement) {
        logoElement.textContent = logos[persona];
    }
    
    // Save preference
    localStorage.setItem('preferredPersona', persona);
    
    // Reload data for new persona
    loadRealData();
}

// Tab Navigation
function switchTab(tabName) {
    AppState.currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const tabElement = document.getElementById(`${tabName}-tab`);
    if (tabElement) {
        tabElement.classList.add('active');
    }
    
    // Load tab-specific data
    loadTabData(tabName);
}

// Agent Management Functions
async function createAgent(type) {
    const agentData = {
        name: prompt('Enter agent name:'),
        type: type,
        persona: AppState.currentPersona,
        capabilities: ['content_creation', 'data_analysis'],
        config: {
            model: 'gpt-4',
            temperature: 0.7
        }
    };
    
    if (!agentData.name) return;
    
    try {
        const response = await fetch(`${AppState.apiEndpoint}/api/agents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(agentData)
        });
        
        if (response.ok) {
            const newAgent = await response.json();
            AppState.agents.push(newAgent);
            updateAgentsList();
            showNotification(`Agent "${newAgent.name}" created successfully!`, 'success');
        } else {
            throw new Error('Failed to create agent');
        }
    } catch (error) {
        showNotification(`Failed to create agent: ${error.message}`, 'error');
    }
}

async function deleteAgent(agentId) {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
        const response = await fetch(`${AppState.apiEndpoint}/api/agents/${agentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            AppState.agents = AppState.agents.filter(a => a.id !== agentId);
            updateAgentsList();
            showNotification('Agent deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete agent');
        }
    } catch (error) {
        showNotification(`Failed to delete agent: ${error.message}`, 'error');
    }
}

// Utility Functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#4ade80' : type === 'error' ? '#ef4444' : '#60a5fa'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
        z-index: 3000;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function updateDateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
}

function loadUserPreferences() {
    const savedPersona = localStorage.getItem('preferredPersona');
    if (savedPersona && ['cherry', 'sophia', 'karen'].includes(savedPersona)) {
        switchPersona(savedPersona);
    }
}

function updateSystemMetrics(metrics) {
    // Update dashboard with real metrics
    const cpuElement = document.querySelector('.metric-value[data-metric="cpu"]');
    const memoryElement = document.querySelector('.metric-value[data-metric="memory"]');
    const requestsElement = document.querySelector('.metric-value[data-metric="requests"]');
    
    if (cpuElement && metrics.cpu) cpuElement.textContent = `${metrics.cpu}%`;
    if (memoryElement && metrics.memory) memoryElement.textContent = `${metrics.memory}%`;
    if (requestsElement && metrics.requests) requestsElement.textContent = metrics.requests;
}

function loadTabData(tabName) {
    // Refresh data when switching tabs
    switch(tabName) {
        case 'agents':
            updateAgentsList();
            break;
        case 'orchestrations':
            updateOrchestrationsList();
            break;
        case 'workflows':
            updateWorkflowsList();
            break;
    }
}

// Export functions for HTML
window.switchPersona = switchPersona;
window.switchTab = switchTab;
window.setSearchMode = (type, mode) => {
    AppState.searchModes[type] = mode;
    const container = type === 'domain' ? 
        document.querySelector('.search-section:first-child') : 
        document.querySelector('.search-section:last-child');
    
    container?.querySelectorAll('.mode-chip').forEach(chip => {
        chip.classList.remove('active');
    });
    
    container?.querySelector(`[data-mode="${mode}"]`)?.classList.add('active');
};
window.handleSearchEnter = (event, type) => {
    if (event.key === 'Enter') {
        performSearch(type);
    }
};
window.performSearch = performSearch;
window.createAgent = createAgent;
window.deleteAgent = deleteAgent;
window.viewAgentDetails = (agentId) => {
    const agent = AppState.agents.find(a => a.id === agentId);
    if (agent) {
        alert(`Agent Details:\n\nName: ${agent.name}\nType: ${agent.type}\nStatus: ${agent.status}\nID: ${agent.id}`);
    }
};
window.configureAgent = (agentId) => {
    console.log('Configure agent:', agentId);
};
window.deployOrchestration = async (type) => {
    const name = prompt('Enter orchestration name:');
    if (!name) return;
    
    showNotification('Deploying orchestration...', 'info');
    // Implementation would go here
};
window.editWorkflow = (workflowId) => {
    console.log('Edit workflow:', workflowId);
};
window.createWorkflow = () => {
    const name = prompt('Enter workflow name:');
    if (!name) return;
    
    showNotification('Creating workflow...', 'info');
    // Implementation would go here
};
window.runWorkflow = async (workflowId) => {
    showNotification('Running workflow...', 'info');
    // Implementation would go here
};
window.showModal = (modalType, data) => {
    console.log('Show modal:', modalType, data);
};
window.closeModal = () => {
    document.getElementById('modal-overlay')?.classList.remove('active');
};
window.expandResult = (index) => {
    console.log('Expanding result:', index);
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .loading {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 40px;
        gap: 16px;
    }
    
    .loading-spinner {
        width: 24px;
        height: 24px;
        border: 3px solid rgba(255,255,255,0.3);
        border-top-color: var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .result-item {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .result-item:hover {
        background: rgba(255,255,255,0.08);
        transform: translateY(-2px);
    }
    
    .result-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .result-snippet {
        color: var(--text-secondary);
        margin-bottom: 12px;
        line-height: 1.5;
    }
    
    .result-meta {
        display: flex;
        gap: 20px;
        font-size: 0.9rem;
        color: var(--text-tertiary);
    }
`;
document.head.appendChild(style);

console.log('Cherry AI Orchestrator Enhanced loaded - Connected to Lambda Labs');