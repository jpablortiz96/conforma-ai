"""In-memory audit event broker for D5 SSE streaming."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.schemas.audit import AuditStreamEvent


@dataclass
class AuditStreamState:
    """Mutable stream state for one audit run."""

    history: list[AuditStreamEvent] = field(default_factory=list)
    subscribers: list[asyncio.Queue[AuditStreamEvent]] = field(default_factory=list)
    completed: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditEventBroker:
    """Simple in-memory fan-out broker for SSE event delivery."""

    def __init__(self) -> None:
        self._streams: dict[str, AuditStreamState] = {}

    def ensure_stream(self, audit_id: UUID | str) -> AuditStreamState:
        """Create or return the stream state for one audit."""

        key = str(audit_id)
        state = self._streams.get(key)
        if state is None:
            state = AuditStreamState()
            self._streams[key] = state
        return state

    def snapshot(self, audit_id: UUID | str) -> list[AuditStreamEvent]:
        """Return the current immutable history snapshot."""

        return list(self.ensure_stream(audit_id).history)

    def is_completed(self, audit_id: UUID | str) -> bool:
        """Return whether the audit stream has emitted a terminal event."""

        return self.ensure_stream(audit_id).completed

    def subscribe(self, audit_id: UUID | str) -> asyncio.Queue[AuditStreamEvent]:
        """Register a subscriber queue for one audit stream."""

        state = self.ensure_stream(audit_id)
        queue: asyncio.Queue[AuditStreamEvent] = asyncio.Queue()
        state.subscribers.append(queue)
        return queue

    def unsubscribe(self, audit_id: UUID | str, queue: asyncio.Queue[AuditStreamEvent]) -> None:
        """Detach a subscriber queue from the audit stream."""

        state = self.ensure_stream(audit_id)
        if queue in state.subscribers:
            state.subscribers.remove(queue)

    async def publish(
        self,
        *,
        audit_id: UUID | str,
        event_name: str,
        agent: str,
        status: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AuditStreamEvent:
        """Publish one event into the audit stream and fan it out to subscribers."""

        event = AuditStreamEvent(
            audit_id=UUID(str(audit_id)) if not isinstance(audit_id, UUID) else audit_id,
            agent=agent,
            status=status,  # type: ignore[arg-type]
            message=message,
            timestamp=datetime.now(timezone.utc),
            payload={"event": event_name, **(payload or {})},
        )
        state = self.ensure_stream(audit_id)
        state.history.append(event)
        state.updated_at = event.timestamp
        if event_name in {"audit_completed", "audit_failed"}:
            state.completed = True

        for queue in list(state.subscribers):
            await queue.put(event)
        return event

    async def wait_for_completion(
        self,
        audit_id: UUID | str,
        *,
        timeout: float = 30.0,
    ) -> bool:
        """Wait until a terminal event is published for one audit stream."""

        if self.is_completed(audit_id):
            return True

        queue = self.subscribe(audit_id)
        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=timeout)
                event_name = str(event.payload.get("event", ""))
                if event_name in {"audit_completed", "audit_failed"}:
                    return True
        except TimeoutError:
            return False
        finally:
            self.unsubscribe(audit_id, queue)


AUDIT_EVENT_BROKER = AuditEventBroker()


def encode_sse(event: AuditStreamEvent) -> str:
    """Serialize one stream event into SSE wire format."""

    event_name = str(event.payload.get("event", "agent_progress"))
    return (
        f"event: {event_name}\n"
        f"data: {event.model_dump_json()}\n\n"
    )
