import os
from pathlib import Path

TEST_DB = Path("./test_brsr_nexus.db")
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["DATABASE_URL"] = "sqlite:///./test_brsr_nexus.db"
os.environ["STORAGE_ROOT"] = "./test_evidence"

from fastapi.testclient import TestClient
from app.main import app

ADMIN = {"X-Demo-User": "admin"}
OWNER = {"X-Demo-User": "owner"}
REVIEWER = {"X-Demo-User": "reviewer"}


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["version"] == "3.0.0"


def test_seeded_catalogue_cycles_and_assignments():
    with TestClient(app) as client:
        disclosures = client.get("/api/v1/disclosures", headers=ADMIN)
        cycles = client.get("/api/v1/reporting-cycles", headers=ADMIN)
        assignments = client.get("/api/v1/assignments", headers=ADMIN)
        assert disclosures.status_code == 200 and len(disclosures.json()) >= 20
        assert cycles.status_code == 200 and len(cycles.json()) >= 1
        assert assignments.status_code == 200 and len(assignments.json()) >= 20


def test_disclosure_specific_schema_and_structured_tables():
    with TestClient(app) as client:
        disclosure = client.get("/api/v1/disclosures/P6-E1", headers=ADMIN)
        schema = disclosure.json()["form_schema"]
        energy = next(field for field in schema if field["key"] == "energy")
        assert energy["type"] == "table"
        assert {"metric", "current_year", "previous_year"}.issubset({column["key"] for column in energy["columns"]})
        created = client.post("/api/v1/submissions", headers=OWNER, json={
            "disclosure_id": "P6-E1", "organization_id": "DELTA", "financial_year": "2025-26",
            "value": {"energy": [{"metric": "Renewable electricity", "unit": "GJ", "current_year": 10, "previous_year": 8}], "energy_methodology": "Metered consumption converted to GJ."},
            "owner": "Kabir — Project Owner", "source_method": "manual"
        })
        assert created.status_code == 201
        assert created.json()["validation_errors"] == []

def test_required_evidence_blocks_submission_then_upload_allows_it():
    with TestClient(app) as client:
        created = client.post("/api/v1/submissions", headers=OWNER, json={
            "disclosure_id": "P6-E8", "organization_id": "DELTA", "financial_year": "2025-26",
            "value": {"waste_generation": [{"metric": "Plastic waste", "unit": "tonnes", "current_year": 12, "previous_year": 10}], "waste_treatment": [{"route": "Recycled", "current_year": 12, "previous_year": 10}], "waste_methodology": "Weighbridge records."},
            "owner": "Kabir — Project Owner", "source_method": "manual"
        })
        assert created.status_code == 201
        submission_id = created.json()["id"]
        blocked = client.post(f"/api/v1/workflow/{submission_id}/transition", headers=OWNER, json={"to_status": "submitted"})
        assert blocked.status_code == 422
        uploaded = client.post(
            "/api/v1/evidence/upload",
            headers=OWNER,
            data={"submission_id": submission_id, "organization_id": "DELTA", "financial_year": "2025-26", "document_type": "calculation_workbook"},
            files={"file": ("waste-register.csv", b"type,tonnes\nrecovered,8\ndisposed,4\n", "text/csv")},
        )
        assert uploaded.status_code == 201
        assert len(uploaded.json()["evidence"]["checksum"]) == 64
        submitted = client.post(f"/api/v1/workflow/{submission_id}/transition", headers=OWNER, json={"to_status": "submitted", "comment": "Evidence attached"})
        assert submitted.status_code == 200
        assert submitted.json()["status"] == "submitted"


def test_request_changes_requires_comment_and_is_audited():
    with TestClient(app) as client:
        rows = client.get("/api/v1/submissions", headers=REVIEWER).json()
        submitted = next(row for row in rows if row["status"] == "submitted")
        missing = client.post(f'/api/v1/workflow/{submitted["id"]}/transition', headers=REVIEWER, json={"to_status": "changes_requested"})
        assert missing.status_code == 422
        returned = client.post(f'/api/v1/workflow/{submitted["id"]}/transition', headers=REVIEWER, json={"to_status": "changes_requested", "comment": "Clarify the calculation basis"})
        assert returned.status_code == 200
        comments = client.get(f'/api/v1/submissions/{submitted["id"]}/comments', headers=REVIEWER).json()
        assert any("calculation basis" in row["body"] for row in comments)
        audit = client.get("/api/v1/audit?entity_type=submission", headers=ADMIN).json()
        assert any(row["action"] == "status_changes_requested" for row in audit)


def test_owner_cannot_approve():
    with TestClient(app) as client:
        rows = client.get("/api/v1/submissions", headers=OWNER).json()
        target = rows[0]
        response = client.post(f'/api/v1/workflow/{target["id"]}/transition', json={"to_status": "approved"}, headers=OWNER)
        assert response.status_code == 403


def test_consolidation_preview_and_exports():
    with TestClient(app) as client:
        consolidation = client.get("/api/v1/consolidation", headers=ADMIN)
        preview = client.get("/api/v1/reports/preview", headers=ADMIN)
        excel = client.get("/api/v1/reports/export.xlsx", headers=ADMIN)
        pdf = client.get("/api/v1/reports/export.pdf", headers=ADMIN)
        assert consolidation.status_code == 200
        assert consolidation.json()["approved_inputs"] >= 1
        assert preview.status_code == 200 and preview.json()["total_disclosures"] >= 20
        assert excel.status_code == 200 and excel.content[:2] == b"PK"
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
