"""Initial Conforma-AI schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial D2 schema."""

    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("compliance_score", sa.Integer(), nullable=True),
        sa.Column("risk_index", sa.Text(), nullable=True),
        sa.Column("fine_exposure_eur", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "ai_systems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_files", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("risk_class", sa.Text(), nullable=True),
        sa.Column("primary_article", sa.Text(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_systems_audit_id", "ai_systems", ["audit_id"])

    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_system_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_systems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_agent_runs_audit_id", "agent_runs", ["audit_id"])
    op.create_index("ix_agent_runs_ai_system_id", "agent_runs", ["ai_system_id"])

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_system_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_systems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("storage_url", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_artifacts_audit_id", "artifacts", ["audit_id"])
    op.create_index("ix_artifacts_ai_system_id", "artifacts", ["ai_system_id"])

    op.create_table(
        "gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ai_system_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_systems.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("effort_days", sa.Integer(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
    )
    op.create_index("ix_gaps_audit_id", "gaps", ["audit_id"])
    op.create_index("ix_gaps_ai_system_id", "gaps", ["ai_system_id"])


def downgrade() -> None:
    """Drop the initial D2 schema."""

    op.drop_index("ix_gaps_ai_system_id", table_name="gaps")
    op.drop_index("ix_gaps_audit_id", table_name="gaps")
    op.drop_table("gaps")

    op.drop_index("ix_artifacts_ai_system_id", table_name="artifacts")
    op.drop_index("ix_artifacts_audit_id", table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index("ix_agent_runs_ai_system_id", table_name="agent_runs")
    op.drop_index("ix_agent_runs_audit_id", table_name="agent_runs")
    op.drop_table("agent_runs")

    op.drop_index("ix_ai_systems_audit_id", table_name="ai_systems")
    op.drop_table("ai_systems")

    op.drop_table("audits")
