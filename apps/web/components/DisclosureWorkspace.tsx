"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  apiDelete,
  apiGet,
  apiPost,
  apiPut,
  Assignment,
  Cycle,
  Disclosure,
  Framework,
  Organization,
  Submission,
} from "@/lib/api";
import { useDemoUser } from "./DemoUserContext";
import { SectionBadge, SectionIcon, sectionMeta } from "./BRSRSection";

const owners = [
  { id: "owner", label: "Project Data Owner" },
  { id: "coordinator", label: "Entity Coordinator" },
  { id: "admin", label: "ESG Administrator" },
];

function Status({ value }: { value: string }) {
  return <span className={`status-chip ${value}`}>{value.replaceAll("_", " ")}</span>;
}

export function DisclosureWorkspace() {
  const { userKey } = useDemoUser();
  const [disclosures, setDisclosures] = useState<Disclosure[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [query, setQuery] = useState("");
  const [section, setSection] = useState("");
  const [principle, setPrinciple] = useState("");
  const [classification, setClassification] = useState("");
  const [workflow, setWorkflow] = useState("");
  const [organization, setOrganization] = useState("");
  const [owner, setOwner] = useState(userKey === "owner" ? "owner" : "");
  const [editor, setEditor] = useState<Disclosure | "new" | null>(null);
  const [assigning, setAssigning] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [d, a, o, c, f, s] = await Promise.all([
        apiGet<Disclosure[]>("/disclosures"),
        apiGet<Assignment[]>("/assignments"),
        apiGet<Organization[]>("/organizations"),
        apiGet<Cycle[]>("/reporting-cycles"),
        apiGet<Framework[]>("/frameworks"),
        apiGet<Submission[]>("/submissions"),
      ]);
      setDisclosures(d);
      setAssignments(a);
      setOrgs(o);
      setCycles(c);
      setFrameworks(f);
      setSubmissions(s);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setOwner(userKey === "owner" ? "owner" : "");
    load();
  }, [userKey]);

  const assignmentFor = (disclosureId: string) => assignments.filter((row) => row.disclosure_id === disclosureId);
  const submissionFor = (assignment: Assignment) => submissions.find((row) => row.disclosure_id === assignment.disclosure_id && row.organization_id === assignment.organization_id);
  const statusesFor = (disclosureId: string) => assignmentFor(disclosureId).map((row) => submissionFor(row)?.status ?? "not_started");

  const filtered = useMemo(() => disclosures.filter((row) => {
    const related = assignmentFor(row.id);
    const statuses = statusesFor(row.id);
    const matchesQuery = !query || `${row.id} ${row.title}`.toLowerCase().includes(query.toLowerCase());
    return matchesQuery
      && (!section || row.section === section)
      && (!principle || String(row.principle ?? "") === principle)
      && (!classification || row.classification === classification)
      && (!workflow || statuses.includes(workflow))
      && (!organization || related.some((item) => item.organization_id === organization))
      && (!owner || related.some((item) => item.owner_user_id === owner));
  }), [disclosures, assignments, submissions, query, section, principle, classification, workflow, organization, owner]);

  const saveDisclosure = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = {
      framework_id: form.get("framework_id"),
      section: form.get("section"),
      principle: form.get("principle") ? Number(form.get("principle")) : null,
      question_number: form.get("question_number"),
      title: form.get("title"),
      classification: form.get("classification"),
      response_type: form.get("response_type"),
      reporting_level: form.get("reporting_level"),
      unit: form.get("unit") || null,
      evidence_required: form.get("evidence_required") === "on",
      guidance: form.get("guidance"),
      validation_rules: { required: true },
    };
    try {
      if (editor === "new") {
        await apiPost("/disclosures", { id: form.get("id"), ...payload });
        setMessage("Disclosure created.");
      } else if (editor) {
        const { framework_id: _framework, ...update } = payload;
        await apiPut(`/disclosures/${editor.id}`, update);
        setMessage("Disclosure updated.");
      }
      setEditor(null);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  };

  const createAssignment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiPost("/assignments", {
        cycle_id: form.get("cycle_id"),
        disclosure_id: form.get("disclosure_id"),
        organization_id: form.get("organization_id"),
        owner_user_id: form.get("owner_user_id"),
        reviewer_user_id: "reviewer",
        approver_user_id: "approver",
        due_date: form.get("due_date"),
        frequency: form.get("frequency"),
      });
      setAssigning(null);
      setMessage("Assignment created.");
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  };

  const archive = async (row: Disclosure) => {
    if (!window.confirm(`Archive ${row.id}? Existing submissions and audit records will be preserved.`)) return;
    try {
      await apiDelete(`/disclosures/${row.id}`);
      setMessage(`${row.id} archived.`);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  };

  const defaults = editor && editor !== "new" ? editor : null;
  return <main>
    <section className="hero compact">
      <div>
        <span className="eyebrow">Catalogue · assignments · collection</span>
        <h1>Disclosure workspace</h1>
        <p>Search the versioned catalogue, route ownership, open responses, and monitor workflow from one governed workspace.</p>
      </div>
      <div className="hero-actions">
        <button className="button secondary" onClick={() => setEditor("new")}>New disclosure</button>
        <button className="button primary" onClick={() => setAssigning("")}>New assignment</button>
      </div>
    </section>

    <section className="section-overview" aria-label="Statutory BRSR sections">{(["A","B","C"] as const).map(code=>{const meta=sectionMeta[code];const count=disclosures.filter(row=>row.section===code).length;return <button type="button" key={code} className={`section-card section-${code.toLowerCase()} ${section===code?"selected":""}`} onClick={()=>setSection(section===code?"":code)}><span className="section-icon"><SectionIcon section={code}/></span><span><small>Section {code}</small><b>{meta.title}</b><p>{meta.description}</p></span><strong>{count}</strong></button>})}</section>

    <section className="metrics three compact-metrics">
      <article className="metric-card"><p>Active disclosures</p><strong>{disclosures.length}</strong><small>Current framework baseline</small></article>
      <article className="metric-card green"><p>Assignments</p><strong>{assignments.length}</strong><small>Across {new Set(assignments.map((row) => row.organization_id)).size} organizations</small></article>
      <article className="metric-card amber"><p>Awaiting action</p><strong>{assignments.filter((row) => !["approved", "locked"].includes(submissionFor(row)?.status ?? "not_started")).length}</strong><small>Not started, draft, returned, or review</small></article>
    </section>

    <section className="panel filter-panel" aria-label="Disclosure filters">
      <input className="search-input" placeholder="Search by ID or disclosure title…" value={query} onChange={(event) => setQuery(event.target.value)} />
      <select value={section} onChange={(event) => setSection(event.target.value)}><option value="">All sections</option><option value="A">Section A</option><option value="B">Section B</option><option value="C">Section C</option></select>
      <select value={principle} onChange={(event) => setPrinciple(event.target.value)}><option value="">All principles</option>{[1,2,3,4,5,6,7,8,9].map((value) => <option key={value}>{value}</option>)}</select>
      <select value={classification} onChange={(event) => setClassification(event.target.value)}><option value="">All classes</option><option value="essential">Essential</option><option value="leadership">Leadership</option></select>
      <select value={workflow} onChange={(event) => setWorkflow(event.target.value)}><option value="">All statuses</option>{["not_started","draft","submitted","changes_requested","approved","locked"].map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}</select>
      <select value={organization} onChange={(event) => setOrganization(event.target.value)}><option value="">All organizations</option>{orgs.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select>
      <select value={owner} onChange={(event) => setOwner(event.target.value)}><option value="">All owners</option>{owners.map((row) => <option key={row.id} value={row.id}>{row.label}</option>)}</select>
      <button className="button ghost" onClick={() => { setQuery(""); setSection(""); setPrinciple(""); setClassification(""); setWorkflow(""); setOrganization(""); setOwner(""); }}>Clear</button>
    </section>

    {error && <div className="form-message error">{error}</div>}
    {message && <div className="form-message success">{message}</div>}
    {loading ? <div className="loading-panel">Loading disclosure workspace…</div> : <article className="panel table-panel">
      <div className="panel-heading"><div><h2>Disclosures</h2><p>{filtered.length} matching records · approved records remain protected from destructive deletion</p></div><span className="stage-badge">Live governance</span></div>
      <div className="table-scroll"><table className="data-table disclosure-table">
        <thead><tr><th>Disclosure</th><th>Classification</th><th>Assignments</th><th>Workflow</th><th>Controls</th></tr></thead>
        <tbody>{filtered.map((row) => {
          const related = assignmentFor(row.id);
          const statuses = statusesFor(row.id);
          const primary = related[0];
          return <tr key={row.id}>
            <td><div className="disclosure-title"><SectionBadge section={row.section}/><span><b>{row.id} · {row.title}</b><small>{row.principle ? `Principle ${row.principle} · ` : ""}{row.reporting_level} · {row.unit ?? "field-specific units"}</small></span></div></td>
            <td><span className="classification-tag">{row.classification}</span><small>{row.evidence_required ? "Evidence required" : "Evidence optional"}</small></td>
            <td><b>{related.length}</b><small>{related.slice(0, 2).map((item) => orgs.find((org) => org.id === item.organization_id)?.name).filter(Boolean).join(", ") || "Unassigned"}</small></td>
            <td><div className="status-stack">{Array.from(new Set(statuses)).slice(0, 3).map((status) => <Status key={status} value={status} />)}{!statuses.length && <Status value="unassigned" />}</div></td>
            <td><div className="row-actions">
              <Link className="button secondary small" href={`/workspace/collection/${row.id}${primary ? `?organization=${primary.organization_id}` : ""}`}>Open</Link>
              <button className="button ghost small" onClick={() => setAssigning(row.id)}>Assign</button>
              <button className="button ghost small" onClick={() => setEditor(row)}>Edit</button>
              <button className="button danger small" onClick={() => archive(row)}>Archive</button>
            </div></td>
          </tr>;
        })}</tbody>
      </table></div>
    </article>}

    {editor && <div className="modal-backdrop" role="presentation" onMouseDown={() => setEditor(null)}><form className="modal-card" onSubmit={saveDisclosure} onMouseDown={(event) => event.stopPropagation()}>
      <div className="panel-heading"><div><span className="eyebrow">Framework control</span><h2>{editor === "new" ? "Create disclosure" : `Edit ${editor.id}`}</h2><p>Changes are written to the immutable audit log.</p></div><button className="icon-button" type="button" onClick={() => setEditor(null)} aria-label="Close">×</button></div>
      <div className="form-grid">
        <label>Disclosure ID<input name="id" defaultValue={defaults?.id ?? ""} disabled={Boolean(defaults)} required /></label>
        <label>Framework<select name="framework_id" defaultValue={defaults?.framework_id ?? frameworks[0]?.id}>{frameworks.map((row) => <option key={row.id} value={row.id}>{row.version}</option>)}</select></label>
        <label className="span-2">Title<input name="title" defaultValue={defaults?.title ?? ""} required /></label>
        <label>Section<select name="section" defaultValue={defaults?.section ?? "C"}><option>A</option><option>B</option><option>C</option></select></label>
        <label>Principle<input name="principle" type="number" min="1" max="9" defaultValue={defaults?.principle ?? ""} /></label>
        <label>Question number<input name="question_number" defaultValue={defaults?.question_number ?? ""} required /></label>
        <label>Classification<select name="classification" defaultValue={defaults?.classification ?? "essential"}><option>essential</option><option>leadership</option></select></label>
        <label>Response type<select name="response_type" defaultValue={defaults?.response_type ?? "narrative"}><option>narrative</option><option>number</option><option>percentage</option><option>table</option></select></label>
        <label>Reporting level<select name="reporting_level" defaultValue={defaults?.reporting_level ?? "entity"}><option>group</option><option>entity</option><option>business_unit</option><option>project</option><option>site</option></select></label>
        <label>Unit<input name="unit" defaultValue={defaults?.unit ?? ""} placeholder="%, GJ, KL, count…" /></label>
        <label className="checkbox-field"><input name="evidence_required" type="checkbox" defaultChecked={defaults?.evidence_required ?? true} /> Evidence required</label>
        <label className="span-2">Guidance<textarea name="guidance" rows={4} defaultValue={defaults?.guidance ?? ""} /></label>
      </div>
      <div className="form-footer"><button className="button ghost" type="button" onClick={() => setEditor(null)}>Cancel</button><button className="button primary">{editor === "new" ? "Create disclosure" : "Save changes"}</button></div>
    </form></div>}

    {assigning !== null && <div className="modal-backdrop" role="presentation" onMouseDown={() => setAssigning(null)}><form className="modal-card compact-modal" onSubmit={createAssignment} onMouseDown={(event) => event.stopPropagation()}>
      <div className="panel-heading"><div><span className="eyebrow">Ownership</span><h2>New assignment</h2><p>Route a disclosure to an accountable owner and review chain.</p></div><button className="icon-button" type="button" onClick={() => setAssigning(null)} aria-label="Close">×</button></div>
      <div className="form-grid">
        <label className="span-2">Disclosure<select name="disclosure_id" defaultValue={assigning}>{disclosures.map((row) => <option key={row.id} value={row.id}>{row.id} — {row.title}</option>)}</select></label>
        <label>Cycle<select name="cycle_id">{cycles.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
        <label>Organization<select name="organization_id">{orgs.map((row) => <option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
        <label>Owner<select name="owner_user_id">{owners.map((row) => <option key={row.id} value={row.id}>{row.label}</option>)}</select></label>
        <label>Frequency<select name="frequency"><option>annual</option><option>quarterly</option><option>monthly</option></select></label>
        <label>Due date<input name="due_date" type="date" required /></label>
      </div>
      <div className="form-footer"><button className="button ghost" type="button" onClick={() => setAssigning(null)}>Cancel</button><button className="button primary">Create assignment</button></div>
    </form></div>}
  </main>;
}
