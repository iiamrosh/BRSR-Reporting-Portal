"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { modules } from "@/lib/modules";
import { useDemoUser } from "./DemoUserContext";

const icons:Record<string,string>={organization:"◇",cycles:"◫",collection:"▤",imports:"⇧",metrics:"⌁",review:"✓",evidence:"□",assurance:"◎",consolidation:"∑",reports:"▧",audit:"◷",admin:"⚙"};
const roles=[{id:"admin",label:"ESG Administrator"},{id:"coordinator",label:"Entity Coordinator"},{id:"owner",label:"Project Data Owner"},{id:"reviewer",label:"Functional Reviewer"},{id:"approver",label:"Approver"},{id:"assurance",label:"Assurance Reviewer"}];
export function AppShell({children}:{children:React.ReactNode}){
 const path=usePathname(); const [open,setOpen]=useState(false); const {userKey,setUserKey}=useDemoUser(); const role=roles.find(item=>item.id===userKey)??roles[0];
 return <div className="app-shell">
  <aside className={open?"sidebar open":"sidebar"}>
   <div className="brand"><div className="brand-mark">N</div><div><strong>BRSR Nexus</strong><small>ESG reporting OS</small></div></div>
   <nav aria-label="Primary navigation"><Link className={path==="/"?"nav-link active":"nav-link"} href="/" onClick={()=>setOpen(false)}><span>⌂</span>Command center</Link><div className="nav-label">Workspace</div>{modules.map(item=><Link className={path.includes(`/workspace/${item.slug}`)?"nav-link active":"nav-link"} key={item.slug} href={`/workspace/${item.slug}`} onClick={()=>setOpen(false)}><span>{icons[item.slug]}</span>{item.label}</Link>)}</nav>
   <div className="sidebar-foot"><div className="scope-dot"/><div><strong>FY 2025–26</strong><small>Annexure baseline</small></div></div>
  </aside>
  <div className="main-area"><header className="topbar"><button className="menu-button" onClick={()=>setOpen(!open)} aria-label="Toggle navigation">☰</button><div className="top-context"><span className="live-dot"/><b>MEIL Demo Group</b><span>Consolidated boundary</span></div><div className="top-actions"><button className="icon-button" aria-label="Notifications">○<span className="notification-dot"/></button><label className="role-select"><span>Viewing as</span><select value={userKey} onChange={e=>setUserKey(e.target.value)}>{roles.map(r=><option value={r.id} key={r.id}>{r.label}</option>)}</select></label><div className="avatar">{role.label.split(" ").map(w=>w[0]).slice(0,2).join("")}</div></div></header><div className="page-wrap">{children}</div></div>
  {open&&<button className="scrim" onClick={()=>setOpen(false)} aria-label="Close navigation"/>}
 </div>
}
