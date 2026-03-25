from __future__ import annotations

from typing import Self
from uuid import UUID

import pytest

from positions_service.application.commands import RegisterPositionCommand
from positions_service.application.handlers import RegisterPositionHandler
from positions_service.application.ports import DomainEventPublisher
from positions_service.domain.entities import Position
from positions_service.domain.events import PositionRecorded
from positions_service.domain.value_objects import Coordinates


class FakePositionRepository:
    def __init__(self) -> None:
        self.items: list[Position] = []

    async def add(self, position: Position) -> None:
        self.items.append(position)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self._repo = FakePositionRepository()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        pass

    @property
    def positions(self) -> FakePositionRepository:
        return self._repo

    async def commit(self) -> None:
        self.committed = True


class FakePublisher(DomainEventPublisher):
    def __init__(self) -> None:
        self.recorded: list[tuple[PositionRecorded, ...]] = []

    async def publish_position_recorded(self, events: tuple[PositionRecorded, ...]) -> None:
        self.recorded.append(events)


@pytest.mark.asyncio
async def test_register_position_handler() -> None:
    publisher = FakePublisher()
    uow_instances: list[FakeUnitOfWork] = []

    def uow_factory() -> FakeUnitOfWork:
        u = FakeUnitOfWork()
        uow_instances.append(u)
        return u

    handler = RegisterPositionHandler(uow_factory=uow_factory, publisher=publisher)
    coords = Coordinates(latitude=59.93, longitude=30.33)
    cmd = RegisterPositionCommand(coordinates=coords, external_ref="track-1")

    pid = await handler(cmd)

    assert isinstance(pid, UUID)
    assert len(uow_instances) == 1
    assert uow_instances[0].committed is True
    assert len(uow_instances[0].positions.items) == 1
    assert len(publisher.recorded) == 1
    ev = publisher.recorded[0][0]
    assert ev.latitude == 59.93
    assert ev.external_ref == "track-1"
