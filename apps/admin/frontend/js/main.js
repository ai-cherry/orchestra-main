/**
 * Orchestra Admin Dashboard - Main JavaScript
 * Handles advanced functionality for the admin interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the app on content load
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('Orchestra Admin Dashboard initialized');
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize any components that need JavaScript setup
    initializeComponents();
}

/**
 * Set up event listeners for interactive components
 */
function setupEventListeners() {
    // Add event listener for the "Create New Persona" button
    const createPersonaBtn = document.querySelector('[x-show="activeTab === \'personas\'"] button');
    if (createPersonaBtn) {
        createPersonaBtn.addEventListener('click', () => {
            showPersonaEditor();
        });
    }
    
    // Add event listeners for the "Edit" buttons on persona cards
    const editButtons = document.querySelectorAll('[x-show="activeTab === \'personas\'"] button:first-child');
    editButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            // Get the persona name from the card
            const personaCard = e.target.closest('.bg-gray-700');
            const personaName = personaCard.querySelector('h3').textContent;
            
            // Open the persona editor with the selected persona
            showPersonaEditor(personaName);
        });
    });
}

/**
 * Initialize UI components that require JavaScript
 */
function initializeComponents() {
    // Nothing to initialize yet, Alpine.js handles most of the UI reactivity
}

/**
 * Shows the persona editor modal for creating or editing a persona
 * @param {string} personaName - The name of the persona to edit (optional)
 */
function showPersonaEditor(personaName = null) {
    // Create and show the modal
    const isNewPersona = !personaName;
    const modalTitle = isNewPersona ? 'Create New Persona' : `Edit Persona: ${personaName}`;
    
    // Sample traits data - this would come from the backend in a real implementation
    const traits = isNewPersona ? {
        'detail_orientation': 5,
        'timeline_adherence': 5,
        'resource_optimization': 5,
        'risk_assessment': 5
    } : (personaName === 'Pauline' ? {
        'detail_orientation': 8.5,
        'timeline_adherence': 9.0,
        'resource_optimization': 7.5,
        'risk_assessment': 8.0
    } : {
        'information_classification': 9.2,
        'retrieval_accuracy': 8.8,
        'context_sensitivity': 8.5,
        'pattern_recognition': 9.5
    });
    
    // Create modal HTML
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    modal.id = 'personaEditorModal';
    
    // Modal content
    modal.innerHTML = `
        <div class="bg-gray-800 rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center p-6 border-b border-gray-700">
                <h3 class="text-xl font-semibold">${modalTitle}</h3>
                <button class="text-gray-400 hover:text-white" id="closePersonaEditor">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <div class="p-6">
                <!-- Basic Information -->
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">Basic Information</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Persona Name</label>
                            <input type="text" class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" 
                                value="${isNewPersona ? '' : personaName}">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Role/Function</label>
                            <input type="text" class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" 
                                value="${isNewPersona ? '' : (personaName === 'Pauline' ? 'Project Management Expert' : 'Memory Management & Retrieval')}">
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-300 mb-1">Description</label>
                            <textarea class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white h-20"></textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Behavioral Traits -->
                <div class="mb-6">
                    <div class="flex justify-between items-center mb-3">
                        <h4 class="text-lg font-semibold">Behavioral Traits</h4>
                        <button class="text-sm text-primary-500 hover:text-primary-400">Add Trait</button>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-4 mb-4">
                        <div class="grid grid-cols-2 gap-6">
                            <div>
                                <!-- Trait sliders -->
                                <div class="space-y-4">
                                    ${Object.entries(traits).map(([trait, value]) => `
                                        <div>
                                            <div class="flex justify-between mb-1">
                                                <label class="text-sm font-medium text-gray-300">${trait.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}</label>
                                                <span class="text-sm text-gray-400">${value}</span>
                                            </div>
                                            <input type="range" min="1" max="10" step="0.1" value="${value}" 
                                                class="trait-slider" data-trait="${trait}">
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                            
                            <div>
                                <!-- Radar chart container -->
                                <div class="radar-chart-container">
                                    <canvas id="traitRadarChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Advanced Configuration Tabs -->
                <div class="mb-6">
                    <div class="border-b border-gray-700">
                        <nav class="flex -mb-px">
                            <button class="py-2 px-4 text-center border-b-2 border-primary-500 font-medium text-white">
                                Communication
                            </button>
                            <button class="py-2 px-4 text-center border-b-2 border-transparent font-medium text-gray-400 hover:text-gray-300">
                                Decision Making
                            </button>
                            <button class="py-2 px-4 text-center border-b-2 border-transparent font-medium text-gray-400 hover:text-gray-300">
                                Cognitive Style
                            </button>
                            <button class="py-2 px-4 text-center border-b-2 border-transparent font-medium text-gray-400 hover:text-gray-300">
                                Learning
                            </button>
                        </nav>
                    </div>
                    
                    <div class="py-4">
                        <!-- Communication Style Panel (active by default) -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Formality Level</label>
                                <div class="flex items-center">
                                    <span class="text-xs text-gray-400 mr-2">Casual</span>
                                    <input type="range" min="1" max="10" value="6" class="trait-slider flex-1">
                                    <span class="text-xs text-gray-400 ml-2">Formal</span>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Response Detail</label>
                                <div class="flex items-center">
                                    <span class="text-xs text-gray-400 mr-2">Concise</span>
                                    <input type="range" min="1" max="10" value="7" class="trait-slider flex-1">
                                    <span class="text-xs text-gray-400 ml-2">Elaborate</span>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Empathy Display</label>
                                <div class="flex items-center">
                                    <span class="text-xs text-gray-400 mr-2">Clinical</span>
                                    <input type="range" min="1" max="10" value="5" class="trait-slider flex-1">
                                    <span class="text-xs text-gray-400 ml-2">Empathetic</span>
                                </div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Initiative Level</label>
                                <div class="flex items-center">
                                    <span class="text-xs text-gray-400 mr-2">Reactive</span>
                                    <input type="range" min="1" max="10" value="8" class="trait-slider flex-1">
                                    <span class="text-xs text-gray-400 ml-2">Proactive</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Relationship Configuration -->
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">Team & Relationship Configuration</h4>
                    <div class="bg-gray-700 rounded-lg p-4">
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-300 mb-1">Default Team Role</label>
                            <select class="w-full bg-gray-600 border border-gray-700 rounded-md py-2 px-3 text-white">
                                <option value="leader">Team Leader</option>
                                <option value="specialist">Domain Specialist</option>
                                <option value="coordinator">Team Coordinator</option>
                                <option value="support">Support Member</option>
                            </select>
                        </div>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-gray-300 mb-2">Knowledge Sharing Permissions</label>
                            <div class="space-y-2">
                                <div class="flex items-center">
                                    <input type="checkbox" id="share_all" class="mr-2 bg-gray-600 border-gray-700 rounded text-primary-600">
                                    <label for="share_all" class="text-sm text-gray-300">Share all knowledge with team members</label>
                                </div>
                                <div class="flex items-center">
                                    <input type="checkbox" id="share_selective" class="mr-2 bg-gray-600 border-gray-700 rounded text-primary-600" checked>
                                    <label for="share_selective" class="text-sm text-gray-300">Share only domain-specific knowledge</label>
                                </div>
                                <div class="flex items-center">
                                    <input type="checkbox" id="request_approval" class="mr-2 bg-gray-600 border-gray-700 rounded text-primary-600">
                                    <label for="request_approval" class="text-sm text-gray-300">Request approval before sharing sensitive information</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="p-6 border-t border-gray-700 flex justify-end space-x-3">
                <button class="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg" id="cancelPersonaEditor">
                    Cancel
                </button>
                <button class="px-4 py-2 bg-primary-700 hover:bg-primary-600 text-white rounded-lg">
                    ${isNewPersona ? 'Create Persona' : 'Save Changes'}
                </button>
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('closePersonaEditor').addEventListener('click', closePersonaEditor);
    document.getElementById('cancelPersonaEditor').addEventListener('click', closePersonaEditor);
    
    // Initialize the radar chart
    initTraitRadarChart(traits);
    
    // Set up trait slider events
    const traitSliders = document.querySelectorAll('.trait-slider[data-trait]');
    traitSliders.forEach(slider => {
        slider.addEventListener('input', (e) => {
            const trait = e.target.getAttribute('data-trait');
            const value = parseFloat(e.target.value);
            
            // Update the displayed value
            const valueDisplay = e.target.parentElement.querySelector('span');
            if (valueDisplay) valueDisplay.textContent = value;
            
            // Update traits object and chart
            traits[trait] = value;
            updateTraitRadarChart(traits);
        });
    });
}

/**
 * Close the persona editor modal
 */
function closePersonaEditor() {
    const modal = document.getElementById('personaEditorModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Initialize the radar chart for persona traits visualization
 * @param {Object} traits - Object containing trait names and values
 */
function initTraitRadarChart(traits) {
    const ctx = document.getElementById('traitRadarChart');
    if (!ctx) return;
    
    const labels = Object.keys(traits).map(trait => 
        trait.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    );
    const data = Object.values(traits);
    
    window.traitChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Trait Strength',
                data: data,
                backgroundColor: 'rgba(220, 38, 38, 0.2)', // primary-600 with opacity
                borderColor: '#dc2626', // primary-600
                pointBackgroundColor: '#ef4444', // primary-500
                pointBorderColor: '#ffffff',
                pointHoverBackgroundColor: '#ffffff',
                pointHoverBorderColor: '#b91c1c', // primary-700
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        color: '#f3f4f6', // gray-100
                        font: {
                            size: 12
                        }
                    },
                    ticks: {
                        color: '#9ca3af', // gray-400
                        backdropColor: 'transparent',
                        z: 100,
                        max: 10,
                        min: 0
                    },
                    suggestedMin: 0,
                    suggestedMax: 10
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            },
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

/**
 * Update the radar chart with new trait values
 * @param {Object} traits - Object containing trait names and values
 */
function updateTraitRadarChart(traits) {
    if (!window.traitChart) return;
    
    window.traitChart.data.datasets[0].data = Object.values(traits);
    window.traitChart.update();
}

/**
 * API mock functions for development - these would be replaced with actual API calls
 */
const apiMock = {
    /**
     * Get all personas from the system
     * @returns {Promise} A promise that resolves to an array of personas
     */
    getPersonas: () => {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve([
                    {
                        id: 'pauline',
                        name: 'Pauline',
                        description: 'Project Management Expert',
                        traits: {
                            detail_orientation: 8.5,
                            timeline_adherence: 9.0,
                            resource_optimization: 7.5,
                            risk_assessment: 8.0
                        }
                    },
                    {
                        id: 'maggy',
                        name: 'Maggy',
                        description: 'Memory Management & Retrieval',
                        traits: {
                            information_classification: 9.2,
                            retrieval_accuracy: 8.8,
                            context_sensitivity: 8.5,
                            pattern_recognition: 9.5
                        }
                    }
                ]);
            }, 300);
        });
    },
    
    /**
     * Save a persona to the system
     * @param {Object} persona - The persona object to save
     * @returns {Promise} A promise that resolves when the persona is saved
     */
    savePersona: (persona) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                console.log('Persona saved:', persona);
                resolve({ success: true, id: persona.id || 'new-persona-id' });
            }, 500);
        });
    }
};