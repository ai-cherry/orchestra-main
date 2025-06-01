"""
Compatibility wrapper for unified PostgreSQL architecture.

This module redirects imports to the enhanced versions that include all missing methods.
"""

# Import enhanced versions
from .connection_manager_enhanced import (
    PostgreSQLConnectionManagerEnhanced as PostgreSQLConnectionManager,
    get_connection_manager_enhanced as get_connection_manager,
    close_connection_manager_enhanced as close_connection_manager
)

from .unified_postgresql_enhanced import (
    UnifiedPostgreSQLEnhanced as UnifiedPostgreSQL,
    get_unified_postgresql_enhanced as get_unified_postgresql,
    close_unified_postgresql_enhanced as close_unified_postgresql
)

# Re-export for compatibility
__all__ = [
    'PostgreSQLConnectionManager',
    'get_connection_manager',
    'close_connection_manager',
    'UnifiedPostgreSQL',
    'get_unified_postgresql',
    'close_unified_postgresql'
]
