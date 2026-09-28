from __future__ import annotations

import hashlib
import html
import io
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.form_definitions import form_schema, quality_score, validate_response
from app.models import (
    Assignment,
    AssuranceFinding,
    AuditEvent,
    Disclosure,
    Evidence,
    EvidenceVersion,
    Framework,
    Job,
    Organization,
    ReportingCycle,
    Submission,
    SubmissionComment,
    WorkflowEvent,
)
from app.schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    CommentCreate,
    CycleCreate,
    DisclosureCreate,
    DisclosureUpdate,
    FindingCreate,
    JobCreate,
    OrganizationCreate,
    SubmissionCreate,
    TransitionRequest,
)
from app.security import PERMISSIONS, USERS, current_user, require
from app.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(
    title="BRSR Nexus API",
    version="3.0.0",
    description="Governed ESG collection, evidence, workflow, consolidation, assurance, and reporting.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def record_audit(db: Session, entity_type: str, entity_id: str, action: str, user: Any, detail: dict | None = None) -> None:
    db.add(AuditEvent(entity_type=entity_type, entity_id=entity_id, action=action, actor=user.name, actor_role=user.role, detail=detail or {}))


def disclosure_json(item: Disclosure) -> dict:
    return {
        "id": item.id,
        "framework_id": item.framework_id,
        "section": item.section,
        "principle": item.principle,
        "question_number": item.question_number,
        "title": item.title,
        "classification": item.classification,
        "response_type": item.response_type,
        "reporting_level": item.reporting_level,
        "unit": item.unit,
        "evidence_required": item.evidence_required,
        "guidance": item.guidance,
        "validation_rules": item.validation_rules,
        "active": item.active,
        "form_schema": form_schema(item),
    }


def evidence_count(db: Session, submission_id: str) -> int:
    return db.scalar(select(func.count(Evidence.id)).where(Evidence.submission_id == submission_id)) or 0


def validation_state(db: Session, item: Submission) -> tuple[list[str], int]:
    disclosure = db.get(Disclosure, item.disclosure_id)
    if not disclosure:
        return ["Disclosure no longer exists"], 0
    errors = validate_response(disclosure, item.value or {})
    has_evidence = evidence_count(db, item.id) > 0
    return errors, quality_score(errors, has_evidence, disclosure.evidence_required)


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "service": "brsr-nexus-api", "version": "3.0.0"}


@app.get("/api/v1/auth/users")
def users():
    return [u.__dict__ for u in USERS.values()]


@app.get("/api/v1/auth/me")
def me(user=Depends(current_user)):
    return user.__dict__


@app.get("/api/v1/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(require("read"))):
    financial_year = "2025-26"
    rows = db.scalars(select(Submission).where(Submission.financial_year == financial_year)).all()
    counts = {status: sum(1 for row in rows if row.status == status) for status in ["draft", "submitted", "changes_requested", "approved", "locked"]}
    approved = counts["approved"] + counts["locked"]
    avg_quality = round(sum(r.quality_score for r in rows) / len(rows)) if rows else 0
    assigned = db.scalar(select(func.count(Assignment.id))) or 0
    principle_rows = []
    principle_names = {
        1: "Ethics & governance",
        2: "Sustainable goods & services",
        3: "Employee well-being",
        4: "Stakeholder engagement",
        5: "Human rights",
        6: "Environment",
        7: "Public policy",
        8: "Inclusive growth",
        9: "Consumer value",
    }
    disclosures = db.scalars(select(Disclosure).where(Disclosure.active.is_(True), Disclosure.section == "C")).all()
    for principle in range(1, 10):
        scoped = [item for item in disclosures if item.principle == principle]
        scoped_ids = {item.id for item in scoped}
        related = [row for row in rows if row.disclosure_id in scoped_ids]
        ready_ids = {row.disclosure_id for row in related if eligible_for_reporting(db, row)}
        approved_ids = {row.disclosure_id for row in related if row.status in {"approved", "locked"}}
        awaiting_review = sum(1 for row in related if row.status == "submitted")
        missing_evidence = sum(
            1
            for item in scoped
            if item.evidence_required
            and any(row.disclosure_id == item.id and row.status in {"approved", "locked"} for row in related)
            and not any(
                row.disclosure_id == item.id
                and row.status in {"approved", "locked"}
                and evidence_count(db, row.id) > 0
                for row in related
            )
        )
        principle_rows.append({
            "principle": principle,
            "name": principle_names[principle],
            "ready": len(ready_ids),
            "total": len(scoped),
            "readiness_percent": round(len(ready_ids) / len(scoped) * 100) if scoped else 0,
            "approved": len(approved_ids),
            "awaiting_review": awaiting_review,
            "missing_evidence": missing_evidence,
        })
    return {
        "financial_year": financial_year,
        "reporting_cycle": "FY 2025–26 · Annexure baseline",
        "total": len(rows),
        "assigned": assigned,
        "approved": approved,
        "awaiting_review": counts["submitted"],
        "changes_requested": counts["changes_requested"],
        "completion_percent": round(approved / assigned * 100) if assigned else 0,
        "quality_score": avg_quality,
        "status_counts": counts,
        "modules": 14,
        "principle_readiness": principle_rows,
    }


@app.get("/api/v1/organizations")
def organizations(db: Session = Depends(get_db), user=Depends(require("read"))):
    return db.scalars(select(Organization).order_by(Organization.organization_type, Organization.name)).all()


@app.post("/api/v1/organizations", status_code=201)
def create_organization(payload: OrganizationCreate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    if payload.parent_id and not db.get(Organization, payload.parent_id):
        raise HTTPException(404, "Parent organization not found")
    if db.scalar(select(Organization).where(Organization.code == payload.code)):
        raise HTTPException(409, "Organization code already exists")
    item = Organization(**payload.model_dump())
    db.add(item)
    db.flush()
    record_audit(db, "organization", item.id, "created", user, {"name": item.name, "code": item.code})
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/frameworks")
def frameworks(db: Session = Depends(get_db), user=Depends(require("read"))):
    return db.scalars(select(Framework)).all()


@app.get("/api/v1/reporting-cycles")
def reporting_cycles(db: Session = Depends(get_db), user=Depends(require("read"))):
    return db.scalars(select(ReportingCycle).order_by(ReportingCycle.financial_year.desc())).all()


@app.post("/api/v1/reporting-cycles", status_code=201)
def create_cycle(payload: CycleCreate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    if not db.get(Framework, payload.framework_id):
        raise HTTPException(404, "Framework not found")
    item = ReportingCycle(**payload.model_dump(), status="open")
    db.add(item)
    db.flush()
    record_audit(db, "reporting_cycle", item.id, "created", user, {"financial_year": item.financial_year})
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/disclosures")
def disclosures(
    section: str | None = None,
    principle: int | None = None,
    classification: str | None = None,
    q: str | None = None,
    include_inactive: bool = False,
    limit: int = Query(300, le=500),
    db: Session = Depends(get_db),
    user=Depends(require("read")),
):
    stmt = select(Disclosure)
    if not include_inactive:
        stmt = stmt.where(Disclosure.active.is_(True))
    if section:
        stmt = stmt.where(Disclosure.section == section)
    if principle is not None:
        stmt = stmt.where(Disclosure.principle == principle)
    if classification:
        stmt = stmt.where(Disclosure.classification == classification)
    if q:
        term = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Disclosure.title).like(term) | func.lower(Disclosure.id).like(term))
    rows = db.scalars(stmt.order_by(Disclosure.section, Disclosure.principle, Disclosure.question_number).limit(limit)).all()
    return [disclosure_json(item) for item in rows]


@app.get("/api/v1/disclosures/{disclosure_id}")
def disclosure_detail(disclosure_id: str, db: Session = Depends(get_db), user=Depends(require("read"))):
    item = db.get(Disclosure, disclosure_id)
    if not item:
        raise HTTPException(404, "Disclosure not found")
    return disclosure_json(item)


@app.post("/api/v1/disclosures", status_code=201)
def create_disclosure(payload: DisclosureCreate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    if db.get(Disclosure, payload.id):
        raise HTTPException(409, "Disclosure ID already exists")
    if not db.get(Framework, payload.framework_id):
        raise HTTPException(404, "Framework not found")
    item = Disclosure(**payload.model_dump(), active=True)
    db.add(item)
    record_audit(db, "disclosure", item.id, "created", user, {"title": item.title})
    db.commit()
    db.refresh(item)
    return disclosure_json(item)


@app.put("/api/v1/disclosures/{disclosure_id}")
def update_disclosure(disclosure_id: str, payload: DisclosureUpdate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    item = db.get(Disclosure, disclosure_id)
    if not item:
        raise HTTPException(404, "Disclosure not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    record_audit(db, "disclosure", item.id, "updated", user, {"title": item.title})
    db.commit()
    db.refresh(item)
    return disclosure_json(item)


@app.delete("/api/v1/disclosures/{disclosure_id}")
def archive_disclosure(disclosure_id: str, db: Session = Depends(get_db), user=Depends(require("assign"))):
    item = db.get(Disclosure, disclosure_id)
    if not item:
        raise HTTPException(404, "Disclosure not found")
    item.active = False
    record_audit(db, "disclosure", item.id, "archived", user, {"title": item.title})
    db.commit()
    return {"id": item.id, "active": False}


@app.get("/api/v1/assignments")
def assignments(
    cycle_id: str | None = None,
    owner_user_id: str | None = None,
    disclosure_id: str | None = None,
    organization_id: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require("read")),
):
    stmt = select(Assignment)
    if cycle_id:
        stmt = stmt.where(Assignment.cycle_id == cycle_id)
    if owner_user_id:
        stmt = stmt.where(Assignment.owner_user_id == owner_user_id)
    if disclosure_id:
        stmt = stmt.where(Assignment.disclosure_id == disclosure_id)
    if organization_id:
        stmt = stmt.where(Assignment.organization_id == organization_id)
    return db.scalars(stmt.order_by(Assignment.due_date, Assignment.disclosure_id)).all()


@app.post("/api/v1/assignments", status_code=201)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    if not db.get(ReportingCycle, payload.cycle_id):
        raise HTTPException(404, "Reporting cycle not found")
    if not db.get(Disclosure, payload.disclosure_id):
        raise HTTPException(404, "Disclosure not found")
    if not db.get(Organization, payload.organization_id):
        raise HTTPException(404, "Organization not found")
    duplicate = db.scalar(select(Assignment).where(Assignment.cycle_id == payload.cycle_id, Assignment.disclosure_id == payload.disclosure_id, Assignment.organization_id == payload.organization_id))
    if duplicate:
        raise HTTPException(409, "This disclosure is already assigned to that organization for the cycle")
    item = Assignment(**payload.model_dump())
    db.add(item)
    db.flush()
    record_audit(db, "assignment", item.id, "created", user, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/v1/assignments/{assignment_id}")
def update_assignment(assignment_id: str, payload: AssignmentUpdate, db: Session = Depends(get_db), user=Depends(require("assign"))):
    item = db.get(Assignment, assignment_id)
    if not item:
        raise HTTPException(404, "Assignment not found")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    record_audit(db, "assignment", item.id, "updated", user, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.delete("/api/v1/assignments/{assignment_id}")
def delete_assignment(assignment_id: str, db: Session = Depends(get_db), user=Depends(require("assign"))):
    item = db.get(Assignment, assignment_id)
    if not item:
        raise HTTPException(404, "Assignment not found")
    linked = db.scalar(select(func.count(Submission.id)).where(Submission.disclosure_id == item.disclosure_id, Submission.organization_id == item.organization_id)) or 0
    if linked:
        raise HTTPException(409, "Assignment has submissions and cannot be removed")
    record_audit(db, "assignment", item.id, "deleted", user, {"disclosure_id": item.disclosure_id})
    db.delete(item)
    db.commit()
    return {"deleted": assignment_id}


@app.get("/api/v1/submissions")
def submissions(status: str | None = None, financial_year: str | None = None, db: Session = Depends(get_db), user=Depends(require("read"))):
    stmt = select(Submission)
    if status:
        stmt = stmt.where(Submission.status == status)
    if financial_year:
        stmt = stmt.where(Submission.financial_year == financial_year)
    return db.scalars(stmt.order_by(Submission.updated_at.desc())).all()


@app.post("/api/v1/submissions", status_code=201)
def create_submission(payload: SubmissionCreate, db: Session = Depends(get_db), user=Depends(require("collect"))):
    disclosure = db.get(Disclosure, payload.disclosure_id)
    if not disclosure or not disclosure.active:
        raise HTTPException(404, "Disclosure not found")
    if not db.get(Organization, payload.organization_id):
        raise HTTPException(404, "Organization not found")
    duplicate = db.scalar(select(Submission).where(Submission.disclosure_id == payload.disclosure_id, Submission.organization_id == payload.organization_id, Submission.financial_year == payload.financial_year))
    if duplicate:
        raise HTTPException(409, "A submission already exists for this disclosure, organization, and year")
    errors = validate_response(disclosure, payload.value)
    item = Submission(**payload.model_dump(), status="draft", quality_score=quality_score(errors, False, disclosure.evidence_required), validation_errors=errors)
    db.add(item)
    db.flush()
    record_audit(db, "submission", item.id, "draft_created", user, {"disclosure_id": item.disclosure_id, "organization_id": item.organization_id})
    db.commit()
    db.refresh(item)
    return item


@app.put("/api/v1/submissions/{submission_id}")
def update_submission(submission_id: str, payload: SubmissionCreate, db: Session = Depends(get_db), user=Depends(require("collect"))):
    item = db.get(Submission, submission_id)
    if not item:
        raise HTTPException(404, "Submission not found")
    if item.status not in {"draft", "changes_requested"}:
        raise HTTPException(409, "Only drafts or returned submissions can be edited")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    item.validation_errors, item.quality_score = validation_state(db, item)
    record_audit(db, "submission", item.id, "draft_updated", user, {"quality_score": item.quality_score, "validation_errors": item.validation_errors})
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/submissions/{submission_id}/comments")
def comments(submission_id: str, db: Session = Depends(get_db), user=Depends(require("read"))):
    if not db.get(Submission, submission_id):
        raise HTTPException(404, "Submission not found")
    return db.scalars(select(SubmissionComment).where(SubmissionComment.submission_id == submission_id).order_by(SubmissionComment.created_at)).all()


@app.post("/api/v1/submissions/{submission_id}/comments", status_code=201)
def add_comment(submission_id: str, payload: CommentCreate, db: Session = Depends(get_db), user=Depends(require("read"))):
    if not db.get(Submission, submission_id):
        raise HTTPException(404, "Submission not found")
    item = SubmissionComment(submission_id=submission_id, actor=user.name, actor_role=user.role, body=payload.body.strip())
    db.add(item)
    record_audit(db, "submission", submission_id, "comment_added", user, {"comment": payload.body.strip()})
    db.commit()
    db.refresh(item)
    return item


ALLOWED = {
    "draft": {"submitted"},
    "submitted": {"changes_requested", "approved"},
    "changes_requested": {"submitted"},
    "approved": {"locked"},
    "locked": set(),
}


@app.post("/api/v1/workflow/{submission_id}/transition")
def transition(submission_id: str, payload: TransitionRequest, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.get(Submission, submission_id)
    if not item:
        raise HTTPException(404, "Submission not found")
    permission = {"submitted": "submit", "changes_requested": "request_changes", "approved": "approve", "locked": "lock"}.get(payload.to_status, "review")
    allowed = {"*"} if user.role == "administrator" else PERMISSIONS[user.role]
    if "*" not in allowed and permission not in allowed:
        raise HTTPException(403, f"Role {user.role} cannot {permission}")
    if payload.to_status not in ALLOWED.get(item.status, set()):
        raise HTTPException(409, f"Invalid transition {item.status} → {payload.to_status}")
    if payload.to_status == "changes_requested" and not (payload.comment or "").strip():
        raise HTTPException(422, "A correction comment is required")
    if payload.to_status in {"submitted", "approved"}:
        errors, score = validation_state(db, item)
        disclosure = db.get(Disclosure, item.disclosure_id)
        if disclosure and disclosure.evidence_required and evidence_count(db, item.id) == 0:
            errors.append("Required evidence has not been uploaded")
        item.validation_errors = errors
        item.quality_score = quality_score(errors, evidence_count(db, item.id) > 0, bool(disclosure and disclosure.evidence_required))
        if errors:
            db.commit()
            raise HTTPException(422, {"message": "Resolve validation issues before continuing", "errors": errors})
    event = WorkflowEvent(submission_id=item.id, from_status=item.status, to_status=payload.to_status, actor=user.name, comment=payload.comment)
    previous = item.status
    item.status = payload.to_status
    item.reviewer = user.name
    if payload.to_status == "approved":
        item.quality_score = max(item.quality_score, 95)
    db.add(event)
    if payload.comment:
        db.add(SubmissionComment(submission_id=item.id, actor=user.name, actor_role=user.role, body=payload.comment.strip()))
    record_audit(db, "submission", item.id, f"status_{payload.to_status}", user, {"from_status": previous, "to_status": payload.to_status, "comment": payload.comment})
    db.commit()
    db.refresh(item)
    return item


ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".png", ".jpg", ".jpeg", ".doc", ".docx"}


@app.get("/api/v1/evidence")
def evidence(submission_id: str | None = None, db: Session = Depends(get_db), user=Depends(require("read"))):
    stmt = select(Evidence)
    if submission_id:
        stmt = stmt.where(Evidence.submission_id == submission_id)
    return db.scalars(stmt.order_by(Evidence.created_at.desc())).all()


@app.post("/api/v1/evidence/upload", status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    submission_id: str = Form(...),
    organization_id: str = Form(...),
    financial_year: str = Form(...),
    document_type: str = Form("supporting_document"),
    evidence_id: str | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(require("collect")),
):
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    if submission.status in {"approved", "locked"}:
        raise HTTPException(409, "Evidence cannot be changed after approval")
    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, f"Unsupported file type: {suffix or 'unknown'}")
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB")
    checksum = hashlib.sha256(data).hexdigest()
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(file.filename or "evidence").name).strip("-")
    item = db.get(Evidence, evidence_id) if evidence_id else None
    if evidence_id and not item:
        raise HTTPException(404, "Evidence record not found")
    if item and item.submission_id != submission_id:
        raise HTTPException(409, "Evidence belongs to another submission")
    if not item:
        item = Evidence(submission_id=submission_id, organization_id=organization_id, financial_year=financial_year, file_name=safe_name, document_type=document_type, storage_key="pending", checksum=checksum, processing_status="stored")
        db.add(item)
        db.flush()
    version_no = (db.scalar(select(func.max(EvidenceVersion.version_number)).where(EvidenceVersion.evidence_id == item.id)) or 0) + 1
    relative = f"{financial_year}/{submission_id}/{item.id}/v{version_no}-{safe_name}"
    destination = Path(settings.storage_root) / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    item.file_name = safe_name
    item.document_type = document_type
    item.storage_key = relative
    item.checksum = checksum
    item.processing_status = "stored"
    version = EvidenceVersion(evidence_id=item.id, version_number=version_no, storage_key=relative, checksum=checksum, content_type=file.content_type or "application/octet-stream", size_bytes=len(data), uploaded_by=user.name)
    db.add(version)
    submission.validation_errors, submission.quality_score = validation_state(db, submission)
    record_audit(db, "evidence", item.id, "uploaded" if version_no == 1 else "version_uploaded", user, {"submission_id": submission_id, "file_name": safe_name, "version": version_no, "checksum": checksum, "size_bytes": len(data)})
    db.commit()
    db.refresh(item)
    return {"evidence": item, "version": version}


@app.get("/api/v1/evidence/{evidence_id}/versions")
def evidence_versions(evidence_id: str, db: Session = Depends(get_db), user=Depends(require("read"))):
    if not db.get(Evidence, evidence_id):
        raise HTTPException(404, "Evidence not found")
    return db.scalars(select(EvidenceVersion).where(EvidenceVersion.evidence_id == evidence_id).order_by(EvidenceVersion.version_number.desc())).all()


@app.get("/api/v1/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Session = Depends(get_db), user=Depends(require("read"))):
    item = db.get(Evidence, evidence_id)
    if not item:
        raise HTTPException(404, "Evidence not found")
    path = Path(settings.storage_root) / item.storage_key
    if not path.exists():
        raise HTTPException(404, "Stored file is unavailable")
    return FileResponse(path, filename=item.file_name)


@app.get("/api/v1/submissions/{submission_id}/timeline")
def submission_timeline(submission_id: str, db: Session = Depends(get_db), user=Depends(require("read"))):
    if not db.get(Submission, submission_id):
        raise HTTPException(404, "Submission not found")
    audits = db.scalars(select(AuditEvent).where(AuditEvent.entity_type == "submission", AuditEvent.entity_id == submission_id)).all()
    evidence_rows = db.scalars(select(Evidence).where(Evidence.submission_id == submission_id)).all()
    evidence_ids = [row.id for row in evidence_rows]
    evidence_audits = db.scalars(select(AuditEvent).where(AuditEvent.entity_type == "evidence", AuditEvent.entity_id.in_(evidence_ids))).all() if evidence_ids else []
    events = [
        {"id": row.id, "kind": row.action, "actor": row.actor, "role": row.actor_role, "detail": row.detail, "created_at": row.created_at}
        for row in [*audits, *evidence_audits]
    ]
    return sorted(events, key=lambda row: row["created_at"], reverse=True)


def eligible_for_reporting(db: Session, item: Submission) -> bool:
    if item.status not in {"approved", "locked"}:
        return False
    disclosure = db.get(Disclosure, item.disclosure_id)
    if not disclosure or validate_response(disclosure, item.value or {}):
        return False
    if disclosure.evidence_required and evidence_count(db, item.id) == 0:
        return False
    return True


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


@app.get("/api/v1/consolidation")
def consolidation(financial_year: str = "2025-26", db: Session = Depends(get_db), user=Depends(require("read"))):
    candidates = db.scalars(select(Submission).where(Submission.financial_year == financial_year, Submission.status.in_(["approved", "locked"]))).all()
    rows = [row for row in candidates if eligible_for_reporting(db, row)]
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        disclosure = db.get(Disclosure, row.disclosure_id)
        entry = grouped.setdefault(row.disclosure_id, {"disclosure_id": row.disclosure_id, "title": disclosure.title if disclosure else row.disclosure_id, "unit": disclosure.unit if disclosure else None, "submission_count": 0, "organization_ids": [], "metrics": {}, "source_submission_ids": []})
        entry["submission_count"] += 1
        entry["organization_ids"].append(row.organization_id)
        entry["source_submission_ids"].append(row.id)
        for key, raw in (row.value or {}).items():
            number = numeric_value(raw)
            if number is not None:
                entry["metrics"][key] = round(entry["metrics"].get(key, 0) + number, 4)
    return {"financial_year": financial_year, "approved_inputs": len(rows), "excluded_inputs": len(candidates) - len(rows), "rows": list(grouped.values()), "method": "Sum of validation-complete approved or locked numeric source fields with required evidence; narratives remain traceable but are not summed."}


def report_payload(financial_year: str, db: Session) -> dict[str, Any]:
    all_disclosures = db.scalars(select(Disclosure).where(Disclosure.active.is_(True)).order_by(Disclosure.section, Disclosure.principle, Disclosure.question_number)).all()
    submissions = db.scalars(select(Submission).where(Submission.financial_year == financial_year)).all()
    output = []
    for disclosure in all_disclosures:
        related = [row for row in submissions if row.disclosure_id == disclosure.id]
        approved = [row for row in related if eligible_for_reporting(db, row)]
        output.append({"id": disclosure.id, "section": disclosure.section, "principle": disclosure.principle, "question_number": disclosure.question_number, "classification": disclosure.classification, "title": disclosure.title, "unit": disclosure.unit, "form_schema": form_schema(disclosure), "status": "ready" if approved else (related[0].status if related else "not_started"), "responses": [{"submission_id": row.id, "organization_id": row.organization_id, "value": row.value, "status": row.status, "quality_score": row.quality_score} for row in approved]})
    ready = sum(1 for row in output if row["status"] == "ready")
    return {"financial_year": financial_year, "generated_from": "Approved and locked submissions only", "readiness_percent": round(ready / len(output) * 100) if output else 0, "ready_disclosures": ready, "total_disclosures": len(output), "sections": output}


@app.get("/api/v1/reports/preview")
def report_preview(financial_year: str = "2025-26", db: Session = Depends(get_db), user=Depends(require("read"))):
    return report_payload(financial_year, db)


@app.get("/api/v1/reports/export.xlsx")
def export_excel(financial_year: str = "2025-26", db: Session = Depends(get_db), user=Depends(require("read"))):
    payload = report_payload(financial_year, db)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "BRSR report"
    sheet.append(["Disclosure ID", "Section", "Principle", "Disclosure", "Unit", "Status", "Organization", "Approved response", "Quality"])
    for row in payload["sections"]:
        if row["responses"]:
            for response in row["responses"]:
                sheet.append([row["id"], row["section"], row["principle"], row["title"], row["unit"], response["status"], response["organization_id"], json.dumps(response["value"], ensure_ascii=False), response["quality_score"]])
        else:
            sheet.append([row["id"], row["section"], row["principle"], row["title"], row["unit"], row["status"], "", "", ""])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in {"A": 16, "B": 10, "C": 10, "D": 48, "E": 18, "F": 18, "G": 20, "H": 60, "I": 12}.items():
        sheet.column_dimensions[column].width = width
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="BRSR-{financial_year}.xlsx"'})


@app.get("/api/v1/reports/export.pdf")
def export_pdf(financial_year: str = "2025-26", db: Session = Depends(get_db), user=Depends(require("read"))):
    payload = report_payload(financial_year, db)
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=14 * mm, leftMargin=14 * mm, topMargin=16 * mm, bottomMargin=16 * mm, title=f"BRSR {financial_year}")
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#173B61")
    styles["Title"].fontSize = 25
    styles["Heading1"].textColor = colors.HexColor("#236FD1")
    styles["Heading1"].fontSize = 16
    styles["Heading2"].fontSize = 12
    styles["BodyText"].fontSize = 8
    styles["BodyText"].leading = 11
    story = [Spacer(1, 28 * mm), Paragraph("BUSINESS RESPONSIBILITY AND<br/>SUSTAINABILITY REPORT", styles["Title"]), Spacer(1, 8 * mm), Paragraph("MEIL Demo Group", styles["Heading1"]), Paragraph(f"Financial year {html.escape(financial_year)}", styles["Heading2"]), Spacer(1, 18 * mm), Paragraph("Generated from approved and locked, validation-complete source records with required evidence.", styles["BodyText"]), PageBreak()]
    section_names = {"A": "General Disclosures", "B": "Management and Process Disclosures", "C": "Principle-wise Performance Disclosure"}
    current_section = None
    current_principle = None
    for row in payload["sections"]:
        if row["section"] != current_section:
            current_section = row["section"]
            current_principle = None
            story.extend([Paragraph(f'SECTION {current_section}', styles["Heading1"]), Paragraph(section_names[current_section], styles["Heading2"]), Spacer(1, 4 * mm)])
        if current_section == "C" and row["principle"] != current_principle:
            current_principle = row["principle"]
            story.extend([Spacer(1, 3 * mm), Paragraph(f'PRINCIPLE {current_principle}', styles["Heading2"])])
        status = row["status"].replace("_", " ").title()
        story.append(Table([[Paragraph(f'<b>{html.escape(str(row["question_number"]))}</b>', styles["BodyText"]), Paragraph(f'<b>{html.escape(row["title"])}</b><br/><font color="#737674">{html.escape(row["classification"].title())} indicator · {html.escape(status)}</font>', styles["BodyText"])]], colWidths=[10 * mm, 170 * mm], style=TableStyle([("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E5F2FC")), ("BOX", (0,0), (-1,-1), .35, colors.HexColor("#D9DEDC")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("PADDING", (0,0), (-1,-1), 5)])))
        if not row["responses"]:
            story.append(Paragraph("No approved source response is available for publication.", styles["BodyText"]))
        for response in row["responses"]:
            story.append(Paragraph(f'<font color="#737674">Source: {html.escape(response["organization_id"])} · Quality {response["quality_score"]}/100</font>', styles["BodyText"]))
            for field in row["form_schema"]:
                raw = response["value"].get(field["key"])
                story.append(Paragraph(f'<b>{html.escape(field["label"])}</b>', styles["BodyText"]))
                if field["type"] == "table" and isinstance(raw, list) and raw:
                    columns = field.get("columns", [])
                    table_data = [[Paragraph(html.escape(column["label"]), styles["BodyText"]) for column in columns]]
                    for item in raw:
                        table_data.append([Paragraph(html.escape(str(item.get(column["key"], "—") or "—")), styles["BodyText"]) for column in columns])
                    widths = [180 * mm / max(1, len(columns))] * len(columns)
                    answer_table = Table(table_data, colWidths=widths, repeatRows=1)
                    answer_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E5F2FC")), ("GRID", (0,0), (-1,-1), .3, colors.HexColor("#D9DEDC")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("PADDING", (0,0), (-1,-1), 3)]))
                    story.append(answer_table)
                else:
                    story.append(Paragraph(html.escape(str(raw if raw not in (None, "") else "—")), styles["BodyText"]))
        story.append(Spacer(1, 5 * mm))
    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont("Helvetica", 7); canvas.setFillColor(colors.HexColor("#737674")); canvas.drawString(14*mm, 8*mm, "BRSR Nexus · Controlled publication"); canvas.drawRightString(196*mm, 8*mm, f"Page {doc.page}"); canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    output.seek(0)
    return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="BRSR-{financial_year}.pdf"'})


@app.get("/api/v1/assurance/findings")
def findings(db: Session = Depends(get_db), user=Depends(require("read"))):
    return db.scalars(select(AssuranceFinding)).all()


@app.post("/api/v1/assurance/findings", status_code=201)
def create_finding(payload: FindingCreate, db: Session = Depends(get_db), user=Depends(require("assure"))):
    item = AssuranceFinding(**payload.model_dump())
    db.add(item)
    db.flush()
    record_audit(db, "assurance_finding", item.id, "created", user, payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/v1/imports", status_code=202)
def create_import(payload: JobCreate, db: Session = Depends(get_db), user=Depends(require("collect"))):
    item = Job(job_type="import", requested_by=user.name, parameters=payload.parameters)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/api/v1/reports", status_code=202)
def create_report(payload: JobCreate, db: Session = Depends(get_db), user=Depends(require("read"))):
    item = Job(job_type="report", requested_by=user.name, parameters=payload.parameters)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/v1/jobs")
def jobs(db: Session = Depends(get_db), user=Depends(require("read"))):
    return db.scalars(select(Job).order_by(Job.created_at.desc())).all()


@app.get("/api/v1/audit")
def audit(
    entity_type: str | None = None,
    action: str | None = None,
    q: str | None = None,
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
    user=Depends(require("read")),
):
    stmt = select(AuditEvent)
    if entity_type:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    if q:
        stmt = stmt.where(func.lower(AuditEvent.actor).like(f"%{q.lower()}%") | func.lower(AuditEvent.entity_id).like(f"%{q.lower()}%"))
    return db.scalars(stmt.order_by(AuditEvent.created_at.desc()).limit(limit)).all()
