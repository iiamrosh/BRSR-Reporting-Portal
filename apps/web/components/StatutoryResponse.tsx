import { FormField } from "@/lib/api";

const format=(value:unknown,unit?:string|null)=>{if(value===null||value===undefined||value==="")return "—";const numeric=typeof value==="number"||(/^[-+]?\d+(\.\d+)?$/.test(String(value)));return `${numeric?Number(value).toLocaleString("en-IN"):String(value)}${unit?` ${unit}`:""}`};

export function StatutoryResponse({schema,value}:{schema:FormField[];value:Record<string,unknown>|null|undefined}){
  // Older submissions can contain an empty/null JSON value while their
  // disclosure is being migrated to the structured schema. Keep publication
  // rendering read-only and resilient to that legacy data.
  const safeValue=value && typeof value==="object" && !Array.isArray(value)?value:{};
  const safeSchema=Array.isArray(schema)?schema:[];
  return <div className="statutory-response">{safeSchema.map(field=>{const raw=safeValue[field.key];if(field.type==="table"){const rows=Array.isArray(raw)?raw.filter((row):row is Record<string,unknown>=>Boolean(row)&&typeof row==="object"&&!Array.isArray(row)):[];return <section className="report-field" key={field.key}><h4>{field.label}</h4>{rows.length?<div className="publication-table-scroll"><table className="publication-table"><thead><tr>{(field.columns??[]).map(column=><th key={column.key}>{column.label}{column.unit&&<small>{column.unit}</small>}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={index}>{(field.columns??[]).map(column=><td key={column.key}>{format(row[column.key],column.unit)}</td>)}</tr>)}</tbody></table></div>:<p className="muted">No reportable rows.</p>}</section>}
    return <section className="report-field narrative" key={field.key}><h4>{field.label}</h4><p>{format(raw,field.unit)}</p></section>})}</div>
}
