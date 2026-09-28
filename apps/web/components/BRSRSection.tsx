export const sectionMeta={
  A:{title:"General Disclosures",description:"Entity profile, operations, workforce, CSR and transparency",tone:"blue"},
  B:{title:"Management & Process",description:"Policies, governance, targets, review and accountability",tone:"purple"},
  C:{title:"Principle-wise Performance",description:"Essential and leadership indicators across Principles 1–9",tone:"green"},
} as const;

export function SectionIcon({section}:{section:string}){
  if(section==="A") return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V7l8-4 8 4v14M8 10h2m4 0h2m-8 4h2m4 0h2m-8 4h8"/></svg>;
  if(section==="B") return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 20 7v5c0 5-3.4 8-8 9-4.6-1-8-4-8-9V7l8-4Z"/><path d="m8.5 12 2.2 2.2 4.8-5"/></svg>;
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4c-8 .2-14 3.2-14 9 0 3.2 2.4 5 5.2 5C17 18 20 11 20 4Z"/><path d="M4 21c2-5 6-8 12-11"/></svg>;
}

export function SectionBadge({section}:{section:string}){const meta=sectionMeta[section as keyof typeof sectionMeta];return <span className={`section-badge section-${section.toLowerCase()}`}><SectionIcon section={section}/><span><b>Section {section}</b><small>{meta?.title}</small></span></span>}
