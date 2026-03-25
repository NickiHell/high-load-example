from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from positions_service.domain.entities import Position
from positions_service.infrastructure.persistence.mappers import position_to_row


class PostgresPositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, position: Position) -> None:
        row = position_to_row(position)
        self._session.add(row)
