"""Monitor Agent tests for D5."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.monitor import MonitorAgent
from app.db.models import Audit


class FakeAsyncSession:
    """Minimal async-session double for Monitor Agent tests."""

    def __init__(self) -> None:
        self.records: dict[str, list[object]] = {
            "audits": [],
            "ai_systems": [],
            "agent_runs": [],
            "artifacts": [],
            "gaps": [],
        }

    def add(self, instance: object) -> None:
        table_name = getattr(instance.__class__, "__tablename__", None)
        if hasattr(instance, "id") and getattr(instance, "id", None) is None:
            setattr(instance, "id", uuid4())
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            setattr(instance, "created_at", datetime.now(timezone.utc))
        if table_name in self.records and instance not in self.records[table_name]:
            self.records[table_name].append(instance)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def get(self, model: type[object], record_id) -> object | None:
        table_name = getattr(model, "__tablename__", "")
        for instance in self.records.get(table_name, []):
            if getattr(instance, "id", None) == record_id:
                return instance
        return None


@pytest.mark.asyncio
async def test_monitor_agent_generates_deadline_and_control_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Monitor Agent should produce deadline, roadmap, drift, and control alerts."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/karpathy/llm.c",
        source_type="github_repo",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(audit)

    monkeypatch.setattr(
        "app.agents.monitor.get_settings",
        lambda: SimpleNamespace(gemini_api_key=""),
    )

    today = date.today()
    agent = MonitorAgent(fake_db)
    result = await agent.run(
        {
            "systems": [
                {
                    "id": str(uuid4()),
                    "name": "language_model_training_and_inference",
                    "risk_class": "LIMITED_RISK",
                    "primary_article": "Article 50(2)",
                    "deadline_iso": (today + timedelta(days=25)).isoformat(),
                },
                {
                    "id": str(uuid4()),
                    "name": "resume_screening_model",
                    "risk_class": "HIGH_RISK",
                    "primary_article": "Annex III Section 4(a)",
                    "deadline_iso": (today + timedelta(days=75)).isoformat(),
                },
            ],
            "gaps": [
                {
                    "severity": "HIGH",
                    "title": "Annex IV technical documentation is missing",
                    "description": "No Annex IV artifact exists for the high-risk system.",
                    "affected_system_id": str(uuid4()),
                    "recommended_action": "Generate Annex IV documentation.",
                    "legal_reference": "Article 11 and Annex IV",
                }
            ],
            "artifacts": [],
        },
        audit.id,
    )

    assert result["audit_id"] == str(audit.id)
    assert result["alerts"]
    assert {alert["type"] for alert in result["alerts"]} >= {
        "DEADLINE_APPROACH",
        "REGULATORY_UPDATE",
        "DRIFT_SIMULATION",
        "MISSING_CONTROL",
    }
    assert any(alert["severity"] == "CRITICAL" for alert in result["alerts"])
    assert any(alert["severity"] == "WARNING" for alert in result["alerts"])
    assert any(alert["severity"] == "INFO" for alert in result["alerts"])
    assert result["next_check_at"] > datetime.now(timezone.utc).isoformat()
    assert len(fake_db.records["agent_runs"]) == 1
