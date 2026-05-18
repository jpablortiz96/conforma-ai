"""Gap Auditor tests for D4B."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.agents.gap_auditor import GapAuditorAgent


class FakeAsyncSession:
    """Minimal async-session double for Gap Auditor tests."""

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
        if table_name in self.records and instance not in self.records[table_name]:
            self.records[table_name].append(instance)

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_gap_auditor_computes_deterministic_score_and_gaps() -> None:
    """The Gap Auditor should apply the published deterministic scoring model."""

    audit_id = uuid4()
    fake_db = FakeAsyncSession()
    agent = GapAuditorAgent(fake_db)

    result = await agent.run(
        {
            "audit_id": audit_id,
            "systems": [
                {
                    "id": str(uuid4()),
                    "name": "resume_screening_model",
                    "description": "Resume screening model for recruitment.",
                    "risk_class": "HIGH_RISK",
                    "primary_article": "Annex III Section 4(a)",
                    "secondary_articles": [],
                    "deadline": "2 December 2027 for Annex III high-risk systems.",
                    "deadline_iso": "2027-12-02",
                    "triggers_article_50": False,
                },
                {
                    "id": str(uuid4()),
                    "name": "language_model_training_and_inference",
                    "description": "Language model inference system for text generation.",
                    "risk_class": "LIMITED_RISK",
                    "primary_article": "Article 50(2)",
                    "secondary_articles": [],
                    "deadline": "2 December 2026 for Article 50 transparency obligations.",
                    "deadline_iso": "2026-12-02",
                    "triggers_article_50": True,
                },
            ],
            "artifacts": [],
            "disclosures": [],
        },
        audit_id,
    )

    assert result["compliance_score"] == 45
    assert result["estimated_fine_exposure_eur"] == 1_120_000
    assert result["time_to_compliant_days"] >= 0
    assert len(result["gaps"]) >= 3
    assert any(gap["title"] == "Annex IV technical documentation is missing" for gap in result["gaps"])
    assert any(gap["title"] == "Article 50 disclosure is missing" for gap in result["gaps"])
    assert result["priority_actions"]
    assert len(fake_db.records["agent_runs"]) == 1
