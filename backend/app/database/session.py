from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.database.engine import create_engine

settings = Settings()
engine = create_engine(settings)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncSession:
    """FastAPI dependency that provides an AsyncSession."""
    async with async_session_maker() as session:
        yield session


