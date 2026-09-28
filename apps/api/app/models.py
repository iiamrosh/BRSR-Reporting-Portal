from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def uid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    organization_type: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Framework(Base):
    __tablename__ = "frameworks"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(50), unique=True)
    baseline: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="draft")


class Disclosure(Base):
    __tablename__ = "disclosures"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id"))
    section: Mapped[str] = mapped_column(String(10))
    principle: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_number: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(300))
    classification: Mapped[str] = mapped_column(String(30))
    response_type: Mapped[str] = mapped_column(String(30))
    reporting_level: Mapped[str] = mapped_column(String(30))
    unit: Mapped[str | None] = mapped_column(String(60), nullable=True)
    evidence_required: Mapped[bool] = mapped_column(Boolean, default=False)
    guidance: Mapped[str] = mapped_column(Text, default="")
    validation_rules: Mapped[dict] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReportingCycle(Base):
    __tablename__ = "reporting_cycles"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    framework_id: Mapped[str] = mapped_column(ForeignKey("frameworks.id"))
    name: Mapped[str] = mapped_column(String(120))
    financial_year: Mapped[str] = mapped_column(String(20), index=True)
    boundary_type: Mapped[str] = mapped_column(String(30), default="consolidated")
    status: Mapped[str] = mapped_column(String(30), default="open")
    starts_on: Mapped[str] = mapped_column(String(20))
    ends_on: Mapped[str] = mapped_column(String(20))


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    cycle_id: Mapped[str] = mapped_column(ForeignKey("reporting_cycles.id"))
    disclosure_id: Mapped[str] = mapped_column(ForeignKey("disclosures.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    owner_user_id: Mapped[str] = mapped_column(String(60))
    reviewer_user_id: Mapped[str] = mapped_column(String(60))
    approver_user_id: Mapped[str] = mapped_column(String(60), default="approver")
    due_date: Mapped[str] = mapped_column(String(20))
    frequency: Mapped[str] = mapped_column(String(30), default="annual")
    status: Mapped[str] = mapped_column(String(30), default="not_started")


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    disclosure_id: Mapped[str] = mapped_column(ForeignKey("disclosures.id"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    financial_year: Mapped[str] = mapped_column(String(20))
    value: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    owner: Mapped[str] = mapped_column(String(120))
    reviewer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_method: Mapped[str] = mapped_column(String(30), default="manual")
    quality_score: Mapped[float] = mapped_column(Float, default=0)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    submission_id: Mapped[str | None] = mapped_column(ForeignKey("submissions.id"), nullable=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    financial_year: Mapped[str] = mapped_column(String(20))
    file_name: Mapped[str] = mapped_column(String(260))
    document_type: Mapped[str] = mapped_column(String(60))
    storage_key: Mapped[str] = mapped_column(String(300), default="pending")
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="stored")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EvidenceVersion(Base):
    __tablename__ = "evidence_versions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id"))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    storage_key: Mapped[str] = mapped_column(String(300))
    checksum: Mapped[str] = mapped_column(String(128))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    uploaded_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class SubmissionComment(Base):
    __tablename__ = "submission_comments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"))
    actor: Mapped[str] = mapped_column(String(120))
    actor_role: Mapped[str] = mapped_column(String(40))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"))
    from_status: Mapped[str] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30))
    actor: Mapped[str] = mapped_column(String(120))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(80), index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    actor: Mapped[str] = mapped_column(String(120))
    actor_role: Mapped[str] = mapped_column(String(40))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AssuranceFinding(Base):
    __tablename__ = "assurance_findings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"))
    severity: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(30), default="open")
    owner: Mapped[str] = mapped_column(String(120))
    due_date: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    job_type: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    requested_by: Mapped[str] = mapped_column(String(120))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
