from __future__ import annotations

import json
from typing import Any

from aiokafka import AIOKafkaProducer

from positions_service.domain.events import PositionRecorded


class KafkaPositionEventPublisher:
    def __init__(self, producer: AIOKafkaProducer, topic: str) -> None:
        self._producer = producer
        self._topic = topic

    async def publish_position_recorded(self, events: tuple[PositionRecorded, ...]) -> None:
        for event in events:
            payload: dict[str, Any] = {
                "event_type": "PositionRecorded",
                "position_id": str(event.position_id),
                "latitude": event.latitude,
                "longitude": event.longitude,
                "recorded_at": event.recorded_at.isoformat(),
                "external_ref": event.external_ref,
            }
            await self._producer.send_and_wait(  # type: ignore[union-attr]  # aiokafka missing stubs
                self._topic,
                json.dumps(payload).encode("utf-8"),
            )
