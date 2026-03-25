from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from positions_service.application.commands import RegisterPositionCommand
from positions_service.application.ports import DomainEventPublisher, UnitOfWork
from positions_service.domain.entities import Position

UoWFactory = Callable[[], AbstractAsyncContextManager[UnitOfWork]]


class RegisterPositionHandler:
    def __init__(
        self,
        uow_factory: UoWFactory,
        publisher: DomainEventPublisher,
    ) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher

    async def __call__(self, command: RegisterPositionCommand) -> UUID:
        position, events = Position.register(
            command.coordinates,
            external_ref=command.external_ref,
        )
        async with self._uow_factory() as uow:
            await uow.positions.add(position)
            await uow.commit()
        await self._publisher.publish_position_recorded(events)
        return position.id
