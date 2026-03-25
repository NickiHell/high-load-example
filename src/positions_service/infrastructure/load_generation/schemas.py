from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

_MAX_STAGES = 64


class LoadWaveStage(BaseModel):
    duration_seconds: float = Field(gt=0, le=3600)
    concurrency: int = Field(ge=0, le=2000)


class LoadWaveRequest(BaseModel):
    stages: list[LoadWaveStage] | None = None
    think_time_ms_min: float = Field(default=30, ge=0, le=10_000)
    think_time_ms_max: float = Field(default=100, ge=0, le=10_000)

    @model_validator(mode="after")
    def think_order(self) -> Self:
        if self.think_time_ms_min > self.think_time_ms_max:
            msg = "think_time_ms_min must be <= think_time_ms_max"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def stages_limit(self) -> Self:
        if self.stages is not None and len(self.stages) > _MAX_STAGES:
            msg = f"at most {_MAX_STAGES} stages"
            raise ValueError(msg)
        return self


def default_demo_stages() -> list[LoadWaveStage]:
    """Сценарий по умолчанию для POST /api/v1/load/wave (без тела)."""
    return [
        LoadWaveStage(duration_seconds=30, concurrency=15),
        LoadWaveStage(duration_seconds=45, concurrency=15),
        LoadWaveStage(duration_seconds=20, concurrency=55),
        LoadWaveStage(duration_seconds=60, concurrency=55),
        LoadWaveStage(duration_seconds=40, concurrency=10),
        LoadWaveStage(duration_seconds=45, concurrency=10),
        LoadWaveStage(duration_seconds=30, concurrency=0),
        LoadWaveStage(duration_seconds=45, concurrency=0),
        LoadWaveStage(duration_seconds=25, concurrency=75),
        LoadWaveStage(duration_seconds=70, concurrency=75),
        LoadWaveStage(duration_seconds=35, concurrency=20),
        LoadWaveStage(duration_seconds=40, concurrency=20),
        LoadWaveStage(duration_seconds=40, concurrency=0),
    ]


class LoadWaveAccepted(BaseModel):
    run_id: str
    status: Literal["accepted"] = "accepted"


class LoadWaveStatusBody(BaseModel):
    running: bool
    run_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
