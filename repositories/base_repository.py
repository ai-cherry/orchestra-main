"""
Base Repository Pattern
Provides abstract interface for data access following SOLID principles
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncpg

class BaseRepository(ABC):
    """Abstract base repository"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Find all entities"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete entity"""
        pass

class UserRepository(BaseRepository):
    """Repository for user data access"""
    
    async def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE id = $1", id
            )
            return dict(row) if row else None
    
    async def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE username = $1", username
            )
            return dict(row) if row else None
    
    async def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM shared.users ORDER BY created_at DESC LIMIT $1", limit
            )
            return [dict(row) for row in rows]
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO shared.users (username, email, password_hash, role)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """, data['username'], data['email'], data['password_hash'], data.get('role', 'user'))
            return dict(row)
    
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Build dynamic update query
        set_clauses = []
        values = []
        param_count = 1
        
        for key, value in data.items():
            if key not in ['id', 'created_at']:  # Skip immutable fields
                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not set_clauses:
            return None
        
        values.append(id)
        query = f"""
            UPDATE shared.users 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ${param_count}
            RETURNING *
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None
    
    async def delete(self, id: int) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM shared.users WHERE id = $1", id
            )
            return result.split()[-1] != '0'
