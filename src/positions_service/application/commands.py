from __future__ import annotations

from dataclasses import dataclass

from positions_service.domain.value_objects import Coordinates


@dataclass(frozen=True, slots=True)
class RegisterPositionCommand:
    coordinates: Coordinates
    external_ref: str | None = None
