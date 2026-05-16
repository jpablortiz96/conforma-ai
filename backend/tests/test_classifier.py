"""Classifier agent tests."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.agents.classifier import ClassifierAgent, classify_with_fallback
from app.core.gemini_client import GeminiClientError
from app.db.models import AISystem


class FakeAsyncSession:
    """Minimal async-session double for classifier tests."""

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


@pytest.mark.parametrize(
    ("description", "risk_class", "primary_article", "article_50", "omnibus_required"),
    [
        ("CV ranking for recruitment at a bank", "HIGH_RISK", "Annex III Section 4(a)", False, True),
        ("Customer service chatbot for password reset", "LIMITED_RISK", "Article 50(1)", True, False),
        ("Social credit scoring by Dutch municipality", "UNACCEPTABLE", "Article 5(1)(c)", False, False),
        ("Email spam classifier", "MINIMAL_RISK", "Not applicable", False, False),
        ("AI evaluating insurance premiums for life insurance", "HIGH_RISK", "Annex III Section 5(c)", False, True),
        ("Deep fake video generator marketed to consumers", "LIMITED_RISK", "Article 50(4)", True, False),
        ("Facial recognition for shoplifter detection in supermarkets private", "HIGH_RISK", "Annex III Section 1", False, True),
        ("Real-time biometric ID in public squares for police", "UNACCEPTABLE", "Article 5(1)(h)", False, False),
        ("Predictive maintenance for industrial machinery", "MINIMAL_RISK", "Not applicable", False, False),
        ("Resume scoring AI that also generates explanations", "HIGH_RISK", "Annex III Section 4(a)", True, True),
    ],
)
def test_classifier_fallback_covers_all_required_d3_cases(
    description: str,
    risk_class: str,
    primary_article: str,
    article_50: bool,
    omnibus_required: bool,
) -> None:
    """The deterministic classifier fallback should cover the mandatory D3 edge cases."""

    response = classify_with_fallback(description)

    assert response.risk_class == risk_class
    assert response.primary_article == primary_article
    assert response.triggers_article_50 is article_50
    assert "Section" in response.primary_article or response.primary_article.startswith("Article") or response.primary_article == "Not applicable"
    if omnibus_required:
        assert "Digital Omnibus deal of 7 May 2026" in response.reasoning
    if description == "Resume scoring AI that also generates explanations":
        assert "Article 50(2)" in response.secondary_articles


@pytest.mark.asyncio
async def test_classifier_agent_updates_ai_system_and_persists_agent_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ClassifierAgent should persist classifier output back onto the AI system row."""

    fake_db = FakeAsyncSession()
    audit_id = uuid4()
    ai_system = AISystem(
        audit_id=audit_id,
        name="resume_scorer",
        description="Resume scoring AI that also generates explanations.",
        source_files=["models/resume_ranker.py"],
    )
    fake_db.add(ai_system)

    async def failing_call_pro_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.agents.classifier.call_pro_json", failing_call_pro_json)

    agent = ClassifierAgent(fake_db)
    result = await agent.run(
        {
            "ai_system_id": ai_system.id,
            "system_description": "Resume scoring AI that also generates explanations",
            "context_files": ["models/resume_ranker.py", "README mentions candidate ranking"],
        },
        audit_id=audit_id,
    )

    assert result["risk_class"] == "HIGH_RISK"
    assert result["primary_article"] == "Annex III Section 4(a)"
    assert result["triggers_article_50"] is True
    assert ai_system.risk_class == "HIGH_RISK"
    assert ai_system.primary_article == "Annex III Section 4(a)"
    assert ai_system.secondary_articles == ["Article 50(2)"]
    assert ai_system.deadline_iso is not None
    assert ai_system.triggers_article_50 is True
    assert len(fake_db.records["agent_runs"]) == 1
