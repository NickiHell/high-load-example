from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from positions_service.application.handlers import RegisterPositionHandler
from positions_service.domain.exceptions import DomainError
from positions_service.infrastructure.config import get_settings
from positions_service.infrastructure.messaging.kafka_publisher import KafkaPositionEventPublisher
from positions_service.infrastructure.persistence.uow import SqlAlchemyUnitOfWork
from positions_service.interfaces.http.errors import domain_error_handler
from positions_service.interfaces.http.load_router import load_router
from positions_service.interfaces.http.router import get_register_handler, router

logger = structlog.get_logger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _configure_logging()
    settings = get_settings()
    engine = create_async_engine(
        str(settings.database_url),
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
    )
    await producer.start()

    publisher = KafkaPositionEventPublisher(producer, settings.kafka_topic_positions)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    handler = RegisterPositionHandler(uow_factory=uow_factory, publisher=publisher)

    app.state.engine = engine
    app.state.producer = producer
    app.state.settings = settings

    def override_handler() -> RegisterPositionHandler:
        return handler

    app.dependency_overrides[get_register_handler] = override_handler

    logger.info("app_started", app=settings.app_name)
    yield
    await producer.stop()
    await engine.dispose()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(router)
    app.include_router(load_router)
    app.add_exception_handler(DomainError, domain_error_handler)

    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health/live", "/health/ready"],
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)

    @app.get("/health/live", tags=["health"])
    async def health_live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["health"])
    async def health_ready(request: Request) -> dict[str, Any]:
        engine = request.app.state.engine
        settings = request.app.state.settings
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except (OSError, TimeoutError, RuntimeError) as exc:
            logger.exception("health_db_failed", error=str(exc))
            return {"status": "not_ready", "database": "down"}
        return {
            "status": "ok",
            "database": "up",
            "kafka_bootstrap": settings.kafka_bootstrap_servers,
        }

    return app


app = create_app()
