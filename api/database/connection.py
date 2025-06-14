"""
Database connection proxy for API module
Re-exports from root database module for backward compatibility
"""

# Re-export everything from the root database module
from database.connection import *

# This allows the API to use:
# from api.database.connection import init_database, close_database, get_db, db_manager 