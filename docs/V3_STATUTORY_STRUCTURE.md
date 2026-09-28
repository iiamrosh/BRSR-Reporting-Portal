# V3 statutory BRSR structure

## Scope

V3 implements the statutory Section A/B/C hierarchy and a richer schema-driven collection engine for the 23 representative hackathon disclosures. The design is informed by the supplied L&T BRSR report but uses BRSR Nexus / MEIL-neutral identity and no L&T branding or values.

## Form engine

Supported templates include text, narrative, numeric/unit-aware fields, Yes/No/Not applicable, select inputs, repeating rows, fixed regulatory rows, multi-year columns, methodology, scope, variance and restatement notes. Structured values continue to be stored in the existing Submission JSON column, so no destructive database migration is required.

## Compatibility

Existing evidence, comments, workflow events, audit records and Docker volumes are untouched. Legacy drafts may show validation requirements under their new schema until the owner opens and resaves them. Approved publication remains restricted to validation-complete records with required evidence.

## Verification

- Python source compilation: completed in the release sandbox.
- 23 schema definitions and representative energy validation: completed.
- Desktop visual QA of the section cards and structured table: completed at 1440×900 with no overflow or overlap.
- Full FastAPI/Next.js dependency-backed tests could not run in the offline sandbox because project dependencies were not installed. Run the Docker checks below.

```powershell
docker compose build --no-cache web
docker compose up
docker compose exec api pytest -q
```
