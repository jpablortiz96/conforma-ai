"""Synchronous audit flow tests for D3."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.gemini_client import GeminiClientError
from app.db.models import AISystem
from app.db.session import get_db
from app.main import app


class FakeAsyncSession:
    """Minimal async-session double for audit flow tests."""

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


def test_audit_flow_runs_scanner_then_classifier_and_returns_portfolio_index(
    monkeypatch,
) -> None:
    """POST /api/v1/audits should chain scanner plus classifier and return a completed audit."""

    fake_db = FakeAsyncSession()

    async def override_get_db():
        yield fake_db

    async def fake_scanner_run(self, input_data, audit_id):
        systems = [
            AISystem(
                audit_id=audit_id,
                name="resume_scorer",
                description="Resume scoring AI that also generates explanations.",
                source_files=["models/resume_ranker.py"],
            ),
            AISystem(
                audit_id=audit_id,
                name="spam_classifier",
                description="Email spam classifier for inbox filtering.",
                source_files=["models/spam_filter.py"],
            ),
        ]
        self.db.add_all(systems)
        await self.db.flush()
        return {
            "audit_id": audit_id,
            "repo_url": input_data["repo_url"],
            "files_inspected": 12,
            "ai_systems_found": [
                {
                    "id": systems[0].id,
                    "name": systems[0].name,
                    "description": systems[0].description,
                    "source_files": systems[0].source_files,
                    "detection_signals": [
                        "dependency signal: requirements.txt references transformers",
                        "README signal: README mentions candidate ranking",
                    ],
                },
                {
                    "id": systems[1].id,
                    "name": systems[1].name,
                    "description": systems[1].description,
                    "source_files": systems[1].source_files,
                    "detection_signals": [
                        "file signal: models/spam_filter.py matched *model*.py",
                    ],
                },
            ],
            "summary": "Two AI system candidates detected.",
            "mode": "gemini",
        }

    async def failing_call_pro_json(prompt: str, temperature: float = 0.0) -> dict[str, object]:
        raise GeminiClientError("forced fallback")

    monkeypatch.setattr("app.routers.audits.ScannerAgent.run", fake_scanner_run)
    monkeypatch.setattr("app.agents.classifier.call_pro_json", failing_call_pro_json)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/audits",
                json={"repo_url": "https://github.com/karpathy/llm.c", "max_files_to_inspect": 50},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["repo_url"] == "https://github.com/karpathy/llm.c"
    assert payload["audit_id"]
    assert payload["portfolio_risk_index"] == 44
    assert len(payload["systems"]) == 2
    assert payload["systems"][0]["risk_class"] == "HIGH_RISK"
    assert payload["systems"][0]["triggers_article_50"] is True
    assert payload["systems"][1]["risk_class"] == "MINIMAL_RISK"
    assert len(fake_db.records["audits"]) == 1
    assert len(fake_db.records["ai_systems"]) == 2
    assert len(fake_db.records["agent_runs"]) == 2
    audit = fake_db.records["audits"][0]
    assert audit.status == "completed"
    assert audit.risk_index == "MEDIUM"
