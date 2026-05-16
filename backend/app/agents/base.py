"""Shared base agent implementation."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentRun

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all Conforma-AI agents."""

    name: str = ""
    model: str = ""
    description: str = ""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @abstractmethod
    async def run(self, input_data: dict[str, Any], audit_id: UUID) -> dict[str, Any]:
        """Execute the agent and return a structured result."""

    def estimate_tokens(self, payload: Any) -> int:
        """Estimate token usage when the SDK does not expose exact counts."""

        if payload is None:
            return 0
        serialized = json.dumps(payload, ensure_ascii=True, default=str)
        return max(1, len(serialized) // 4)

    async def _persist_run(
        self,
        *,
        audit_id: UUID,
        ai_system_id: UUID | None,
        status: str,
        input_data: dict[str, Any] | None,
        output: dict[str, Any] | None,
        tokens_in: int | None,
        tokens_out: int | None,
        started_at: datetime,
        error: str | None = None,
        model: str | None = None,
    ) -> AgentRun:
        """Persist an agent run trace into the database."""

        run = AgentRun(
            audit_id=audit_id,
            ai_system_id=ai_system_id,
            agent_name=self.name,
            status=status,
            input=input_data,
            output=output,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=model or self.model,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            error=error,
        )
        self.db.add(run)
        await self.db.commit()
        return run
