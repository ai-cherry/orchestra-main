"""
Database schema for the WIF implementation plan.

This module defines the database schema for storing vulnerability information
and implementation plan progress.
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    Any,
    Iterator,
    TypeVar,
    Generic,
)

from .models import (
    ImplementationPhase,
    TaskStatus,
    Task,
    ImplementationPlan,
    Vulnerability,
)

# Configure logging
logger = logging.getLogger("wif_implementation.db_schema")

# Type variable for the context manager
T = TypeVar("T")


class DatabaseError(Exception):
    """Base exception for database errors."""

    pass


class ConnectionError(DatabaseError):
    """Exception raised when a database connection cannot be established."""

    pass


class QueryError(DatabaseError):
    """Exception raised when a database query fails."""

    pass


@contextmanager
def db_connection(db_path: Union[str, Path]) -> Iterator[sqlite3.Connection]:
    """
    Context manager for database connections.

    Args:
        db_path: The path to the database file

    Yields:
        A database connection

    Raises:
        ConnectionError: If the connection cannot be established
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Return dictionary-like rows
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        raise ConnectionError(f"Failed to connect to database: {str(e)}") from e
    finally:
        if conn:
            conn.close()


class DatabaseManager:
    """
    Manager for the WIF implementation database.

    This class provides functionality to manage the database for storing
    vulnerability information and implementation plan progress.
    """

    def __init__(
        self,
        db_path: Union[str, Path] = "wif_implementation.db",
        verbose: bool = False,
    ):
        """
        Initialize the database manager.

        Args:
            db_path: The path to the database file
            verbose: Whether to show detailed output during processing
        """
        self.db_path = Path(db_path).resolve()
        self.verbose = verbose

        if verbose:
            logger.setLevel(logging.DEBUG)

        logger.debug(f"Initialized database manager with path: {self.db_path}")

        # Initialize the database
        self._init_db()

    def _init_db(self) -> None:
        """
        Initialize the database schema.

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the schema creation fails
        """
        logger.debug("Initializing database schema")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Create vulnerabilities table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vulnerabilities (
                        id TEXT PRIMARY KEY,
                        package TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT NOT NULL,
                        current_version TEXT NOT NULL,
                        fixed_version TEXT,
                        is_direct INTEGER NOT NULL,
                        is_fixed INTEGER NOT NULL,
                        fix_command TEXT,
                        notes TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )

                # Create tasks table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        name TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        phase TEXT NOT NULL,
                        status TEXT NOT NULL,
                        start_time TEXT,
                        end_time TEXT,
                        notes TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )

                # Create task dependencies table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS task_dependencies (
                        task_name TEXT NOT NULL,
                        dependency_name TEXT NOT NULL,
                        PRIMARY KEY (task_name, dependency_name),
                        FOREIGN KEY (task_name) REFERENCES tasks (name) ON DELETE CASCADE,
                        FOREIGN KEY (dependency_name) REFERENCES tasks (name) ON DELETE CASCADE
                    )
                """
                )

                # Create implementation plan table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS implementation_plan (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        start_time TEXT,
                        end_time TEXT,
                        current_phase TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """
                )

                # Commit the changes
                conn.commit()

                logger.debug("Database schema initialized successfully")

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error initializing database schema: {str(e)}")
            raise QueryError(f"Failed to initialize database schema: {str(e)}") from e

    def save_vulnerability(self, vulnerability: Vulnerability) -> None:
        """
        Save a vulnerability to the database.

        Args:
            vulnerability: The vulnerability to save

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the save operation fails
        """
        logger.debug(f"Saving vulnerability: {vulnerability.id}")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if the vulnerability already exists
                cursor.execute(
                    "SELECT id FROM vulnerabilities WHERE id = ?", (vulnerability.id,)
                )
                exists = cursor.fetchone() is not None

                now = datetime.now().isoformat()

                if exists:
                    # Update the vulnerability
                    cursor.execute(
                        """
                        UPDATE vulnerabilities
                        SET package = ?, severity = ?, description = ?, current_version = ?,
                            fixed_version = ?, is_direct = ?, is_fixed = ?, fix_command = ?,
                            notes = ?, updated_at = ?
                        WHERE id = ?
                    """,
                        (
                            vulnerability.package,
                            vulnerability.severity,
                            vulnerability.description,
                            vulnerability.current_version,
                            vulnerability.fixed_version,
                            1 if vulnerability.is_direct else 0,
                            1 if vulnerability.is_fixed else 0,
                            vulnerability.fix_command,
                            vulnerability.notes,
                            now,
                            vulnerability.id,
                        ),
                    )
                else:
                    # Insert the vulnerability
                    cursor.execute(
                        """
                        INSERT INTO vulnerabilities (
                            id, package, severity, description, current_version,
                            fixed_version, is_direct, is_fixed, fix_command,
                            notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            vulnerability.id,
                            vulnerability.package,
                            vulnerability.severity,
                            vulnerability.description,
                            vulnerability.current_version,
                            vulnerability.fixed_version,
                            1 if vulnerability.is_direct else 0,
                            1 if vulnerability.is_fixed else 0,
                            vulnerability.fix_command,
                            vulnerability.notes,
                            now,
                            now,
                        ),
                    )

                # Commit the changes
                conn.commit()

                logger.debug(f"Vulnerability {vulnerability.id} saved successfully")

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error saving vulnerability: {str(e)}")
            raise QueryError(f"Failed to save vulnerability: {str(e)}") from e

    def get_vulnerability(self, vulnerability_id: str) -> Optional[Vulnerability]:
        """
        Get a vulnerability from the database.

        Args:
            vulnerability_id: The ID of the vulnerability to get

        Returns:
            The vulnerability, or None if not found

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the query fails
        """
        logger.debug(f"Getting vulnerability: {vulnerability_id}")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get the vulnerability
                cursor.execute(
                    "SELECT * FROM vulnerabilities WHERE id = ?", (vulnerability_id,)
                )
                row = cursor.fetchone()

                if not row:
                    logger.debug(f"Vulnerability {vulnerability_id} not found")
                    return None

                # Create a Vulnerability object
                vulnerability = Vulnerability(
                    id=row["id"],
                    package=row["package"],
                    severity=row["severity"],
                    description=row["description"],
                    current_version=row["current_version"],
                    fixed_version=row["fixed_version"],
                    is_direct=bool(row["is_direct"]),
                    is_fixed=bool(row["is_fixed"]),
                    fix_command=row["fix_command"],
                    notes=row["notes"],
                )

                logger.debug(f"Vulnerability {vulnerability_id} retrieved successfully")
                return vulnerability

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error getting vulnerability: {str(e)}")
            raise QueryError(f"Failed to get vulnerability: {str(e)}") from e

    def get_vulnerabilities(self) -> List[Vulnerability]:
        """
        Get all vulnerabilities from the database.

        Returns:
            A list of all vulnerabilities

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the query fails
        """
        logger.debug("Getting all vulnerabilities")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get all vulnerabilities
                cursor.execute("SELECT * FROM vulnerabilities")
                rows = cursor.fetchall()

                # Create Vulnerability objects
                vulnerabilities = []
                for row in rows:
                    vulnerability = Vulnerability(
                        id=row["id"],
                        package=row["package"],
                        severity=row["severity"],
                        description=row["description"],
                        current_version=row["current_version"],
                        fixed_version=row["fixed_version"],
                        is_direct=bool(row["is_direct"]),
                        is_fixed=bool(row["is_fixed"]),
                        fix_command=row["fix_command"],
                        notes=row["notes"],
                    )
                    vulnerabilities.append(vulnerability)

                logger.debug(f"Retrieved {len(vulnerabilities)} vulnerabilities")
                return vulnerabilities

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error getting vulnerabilities: {str(e)}")
            raise QueryError(f"Failed to get vulnerabilities: {str(e)}") from e

    def clear_vulnerabilities(self) -> None:
        """
        Clear all vulnerabilities from the database.

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the delete operation fails
        """
        logger.debug("Clearing all vulnerabilities")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete all vulnerabilities
                cursor.execute("DELETE FROM vulnerabilities")
                conn.commit()

                logger.debug("Cleared all vulnerabilities")

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error clearing vulnerabilities: {str(e)}")
            raise QueryError(f"Failed to clear vulnerabilities: {str(e)}") from e

    def save_task(self, task: Task) -> None:
        """
        Save a task to the database.

        Args:
            task: The task to save

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the save operation fails
        """
        logger.debug(f"Saving task: {task.name}")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if the task already exists
                cursor.execute("SELECT name FROM tasks WHERE name = ?", (task.name,))
                exists = cursor.fetchone() is not None

                now = datetime.now().isoformat()

                if exists:
                    # Update the task
                    cursor.execute(
                        """
                        UPDATE tasks
                        SET description = ?, phase = ?, status = ?, start_time = ?,
                            end_time = ?, notes = ?, updated_at = ?
                        WHERE name = ?
                    """,
                        (
                            task.description,
                            task.phase.value,
                            task.status.value,
                            task.start_time.isoformat() if task.start_time else None,
                            task.end_time.isoformat() if task.end_time else None,
                            task.notes,
                            now,
                            task.name,
                        ),
                    )

                    # Delete existing dependencies
                    cursor.execute(
                        "DELETE FROM task_dependencies WHERE task_name = ?",
                        (task.name,),
                    )
                else:
                    # Insert the task
                    cursor.execute(
                        """
                        INSERT INTO tasks (
                            name, description, phase, status, start_time,
                            end_time, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            task.name,
                            task.description,
                            task.phase.value,
                            task.status.value,
                            task.start_time.isoformat() if task.start_time else None,
                            task.end_time.isoformat() if task.end_time else None,
                            task.notes,
                            now,
                            now,
                        ),
                    )

                # Insert dependencies
                for dependency in task.dependencies:
                    cursor.execute(
                        """
                        INSERT INTO task_dependencies (task_name, dependency_name)
                        VALUES (?, ?)
                    """,
                        (
                            task.name,
                            dependency,
                        ),
                    )

                # Commit the changes
                conn.commit()

                logger.debug(f"Task {task.name} saved successfully")

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error saving task: {str(e)}")
            raise QueryError(f"Failed to save task: {str(e)}") from e

    def get_task(self, task_name: str) -> Optional[Task]:
        """
        Get a task from the database.

        Args:
            task_name: The name of the task to get

        Returns:
            The task, or None if not found

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the query fails
        """
        logger.debug(f"Getting task: {task_name}")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get the task
                cursor.execute("SELECT * FROM tasks WHERE name = ?", (task_name,))
                row = cursor.fetchone()

                if not row:
                    logger.debug(f"Task {task_name} not found")
                    return None

                # Get dependencies
                cursor.execute(
                    "SELECT dependency_name FROM task_dependencies WHERE task_name = ?",
                    (task_name,),
                )
                dependencies = [r["dependency_name"] for r in cursor.fetchall()]

                # Create a Task object
                task = Task(
                    name=row["name"],
                    description=row["description"],
                    phase=ImplementationPhase(row["phase"]),
                    status=TaskStatus(row["status"]),
                    dependencies=dependencies,
                    notes=row["notes"],
                )

                # Set start and end times
                if row["start_time"]:
                    task.start_time = datetime.fromisoformat(row["start_time"])
                if row["end_time"]:
                    task.end_time = datetime.fromisoformat(row["end_time"])

                logger.debug(f"Task {task_name} retrieved successfully")
                return task

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            raise QueryError(f"Failed to get task: {str(e)}") from e

    def get_tasks(self) -> List[Task]:
        """
        Get all tasks from the database.

        Returns:
            A list of all tasks

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the query fails
        """
        logger.debug("Getting all tasks")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get all tasks
                cursor.execute("SELECT * FROM tasks")
                rows = cursor.fetchall()

                # Create Task objects
                tasks = []
                for row in rows:
                    # Get dependencies
                    cursor.execute(
                        "SELECT dependency_name FROM task_dependencies WHERE task_name = ?",
                        (row["name"],),
                    )
                    dependencies = [r["dependency_name"] for r in cursor.fetchall()]

                    # Create a Task object
                    task = Task(
                        name=row["name"],
                        description=row["description"],
                        phase=ImplementationPhase(row["phase"]),
                        status=TaskStatus(row["status"]),
                        dependencies=dependencies,
                        notes=row["notes"],
                    )

                    # Set start and end times
                    if row["start_time"]:
                        task.start_time = datetime.fromisoformat(row["start_time"])
                    if row["end_time"]:
                        task.end_time = datetime.fromisoformat(row["end_time"])

                    tasks.append(task)

                logger.debug(f"Retrieved {len(tasks)} tasks")
                return tasks

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error getting tasks: {str(e)}")
            raise QueryError(f"Failed to get tasks: {str(e)}") from e

    def save_implementation_plan(self, plan: ImplementationPlan) -> None:
        """
        Save an implementation plan to the database.

        Args:
            plan: The implementation plan to save

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the save operation fails
        """
        logger.debug("Saving implementation plan")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if an implementation plan already exists
                cursor.execute("SELECT id FROM implementation_plan")
                row = cursor.fetchone()

                now = datetime.now().isoformat()

                if row:
                    # Update the implementation plan
                    cursor.execute(
                        """
                        UPDATE implementation_plan
                        SET start_time = ?, end_time = ?, current_phase = ?, updated_at = ?
                        WHERE id = ?
                    """,
                        (
                            plan.start_time.isoformat() if plan.start_time else None,
                            plan.end_time.isoformat() if plan.end_time else None,
                            plan.current_phase.value if plan.current_phase else None,
                            now,
                            row["id"],
                        ),
                    )
                else:
                    # Insert the implementation plan
                    cursor.execute(
                        """
                        INSERT INTO implementation_plan (
                            start_time, end_time, current_phase, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            plan.start_time.isoformat() if plan.start_time else None,
                            plan.end_time.isoformat() if plan.end_time else None,
                            plan.current_phase.value if plan.current_phase else None,
                            now,
                            now,
                        ),
                    )

                # Save all tasks
                for task in plan.tasks.values():
                    self.save_task(task)

                # Commit the changes
                conn.commit()

                logger.debug("Implementation plan saved successfully")

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error saving implementation plan: {str(e)}")
            raise QueryError(f"Failed to save implementation plan: {str(e)}") from e

    def get_implementation_plan(self) -> Optional[ImplementationPlan]:
        """
        Get the implementation plan from the database.

        Returns:
            The implementation plan, or None if not found

        Raises:
            ConnectionError: If the connection cannot be established
            QueryError: If the query fails
        """
        logger.debug("Getting implementation plan")

        try:
            with db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get the implementation plan
                cursor.execute("SELECT * FROM implementation_plan")
                row = cursor.fetchone()

                if not row:
                    logger.debug("Implementation plan not found")
                    return None

                # Create an ImplementationPlan object
                plan = ImplementationPlan()

                # Set start and end times
                if row["start_time"]:
                    plan.start_time = datetime.fromisoformat(row["start_time"])
                if row["end_time"]:
                    plan.end_time = datetime.fromisoformat(row["end_time"])

                # Set current phase
                if row["current_phase"]:
                    plan.current_phase = ImplementationPhase(row["current_phase"])

                # Get all tasks
                tasks = self.get_tasks()
                for task in tasks:
                    plan.add_task(task)

                logger.debug("Implementation plan retrieved successfully")
                return plan

        except ConnectionError:
            # Re-raise connection errors
            raise
        except Exception as e:
            logger.error(f"Error getting implementation plan: {str(e)}")
            raise QueryError(f"Failed to get implementation plan: {str(e)}") from e
