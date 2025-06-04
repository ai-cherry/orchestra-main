"""
Role-Based Access Control (RBAC) configuration
"""

from enum import Enum
from typing import Dict, List, Set
from pydantic import BaseModel

class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    DEVELOPER = "developer"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Permission(str, Enum):
    """System permissions"""
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    MANAGE_SYSTEM = "manage_system"

    # Development permissions
    CREATE_AGENTS = "create_agents"
    MODIFY_AGENTS = "modify_agents"
    DELETE_AGENTS = "delete_agents"
    EXECUTE_AGENTS = "execute_agents"

    # Operational permissions
    VIEW_LOGS = "view_logs"
    VIEW_METRICS = "view_metrics"
    MANAGE_DEPLOYMENTS = "manage_deployments"

    # Data permissions
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"

    # API permissions
    API_READ = "api_read"
    API_WRITE = "api_write"
    API_DELETE = "api_delete"

# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions

    Role.DEVELOPER: {
        Permission.CREATE_AGENTS,
        Permission.MODIFY_AGENTS,
        Permission.DELETE_AGENTS,
        Permission.EXECUTE_AGENTS,
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS,
        Permission.READ_DATA,
        Permission.WRITE_DATA,
        Permission.API_READ,
        Permission.API_WRITE,
    },

    Role.OPERATOR: {
        Permission.EXECUTE_AGENTS,
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS,
        Permission.MANAGE_DEPLOYMENTS,
        Permission.READ_DATA,
        Permission.API_READ,
    },

    Role.VIEWER: {
        Permission.VIEW_LOGS,
        Permission.VIEW_METRICS,
        Permission.READ_DATA,
        Permission.API_READ,
    },
}

class UserRole(BaseModel):
    """User role assignment"""
    user_id: str
    role: Role
    permissions: Set[Permission] = set()

    def __init__(self, **data):
        super().__init__(**data)
        # Automatically assign permissions based on role
        if not self.permissions:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set())

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(p in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        return all(p in self.permissions for p in permissions)

def check_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if user has required permission"""
    return user_role.has_permission(required_permission)

def check_any_permission(user_role: UserRole, required_permissions: List[Permission]) -> bool:
    """Check if user has any of the required permissions"""
    return user_role.has_any_permission(required_permissions)

def check_all_permissions(user_role: UserRole, required_permissions: List[Permission]) -> bool:
    """Check if user has all required permissions"""
    return user_role.has_all_permissions(required_permissions)
