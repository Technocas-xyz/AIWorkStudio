"""Database session configuration."""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Detect local mode
if os.environ.get("APP_ENV") == "local":
    from app.config_local import get_local_settings
    _settings = get_local_settings()
    engine = create_async_engine(_settings.database_url, echo=False)
else:
    from app.config import get_settings
    _settings = get_settings()
    engine = create_async_engine(
        _settings.database_url,
        echo=_settings.app_debug,
        pool_pre_ping=True,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
