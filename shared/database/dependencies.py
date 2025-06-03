# TODO: Consider adding connection pooling configuration
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession # Keep for type hint if UnifiedPostgreSQL provides compatible session
from shared.unified_postgresql import get_unified_postgresql, UnifiedPostgreSQL

async def get_db_client() -> UnifiedPostgreSQL:
    """FastAPI dependency to get the UnifiedPostgreSQL client."""