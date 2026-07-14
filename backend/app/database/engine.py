from app.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    return create_async_engine(settings.database_url, pool_pre_ping=True)

