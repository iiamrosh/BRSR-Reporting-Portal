"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet, apiPost, AssuranceFinding, Disclosure, Organization, Submission } from "@/lib/api";
import { useDemoUser } from "./DemoUserContext";

function Status({ value }: { value:string }) {
  return <span className={`status-chip ${value}`}>{value.replaceAll("_", " ")}</span>;
}

export function AssuranceLive() {
  const { userKey } = useDemoUser();
  const [findings, setFindings] = useState<AssuranceFinding[]>([]);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [disclosures, setDisclosures] = useState<Disclosure[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [f, s, d, o] = await Promise.all([
        apiGet<AssuranceFinding[]>("/assurance/findings"),
        apiGet<Submission[]>("/submissions"),
        apiGet<Disclosure[]>("/disclosures"),
        apiGet<Organization[]>("/organizations"),
      ]);
      setFindings(f);
      setSubmissions(s);
      setDisclosures(d);
      setOrganizations(o);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [userKey]);

  const openFindings = findings.filter((item) => item.status === "open");
  const highFindings = openFindings.filter((item) => ["high", "critical"].includes(item.severity));
  const submissionLabel = (id: string) => {
    const submission = submissions.find((item) => item.id === id);
    if (!submission) return id;
    const disclosure = disclosures.find((item) => item.id === submission.disclosure_id);
    const organization = organizations.find((item) => item.id === submission.organization_id);
    return `${submission.disclosure_id} · ${organization?.name ?? submission.organization_id}${disclosure ? ` · ${disclosure.title}` : ""}`;
  };

  const createFinding = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await apiPost("/assurance/findings", {
        submission_id: form.get("submission_id"),
        severity: form.get("severity"),
        title: form.get("title"),
        owner: form.get("owner"),
        due_date: form.get("due_date") || null,
      });
      setOpen(false);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  };

  const rows = useMemo(() => findings.map((finding) => {
    const submission = submissions.find((item) => item.id === finding.submission_id);
    return { finding, submission };
  }), [findings, submissions]);

  return <main>
    <section className="hero compact">
      <div>
        <span className="eyebrow">Independent review · live findings</span>
        <h1>Assurance workspace</h1>
        <p>Select source submissions for review, record findings, assign management owners, and track remediation before publication.</p>
      </div>
      <div className="hero-actions">
        <Link className="button secondary" href="/workspace/review">Open review queue</Link>
        <button className="button primary" onClick={() => setOpen(true)}>Create finding</button>
      </div>
    </section>

    <section className="metrics three">
      <article className="metric-card"><p>Available submissions</p><strong>{submissions.length}</strong><small>Candidate source records</small></article>
      <article className="metric-card amber"><p>Open findings</p><strong>{openFindings.length}</strong><small>Management response required</small></article>
      <article className="metric-card red"><p>High-severity open</p><strong>{highFindings.length}</strong><small>Priority assurance attention</small></article>
    </section>

    {error && <div className="form-message error">{error}</div>}
    {loading ? <div className="loading-panel">Loading assurance findings…</div> : <article className="panel table-panel">
      <div className="panel-heading"><div><h2>Findings register</h2><p>Every finding remains linked to a source submission and its reporting context.</p></div><span className="stage-badge">Live API</span></div>
      <div className="table-scroll"><table className="data-table assurance-table">
        <thead><tr><th>Finding</th><th>Source submission</th><th>Severity</th><th>Owner</th><th>Due</th><th>Status</th></tr></thead>
        <tbody>{rows.length ? rows.map(({ finding, submission }) => <tr key={finding.id}>
          <td><b>{finding.title}</b><small>{finding.id.slice(0, 8)}</small></td>
          <td><b>{submission?.disclosure_id ?? "Unknown"}</b><small>{submission ? submissionLabel(finding.submission_id) : finding.submission_id}</small></td>
          <td><Status value={finding.severity} /></td>
          <td>{finding.owner}</td>
          <td>{finding.due_date ?? "Not set"}</td>
          <td><Status value={finding.status} /></td>
        </tr>) : <tr><td colSpan={6}><div className="empty-inline">No assurance findings yet. Create one from a submitted or approved source response.</div></td></tr>}</tbody>
      </table></div>
    </article>}

    {open && <div className="modal-backdrop" role="presentation" onMouseDown={() => setOpen(false)}>
      <form className="modal-card compact-modal" onSubmit={createFinding} onMouseDown={(event) => event.stopPropagation()}>
        <div className="panel-heading"><div><span className="eyebrow">Assurance register</span><h2>Create finding</h2><p>Link the finding to the exact source response that needs attention.</p></div><button className="icon-button" type="button" onClick={() => setOpen(false)} aria-label="Close">×</button></div>
        <div className="form-grid">
          <label className="span-2">Source submission<select name="submission_id" required defaultValue={submissions[0]?.id ?? ""}>{submissions.map((submission) => <option key={submission.id} value={submission.id}>{submissionLabel(submission.id)}</option>)}</select></label>
          <label>Severity<select name="severity" defaultValue="medium"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></label>
          <label>Due date<input name="due_date" type="date" /></label>
          <label className="span-2">Finding title<input name="title" placeholder="Describe the assurance issue" required /></label>
          <label className="span-2">Management owner<input name="owner" placeholder="Responsible owner or function" required /></label>
        </div>
        <div className="form-footer"><button className="button ghost" type="button" onClick={() => setOpen(false)}>Cancel</button><button className="button primary" disabled={!submissions.length}>Create finding</button></div>
      </form>
    </div>}
  </main>;
}