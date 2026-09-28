"use client";

import { FormField, TableColumn } from "@/lib/api";

function emptyRow(field: FormField): Record<string, unknown> {
  return Object.fromEntries((field.columns ?? []).map((column) => [column.key, ""]));
}

function CellInput({column,value,disabled,onChange}:{column:TableColumn;value:unknown;disabled:boolean;onChange:(value:string)=>void}) {
  const common={value:String(value??""),disabled,required:column.required,onChange:(event:React.ChangeEvent<HTMLInputElement|HTMLSelectElement|HTMLTextAreaElement>)=>onChange(event.target.value)};
  if(column.type==="select"||column.type==="yes_no_na") return <select {...common}><option value="">Select…</option>{(column.options??(column.type==="yes_no_na"?["Yes","No","Not applicable"]:[])).map(option=><option key={option}>{option}</option>)}</select>;
  if(column.type==="textarea") return <textarea {...common} rows={2}/>;
  if(column.type==="number") return <div className="table-number"><input {...common} type="number" min="0" step="any"/>{column.unit&&<small>{column.unit}</small>}</div>;
  return <input {...common} type={column.type==="url"?"url":"text"}/>;
}

export function StructuredField({field,value,disabled,onChange}:{field:FormField;value:unknown;disabled:boolean;onChange:(value:unknown)=>void}) {
  if(field.type==="table") {
    const rows=Array.isArray(value)?value as Record<string,unknown>[]:[];
    const update=(rowIndex:number,key:string,next:string)=>onChange(rows.map((row,index)=>index===rowIndex?{...row,[key]:next}:row));
    return <fieldset className="structured-table-field"><legend>{field.label}{field.required&&<em>*</em>}</legend>{field.helpText&&<p className="field-help">{field.helpText}</p>}<div className="structured-table-scroll"><table><thead><tr>{(field.columns??[]).map(column=><th key={column.key}>{column.label}{column.unit&&<small>{column.unit}</small>}</th>)}<th aria-label="Row controls"/></tr></thead><tbody>{rows.map((row,rowIndex)=><tr key={rowIndex}>{(field.columns??[]).map(column=><td key={column.key}><CellInput column={column} value={row[column.key]} disabled={disabled} onChange={next=>update(rowIndex,column.key,next)}/></td>)}<td><button type="button" className="remove-row" disabled={disabled} onClick={()=>onChange(rows.filter((_,index)=>index!==rowIndex))} aria-label="Remove row">×</button></td></tr>)}</tbody></table></div><button type="button" className="button ghost small add-row" disabled={disabled} onClick={()=>onChange([...rows,emptyRow(field)])}>+ Add row</button></fieldset>;
  }
  const current=String(value??"");
  const label=<>{field.label}{field.required&&<em>*</em>}</>;
  if(field.type==="textarea") return <label className="span-2">{label}<textarea rows={5} maxLength={field.maxLength} value={current} onChange={event=>onChange(event.target.value)} required={field.required} disabled={disabled}/></label>;
  if(field.type==="yes_no_na"||field.type==="select") return <label>{label}<select value={current} onChange={event=>onChange(event.target.value)} required={field.required} disabled={disabled}><option value="">Select…</option>{(field.options??[]).map(option=><option key={option}>{option}</option>)}</select></label>;
  return <label>{label}<div className="input-unit"><input type={field.type==="number"?"number":field.type==="url"?"url":field.type==="date"?"date":"text"} step={field.integer?"1":"any"} min={field.min??undefined} max={field.max??undefined} value={current} onChange={event=>onChange(event.target.value)} required={field.required} disabled={disabled}/>{field.unit&&<span>{field.unit}</span>}</div></label>;
}

export function seededValues(schema:FormField[], source:Record<string,unknown>={}):Record<string,unknown>{
  const next={...source};
  for(const field of schema) if(field.type==="table" && next[field.key]===undefined && field.rows?.length) next[field.key]=field.rows.map(row=>({...emptyRow(field),...row}));
  return next;
}
