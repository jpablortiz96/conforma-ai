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
    (
        "description",
        "risk_class",
        "primary_article",
        "article_50",
        "deadline_iso",
        "omnibus_required",
    ),
    [
        (
            "resume screening model for recruitment",
            "HIGH_RISK",
            "Annex III Section 4(a)",
            False,
            "2027-12-02",
            True,
        ),
        (
            "CV ranking for recruitment at a bank",
            "HIGH_RISK",
            "Annex III Section 4(a)",
            False,
            "2027-12-02",
            True,
        ),
        (
            "Customer service chatbot for password reset",
            "LIMITED_RISK",
            "Article 50(1)",
            True,
            "2026-12-02",
            False,
        ),
        (
            "Social credit scoring by Dutch municipality",
            "UNACCEPTABLE",
            "Article 5(1)(c)",
            False,
            "2025-02-02",
            False,
        ),
        ("Email spam classifier", "MINIMAL_RISK", "Not applicable", False, None, False),
        (
            "AI evaluating insurance premiums for life insurance",
            "HIGH_RISK",
            "Annex III Section 5(c)",
            False,
            "2027-12-02",
            True,
        ),
        (
            "Deep fake video generator marketed to consumers",
            "LIMITED_RISK",
            "Article 50(4)",
            True,
            "2026-12-02",
            False,
        ),
        (
            "Facial recognition for shoplifter detection in supermarkets private",
            "HIGH_RISK",
            "Annex III Section 1",
            False,
            "2027-12-02",
            True,
        ),
        (
            "Real-time biometric ID in public squares for police",
            "UNACCEPTABLE",
            "Article 5(1)(h)",
            False,
            "2025-02-02",
            False,
        ),
        (
            "Predictive maintenance for industrial machinery",
            "MINIMAL_RISK",
            "Not applicable",
            False,
            None,
            False,
        ),
        (
            "Resume scoring AI that also generates explanations",
            "HIGH_RISK",
            "Annex III Section 4(a)",
            True,
            "2027-12-02",
            True,
        ),
        (
            "AI safety component in a medical device",
            "HIGH_RISK",
            "Annex I",
            False,
            "2028-08-02",
            False,
        ),
    ],
)
def test_classifier_fallback_covers_all_required_d3_cases(
    description: str,
    risk_class: str,
    primary_article: str,
    article_50: bool,
    deadline_iso: str | None,
    omnibus_required: bool,
) -> None:
    """The deterministic classifier fallback should cover the mandatory D3 edge cases."""

    response = classify_with_fallback(description)

    assert response.risk_class == risk_class
    assert response.primary_article == primary_article
    assert response.triggers_article_50 is article_50
    assert (
        response.deadline_iso.isoformat() if response.deadline_iso is not None else None
    ) == deadline_iso
    assert (
        "Section" in response.primary_article
        or response.primary_article.startswith("Article")
        or response.primary_article == "Annex I"
        or response.primary_article == "Not applicable"
    )
    if omnibus_required:
        assert "Digital Omnibus deal of 7 May 2026" in response.reasoning
    if description == "Resume scoring AI that also generates explanations":
        assert "Article 50(2)" in response.secondary_articles


def test_classifier_fallback_generative_guardrail_does_not_append_minimal_risk_reasoning() -> None:
    """Article 50 guardrails should replace contradictory minimal-risk fallback language."""

    response = classify_with_fallback("Language model training and inference system for synthetic text generation")

    assert response.risk_class == "LIMITED_RISK"
    assert response.primary_article == "Article 50(2)"
    assert response.triggers_article_50 is True
    assert response.deadline_iso is not None
    assert response.deadline_iso.isoformat() == "2026-12-02"
    assert "does not clearly map to a prohibited practice" not in response.reasoning
    assert "smallest solid classification is minimal risk" not in response.reasoning.lower()


def test_classifier_guardrail_ignores_repo_url_only_recruitment_signal_for_generative_system() -> None:
    """Repo-level recruitment keywords must not override system-specific generative evidence."""

    response = classify_with_fallback(
        "\n".join(
            [
                "AI system name: language_model_training_and_inference",
                "Repository URL: https://github.com/anukalp-mishra/Resume-Screening",
                "Description: Language model inference system for synthetic text generation.",
                "Source files: train_gpt2.py",
                "Detection signals: file signal: train_gpt2.py matched *train*.py; dependency signal: train_gpt2.py imports torch",
            ]
        )
    )

    assert response.risk_class == "LIMITED_RISK"
    assert response.primary_article == "Article 50(2)"
    assert response.deadline_iso is not None
    assert response.deadline_iso.isoformat() == "2026-12-02"


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
    assert ai_system.deadline_iso.isoformat() == "2027-12-02"
    assert ai_system.triggers_article_50 is True
    assert len(fake_db.records["agent_runs"]) == 1
