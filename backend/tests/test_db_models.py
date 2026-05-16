"""Database model tests."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect

from app.db.models import Base


def test_initial_metadata_exposes_the_expected_five_tables() -> None:
    """The ORM metadata should define exactly the five D2 tables."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    assert set(inspector.get_table_names()) == {
        "agent_runs",
        "ai_systems",
        "artifacts",
        "audits",
        "gaps",
    }


def test_indexes_exist_for_audit_foreign_keys() -> None:
    """Child tables should expose audit_id indexes required by the handoff."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    assert any(index["name"] == "ix_ai_systems_audit_id" for index in inspector.get_indexes("ai_systems"))
    assert any(index["name"] == "ix_agent_runs_audit_id" for index in inspector.get_indexes("agent_runs"))
    assert any(index["name"] == "ix_artifacts_audit_id" for index in inspector.get_indexes("artifacts"))
    assert any(index["name"] == "ix_gaps_audit_id" for index in inspector.get_indexes("gaps"))
