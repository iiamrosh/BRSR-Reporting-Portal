# V2.1 governance milestone status

## Working end-to-end

- Docker Compose topology for Next.js, FastAPI, PostgreSQL, and a persistent evidence volume
- PostgreSQL-backed domain models with idempotent development seeding
- Versioned supplied-Annexure baseline with 23 representative disclosures
- Unified Disclosure Workspace combining catalogue, assignments, collection, search, and filters
- Disclosure create, edit, and archive controls with permission checks and audit events
- Assignment creation, editing API, protected deletion, ownership, review chain, and due dates
- MEIL-like group/entity/project hierarchy and reporting cycles
- Demo-user RBAC for administrator, coordinator, data owner, reviewer, approver, and assurance
- Guided response forms for all seeded disclosures
- Exact disclosure-specific schemas for all 23 seeded indicators, with reconciliation for energy, water, GHG, waste, safety, training, complaints, sustainable sourcing, MSME sourcing, and recalls
- Draft, validation, evidence, submit, comment, return, resubmit, approve, and lock controls
- Required-evidence gate before submission or approval
- Binary evidence storage with file restrictions, SHA-256 checksums, version metadata, download, and persistent Docker volume
- Submission discussion and immutable audit timeline
- Approved/locked-only consolidation with source submission lineage
- BRSR report preview and downloadable PDF/XLSX exports
- Live evidence vault, consolidation, report, and audit workspaces
- API tests covering seeding, schemas, reconciliation, evidence gates, comments, RBAC, audit, consolidation, and exports

## Important boundaries

- Evidence uses a persistent local Docker volume, not cloud object storage or signed URLs.
- Consolidation sums approved numeric source fields but does not yet implement complex elimination rules or unit conversion.
- PDF/XLSX exports are controlled reporting previews, not a pixel-identical regulatory filing template or cryptographically signed snapshot.
- Existing PostgreSQL tables are preserved. New governance tables are added automatically at startup.

## Still deferred

- Executable Excel/CSV import mapping and row-level correction workflow
- PDF parsing, OCR, malware scanning, and authorized vector retrieval
- Full applicability/rule builder and reusable metric registry
- Advanced unit conversions, emission factors, boundary eliminations, and double-count detection
- Notification and escalation workers
- Assurance sampling and finding-closure UI
- Signed/locked report snapshots and a full report lineage graph
- Enterprise SSO and production organization-scoped authorization
- Production storage adapter, backup, retention, observability, and deployment hardening

## Recommended verification

1. Rebuild all containers with `docker compose up --build`.
2. Open the Disclosure Workspace and verify search/filter/create/edit/archive permissions.
3. As Data Owner, create a valid draft and upload evidence.
4. Submit it, return it with a reviewer comment, correct it, approve it, and lock it.
5. Inspect the submission timeline and global audit trail.
6. Open Consolidation and confirm only approved/locked records appear.
7. Open Reports and download both PDF and Excel outputs.
8. Restart the stack and confirm database records and evidence files persist.
