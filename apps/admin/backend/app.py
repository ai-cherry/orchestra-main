"""
Orchestra Admin Backend API

This module provides the API endpoints for the Orchestra Admin Dashboard.
It serves persona data, configuration options, and handles updates.
"""

import json
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

# Import project management module
from api.projects import (
    get_all_projects, get_project_by_id, create_project, update_project, 
    delete_project, filter_projects, update_project_status, assign_persona_to_project
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Import agent teams API router
from api.agent_teams import router as agent_teams_router

# Register agent teams API routes
app.register_blueprint(agent_teams_router, url_prefix='/api')

# Directory for data storage
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Path to persona data file
PERSONA_FILE = os.path.join(DATA_DIR, 'personas.json')

# Initialize with default personas if file doesn't exist
def init_personas():
    if not os.path.exists(PERSONA_FILE):
        default_personas = [
            {
                "id": "pauline",
                "name": "Pauline",
                "description": "Project Management Expert",
                "traits": {
                    "detail_orientation": 8.5,
                    "timeline_adherence": 9.0,
                    "resource_optimization": 7.5,
                    "risk_assessment": 8.0
                },
                "communication_style": {
                    "formality_level": 7,
                    "response_detail": 8,
                    "empathy_display": 6,
                    "initiative_level": 9
                },
                "team_role": "leader",
                "knowledge_sharing": ["domain_specific"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "id": "maggy",
                "name": "Maggy",
                "description": "Memory Management & Retrieval",
                "traits": {
                    "information_classification": 9.2,
                    "retrieval_accuracy": 8.8,
                    "context_sensitivity": 8.5,
                    "pattern_recognition": 9.5
                },
                "communication_style": {
                    "formality_level": 5,
                    "response_detail": 9,
                    "empathy_display": 4,
                    "initiative_level": 7
                },
                "team_role": "specialist",
                "knowledge_sharing": ["domain_specific", "approval_required"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        with open(PERSONA_FILE, 'w') as f:
            json.dump(default_personas, f, indent=2)
        logger.info(f"Created default personas file at {PERSONA_FILE}")
    else:
        logger.info(f"Using existing personas file at {PERSONA_FILE}")

# Helper functions for persona management
def get_all_personas():
    try:
        with open(PERSONA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading personas: {e}")
        return []

def save_personas(personas):
    try:
        with open(PERSONA_FILE, 'w') as f:
            json.dump(personas, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving personas: {e}")
        return False

def get_persona_by_id(persona_id):
    personas = get_all_personas()
    for persona in personas:
        if persona["id"] == persona_id:
            return persona
    return None

def update_persona(persona_data):
    personas = get_all_personas()
    found = False
    
    for i, persona in enumerate(personas):
        if persona["id"] == persona_data["id"]:
            # Update existing persona
            persona_data["updated_at"] = datetime.utcnow().isoformat()
            personas[i] = persona_data
            found = True
            break
    
    if not found:
        # Add new persona
        if "id" not in persona_data or not persona_data["id"]:
            persona_data["id"] = persona_data["name"].lower().replace(" ", "_")
        
        persona_data["created_at"] = datetime.utcnow().isoformat()
        persona_data["updated_at"] = datetime.utcnow().isoformat()
        personas.append(persona_data)
    
    return save_personas(personas)

def delete_persona(persona_id):
    personas = get_all_personas()
    updated_personas = [p for p in personas if p["id"] != persona_id]
    
    if len(updated_personas) < len(personas):
        return save_personas(updated_personas)
    return False

# API Routes - Personas
@app.route('/api/personas', methods=['GET'])
def api_get_personas():
    """Get all personas"""
    personas = get_all_personas()
    return jsonify(personas)

@app.route('/api/personas/<persona_id>', methods=['GET'])
def api_get_persona(persona_id):
    """Get a specific persona by ID"""
    persona = get_persona_by_id(persona_id)
    if persona:
        return jsonify(persona)
    return jsonify({"error": "Persona not found"}), 404

@app.route('/api/personas', methods=['POST'])
def api_create_persona():
    """Create a new persona"""
    if not request.json:
        return jsonify({"error": "Invalid request data"}), 400
    
    persona_data = request.json
    success = update_persona(persona_data)
    
    if success:
        return jsonify({"success": True, "id": persona_data["id"]})
    return jsonify({"error": "Failed to create persona"}), 500

@app.route('/api/personas/<persona_id>', methods=['PUT'])
def api_update_persona(persona_id):
    """Update an existing persona"""
    if not request.json:
        return jsonify({"error": "Invalid request data"}), 400
    
    persona_data = request.json
    persona_data["id"] = persona_id
    
    success = update_persona(persona_data)
    
    if success:
        return jsonify({"success": True, "id": persona_id})
    return jsonify({"error": "Failed to update persona"}), 500

@app.route('/api/personas/<persona_id>', methods=['DELETE'])
def api_delete_persona(persona_id):
    """Delete a persona"""
    success = delete_persona(persona_id)
    
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete persona"}), 500

# API Routes - Projects
@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get all projects with optional filtering"""
    status = request.args.get('status')
    persona_id = request.args.get('persona_id')
    priority = request.args.get('priority')
    
    if any([status, persona_id, priority]):
        projects = filter_projects(status, persona_id, priority)
    else:
        projects = get_all_projects()
    
    return jsonify(projects)

@app.route('/api/projects/<project_id>', methods=['GET'])
def api_get_project(project_id):
    """Get a specific project by ID"""
    project = get_project_by_id(project_id)
    if project:
        return jsonify(project)
    return jsonify({"error": "Project not found"}), 404

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create a new project"""
    if not request.json:
        return jsonify({"error": "Invalid request data"}), 400
    
    project_data = request.json
    project_id = create_project(project_data)
    
    if project_id:
        return jsonify({"success": True, "id": project_id})
    return jsonify({"error": "Failed to create project"}), 500

@app.route('/api/projects/<project_id>', methods=['PUT'])
def api_update_project(project_id):
    """Update an existing project"""
    if not request.json:
        return jsonify({"error": "Invalid request data"}), 400
    
    project_data = request.json
    success = update_project(project_id, project_data)
    
    if success:
        return jsonify({"success": True, "id": project_id})
    return jsonify({"error": "Failed to update project"}), 500

@app.route('/api/projects/<project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    """Delete a project"""
    success = delete_project(project_id)
    
    if success:
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete project"}), 500

@app.route('/api/projects/<project_id>/status/<status>', methods=['PUT'])
def api_update_project_status(project_id, status):
    """Update a project's status"""
    success = update_project_status(project_id, status)
    
    if success:
        return jsonify({"success": True, "id": project_id, "status": status})
    return jsonify({"error": "Failed to update project status"}), 500

@app.route('/api/projects/<project_id>/assign/<persona_id>', methods=['PUT'])
def api_assign_persona_to_project(project_id, persona_id):
    """Assign a persona to a project"""
    success = assign_persona_to_project(project_id, persona_id)
    
    if success:
        return jsonify({"success": True, "project_id": project_id, "persona_id": persona_id})
    return jsonify({"error": "Failed to assign persona to project"}), 500

# Serve static files from the frontend directory
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the frontend directory"""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    return send_from_directory(frontend_dir, path)

# Initialize app with data
init_personas()

if __name__ == '__main__':
    logger.info("Starting Orchestra Admin Backend API")
    app.run(host='0.0.0.0', port=5000, debug=True)