export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function selectedUser(): string {
  if (typeof window === "undefined") return "admin";
  return window.localStorage.getItem("brsr-demo-user") ?? "admin";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isForm = init?.body instanceof FormData;
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...init,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      "X-Demo-User": selectedUser(),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? `Request failed (${response.status})`;
    const errors = Array.isArray(detail?.errors) ? `: ${detail.errors.join("; ")}` : "";
    throw new Error(`${message}${errors}`);
  }
  return response.json() as Promise<T>;
}

export const apiGet = <T,>(path: string) => request<T>(path);
export const apiPost = <T,>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });
export const apiPut = <T,>(path: string, body: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body) });
export const apiDelete = <T,>(path: string) => request<T>(path, { method: "DELETE" });
export const apiUpload = <T,>(path: string, body: FormData) => request<T>(path, { method: "POST", body });
export const downloadUrl = (path: string) => `${API_URL}/api/v1${path}`;

export type Organization = { id:string; parent_id:string|null; name:string; organization_type:string; code:string; active:boolean };
export type Framework = { id:string; name:string; version:string; baseline:string; status:string };
export type Cycle = { id:string; framework_id:string; name:string; financial_year:string; boundary_type:string; status:string; starts_on:string; ends_on:string };
export type TableColumn = { key:string; label:string; type:string; unit?:string|null; required:boolean; options?:string[] };
export type FormField = { key:string; label:string; type:string; unit?:string|null; required:boolean; min?:number|null; max?:number|null; integer?:boolean; maxLength?:number; options?:string[]; columns?:TableColumn[]; rows?:Record<string,string>[]; helpText?:string };
export type Disclosure = { id:string; framework_id:string; section:string; principle:number|null; question_number:string; title:string; classification:string; response_type:string; reporting_level:string; unit:string|null; evidence_required:boolean; guidance:string; validation_rules:Record<string,unknown>; active:boolean; form_schema:FormField[] };
export type Assignment = { id:string; cycle_id:string; disclosure_id:string; organization_id:string; owner_user_id:string; reviewer_user_id:string; approver_user_id:string; due_date:string; frequency:string; status:string };
export type Submission = { id:string; disclosure_id:string; organization_id:string; financial_year:string; value:Record<string,unknown>; status:string; owner:string; reviewer:string|null; quality_score:number; validation_errors:string[]; updated_at:string };
export type Evidence = { id:string; submission_id:string|null; organization_id:string; financial_year:string; file_name:string; document_type:string; storage_key:string; checksum:string|null; processing_status:string; created_at:string };
export type EvidenceVersion = { id:string; evidence_id:string; version_number:number; checksum:string; content_type:string; size_bytes:number; uploaded_by:string; created_at:string };
export type Comment = { id:string; submission_id:string; actor:string; actor_role:string; body:string; created_at:string };
export type TimelineEvent = { id:string; kind:string; actor:string; role:string; detail:Record<string,unknown>; created_at:string };
export type PrincipleReadiness = { principle:number; name:string; ready:number; total:number; readiness_percent:number; approved:number; awaiting_review:number; missing_evidence:number };
export type Dashboard = { financial_year:string; reporting_cycle:string; total:number; assigned:number; approved:number; awaiting_review:number; changes_requested:number; completion_percent:number; quality_score:number; status_counts:Record<string,number>; modules:number; principle_readiness:PrincipleReadiness[] };
export type ConsolidationRow = { disclosure_id:string; title:string; unit:string|null; submission_count:number; organization_ids:string[]; metrics:Record<string,number>; source_submission_ids:string[] };
export type Consolidation = { financial_year:string; approved_inputs:number; rows:ConsolidationRow[]; method:string };
export type AssuranceFinding = { id:string; submission_id:string; severity:string; title:string; status:string; owner:string; due_date:string|null };
export type ReportSection = { id:string; section:string; principle:number|null; question_number:string; classification:string; title:string; unit:string|null; form_schema:FormField[]; status:string; responses:Array<{submission_id:string;organization_id:string;value:Record<string,unknown>;status:string;quality_score:number}> };
export type ReportPreview = { financial_year:string; generated_from:string; readiness_percent:number; ready_disclosures:number; total_disclosures:number; sections:ReportSection[] };
export type AuditEvent = { id:string; entity_type:string; entity_id:string; action:string; actor:string; actor_role:string; detail:Record<string,unknown>; created_at:string };
