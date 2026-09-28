from typing import Any

from pydantic import BaseModel, Field


class SubmissionCreate(BaseModel):
    disclosure_id: str
    organization_id: str
    financial_year: str
    value: dict[str, Any]
    owner: str
    source_method: str = "manual"


class OrganizationCreate(BaseModel):
    parent_id: str | None = None
    name: str
    organization_type: str
    code: str


class CycleCreate(BaseModel):
    framework_id: str
    name: str
    financial_year: str
    boundary_type: str = "consolidated"
    starts_on: str
    ends_on: str


class AssignmentCreate(BaseModel):
    cycle_id: str
    disclosure_id: str
    organization_id: str
    owner_user_id: str = "owner"
    reviewer_user_id: str = "reviewer"
    approver_user_id: str = "approver"
    due_date: str
    frequency: str = "annual"


class AssignmentUpdate(BaseModel):
    owner_user_id: str
    reviewer_user_id: str = "reviewer"
    approver_user_id: str = "approver"
    due_date: str
    frequency: str = "annual"


class DisclosureCreate(BaseModel):
    id: str
    framework_id: str
    section: str
    principle: int | None = None
    question_number: str
    title: str
    classification: str = "essential"
    response_type: str = "narrative"
    reporting_level: str = "entity"
    unit: str | None = None
    evidence_required: bool = False
    guidance: str = ""
    validation_rules: dict[str, Any] = Field(default_factory=dict)


class DisclosureUpdate(BaseModel):
    title: str
    section: str
    principle: int | None = None
    question_number: str
    classification: str
    response_type: str
    reporting_level: str
    unit: str | None = None
    evidence_required: bool = False
    guidance: str = ""
    validation_rules: dict[str, Any] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    to_status: str
    comment: str | None = None


class CommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=4000)


class EvidenceCreate(BaseModel):
    submission_id: str | None = None
    organization_id: str
    financial_year: str
    file_name: str
    document_type: str


class FindingCreate(BaseModel):
    submission_id: str
    severity: str
    title: str
    owner: str
    due_date: str | None = None


class JobCreate(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)
