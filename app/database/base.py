from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, joinedload, mapped_column
from sqlalchemy.orm.attributes import QueryableAttribute

from app.database.exceptions import conflict_error, not_found_error


class Base(DeclarativeBase):
    __abstract__ = True

    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return resolve_table_name(cls.__name__)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=lambda: uuid4())

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
        sort_order=-2,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        sort_order=-1,
    )

    async def save(
        self,
        async_session: AsyncSession,
        relationships: list[QueryableAttribute] | None = None,
    ) -> Self:
        try:
            async_session.add(self)
            await async_session.commit()
        except IntegrityError as e:
            raise conflict_error() from e
        if relationships:
            return await self.__class__.get_or_raise(async_session, self.id, relationships)
        return self

    @classmethod
    async def get(
        cls,
        async_session: AsyncSession,
        id_: UUID,
        relationships: list[QueryableAttribute] | None = None,
    ) -> Self | None:
        stmt = select(cls).where(cls.id == id_)
        if relationships:
            stmt = stmt.options(*[joinedload(r) for r in relationships])
        return await async_session.scalar(stmt)

    @classmethod
    async def get_or_raise(
        cls,
        async_session: AsyncSession,
        id_: UUID,
        relationships: list[QueryableAttribute] | None = None,
    ) -> Self:
        result = await cls.get(async_session, id_, relationships)
        if not result:
            raise not_found_error(msg=f"{cls.__name__} not found")
        return result

    @classmethod
    async def all(cls, async_session: AsyncSession) -> Sequence[Self]:
        result = await async_session.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def delete_all(cls, async_session: AsyncSession) -> None:
        stmt = delete(cls)
        await async_session.execute(stmt)

    async def delete(self, async_session: AsyncSession) -> None:
        await async_session.delete(self)
        await async_session.commit()

    async def update(self, async_session: AsyncSession, **kwargs: dict[str, Any]) -> Self:
        for key, value in kwargs.items():
            setattr(self, key, value)
        await async_session.commit()
        return self

    @classmethod
    async def find(
        cls,
        async_session: AsyncSession,
        relationships: list[QueryableAttribute] | None = None,
        **kwargs,  # noqa: ANN003
    ) -> Self | None:
        stmt = select(cls).filter_by(**kwargs)
        if relationships:
            stmt = stmt.options(*[joinedload(r) for r in relationships])
        return await async_session.scalar(stmt)

    @classmethod
    async def find_or_raise(
        cls,
        async_session: AsyncSession,
        relationships: list[QueryableAttribute] | None = None,
        **kwargs,  # noqa: ANN003
    ) -> Self:
        resp = await cls.find(async_session, relationships, **kwargs)
        if not resp:
            raise not_found_error(msg=f"{cls.__name__} not found")
        return resp

    @classmethod
    async def find_all(
        cls,
        async_session: AsyncSession,
        relationships: list[QueryableAttribute] | None = None,
        **kwargs,  # noqa: ANN003
    ) -> Sequence[Self]:
        stmt = select(cls).filter_by(**kwargs)
        if relationships:
            stmt = stmt.options(*[joinedload(r) for r in relationships])
        result = await async_session.execute(stmt)
        return result.scalars().all()


def resolve_table_name(name: str) -> str:
    """Resolves table names to their mapped names."""
    names = re.split("(?=[A-Z])", name)
    return "_".join([x.lower() for x in names if x])
