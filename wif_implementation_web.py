#!/usr/bin/env python3
"""
WIF Implementation Web Interface

This script provides a web interface for the Workload Identity Federation (WIF)
implementation plan for the AI Orchestra project.
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

import uvicorn
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wif_implementation import (
    ImplementationPhase,
    TaskStatus,
    Task,
    ImplementationPlan,
    Vulnerability,
    VulnerabilityManager,
    MigrationManager,
    CICDManager,
    TrainingManager,
)
from wif_implementation.db_schema import DatabaseManager
from wif_implementation.template_manager import template_manager
from wif_implementation.csrf_loader import csrf_protection, csrf_protect
from wif_implementation.error_handler import (
    WIFError,
    ErrorSeverity,
    handle_exception,
    safe_execute,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("wif_implementation_web")

# Create FastAPI app
app = FastAPI(
    title="WIF Implementation Plan",
    description="Web interface for the Workload Identity Federation (WIF) implementation plan",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database manager
db_manager = DatabaseManager(db_path="wif_implementation.db")

# Create implementation plan
plan = db_manager.get_implementation_plan()
if not plan:
    from wif_implementation_cli import create_implementation_plan

    plan = create_implementation_plan(Path("."))
    db_manager.save_implementation_plan(plan)


# Models
class TaskModel(BaseModel):
    """Task model for the API."""

    name: str
    description: str
    phase: str
    status: str
    dependencies: List[str] = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: str = ""


class VulnerabilityModel(BaseModel):
    """Vulnerability model for the API."""

    id: str
    package: str
    severity: str
    description: str
    current_version: str
    fixed_version: Optional[str] = None
    is_direct: bool = True
    is_fixed: bool = False
    fix_command: Optional[str] = None
    notes: str = ""


class MessageModel(BaseModel):
    """Message model for the API."""

    type: str
    text: str


# Routes
@app.get("/", response_class=HTMLResponse)
@handle_exception
async def index(request: Request):
    """Render the index page."""
    # Get tasks from the database
    tasks = db_manager.get_tasks()

    # Get vulnerabilities from the database
    vulnerabilities = db_manager.get_vulnerabilities()

    # If no vulnerabilities, scan for real ones
    if not vulnerabilities:
        manager = VulnerabilityManager(verbose=True, dry_run=False)
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Try to scan for real vulnerabilities
        manager._inventory_vulnerabilities(plan)

        # Save found vulnerabilities to the database
        for vuln in manager.vulnerabilities:
            db_manager.save_vulnerability(vuln)
        vulnerabilities = db_manager.get_vulnerabilities()

    # Generate a CSRF token
    csrf_token = csrf_protection.generate_token()

    # Render the template
    return template_manager.render_template(
        "index.html",
        {
            "request": request,
            "tasks": tasks,
            "vulnerabilities": vulnerabilities,
            "csrf_token": csrf_token,
            "csrf_token_url": "/csrf-token",
            "messages": [],
        },
    )


@app.post("/csrf-token")
@handle_exception
async def csrf_token():
    """Generate a new CSRF token."""
    # Generate a new CSRF token
    csrf_token = csrf_protection.generate_token()

    # Return the token
    return {"csrf_token": csrf_token}


@app.get("/execute-phase/{phase_name}")
@handle_exception
async def execute_phase(
    phase_name: str, request: Request, _: None = Depends(csrf_protect)
):
    """Execute a phase of the implementation plan."""
    try:
        # Get the phase
        phase = ImplementationPhase(phase_name)

        # Get the implementation plan
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Create the appropriate manager
        if phase == ImplementationPhase.VULNERABILITIES:
            manager = VulnerabilityManager(verbose=True, dry_run=True)
        elif phase == ImplementationPhase.MIGRATION:
            manager = MigrationManager(verbose=True, dry_run=True)
        elif phase == ImplementationPhase.CICD:
            manager = CICDManager(verbose=True, dry_run=True)
        elif phase == ImplementationPhase.TRAINING:
            manager = TrainingManager(verbose=True, dry_run=True)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown phase: {phase_name}")

        # Get tasks for this phase
        tasks = plan.get_tasks_by_phase(phase)
        if not tasks:
            raise HTTPException(
                status_code=404, detail=f"No tasks found for phase {phase_name}"
            )

        # Execute tasks in order
        for task in tasks:
            # Check dependencies
            for dependency in task.dependencies:
                dependency_task = plan.get_task_by_name(dependency)
                if dependency_task and dependency_task.status != TaskStatus.COMPLETED:
                    continue

            # Start the task
            task.start()

            # Execute the task
            success = manager.execute_task(task.name, plan)

            # Update task status
            if success:
                task.complete()
            else:
                task.fail(f"Task {task.name} failed")

            # Save the task
            db_manager.save_task(task)

        # Save the implementation plan
        db_manager.save_implementation_plan(plan)

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the phase section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#{phase_name}",
            status_code=303,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing phase {phase_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/execute-task/{task_name}")
@handle_exception
async def execute_task(
    task_name: str, request: Request, _: None = Depends(csrf_protect)
):
    """Execute a task in the implementation plan."""
    try:
        # Get the implementation plan
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Get the task
        task = plan.get_task_by_name(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_name} not found")

        # Check dependencies
        for dependency in task.dependencies:
            dependency_task = plan.get_task_by_name(dependency)
            if dependency_task and dependency_task.status != TaskStatus.COMPLETED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Dependency {dependency} not completed",
                )

        # Start the task
        task.start()

        # Save the task
        db_manager.save_task(task)

        # Create the appropriate manager
        if task.phase == ImplementationPhase.VULNERABILITIES:
            manager = VulnerabilityManager(verbose=True, dry_run=True)
        elif task.phase == ImplementationPhase.MIGRATION:
            manager = MigrationManager(verbose=True, dry_run=True)
        elif task.phase == ImplementationPhase.CICD:
            manager = CICDManager(verbose=True, dry_run=True)
        elif task.phase == ImplementationPhase.TRAINING:
            manager = TrainingManager(verbose=True, dry_run=True)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown phase: {task.phase}")

        # Execute the task
        success = manager.execute_task(task.name, plan)

        # Update task status
        if success:
            task.complete()
        else:
            task.fail(f"Task {task.name} failed")

        # Save the task
        db_manager.save_task(task)

        # Save the implementation plan
        db_manager.save_implementation_plan(plan)

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the phase section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#{task.phase.value}",
            status_code=303,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing task {task_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/complete-task/{task_name}")
@handle_exception
async def complete_task(
    task_name: str, request: Request, _: None = Depends(csrf_protect)
):
    """Mark a task as completed."""
    try:
        # Get the implementation plan
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Get the task
        task = plan.get_task_by_name(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_name} not found")

        # Complete the task
        task.complete()

        # Save the task
        db_manager.save_task(task)

        # Save the implementation plan
        db_manager.save_implementation_plan(plan)

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the phase section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#{task.phase.value}",
            status_code=303,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error completing task {task_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fail-task/{task_name}")
@handle_exception
async def fail_task(task_name: str, request: Request, _: None = Depends(csrf_protect)):
    """Mark a task as failed."""
    try:
        # Get the implementation plan
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Get the task
        task = plan.get_task_by_name(task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_name} not found")

        # Fail the task
        task.fail("Task failed manually")

        # Save the task
        db_manager.save_task(task)

        # Save the implementation plan
        db_manager.save_implementation_plan(plan)

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the phase section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#{task.phase.value}",
            status_code=303,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error failing task {task_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scan-vulnerabilities")
@handle_exception
async def scan_vulnerabilities(request: Request, _: None = Depends(csrf_protect)):
    """Scan for vulnerabilities."""
    try:
        # Create a vulnerability manager
        manager = VulnerabilityManager(verbose=True, dry_run=False)

        # Get the implementation plan
        plan = db_manager.get_implementation_plan()
        if not plan:
            from wif_implementation_cli import create_implementation_plan

            plan = create_implementation_plan(Path("."))

        # Clear existing vulnerabilities
        db_manager.clear_vulnerabilities()

        # Scan for real vulnerabilities
        manager._inventory_vulnerabilities(plan)

        # Save vulnerabilities to the database
        for vuln in manager.vulnerabilities:
            db_manager.save_vulnerability(vuln)

        # Log the number of vulnerabilities found
        logger.info(f"Found {len(manager.vulnerabilities)} vulnerabilities")

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the vulnerabilities section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#vulnerabilities",
            status_code=303,
        )

    except Exception as e:
        logger.error(f"Error scanning for vulnerabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fix-vulnerability/{vulnerability_id}")
@handle_exception
async def fix_vulnerability(
    vulnerability_id: str, request: Request, _: None = Depends(csrf_protect)
):
    """Fix a vulnerability."""
    try:
        # Get the vulnerability
        vulnerability = db_manager.get_vulnerability(vulnerability_id)
        if not vulnerability:
            raise HTTPException(
                status_code=404, detail=f"Vulnerability {vulnerability_id} not found"
            )

        # Fix the vulnerability
        vulnerability.is_fixed = True
        vulnerability.fix_command = (
            f"npm update {vulnerability.package}"
            if vulnerability.package
            in ["lodash", "axios", "react", "express", "minimist"]
            else f"pip install {vulnerability.package}=={vulnerability.fixed_version}"
        )

        # Save the vulnerability
        db_manager.save_vulnerability(vulnerability)

        # Generate a new CSRF token
        csrf_token = csrf_protection.generate_token()

        # Redirect to the vulnerabilities section
        return RedirectResponse(
            url=f"/?csrf_token={csrf_token}#vulnerabilities",
            status_code=303,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error fixing vulnerability {vulnerability_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# API routes
@app.get("/api/tasks", response_model=List[TaskModel])
@handle_exception
async def api_get_tasks():
    """Get all tasks."""
    tasks = db_manager.get_tasks()
    return [
        TaskModel(
            name=task.name,
            description=task.description,
            phase=task.phase.value,
            status=task.status.value,
            dependencies=task.dependencies,
            start_time=task.start_time,
            end_time=task.end_time,
            notes=task.notes,
        )
        for task in tasks
    ]


@app.get("/api/tasks/{task_name}", response_model=TaskModel)
@handle_exception
async def api_get_task(task_name: str):
    """Get a task by name."""
    task = db_manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_name} not found")

    return TaskModel(
        name=task.name,
        description=task.description,
        phase=task.phase.value,
        status=task.status.value,
        dependencies=task.dependencies,
        start_time=task.start_time,
        end_time=task.end_time,
        notes=task.notes,
    )


@app.get("/api/vulnerabilities", response_model=List[VulnerabilityModel])
@handle_exception
async def api_get_vulnerabilities():
    """Get all vulnerabilities."""
    vulnerabilities = db_manager.get_vulnerabilities()
    return [
        VulnerabilityModel(
            id=vuln.id,
            package=vuln.package,
            severity=vuln.severity,
            description=vuln.description,
            current_version=vuln.current_version,
            fixed_version=vuln.fixed_version,
            is_direct=vuln.is_direct,
            is_fixed=vuln.is_fixed,
            fix_command=vuln.fix_command,
            notes=vuln.notes,
        )
        for vuln in vulnerabilities
    ]


@app.get("/api/vulnerabilities/{vulnerability_id}", response_model=VulnerabilityModel)
@handle_exception
async def api_get_vulnerability(vulnerability_id: str):
    """Get a vulnerability by ID."""
    vulnerability = db_manager.get_vulnerability(vulnerability_id)
    if not vulnerability:
        raise HTTPException(
            status_code=404, detail=f"Vulnerability {vulnerability_id} not found"
        )

    return VulnerabilityModel(
        id=vulnerability.id,
        package=vulnerability.package,
        severity=vulnerability.severity,
        description=vulnerability.description,
        current_version=vulnerability.current_version,
        fixed_version=vulnerability.fixed_version,
        is_direct=vulnerability.is_direct,
        is_fixed=vulnerability.is_fixed,
        fix_command=vulnerability.fix_command,
        notes=vulnerability.notes,
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    # Generate a new CSRF token
    csrf_token = csrf_protection.generate_token()

    # If the request accepts JSON, return a JSON response
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # Otherwise, redirect to the index page with an error message
    return RedirectResponse(
        url=f"/?csrf_token={csrf_token}&error={exc.detail}",
        status_code=303,
    )


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    # Log the exception
    logger.error(f"Unhandled exception: {str(exc)}")

    # Generate a new CSRF token
    csrf_token = csrf_protection.generate_token()

    # If the request accepts JSON, return a JSON response
    if "application/json" in request.headers.get("accept", ""):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Otherwise, redirect to the index page with an error message
    return RedirectResponse(
        url=f"/?csrf_token={csrf_token}&error=Internal+server+error",
        status_code=303,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Start the WIF implementation web interface."
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()

    # Start the server
    uvicorn.run(
        "wif_implementation_web:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
