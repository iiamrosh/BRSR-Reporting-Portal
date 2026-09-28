from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Assignment, Disclosure, Framework, Organization, ReportingCycle, Submission

DISCLOSURES = [
    ("A-14", "A", None, "14", "Details of business activities", "essential", "table", "entity", None, True),
    ("A-15", "A", None, "15", "Products sold or services offered", "essential", "table", "entity", "% turnover", True),
    ("A-18", "A", None, "18", "Employees and workers", "essential", "table", "entity", "count", True),
    ("A-20", "A", None, "20", "Turnover rate for permanent employees and workers", "essential", "table", "entity", "%", True),
    ("A-23", "A", None, "23", "Stakeholder grievance redressal mechanism", "essential", "narrative", "entity", None, True),
    ("A-24", "A", None, "24", "Material sustainability risks and opportunities", "essential", "table", "entity", None, True),
    ("B-05", "B", None, "5–6", "Commitments, goals, targets, and performance", "essential", "table", "entity", None, True),
    ("B-08", "B", None, "8", "Authority for policy implementation and oversight", "essential", "narrative", "entity", None, True),
    ("P1-E2", "C", 1, "2", "Material fines, penalties, and settlements", "essential", "table", "entity", "INR", True),
    ("P2-E2", "C", 2, "2", "Sustainable sourcing", "essential", "percentage", "entity", "%", True),
    ("P3-E5", "C", 3, "5", "Parental leave return and retention", "essential", "table", "entity", "%", True),
    ("P3-E11", "C", 3, "11", "Safety incidents and LTIFR", "essential", "table", "project", "rate", True),
    ("P4-E2", "C", 4, "2", "Key stakeholder groups", "essential", "table", "entity", None, True),
    ("P5-E1", "C", 5, "1", "Human-rights training", "essential", "table", "entity", "%", True),
    ("P5-E6", "C", 5, "6", "Human-rights complaints", "essential", "table", "entity", "count", True),
    ("P6-E1", "C", 6, "1", "Energy consumption and intensity", "essential", "table", "project", "GJ", True),
    ("P6-E3", "C", 6, "3", "Water withdrawal, consumption, and intensity", "essential", "table", "project", "KL", True),
    ("P6-E6", "C", 6, "6", "Scope 1 and Scope 2 GHG emissions", "essential", "table", "entity", "tCO2e", True),
    ("P6-E8", "C", 6, "8", "Waste generated, recovered, and disposed", "essential", "table", "project", "tonnes", True),
    ("P7-L1", "C", 7, "L1", "Public policy positions advocated", "leadership", "table", "entity", None, False),
    ("P8-E4", "C", 8, "4", "Inputs sourced from MSMEs or small producers", "essential", "percentage", "entity", "%", True),
    ("P8-L6", "C", 8, "L6", "Beneficiaries of CSR projects", "leadership", "table", "project", "count", True),
    ("P9-E4", "C", 9, "4", "Product recalls due to safety issues", "essential", "table", "entity", "count", True),
]

def seed(db: Session) -> None:
    framework = db.scalar(select(Framework).where(Framework.version == "ANNEXURE-BASELINE-1"))
    if not framework:
        framework = Framework(name="SEBI BRSR Annexure baseline", version="ANNEXURE-BASELINE-1", baseline="Supplied Annexure II", status="active")
        db.add(framework)
        db.flush()
    orgs = [
        ("MEIL", None, "MEIL Demo Group", "MEIL", "group"),
        ("MEIL-INFRA", "MEIL", "MEIL Infrastructure", "MEIL-INFRA", "entity"),
        ("MEIL-ENERGY", "MEIL", "MEIL Energy", "MEIL-ENERGY", "entity"),
        ("ATLAS", "MEIL-INFRA", "Project Atlas", "ATLAS", "project"),
        ("DELTA", "MEIL-INFRA", "Project Delta", "DELTA", "project"),
    ]
    for organization_id, parent_id, name, code, organization_type in orgs:
        if not db.get(Organization, organization_id):
            db.add(Organization(id=organization_id, parent_id=parent_id, name=name, code=code, organization_type=organization_type))
    for item in DISCLOSURES:
        did, section, principle, qno, title, classification, response_type, level, unit, evidence = item
        if not db.get(Disclosure, did):
            db.add(Disclosure(id=did, framework_id=framework.id, section=section, principle=principle, question_number=qno, title=title, classification=classification, response_type=response_type, reporting_level=level, unit=unit, evidence_required=evidence, guidance="Configured from the supplied SEBI BRSR guidance Annexure.", validation_rules={"required": True}))
    db.flush()
    cycle = db.get(ReportingCycle, "FY25-26")
    if not cycle:
        cycle = ReportingCycle(id="FY25-26", framework_id=framework.id, name="FY 2025–26 BRSR", financial_year="2025-26", boundary_type="consolidated", status="open", starts_on="2025-04-01", ends_on="2026-03-31")
        db.add(cycle)
        db.flush()
    project_disclosures = {"P3-E11", "P6-E1", "P6-E3", "P6-E8", "P8-L6"}
    for item in DISCLOSURES:
        disclosure_id = item[0]
        organization_id = "ATLAS" if disclosure_id in project_disclosures else "MEIL-INFRA"
        existing = db.scalar(select(Assignment).where(Assignment.cycle_id == cycle.id, Assignment.disclosure_id == disclosure_id, Assignment.organization_id == organization_id))
        if not existing:
            db.add(Assignment(cycle_id=cycle.id, disclosure_id=disclosure_id, organization_id=organization_id, owner_user_id="owner", reviewer_user_id="reviewer", approver_user_id="approver", due_date="2026-02-28", frequency="annual"))
    db.flush()
    if not db.scalar(select(Submission.id).limit(1)):
        db.add_all([
            Submission(disclosure_id="P6-E1", organization_id="ATLAS", financial_year="2025-26", value={"total": 128400, "unit": "kWh"}, status="draft", owner="Kabir — Project Owner", reviewer="Meera — EHS Reviewer", quality_score=40, validation_errors=["Response must be migrated to the disclosure-specific schema", "Supporting evidence is required"]),
            Submission(disclosure_id="P6-E3", organization_id="ATLAS", financial_year="2025-26", value={"withdrawal": 18200, "unit": "KL"}, status="draft", owner="Kabir — Project Owner", quality_score=40, validation_errors=["Response must be migrated to the disclosure-specific schema", "Supporting evidence is required"]),
            Submission(disclosure_id="P3-E11", organization_id="DELTA", financial_year="2025-26", value={"ltifr": 0.38}, status="changes_requested", owner="Kabir — Project Owner", reviewer="Meera — EHS Reviewer", quality_score=40, validation_errors=["Complete hours worked and injury counts", "Supporting evidence is required"]),
        ])
    approved_demo = db.scalar(select(Submission).where(Submission.disclosure_id == "P7-L1", Submission.organization_id == "MEIL-INFRA", Submission.financial_year == "2025-26"))
    if not approved_demo:
        db.add(Submission(disclosure_id="P7-L1", organization_id="MEIL-INFRA", financial_year="2025-26", value={"policy_positions": [{"issue": "No material public-policy positions were advocated during the reporting year.", "method": "Not applicable", "association": "None reported", "board_review": "Annual", "alignment": "The entity monitors alignment with the NGRBC principles."}], "governance_alignment": "The entity monitors alignment with the NGRBC principles."}, status="approved", owner="Diya — Entity Coordinator", reviewer="Meera — EHS Reviewer", quality_score=100))
    db.commit()
