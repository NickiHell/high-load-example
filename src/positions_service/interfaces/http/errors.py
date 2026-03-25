from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse

from positions_service.domain.exceptions import DomainError, InvalidCoordinatesError


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    if not isinstance(exc, DomainError):
        raise exc
    if isinstance(exc, InvalidCoordinatesError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )
