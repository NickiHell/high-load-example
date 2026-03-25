from __future__ import annotations

from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from positions_service.domain.entities import Position
from positions_service.domain.events import PositionRecorded


@runtime_checkable
class PositionRepository(Protocol):
    async def add(self, position: Position) -> None: ...


@runtime_checkable
class DomainEventPublisher(Protocol):
    async def publish_position_recorded(self, events: tuple[PositionRecorded, ...]) -> None: ...


@runtime_checkable
class UnitOfWork(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

    @property
    def positions(self) -> PositionRepository: ...

    async def commit(self) -> None: ...
