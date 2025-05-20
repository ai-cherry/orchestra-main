"""
Project Management API endpoints.

This module provides API endpoints for managing projects in the Orchestra admin interface.
"""

import logging
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any

from flask import Blueprint, jsonify, request

# Initialize logger
logger = logging.getLogger(__name__)

# Create Blueprint
projects_api = Blueprint("projects_api", __name__)

# In-memory projects store (would be replaced with database in production)
PROJECTS = {}

# Project status states
PROJECT_STATUSES = [
    "initiated",
    "planning",
    "execution",
    "review",
    "consolidation",
    "completed",
    "failed",
]


@projects_api.route("/api/projects", methods=["GET"])
def get_projects():
    """
    Get all projects, optionally filtered by status.

    Query Parameters:
        status (str, optional): Filter projects by status

    Returns:
        JSON list of projects
    """
    status_filter = request.args.get("status")

    if status_filter and status_filter != "all":
        filtered_projects = [
            project
            for project in PROJECTS.values()
            if project.get("status") == status_filter
        ]
        return jsonify(filtered_projects)

    return jsonify(list(PROJECTS.values()))


@projects_api.route("/api/projects/<project_id>", methods=["GET"])
def get_project(project_id):
    """
    Get a specific project by ID.

    Path Parameters:
        project_id (str): The project ID

    Returns:
        JSON project object
    """
    project = PROJECTS.get(project_id)
    if not project:
        return jsonify({"error": f"Project {project_id} not found"}), 404

    return jsonify(project)


@projects_api.route("/api/projects", methods=["POST"])
def create_project():
    """
    Create a new project.

    Request Body:
        title (str): Project title
        description (str): Project description
        status (str): Project status
        priority (str): Project priority
        active_persona (str, optional): ID of the active persona

    Returns:
        JSON project object
    """
    data = request.json

    # Validate required fields
    required_fields = ["title", "description", "status", "priority"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Validate status
    if data["status"] not in PROJECT_STATUSES:
        return (
            jsonify(
                {
                    "error": f"Invalid status: {data['status']}. Must be one of {PROJECT_STATUSES}"
                }
            ),
            400,
        )

    # Create new project
    project_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()

    project = {
        "id": project_id,
        "title": data["title"],
        "description": data["description"],
        "status": data["status"],
        "priority": data["priority"],
        "active_persona": data.get("active_persona"),
        "team_members": data.get("team_members", 1),
        "tasks": data.get("tasks", {"total": 0, "completed": 0}),
        "progress": data.get("progress", 0),
        "created_at": created_at,
        "updated_at": created_at,
    }

    PROJECTS[project_id] = project

    return jsonify(project), 201


@projects_api.route("/api/projects/<project_id>", methods=["PUT"])
def update_project(project_id):
    """
    Update an existing project.

    Path Parameters:
        project_id (str): The project ID

    Request Body:
        title (str, optional): Project title
        description (str, optional): Project description
        priority (str, optional): Project priority
        progress (int, optional): Project progress percentage
        active_persona (str, optional): ID of the active persona
        tasks (dict, optional): Project tasks info

    Returns:
        JSON project object
    """
    if project_id not in PROJECTS:
        return jsonify({"error": f"Project {project_id} not found"}), 404

    data = request.json
    project = PROJECTS[project_id]

    # Update fields if provided
    if "title" in data:
        project["title"] = data["title"]
    if "description" in data:
        project["description"] = data["description"]
    if "priority" in data:
        project["priority"] = data["priority"]
    if "progress" in data:
        project["progress"] = data["progress"]
    if "active_persona" in data:
        project["active_persona"] = data["active_persona"]
    if "tasks" in data:
        project["tasks"] = data["tasks"]

    # Update timestamp
    project["updated_at"] = datetime.now().isoformat()

    return jsonify(project)


@projects_api.route("/api/projects/<project_id>/status/<status>", methods=["PUT"])
def update_project_status(project_id, status):
    """
    Update a project's status.

    Path Parameters:
        project_id (str): The project ID
        status (str): The new status

    Returns:
        JSON project object
    """
    if project_id not in PROJECTS:
        return jsonify({"error": f"Project {project_id} not found"}), 404

    if status not in PROJECT_STATUSES:
        return (
            jsonify(
                {
                    "error": f"Invalid status: {status}. Must be one of {PROJECT_STATUSES}"
                }
            ),
            400,
        )

    project = PROJECTS[project_id]
    project["status"] = status
    project["updated_at"] = datetime.now().isoformat()

    # Auto-update progress based on status
    status_progress_map = {
        "initiated": 0,
        "planning": 15,
        "execution": 40,
        "review": 70,
        "consolidation": 90,
        "completed": 100,
        "failed": project["progress"],  # Preserve current progress if failed
    }

    if (
        status in status_progress_map
        and project["progress"] < status_progress_map[status]
    ):
        project["progress"] = status_progress_map[status]

    return jsonify(project)


@projects_api.route("/api/projects/<project_id>", methods=["DELETE"])
def delete_project(project_id):
    """
    Delete a project.

    Path Parameters:
        project_id (str): The project ID

    Returns:
        JSON success message
    """
    if project_id not in PROJECTS:
        return jsonify({"error": f"Project {project_id} not found"}), 404

    del PROJECTS[project_id]

    return jsonify({"message": f"Project {project_id} deleted successfully"}), 200


# Initialize sample data
def init_sample_projects():
    """Initialize with some sample projects"""
    if not PROJECTS:
        sample_projects = [
            {
                "id": str(uuid.uuid4()),
                "title": "AI Design Portal Revamp",
                "description": "Redesign the AI design portal with better UX flow and advanced visualization capabilities",
                "status": "execution",
                "priority": "high",
                "active_persona": "pauline",
                "team_members": 4,
                "tasks": {"total": 12, "completed": 5},
                "progress": 45,
                "created_at": (datetime.now().replace(hour=10, minute=30)).isoformat(),
                "updated_at": (datetime.now().replace(hour=14, minute=15)).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Persona Behavior Analysis Tool",
                "description": "Develop a tool for analyzing and visualizing AI persona behaviors across different scenarios",
                "status": "planning",
                "priority": "medium",
                "active_persona": "maggy",
                "team_members": 2,
                "tasks": {"total": 8, "completed": 1},
                "progress": 15,
                "created_at": (
                    datetime.now().replace(day=datetime.now().day - 2)
                ).isoformat(),
                "updated_at": (
                    datetime.now().replace(day=datetime.now().day - 1)
                ).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Orchestra Integration Framework",
                "description": "Build a framework to integrate Orchestra with external design systems and tools",
                "status": "review",
                "priority": "high",
                "active_persona": "pauline",
                "team_members": 5,
                "tasks": {"total": 18, "completed": 14},
                "progress": 75,
                "created_at": (
                    datetime.now().replace(day=datetime.now().day - 5)
                ).isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Behavioral Trait Configuration System",
                "description": "Create an advanced system for configuring and testing AI persona behavioral traits",
                "status": "completed",
                "priority": "medium",
                "active_persona": "maggy",
                "team_members": 3,
                "tasks": {"total": 10, "completed": 10},
                "progress": 100,
                "created_at": (
                    datetime.now().replace(day=datetime.now().day - 10)
                ).isoformat(),
                "updated_at": (
                    datetime.now().replace(day=datetime.now().day - 1)
                ).isoformat(),
            },
        ]

        # Add to dictionary
        for project in sample_projects:
            PROJECTS[project["id"]] = project

        logger.info(f"Initialized {len(sample_projects)} sample projects")


# Initialize sample data
init_sample_projects()
