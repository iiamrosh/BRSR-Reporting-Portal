# Product blueprint

## Mission

Turn BRSR reporting from an annual spreadsheet exercise into a governed source-to-report operating system for group, company, business-unit, project, and site data.

## Modules

1. Command center — completion, quality, risk, due dates, bottlenecks.
2. Organization — hierarchy, reporting boundaries, ownership, locations.
3. Framework library — versioned Sections A/B/C, NGRBC principles, Essential/Leadership/Core classifications.
4. Assignments — owners, reviewers, approvers, frequency, due dates.
5. Collection workspace — forms, tables, narratives, evidence, prior year.
6. Imports — Excel/CSV mapping, validation, row-level errors, reconciliation.
7. Metric registry — collect once/use many, units, formulas, lineage.
8. Review workflow — comments, correction, approval, locking, exceptions.
9. Evidence vault — provenance, checksum, access, expiry, page references.
10. Assurance — samples, evidence requests, findings, responses, closure.
11. Consolidation — boundary-aware rollups and double-count prevention.
12. Reports — BRSR preview, snapshots, PDF/Excel adapters.
13. Audit — immutable history and source-to-report lineage.
14. Administration — users, roles, templates, rules, notifications.

## Improvements beyond the original plan

- Reusable metric registry to eliminate duplicate entry.
- Data-quality score using completeness, evidence, timeliness, reconciliation, and anomaly signals.
- Monthly project reporting packs feeding annual BRSR automatically.
- Framework-diff and answer migration between reporting years.
- Configurable rule engine instead of hard-coded validations.
- Evidence expiry and assurance readiness indicators.
- Exception workflow for post-lock corrections.
- Data lineage graph from report number to source record.
- Offline-friendly site capture and resumable uploads (future PWA adapter).
- Notification/escalation policies and SLA tracking.
- Scenario and target tracking for energy, water, emissions, and safety.
- Consent-aware AI assistant restricted to authorized entity/year evidence.

## Delivery phases

- Phase 1: all-module scaffold and vertical contracts.
- Phase 2: persistence, live UI, collection workflow, 20–30 indicators.
- Phase 3: calculations, imports, consolidation, report preview.
- Phase 4: evidence parsing, RAG, assurance, locked snapshots.
- Phase 5: enterprise SSO, integrations, hardening, deployment.
