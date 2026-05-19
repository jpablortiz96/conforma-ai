"""Compliance-pack endpoint tests for D4B."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import AISystem, Artifact, Audit
from app.db.session import get_db
from app.main import app


class FakeAsyncSession:
    """Minimal async-session double for compliance-pack route tests."""

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

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def get(self, model: type[object], record_id) -> object | None:
        table_name = getattr(model, "__tablename__", "")
        for instance in self.records.get(table_name, []):
            if getattr(instance, "id", None) == record_id:
                return instance
        return None

    async def flush(self) -> None:
        return None


def test_compliance_pack_for_resume_screening_uses_existing_annex_iv_and_returns_gaps() -> None:
    """High-risk systems with Annex IV artifacts should surface documentation gaps and no disclosures."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/anukalp-mishra/Resume-Screening",
        source_type="github_repo",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(audit)
    ai_system = AISystem(
        audit_id=audit.id,
        name="resume_screening_model",
        description="Resume screening model for recruitment.",
        source_files=["README.md", "Resume_Screening.ipynb"],
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        secondary_articles=[],
        reasoning="High-risk recruitment screening.",
        deadline="2 December 2027 for Annex III high-risk systems.",
        deadline_iso=date(2027, 12, 2),
        confidence=0.94,
        triggers_article_50=False,
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(ai_system)
    fake_db.add(
        Artifact(
            audit_id=audit.id,
            ai_system_id=ai_system.id,
            kind="annex_iv_pdf",
            language="en",
            storage_url="D:/tmp/annex_iv.pdf",
            content=json.dumps(
                {
                    "system_name": "resume_screening_model",
                    "gaps_identified": [
                        "Human oversight procedures are not documented in the repository.",
                        "Dataset provenance and quality controls are not documented in the repository.",
                        "The Article 9 risk-management process is not documented in the repository.",
                        "Post-market monitoring procedures are not documented in the repository.",
                    ],
                }
            ),
            created_at=datetime.now(timezone.utc),
        )
    )

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/audits/{audit.id}/compliance-pack")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit_id"] == str(audit.id)
    assert payload["compliance_score"] == 71
    assert payload["systems_count"] == 1
    assert payload["high_risk_count"] == 1
    assert payload["article_50_count"] == 0
    assert payload["disclosures"] == []
    assert payload["gaps"]
    assert not any(
        gap["title"] == "Annex IV technical documentation is missing" for gap in payload["gaps"]
    )
    assert len(fake_db.records["gaps"]) == len(payload["gaps"])
    assert len(fake_db.records["agent_runs"]) == 1


def test_compliance_pack_for_llmc_generates_disclosures_in_five_languages() -> None:
    """Generative systems should receive Article 50 notices through the compliance pack."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/karpathy/llm.c",
        source_type="github_repo",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(audit)
    ai_system = AISystem(
        audit_id=audit.id,
        name="language_model_training_and_inference",
        description="Language model training and inference system with generation logic.",
        source_files=["train_gpt2.py"],
        risk_class="LIMITED_RISK",
        primary_article="Article 50(2)",
        secondary_articles=[],
        reasoning="Generative model for synthetic text outputs.",
        deadline="2 December 2026 for Article 50 transparency obligations.",
        deadline_iso=date(2026, 12, 2),
        confidence=0.88,
        triggers_article_50=True,
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(ai_system)

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(f"/api/v1/audits/{audit.id}/compliance-pack")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["article_50_count"] == 1
    assert len(payload["disclosures"]) == 1
    disclosure = payload["disclosures"][0]
    assert disclosure["requires_disclosure"] is True
    assert disclosure["article"] == "Article 50(2)"
    assert set(disclosure["notices"]) == {"en", "it", "es", "fr", "de"}
    assert all(key in disclosure["notices"] for key in ("en", "it", "es", "fr", "de"))
    assert not any(gap["title"] == "Article 50 disclosure is missing" for gap in payload["gaps"])
    assert len(fake_db.records["artifacts"]) == 1
    assert fake_db.records["artifacts"][0].kind == "article_50_notice_json"
    assert len(fake_db.records["agent_runs"]) == 2
