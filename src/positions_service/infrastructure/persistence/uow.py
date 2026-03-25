from __future__ import annotations

from types import TracebackType
from typing import TYPE_CHECKING, Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from positions_service.infrastructure.persistence.repository import PostgresPositionRepository

if TYPE_CHECKING:
    from positions_service.application.ports import PositionRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._positions: PostgresPositionRepository | None = None

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self._positions = PostgresPositionRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()
        self._session = None
        self._positions = None

    @property
    def positions(self) -> PositionRepository:
        if self._positions is None:
            msg = "UnitOfWork не инициализирован"
            raise RuntimeError(msg)
        return self._positions

    async def commit(self) -> None:
        if self._session is None:
            msg = "UnitOfWork не инициализирован"
            raise RuntimeError(msg)
        await self._session.commit()
