from __future__ import annotations

from positions_service.domain.entities import Position
from positions_service.infrastructure.persistence.models import PositionRow


def position_to_row(position: Position) -> PositionRow:
    return PositionRow(
        id=position.id,
        latitude=position.coordinates.latitude,
        longitude=position.coordinates.longitude,
        recorded_at=position.recorded_at,
        external_ref=position.external_ref,
    )
