import { CaseWorkspace } from "@/components/CaseWorkspace";
import { workspaceSections } from "@/lib/workspace";
import { notFound } from "next/navigation";
export default async function Page({params}:{params:Promise<{caseId:string;section:string}>}){const {caseId,section}=await params;if(!workspaceSections.includes(section as typeof workspaceSections[number]))notFound();return <CaseWorkspace caseId={caseId} section={section} language="zh-TW"/>;}
