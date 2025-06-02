from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession # Keep for type hint if UnifiedPostgreSQL provides compatible session
from .unified_postgresql import get_unified_postgresql, UnifiedPostgreSQL

async def get_db_client() -> UnifiedPostgreSQL:
    """FastAPI dependency to get the UnifiedPostgreSQL client."""
    db_client = await get_unified_postgresql()
    return db_client

# If UnifiedPostgreSQL or its manager directly provides an SQLAlchemy-like AsyncSession:
# async def get_db() -> AsyncGenerator[AsyncSession, None]:
#     db_client = await get_unified_postgresql()
#     # This part depends on how UnifiedPostgreSQL/ConnectionManager exposes sessions
#     # Assuming it has a method like .get_session() that returns an AsyncSession
#     async with db_client.get_sqlalchemy_session() as session: # This method needs to exist
#         yield session

# For now, let's provide the client. Routers might need to be adjusted
# if they expect an AsyncSession directly for SQLAlchemy ORM operations.
# If routers use methods from UnifiedPostgreSQL directly, get_db_client is fine. 