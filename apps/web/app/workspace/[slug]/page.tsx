import { notFound } from "next/navigation";
import { ModulePage } from "@/components/ModulePage";
import { CyclesLive, OrganizationLive, ReviewLive } from "@/components/LiveModules";
import { DisclosureWorkspace } from "@/components/DisclosureWorkspace";
import { AuditLive, ConsolidationLive, EvidenceVaultLive, ReportsLive } from "@/components/GovernanceModules";
import { AssuranceLive } from "@/components/AssuranceLive";
import { moduleBySlug } from "@/lib/modules";
export default async function WorkspacePage({params}:{params:Promise<{slug:string}>}){const {slug}=await params;const config=moduleBySlug(slug);if(!config)notFound();if(slug==="organization")return <OrganizationLive/>;if(slug==="cycles")return <CyclesLive/>;if(slug==="collection")return <DisclosureWorkspace/>;if(slug==="review")return <ReviewLive/>;if(slug==="evidence")return <EvidenceVaultLive/>;if(slug==="assurance")return <AssuranceLive/>;if(slug==="consolidation")return <ConsolidationLive/>;if(slug==="reports")return <ReportsLive/>;if(slug==="audit")return <AuditLive/>;return <ModulePage config={config}/>}
