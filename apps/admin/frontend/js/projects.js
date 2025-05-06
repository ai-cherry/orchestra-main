/**
 * Orchestra Admin Dashboard - Projects Management
 * Handles project management functionality for the admin interface
 */

// Initialize the projects functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('[x-show="activeTab === \'projects\'"]')) {
        initializeProjectsTab();
    }
});

/**
 * Initialize the Projects tab functionality
 */
function initializeProjectsTab() {
    // Load projects data when the tab becomes active
    document.querySelectorAll('a[href="#"]').forEach(link => {
        if (link.textContent.trim() === 'Projects') {
            link.addEventListener('click', () => {
                setTimeout(() => loadProjects(), 100);
            });
        }
    });
}

/**
 * Load projects data and render the projects interface
 */
function loadProjects() {
    const projectsContainer = document.querySelector('[x-show="activeTab === \'projects\'"]');
    if (!projectsContainer || projectsContainer.dataset.initialized) return;
    
    // Mark as initialized to prevent duplicate loading
    projectsContainer.dataset.initialized = 'true';
    
    // Replace placeholder with actual projects interface
    projectsContainer.innerHTML = `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h2 class="text-2xl font-bold">Project Management</h2>
                <div class="flex space-x-2">
                    <div class="relative">
                        <input type="text" placeholder="Search projects..." class="bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white w-64">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 absolute right-3 top-2.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </div>
                    <button class="bg-primary-700 hover:bg-primary-600 text-white px-4 py-2 rounded-lg flex items-center" id="createProjectBtn">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                        </svg>
                        New Project
                    </button>
                </div>
            </div>

            <!-- Project filters -->
            <div class="flex items-center space-x-4 overflow-x-auto pb-2">
                <button class="filter-btn bg-primary-700 text-white px-4 py-1.5 rounded-full text-sm" data-filter="all">All Projects</button>
                <button class="filter-btn bg-gray-700 hover:bg-gray-600 text-white px-4 py-1.5 rounded-full text-sm" data-filter="active">Active</button>
                <button class="filter-btn bg-gray-700 hover:bg-gray-600 text-white px-4 py-1.5 rounded-full text-sm" data-filter="planning">Planning</button>
                <button class="filter-btn bg-gray-700 hover:bg-gray-600 text-white px-4 py-1.5 rounded-full text-sm" data-filter="execution">Execution</button>
                <button class="filter-btn bg-gray-700 hover:bg-gray-600 text-white px-4 py-1.5 rounded-full text-sm" data-filter="review">Review</button>
                <button class="filter-btn bg-gray-700 hover:bg-gray-600 text-white px-4 py-1.5 rounded-full text-sm" data-filter="completed">Completed</button>
            </div>

            <!-- Projects Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="projectsGrid">
                <!-- Loading indicator -->
                <div class="col-span-full text-center py-12">
                    <svg class="animate-spin h-10 w-10 text-primary-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="text-gray-400">Loading projects...</p>
                </div>
            </div>
        </div>
    `;
    
    // Add event listener for create project button
    document.getElementById('createProjectBtn').addEventListener('click', showProjectCreator);
    
    // Add event listeners for filter buttons
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            // Update active filter styling
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('bg-primary-700');
                btn.classList.add('bg-gray-700', 'hover:bg-gray-600');
            });
            e.currentTarget.classList.remove('bg-gray-700', 'hover:bg-gray-600');
            e.currentTarget.classList.add('bg-primary-700');
            
            // Apply filter
            const filter = e.currentTarget.dataset.filter;
            fetchFilteredProjects(filter);
        });
    });
    
    // Fetch and display projects
    fetchProjects().then(renderProjects);
}

/**
 * Fetch projects from the API
 * @returns {Promise} Promise that resolves to an array of projects
 */
function fetchProjects() {
    return fetch('/api/projects')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch projects');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error fetching projects:', error);
            showNotification('Error loading projects', 'error');
            return [];
        });
}

/**
 * Fetch filtered projects from the API
 * @param {string} filter The filter to apply (status)
 */
function fetchFilteredProjects(filter) {
    const projectsGrid = document.getElementById('projectsGrid');
    
    // Show loading indicator
    projectsGrid.innerHTML = `
        <div class="col-span-full text-center py-12">
            <svg class="animate-spin h-10 w-10 text-primary-500 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-400">Loading projects...</p>
        </div>
    `;
    
    // If filter is "all", fetch all projects
    if (filter === 'all') {
        fetchProjects().then(renderProjects);
        return;
    }
    
    // Fetch filtered projects
    fetch(`/api/projects?status=${filter}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch filtered projects');
            }
            return response.json();
        })
        .then(projects => {
            renderProjects(projects);
        })
        .catch(error => {
            console.error('Error fetching filtered projects:', error);
            showNotification('Error loading projects', 'error');
            projectsGrid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <p class="text-red-400">Error loading projects. Please try again.</p>
                </div>
            `;
        });
}

/**
 * Show a notification message to the user
 * @param {string} message The message to show
 * @param {string} type The type of notification: 'success', 'error', 'info'
 */
function showNotification(message, type = 'info') {
    // Create the notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-5 py-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-600' : 
        type === 'error' ? 'bg-red-600' : 
        'bg-blue-600'
    } text-white flex items-center`;
    
    notification.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            ${type === 'success' 
                ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />'
                : type === 'error'
                    ? '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
                    : '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />'
            }
        </svg>
        <span>${message}</span>
    `;
    
    // Add notification to the document
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.classList.add('opacity-0', 'transition-opacity', 'duration-300');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Render projects in the grid
 * @param {Array} projects Array of project objects
 */
function renderProjects(projects) {
    const projectsGrid = document.getElementById('projectsGrid');
    
    // Clear loading indicator
    projectsGrid.innerHTML = '';
    
    if (!projects || projects.length === 0) {
        projectsGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p class="text-gray-400">No projects found</p>
                <button class="mt-4 bg-primary-700 hover:bg-primary-600 text-white px-4 py-2 rounded-lg" id="emptyStateCreateBtn">
                    Create your first project
                </button>
            </div>
        `;
        
        document.getElementById('emptyStateCreateBtn').addEventListener('click', showProjectCreator);
        return;
    }
    
    // Render each project
    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'bg-gray-700 rounded-lg shadow-lg overflow-hidden card-hover';
        card.setAttribute('data-project-id', project.id);
        
        // Status color map
        const statusColors = {
            'active': 'bg-blue-500',
            'initiated': 'bg-blue-500',
            'planning': 'bg-purple-500',
            'execution': 'bg-amber-500',
            'review': 'bg-teal-500',
            'consolidation': 'bg-indigo-500',
            'completed': 'bg-green-500',
            'failed': 'bg-red-500'
        };
        
        // Priority badge colors
        const priorityColors = {
            'high': 'badge-primary',
            'medium': 'badge-info',
            'low': 'badge-success'
        };
        
        // Format date
        const createdAt = new Date(project.created_at);
        const formattedDate = `${createdAt.toLocaleDateString()} at ${createdAt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
        
        card.innerHTML = `
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-lg font-semibold">${project.title}</h3>
                    <span class="badge ${priorityColors[project.priority] || 'badge-info'}">${project.priority}</span>
                </div>
                <p class="text-gray-400 mb-4 text-sm h-12 overflow-hidden">${project.description}</p>
                
                <div class="mb-4">
                    <div class="flex justify-between text-sm mb-1">
                        <span>Progress</span>
                        <span>${project.progress}%</span>
                    </div>
                    <div class="w-full bg-gray-600 rounded-full h-2">
                        <div class="${statusColors[project.status] || 'bg-blue-500'} h-2 rounded-full" style="width: ${project.progress}%"></div>
                    </div>
                </div>
                
                <div class="flex justify-between items-center text-sm text-gray-400">
                    <div>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        ${formattedDate}
                    </div>
                    <div>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        ${project.team_members}
                    </div>
                    <div>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                        </svg>
                        ${project.tasks ? `${project.tasks.completed || 0}/${project.tasks.total || 0}` : '0/0'}
                    </div>
                </div>
            </div>
            
            <div class="border-t border-gray-600 px-6 py-3 flex justify-between items-center bg-gray-800 bg-opacity-50">
                <div class="flex items-center">
                    <span class="inline-block w-2 h-2 rounded-full ${statusColors[project.status] || 'bg-blue-500'} mr-2"></span>
                    <span class="capitalize">${project.status}</span>
                </div>
                <div>
                    <span class="text-sm text-gray-400">Assigned to:</span>
                    <span class="text-sm font-medium ml-1 capitalize">${project.active_persona || 'Unassigned'}</span>
                </div>
            </div>
        `;
        
        // Add click event to open project details
        card.addEventListener('click', () => showProjectDetails(project));
        
        projectsGrid.appendChild(card);
    });
}

/**
 * Show project creator modal
 */
function showProjectCreator() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    modal.id = 'projectCreatorModal';
    
    modal.innerHTML = `
        <div class="bg-gray-800 rounded-lg shadow-lg w-full max-w-3xl overflow-hidden">
            <div class="flex justify-between items-center p-6 border-b border-gray-700">
                <h3 class="text-xl font-semibold">Create New Project</h3>
                <button class="text-gray-400 hover:text-white" id="closeProjectCreator">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <form id="createProjectForm">
                <div class="p-6">
                    <div class="grid grid-cols-1 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Project Title</label>
                            <input type="text" name="title" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" placeholder="Enter project title">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Description</label>
                            <textarea name="description" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white h-32" placeholder="Enter project description"></textarea>
                        </div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Priority</label>
                                <select name="priority" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white">
                                    <option value="high">High</option>
                                    <option value="medium" selected>Medium</option>
                                    <option value="low">Low</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Assign Persona</label>
                                <select name="active_persona" class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white">
                                    <option value="">Select Persona</option>
                                </select>
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Initial Project Phase</label>
                            <div class="flex flex-wrap gap-2">
                                <label class="flex items-center bg-gray-700 px-3 py-2 rounded-md cursor-pointer">
                                    <input type="radio" name="status" value="planning" class="mr-2" checked>
                                    <span>Planning</span>
                                </label>
                                <label class="flex items-center bg-gray-700 px-3 py-2 rounded-md cursor-pointer">
                                    <input type="radio" name="status" value="execution" class="mr-2">
                                    <span>Execution</span>
                                </label>
                                <label class="flex items-center bg-gray-700 px-3 py-2 rounded-md cursor-pointer">
                                    <input type="radio" name="status" value="review" class="mr-2">
                                    <span>Review</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="p-6 border-t border-gray-700 flex justify-end space-x-3">
                    <button type="button" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg" id="cancelProjectCreator">
                        Cancel
                    </button>
                    <button type="submit" class="px-4 py-2 bg-primary-700 hover:bg-primary-600 text-white rounded-lg">
                        Create Project
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('closeProjectCreator').addEventListener('click', closeProjectCreator);
    document.getElementById('cancelProjectCreator').addEventListener('click', closeProjectCreator);
    
    // Load personas for dropdown
    loadPersonasForDropdown();
    
    // Handle form submission
    document.getElementById('createProjectForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitNewProject(this);
    });
}

/**
 * Load personas for the dropdown in project creator
 */
function loadPersonasForDropdown() {
    const dropdown = document.querySelector('select[name="active_persona"]');
    
    // Fetch personas from API
    fetch('/api/personas')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch personas');
            }
            return response.json();
        })
        .then(personas => {
            personas.forEach(persona => {
                const option = document.createElement('option');
                option.value = persona.id;
                option.textContent = `${persona.name} (${persona.description})`;
                dropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading personas:', error);
        });
}

/**
 * Submit a new project to the API
 * @param {HTMLFormElement} form The form element
 */
function submitNewProject(form) {
    // Get form data
    const formData = new FormData(form);
    const projectData = {
        title: formData.get('title'),
        description: formData.get('description'),
        status: formData.get('status'),
        priority: formData.get('priority'),
        active_persona: formData.get('active_persona'),
        team_members: 1,
        tasks: {
            total: 0,
            completed: 0
        },
        progress: 0
    };
    
    // Submit to API
    fetch('/api/projects', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to create project');
        }
        return response.json();
    })
    .then(data => {
        closeProjectCreator();
        showNotification('Project created successfully', 'success');
        
        // Refresh projects list
        fetchProjects().then(renderProjects);
    })
    .catch(error => {
        console.error('Error creating project:', error);
        showNotification('Error creating project', 'error');
    });
}

/**
 * Close project creator modal
 */
function closeProjectCreator() {
    const modal = document.getElementById('projectCreatorModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Show project details modal
 * @param {Object} project Project object
 */
function showProjectDetails(project) {
    // Fetch the latest project data first
    fetch(`/api/projects/${project.id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch project details');
            }
            return response.json();
        })
        .then(latestProject => {
            displayProjectDetailsModal(latestProject);
        })
        .catch(error => {
            console.error('Error fetching project details:', error);
            // Fall back to existing data if API request fails
            displayProjectDetailsModal(project);
        });
}

/**
 * Display the project details modal with the provided project data
 * @param {Object} project Project object
 */
function displayProjectDetailsModal(project) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    modal.id = 'projectDetailsModal';
    
    // Status color map
    const statusColors = {
        'active': 'bg-blue-500',
        'initiated': 'bg-blue-500',
        'planning': 'bg-purple-500',
        'execution': 'bg-amber-500',
        'review': 'bg-teal-500',
        'consolidation': 'bg-indigo-500',
        'completed': 'bg-green-500',
        'failed': 'bg-red-500'
    };
    
    // Format date
    const createdAt = new Date(project.created_at);
    const formattedDate = `${createdAt.toLocaleDateString()} at ${createdAt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    
    modal.innerHTML = `
        <div class="bg-gray-800 rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center p-6 border-b border-gray-700">
                <h3 class="text-xl font-semibold">${project.title}</h3>
                <button class="text-gray-400 hover:text-white" id="closeProjectDetails">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <div class="p-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div class="md:col-span-2">
                        <h4 class="text-lg font-semibold mb-2">Project Description</h4>
                        <p class="text-gray-300">${project.description}</p>
                        
                        <div class="mt-6">
                            <h4 class="text-lg font-semibold mb-2">Progress</h4>
                            <div class="flex justify-between text-sm mb-1">
                                <span>Overall Completion</span>
                                <span>${project.progress}%</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-3 mb-4">
                                <div class="${statusColors[project.status] || 'bg-blue-500'} h-3 rounded-full" style="width: ${project.progress}%"></div>
                            </div>
                            
                            <div class="flex justify-between text-sm mb-1">
                                <span>Tasks Completed</span>
                                <span>${project.tasks ? `${project.tasks.completed || 0}/${project.tasks.total || 0}` : '0/0'}</span>
                            </div>
                            <div class="w-full bg-gray-700 rounded-full h-3">
                                <div class="bg-green-500 h-3 rounded-full" style="width: ${project.tasks && project.tasks.total ? (project.tasks.completed / project.tasks.total) * 100 : 0}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="text-lg font-semibold mb-3">Project Details</h4>
                        <div class="bg-gray-700 rounded-lg p-4 space-y-3">
                            <div>
                                <span class="text-sm text-gray-400">Status:</span>
                                <div class="flex items-center mt-1">
                                    <span class="inline-block w-3 h-3 rounded-full ${statusColors[project.status] || 'bg-blue-500'} mr-2"></span>
                                    <span class="font-medium capitalize">${project.status}</span>
                                </div>
                            </div>
                            
                            <div>
                                <span class="text-sm text-gray-400">Priority:</span>
                                <div class="mt-1">
                                    <span class="badge badge-${project.priority === 'high' ? 'primary' : (project.priority === 'medium' ? 'info' : 'success')}">${project.priority}</span>
                                </div>
                            </div>
                            
                            <div>
                                <span class="text-sm text-gray-400">Created:</span>
                                <div class="mt-1 font-medium">${formattedDate}</div>
                            </div>
                            
                            <div>
                                <span class="text-sm text-gray-400">Managed By:</span>
                                <div class="mt-1 font-medium capitalize">${project.active_persona || 'Unassigned'}</div>
                            </div>
                            
                            <div>
                                <span class="text-sm text-gray-400">Team Size:</span>
                                <div class="mt-1 font-medium">${project.team_members} members</div>
                            </div>
                        </div>
                        
                        <div class="mt-4 space-x-2">
                            <button class="bg-primary-700 hover:bg-primary-600 text-white px-4 py-2 rounded" id="editProjectBtn">
                                Edit Project
                            </button>
                            <button class="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded" id="viewTasksBtn">
                                View Tasks
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Project Status Updater -->
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-3">Update Project Status</h4>
                    <div class="flex flex-wrap gap-2">
                        <button class="status-btn ${project.status === 'planning' ? 'bg-purple-700' : 'bg-gray-700 hover:bg-gray-600'} text-white px-4 py-2 rounded-md" data-status="planning">
                            Planning
                        </button>
                        <button class="status-btn ${project.status === 'execution' ? 'bg-amber-700' : 'bg-gray-700 hover:bg-gray-600'} text-white px-4 py-2 rounded-md" data-status="execution">
                            Execution
                        </button>
                        <button class="status-btn ${project.status === 'review' ? 'bg-teal-700' : 'bg-gray-700 hover:bg-gray-600'} text-white px-4 py-2 rounded-md" data-status="review">
                            Review
                        </button>
                        <button class="status-btn ${project.status === 'consolidation' ? 'bg-indigo-700' : 'bg-gray-700 hover:bg-gray-600'} text-white px-4 py-2 rounded-md" data-status="consolidation">
                            Consolidation
                        </button>
                        <button class="status-btn ${project.status === 'completed' ? 'bg-green-700' : 'bg-gray-700 hover:bg-gray-600'} text-white px-4 py-2 rounded-md" data-status="completed">
                            Completed
                        </button>
                    </div>
                </div>
                
                <!-- Activity Timeline -->
                <div>
                    <h4 class="text-lg font-semibold mb-3">Project Timeline</h4>
                    <div class="space-y-4">
                        <div class="flex">
                            <div class="flex flex-col items-center mr-4">
                                <div class="bg-primary-600 rounded-full p-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <div class="h-full w-0.5 bg-gray-600"></div>
                            </div>
                            <div class="pb-4">
                                <span class="text-sm text-gray-400">Today at 4:30 PM</span>
                                <p class="font-medium">Project status updated to ${project.status}</p>
                            </div>
                        </div>
                        
                        <div class="flex">
                            <div class="flex flex-col items-center mr-4">
                                <div class="bg-green-600 rounded-full p-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                    </svg>
                                </div>
                                <div class="h-full w-0.5 bg-gray-600"></div>
                            </div>
                            <div class="pb-4">
                                <span class="text-sm text-gray-400">Yesterday at 2:15 PM</span>
                                <p class="font-medium">New task added: "Update design mockups with feedback"</p>
                            </div>
                        </div>
                        
                        <div class="flex">
                            <div class="flex flex-col items-center mr-4">
                                <div class="bg-blue-600 rounded-full p-1">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                </div>
                            </div>
                            <div>
                                <span class="text-sm text-gray-400">${formattedDate}</span>
                                <p class="font-medium">Project created</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener to close button
    document.getElementById('closeProjectDetails').addEventListener('click', closeProjectDetails);
    
    // Add event listeners to status buttons
    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const newStatus = e.currentTarget.dataset.status;
            updateProjectStatus(project.id, newStatus);
        });
    });
    
    // Add event listener to edit project button
    document.getElementById('editProjectBtn').addEventListener('click', () => {
        showEditProjectModal(project);
    });
}

/**
 * Update a project's status
 * @param {string} projectId The project ID
 * @param {string} newStatus The new status
 */
function updateProjectStatus(projectId, newStatus) {
    fetch(`/api/projects/${projectId}/status/${newStatus}`, {
        method: 'PUT'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update project status');
        }
        return response.json();
    })
    .then(data => {
        showNotification('Project status updated', 'success');
        
        // Close the current details modal
        closeProjectDetails();
        
        // Fetch the updated project and reopen the details modal
        fetch(`/api/projects/${projectId}`)
            .then(response => response.json())
            .then(updatedProject => {
                displayProjectDetailsModal(updatedProject);
            });
        
        // Refresh projects list
        fetchProjects().then(renderProjects);
    })
    .catch(error => {
        console.error('Error updating project status:', error);
        showNotification('Error updating project status', 'error');
    });
}

/**
 * Show edit project modal
 * @param {Object} project Project object
 */
function showEditProjectModal(project) {
    // Close details modal first
    closeProjectDetails();
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    modal.id = 'editProjectModal';
    
    modal.innerHTML = `
        <div class="bg-gray-800 rounded-lg shadow-lg w-full max-w-3xl overflow-hidden">
            <div class="flex justify-between items-center p-6 border-b border-gray-700">
                <h3 class="text-xl font-semibold">Edit Project: ${project.title}</h3>
                <button class="text-gray-400 hover:text-white" id="closeEditProject">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <form id="editProjectForm">
                <div class="p-6">
                    <div class="grid grid-cols-1 gap-6">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Project Title</label>
                            <input type="text" name="title" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" value="${project.title}">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Description</label>
                            <textarea name="description" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white h-32">${project.description}</textarea>
                        </div>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Priority</label>
                                <select name="priority" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white">
                                    <option value="high" ${project.priority === 'high' ? 'selected' : ''}>High</option>
                                    <option value="medium" ${project.priority === 'medium' ? 'selected' : ''}>Medium</option>
                                    <option value="low" ${project.priority === 'low' ? 'selected' : ''}>Low</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-300 mb-1">Progress (%)</label>
                                <input type="number" name="progress" min="0" max="100" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" value="${project.progress}">
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Assign Persona</label>
                            <select name="active_persona" class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white">
                                <option value="">Select Persona</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-1">Tasks</label>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm text-gray-400 mb-1">Total Tasks</label>
                                    <input type="number" name="tasks_total" min="0" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" value="${project.tasks ? project.tasks.total : 0}">
                                </div>
                                <div>
                                    <label class="block text-sm text-gray-400 mb-1">Completed Tasks</label>
                                    <input type="number" name="tasks_completed" min="0" required class="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white" value="${project.tasks ? project.tasks.completed : 0}">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="p-6 border-t border-gray-700 flex justify-end space-x-3">
                    <button type="button" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg" id="cancelEditProject">
                        Cancel
                    </button>
                    <button type="submit" class="px-4 py-2 bg-primary-700 hover:bg-primary-600 text-white rounded-lg">
                        Save Changes
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    document.getElementById('closeEditProject').addEventListener('click', closeEditProjectModal);
    document.getElementById('cancelEditProject').addEventListener('click', closeEditProjectModal);
    
    // Load personas for dropdown
    loadPersonasForEditDropdown(project.active_persona);
    
    // Handle form submission
    document.getElementById('editProjectForm').addEventListener('submit', function(e) {
        e.preventDefault();
        submitProjectEdits(project.id, this);
    });
}

/**
 * Load personas for the dropdown in project editor
 * @param {string} selectedPersonaId The currently selected persona ID
 */
function loadPersonasForEditDropdown(selectedPersonaId) {
    const dropdown = document.querySelector('#editProjectForm select[name="active_persona"]');
    
    // Fetch personas from API
    fetch('/api/personas')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch personas');
            }
            return response.json();
        })
        .then(personas => {
            personas.forEach(persona => {
                const option = document.createElement('option');
                option.value = persona.id;
                option.textContent = `${persona.name} (${persona.description})`;
                
                if (persona.id === selectedPersonaId) {
                    option.selected = true;
                }
                
                dropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading personas:', error);
        });
}

/**
 * Submit project edits to the API
 * @param {string} projectId The project ID
 * @param {HTMLFormElement} form The form element
 */
function submitProjectEdits(projectId, form) {
    // Get form data
    const formData = new FormData(form);
    
    const projectData = {
        title: formData.get('title'),
        description: formData.get('description'),
        priority: formData.get('priority'),
        progress: parseInt(formData.get('progress')),
        active_persona: formData.get('active_persona'),
        tasks: {
            total: parseInt(formData.get('tasks_total')),
            completed: parseInt(formData.get('tasks_completed'))
        }
    };
    
    // Submit to API
    fetch(`/api/projects/${projectId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(projectData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to update project');
        }
        return response.json();
    })
    .then(data => {
        closeEditProjectModal();
        showNotification('Project updated successfully', 'success');
        
        // Refresh projects list
        fetchProjects().then(renderProjects);
        
        // Show updated project details
        fetch(`/api/projects/${projectId}`)
            .then(response => response.json())
            .then(updatedProject => {
                showProjectDetails(updatedProject);
            });
    })
    .catch(error => {
        console.error('Error updating project:', error);
        showNotification('Error updating project', 'error');
    });
}

/**
 * Close edit project modal
 */
function closeEditProjectModal() {
    const modal = document.getElementById('editProjectModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Close project details modal
 */
function closeProjectDetails() {
    const modal = document.getElementById('projectDetailsModal');
    if (modal) {
        modal.remove();
    }
}

// Export functions for global access
window.projectManager = {
    loadProjects,
    showProjectCreator,
    showProjectDetails,
    fetchFilteredProjects
};