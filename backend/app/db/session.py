"""Database session helpers for Conforma-AI."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def build_async_database_url(database_url: str) -> str:
    """Convert the configured database URL into an async SQLAlchemy URL."""

    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


settings = get_settings()
engine = create_async_engine(build_async_database_url(settings.database_url), future=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for FastAPI dependencies."""

    async with async_session_factory() as session:
        yield session
