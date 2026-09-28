# BRSR Nexus

A governed ESG reporting platform for the BPUT Hackathon problem statement, built with Next.js, FastAPI, PostgreSQL, and Docker Compose.

## V3.0 statutory structure milestone

This release adds an L&T-report-inspired statutory information architecture while retaining the governed source-to-report workflow:

- First-class Section A, B and C cards, filters and statutory report hierarchy
- Dedicated organization, governance and ESG-performance icons (without mislabelling A/B/C as E/S/G)
- Principle 1–9 organization with Essential and Leadership indicator banners
- Disclosure-specific schemas for all 23 hackathon indicators
- Repeating tables, multi-year columns, row dimensions, units, Yes/No/NA fields, notes and methodology fields
- High-value templates for workforce, grievances, policy matrices, energy, water, GHG, waste, safety, human rights, sourcing, CSR and recalls
- Structured report preview that renders regulatory questions and answer tables instead of raw JSON
- Upgraded multi-page PDF publication output and structured Excel export
- Existing draft/review/approval/locking, evidence, comments, audit and approved-only publication rules retained

The architecture supports extending the catalogue to the full BRSR question set without a destructive database reset. Existing submissions and Docker volumes are preserved; older draft values remain stored and can be migrated by opening and resaving the disclosure in its new template.

## Start or upgrade on Windows

From PowerShell in the project directory:

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker compose down
docker compose build --no-cache web
docker compose up
```

Existing database data is preserved. Docker will create the new governance tables and the `brsr_nexus_evidence` volume automatically.

Open:

- Application: http://localhost:3000
- API documentation: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health

Check service health:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:8000/api/v1/health
```

## Demo workflow

1. Select **ESG Administrator** to manage organizations, reporting cycles, disclosures, and assignments.
2. Select **Project Data Owner** to open an assigned disclosure, save a valid draft, and upload evidence.
3. Submit the response for review.
4. Select **Functional Reviewer** to inspect the response, add a comment, request a correction, or approve it.
5. Select **Approver** to lock an approved response.
6. Inspect **Evidence vault**, **Consolidation**, **Reports**, and **Audit trail**.

## Evidence storage

Evidence files are stored in a dedicated Docker volume and their metadata is stored in PostgreSQL. Supported file types are PDF, Excel, CSV, PNG/JPEG, and Word. The default maximum file size is 20 MB.

For production, replace the local-volume adapter with S3-compatible object storage, signed URLs, malware scanning, encryption controls, backup, and retention policies.

## Product rule

Only approved or locked structured submissions enter consolidation and report output. Required evidence and validation issues block submission. AI output, when added later, must remain a cited draft until a human accepts it.

## Current limitations

Not yet implemented end to end:

- Excel/CSV import execution and row-level correction
- PDF/OCR parsing and malware scanning
- Advanced unit conversion, emission-factor, applicability, and elimination engines
- Notification and escalation workers
- Assurance sampling UI
- Cryptographically locked report snapshots
- Real permission-constrained RAG/vector retrieval
- Enterprise SSO and production-grade organization scoping

See `docs/IMPLEMENTATION_STATUS.md` for detailed maturity and verification steps.
