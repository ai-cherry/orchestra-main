// Cherry AI Orchestrator - Main JavaScript Module
// Comprehensive functionality for the admin interface

// Global state management
const AppState = {
    currentPersona: 'cherry',
    currentTab: 'dashboard',
    searchModes: {
        domain: 'summary',
        web: 'creative'
    },
    apiEndpoint: 'https://cherry-ai.me/api',
    sessionId: `session_${Date.now()}`,
    activeConnections: new Map(),
    searchHistory: [],
    metrics: {
        apiCalls: 0,
        successRate: 100,
        avgResponseTime: 0
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Check API connection
    checkAPIConnection();
    setInterval(checkAPIConnection, 30000);
    
    // Update time
    updateDateTime();
    setInterval(updateDateTime, 60000);
    
    // Initialize WebSocket for real-time updates
    initializeWebSocket();
    
    // Load saved preferences
    loadUserPreferences();
    
    // Initialize charts
    initializeCharts();
}

// API Connection Management
async function checkAPIConnection() {
    const statusElement = document.querySelector('.status-dot');
    const statusText = statusElement.nextElementSibling;
    
    try {
        const response = await fetch(`${AppState.apiEndpoint}/health`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            statusElement.style.background = '#4ade80';
            statusText.textContent = 'API Connected';
            updateSystemMetrics(data);
        } else {
            throw new Error('API unhealthy');
        }
    } catch (error) {
        statusElement.style.background = '#ef4444';
        statusText.textContent = 'API Offline';
        console.error('API connection error:', error);
    }
}

// Persona Management
function switchPersona(persona) {
    AppState.currentPersona = persona;
    document.body.setAttribute('data-persona', persona);
    
    // Update UI elements
    document.querySelectorAll('.persona-card').forEach(card => {
        card.classList.remove('active');
    });
    document.querySelector(`[data-persona="${persona}"]`).classList.add('active');
    
    // Update header
    document.getElementById('active-persona').textContent = 
        persona.charAt(0).toUpperCase() + persona.slice(1);
    
    // Update logo
    const logos = { cherry: '🍒', sophia: '💼', karen: '🏥' };
    document.querySelector('.logo span').textContent = logos[persona];
    
    // Save preference
    localStorage.setItem('preferredPersona', persona);
    
    // Notify other components
    broadcastPersonaChange(persona);
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
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load tab-specific data
    loadTabData(tabName);
}

// Search Functionality
function setSearchMode(type, mode) {
    AppState.searchModes[type] = mode;
    
    // Update UI
    const container = type === 'domain' ? 
        document.querySelector('.search-section:first-child') : 
        document.querySelector('.search-section:last-child');
    
    container.querySelectorAll('.mode-chip').forEach(chip => {
        chip.classList.remove('active');
    });
    
    container.querySelector(`[data-mode="${mode}"]`).classList.add('active');
}

function handleSearchEnter(event, type) {
    if (event.key === 'Enter') {
        performSearch(type);
    }
}

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
        
        const startTime = Date.now();
        const response = await fetch(`${AppState.apiEndpoint}/search`, {
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
        
        const responseTime = Date.now() - startTime;
        updateMetrics('search', responseTime, response.ok);
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        const data = await response.json();
        displaySearchResults(data, type);
        
        // Save to history
        saveSearchHistory(query, type, mode, data.results.length);
        
    } catch (error) {
        console.error('Search error:', error);
        resultsContainer.innerHTML = `
            <div class="error">
                <strong>Search failed:</strong> ${error.message}
            </div>
        `;
    }
}

function displaySearchResults(data, type) {
    const resultsContainer = document.getElementById('search-results');
    
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="results-container">
                <div class="text-center" style="padding: 40px; color: var(--text-tertiary);">
                    No results found for "${data.query}"
                </div>
            </div>
        `;
        return;
    }
    
    let html = '<div class="results-container">';
    html += `
        <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 20px;">
            <h3 style="margin-bottom: 10px;">Search Results</h3>
            <div style="display: flex; gap: 20px; color: var(--text-secondary);">
                <span>Query: "${data.query}"</span>
                <span>Mode: ${data.mode}</span>
                <span>Results: ${data.results.length}</span>
                <span>Time: ${data.responseTime}ms</span>
            </div>
        </div>
    `;
    
    data.results.forEach((result, index) => {
        html += `
            <div class="result-item" onclick="expandResult(${index})">
                <div class="result-title">${result.title}</div>
                <div class="result-snippet">${result.snippet}</div>
                <div class="result-meta">
                    <span>Source: ${result.source}</span>
                    <span>Relevance: ${(result.relevance * 100).toFixed(1)}%</span>
                    ${result.timestamp ? `<span>${formatTimestamp(result.timestamp)}</span>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    resultsContainer.innerHTML = html;
}

// Agent Factory Functions
function createAgent(type) {
    showModal('agent-creator', {
        title: `Create ${type.charAt(0).toUpperCase() + type.slice(1)} Agent`,
        type: type
    });
}

function deployAgent(type) {
    showConfirmDialog(
        `Deploy ${type} Agent?`,
        `This will create a new instance of the ${type} agent. Continue?`,
        () => executeAgentDeployment(type)
    );
}

async function executeAgentDeployment(type) {
    try {
        const response = await fetch(`${AppState.apiEndpoint}/agents/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': AppState.sessionId
            },
            body: JSON.stringify({
                type: type,
                persona: AppState.currentPersona,
                config: getAgentConfig(type)
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification(`Agent deployed successfully! ID: ${data.agentId}`, 'success');
            refreshAgentList();
        } else {
            throw new Error('Deployment failed');
        }
    } catch (error) {
        showNotification(`Failed to deploy agent: ${error.message}`, 'error');
    }
}

function configureAgent(type) {
    showModal('agent-config', {
        title: `Configure ${type} Agent`,
        type: type,
        config: getAgentConfig(type)
    });
}

// Orchestrator Functions
function deployOrchestration(type) {
    showConfirmDialog(
        `Deploy ${type} Orchestration?`,
        `This will start the ${type} workflow orchestration. Continue?`,
        () => executeOrchestrationDeployment(type)
    );
}

async function executeOrchestrationDeployment(type) {
    try {
        const response = await fetch(`${AppState.apiEndpoint}/orchestrations/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': AppState.sessionId
            },
            body: JSON.stringify({
                type: type,
                workflow: getWorkflowDefinition(type)
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification(`Orchestration deployed! ID: ${data.orchestrationId}`, 'success');
            monitorOrchestration(data.orchestrationId);
        } else {
            throw new Error('Orchestration deployment failed');
        }
    } catch (error) {
        showNotification(`Failed to deploy orchestration: ${error.message}`, 'error');
    }
}

function editWorkflow(type) {
    showModal('workflow-editor', {
        title: `Edit ${type} Workflow`,
        type: type,
        workflow: getWorkflowDefinition(type)
    });
}

// Supervisor Functions
function configureSupervisor(type) {
    showModal('supervisor-config', {
        title: `Configure ${type} Supervisor`,
        type: type,
        config: getSupervisorConfig(type)
    });
}

function viewMetrics(type) {
    showModal('metrics-viewer', {
        title: `${type} Metrics`,
        type: type,
        metrics: getSupervisorMetrics(type)
    });
}

// Modal System
function showModal(modalType, data = {}) {
    const overlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');
    
    modalTitle.textContent = data.title || 'Modal';
    modalContent.innerHTML = getModalContent(modalType, data);
    
    overlay.classList.add('active');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
}

function getModalContent(modalType, data) {
    const modalTemplates = {
        'agent-creator': `
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div>
                    <label style="display: block; margin-bottom: 8px;">Agent Name</label>
                    <input type="text" class="search-input" placeholder="Enter agent name">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 8px;">Description</label>
                    <textarea class="search-input" rows="3" placeholder="Describe the agent's purpose"></textarea>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 8px;">Capabilities</label>
                    <div class="search-modes">
                        <div class="mode-chip">Content Creation</div>
                        <div class="mode-chip">Data Analysis</div>
                        <div class="mode-chip">Communication</div>
                        <div class="mode-chip">Research</div>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button class="action-button" onclick="closeModal()">Cancel</button>
                    <button class="search-button" style="width: auto; padding: 12px 24px;">Create Agent</button>
                </div>
            </div>
        `,
        'workflow-designer': `
            <div style="height: 500px; background: rgba(255,255,255,0.05); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary);">
                <div style="text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 20px;">🎼</div>
                    <div>Visual Workflow Designer</div>
                    <div style="margin-top: 10px; font-size: 0.9rem;">Drag and drop agents to create workflows</div>
                </div>
            </div>
        `,
        'file-upload': `
            <div style="border: 2px dashed rgba(255,255,255,0.3); border-radius: 12px; padding: 60px; text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 20px;">📁</div>
                <div style="font-size: 1.2rem; margin-bottom: 10px;">Drop files here or click to upload</div>
                <div style="color: var(--text-tertiary);">Supports PDF, DOCX, TXT, CSV</div>
                <input type="file" style="display: none;" id="file-input" multiple>
                <button class="search-button" style="margin-top: 20px; width: auto; padding: 12px 24px;" onclick="document.getElementById('file-input').click()">
                    Choose Files
                </button>
            </div>
        `,
        'music-creator': `
            <div style="display: flex; flex-direction: column; gap: 20px;">
                <div>
                    <label style="display: block; margin-bottom: 8px;">Song Title</label>
                    <input type="text" class="search-input" placeholder="Enter song title">
                </div>
                <div>
                    <label style="display: block; margin-bottom: 8px;">Lyrics</label>
                    <textarea class="search-input" rows="6" placeholder="Enter your lyrics or let AI generate them"></textarea>
                </div>
                <div>
                    <label style="display: block; margin-bottom: 8px;">Music Style</label>
                    <select class="search-input">
                        <option>Pop</option>
                        <option>Rock</option>
                        <option>Jazz</option>
                        <option>Electronic</option>
                        <option>Classical</option>
                    </select>
                </div>
                <button class="search-button">Generate Music</button>
            </div>
        `
    };
    
    return modalTemplates[modalType] || '<div>Modal content not found</div>';
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

function showConfirmDialog(title, message, onConfirm) {
    const dialog = document.createElement('div');
    dialog.className = 'modal-overlay active';
    dialog.innerHTML = `
        <div class="modal" style="max-width: 400px;">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
            </div>
            <div style="padding: 20px 0;">
                ${message}
            </div>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button class="action-button" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="search-button" style="width: auto; padding: 10px 20px;" onclick="confirmAction()">Confirm</button>
            </div>
        </div>
    `;
    
    window.confirmAction = function() {
        dialog.remove();
        onConfirm();
    };
    
    document.body.appendChild(dialog);
}

function updateDateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    // Update time display if element exists
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

function updateMetrics(type, responseTime, success) {
    AppState.metrics.apiCalls++;
    if (!success) {
        AppState.metrics.successRate = 
            ((AppState.metrics.apiCalls - 1) * AppState.metrics.successRate) / AppState.metrics.apiCalls;
    }
    AppState.metrics.avgResponseTime = 
        ((AppState.metrics.apiCalls - 1) * AppState.metrics.avgResponseTime + responseTime) / AppState.metrics.apiCalls;
}

function saveSearchHistory(query, type, mode, resultCount) {
    AppState.searchHistory.unshift({
        query,
        type,
        mode,
        resultCount,
        timestamp: new Date().toISOString(),
        persona: AppState.currentPersona
    });
    
    // Keep only last 50 searches
    if (AppState.searchHistory.length > 50) {
        AppState.searchHistory.pop();
    }
    
    // Save to localStorage
    localStorage.setItem('searchHistory', JSON.stringify(AppState.searchHistory));
}

function loadUserPreferences() {
    const savedPersona = localStorage.getItem('preferredPersona');
    if (savedPersona && ['cherry', 'sophia', 'karen'].includes(savedPersona)) {
        switchPersona(savedPersona);
    }
    
    const savedHistory = localStorage.getItem('searchHistory');
    if (savedHistory) {
        try {
            AppState.searchHistory = JSON.parse(savedHistory);
        } catch (e) {
            console.error('Failed to load search history:', e);
        }
    }
}

// WebSocket for real-time updates
function initializeWebSocket() {
    try {
        const ws = new WebSocket('wss://cherry-ai.me/ws');
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            ws.send(JSON.stringify({
                type: 'auth',
                sessionId: AppState.sessionId
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleRealtimeUpdate(data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected, reconnecting in 5s...');
            setTimeout(initializeWebSocket, 5000);
        };
        
        AppState.ws = ws;
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
    }
}

function handleRealtimeUpdate(data) {
    switch (data.type) {
        case 'metrics':
            updateSystemMetrics(data.metrics);
            break;
        case 'agent-status':
            updateAgentStatus(data.agentId, data.status);
            break;
        case 'orchestration-progress':
            updateOrchestrationProgress(data.orchestrationId, data.progress);
            break;
        case 'notification':
            showNotification(data.message, data.level);
            break;
    }
}

// Chart initialization (placeholder for actual chart library integration)
function initializeCharts() {
    // This would integrate with Chart.js or similar library
    console.log('Charts initialized');
}

// Helper functions for getting configurations
function getAgentConfig(type) {
    const configs = {
        cherry: {
            personality: 'curious, health-conscious, creative',
            capabilities: ['health advice', 'entertainment', 'creative writing'],
            model: 'gpt-4',
            temperature: 0.8
        },
        sophia: {
            personality: 'professional, analytical, goal-oriented',
            capabilities: ['business analysis', 'financial planning', 'market research'],
            model: 'gpt-4',
            temperature: 0.6
        },
        karen: {
            personality: 'caring, detail-oriented, safety-focused',
            capabilities: ['medical data analysis', 'health monitoring', 'compliance'],
            model: 'gpt-4',
            temperature: 0.4
        }
    };
    return configs[type] || {};
}

function getWorkflowDefinition(type) {
    const workflows = {
        content: {
            name: 'Content Creation Orchestra',
            steps: [
                { id: 1, agent: 'researcher', action: 'gather_information' },
                { id: 2, agent: 'writer', action: 'create_draft' },
                { id: 3, agent: 'editor', action: 'review_and_edit' },
                { id: 4, agent: 'seo_optimizer', action: 'optimize_content' },
                { id: 5, agent: 'publisher', action: 'publish_content' }
            ]
        },
        business: {
            name: 'Business Intelligence Team',
            steps: [
                { id: 1, agent: 'data_collector', action: 'gather_market_data' },
                { id: 2, agent: 'analyst', action: 'analyze_trends' },
                { id: 3, agent: 'strategist', action: 'develop_recommendations' },
                { id: 4, agent: 'reporter', action: 'create_report' }
            ]
        }
    };
    return workflows[type] || {};
}

function getSupervisorConfig(type) {
    return {
        type: type,
        rules: [],
        thresholds: {},
        alerts: []
    };
}

function getSupervisorMetrics(type) {
    return {
        performance: Math.random() * 100,
        accuracy: Math.random() * 100,
        throughput: Math.floor(Math.random() * 1000)
    };
}

// Export for use in HTML
window.switchPersona = switchPersona;
window.switchTab = switchTab;
window.setSearchMode = setSearchMode;
window.handleSearchEnter = handleSearchEnter;
window.performSearch = performSearch;
window.createAgent = createAgent;
window.deployAgent = deployAgent;
window.configureAgent = configureAgent;
window.deployOrchestration = deployOrchestration;
window.editWorkflow = editWorkflow;
window.configureSupervisor = configureSupervisor;
window.viewMetrics = viewMetrics;
window.showModal = showModal;
window.closeModal = closeModal;
window.expandResult = function(index) {
    console.log('Expanding result:', index);
};
window.broadcastPersonaChange = function(persona) {
    console.log('Broadcasting persona change:', persona);
};
window.loadTabData = function(tabName) {
    console.log('Loading data for tab:', tabName);
};
window.refreshAgentList = function() {
    console.log('Refreshing agent list');
};
window.monitorOrchestration = function(id) {
    console.log('Monitoring orchestration:', id);
};
window.updateSystemMetrics = function(metrics) {
    console.log('Updating system metrics:', metrics);
};
window.updateAgentStatus = function(agentId, status) {
    console.log('Updating agent status:', agentId, status);
};
window.updateOrchestrationProgress = function(orchestrationId, progress) {
    console.log('Updating orchestration progress:', orchestrationId, progress);
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
`;
document.head.appendChild(style);