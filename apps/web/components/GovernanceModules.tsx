"use client";

import { useEffect, useMemo, useState } from "react";
import {
  apiGet,
  AuditEvent,
  Consolidation,
  Disclosure,
  downloadUrl,
  Evidence,
  Organization,
  ReportPreview,
  Submission,
} from "@/lib/api";
import { useDemoUser } from "./DemoUserContext";
import { SectionIcon, sectionMeta } from "./BRSRSection";
import { StatutoryResponse } from "./StatutoryResponse";

function Header({ eyebrow, title, description, action }: { eyebrow:string; title:string; description:string; action?:React.ReactNode }) {
  return <section className="hero compact"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action && <div className="hero-actions">{action}</div>}</section>;
}

function Loading({ text = "Loading live workspace…" }: { text?:string }) { return <div className="loading-panel">{text}</div>; }
function Failure({ message }: { message:string }) { return <div className="error-panel"><b>Unable to load this workspace</b><span>{message}</span></div>; }
function Status({ value }: { value:string }) { return <span className={`status-chip ${value}`}>{value.replaceAll("_", " ")}</span>; }

export function EvidenceVaultLive() {
  const { userKey } = useDemoUser();
  const [rows, setRows] = useState<Evidence[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [disclosures, setDisclosures] = useState<Disclosure[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { setLoading(true); Promise.all([apiGet<Evidence[]>("/evidence"), apiGet<Submission[]>("/submissions"), apiGet<Disclosure[]>("/disclosures"), apiGet<Organization[]>("/organizations")]).then(([e,s,d,o]) => {setRows(e);setSubmissions(s);setDisclosures(d);setOrgs(o);}).catch((reason) => setError(reason.message)).finally(() => setLoading(false)); }, [userKey]);
  const filtered = useMemo(() => rows.filter((row) => `${row.file_name} ${row.document_type} ${row.checksum}`.toLowerCase().includes(query.toLowerCase())), [rows, query]);
  return <main><Header eyebrow="Provenance & document control" title="Evidence vault" description="Stored source files are checksum-protected, versioned, linked to submissions, and retained in a dedicated Docker volume." />
    <div className="toolbar"><input className="search-input" placeholder="Search filename, type, or checksum…" value={query} onChange={(event) => setQuery(event.target.value)} /><span>{filtered.length} stored files</span></div>
    {loading ? <Loading /> : error ? <Failure message={error} /> : <article className="panel table-panel"><div className="table-scroll"><table className="data-table"><thead><tr><th>Evidence</th><th>Disclosure</th><th>Organization</th><th>Integrity</th><th>Stored</th><th></th></tr></thead><tbody>{filtered.map((row) => {const submission=submissions.find((item) => item.id===row.submission_id);return <tr key={row.id}><td><b>{row.file_name}</b><small>{row.document_type} · {row.processing_status}</small></td><td><b>{submission?.disclosure_id ?? "Unlinked"}</b><small>{disclosures.find((item) => item.id===submission?.disclosure_id)?.title}</small></td><td>{orgs.find((item) => item.id===row.organization_id)?.name ?? row.organization_id}</td><td><code title={row.checksum ?? ""}>{row.checksum ? `SHA-256 ${row.checksum.slice(0,12)}…` : "Pending"}</code></td><td>{new Date(row.created_at).toLocaleString()}</td><td><a className="button secondary small" href={downloadUrl(`/evidence/${row.id}/download`)}>Download</a></td></tr>;})}</tbody></table></div></article>}
  </main>;
}

export function ConsolidationLive() {
  const { userKey } = useDemoUser();
  const [data, setData] = useState<Consolidation | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { apiGet<Consolidation>("/consolidation").then(setData).catch((reason) => setError(reason.message)); }, [userKey]);
  return <main><Header eyebrow="Approved-data boundary" title="Consolidation" description="Only approved and locked numeric source fields are rolled up. Every result retains its organization and submission lineage." />
    {error ? <Failure message={error} /> : !data ? <Loading /> : <><section className="metrics three"><article className="metric-card green"><p>Approved inputs</p><strong>{data.approved_inputs}</strong><small>Eligible for roll-up</small></article><article className="metric-card"><p>Consolidated disclosures</p><strong>{data.rows.length}</strong><small>With approved numeric data</small></article><article className="metric-card amber"><p>Boundary</p><strong>{data.financial_year}</strong><small>Current reporting year</small></article></section><div className="method-note">{data.method}</div><article className="panel table-panel"><div className="table-scroll"><table className="data-table"><thead><tr><th>Disclosure</th><th>Organizations</th><th>Consolidated metrics</th><th>Lineage</th></tr></thead><tbody>{data.rows.map((row) => <tr key={row.disclosure_id}><td><b>{row.disclosure_id}</b><small>{row.title}</small></td><td>{row.organization_ids.join(", ")}</td><td><div className="metric-values">{Object.entries(row.metrics).map(([key,value]) => <span key={key}><small>{key.replaceAll("_"," ")}</small><b>{value.toLocaleString()} {row.unit ?? ""}</b></span>)}</div></td><td><b>{row.submission_count} source record{row.submission_count===1?"":"s"}</b><small>{row.source_submission_ids.map((id) => id.slice(0,8)).join(", ")}</small></td></tr>)}</tbody></table></div></article></>}
  </main>;
}

export function ReportsLive() {
  const { userKey } = useDemoUser();
  const [data, setData] = useState<ReportPreview | null>(null);
  const [error, setError] = useState("");
  const [section, setSection] = useState("");
  useEffect(() => { apiGet<ReportPreview>("/reports/preview").then(setData).catch((reason) => setError(reason.message)); }, [userKey]);
  // Treat the API payload as untrusted at this boundary. This keeps a legacy
  // or partially migrated report response from taking down the whole page.
  const reportSections = Array.isArray(data?.sections) ? data.sections : [];
  const visible = reportSections.filter((row) => !section || row.section === section);
  const grouped=(["A","B","C"] as const).map(code=>({code,rows:visible.filter(row=>row.section===code)})).filter(group=>group.rows.length);
  return <main><Header eyebrow="Controlled statutory publication" title="BRSR report preview" description="Review the statutory Section A–C hierarchy, question-specific tables and approved source responses before publication." action={<><a className="button secondary" href={downloadUrl("/reports/export.xlsx")}>Export Excel</a><a className="button primary" href={downloadUrl("/reports/export.pdf")}>Export PDF</a></>} />
    {error ? <Failure message={error} /> : !data ? <Loading /> : <><section className="metrics three"><article className="metric-card"><p>Report readiness</p><strong>{data.readiness_percent}%</strong><small>{data.ready_disclosures} of {data.total_disclosures} disclosures</small></article><article className="metric-card green"><p>Publication rule</p><strong>Approved</strong><small>Validation-complete with required evidence</small></article><article className="metric-card amber"><p>Financial year</p><strong>{data.financial_year}</strong><small>{data.generated_from}</small></article></section><div className="toolbar"><select value={section} onChange={(event) => setSection(event.target.value)}><option value="">All statutory sections</option><option value="A">Section A · General Disclosures</option><option value="B">Section B · Management & Process</option><option value="C">Section C · Principle-wise Performance</option></select><span>{visible.length} disclosures</span></div><article className="report-sheet statutory"><div className="report-cover"><span>Business Responsibility and Sustainability Report</span><h2>MEIL Demo Group</h2><p>Financial year {data.financial_year}</p><small>Prepared through BRSR Nexus · governed source-to-report traceability</small></div>{grouped.map(group=>{const meta=sectionMeta[group.code];let previousPrinciple:number|null=null;return <section className="report-section" key={group.code}><header className={`publication-section-head section-${group.code.toLowerCase()}`}><span className="section-icon"><SectionIcon section={group.code}/></span><div><small>SECTION {group.code}</small><h2>{meta.title}</h2><p>{meta.description}</p></div></header>{group.rows.map(row=>{const showPrinciple=group.code==="C"&&row.principle!==previousPrinciple;if(showPrinciple)previousPrinciple=row.principle;const responses=Array.isArray(row.responses)?row.responses:[];return <div key={row.id}>{showPrinciple&&<div className="principle-banner"><span>Principle {row.principle}</span><b>{row.classification === "leadership" ? "Leadership indicators" : "Essential indicators"}</b></div>}<section className="report-row"><div className="report-question"><span>{row.question_number}</span><div><small>{row.classification} indicator</small><h3>{row.title}</h3></div><Status value={row.status}/></div>{responses.length?responses.map(response=><article className="approved-response" key={response.submission_id}><div className="response-source"><b>{response.organization_id}</b><small>{response.status} · Data quality {response.quality_score}/100</small></div><StatutoryResponse schema={row.form_schema} value={response.value}/></article>):<p className="report-empty">No approved, validation-complete source response is available for publication.</p>}</section></div>})}</section>})}<footer className="report-footer-note">Independent assurance and the BRSR Core attribute mapping are generated from eligible assured disclosures and retained evidence.</footer></article></>}
  </main>;
}

export function AuditLive() {
  const { userKey } = useDemoUser();
  const [rows, setRows] = useState<AuditEvent[]>([]);
  const [query, setQuery] = useState("");
  const [type, setType] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { apiGet<AuditEvent[]>("/audit").then(setRows).catch((reason) => setError(reason.message)); }, [userKey]);
  const filtered = rows.filter((row) => (!type || row.entity_type===type) && (!query || `${row.actor} ${row.entity_id} ${row.action}`.toLowerCase().includes(query.toLowerCase())));
  return <main><Header eyebrow="Immutable accountability" title="Audit trail" description="Search creation, editing, evidence, comments, workflow, assignments, and configuration events across the reporting cycle." />
    <div className="toolbar"><input className="search-input" placeholder="Search actor, record, or action…" value={query} onChange={(event) => setQuery(event.target.value)} /><select value={type} onChange={(event) => setType(event.target.value)}><option value="">All record types</option>{["submission","evidence","assignment","disclosure","organization","reporting_cycle","assurance_finding"].map((value) => <option key={value} value={value}>{value.replaceAll("_"," ")}</option>)}</select><span>{filtered.length} events</span></div>
    {error ? <Failure message={error} /> : <article className="panel timeline-panel">{filtered.length ? filtered.map((row) => <div className="audit-row" key={row.id}><span className="audit-icon">{row.action.includes("created") ? "+" : row.action.includes("uploaded") ? "↑" : "✓"}</span><div><b>{row.action.replaceAll("_"," ")}</b><p>{row.entity_type.replaceAll("_"," ")} · {row.entity_id}</p><small>{row.actor} · {row.actor_role.replaceAll("_"," ")}</small></div><time>{new Date(row.created_at).toLocaleString()}</time></div>) : <div className="empty-state"><h3>No matching audit events</h3><p>Events appear as users create, edit, upload, comment, review, approve, and lock records.</p></div>}</article>}
  </main>;
}
