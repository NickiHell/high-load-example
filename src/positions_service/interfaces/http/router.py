from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from positions_service.application.commands import RegisterPositionCommand
from positions_service.application.handlers import RegisterPositionHandler
from positions_service.domain.value_objects import Coordinates
from positions_service.interfaces.http.schemas import PositionCreatedResponse, PositionCreateRequest

router = APIRouter(prefix="/api/v1")


def get_register_handler() -> RegisterPositionHandler:
    msg = "RegisterPositionHandler не сконфигурирован"
    raise RuntimeError(msg)


HandlerDep = Annotated[RegisterPositionHandler, Depends(get_register_handler)]


@router.post(
    "/positions",
    response_model=PositionCreatedResponse,
    status_code=201,
    summary="Зарегистрировать позицию",
)
async def create_position(
    body: PositionCreateRequest,
    handler: HandlerDep,
) -> PositionCreatedResponse:
    coords = Coordinates(latitude=body.latitude, longitude=body.longitude)
    command = RegisterPositionCommand(coordinates=coords, external_ref=body.external_ref)
    position_id = await handler(command)
    return PositionCreatedResponse(id=position_id)
