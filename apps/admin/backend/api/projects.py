"""
Orchestra Admin - Projects API

This module provides API endpoints for managing projects within the Orchestra Admin dashboard.
It handles CRUD operations for projects and provides linkage between projects and personas.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Directory for data storage
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
os.makedirs(DATA_DIR, exist_ok=True)

# Path to projects data file
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

# Project status enum values
PROJECT_STATUS_VALUES = [
    "initiated",
    "planning",
    "execution",
    "review",
    "consolidation",
    "completed",
    "failed",
]


# Initialize with default projects if file doesn't exist
def init_projects():
    """Initialize the projects data file with default data if it doesn't exist."""
    if not os.path.exists(PROJECTS_FILE):
        default_projects = [
            {
                "id": "proj-001",
                "title": "Website Redesign",
                "description": "Redesign the company website with modern UX principles",
                "status": "execution",
                "progress": 65,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "active_persona": "pauline",
                "team_members": 5,
                "tasks": {"total": 32, "completed": 21},
                "priority": "high",
            },
            {
                "id": "proj-002",
                "title": "Mobile App Design",
                "description": "Design UI/UX for new mobile application",
                "status": "planning",
                "progress": 25,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "active_persona": "maggy",
                "team_members": 3,
                "tasks": {"total": 18, "completed": 5},
                "priority": "medium",
            },
        ]

        with open(PROJECTS_FILE, "w") as f:
            json.dump(default_projects, f, indent=2)
        logger.info(f"Created default projects file at {PROJECTS_FILE}")
    else:
        logger.info(f"Using existing projects file at {PROJECTS_FILE}")


# Helper functions for project management
def get_all_projects() -> List[Dict[str, Any]]:
    """Get all projects from the data file."""
    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading projects: {e}")
        return []


def save_projects(projects: List[Dict[str, Any]]) -> bool:
    """Save projects to the data file."""
    try:
        with open(PROJECTS_FILE, "w") as f:
            json.dump(projects, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving projects: {e}")
        return False


def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """Get a project by ID."""
    projects = get_all_projects()
    for project in projects:
        if project["id"] == project_id:
            return project
    return None


def create_project(project_data: Dict[str, Any]) -> Optional[str]:
    """Create a new project."""
    projects = get_all_projects()

    # Generate ID if not provided
    if "id" not in project_data or not project_data["id"]:
        # Simple ID generation - in production, use a more robust method
        existing_ids = [p["id"] for p in projects]
        counter = 1
        while True:
            new_id = f"proj-{counter:03d}"
            if new_id not in existing_ids:
                project_data["id"] = new_id
                break
            counter += 1

    # Add timestamps
    now = datetime.utcnow().isoformat()
    project_data["created_at"] = now
    project_data["updated_at"] = now

    # Default values if not provided
    project_data.setdefault("progress", 0)
    project_data.setdefault("tasks", {"total": 0, "completed": 0})
    project_data.setdefault("team_members", 1)

    # Validate status
    if "status" in project_data and project_data["status"] not in PROJECT_STATUS_VALUES:
        project_data["status"] = "initiated"

    # Add to projects
    projects.append(project_data)

    if save_projects(projects):
        return project_data["id"]
    return None


def update_project(project_id: str, project_data: Dict[str, Any]) -> bool:
    """Update an existing project."""
    projects = get_all_projects()

    for i, project in enumerate(projects):
        if project["id"] == project_id:
            # Keep original data that shouldn't change
            project_data["id"] = project_id
            project_data["created_at"] = project.get("created_at")
            project_data["updated_at"] = datetime.utcnow().isoformat()

            # Validate status
            if (
                "status" in project_data
                and project_data["status"] not in PROJECT_STATUS_VALUES
            ):
                project_data["status"] = project.get("status", "initiated")

            # Update the project
            projects[i] = project_data
            return save_projects(projects)

    return False


def delete_project(project_id: str) -> bool:
    """Delete a project."""
    projects = get_all_projects()
    updated_projects = [p for p in projects if p["id"] != project_id]

    if len(updated_projects) < len(projects):
        return save_projects(updated_projects)
    return False


def filter_projects(
    status: Optional[str] = None,
    persona_id: Optional[str] = None,
    priority: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter projects by various criteria."""
    projects = get_all_projects()
    filtered_projects = projects

    # Apply filters
    if status:
        filtered_projects = [p for p in filtered_projects if p.get("status") == status]

    if persona_id:
        filtered_projects = [
            p for p in filtered_projects if p.get("active_persona") == persona_id
        ]

    if priority:
        filtered_projects = [
            p for p in filtered_projects if p.get("priority") == priority
        ]

    return filtered_projects


def update_project_status(project_id: str, status: str) -> bool:
    """Update a project's status."""
    if status not in PROJECT_STATUS_VALUES:
        return False

    project = get_project_by_id(project_id)
    if not project:
        return False

    project["status"] = status
    project["updated_at"] = datetime.utcnow().isoformat()

    # If completed, set progress to 100%
    if status == "completed":
        project["progress"] = 100

    return update_project(project_id, project)


def assign_persona_to_project(project_id: str, persona_id: str) -> bool:
    """Assign a persona to a project."""
    project = get_project_by_id(project_id)
    if not project:
        return False

    project["active_persona"] = persona_id
    project["updated_at"] = datetime.utcnow().isoformat()

    return update_project(project_id, project)


# Initialize projects data
init_projects()
