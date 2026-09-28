"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  apiGet,
  apiPost,
  apiPut,
  apiUpload,
  Comment,
  Cycle,
  Disclosure,
  downloadUrl,
  Evidence,
  Organization,
  Submission,
  TimelineEvent,
} from "@/lib/api";
import { useDemoUser } from "./DemoUserContext";
import { seededValues, StructuredField } from "./StructuredField";

const ownerNames:Record<string,string>={admin:"Aarav — ESG Admin",coordinator:"Diya — Entity Coordinator",owner:"Kabir — Project Owner",reviewer:"Meera — EHS Reviewer",approver:"Rohan — Approver",assurance:"Sara — Assurance"};

export function DisclosureForm({disclosureId,initialOrganization}:{disclosureId:string;initialOrganization?:string}){
  const {userKey}=useDemoUser();
  const [disclosure,setDisclosure]=useState<Disclosure|null>(null);
  const [orgs,setOrgs]=useState<Organization[]>([]);
  const [cycles,setCycles]=useState<Cycle[]>([]);
  const [submissions,setSubmissions]=useState<Submission[]>([]);
  const [organization,setOrganization]=useState(initialOrganization??"");
  const [values,setValues]=useState<Record<string,unknown>>({});
  const [saved,setSaved]=useState<Submission|null>(null);
  const [evidence,setEvidence]=useState<Evidence[]>([]);
  const [comments,setComments]=useState<Comment[]>([]);
  const [timeline,setTimeline]=useState<TimelineEvent[]>([]);
  const [message,setMessage]=useState("");
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(true);
  const [uploading,setUploading]=useState(false);

  const loadBase=async()=>{
    setLoading(true);setError("");
    try{
      const [d,o,c,s]=await Promise.all([apiGet<Disclosure>(`/disclosures/${disclosureId}`),apiGet<Organization[]>("/organizations"),apiGet<Cycle[]>("/reporting-cycles"),apiGet<Submission[]>("/submissions")]);
      setDisclosure(d);setOrgs(o);setCycles(c);setSubmissions(s);
      const selected=initialOrganization||organization||o.find(x=>x.organization_type===d.reporting_level)?.id||o[0]?.id||"";
      setOrganization(selected);
    }catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
    finally{setLoading(false);}
  };
  useEffect(()=>{loadBase();},[disclosureId,initialOrganization,userKey]);

  const existing=useMemo(()=>submissions.find(x=>x.disclosure_id===disclosureId&&x.organization_id===organization),[submissions,disclosureId,organization]);
  useEffect(()=>{
    setSaved(existing??null);
    setValues(seededValues(disclosure?.form_schema??[], existing?.value??{}));
  },[existing?.id,organization,disclosure?.id]);

  const refreshGovernance=async(submissionId:string)=>{
    const [files,notes,events]=await Promise.all([apiGet<Evidence[]>(`/evidence?submission_id=${submissionId}`),apiGet<Comment[]>(`/submissions/${submissionId}/comments`),apiGet<TimelineEvent[]>(`/submissions/${submissionId}/timeline`)]);
    setEvidence(files);setComments(notes);setTimeline(events);
  };
  useEffect(()=>{if(saved?.id)refreshGovernance(saved.id).catch(reason=>setError(reason.message));else{setEvidence([]);setComments([]);setTimeline([]);}},[saved?.id,userKey]);

  const activeCycle=cycles.find(c=>c.status==="open")??cycles[0];
  const editable=!saved||["draft","changes_requested"].includes(saved.status);

  const save=async(event:FormEvent)=>{
    event.preventDefault();if(!disclosure||!activeCycle)return;setMessage("");setError("");
    const payload={disclosure_id:disclosure.id,organization_id:organization,financial_year:activeCycle.financial_year,value:values,owner:ownerNames[userKey]??ownerNames.admin,source_method:"manual"};
    try{
      const item=(existing&&["draft","changes_requested"].includes(existing.status))?await apiPut<Submission>(`/submissions/${existing.id}`,payload):await apiPost<Submission>("/submissions",payload);
      setSaved(item);setSubmissions(current=>[...current.filter(row=>row.id!==item.id),item]);setMessage("Draft saved and validation refreshed.");
    }catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
  };

  const submit=async()=>{
    if(!saved)return;setError("");
    try{const item=await apiPost<Submission>(`/workflow/${saved.id}/transition`,{to_status:"submitted",comment:"Submitted from guided disclosure form"});setSaved(item);setMessage("Response submitted for review.");await refreshGovernance(item.id);}
    catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
  };

  const upload=async(event:FormEvent<HTMLFormElement>)=>{
    event.preventDefault();if(!saved)return;setUploading(true);setError("");
    const form=new FormData(event.currentTarget);const file=form.get("file");
    if(!(file instanceof File)||!file.size){setError("Choose a file to upload.");setUploading(false);return;}
    form.set("submission_id",saved.id);form.set("organization_id",organization);form.set("financial_year",saved.financial_year);
    try{await apiUpload("/evidence/upload",form);setMessage("Evidence stored with a SHA-256 checksum.");event.currentTarget.reset();await refreshGovernance(saved.id);const refreshed=await apiGet<Submission[]>("/submissions");setSubmissions(refreshed);setSaved(refreshed.find(row=>row.id===saved.id)??saved);}
    catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
    finally{setUploading(false);}
  };

  const addComment=async(event:FormEvent<HTMLFormElement>)=>{
    event.preventDefault();if(!saved)return;const form=new FormData(event.currentTarget);const body=String(form.get("body")??"").trim();if(!body)return;
    try{await apiPost(`/submissions/${saved.id}/comments`,{body});event.currentTarget.reset();await refreshGovernance(saved.id);}
    catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
  };

  if(loading)return <div className="loading-panel">Loading disclosure form…</div>;
  if(error&&!disclosure)return <div className="error-panel">{error}</div>;
  if(!disclosure)return null;

  return <main>
    <div className="breadcrumb"><Link href="/workspace/collection">Disclosure workspace</Link><span>›</span><b>{disclosure.id}</b></div>
    <section className="hero compact"><div><span className="eyebrow">Section {disclosure.section}{disclosure.principle?` · Principle ${disclosure.principle}`:""} · Question {disclosure.question_number}</span><h1>{disclosure.title}</h1><p>{disclosure.guidance}</p></div><div className="hero-actions"><span className="stage-badge">{saved?.status?.replaceAll("_"," ")??"not started"}</span></div></section>
    <div className="form-layout">
      <form className="panel response-form" onSubmit={save}>
        <div className="panel-heading"><div><h2>Structured response</h2><p>Disclosure-specific fields, current/prior-year context, and reconciliation rules.</p></div><span className="required-note">* Required</span></div>
        <div className="form-grid">
          <label>Reporting organization<select value={organization} onChange={event=>setOrganization(event.target.value)} disabled={!editable}>{orgs.map(org=><option value={org.id} key={org.id}>{org.name} · {org.organization_type}</option>)}</select></label>
          <label>Reporting cycle<select value={activeCycle?.id??""} disabled>{cycles.map(cycle=><option value={cycle.id} key={cycle.id}>{cycle.name}</option>)}</select></label>
          {disclosure.form_schema.map(field=><StructuredField key={field.key} field={field} value={values[field.key]} disabled={!editable} onChange={next=>setValues(current=>({...current,[field.key]:next}))}/>)}
        </div>
        {(saved?.validation_errors?.length ?? 0) > 0 && <div className="validation-box"><b>Resolve before submission</b><ul>{(saved?.validation_errors ?? []).map(issue=><li key={issue}>{issue}</li>)}</ul></div>}
        {error&&<div className="form-message error">{error}</div>}{message&&<div className="form-message success">{message}</div>}
        <div className="form-footer"><Link className="button ghost" href="/workspace/collection">Back</Link><div><button className="button secondary" type="submit" disabled={!editable}>Save draft</button><button className="button primary" type="button" disabled={!saved||!editable} onClick={submit}>Submit for review</button></div></div>
      </form>
      <aside className="panel form-aside"><span className="eyebrow">Disclosure controls</span><h3>{disclosure.classification}</h3><dl><div><dt>Response type</dt><dd>{disclosure.response_type}</dd></div><div><dt>Reporting level</dt><dd>{disclosure.reporting_level}</dd></div><div><dt>Unit</dt><dd>{disclosure.unit??"Field-specific"}</dd></div><div><dt>Evidence</dt><dd>{disclosure.evidence_required?"Required":"Optional"}</dd></div></dl><div className="quality-block"><span>Data-quality score</span><strong>{saved?.quality_score??0}/100</strong><div className="track"><i style={{width:`${saved?.quality_score??0}%`}}/></div></div><p className="aside-note">Quality combines field validation, reconciliation, and evidence completeness. Only approved or locked records enter reports.</p></aside>
    </div>

    <section className="governance-grid">
      <article className="panel">
        <div className="panel-heading"><div><h2>Evidence</h2><p>Files are stored outside PostgreSQL with checksum and version metadata.</p></div><span className={disclosure.evidence_required?"required-pill":"optional-pill"}>{disclosure.evidence_required?"Required":"Optional"}</span></div>
        {!saved?<div className="empty-inline">Save the draft before attaching evidence.</div>:<><form className="upload-row" onSubmit={upload}><label>Document type<select name="document_type"><option value="supporting_document">Supporting document</option><option value="calculation_workbook">Calculation workbook</option><option value="invoice_or_register">Invoice or register</option><option value="assurance_evidence">Assurance evidence</option></select></label><label className="file-field">Choose file<input name="file" type="file" accept=".pdf,.xlsx,.xls,.csv,.png,.jpg,.jpeg,.doc,.docx" required /></label><button className="button primary" disabled={uploading||!editable}>{uploading?"Uploading…":"Upload evidence"}</button></form>{evidence.length?<div className="evidence-list">{evidence.map(file=><div key={file.id}><div className="file-icon">{file.file_name.split(".").pop()?.toUpperCase()}</div><div><b>{file.file_name}</b><small>SHA-256 {file.checksum?.slice(0,16)}… · {new Date(file.created_at).toLocaleString()}</small></div><a className="button ghost small" href={downloadUrl(`/evidence/${file.id}/download`)}>Download</a></div>)}</div>:<div className="empty-inline">No evidence uploaded yet.</div>}</>}
      </article>
      <article className="panel">
        <div className="panel-heading"><div><h2>Discussion</h2><p>Reviewer guidance and owner responses stay with the submission.</p></div></div>
        {!saved?<div className="empty-inline">Save the draft to open discussion.</div>:<><div className="comment-list">{comments.map(note=><div className="comment" key={note.id}><div className="comment-avatar">{note.actor.split(" ")[0][0]}</div><div><b>{note.actor}</b><small>{note.actor_role.replaceAll("_"," ")} · {new Date(note.created_at).toLocaleString()}</small><p>{note.body}</p></div></div>)}{!comments.length&&<div className="empty-inline">No comments yet.</div>}</div><form className="comment-form" onSubmit={addComment}><textarea name="body" rows={3} placeholder="Add a traceable comment…" required/><button className="button secondary">Add comment</button></form></>}
      </article>
    </section>

    {saved&&<section className="panel submission-timeline"><div className="panel-heading"><div><h2>Submission timeline</h2><p>Immutable source-to-review events for this response.</p></div></div>{timeline.length?<div className="timeline-list">{timeline.map(event=><div key={event.id}><span/><div><b>{event.kind.replaceAll("_"," ")}</b><small>{event.actor} · {event.role.replaceAll("_"," ")}</small></div><time>{new Date(event.created_at).toLocaleString()}</time></div>)}</div>:<div className="empty-inline">Timeline events appear after the next saved change, upload, comment, or workflow action.</div>}</section>}
  </main>;
}
