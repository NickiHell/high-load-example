from __future__ import annotations

from dataclasses import dataclass

from positions_service.domain.exceptions import InvalidCoordinatesError

_MIN_LAT = -90.0
_MAX_LAT = 90.0
_MIN_LON = -180.0
_MAX_LON = 180.0


@dataclass(frozen=True, slots=True)
class Coordinates:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not _MIN_LAT <= self.latitude <= _MAX_LAT:
            msg = "Широта должна быть в диапазоне [-90, 90]"
            raise InvalidCoordinatesError(msg)
        if not _MIN_LON <= self.longitude <= _MAX_LON:
            msg = "Долгота должна быть в диапазоне [-180, 180]"
            raise InvalidCoordinatesError(msg)
