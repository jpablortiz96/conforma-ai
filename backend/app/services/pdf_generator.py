"""Annex IV PDF generation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import textwrap
from typing import Any
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:  # pragma: no cover - import availability depends on runtime environment
    from weasyprint import HTML
except Exception:  # pragma: no cover - guarded at runtime
    HTML = None  # type: ignore[assignment]

from app.schemas.agent import AnnexIVDocument
from app.knowledge.eu_ai_act_kb import deadline_for_classification

BACKEND_DIR = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = BACKEND_DIR / "app" / "templates" / "annex_iv_document.html"
GENERATED_ARTIFACTS_DIR = BACKEND_DIR / "generated" / "artifacts"


@dataclass(slots=True)
class GeneratedPdfArtifact:
    """Metadata for a generated PDF artifact on local disk."""

    file_path: Path
    file_name: str
    storage_url: str
    size_bytes: int
    generated_at: datetime


def build_artifact_output_path(audit_id: UUID, ai_system_id: UUID) -> Path:
    """Return the canonical D4A local output path for an Annex IV PDF."""

    return GENERATED_ARTIFACTS_DIR / str(audit_id) / str(ai_system_id) / "annex_iv.pdf"


def _build_template_environment() -> Environment:
    """Create a Jinja environment rooted at the backend template directory."""

    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_PATH.parent)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_annex_iv_html(
    *,
    audit_id: UUID,
    ai_system_id: UUID,
    risk_class: str,
    primary_article: str,
    document: AnnexIVDocument,
    repo_metadata: dict[str, Any],
    generated_at: datetime | None = None,
) -> str:
    """Render the Annex IV Jinja2 template into an HTML document string."""

    generated_at = generated_at or datetime.now(timezone.utc)
    environment = _build_template_environment()
    template = environment.get_template(TEMPLATE_PATH.name)
    deadline_text, deadline_iso = deadline_for_classification(
        risk_class,
        triggers_article_50=False,
        primary_article=primary_article,
    )
    deadline_display = _format_deadline_display(deadline_text, deadline_iso)

    references = [
        {"label": "Regulation", "value": "EU 2024/1689"},
        {"label": "Source repository", "value": str(repo_metadata.get("repo_url", "Not provided"))},
        {"label": "Audit ID", "value": str(audit_id)},
        {"label": "AI System ID", "value": str(ai_system_id)},
        {"label": "Deadline", "value": deadline_display},
        {"label": "Generation timestamp", "value": generated_at.isoformat()},
    ]

    source_files = repo_metadata.get("source_files", [])
    if isinstance(source_files, list):
        for source_file in source_files[:10]:
            references.append({"label": "Source file", "value": str(source_file)})

    evidence_trail = repo_metadata.get("detection_signals", [])
    if isinstance(evidence_trail, list):
        for signal in evidence_trail[:8]:
            references.append({"label": "Evidence", "value": str(signal)})

    sections = [
        {"number": "1", "title": "General Description", "body": document.section_1_general_description},
        {"number": "2", "title": "Intended Purpose", "body": document.section_2_intended_purpose},
        {
            "number": "3",
            "title": "Human Oversight Measures",
            "body": document.section_3_human_oversight_measures,
        },
        {"number": "4", "title": "Input Data Specifications", "body": document.section_4_input_data_specs},
        {"number": "5", "title": "Design Specifications", "body": document.section_5_design_specifications},
        {
            "number": "6",
            "title": "Risk Management System",
            "body": document.section_6_risk_management_system,
        },
        {"number": "7", "title": "Validation and Testing", "body": document.section_7_validation_testing},
        {"number": "8", "title": "Performance Metrics", "body": document.section_8_performance_metrics},
        {
            "number": "9",
            "title": "Post-Market Monitoring",
            "body": document.section_9_post_market_monitoring,
        },
    ]

    html = template.render(
        audit_id=str(audit_id),
        ai_system_id=str(ai_system_id),
        system_name=document.system_name,
        risk_class=risk_class,
        primary_article=primary_article,
        deadline_display=deadline_display,
        generated_at_iso=generated_at.isoformat(),
        generated_at_display=generated_at.strftime("%d %B %Y %H:%M UTC"),
        sections=sections,
        gaps_identified=document.gaps_identified,
        references=references,
    )

    if "{{" in html or "{%" in html:
        raise ValueError("Rendered Annex IV HTML still contains unresolved template placeholders.")

    return html


def generate_annex_iv_pdf(
    *,
    audit_id: UUID,
    ai_system_id: UUID,
    risk_class: str,
    primary_article: str,
    document: AnnexIVDocument,
    repo_metadata: dict[str, Any],
    generated_at: datetime | None = None,
) -> GeneratedPdfArtifact:
    """Render and write a premium Annex IV PDF to local storage."""

    generated_at = generated_at or datetime.now(timezone.utc)
    output_path = build_artifact_output_path(audit_id, ai_system_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    html_content = render_annex_iv_html(
        audit_id=audit_id,
        ai_system_id=ai_system_id,
        risk_class=risk_class,
        primary_article=primary_article,
        document=document,
        repo_metadata=repo_metadata,
        generated_at=generated_at,
    )

    if HTML is None:  # pragma: no cover - executed only when native WeasyPrint libs are unavailable
        _write_fallback_pdf(
            output_path=output_path,
            document=document,
            audit_id=audit_id,
            ai_system_id=ai_system_id,
            risk_class=risk_class,
            primary_article=primary_article,
            repo_metadata=repo_metadata,
            generated_at=generated_at,
        )
    else:
        HTML(string=html_content, base_url=str(TEMPLATE_PATH.parent)).write_pdf(str(output_path))

    if not output_path.exists():
        raise RuntimeError("Annex IV PDF generation completed without creating the output file.")

    return GeneratedPdfArtifact(
        file_path=output_path,
        file_name=output_path.name,
        storage_url=str(output_path),
        size_bytes=output_path.stat().st_size,
        generated_at=generated_at,
    )


def _write_fallback_pdf(
    *,
    output_path: Path,
    document: AnnexIVDocument,
    audit_id: UUID,
    ai_system_id: UUID,
    risk_class: str,
    primary_article: str,
    repo_metadata: dict[str, Any],
    generated_at: datetime,
) -> None:
    """Write a simple PDF when WeasyPrint native libraries are unavailable."""

    pages = _build_fallback_pages(
        document=document,
        audit_id=audit_id,
        ai_system_id=ai_system_id,
        risk_class=risk_class,
        primary_article=primary_article,
        repo_metadata=repo_metadata,
        generated_at=generated_at,
    )
    output_path.write_bytes(_build_simple_pdf_bytes(pages))


def _build_fallback_pages(
    *,
    document: AnnexIVDocument,
    audit_id: UUID,
    ai_system_id: UUID,
    risk_class: str,
    primary_article: str,
    repo_metadata: dict[str, Any],
    generated_at: datetime,
) -> list[list[str]]:
    """Build paginated plain-text content for the fallback PDF writer."""

    deadline_text, deadline_iso = deadline_for_classification(
        risk_class,
        triggers_article_50=False,
        primary_article=primary_article,
    )
    deadline_display = _format_deadline_display(deadline_text, deadline_iso)

    section_pairs = [
        ("Section 1 - General Description", document.section_1_general_description),
        ("Section 2 - Intended Purpose", document.section_2_intended_purpose),
        ("Section 3 - Human Oversight Measures", document.section_3_human_oversight_measures),
        ("Section 4 - Input Data Specifications", document.section_4_input_data_specs),
        ("Section 5 - Design Specifications", document.section_5_design_specifications),
        ("Section 6 - Risk Management System", document.section_6_risk_management_system),
        ("Section 7 - Validation and Testing", document.section_7_validation_testing),
        ("Section 8 - Performance Metrics", document.section_8_performance_metrics),
        ("Section 9 - Post-Market Monitoring", document.section_9_post_market_monitoring),
    ]

    lines: list[str] = [
        "Annex IV Technical Documentation",
        document.system_name,
        "",
        f"Audit ID: {audit_id}",
        f"AI System ID: {ai_system_id}",
        f"Risk class: {risk_class}",
        f"Primary article: {primary_article}",
        f"Deadline: {deadline_display}",
        f"Generated at: {generated_at.isoformat()}",
        "",
    ]

    for title, body in section_pairs:
        lines.append(title)
        lines.extend(_wrap_text_block(body))
        lines.append("")

    lines.append("Appendix A - Gaps Identified")
    if document.gaps_identified:
        for gap in document.gaps_identified:
            lines.extend(_wrap_text_block(f"- {gap}"))
    else:
        lines.append("- No explicit gaps were identified.")
    lines.append("")

    lines.append("Appendix B - References")
    references = [
        "Regulation EU 2024/1689",
        f"Source repository: {repo_metadata.get('repo_url', 'Not provided')}",
        f"Audit ID: {audit_id}",
        f"AI System ID: {ai_system_id}",
        f"Generated at: {generated_at.isoformat()}",
        f"Deadline: {deadline_display}",
    ]
    for item in references:
        lines.extend(_wrap_text_block(f"- {item}"))

    page_size = 44
    return [lines[index : index + page_size] for index in range(0, len(lines), page_size)]


def _wrap_text_block(value: str, width: int = 92) -> list[str]:
    """Wrap a long paragraph into PDF-friendly line lengths."""

    cleaned = re.sub(r"\s+", " ", value).strip()
    if not cleaned:
        return [""]
    return textwrap.wrap(cleaned, width=width, break_long_words=False, break_on_hyphens=False)


def _format_deadline_display(deadline_text: str, deadline_iso) -> str:
    """Prefer a clean date label when a machine-readable deadline exists."""

    if deadline_iso is None:
        return deadline_text.rstrip(".")
    return f"{deadline_iso.day} {deadline_iso.strftime('%B %Y')}"


def _escape_pdf_text(value: str) -> str:
    """Escape PDF text operators."""

    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf_bytes(pages: list[list[str]]) -> bytes:
    """Build a minimal multi-page PDF from plain-text lines."""

    objects: dict[int, bytes] = {}
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    page_ids: list[int] = []
    next_object_id = 4
    for page_index, page_lines in enumerate(pages, start=1):
        page_id = next_object_id
        content_id = next_object_id + 1
        page_ids.append(page_id)
        next_object_id += 2

        content_lines = [
            "BT",
            "/F1 11 Tf",
            "72 760 Td",
            "14 TL",
        ]
        for line in page_lines:
            content_lines.append(f"({_escape_pdf_text(line)}) Tj")
            content_lines.append("T*")
        content_lines.append("(Regulation EU 2024/1689) Tj")
        content_lines.append("T*")
        content_lines.append(f"(Page {page_index}) Tj")
        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")
        objects[content_id] = (
            f"<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
            + content_stream
            + b"\nendstream"
        )
        objects[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    pdf_parts = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for object_id in range(1, max(objects) + 1):
        offsets.append(sum(len(part) for part in pdf_parts))
        pdf_parts.append(f"{object_id} 0 obj\n".encode("ascii"))
        pdf_parts.append(objects[object_id])
        pdf_parts.append(b"\nendobj\n")

    xref_offset = sum(len(part) for part in pdf_parts)
    pdf_parts.append(f"xref\n0 {max(objects) + 1}\n".encode("ascii"))
    pdf_parts.append(b"0000000000 65535 f \n")
    for object_id in range(1, max(objects) + 1):
        pdf_parts.append(f"{offsets[object_id]:010d} 00000 n \n".encode("ascii"))
    pdf_parts.append(
        (
            f"trailer\n<< /Size {max(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )
    return b"".join(pdf_parts)
