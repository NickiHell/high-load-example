from __future__ import annotations

import pytest

from positions_service.domain.exceptions import InvalidCoordinatesError
from positions_service.domain.value_objects import Coordinates


def test_coordinates_valid() -> None:
    c = Coordinates(latitude=55.75, longitude=37.62)
    assert c.latitude == 55.75
    assert c.longitude == 37.62


@pytest.mark.parametrize(
    ("lat", "lon"),
    [
        (91.0, 0.0),
        (-91.0, 0.0),
        (0.0, 181.0),
        (0.0, -181.0),
    ],
)
def test_coordinates_invalid(lat: float, lon: float) -> None:
    with pytest.raises(InvalidCoordinatesError):
        Coordinates(latitude=lat, longitude=lon)
