from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PositionCreateRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90, description="Широта WGS-84")
    longitude: float = Field(ge=-180, le=180, description="Долгота WGS-84")
    external_ref: str | None = Field(None, max_length=256, description="Внешний идентификатор")

    @field_validator("external_ref")
    @classmethod
    def strip_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class PositionCreatedResponse(BaseModel):
    id: UUID
