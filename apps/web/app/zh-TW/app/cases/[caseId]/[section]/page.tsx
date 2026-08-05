import { CaseWorkspace } from "@/components/CaseWorkspace";
export default async function Page({params}:{params:Promise<{caseId:string;section:string}>}){const {caseId,section}=await params;return <CaseWorkspace caseId={caseId} section={section} language="zh-TW"/>;}
