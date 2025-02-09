from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.database.exceptions import DBSessionNotInitializedError
from app.settings import db_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, host: str, /, *, kwargs: dict[str, Any] | None = None) -> None:
        if kwargs is None:
            kwargs = {}

        self.engine: AsyncEngine | None = create_async_engine(str(host), **kwargs)
        self._session_maker: async_sessionmaker[AsyncSession] | None = async_sessionmaker(
            autocommit=False,
            bind=self.engine,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()

            self.engine = None
            self._session_maker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if not self.engine:
            raise DBSessionNotInitializedError

        async with self.engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise DBSessionNotInitializedError

        session = self._session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


session_manager = SessionManager(
    db_settings.url,
    kwargs={
        "echo": False,
        "pool_pre_ping": True,
        # For SQLite
        "connect_args": {"check_same_thread": False},
    },
)


async def get_async_session() -> AsyncGenerator:
    async with session_manager.session() as session:
        yield session
