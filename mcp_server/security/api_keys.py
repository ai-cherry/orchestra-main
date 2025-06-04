"""
Enhanced API Key Management
"""

import os
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path
import asyncpg
from pydantic import BaseModel

class APIKey(BaseModel):
    """API Key model"""
    id: str
    name: str
    key_hash: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    permissions: List[str] = []
    rate_limit: int = 100
    is_active: bool = True

class APIKeyManager:
    """Manage API keys with database persistence"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.key_prefix = "sk-"
        self.key_length = 48

    async def initialize(self):
        """Initialize API key table"""
        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    last_used TIMESTAMP,
                    permissions JSONB DEFAULT '[]',
                    rate_limit INTEGER DEFAULT 100,
                    is_active BOOLEAN DEFAULT true
                )
            """)

            # Create index on key_hash for fast lookups
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_hash 
                ON api_keys(key_hash)
            """)
        finally:
            await conn.close()

    def generate_api_key(self) -> tuple[str, str]:
        """Generate a new API key"""
        key_id = secrets.token_urlsafe(16)
        key_secret = secrets.token_urlsafe(self.key_length)
        full_key = f"{self.key_prefix}{key_secret}"
        return key_id, full_key

    def hash_key(self, key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    async def create_key(
        self, 
        name: str, 
        permissions: List[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit: int = 100
    ) -> Dict[str, str]:
        """Create a new API key"""
        key_id, full_key = self.generate_api_key()
        key_hash = self.hash_key(full_key)

        created_at = datetime.utcnow()
        expires_at = None
        if expires_in_days:
            expires_at = created_at + timedelta(days=expires_in_days)

        conn = await asyncpg.connect(self.db_url)
        try:
            await conn.execute("""
                INSERT INTO api_keys 
                (id, name, key_hash, created_at, expires_at, permissions, rate_limit)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, key_id, name, key_hash, created_at, expires_at, 
                json.dumps(permissions or []), rate_limit)
        finally:
            await conn.close()

        return {
            "id": key_id,
            "key": full_key,
            "name": name,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None
        }

    async def validate_key(self, api_key: str) -> Optional[APIKey]:
        """Validate an API key and return its details"""
        if not api_key or not api_key.startswith(self.key_prefix):
            return None

        key_hash = self.hash_key(api_key)

        conn = await asyncpg.connect(self.db_url)
        try:
            # Get key details
            row = await conn.fetchrow("""
                SELECT * FROM api_keys 
                WHERE key_hash = $1 AND is_active = true
            """, key_hash)

            if not row:
                return None

            # Check expiration
            if row['expires_at'] and row['expires_at'] < datetime.utcnow():
                return None

            # Update last used
            await conn.execute("""
                UPDATE api_keys 
                SET last_used = $1 
                WHERE id = $2
            """, datetime.utcnow(), row['id'])

            return APIKey(
                id=row['id'],
                name=row['name'],
                key_hash=row['key_hash'],
                created_at=row['created_at'],
                expires_at=row['expires_at'],
                last_used=row['last_used'],
                permissions=json.loads(row['permissions']),
                rate_limit=row['rate_limit'],
                is_active=row['is_active']
            )
        finally:
            await conn.close()
