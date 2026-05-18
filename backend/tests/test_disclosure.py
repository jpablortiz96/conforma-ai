"""Disclosure Agent tests for D4B."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.disclosure import DisclosureAgent
from app.core.gemini_client import GeminiClientError
from app.db.models import AISystem, Audit


class FakeAsyncSession:
    """Minimal async-session double for Disclosure Agent tests."""

    def __init__(self) -> None:
        self.records: dict[str, list[object]] = {
            "audits": [],
            "ai_systems": [],
            "agent_runs": [],
            "artifacts": [],
            "gaps": [],
        }
        self.commits = 0
        self.rollbacks = 0

    def add(self, instance: object) -> None:
        table_name = getattr(instance.__class__, "__tablename__", None)
        if hasattr(instance, "id") and getattr(instance, "id", None) is None:
            setattr(instance, "id", uuid4())
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            setattr(instance, "created_at", datetime.now(timezone.utc))
        if table_name in self.records and instance not in self.records[table_name]:
            self.records[table_name].append(instance)

    def add_all(self, instances: list[object]) -> None:
        for instance in instances:
            self.add(instance)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, instance: object) -> None:
        return None

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def get(self, model: type[object], record_id) -> object | None:
        table_name = getattr(model, "__tablename__", "")
        for instance in self.records.get(table_name, []):
            if getattr(instance, "id", None) == record_id:
                return instance
        return None


@pytest.mark.asyncio
async def test_disclosure_agent_returns_not_required_when_trigger_is_false() -> None:
    """The Disclosure Agent should not fabricate notices when Article 50 does not apply."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/example/recruitment",
        source_type="github_repo",
        status="completed",
    )
    fake_db.add(audit)
    ai_system = AISystem(
        audit_id=audit.id,
        name="resume_screening_model",
        description="Resume screening model for recruitment.",
        source_files=["README.md"],
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        deadline="2 December 2027",
        deadline_iso=date(2027, 12, 2),
        confidence=0.94,
        triggers_article_50=False,
    )
    fake_db.add(ai_system)

    agent = DisclosureAgent(fake_db)
    result = await agent.run(
        {
            "ai_system_id": ai_system.id,
            "system_name": ai_system.name,
            "description": ai_system.description,
            "risk_class": ai_system.risk_class,
            "primary_article": ai_system.primary_article,
            "triggers_article_50": False,
        },
        audit.id,
    )

    assert result["requires_disclosure"] is False
    assert result["article"] is None
    assert result["notices"] is None
    assert len(fake_db.records["artifacts"]) == 0
    assert len(fake_db.records["agent_runs"]) == 1


@pytest.mark.asyncio
async def test_disclosure_agent_fallback_generates_multilingual_notices_and_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fallback disclosure generation should still produce 5-language notices and persist a JSON artifact."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/karpathy/llm.c",
        source_type="github_repo",
        status="completed",
    )
    fake_db.add(audit)
    ai_system = AISystem(
        audit_id=audit.id,
        name="language_model_training_and_inference",
        description="Language model training and inference system with generation logic.",
        source_files=["train_gpt2.py"],
        risk_class="LIMITED_RISK",
        primary_article="Article 50(2)",
        deadline="2 December 2026",
        deadline_iso=date(2026, 12, 2),
        confidence=0.88,
        triggers_article_50=True,
    )
    fake_db.add(ai_system)

    monkeypatch.setattr("app.agents.disclosure.get_settings", lambda: SimpleNamespace(gemini_api_key="test-key"))

    async def failing_call_flash_json(prompt: str, temperature: float = 0.1) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.agents.disclosure.call_flash_json", failing_call_flash_json)

    agent = DisclosureAgent(fake_db)
    result = await agent.run(
        {
            "ai_system_id": ai_system.id,
            "system_name": ai_system.name,
            "description": ai_system.description,
            "risk_class": ai_system.risk_class,
            "primary_article": ai_system.primary_article,
            "triggers_article_50": True,
        },
        audit.id,
    )

    assert result["requires_disclosure"] is True
    assert result["article"] == "Article 50(2)"
    assert set(result["notices"]) == {"en", "it", "es", "fr", "de"}
    assert len(result["placement_recommendations"]) >= 2
    assert len(fake_db.records["artifacts"]) == 1
    assert fake_db.records["artifacts"][0].kind == "article_50_notice_json"
    assert len(fake_db.records["agent_runs"]) == 1
