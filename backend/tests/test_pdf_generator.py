"""PDF generator tests for D4A."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.schemas.agent import AnnexIVDocument
from app.services import pdf_generator


def _build_document() -> AnnexIVDocument:
    return AnnexIVDocument(
        system_name="bank_cv_ranking_system",
        section_1_general_description="General description text for the system and its operating context.",
        section_2_intended_purpose="Intended purpose text covering users, affected persons, and misuse boundaries.",
        section_3_human_oversight_measures="Human oversight measures describing operator review and escalation controls.",
        section_4_input_data_specs="Input data specifications covering provenance, labeling, and cleaning assumptions.",
        section_5_design_specifications="Design specifications documenting architecture and key model choices.",
        section_6_risk_management_system="Risk management text covering risk identification, evaluation, and controls.",
        section_7_validation_testing="Validation and testing text covering methodology, datasets, and bias evaluation.",
        section_8_performance_metrics="Performance metrics text covering accuracy, robustness, and cybersecurity.",
        section_9_post_market_monitoring="Post-market monitoring text covering incident review and risk reassessment.",
        gaps_identified=["Provider version information is not documented in the repository."],
        confidence=0.91,
    )


def test_render_annex_iv_html_contains_required_sections() -> None:
    """Rendered Annex IV HTML should include all required content blocks."""

    html = pdf_generator.render_annex_iv_html(
        audit_id=uuid4(),
        ai_system_id=uuid4(),
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        document=_build_document(),
        repo_metadata={
            "repo_url": "https://github.com/example/repo",
            "source_files": ["src/recruitment/ranker.py"],
            "detection_signals": ["README mentions candidate ranking"],
        },
        generated_at=datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc),
    )

    assert "Annex IV Technical Documentation" in html
    assert "Audit ID" in html
    assert "AI System ID" in html
    assert "Section 9 — Post-Market Monitoring" in html
    assert "Appendix A — Gaps Identified" in html
    assert "Appendix B — References" in html
    assert "Regulation EU 2024/1689" in html
    assert "{{" not in html
    assert "{%" not in html


def test_generate_annex_iv_pdf_writes_expected_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    """PDF generation should write the canonical Annex IV file to disk."""

    class FakeHTML:
        def __init__(self, *, string: str, base_url: str) -> None:
            self.string = string
            self.base_url = base_url

        def write_pdf(self, target: str) -> None:
            Path(target).write_bytes(b"%PDF-1.4\n%fake-annex-iv\n")

    monkeypatch.setattr(pdf_generator, "GENERATED_ARTIFACTS_DIR", tmp_path)
    monkeypatch.setattr(pdf_generator, "HTML", FakeHTML)

    audit_id = uuid4()
    ai_system_id = uuid4()
    result = pdf_generator.generate_annex_iv_pdf(
        audit_id=audit_id,
        ai_system_id=ai_system_id,
        risk_class="HIGH_RISK",
        primary_article="Annex III Section 4(a)",
        document=_build_document(),
        repo_metadata={
            "repo_url": "https://github.com/example/repo",
            "source_files": ["src/recruitment/ranker.py"],
            "detection_signals": ["README mentions candidate ranking"],
        },
        generated_at=datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc),
    )

    assert result.file_name == "annex_iv.pdf"
    assert result.file_path == tmp_path / str(audit_id) / str(ai_system_id) / "annex_iv.pdf"
    assert result.file_path.exists()
    assert result.file_path.read_bytes().startswith(b"%PDF-1.4")
    assert result.storage_url == str(result.file_path)
    assert result.size_bytes > 0
