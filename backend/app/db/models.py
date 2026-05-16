"""SQLAlchemy ORM models for Conforma-AI."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text, Uuid, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

json_type = JSONB().with_variant(JSON(), "sqlite")
text_list_type = ARRAY(Text()).with_variant(JSON(), "sqlite")


class Base(DeclarativeBase):
    """Base declarative model for Conforma-AI."""


class Audit(Base):
    """Top-level audit job metadata."""

    __tablename__ = "audits"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    compliance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_index: Mapped[str | None] = mapped_column(Text, nullable=True)
    fine_exposure_eur: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    audit_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", json_type, nullable=True)

    ai_systems: Mapped[list["AISystem"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        back_populates="audit", cascade="all, delete-orphan"
    )
    gaps: Mapped[list["Gap"]] = relationship(back_populates="audit", cascade="all, delete-orphan")


class AISystem(Base):
    """AI system discovered inside an audit."""

    __tablename__ = "ai_systems"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    audit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_files: Mapped[list[str] | None] = mapped_column(text_list_type, nullable=True)
    risk_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_article: Mapped[str | None] = mapped_column(Text, nullable=True)
    secondary_articles: Mapped[list[str] | None] = mapped_column(text_list_type, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline_iso: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    triggers_article_50: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    audit: Mapped["Audit"] = relationship(back_populates="ai_systems")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="ai_system")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="ai_system")
    gaps: Mapped[list["Gap"]] = relationship(back_populates="ai_system")


class AgentRun(Base):
    """Execution trace for an agent invocation."""

    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    audit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    ai_system_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_systems.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    input: Mapped[dict[str, Any] | None] = mapped_column(json_type, nullable=True)
    output: Mapped[dict[str, Any] | None] = mapped_column(json_type, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    audit: Mapped["Audit"] = relationship(back_populates="agent_runs")
    ai_system: Mapped["AISystem"] = relationship(back_populates="agent_runs")


class Artifact(Base):
    """Generated documentation or disclosure artifact."""

    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    audit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    ai_system_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ai_systems.id", ondelete="SET NULL"), index=True, nullable=True
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    audit: Mapped["Audit"] = relationship(back_populates="artifacts")
    ai_system: Mapped["AISystem"] = relationship(back_populates="artifacts")


class Gap(Base):
    """Compliance gap identified during an audit."""

    __tablename__ = "gaps"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    audit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audits.id", ondelete="CASCADE"), index=True, nullable=False
    )
    ai_system_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("ai_systems.id", ondelete="SET NULL"), index=True, nullable=True
    )
    category: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    effort_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    audit: Mapped["Audit"] = relationship(back_populates="gaps")
    ai_system: Mapped["AISystem"] = relationship(back_populates="gaps")
