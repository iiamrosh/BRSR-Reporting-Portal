import { DisclosureForm } from "@/components/DisclosureForm";
export default async function DisclosurePage({params,searchParams}:{params:Promise<{disclosureId:string}>;searchParams:Promise<{organization?:string}>}){const {disclosureId}=await params;const {organization}=await searchParams;return <DisclosureForm disclosureId={disclosureId} initialOrganization={organization}/>}
