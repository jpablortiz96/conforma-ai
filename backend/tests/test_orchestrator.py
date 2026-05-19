"""D5 orchestrator and SSE event tests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.orchestrator import AuditOrchestrator
from app.db.models import AISystem, Artifact, Audit
from app.schemas.audit import AuditCreateRequest
from app.services.audit_events import AUDIT_EVENT_BROKER
from app.services.pdf_generator import GeneratedPdfArtifact


class FakeAsyncSession:
    """Minimal async-session double for orchestrator tests."""

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
async def test_orchestrator_runs_full_pipeline_and_emits_stream_events(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The orchestrator should complete scanner, classifier, docs, disclosure, gap, and monitor steps."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="https://github.com/anukalp-mishra/Resume-Screening",
        source_type="github_repo",
        status="running",
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(audit)

    async def fake_scanner_run(self, input_data, audit_id):
        systems = [
            AISystem(
                audit_id=audit_id,
                name="resume_screening_model",
                description=(
                    "Resume screening model for recruitment that ranks applicants using CV content, "
                    "skills, and project experience."
                ),
                source_files=["README.md", "Resume_Screening.ipynb"],
            ),
            AISystem(
                audit_id=audit_id,
                name="language_model_training_and_inference",
                description="Language model inference system for synthetic text generation.",
                source_files=["train_gpt2.py"],
            ),
        ]
        self.db.add_all(systems)
        await self.db.flush()
        return {
            "audit_id": audit_id,
            "repo_url": input_data["repo_url"],
            "files_inspected": 15,
            "ai_systems_found": [
                {
                    "id": systems[0].id,
                    "name": systems[0].name,
                    "description": systems[0].description,
                    "source_files": systems[0].source_files,
                    "detection_signals": [
                        "repository signal: repository name contains Resume-Screening",
                        "README signal: README.md mentions machine learning",
                        "domain signal: README.md mentions recruitment or hiring workflows",
                    ],
                },
                {
                    "id": systems[1].id,
                    "name": systems[1].name,
                    "description": systems[1].description,
                    "source_files": systems[1].source_files,
                    "detection_signals": [
                        "file signal: train_gpt2.py matched *train*.py",
                        "dependency signal: train_gpt2.py imports torch",
                    ],
                },
            ],
            "summary": "Two AI system candidates detected.",
            "mode": "fallback",
        }

    def fake_get_settings():
        return SimpleNamespace(gemini_api_key="")

    def fake_generate_annex_iv_pdf(**kwargs) -> GeneratedPdfArtifact:
        output_path = tmp_path / str(kwargs["audit_id"]) / str(kwargs["ai_system_id"]) / "annex_iv.pdf"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"%PDF-1.4\n%d5-demo\n")
        return GeneratedPdfArtifact(
            file_path=output_path,
            file_name=output_path.name,
            storage_url=str(output_path),
            size_bytes=output_path.stat().st_size,
            generated_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr("app.agents.orchestrator.ScannerAgent.run", fake_scanner_run)
    monkeypatch.setattr("app.agents.classifier.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.documentation.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.disclosure.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.gap_auditor.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.monitor.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.documentation.generate_annex_iv_pdf", fake_generate_annex_iv_pdf)

    orchestrator = AuditOrchestrator(fake_db)
    result = await orchestrator.execute(
        AuditCreateRequest(
            repo_url="https://github.com/anukalp-mishra/Resume-Screening",
            max_files_to_inspect=80,
        ),
        audit.id,
    )

    assert result.status == "completed"
    assert result.portfolio_risk_index >= 50
    assert len(result.systems) == 2
    assert result.systems[0].name == "resume_screening_model"
    assert result.systems[0].risk_class == "HIGH_RISK"
    assert result.systems[0].primary_article == "Annex III Section 4(a)"
    assert result.systems[1].risk_class == "LIMITED_RISK"
    assert result.systems[1].primary_article == "Article 50(2)"
    assert result.compliance_pack.compliance_score <= 100
    assert result.monitor.alerts
    assert result.executive_summary.regulatory_timeline
    assert result.evidence_vault.systems
    assert any(artifact.kind == "annex_iv_pdf" for artifact in fake_db.records["artifacts"])
    assert any(artifact.kind == "article_50_notice_json" for artifact in fake_db.records["artifacts"])

    history = AUDIT_EVENT_BROKER.snapshot(audit.id)
    event_names = [str(event.payload.get("event")) for event in history]
    assert event_names == [
        "audit_started",
        "scanner_started",
        "scanner_completed",
        "classifier_started",
        "classifier_completed",
        "documentation_started",
        "documentation_completed",
        "disclosure_started",
        "disclosure_completed",
        "gap_auditor_started",
        "gap_auditor_completed",
        "monitor_started",
        "monitor_completed",
        "audit_completed",
    ]
