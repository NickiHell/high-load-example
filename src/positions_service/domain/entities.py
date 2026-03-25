from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from positions_service.domain.events import PositionRecorded
from positions_service.domain.value_objects import Coordinates


@dataclass(slots=True)
class Position:
    id: UUID
    coordinates: Coordinates
    recorded_at: datetime
    external_ref: str | None

    @classmethod
    def register(
        cls,
        coordinates: Coordinates,
        *,
        external_ref: str | None,
        recorded_at: datetime | None = None,
    ) -> tuple[Position, tuple[PositionRecorded, ...]]:
        now = recorded_at or datetime.now(tz=UTC)
        position_id = uuid4()
        position = cls(
            id=position_id,
            coordinates=coordinates,
            recorded_at=now,
            external_ref=external_ref,
        )
        event = PositionRecorded(
            position_id=position_id,
            latitude=coordinates.latitude,
            longitude=coordinates.longitude,
            recorded_at=now,
            external_ref=external_ref,
        )
        return position, (event,)
