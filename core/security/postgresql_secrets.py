"""
PostgreSQL-based secrets management to replace GCP Secret Manager.
"""
import os
import json
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class PostgreSQLSecretManager:
    """Manage secrets in PostgreSQL instead of GCP Secret Manager."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._ensure_table()
    
    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(self.database_url)
    
    def _ensure_table(self):
        """Ensure secrets table exists."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS secrets (
                        name VARCHAR(255) PRIMARY KEY,
                        value TEXT NOT NULL,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret value."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT value FROM secrets WHERE name = %s",
                    (name,)
                )
                result = cur.fetchone()
                return result['value'] if result else None
    
    def set_secret(self, name: str, value: str, metadata: Dict[str, Any] = None):
        """Set a secret value."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO secrets (name, value, metadata)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (name) DO UPDATE
                    SET value = EXCLUDED.value,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, (name, value, json.dumps(metadata or {})))
                conn.commit()
    
    def delete_secret(self, name: str):
        """Delete a secret."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM secrets WHERE name = %s", (name,))
                conn.commit()
    
    def list_secrets(self) -> list:
        """List all secret names."""
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT name, metadata, created_at, updated_at FROM secrets")
                return cur.fetchall()

# Helper function for compatibility
def get_secret(secret_name: str) -> Optional[str]:
    """Get secret from PostgreSQL (replaces GCP Secret Manager)."""
    database_url = os.getenv("DATABASE_URL", "postgresql://localhost/orchestra")
    manager = PostgreSQLSecretManager(database_url)
    return manager.get_secret(secret_name)
