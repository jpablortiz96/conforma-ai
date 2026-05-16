"""Documentation Agent and artifact route tests for D4A."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import AISystem, Artifact, Audit
from app.db.session import get_db
from app.main import app
from app.services.pdf_generator import GeneratedPdfArtifact


class FakeAsyncSession:
    """Minimal async-session double for Documentation Agent tests."""

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


def _build_high_risk_request_payload(audit_id: str, ai_system_id: str) -> dict[str, object]:
    return {
        "audit_id": audit_id,
        "ai_system_id": ai_system_id,
        "system_description": (
            "AI system that ranks CVs for recruitment in a bank using education, employment "
            "history, skills and interview notes."
        ),
        "risk_class": "HIGH_RISK",
        "primary_article": "Annex III Section 4(a)",
        "source_code_snippets": [
            "src/recruitment/ranker.py: rank_candidate(profile, interview_notes, skill_vector)",
            "README.md: model ranks candidates for recruiter review",
        ],
        "repo_metadata": {
            "repo_url": "https://github.com/demo/bank-cv-ranking-system",
            "source_files": ["src/recruitment/ranker.py", "README.md"],
            "detection_signals": [
                "README mentions candidate ranking",
                "ranker.py evaluates applicants for recruiter review",
            ],
        },
    }


def test_demo_high_risk_system_route_creates_seed_records() -> None:
    """The D4A demo helper should create a completed audit plus one high-risk AI system."""

    fake_db = FakeAsyncSession()

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/demo/high-risk-system")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit_id"]
    assert payload["ai_system_id"]
    assert len(fake_db.records["audits"]) == 1
    assert len(fake_db.records["ai_systems"]) == 1
    ai_system = fake_db.records["ai_systems"][0]
    assert ai_system.name == "bank_cv_ranking_system"
    assert ai_system.risk_class == "HIGH_RISK"
    assert ai_system.primary_article == "Annex III Section 4(a)"
    assert ai_system.deadline == "2 December 2027"


def test_documentation_endpoint_generates_artifact_lists_it_and_downloads_it(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """High-risk documentation should produce structured Annex IV output and a downloadable PDF."""

    fake_db = FakeAsyncSession()
    generated_pdf_path = tmp_path / "annex_iv.pdf"

    async def override_get_db():
        yield fake_db

    def fake_get_settings():
        return SimpleNamespace(gemini_api_key="test-key")

    async def fake_call_pro_json(prompt: str, temperature: float = 0.1) -> dict[str, object]:
        return {
            "system_name": "bank_cv_ranking_system",
            "section_1_general_description": "This system ranks job applicants for bank recruitment workflows using structured profile evidence and reviewer-supplied interview notes. The repository evidence suggests a provider-side ranking component embedded in a broader recruitment workflow and exposed to human reviewers before downstream hiring decisions.",
            "section_2_intended_purpose": "The intended purpose is to support recruitment teams in triaging candidate applications for banking roles. Intended users are recruiters and hiring managers, while affected natural persons are applicants whose education, work history, skills, and interview notes are assessed. Foreseeable misuse includes treating rankings as final employment decisions without human review.",
            "section_3_human_oversight_measures": "Human oversight should require recruiters to review ranked outputs alongside underlying candidate evidence, challenge anomalous recommendations, and override scores where context warrants. The repository does not fully document reviewer escalation paths, so provider-authored operating procedures are still required.",
            "section_4_input_data_specs": "Inputs appear to include education, employment history, skills, and interview notes. The repository materials do not expose a complete dataset register, provenance chain, labeling specification, or retention schedule, so these details must be documented by the provider before deployment.",
            "section_5_design_specifications": "The available source references indicate a ranking-oriented application architecture with model logic implemented inside a recruitment-specific service boundary. A formal architecture decision record, version-control rationale, and standards mapping are not visible and should be added by the provider.",
            "section_6_risk_management_system": "The provider should document an Article 9 risk-management process covering inaccurate ranking, discriminatory outcomes, data-quality failures, and operational over-reliance. A formal risk register is not visible in the repository evidence supplied to the agent.",
            "section_7_validation_testing": "Validation should cover ranking quality, regression checks, discriminatory-bias evaluation, and release sign-off thresholds. The repository inputs do not provide auditable test datasets or result summaries, so the provider must supply them.",
            "section_8_performance_metrics": "Expected metrics include ranking quality, stability under data drift, robustness to malformed input, and cybersecurity assumptions around sensitive applicant data. Quantified metric evidence is not available in the repository materials supplied here.",
            "section_9_post_market_monitoring": "The provider should define post-market monitoring for incident intake, periodic reassessment, and corrective-action triggers once the system is in service. The repository does not contain a monitoring plan or serious-incident procedure.",
            "gaps_identified": [
                "A formal dataset register and provenance record are not documented in the repository.",
                "Validation datasets and bias testing results are not documented in the repository.",
                "Post-market monitoring procedures are not documented in the repository.",
            ],
            "confidence": 0.84,
        }

    def fake_generate_annex_iv_pdf(**kwargs) -> GeneratedPdfArtifact:
        generated_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        generated_pdf_path.write_bytes(b"%PDF-1.4\n%d4a-demo\n")
        return GeneratedPdfArtifact(
            file_path=generated_pdf_path,
            file_name=generated_pdf_path.name,
            storage_url=str(generated_pdf_path),
            size_bytes=generated_pdf_path.stat().st_size,
            generated_at=datetime.now(timezone.utc),
        )

    monkeypatch.setattr("app.agents.documentation.get_settings", fake_get_settings)
    monkeypatch.setattr("app.agents.documentation.call_pro_json", fake_call_pro_json)
    monkeypatch.setattr("app.agents.documentation.generate_annex_iv_pdf", fake_generate_annex_iv_pdf)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            demo_response = client.post("/api/v1/demo/high-risk-system")
            assert demo_response.status_code == 200
            demo_payload = demo_response.json()

            documentation_response = client.post(
                "/api/v1/agents/documentation",
                json=_build_high_risk_request_payload(
                    demo_payload["audit_id"],
                    demo_payload["ai_system_id"],
                ),
            )
            assert documentation_response.status_code == 200
            documentation_payload = documentation_response.json()

            artifacts_response = client.get(
                f"/api/v1/audits/{demo_payload['audit_id']}/artifacts"
            )
            assert artifacts_response.status_code == 200
            artifacts_payload = artifacts_response.json()

            download_response = client.get(
                documentation_payload["artifact"]["download_url"]
            )
    finally:
        app.dependency_overrides.clear()

    assert documentation_payload["required"] is True
    assert documentation_payload["status"] == "generated"
    assert documentation_payload["mode"] == "gemini"
    assert documentation_payload["system_name"] == "bank_cv_ranking_system"
    assert "section_1_general_description" in documentation_payload
    assert documentation_payload["artifact"]["file_name"] == "annex_iv.pdf"
    assert generated_pdf_path.exists()
    assert len(fake_db.records["agent_runs"]) == 1
    assert len(fake_db.records["artifacts"]) == 1

    assert artifacts_payload["audit_id"] == demo_payload["audit_id"]
    assert len(artifacts_payload["artifacts"]) == 1
    assert artifacts_payload["artifacts"][0]["kind"] == "annex_iv_pdf"
    assert artifacts_payload["artifacts"][0]["artifact_id"] == documentation_payload["artifact"]["artifact_id"]

    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith("application/pdf")
    assert download_response.content.startswith(b"%PDF-1.4")


def test_documentation_endpoint_skips_non_high_risk_systems(monkeypatch) -> None:
    """Non-high-risk systems should not generate fake Annex IV PDFs."""

    fake_db = FakeAsyncSession()
    audit = Audit(
        source_url="demo://minimal-risk-system",
        source_type="demo_seed",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(audit)
    ai_system = AISystem(
        audit_id=audit.id,
        name="spam_classifier",
        description="Email spam classifier for inbox filtering.",
        source_files=["src/spam/filter.py"],
        risk_class="MINIMAL_RISK",
        primary_article="Not applicable",
        deadline="No mandatory deadline for minimal-risk systems.",
        deadline_iso=None,
        confidence=0.96,
        triggers_article_50=False,
        created_at=datetime.now(timezone.utc),
    )
    fake_db.add(ai_system)

    async def override_get_db():
        yield fake_db

    monkeypatch.setattr(
        "app.agents.documentation.get_settings",
        lambda: SimpleNamespace(gemini_api_key="test-key"),
    )
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/agents/documentation",
                json={
                    "audit_id": str(audit.id),
                    "ai_system_id": str(ai_system.id),
                    "system_description": "Email spam classifier for inbox filtering.",
                    "risk_class": "MINIMAL_RISK",
                    "primary_article": "Not applicable",
                    "source_code_snippets": ["src/spam/filter.py"],
                    "repo_metadata": {"repo_url": "https://github.com/example/spam-filter"},
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["required"] is False
    assert payload["status"] == "not_required"
    assert payload["message"] == "Annex IV technical documentation is not required for non-high-risk systems."
    assert payload["artifact"] is None
    assert len(fake_db.records["artifacts"]) == 0
    assert len(fake_db.records["agent_runs"]) == 1
