from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.types import ASGIApp

from positions_service.infrastructure.config import Settings, get_settings
from positions_service.infrastructure.load_generation.schemas import (
    LoadWaveAccepted,
    LoadWaveRequest,
    LoadWaveStage,
    LoadWaveStatusBody,
    default_demo_stages,
)
from positions_service.infrastructure.load_generation.wave_runner import run_wave

logger = structlog.get_logger(__name__)

load_router = APIRouter(prefix="/api/v1/load", tags=["load"])


def get_settings_dep() -> Settings:
    return get_settings()


async def _load_guard(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> None:
    if not settings.load_generator_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="load generator disabled")


class _WaveRunState:
    __slots__ = ("error", "finished_at", "lock", "run_id", "running", "started_at")

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.running = False
        self.run_id: str | None = None
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.error: str | None = None


_state = _WaveRunState()


async def _background_wave(
    *,
    run_id: str,
    asgi_app: ASGIApp,
    body: LoadWaveRequest,
    stages_eff: list[LoadWaveStage],
) -> None:
    try:
        await run_wave(
            asgi_app=asgi_app,
            stages=stages_eff,
            think_time_ms_min=body.think_time_ms_min,
            think_time_ms_max=body.think_time_ms_max,
            run_id=run_id,
        )
    except (OSError, RuntimeError, ValueError, httpx.HTTPError) as exc:
        logger.exception("load_wave_failed", run_id=run_id, error=str(exc))
        async with _state.lock:
            _state.error = str(exc)
    else:
        async with _state.lock:
            _state.error = None
    finally:
        async with _state.lock:
            _state.running = False
            _state.finished_at = datetime.now(tz=UTC)
        logger.info("load_wave_finished", run_id=run_id)


@load_router.post(
    "/wave",
    response_model=LoadWaveAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(_load_guard)],
    summary="Запустить волновую нагрузку на сам сервис (in-process ASGI, без TCP loopback)",
)
async def start_load_wave(
    request: Request,
    body: LoadWaveRequest,
) -> LoadWaveAccepted:
    stages_eff = body.stages if body.stages is not None else default_demo_stages()
    async with _state.lock:
        if _state.running:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="wave run already in progress",
            )
        run_id = str(uuid.uuid4())
        _state.running = True
        _state.run_id = run_id
        _state.started_at = datetime.now(tz=UTC)
        _state.finished_at = None
        _state.error = None

    request.app.state.load_wave_task = asyncio.create_task(
        _background_wave(
            run_id=run_id,
            asgi_app=request.app,
            body=body,
            stages_eff=stages_eff,
        ),
    )
    return LoadWaveAccepted(run_id=run_id)


@load_router.get(
    "/wave/status",
    response_model=LoadWaveStatusBody,
    dependencies=[Depends(_load_guard)],
    summary="Статус последнего/текущего прогона волны",
)
async def load_wave_status() -> LoadWaveStatusBody:
    async with _state.lock:
        return LoadWaveStatusBody(
            running=_state.running,
            run_id=_state.run_id,
            started_at=_state.started_at.isoformat() if _state.started_at else None,
            finished_at=_state.finished_at.isoformat() if _state.finished_at else None,
            error=_state.error,
        )
