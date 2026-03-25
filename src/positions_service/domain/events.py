from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypeAlias
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PositionRecorded:
    position_id: UUID
    latitude: float
    longitude: float
    recorded_at: datetime
    external_ref: str | None


DomainEvent: TypeAlias = PositionRecorded
