from __future__ import annotations

import asyncio
import random
from collections.abc import Sequence
from dataclasses import dataclass

import httpx
import structlog
from starlette.types import ASGIApp

from positions_service.infrastructure.load_generation.schemas import LoadWaveStage

logger = structlog.get_logger(__name__)

POSITIONS_PATH = "/api/v1/positions"


def _format_wave_error(exc: BaseException) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        body = ""
        if exc.response is not None:
            try:
                body = exc.response.text[:400]
            except OSError, RuntimeError, ValueError:
                body = ""
        code = exc.response.status_code if exc.response else "?"
        return f"{exc.__class__.__name__} {code} {body!r}".strip()
    if isinstance(exc, httpx.RequestError):
        return f"{exc.__class__.__name__} {exc.request.method!s} {exc.request.url!s} — {exc!r}"
    return f"{exc.__class__.__name__}: {exc!r}"


async def run_wave(
    *,
    asgi_app: ASGIApp,
    stages: Sequence[LoadWaveStage],
    think_time_ms_min: float,
    think_time_ms_max: float,
    run_id: str,
) -> None:
    base = "http://testserver"
    logger.info(
        "load_wave_started",
        run_id=run_id,
        transport="asgi",
        base_url=base,
    )
    for idx, stage in enumerate(stages):
        logger.info(
            "load_wave_stage",
            run_id=run_id,
            stage_index=idx,
            duration_seconds=stage.duration_seconds,
            concurrency=stage.concurrency,
        )
        if stage.concurrency == 0:
            await asyncio.sleep(stage.duration_seconds)
            continue
        await _run_stage(
            _StageParams(
                base=base,
                asgi_app=asgi_app,
                duration_seconds=stage.duration_seconds,
                concurrency=stage.concurrency,
                think_time_ms_min=think_time_ms_min,
                think_time_ms_max=think_time_ms_max,
                run_id=run_id,
                stage_index=idx,
            ),
        )


@dataclass(frozen=True, slots=True)
class _StageParams:
    base: str
    asgi_app: ASGIApp
    duration_seconds: float
    concurrency: int
    think_time_ms_min: float
    think_time_ms_max: float
    run_id: str
    stage_index: int


_MAX_FAILURE_LOGS_PER_STAGE = 40


async def _run_stage(params: _StageParams) -> None:
    stop = asyncio.Event()
    c = params.concurrency
    limits = httpx.Limits(max_connections=max(c + 5, 10), max_keepalive_connections=max(c + 5, 10))
    fail_lock = asyncio.Lock()
    fail_logged = 0
    timeout = httpx.Timeout(60.0)

    async def _drive(client: httpx.AsyncClient) -> None:
        async def worker(worker_id: int) -> None:
            nonlocal fail_logged
            rng = random.Random()  # noqa: S311
            while not stop.is_set():
                lat = 55.75 + rng.random() * 0.08
                lon = 37.62 + rng.random() * 0.08
                payload = {
                    "latitude": lat,
                    "longitude": lon,
                    "external_ref": f"wave-{params.run_id}-s{params.stage_index}-w{worker_id}",
                }
                try:
                    response = await client.post(POSITIONS_PATH, json=payload)
                    response.raise_for_status()
                except (httpx.HTTPError, ValueError) as exc:
                    err_text = _format_wave_error(exc)
                    async with fail_lock:
                        fail_logged += 1
                        n = fail_logged
                    if n <= _MAX_FAILURE_LOGS_PER_STAGE:
                        logger.warning(
                            "load_wave_request_failed",
                            run_id=params.run_id,
                            error=err_text,
                        )
                    elif n == _MAX_FAILURE_LOGS_PER_STAGE + 1:
                        logger.warning(
                            "load_wave_request_failed_suppressing",
                            run_id=params.run_id,
                            logged=_MAX_FAILURE_LOGS_PER_STAGE,
                        )
                think_s = rng.uniform(params.think_time_ms_min, params.think_time_ms_max) / 1000.0
                try:
                    await asyncio.wait_for(stop.wait(), timeout=think_s)
                except TimeoutError:
                    continue

        tasks = [asyncio.create_task(worker(i)) for i in range(params.concurrency)]
        await asyncio.sleep(params.duration_seconds)
        stop.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        if fail_logged > _MAX_FAILURE_LOGS_PER_STAGE:
            logger.warning(
                "load_wave_stage_failures_total",
                run_id=params.run_id,
                stage_index=params.stage_index,
                failures=fail_logged,
            )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=params.asgi_app),
        base_url=params.base,
        limits=limits,
        timeout=timeout,
    ) as client:
        await _drive(client)
