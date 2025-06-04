"""Unified database interface for Cherry AI"""

import os
import logging
from typing import Dict, Any, List, Optional
from typing_extensions import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """Unified interface for database operations"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://localhost/cherry_ai")
        self.engine = None
        self.async_engine = None
        self._init_engines()
    
    def _init_engines(self):
        """Initialize database engines"""
        try:
            # Convert to async URL if needed
            if self.database_url.startswith("postgresql://"):
                async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            else:
                async_url = self.database_url
            
            self.async_engine = create_async_engine(async_url, echo=False)
            logger.info("Database engines initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    async def execute(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        if not self.async_engine:
            return []
        
        try:
            async with AsyncSession(self.async_engine) as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                
                # Convert to list of dicts
                if rows and result.keys():
                    return [dict(zip(result.keys(), row)) for row in rows]
                return []
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    async def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Fetch all results from a query (compatibility method)"""
        # Convert tuple params to dict for execute method
        if params:
            # Simple conversion for positional parameters
            param_dict = {str(i+1): param for i, param in enumerate(params)}
            # Replace $1, $2, etc. with :1, :2, etc.
            for i in range(len(params)):
                query = query.replace(f"${i+1}", f":{i+1}")
        else:
            param_dict = {}
        
        return await self.execute(query, param_dict)
    
    async def insert(self, table: str, data: Dict[str, Any]) -> Optional[str]:
        """Insert data into a table"""
        if not self.async_engine:
            return None
        
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{k}" for k in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
            
            async with AsyncSession(self.async_engine) as session:
                result = await session.execute(text(query), data)
                await session.commit()
                
                row = result.fetchone()
                return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Database insert error: {e}")
            return None
    
    async def update(self, table: str, id: str, data: Dict[str, Any]) -> bool:
        """Update a record in a table"""
        if not self.async_engine:
            return False
        
        try:
            set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE id = :id"
            
            data["id"] = id
            
            async with AsyncSession(self.async_engine) as session:
                await session.execute(text(query), data)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Database update error: {e}")
            return False
    
    async def delete(self, table: str, id: str) -> bool:
        """Delete a record from a table"""
        if not self.async_engine:
            return False
        
        try:
            query = f"DELETE FROM {table} WHERE id = :id"
            
            async with AsyncSession(self.async_engine) as session:
                await session.execute(text(query), {"id": id})
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Database delete error: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()